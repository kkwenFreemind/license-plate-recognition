# 電子圍籬功能使用指南

## 📖 功能概述

電子圍籬（Virtual Fence）是一種虛擬的監控區域，當特定物件（如人員、車輛）進入或離開該區域時，系統會自動觸發警報。

### 主要特點：
- ✅ **多邊形區域定義**：支援任意形狀的圍籬
- ✅ **物件類型過濾**：只偵測特定類型的物件
- ✅ **信心度閾值**：避免誤報
- ✅ **即時警報**：透過 WebSocket 即時推送警報到前端
- ✅ **視覺化顯示**：在影像上繪製圍籬區域

---

## 🚀 快速開始

### 1. 啟用電子圍籬

編輯 `config/config.yaml`：

```yaml
virtual_fences:
  enabled: true  # 設定為 true 啟用功能
  fences:
    - id: "fence_001"
      name: "人員禁入區"
      points:
        - [200, 150]   # 左上角
        - [600, 150]   # 右上角
        - [600, 450]   # 右下角
        - [200, 450]   # 左下角
      target_classes: ["person"]
      min_confidence: 0.6
      enabled: true
```

### 2. 啟動系統

```cmd
start_web.bat
```

或

```cmd
python web_server.py
```

### 3. 查看結果

開啟瀏覽器：`http://localhost:5000`

- **左側影像**：可以看到紅色半透明的圍籬區域
- **右上統計**：顯示 🚨 圍籬警報 次數
- **右上角通知**：當有入侵時會彈出紅色警報通知

---

## ⚙️ 配置說明

### 圍籬參數

| 參數 | 說明 | 範例 |
|------|------|------|
| `id` | 圍籬唯一識別碼 | `"fence_001"` |
| `name` | 圍籬名稱（顯示用） | `"人員禁入區"` |
| `points` | 多邊形頂點座標 | `[[x1,y1], [x2,y2], ...]` |
| `target_classes` | 要偵測的物件類型 | `["person", "car"]` |
| `min_confidence` | 最小信心度（0-1） | `0.6` |
| `enabled` | 是否啟用此圍籬 | `true` / `false` |

### 支援的物件類型

常見的 YOLO 物件類型：

