"""電子圍籬模組 - 偵測物件是否進入特定區域"""

import cv2
import numpy as np
from datetime import datetime
from typing import List, Tuple, Dict, Any


class VirtualFence:
    """電子圍籬類別"""
    
    def __init__(self, fence_id: str, name: str, points: List[Tuple[int, int]], 
                 target_classes: List[str] = None, min_confidence: float = 0.5):
        """
        初始化電子圍籬
        
        Args:
            fence_id: 圍籬 ID
            name: 圍籬名稱
            points: 多邊形頂點座標 [(x1,y1), (x2,y2), ...]
            target_classes: 要偵測的物件類型，None 表示所有類型
            min_confidence: 最小信心度閾值
        """
        self.fence_id = fence_id
        self.name = name
        self.points = np.array(points, dtype=np.int32)
        self.target_classes = target_classes or []
        self.min_confidence = min_confidence
        self.color = (0, 0, 255)  # 紅色
        self.thickness = 2
        
        # 追蹤物件狀態
        self.tracked_objects = {}  # {object_id: {'in_zone': bool, 'last_seen': timestamp}}
        
    def is_point_in_polygon(self, point: Tuple[int, int]) -> bool:
        """
        判斷點是否在多邊形內
        
        Args:
            point: (x, y) 座標
            
        Returns:
            bool: True 如果點在多邊形內
        """
        result = cv2.pointPolygonTest(self.points, point, False)
        return result >= 0
    
    def is_bbox_in_zone(self, bbox: List[float], threshold: float = 0.5) -> bool:
        """
        判斷邊界框是否在區域內
        
        Args:
            bbox: [x1, y1, x2, y2] 邊界框座標
            threshold: 重疊比例閾值（0-1）
            
        Returns:
            bool: True 如果物件在區域內
        """
        x1, y1, x2, y2 = map(int, bbox)
        
        # 計算物件的中心點和四個角點
        center = ((x1 + x2) // 2, (y1 + y2) // 2)
        bottom_center = ((x1 + x2) // 2, y2)  # 底部中心點（更適合追蹤）
        
        # 檢查底部中心點是否在區域內
        if self.is_point_in_polygon(bottom_center):
            return True
            
        # 如果需要更精確，可以檢查邊界框的多個點
        if threshold < 0.5:
            corners = [
                (x1, y1), (x2, y1),  # 上方兩角
                (x1, y2), (x2, y2),  # 下方兩角
                center                # 中心點
            ]
            
            points_inside = sum(1 for p in corners if self.is_point_in_polygon(p))
            return (points_inside / len(corners)) >= threshold
        
        return False
    
    def check_detection(self, detection: Dict[str, Any]) -> Dict[str, Any]:
        """
        檢查偵測結果是否違反圍籬規則
        
        Args:
            detection: 物件偵測結果
            
        Returns:
            Dict: 包含入侵資訊的字典，None 表示沒有入侵
        """
        obj_class = detection['class']
        confidence = detection['confidence']
        bbox = detection['bbox']
        
        # 檢查是否為目標類型
        if self.target_classes and obj_class not in self.target_classes:
            return None
            
        # 檢查信心度
        if confidence < self.min_confidence:
            return None
        
        # 檢查是否在區域內
        in_zone = self.is_bbox_in_zone(bbox)
        
        if in_zone:
            return {
                'fence_id': self.fence_id,
                'fence_name': self.name,
                'object_class': obj_class,
                'confidence': confidence,
                'bbox': bbox,
                'timestamp': datetime.now().isoformat(),
                'event_type': 'intrusion'  # 入侵事件
            }
        
        return None
    
    def draw_on_frame(self, frame: np.ndarray, show_label: bool = True):
        """
        在影像上繪製圍籬
        
        Args:
            frame: 影像幀
            show_label: 是否顯示標籤
        """
        # 繪製多邊形
        cv2.polylines(frame, [self.points], True, self.color, self.thickness)
        
        # 填充半透明區域
        overlay = frame.copy()
        cv2.fillPoly(overlay, [self.points], self.color)
        cv2.addWeighted(overlay, 0.2, frame, 0.8, 0, frame)
        
        # 顯示標籤
        if show_label:
            # 計算多邊形的中心點
            M = cv2.moments(self.points)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                
                # 繪製標籤背景
                label = self.name
                (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                cv2.rectangle(frame, (cx - w//2 - 5, cy - h - 5), 
                            (cx + w//2 + 5, cy + 5), self.color, -1)
                cv2.putText(frame, label, (cx - w//2, cy), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)


class VirtualFenceManager:
    """電子圍籬管理器"""
    
    def __init__(self, logger=None):
        """
        初始化管理器
        
        Args:
            logger: 日誌記錄器
        """
        self.fences = {}  # {fence_id: VirtualFence}
        self.logger = logger
        self.intrusion_callbacks = []  # 入侵事件回調函數列表
        
    def add_fence(self, fence: VirtualFence):
        """
        新增圍籬
        
        Args:
            fence: VirtualFence 實例
        """
        self.fences[fence.fence_id] = fence
        if self.logger:
            self.logger.info(f"已新增電子圍籬: {fence.name} (ID: {fence.fence_id})")
    
    def remove_fence(self, fence_id: str):
        """移除圍籬"""
        if fence_id in self.fences:
            fence_name = self.fences[fence_id].name
            del self.fences[fence_id]
            if self.logger:
                self.logger.info(f"已移除電子圍籬: {fence_name}")
    
    def register_intrusion_callback(self, callback):
        """
        註冊入侵事件回調函數
        
        Args:
            callback: 回調函數 callback(intrusion_event)
        """
        self.intrusion_callbacks.append(callback)
    
    def check_detections(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        檢查所有偵測結果是否違反圍籬規則
        
        Args:
            detections: 物件偵測結果列表
            
        Returns:
            List[Dict]: 入侵事件列表
        """
        intrusions = []
        
        for detection in detections:
            for fence in self.fences.values():
                intrusion = fence.check_detection(detection)
                if intrusion:
                    intrusions.append(intrusion)
                    
                    # 觸發回調函數
                    for callback in self.intrusion_callbacks:
                        try:
                            callback(intrusion)
                        except Exception as e:
                            if self.logger:
                                self.logger.error(f"入侵回調函數執行錯誤: {e}")
        
        return intrusions
    
    def draw_all_fences(self, frame: np.ndarray):
        """
        在影像上繪製所有圍籬
        
        Args:
            frame: 影像幀
        """
        for fence in self.fences.values():
            fence.draw_on_frame(frame)
    
    def load_fences_from_config(self, config: Dict[str, Any]):
        """
        從配置載入圍籬
        
        Args:
            config: 圍籬配置字典
            
        Example config:
        {
            "fences": [
                {
                    "id": "fence_001",
                    "name": "禁止進入區域",
                    "points": [[100, 100], [500, 100], [500, 400], [100, 400]],
                    "target_classes": ["person"],
                    "min_confidence": 0.6
                }
            ]
        }
        """
        fences_config = config.get('fences', [])
        
        for fence_cfg in fences_config:
            fence = VirtualFence(
                fence_id=fence_cfg['id'],
                name=fence_cfg['name'],
                points=[tuple(p) for p in fence_cfg['points']],
                target_classes=fence_cfg.get('target_classes'),
                min_confidence=fence_cfg.get('min_confidence', 0.5)
            )
            self.add_fence(fence)
        
        if self.logger:
            self.logger.info(f"已載入 {len(fences_config)} 個電子圍籬")


def create_fence_from_roi(frame: np.ndarray, window_name: str = "選擇圍籬區域") -> List[Tuple[int, int]]:
    """
    互動式選擇圍籬區域（使用滑鼠點擊）
    
    Args:
        frame: 影像幀
        window_name: 視窗名稱
        
    Returns:
        List[Tuple[int, int]]: 多邊形頂點座標
    """
    points = []
    temp_frame = frame.copy()
    
    def mouse_callback(event, x, y, flags, param):
        nonlocal points, temp_frame
        
        if event == cv2.EVENT_LBUTTONDOWN:
            # 左鍵點擊：新增點
            points.append((x, y))
            temp_frame = frame.copy()
            
            # 繪製已選擇的點
            for i, pt in enumerate(points):
                cv2.circle(temp_frame, pt, 5, (0, 255, 0), -1)
                if i > 0:
                    cv2.line(temp_frame, points[i-1], pt, (0, 255, 0), 2)
            
            # 繪製臨時線到當前滑鼠位置
            if len(points) > 0:
                cv2.line(temp_frame, points[-1], (x, y), (0, 255, 0), 1)
            
            cv2.imshow(window_name, temp_frame)
        
        elif event == cv2.EVENT_RBUTTONDOWN:
            # 右鍵點擊：完成選擇
            if len(points) >= 3:
                # 閉合多邊形
                cv2.line(temp_frame, points[-1], points[0], (0, 255, 0), 2)
                cv2.imshow(window_name, temp_frame)
    
    cv2.imshow(window_name, temp_frame)
    cv2.setMouseCallback(window_name, mouse_callback)
    
    print("左鍵點擊選擇多邊形頂點，右鍵完成選擇，按 ESC 取消")
    
    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            break
        elif key == ord('r'):  # Reset
            points = []
            temp_frame = frame.copy()
            cv2.imshow(window_name, temp_frame)
    
    cv2.destroyAllWindows()
    return points
