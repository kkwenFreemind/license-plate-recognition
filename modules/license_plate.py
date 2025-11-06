"""車牌辨識模組 - 改進版"""

import cv2
import numpy as np
import re
from typing import Optional, Dict, List, Tuple
import logging

from core.recognizer_base import DetailRecognizer


class LicensePlateRecognizer(DetailRecognizer):
    """車牌辨識模組 - 支援台灣車牌格式"""
    
    def __init__(self, config: Dict = None, logger: logging.Logger = None):
        """
        初始化車牌辨識模組
        
        Args:
            config: 模組配置
            logger: 日誌記錄器
        """
        super().__init__(config, logger)
        self.ocr_reader = None
        
        # 從配置讀取參數
        self.min_confidence = config.get('min_confidence', 0.3)
        self.languages = config.get('ocr_languages', ['en', 'ch_tra'])
        self.gpu = config.get('gpu', False)
        self.multi_zone = config.get('multi_zone_search', True)
    
    @property
    def name(self) -> str:
        return "license_plate"
    
    @property
    def target_classes(self) -> List[str]:
        return ['car', 'truck', 'bus', 'motorcycle']
    
    def initialize(self):
        """載入 OCR 模型"""
        try:
            import easyocr
            if self.logger:
                self.logger.info(f"載入 {self.name} 模組...")
            
            self.ocr_reader = easyocr.Reader(
                self.languages, 
                gpu=self.gpu,
                verbose=False
            )
            
            if self.logger:
                self.logger.info(f"✓ {self.name} 模組就緒")
        except Exception as e:
            if self.logger:
                self.logger.error(f"OCR 模組載入失敗: {e}")
            raise
    
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        預處理圖片以提高辨識率
        
        Args:
            image: 輸入影像
        
        Returns:
            np.ndarray: 預處理後的影像
        """
        try:
            # 轉灰階
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # CLAHE 增強對比
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            # Otsu 二值化
            _, binary = cv2.threshold(
                enhanced, 0, 255, 
                cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )
            
            return binary
        except Exception as e:
            if self.logger:
                self.logger.error(f"預處理失敗: {e}")
            return image
    
    def validate_plate(self, text: str) -> Tuple[bool, str]:
        """
        驗證台灣車牌格式
        
        支援格式:
        - ABC-1234 (一般自用車)
        - AB-1234 (舊式)
        - 1234-AB (營業車)
        - ABC-123 (機車)
        
        Args:
            text: OCR 辨識的文字
        
        Returns:
            Tuple[bool, str]: (是否有效, 格式化後的車牌)
        """
        # 清理文字
        text = text.replace(' ', '').replace('-', '').upper()
        text = re.sub(r'[^A-Z0-9]', '', text)
        
        if len(text) < 5:
            return False, text
        
        # 台灣車牌格式
        patterns = [
            (r'^[A-Z]{2,3}\d{4}$', 'car'),       # ABC-1234
            (r'^[A-Z]{2}\d{4}$', 'car'),         # AB-1234
            (r'^\d{4}[A-Z]{2}$', 'commercial'),  # 1234-AB
            (r'^[A-Z]{3}\d{3}$', 'motorcycle'),  # ABC-123
        ]
        
        for pattern, plate_type in patterns:
            if re.match(pattern, text):
                formatted = self.format_plate(text, plate_type)
                return True, formatted
        
        return False, text
    
    def format_plate(self, text: str, plate_type: str) -> str:
        """
        格式化車牌
        
        Args:
            text: 車牌文字
            plate_type: 車牌類型
        
        Returns:
            str: 格式化後的車牌
        """
        alpha_part = ''.join([c for c in text if c.isalpha()])
        digit_part = ''.join([c for c in text if c.isdigit()])
        
        if not alpha_part or not digit_part:
            return text
        
        if plate_type == 'commercial':
            return f"{digit_part}-{alpha_part}"
        else:
            return f"{alpha_part}-{digit_part}"
    
    def _search_single_zone(self, zone: np.ndarray) -> Optional[Dict]:
        """
        在單一區域搜尋車牌
        
        Args:
            zone: 搜尋區域影像
        
        Returns:
            Dict: 辨識結果,或 None
        """
        if zone.size == 0:
            return None
        
        try:
            processed = self.preprocess(zone)
            results = self.ocr_reader.readtext(processed)
            
            if self.logger and results:
                self.logger.debug(f"OCR 偵測到 {len(results)} 個文字區域")
            
            for (bbox, text, prob) in results:
                if self.logger:
                    self.logger.debug(f"OCR 原始結果: '{text}' (信心度: {prob:.2f})")
                
                if prob < self.min_confidence:
                    if self.logger:
                        self.logger.debug(f"  ❌ 信心度過低 ({prob:.2f} < {self.min_confidence})")
                    continue
                
                if len(text) < 5:
                    if self.logger:
                        self.logger.debug(f"  ❌ 文字太短 (長度: {len(text)})")
                    continue
                
                is_valid, formatted = self.validate_plate(text)
                
                if is_valid:  # 只回傳有效格式
                    if self.logger:
                        self.logger.debug(f"  ✅ 格式驗證通過: {formatted}")
                    return {
                        'plate_number': formatted,
                        'confidence': float(prob),
                        'is_valid': is_valid,
                        'raw_text': text
                    }
                else:
                    if self.logger:
                        self.logger.debug(f"  ❌ 格式驗證失敗: '{text}' -> '{formatted}'")
        except Exception as e:
            if self.logger:
                self.logger.error(f"區域搜尋錯誤: {e}")
        
        return None
    
    def recognize(self, image: np.ndarray, detection: Dict) -> Optional[Dict]:
        """
        辨識車牌 - 多區域搜尋策略
        
        Args:
            image: 完整影像
            detection: YOLO 偵測結果
        
        Returns:
            Dict: 辨識結果,或 None
        """
        if self.logger:
            self.logger.debug(
                f"開始車牌辨識: {detection['class']} "
                f"(信心度: {detection['confidence']:.2f})"
            )
        
        # 增加擴展比例，擷取更大範圍 (從 0.1 改為 0.2)
        vehicle_region = self.extract_region(image, detection['bbox'], padding=0.2)
        
        if vehicle_region is None:
            if self.logger:
                self.logger.debug("無法提取車輛區域")
            return None
        
        height, width = vehicle_region.shape[:2]
        
        # 過濾太小的車輛區域（至少要 200x150 才能辨識車牌）
        if width < 200 or height < 150:
            if self.logger:
                self.logger.debug(
                    f"車輛區域太小: {width}x{height} "
                    f"(需要至少 200x150)"
                )
            return None
        
        if self.logger:
            self.logger.debug(f"車輛區域大小: {width}x{height}")
        
        # 定義搜尋區域
        if self.multi_zone:
            search_zones = [
                ('bottom', vehicle_region[int(height*0.5):, :]),
                ('middle', vehicle_region[int(height*0.3):int(height*0.7), :]),
                ('top', vehicle_region[:int(height*0.4), :]),
                ('full', vehicle_region)
            ]
        else:
            search_zones = [('bottom', vehicle_region[int(height*0.5):, :])]
        
        # 依序搜尋各區域
        best_result = None
        best_confidence = 0
        
        for zone_name, zone in search_zones:
            if self.logger:
                self.logger.debug(f"搜尋區域: {zone_name} ({zone.shape[1]}x{zone.shape[0]})")
            
            result = self._search_single_zone(zone)
            
            if result and result['confidence'] > best_confidence:
                best_result = result
                best_confidence = result['confidence']
                best_result['zone'] = zone_name
                
                # 如果找到高信心度結果,提前結束
                if best_confidence > 0.8:
                    if self.logger:
                        self.logger.debug(f"找到高信心度結果，提前結束搜尋")
                    break
        
        if best_result and self.logger:
            self.logger.info(
                f"✅ 車牌辨識成功: {best_result['plate_number']} "
                f"(信心度: {best_result['confidence']:.2f}, "
                f"區域: {best_result['zone']})"
            )
        elif self.logger:
            self.logger.debug(f"❌ 未找到有效車牌")
        
        return best_result
