"""主系統 - 多執行緒版本"""

import cv2
import time
import threading
from queue import Queue, Empty
from typing import List, Dict, Optional, Callable
from datetime import datetime
import logging

from .base_detector import BaseDetector
from .recognizer_base import DetailRecognizer
from utils.performance import PerformanceMonitor


class MultiModalRecognitionSystem:
    """多模態辨識系統 - 非同步版本"""
    
    def __init__(self, config: Dict, logger: logging.Logger = None):
        """
        初始化辨識系統
        
        Args:
            config: 系統配置
            logger: 日誌記錄器
        """
        self.config = config
        self.logger = logger
        
        # 初始化偵測器
        yolo_config = config.get('yolo', {})
        self.base_detector = BaseDetector(
            model_path=yolo_config.get('model_path', 'yolov8n.pt'),
            device=yolo_config.get('device', 'cpu'),
            logger=self.logger
        )
        
        # 辨識模組
        self.recognizers: Dict[str, DetailRecognizer] = {}
        
        # 執行緒控制
        self.running = False
        self.frame_queue = Queue(maxsize=5)
        
        # 效能監控
        perf_config = config.get('performance', {})
        self.monitor = PerformanceMonitor(
            enabled=perf_config.get('enable_monitoring', True),
            logger=self.logger
        )
        
        if self.logger:
            self.logger.info("✓ 系統初始化完成")
    
    def register_recognizer(self, recognizer: DetailRecognizer):
        """
        註冊辨識模組
        
        Args:
            recognizer: 辨識模組實例
        """
        try:
            recognizer.initialize()
            self.recognizers[recognizer.name] = recognizer
            if self.logger:
                self.logger.info(f"✓ 已註冊模組: {recognizer.name}")
        except Exception as e:
            if self.logger:
                self.logger.error(f"模組註冊失敗 {recognizer.name}: {e}")
            raise
    
    def process_image(self, image, conf_threshold: float = 0.5) -> List[Dict]:
        """
        處理單張圖片
        
        Args:
            image: 輸入影像
            conf_threshold: YOLO 信心度閾值
        
        Returns:
            List[Dict]: 辨識結果列表
        """
        start_time = time.time()
        
        if image is None or image.size == 0:
            return []
        
        try:
            # 1. YOLO 偵測
            detections = self.base_detector.detect(image, conf_threshold)
            
            results = []
            
            # 2. 細部辨識
            for detection in detections:
                result = {
                    'timestamp': datetime.now().isoformat(),
                    'base_detection': detection,
                    'details': {}
                }
                
                # 3. 執行適用的辨識模組
                for name, recognizer in self.recognizers.items():
                    if recognizer.should_process(detection):
                        try:
                            detail = recognizer.recognize(image, detection)
                            if detail:
                                result['details'][name] = detail
                        except Exception as e:
                            if self.logger:
                                self.logger.error(f"{name} 辨識失敗: {e}")
                            result['details'][name] = {'error': str(e)}
                
                results.append(result)
            
            # 記錄效能
            duration = time.time() - start_time
            self.monitor.record_processing(duration, len(results))
            
            return results
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"處理影像時發生錯誤: {e}")
            return []
    
    def process_rtsp(self, rtsp_url: str, camera_id: str, 
                     interval: float = 2.0, 
                     callback: Optional[Callable] = None):
        """
        處理 RTSP 串流 - 多執行緒版本
        
        Args:
            rtsp_url: RTSP URL
            camera_id: 攝影機 ID
            interval: 處理間隔(秒)
            callback: 結果回調 callback(camera_id, results)
        """
        if self.logger:
            self.logger.info(f"[{camera_id}] 連接 RTSP: {rtsp_url}")
        
        cap = cv2.VideoCapture(rtsp_url)
        
        if not cap.isOpened():
            if self.logger:
                self.logger.error(f"[{camera_id}] ❌ 無法連接 RTSP")
            return
        
        if self.logger:
            self.logger.info(f"[{camera_id}] ✓ RTSP 連接成功")
            self.logger.info(f"[{camera_id}] 處理間隔: {interval} 秒")
        
        self.running = True
        
        # 影像讀取執行緒
        def capture_frames():
            retry_count = 0
            max_retries = 5
            
            while self.running:
                ret, frame = cap.read()
                if ret:
                    retry_count = 0  # 重置重試次數
                    
                    # 如果佇列滿了,丟棄舊幀
                    if self.frame_queue.full():
                        try:
                            self.frame_queue.get_nowait()
                        except Empty:
                            pass
                    
                    try:
                        self.frame_queue.put((time.time(), frame), timeout=0.1)
                    except:
                        pass
                else:
                    retry_count += 1
                    if self.logger:
                        self.logger.warning(
                            f"[{camera_id}] 讀取幀失敗 ({retry_count}/{max_retries})"
                        )
                    
                    if retry_count >= max_retries:
                        if self.logger:
                            self.logger.error(f"[{camera_id}] 重新連線...")
                        cap.release()
                        time.sleep(5)
                        cap.open(rtsp_url)
                        retry_count = 0
                    else:
                        time.sleep(1)
                        continue
                
                time.sleep(0.033)  # ~30fps
        
        # 辨識處理執行緒
        def process_frames():
            last_process_time = 0
            frame_count = 0
            
            while self.running:
                try:
                    timestamp, frame = self.frame_queue.get(timeout=1)
                    
                    # 檢查是否該處理
                    if timestamp - last_process_time >= interval:
                        frame_count += 1
                        
                        # 執行辨識
                        conf_threshold = self.config.get('yolo', {}).get(
                            'confidence_threshold', 0.5
                        )
                        results = self.process_image(frame, conf_threshold)
                        
                        # 顯示結果
                        if results:
                            self._print_results(results, camera_id, frame_count)
                        
                        # 回調
                        if callback and results:
                            try:
                                callback(camera_id, results)
                            except Exception as e:
                                if self.logger:
                                    self.logger.error(f"回調函數錯誤: {e}")
                        
                        last_process_time = timestamp
                        
                except Empty:
                    continue
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"處理執行緒錯誤: {e}")
        
        # 啟動執行緒
        capture_thread = threading.Thread(target=capture_frames, daemon=True)
        process_thread = threading.Thread(target=process_frames, daemon=True)
        
        capture_thread.start()
        process_thread.start()
        
        try:
            # 主執行緒等待
            last_report_time = time.time()
            report_interval = 60  # 每 60 秒報告一次
            
            while self.running:
                time.sleep(1)
                
                # 定期顯示效能報告
                if time.time() - last_report_time >= report_interval:
                    report = self.monitor.get_report()
                    if report and self.logger:
                        self.logger.info(f"[{camera_id}] 效能報告: {report}")
                    last_report_time = time.time()
                
        except KeyboardInterrupt:
            if self.logger:
                self.logger.info("使用者中斷")
        finally:
            self.running = False
            capture_thread.join(timeout=2)
            process_thread.join(timeout=2)
            cap.release()
            if self.logger:
                self.logger.info(f"[{camera_id}] RTSP 處理已停止")
    
    def _print_results(self, results: List[Dict], camera_id: str, frame_count: int):
        """列印結果"""
        if not results or not self.logger:
            return
        
        self.logger.info(
            f"[{datetime.now().strftime('%H:%M:%S')}] "
            f"Camera: {camera_id}, Frame: {frame_count}, "
            f"Objects: {len(results)}"
        )
        
        for i, result in enumerate(results, 1):
            detection = result['base_detection']
            
            # 格式化細部辨識結果
            details_parts = []
            for k, v in result['details'].items():
                if isinstance(v, dict) and 'plate_number' in v:
                    details_parts.append(f"{k}: {v['plate_number']}")
                elif isinstance(v, dict) and 'error' not in v:
                    details_parts.append(f"{k}: {v}")
            
            details_str = ", ".join(details_parts)
            
            if details_str:
                self.logger.info(
                    f"  #{i} {detection['class']} "
                    f"({detection['confidence']:.2f}) - {details_str}"
                )
            else:
                self.logger.info(
                    f"  #{i} {detection['class']} "
                    f"({detection['confidence']:.2f})"
                )
    
    def stop(self):
        """停止系統"""
        self.running = False
