"""YOLO 基礎偵測器"""

from ultralytics import YOLO
import cv2
import numpy as np
from typing import List, Dict, Optional
import logging


class BaseDetector:
    """YOLO 基礎偵測器"""
    
    def __init__(self, model_path: str = 'yolov8n.pt', 
                 device: str = 'cpu', 
                 logger: logging.Logger = None):
        """
        初始化 YOLO 偵測器
        
        Args:
            model_path: YOLO 模型路徑
            device: 運算設備 ('cpu' 或 'cuda:0')
            logger: 日誌記錄器
        """
        self.logger = logger
        if self.logger:
            self.logger.info(f"載入 YOLO 模型: {model_path}")
        
        self.model = YOLO(model_path)
        self.device = device
        
        if self.logger:
            self.logger.info(f"✓ YOLO 模型載入完成 (設備: {device})")
    
    def detect(self, image: np.ndarray, 
               conf_threshold: float = 0.5, 
               classes: Optional[List[str]] = None,
               track: bool = False) -> List[Dict]:
        """
        執行 YOLO 偵測
        
        Args:
            image: 輸入影像 (BGR 格式)
            conf_threshold: 信心度閾值
            classes: 要偵測的類別列表 (None = 全部)
            track: 是否啟用物件追蹤（用於停留時間偵測）
        
        Returns:
            List[Dict]: 偵測結果列表,每個字典包含:
                - class: 類別名稱
                - confidence: 信心度
                - bbox: [x1, y1, x2, y2]
                - center: [x, y]
                - area: 面積
                - track_id: 追蹤 ID（僅當 track=True 時）
        """
        if image is None or image.size == 0:
            if self.logger:
                self.logger.warning("輸入影像無效")
            return []
        
        try:
            # 根據 track 參數選擇使用 track 或 predict
            if track:
                results = self.model.track(image, persist=True, verbose=False, device=self.device)
            else:
                results = self.model(image, verbose=False, device=self.device)
            
            detections = []
            
            for result in results:
                boxes = result.boxes
                
                # 檢查是否有追蹤 ID
                has_tracking = track and boxes.id is not None
                
                for i, box in enumerate(boxes):
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    label = self.model.names[cls]
                    
                    # 過濾
                    if conf < conf_threshold:
                        continue
                    if classes and label not in classes:
                        continue
                    
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                    
                    # 確保座標合法
                    x1, y1 = max(0, x1), max(0, y1)
                    x2 = min(image.shape[1], x2)
                    y2 = min(image.shape[0], y2)
                    
                    detection = {
                        'class': label,
                        'confidence': float(conf),
                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                        'center': [(x1 + x2) // 2, (y1 + y2) // 2],
                        'area': (x2 - x1) * (y2 - y1)
                    }
                    
                    # 如果有追蹤 ID，加入到結果中
                    if has_tracking:
                        track_id = int(boxes.id[i])
                        detection['track_id'] = track_id
                    
                    detections.append(detection)
            
            if self.logger:
                self.logger.debug(f"偵測到 {len(detections)} 個物件")
            
            return detections
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"YOLO 偵測失敗: {e}")
            return []
    
    def get_class_names(self) -> List[str]:
        """取得所有可偵測的類別名稱"""
        return list(self.model.names.values())
