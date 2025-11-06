"""
停留時間功能測試腳本
測試電子圍籬的停留時間追蹤功能
"""

import sys
import time
from modules.virtual_fence import VirtualFence, VirtualFenceManager


def test_dwell_time_tracking():
    """測試停留時間追蹤功能"""
    
    print("=" * 60)
    print("停留時間追蹤功能測試")
    print("=" * 60)
    
    # 創建測試圍籬（3 秒閾值）
    fence = VirtualFence(
        fence_id="test_001",
        name="測試圍籬",
        points=[(100, 100), (400, 100), (400, 400), (100, 400)],
        target_classes=["person"],
        min_confidence=0.5,
        dwell_time_threshold=3.0  # 3 秒閾值
    )
    
    print(f"\n✅ 創建圍籬: {fence.name}")
    print(f"   - 停留時間閾值: {fence.dwell_time_threshold} 秒")
    print(f"   - 目標類別: {fence.target_classes}")
    
    # 模擬物件偵測序列
    print("\n" + "=" * 60)
    print("模擬物件追蹤序列")
    print("=" * 60)
    
    # 測試案例 1: 物件停留超過閾值
    print("\n📍 測試案例 1: 物件停留 4 秒（應觸發）")
    print("-" * 60)
    
    track_id = 1
    bbox = [200, 200, 300, 350]  # 在圍籬內
    
    triggered = False
    for i in range(5):  # 模擬 5 次偵測（約 4 秒，假設 1 秒 1 幀）
        time.sleep(1)  # 等待 1 秒
        
        detection = {
            'class': 'person',
            'confidence': 0.8,
            'bbox': bbox,
            'track_id': track_id
        }
        
        result = fence.check_detection(detection)
        dwell_time = fence.get_object_dwell_time(track_id)
        
        print(f"   時刻 {i+1}: 停留時間 = {dwell_time:.1f}s", end="")
        
        if result:
            print(f" ⚠️ 觸發警報！")
            triggered = True
        else:
            print(f" (未觸發)")
    
    if triggered:
        print("   ✅ 測試通過：成功在停留 3 秒後觸發")
    else:
        print("   ❌ 測試失敗：未觸發警報")
    
    # 清理
    fence.tracked_objects.clear()
    
    # 測試案例 2: 物件停留不足閾值
    print("\n📍 測試案例 2: 物件停留 2 秒後離開（不應觸發）")
    print("-" * 60)
    
    track_id = 2
    triggered = False
    
    for i in range(2):  # 停留 2 秒
        time.sleep(1)
        
        detection = {
            'class': 'person',
            'confidence': 0.8,
            'bbox': bbox,
            'track_id': track_id
        }
        
        result = fence.check_detection(detection)
        dwell_time = fence.get_object_dwell_time(track_id)
        
        print(f"   時刻 {i+1}: 停留時間 = {dwell_time:.1f}s (未觸發)")
        
        if result:
            triggered = True
    
    # 物件離開
    detection_out = {
        'class': 'person',
        'confidence': 0.8,
        'bbox': [500, 500, 600, 650],  # 在圍籬外
        'track_id': track_id
    }
    
    fence.check_detection(detection_out)
    print(f"   時刻 3: 物件離開圍籬")
    
    if not triggered:
        print("   ✅ 測試通過：未觸發警報（停留時間不足）")
    else:
        print("   ❌ 測試失敗：錯誤觸發警報")
    
    # 清理
    fence.tracked_objects.clear()
    
    # 測試案例 3: 多個物件同時追蹤
    print("\n📍 測試案例 3: 多個物件同時追蹤")
    print("-" * 60)
    
    # 物件 A 停留 2 秒
    # 物件 B 停留 4 秒
    
    track_a = 3
    track_b = 4
    bbox_a = [150, 150, 250, 300]
    bbox_b = [250, 150, 350, 300]
    
    triggered_a = False
    triggered_b = False
    
    for i in range(5):
        time.sleep(1)
        
        # 物件 A 只出現 2 秒
        if i < 2:
            detection_a = {
                'class': 'person',
                'confidence': 0.8,
                'bbox': bbox_a,
                'track_id': track_a
            }
            result_a = fence.check_detection(detection_a)
            if result_a:
                triggered_a = True
            
            dwell_a = fence.get_object_dwell_time(track_a)
            print(f"   時刻 {i+1}: 物件 A 停留 {dwell_a:.1f}s", end="")
        else:
            print(f"   時刻 {i+1}: 物件 A 已離開", end="")
        
        # 物件 B 出現 4 秒
        detection_b = {
            'class': 'person',
            'confidence': 0.8,
            'bbox': bbox_b,
            'track_id': track_b
        }
        result_b = fence.check_detection(detection_b)
        if result_b:
            triggered_b = True
        
        dwell_b = fence.get_object_dwell_time(track_b)
        print(f", 物件 B 停留 {dwell_b:.1f}s", end="")
        
        if result_b:
            print(" ⚠️ 物件 B 觸發！")
        else:
            print()
    
    print()
    if not triggered_a and triggered_b:
        print("   ✅ 測試通過：正確區分不同物件的停留時間")
    else:
        print("   ❌ 測試失敗：多物件追蹤錯誤")
    
    # 測試案例 4: 物件清理功能
    print("\n📍 測試案例 4: 過期物件自動清理")
    print("-" * 60)
    
    fence.tracked_objects.clear()
    
    # 創建一個物件記錄
    old_track_id = 5
    detection = {
        'class': 'person',
        'confidence': 0.8,
        'bbox': bbox,
        'track_id': old_track_id
    }
    
    fence.check_detection(detection)
    print(f"   - 創建物件記錄，追蹤 ID: {old_track_id}")
    print(f"   - 當前追蹤物件數量: {len(fence.tracked_objects)}")
    
    # 等待超過 timeout 時間
    print(f"   - 等待 {fence.object_timeout + 1} 秒...")
    time.sleep(fence.object_timeout + 1)
    
    # 執行清理
    fence.cleanup_old_objects()
    print(f"   - 執行清理後，追蹤物件數量: {len(fence.tracked_objects)}")
    
    if len(fence.tracked_objects) == 0:
        print("   ✅ 測試通過：成功清理過期物件")
    else:
        print("   ❌ 測試失敗：未清理過期物件")
    
    # 總結
    print("\n" + "=" * 60)
    print("測試完成！")
    print("=" * 60)


