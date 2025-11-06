"""
電子圍籬停留時間偵測範例
展示如何使用停留時間閾值功能
"""

import cv2
import numpy as np
from modules.virtual_fence import VirtualFence, VirtualFenceManager
from ultralytics import YOLO
import time


def main():
    """主程式：展示停留時間偵測功能"""
    
    # 1. 初始化 YOLO 模型（用於物件偵測和追蹤）
    print("正在載入 YOLO 模型...")
    model = YOLO('yolov8n.pt')  # 使用 YOLOv8 nano 模型
    
    # 2. 創建電子圍籬管理器
    fence_manager = VirtualFenceManager()
    
    # 3. 創建測試用的圍籬（螢幕中央區域，停留 3 秒才觸發）
    fence = VirtualFence(
        fence_id="dwell_test_001",
        name="3秒停留檢測區",
        points=[
            (200, 150),  # 左上
            (440, 150),  # 右上
            (440, 330),  # 右下
            (200, 330)   # 左下
        ],
        target_classes=["person"],  # 只偵測人
        min_confidence=0.5,
        dwell_time_threshold=3.0  # 關鍵：停留 3 秒才觸發
    )
    fence_manager.add_fence(fence)
    
    # 4. 註冊入侵事件回調函數
    def on_intrusion(intrusion_event):
        """入侵事件處理"""
        print(f"\n⚠️ 觸發警報！")
        print(f"   圍籬: {intrusion_event['fence_name']}")
        print(f"   物件: {intrusion_event['object_class']}")
        print(f"   追蹤 ID: {intrusion_event.get('track_id', 'N/A')}")
        print(f"   停留時間: {intrusion_event['dwell_time']:.2f} 秒")
        print(f"   觸發閾值: {intrusion_event['dwell_time_threshold']} 秒")
        print(f"   時間: {intrusion_event['timestamp']}")
    
    fence_manager.register_intrusion_callback(on_intrusion)
    
    # 5. 開啟攝影機或影片
    print("\n正在開啟攝影機...")
    cap = cv2.VideoCapture(0)  # 0 表示預設攝影機
    # 如果要使用影片，取消下面這行的註解：
    # cap = cv2.VideoCapture("your_video.mp4")
    
    if not cap.isOpened():
        print("❌ 無法開啟攝影機或影片")
        return
    
    # 設定視窗
    cv2.namedWindow("停留時間偵測", cv2.WINDOW_NORMAL)
    
    print("\n✅ 系統啟動成功！")
    print("=" * 60)
    print("說明：")
    print("  - 紅色區域是電子圍籬")
    print("  - 物件進入後會顯示停留時間")
    print("  - 停留達到 3 秒後會觸發警報")
    print("  - 進度條顯示距離觸發還有多久")
    print("  - 按 'q' 結束程式")
    print("=" * 60)
    
    frame_count = 0
    fps_time = time.time()
    fps = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("無法讀取影像")
            break
        
        # 計算 FPS
        frame_count += 1
        if frame_count % 10 == 0:
            current_time = time.time()
            fps = 10 / (current_time - fps_time)
            fps_time = current_time
        
        # 6. 使用 YOLO 進行物件偵測和追蹤
        # track() 方法會自動分配追蹤 ID
        results = model.track(frame, persist=True, verbose=False)
        
        # 7. 轉換偵測結果格式
        detections = []
        if results and len(results) > 0:
            result = results[0]
            if result.boxes is not None:
                boxes = result.boxes
                
                # 如果有追蹤 ID
                if boxes.id is not None:
                    for box, cls, conf, track_id in zip(
                        boxes.xyxy.cpu().numpy(),
                        boxes.cls.cpu().numpy(),
                        boxes.conf.cpu().numpy(),
                        boxes.id.cpu().numpy()
                    ):
                        detections.append({
                            'class': model.names[int(cls)],
                            'confidence': float(conf),
                            'bbox': box.tolist(),
                            'track_id': int(track_id)  # 重要：追蹤 ID
                        })
                else:
                    # 沒有追蹤 ID 的情況
                    for box, cls, conf in zip(
                        boxes.xyxy.cpu().numpy(),
                        boxes.cls.cpu().numpy(),
                        boxes.conf.cpu().numpy()
                    ):
                        detections.append({
                            'class': model.names[int(cls)],
                            'confidence': float(conf),
                            'bbox': box.tolist(),
                            'track_id': None
                        })
        
        # 8. 檢查圍籬入侵（會自動追蹤停留時間）
        intrusions = fence_manager.check_detections(detections)
        
        # 9. 繪製偵測結果
        for detection in detections:
            if detection['class'] == 'person':
                bbox = detection['bbox']
                x1, y1, x2, y2 = map(int, bbox)
                
                # 繪製邊界框
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # 顯示類別和信心度
                label = f"{detection['class']} {detection['confidence']:.2f}"
                if detection['track_id'] is not None:
                    label += f" ID:{detection['track_id']}"
                
                cv2.putText(frame, label, (x1, y1 - 5),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # 10. 繪製圍籬（會自動顯示停留時間和進度條）
        fence_manager.draw_all_fences(frame)
        
        # 11. 顯示 FPS 和狀態資訊
        info_y = 30
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, info_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        info_y += 25
        active_objects = sum(1 for f in fence_manager.fences.values() 
                           for obj in f.tracked_objects.values() 
                           if obj['in_zone'])
        cv2.putText(frame, f"Active Objects: {active_objects}", (10, info_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        info_y += 25
        cv2.putText(frame, f"Intrusions: {len(intrusions)}", (10, info_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # 顯示影像
        cv2.imshow("停留時間偵測", frame)
        
        # 按 'q' 結束
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # 清理資源
    cap.release()
    cv2.destroyAllWindows()
    print("\n程式結束")


if __name__ == "__main__":
    main()
