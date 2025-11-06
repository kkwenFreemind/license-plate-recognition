"""效能監控工具"""

import time
from collections import deque
from typing import Dict, Optional
import logging


class PerformanceMonitor:
    """效能監控器"""
    
    def __init__(self, enabled: bool = True, 
                 window_size: int = 100, 
                 logger: logging.Logger = None):
        """
        初始化效能監控器
        
        Args:
            enabled: 是否啟用監控
            window_size: 滑動視窗大小
            logger: 日誌記錄器
        """
        self.enabled = enabled
        self.logger = logger
        
        # 使用滑動視窗記錄
        self.processing_times = deque(maxlen=window_size)
        self.detection_counts = deque(maxlen=window_size)
        
        self.total_frames = 0
        self.total_detections = 0
        self.start_time = time.time()
        
        self.last_report_time = time.time()
        self.report_interval = 60  # 每 60 秒報告一次
    
    def record_processing(self, duration: float, detections_count: int):
        """
        記錄處理結果
        
        Args:
            duration: 處理時間(秒)
            detections_count: 偵測物件數量
        """
        if not self.enabled:
            return
        
        self.processing_times.append(duration)
        self.detection_counts.append(detections_count)
        
        self.total_frames += 1
        self.total_detections += detections_count
    
    def get_report(self) -> Optional[Dict]:
        """
        取得效能報告
        
        Returns:
            Dict: 效能報告,如果未到報告時間則返回 None
        """
        if not self.enabled:
            return None
        
        current_time = time.time()
        
        # 檢查是否該報告
        if current_time - self.last_report_time < self.report_interval:
            return None
        
        if not self.processing_times:
            return None
        
        avg_time = sum(self.processing_times) / len(self.processing_times)
        avg_detections = sum(self.detection_counts) / len(self.detection_counts)
        
        total_runtime = current_time - self.start_time
        
        report = {
            'avg_processing_time': f"{avg_time:.3f}s",
            'avg_fps': f"{1/avg_time:.1f}" if avg_time > 0 else "N/A",
            'avg_detections': f"{avg_detections:.1f}",
            'total_frames': self.total_frames,
            'total_detections': self.total_detections,
            'runtime': f"{total_runtime/60:.1f}m"
        }
        
        self.last_report_time = current_time
        
        return report
    
    def reset(self):
        """重置統計"""
        self.processing_times.clear()
        self.detection_counts.clear()
        self.total_frames = 0
        self.total_detections = 0
        self.start_time = time.time()
    
    def get_instant_stats(self) -> Dict:
        """取得即時統計 (不受報告間隔限制)"""
        if not self.enabled or not self.processing_times:
            return {}
        
        avg_time = sum(self.processing_times) / len(self.processing_times)
        avg_detections = sum(self.detection_counts) / len(self.detection_counts)
        
        return {
            'avg_time': avg_time,
            'fps': 1/avg_time if avg_time > 0 else 0,
            'avg_detections': avg_detections,
            'total_frames': self.total_frames
        }
