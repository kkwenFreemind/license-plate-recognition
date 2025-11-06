# 電子圍籬停留時間偵測功能說明

## 📋 功能概述

電子圍籬現在支援**停留時間閾值**功能，可以設定物件必須在禁止區域內停留達到指定時間（例如 3 秒）才觸發警報事件，有效減少誤報。

## ✨ 主要特點

1. **物件追蹤**：使用 YOLO 的追蹤功能，為每個物件分配唯一的 ID
2. **停留時間累計**：精確計算物件在區域內的停留時間
3. **可設定閾值**：可為每個圍籬設定不同的停留時間閾值
4. **視覺化回饋**：顯示即時停留時間和進度條
5. **狀態追蹤**：自動追蹤物件進入、停留、離開的狀態

## 🚀 快速開始

### 1. 基本使用

```python
from modules.virtual_fence import VirtualFence, VirtualFenceManager

# 創建圍籬管理器
fence_manager = VirtualFenceManager()

# 創建帶停留時間閾值的圍籬
fence = VirtualFence(
    fence_id="fence_001",
    name="禁止停留區",
    points=[(100, 100), (500, 100), (500, 400), (100, 400)],
    target_classes=["person", "car"],
    min_confidence=0.5,
    dwell_time_threshold=3.0  # 停留 3 秒才觸發
)

fence_manager.add_fence(fence)
```

### 2. 配置文件方式

在 `config/config.yaml` 中設定：

```yaml
virtual_fences:
  fences:
    - id: "fence_001"
      name: "倉庫禁區"
      points: [[100, 100], [500, 100], [500, 400], [100, 400]]
      target_classes: ["person"]
      min_confidence: 0.6
      dwell_time_threshold: 3.0  # 新增：停留時間閾值（秒）
    
    - id: "fence_002"
      name: "車輛禁停區"
      points: [[600, 100], [900, 100], [900, 400], [600, 400]]
      target_classes: ["car", "truck"]
      min_confidence: 0.5
      dwell_time_threshold: 5.0  # 車輛需要停留 5 秒
```

### 3. 在偵測系統中使用

```python
from ultralytics import YOLO
from modules.virtual_fence import VirtualFenceManager

# 初始化模型
model = YOLO('yolov8n.pt')

# 創建圍籬管理器
fence_manager = VirtualFenceManager()
# ... 載入圍籬配置

while True:
    # 讀取影像
    ret, frame = cap.read()
    
    # 重要：使用 track() 方法（而非 predict()）
    # track() 會自動為物件分配追蹤 ID
    results = model.track(frame, persist=True, verbose=False)
    
    # 轉換格式
    detections = []
    if results and len(results) > 0:
        result = results[0]
        if result.boxes is not None and result.boxes.id is not None:
            for box, cls, conf, track_id in zip(
                result.boxes.xyxy.cpu().numpy(),
                result.boxes.cls.cpu().numpy(),
                result.boxes.conf.cpu().numpy(),
                result.boxes.id.cpu().numpy()
            ):
                detections.append({
                    'class': model.names[int(cls)],
                    'confidence': float(conf),
                    'bbox': box.tolist(),
                    'track_id': int(track_id)  # 關鍵：追蹤 ID
                })
    
    # 檢查圍籬入侵（自動處理停留時間）
    intrusions = fence_manager.check_detections(detections)
    
    # 繪製圍籬（會顯示停留時間和進度條）
    fence_manager.draw_all_fences(frame)
```

## 📊 工作原理

### 停留時間追蹤流程

```
物件首次進入區域
    ↓
記錄開始時間，建立追蹤記錄
    ↓
物件持續在區域內
    ↓
累計停留時間 = 當前時間 - 開始時間
    ↓
停留時間 >= 閾值？
    ↓
是 → 觸發警報事件
否 → 繼續追蹤
    ↓
物件離開區域
    ↓
標記為離開狀態（但保留記錄）
    ↓
超過 2 秒未再出現
    ↓
清除追蹤記錄
```

### 資料結構

每個被追蹤的物件會記錄以下資訊：

```python
{
    'in_zone': True,              # 是否在區域內
    'first_seen': 1234567890.0,   # 首次進入時間戳
    'last_seen': 1234567893.0,    # 最後一次出現時間戳
    'dwell_time': 3.0,            # 累計停留時間（秒）
    'triggered': True,            # 是否已觸發警報
    'object_class': 'person',     # 物件類別
    'last_bbox': [x1, y1, x2, y2] # 最後的邊界框位置
}
```

## 🎨 視覺化功能

### 進度條顯示

當物件在區域內但尚未觸發時：
- **橙色進度條**：顯示當前停留進度
- **時間文字**：顯示已停留的秒數

當物件已觸發警報後：
- **紅色進度條**：表示已觸發
- **紅色時間文字**：持續顯示停留時間

### 圍籬標籤

圍籬名稱旁會顯示閾值時間，例如：
```
禁止停留區 (3.0s)
```

## ⚙️ 參數說明

### VirtualFence 參數