def test_fence_manager():
    """測試圍籬管理器功能"""
    
    print("\n" + "=" * 60)
    print("圍籬管理器測試")
    print("=" * 60)
    
    manager = VirtualFenceManager()
    
    # 創建多個圍籬
    fence1 = VirtualFence(
        fence_id="f1",
        name="圍籬 1",
        points=[(0, 0), (100, 0), (100, 100), (0, 100)],
        dwell_time_threshold=2.0
    )
    
    fence2 = VirtualFence(
        fence_id="f2",
        name="圍籬 2",
        points=[(200, 0), (300, 0), (300, 100), (200, 100)],
        dwell_time_threshold=5.0
    )
    
    manager.add_fence(fence1)
    manager.add_fence(fence2)
    
    print(f"\n✅ 已添加 {len(manager.fences)} 個圍籬")
    
    # 測試回調函數
    callback_triggered = []
    
    def test_callback(intrusion):
        callback_triggered.append(intrusion)
        print(f"\n📢 回調觸發！")
        print(f"   圍籬: {intrusion['fence_name']}")
        print(f"   停留時間: {intrusion['dwell_time']:.1f}s")
    
    manager.register_intrusion_callback(test_callback)
    
    # 模擬偵測
    print("\n模擬偵測序列...")
    
    detections = [{
        'class': 'person',
        'confidence': 0.8,
        'bbox': [50, 50, 80, 90],
        'track_id': 1
    }]
    
    for i in range(3):
        time.sleep(1)
        print(f"   時刻 {i+1}...", end=" ")
        intrusions = manager.check_detections(detections)
        if intrusions:
            print(f"發現 {len(intrusions)} 個入侵")
        else:
            print("無入侵")
    
    if len(callback_triggered) > 0:
        print("\n✅ 測試通過：回調函數正常工作")
    else:
        print("\n❌ 測試失敗：回調函數未觸發")


if __name__ == "__main__":
    try:
        # 執行測試
        test_dwell_time_tracking()
        test_fence_manager()
        
        print("\n" + "=" * 60)
        print("所有測試完成！")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n測試中斷")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ 測試過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
