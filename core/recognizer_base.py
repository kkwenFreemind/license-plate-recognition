"""辨識模組抽象基類"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import numpy as np
import logging


class DetailRecognizer(ABC):
    """細部辨識模組的抽象基類"""
    
    def __init__(self, config: Dict = None, logger: logging.Logger = None):
        """
        初始化辨識模組
        
        Args:
            config: 模組配置
            logger: 日誌記錄器
        """
        self.config = config or {}
        self.logger = logger
    
    @property
    @abstractmethod
    def name(self) -> str:
        """模組名稱"""
        pass
    
    @property
    @abstractmethod
    def target_classes(self) -> List[str]:
        """此模組處理的 YOLO 類別"""
        pass
    
    @abstractmethod
    def initialize(self):
        """初始化模組 (載入模型等)"""
        pass
    
    @abstractmethod
    def recognize(self, image: np.ndarray, detection: Dict) -> Optional[Dict]:
        """
        執行細部辨識
        
        Args:
            image: 完整影像
            detection: YOLO 偵測結果
        
        Returns:
            Dict: 辨識結果,或 None 表示無結果
        """
        pass
    
    def should_process(self, detection: Dict) -> bool:
        """
        判斷是否要處理此偵測
        
        Args:
            detection: YOLO 偵測結果
        
        Returns:
            bool: 是否處理
        """
        return detection['class'] in self.target_classes
    
    def extract_region(self, image: np.ndarray, bbox: List[int], 
                       padding: float = 0.1) -> Optional[np.ndarray]:
        """
        提取偵測區域 (支援邊界擴展)
        
        Args:
            image: 完整影像
            bbox: [x1, y1, x2, y2]
            padding: 擴展比例 (0.1 = 10%)
        
        Returns:
            np.ndarray: 提取的區域,或 None 表示無效
        """
        x1, y1, x2, y2 = bbox
        h, w = image.shape[:2]
        
        # 計算擴展
        pad_w = int((x2 - x1) * padding)
        pad_h = int((y2 - y1) * padding)
        
        # 應用擴展並確保不超出邊界
        x1 = max(0, x1 - pad_w)
        y1 = max(0, y1 - pad_h)
        x2 = min(w, x2 + pad_w)
        y2 = min(h, y2 + pad_h)
        
        region = image[y1:y2, x1:x2]
        
        if region.size == 0:
            return None
        
        return region