| 參數 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| `fence_id` | str | - | 圍籬唯一識別碼 |
| `name` | str | - | 圍籬顯示名稱 |
| `points` | List[Tuple[int, int]] | - | 多邊形頂點座標 |
| `target_classes` | List[str] | None | 目標物件類型（None=所有類型）|
| `min_confidence` | float | 0.5 | 最小信心度閾值 |
| `dwell_time_threshold` | float | 0.0 | **停留時間閾值（秒）** |

### 特殊值說明

- `dwell_time_threshold = 0.0`：立即觸發（預設行為）
- `dwell_time_threshold > 0.0`：必須停留達到指定時間才觸發

## 📝 入侵事件格式

當觸發警報時，會產生以下格式的事件：

```python
{
    'fence_id': 'fence_001',
    'fence_name': '禁止停留區',
    'object_class': 'person',
    'confidence': 0.85,
    'bbox': [100, 150, 200, 300],
    'track_id': 42,
    'timestamp': '2025-11-06T10:30:45.123456',
    'event_type': 'intrusion',
    'dwell_time': 3.2,              # 實際停留時間
    'dwell_time_threshold': 3.0     # 設定的閾值
}
```

## 🔧 進階功能

### 1. 取得物件停留時間

```python
# 取得特定物件在圍籬內的停留時間
dwell_time = fence.get_object_dwell_time(track_id=42)
print(f"物件 42 已停留 {dwell_time:.1f} 秒")
```

### 2. 手動清理過期物件

```python
# 清理 2 秒內未出現的物件記錄
fence.cleanup_old_objects()
```

### 3. 自訂回調函數

```python
def custom_callback(intrusion_event):
    """自訂入侵處理"""
    # 發送通知
    send_notification(intrusion_event)
    
    # 記錄到資料庫
    db.save_intrusion(intrusion_event)
    
    # 觸發警報
    if intrusion_event['dwell_time'] > 5.0:
        trigger_alarm()

fence_manager.register_intrusion_callback(custom_callback)
```

## 🎯 使用場景

### 1. 倉庫禁區監控
```python
# 人員不得在危險區域停留超過 3 秒
fence = VirtualFence(
    fence_id="warehouse_001",
    name="危險物品區",
    points=danger_zone_points,
    target_classes=["person"],
    dwell_time_threshold=3.0
)
```

### 2. 車輛禁停監控
```python
# 車輛不得停留超過 10 秒
fence = VirtualFence(
    fence_id="parking_001",
    name="消防通道",
    points=fire_lane_points,
    target_classes=["car", "truck", "bus"],
    dwell_time_threshold=10.0
)
```

### 3. 機器操作安全區
```python
# 人員接近機器超過 2 秒發出警告
fence = VirtualFence(
    fence_id="machine_001",
    name="機器危險區",
    points=machine_zone_points,
    target_classes=["person"],
    dwell_time_threshold=2.0
)
```

## ⚠️ 注意事項

1. **必須使用物件追蹤**
   - 使用 `model.track()` 而非 `model.predict()`
   - 必須傳入 `track_id` 才能正確追蹤停留時間

2. **追蹤 ID 的持續性**
   - 使用 `persist=True` 參數確保追蹤 ID 在幀之間保持一致
   - 如果物件被遮擋後重新出現，可能會分配新的 ID

3. **效能考量**
   - 追蹤功能會稍微增加計算量
   - 建議使用較輕量的模型（如 YOLOv8n）

4. **閾值設定建議**
   - 太短（< 1 秒）：可能仍有誤報
   - 太長（> 10 秒）：反應過慢
   - 建議範圍：2-5 秒

## 🔍 故障排除

### 問題：無法追蹤停留時間

**原因**：未使用追蹤功能或未傳入 `track_id`

**解決方案**：
```python
# ❌ 錯誤：使用 predict
results = model.predict(frame)

# ✅ 正確：使用 track
results = model.track(frame, persist=True)

# ✅ 確保 detection 包含 track_id
detection = {
    'class': 'person',
    'confidence': 0.85,
    'bbox': [100, 150, 200, 300],
    'track_id': 42  # 必須包含
}
```

### 問題：物件 ID 頻繁變更

**原因**：追蹤不穩定或物件被遮擋

**解決方案**：
1. 提高 `min_confidence` 閾值
2. 使用更好的追蹤算法（如 BoT-SORT）
3. 調整攝影機角度減少遮擋

### 問題：進度條不顯示

**原因**：`dwell_time_threshold` 設為 0 或視覺化功能關閉

**解決方案**：
```python
# 確保設定閾值 > 0
fence.dwell_time_threshold = 3.0

# 確保開啟視覺化
fence.draw_on_frame(frame, show_dwell_time=True)
```

## 📚 完整範例

請參考 `examples/dwell_time_example.py` 獲取完整的可執行範例。

執行方式：
```bash
python examples/dwell_time_example.py
```

## 🔗 相關文件

- [虛擬圍籬基礎指南](VIRTUAL_FENCE_GUIDE.md)
- [事件處理指南](FENCE_EVENT_GUIDE.md)
- [Web 監控介面指南](WEB_DEMO_GUIDE.md)

## 💡 技術支援

如有問題或建議，請聯繫開發團隊或提交 Issue。
