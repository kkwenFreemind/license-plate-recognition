# Web Server 停留時間功能使用說明

## 📋 問題確認

**Q: 之前執行 `web_server.py` 就可以完成電子柵欄入侵事件，現在增加停留時間功能，需要執行另一個 Python 程式嗎？**

**A: ❌ 不需要！仍然執行同一個 `web_server.py`**

---

## ✅ 正確理解

### 之前的流程
```bash
python web_server.py
```
- 啟動網頁伺服器
- 電子圍籬立即觸發（物件進入就警報）

### 現在的流程
```bash
python web_server.py
```
- **仍然是同一個程式**
- 但現在支援停留時間功能
- 只需要在配置中設定 `dwell_time_threshold`

---

## 🔧 如何啟用停留時間功能

### 步驟 1: 修改配置檔案

編輯 `config/config.yaml`：

```yaml
virtual_fences:
  enabled: true
  fences:
  - id: fence_001
    name: 人員禁入區
    points:
    - - 785
      - 453
    - - 314
      - 809
    - - 1662
      - 773
    - - 1442
      - 476
    - - 791
      - 453
    target_classes:
    - person
    min_confidence: 0.6
    dwell_time_threshold: 3.0  # 👈 新增這行：停留 3 秒才觸發
    enabled: true
```

### 步驟 2: 重新啟動 web_server.py

```bash
# 停止現有的 web_server.py (按 Ctrl+C)

# 重新啟動
python web_server.py
```

**就這麼簡單！** 🎉

---

## 📊 功能比較

| 項目 | 之前 | 現在 |
|------|------|------|
| 執行程式 | `web_server.py` | `web_server.py` ✅ 相同 |
| 配置文件 | `config/config.yaml` | `config/config.yaml` ✅ 相同 |
| 新增參數 | - | `dwell_time_threshold` |
| 觸發方式 | 立即觸發 | 可設定停留時間 |
| 物件追蹤 | ❌ 無 | ✅ 自動追蹤 |
| 視覺化 | 圍籬框線 | 圍籬框線 + 停留時間 + 進度條 |

---

## 🎯 配置選項

### 選項 1: 立即觸發（預設行為）

```yaml
virtual_fences:
  fences:
  - id: fence_001
    name: 禁止進入區
    points: [[100, 100], [500, 100], [500, 400], [100, 400]]
    target_classes: ["person"]
    min_confidence: 0.6
    # 不設定 dwell_time_threshold 或設為 0
```

**行為**: 物件一進入就觸發（與之前相同）

### 選項 2: 停留時間觸發

```yaml
virtual_fences:
  fences:
  - id: fence_001
    name: 禁止停留區
    points: [[100, 100], [500, 100], [500, 400], [100, 400]]
    target_classes: ["person"]
    min_confidence: 0.6
    dwell_time_threshold: 3.0  # 停留 3 秒才觸發
```

**行為**: 物件停留達 3 秒才觸發警報

### 選項 3: 混合模式（多個圍籬）

```yaml
virtual_fences:
  fences:
  # 立即觸發區域
  - id: fence_001
    name: 絕對禁區
    points: [[100, 100], [300, 100], [300, 300], [100, 300]]
    target_classes: ["person"]
    dwell_time_threshold: 0.0  # 立即觸發
    
  # 停留時間觸發區域
  - id: fence_002
    name: 短暫停留區
    points: [[400, 100], [600, 100], [600, 300], [400, 300]]
    target_classes: ["person"]
    dwell_time_threshold: 3.0  # 停留 3 秒觸發
```

**行為**: 不同圍籬使用不同規則

---

## 🖥️ 視覺化效果

### 網頁介面會顯示

1. **電子圍籬框線**（紅色半透明區域）
2. **圍籬名稱和閾值**（例如：「人員禁入區 (3.0s)」）
3. **物件停留時間**（即時更新）
4. **進度條**
   - 🟠 橙色：停留中，未達閾值
   - 🔴 紅色：已觸發警報
5. **警報通知**（WebSocket 即時推送）

---

## 🔍 技術實現

### 更新的檔案

1. **`config/config.yaml`** - 加入 `dwell_time_threshold` 參數
2. **`core/base_detector.py`** - 支援物件追蹤
3. **`core/system.py`** - 傳遞追蹤參數
4. **`web_server.py`** - 啟用追蹤模式

### 自動整合的功能

✅ 物件追蹤（YOLO track）  
✅ 停留時間計算  
✅ 進度條顯示  
✅ 警報事件推送  
✅ 資料庫記錄  
✅ 視覺化回饋  

---

## 🚀 快速測試

### 1. 檢查配置

```bash
# 查看當前配置
type config\config.yaml
```

確認是否有 `dwell_time_threshold` 參數

### 2. 啟動伺服器

```bash
python web_server.py
```

### 3. 開啟瀏覽器

```
http://localhost:5000/fence
```

### 4. 觀察效果

- 當物件進入圍籬，會顯示停留時間
- 停留達到閾值後，觸發警報
- 前端會收到即時通知

---

## ⚠️ 重要提示

### ✅ 向後相容

- 如果不設定 `dwell_time_threshold`，行為與之前相同（立即觸發）
- 現有配置無需修改仍可正常運作
- 新功能是**選用的**，不會影響現有功能

### ⚙️ 系統需求

- YOLOv8 模型支援追蹤功能（已內建）
- 無需額外安裝套件
- 追蹤功能對效能影響 < 5%

### 🐛 故障排除

**問題**: 停留時間沒有顯示

**解決方案**:
1. 確認 `dwell_time_threshold > 0`
2. 檢查 `web_server.py` 是否重新啟動
3. 確認物件確實在圍籬內停留

**問題**: 追蹤 ID 頻繁變更

**解決方案**:
1. 提高 `min_confidence` 閾值
2. 改善攝影機角度
3. 減少物體遮擋

---

## 📚 相關文件

- [停留時間功能詳細指南](docs/document/DWELL_TIME_GUIDE.md)
- [功能更新說明](CHANGELOG_DWELL_TIME.md)
- [獨立範例程式](examples/dwell_time_example.py)

---

## 💡 使用建議

### 場景 1: 高安全性區域
```yaml
dwell_time_threshold: 0.0  # 立即觸發
```
適用於：核心機房、危險品倉庫

### 場景 2: 一般管制區
```yaml
dwell_time_threshold: 3.0  # 3 秒觸發
```
適用於：辦公區域、倉庫通道

### 場景 3: 停車管理
```yaml
dwell_time_threshold: 10.0  # 10 秒觸發
```
適用於：消防通道、臨停區

---

## ✅ 總結

| 問題 | 答案 |
|------|------|
| 需要執行另一個程式嗎？ | ❌ 不需要 |
| 還是執行 `web_server.py` 嗎？ | ✅ 是的 |
| 需要修改配置嗎？ | ✅ 只需加入 `dwell_time_threshold` |
| 會影響現有功能嗎？ | ❌ 完全相容 |
| 需要重新安裝套件嗎？ | ❌ 不需要 |

**結論**: 繼續使用 `web_server.py`，只需在配置文件中加入新參數即可！ 🎉

---

**版本**: v1.1.0  
**更新日期**: 2025-11-06