- **人員**：`person`
- **車輛**：`car`, `truck`, `bus`, `motorcycle`, `bicycle`
- **動物**：`dog`, `cat`, `bird`
- **其他**：查看 [COCO 資料集](https://cocodataset.org/#explore) 完整列表

### 座標系統

座標以**像素**為單位，原點 `(0, 0)` 在影像**左上角**：

```
(0,0) -------- X 軸 -------→
  |
  |
 Y軸
  |
  ↓
```

**如何獲取座標：**
1. 截圖一張影像
2. 使用畫圖工具（如 Paint）查看座標
3. 或使用滑鼠在影像上點擊（後續會提供互動工具）

---

## 📐 定義圍籬區域

### 方法 1：互動式圍籬工具（推薦）⭐

使用專用的圍籬建立工具，直接在影像上用滑鼠點選區域：

```cmd
python create_fence.py
```

**操作步驟：**

1. **執行工具**：工具會自動從 RTSP 抓取當前影像
2. **選取區域**：
   - 左鍵點擊：選擇圍籬多邊形的頂點（至少 3 個點）
   - 右鍵點擊：完成選取
   - 按 `R` 鍵：重置所有點，重新選擇
   - 按 `S` 鍵：儲存當前圍籬配置
   - 按 `ESC`：取消並退出

3. **設定資訊**：選擇完成後，工具會詢問：
   - 圍籬 ID（例如：`fence_001`）
   - 圍籬名稱（例如：`人員禁入區`）
   - 目標類型（例如：`person,car`）
   - 信心度閾值（例如：`0.6`）

4. **自動儲存**：工具會自動將配置寫入 `config/config.yaml`

5. **重啟伺服器**：執行 `start_web.bat` 或 `python web_server.py`

**優點：**
- ✅ 視覺化操作，不需要手動計算座標
- ✅ 即時預覽圍籬區域
- ✅ 支援任意多邊形形狀
- ✅ 自動儲存配置

### 方法 2：手動配置

如果已知座標，可以直接編輯 `config.yaml`：

```yaml
fences:
  - id: "fence_001"
    name: "大門入口"
    points:
      - [100, 100]   # 左上
      - [700, 100]   # 右上
      - [700, 500]   # 右下
      - [100, 500]   # 左下
    target_classes: ["person"]
    min_confidence: 0.6
    enabled: true
```

---

## 💡 使用範例

### 範例 1：辦公室禁入區

偵測人員進入機房或重要區域：

```yaml
- id: "server_room"
  name: "機房禁入區"
  points:
    - [300, 200]
    - [800, 200]
    - [800, 700]
    - [300, 700]
  target_classes: ["person"]  # 只偵測人員
  min_confidence: 0.7
  enabled: true
```

### 範例 2：車道逆向偵測

偵測車輛駛入逆向車道：

```yaml
- id: "wrong_way"
  name: "逆向車道"
  points:
    - [0, 300]
    - [400, 300]
    - [400, 600]
    - [0, 600]
  target_classes: ["car", "truck", "bus", "motorcycle"]
  min_confidence: 0.6
  enabled: true
```

### 範例 3：停車格占用偵測

偵測特定停車格是否有車輛：

```yaml
- id: "parking_spot_1"
  name: "停車格 A1"
  points:
    - [500, 400]
    - [650, 400]
    - [650, 550]
    - [500, 550]
  target_classes: ["car"]
  min_confidence: 0.5
  enabled: true
```

### 範例 4：全區域監控

偵測畫面中所有物件（不限類型）：

```yaml
- id: "full_area"
  name: "完整監控區"
  points:
    - [0, 0]
    - [1920, 0]
    - [1920, 1080]
    - [0, 1080]
  target_classes: []  # 空白表示所有類型
  min_confidence: 0.5
  enabled: true
```

---

## 🎨 視覺化效果

### 影像上的顯示

- **圍籬邊界**：紅色線條
- **圍籬區域**：紅色半透明填充（透明度 20%）
- **圍籬名稱**：顯示在區域中心

### 警報通知

當有物件入侵時：
1. **右上角彈出紅色通知**
   - 顯示物件類型、圍籬名稱
   - 顯示信心度和時間
   - 5 秒後自動消失

2. **統計數字更新**
   - 🚨 圍籬警報 計數器增加

3. **後端日誌**
   ```
   2025-11-06 13:45:23 - WebServer - WARNING - 🚨 電子圍籬警報: 人員禁入區 - person
   ```

---

## 🔧 進階功能

### 1. 自訂警報處理

編輯 `web_server.py` 中的 `on_intrusion` 回調函數：

```python
def on_intrusion(event):
    # 記錄到日誌
    logger.warning(f"🚨 電子圍籬警報: {event['fence_name']} - {event['object_class']}")
    
    # 發送到前端
    socketio.emit('fence_intrusion', event, namespace='/detections')
    
    # 額外處理（可選）
    # - 發送 Email 通知
    # - 觸發警報器
    # - 儲存截圖
    # - 發送 LINE 訊息
```

### 2. 儲存入侵事件到資料庫

創建資料表：

```sql
CREATE TABLE fence_intrusions (
    id SERIAL PRIMARY KEY,
    fence_id VARCHAR(50),
    fence_name VARCHAR(100),
    object_class VARCHAR(50),
    confidence FLOAT,
    bbox JSON,
    timestamp TIMESTAMP,
    camera_id VARCHAR(50)
);
```

在回調中儲存：

```python
def on_intrusion(event):
    if db_handler:
        db_handler.save_intrusion(event)
```

### 3. 多個圍籬同時使用

可以定義多個圍籬，每個圍籬獨立運作：

```yaml
virtual_fences:
  enabled: true
  fences:
    - id: "fence_001"
      name: "A 區禁入"
      points: [[100,100], [400,100], [400,400], [100,400]]
      target_classes: ["person"]
      
    - id: "fence_002"
      name: "B 區禁行"
      points: [[500,100], [800,100], [800,400], [500,400]]
      target_classes: ["car", "truck"]
      
    - id: "fence_003"
      name: "C 區全監控"
      points: [[100,500], [800,500], [800,800], [100,800]]
      target_classes: []  # 所有物件
```

---

## 🐛 疑難排解

### Q1: 圍籬沒有顯示在影像上

**檢查：**
1. `config.yaml` 中 `virtual_fences.enabled` 是否為 `true`
2. 各圍籬的 `enabled` 是否為 `true`
3. 座標是否在影像範圍內

### Q2: 明明有物件進入，但沒有警報

**檢查：**
1. `target_classes` 是否包含該物件類型
2. `min_confidence` 是否設定太高
3. 查看後端日誌是否有偵測到物件

**調整信心度：**
```yaml
min_confidence: 0.5  # 降低閾值
```

### Q3: 誤報太多

**調整方式：**
1. 提高 `min_confidence`：`0.7` 或 `0.8`
2. 限縮 `target_classes`：只偵測特定類型
3. 縮小圍籬範圍

### Q4: 想知道影像尺寸

查看日誌或執行：

```python
import cv2
cap = cv2.VideoCapture("rtsp://your_url")
ret, frame = cap.read()
print(f"影像尺寸: {frame.shape[1]} x {frame.shape[0]}")
```

---

## 📊 效能考量

### 建議：

- **圍籬數量**：建議不超過 5 個
- **多邊形複雜度**：頂點數不超過 10 個
- **處理間隔**：`process_interval: 1.0` 或更高

### 如果效能不足：

1. 減少圍籬數量
2. 增加 `process_interval`
3. 提高 YOLO `confidence_threshold`
4. 簡化多邊形形狀

---

## 🎯 最佳實踐

1. **先測試後上線**
   - 使用錄影檔測試配置
   - 確認座標正確
   - 調整信心度閾值

2. **合理設定閾值**
   - 室內環境：`min_confidence: 0.7`
   - 室外環境：`min_confidence: 0.5`

3. **明確的圍籬命名**
   - 使用描述性名稱：`"大門入口"`, `"停車場 A 區"`
   - 避免：`"fence_001"`, `"test"`

4. **定期檢視警報**
   - 查看是否有誤報
   - 調整配置參數

---

## 🔗 相關文檔

- [QUICKSTART.md](QUICKSTART.md) - 快速開始指南
- [WEB_DEMO_GUIDE.md](WEB_DEMO_GUIDE.md) - 網頁展示指南
- [config.example.yaml](config/config.example.yaml) - 配置範本

---

**注意**：座標系統以像素為單位，請根據您的實際影像尺寸調整！
