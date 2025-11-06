# 快速開始指南

## 🚀 5 分鐘快速啟動

### Step 1: 安裝依賴 (2 分鐘)

```powershell
# 自動安裝腳本 (推薦)
.\install.ps1

# 或手動安裝
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Step 2: 設定配置 (2 分鐘)

```powershell
# 複製配置檔案
copy config\config.example.yaml config\config.yaml
copy .env.example .env

# 編輯資料庫密碼
notepad .env
# 填入: DB_PASSWORD=你的PostgreSQL密碼

# 編輯攝影機設定
notepad config\config.yaml
# 修改 cameras 區段的 rtsp_url
```

**config.yaml 關鍵設定:**

```yaml
cameras:
  - id: "CAM_001"
    name: "大門入口"
    rtsp_url: "rtsp://admin:password@192.168.1.100:554/stream1"  # ← 修改這裡
    enabled: true
    process_interval: 2.0

database:
  host: "localhost"      # ← PostgreSQL 主機
  database: "surveillance"  # ← 資料庫名稱
  user: "postgres"       # ← 使用者名稱
```

### Step 3: 初始化資料庫 (30 秒)

```powershell
python database\init_db.py
```

### Step 4: 驗證安裝 (30 秒)

```powershell
python tests\verify_installation.py
```

應該看到:
```
✓ NumPy
✓ OpenCV
✓ Ultralytics (YOLO)
✓ PyTorch
✓ EasyOCR
✓ PostgreSQL Driver
✓ YOLO 模型下載成功
🎉 所有必要套件已安裝!
```

### Step 5: 執行系統 (立即)

**方式 1: 命令列模式 (開發/除錯)**
```powershell
python main.py
```

**方式 2: 網頁展示模式 (Demo/展示) ⭐ 推薦**
```powershell
# 先安裝網頁依賴
pip install flask flask-socketio python-socketio eventlet

# 啟動網頁伺服器
python web_server.py
```

然後開啟瀏覽器：
```
http://localhost:5000
```

**網頁功能：**
- 📺 即時影像串流 + YOLO 物件框選
- 🎯 車牌辨識結果即時顯示
- 📊 統計資料（偵測總數、車牌數、成功率）
- 🎨 精美的視覺化介面
- 📱 響應式設計，手機也可觀看

**快速啟動腳本：**
```powershell
# 命令列模式
.\start.bat

# 網頁模式
.\start_web.bat
```

---

## 📋 完整安裝檢查清單

- [ ] Python 3.8+ 已安裝
- [ ] PostgreSQL 已安裝並執行
- [ ] 虛擬環境建立
- [ ] 所有套件安裝完成
- [ ] config.yaml 設定完成
- [ ] .env 資料庫密碼填入
- [ ] 資料庫初始化成功
- [ ] YOLO 模型下載完成
- [ ] RTSP URL 填入正確

---

## 🔧 常用指令

### 啟動系統
```powershell
# 啟動虛擬環境
.\venv\Scripts\Activate.ps1

# 執行主程式
python main.py
```

### 資料庫操作
```powershell
# 初始化資料庫
python database\init_db.py

# 查詢最近偵測 (使用 psql)
psql -U postgres -d surveillance
SELECT * FROM detections ORDER BY timestamp DESC LIMIT 10;
SELECT * FROM plate_records ORDER BY first_seen DESC LIMIT 10;
```

### 測試 RTSP 連線
```powershell
# 使用 ffplay 測試 (需安裝 ffmpeg)
ffplay rtsp://your_rtsp_url

# 使用 VLC 測試
vlc rtsp://your_rtsp_url
```

---

## 🐛 疑難排解

### 問題 1: pip 安裝失敗

**解決方法:**
```powershell
# 使用清華大學鏡像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 問題 2: torch 安裝失敗

**解決方法:**
```powershell
# 手動安裝 CPU 版本
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

### 問題 3: 資料庫連線失敗

**檢查項目:**
1. PostgreSQL 服務是否執行
2. 資料庫名稱是否存在
3. 使用者名稱密碼是否正確
4. .env 檔案是否設定

```powershell
# 檢查 PostgreSQL 服務
Get-Service postgresql*

# 測試連線
psql -U postgres -d surveillance
```

### 問題 4: RTSP 連線失敗

**檢查項目:**
1. RTSP URL 格式是否正確
2. 攝影機是否在線
3. 網路是否通暢
4. 使用者名稱密碼是否正確

```powershell
# 測試連線
ping 192.168.1.100
ffplay rtsp://admin:password@192.168.1.100:554/stream1
```

### 問題 5: 車牌辨識率低

**調整建議:**

1. 降低信心度閾值
```yaml
modules:
  license_plate:
    min_confidence: 0.2  # 預設 0.3
```

2. 改善攝影機設定
- 調整角度 (車牌正面朝向攝影機)
- 改善光線 (增加補光)
- 提高解析度

3. 調整處理間隔
```yaml
cameras:
  - process_interval: 1.0  # 更頻繁處理
```

---

## 📊 效能調優

### 降低 CPU 使用率
```yaml
cameras:
  - process_interval: 3.0  # 增加間隔

performance:
  enable_monitoring: false  # 關閉監控
```

### 降低記憶體使用
```python
# 在 core/system.py 修改
self.frame_queue = Queue(maxsize=3)  # 減少佇列大小
```

### 提高辨識速度
```yaml
yolo:
  model_path: "yolov8n.pt"  # 使用最小模型
  device: "cuda:0"          # 使用 GPU (如果有)
```

---

## 📈 監控與維護

### 查看日誌
```powershell
# 即時日誌
Get-Content logs\system.log -Wait -Tail 50

# 搜尋錯誤
Select-String -Path logs\system.log -Pattern "ERROR"
```

### 資料庫維護
```sql
-- 查看偵測統計
SELECT object_class, COUNT(*) 
FROM detections 
GROUP BY object_class;

-- 查看車牌統計
SELECT plate_number, count, first_seen, last_seen
FROM plate_records
ORDER BY count DESC
LIMIT 20;

-- 清理舊資料 (保留 30 天)
DELETE FROM detections 
WHERE timestamp < NOW() - INTERVAL '30 days';
```

---

## 🎯 下一步

1. **設定自動啟動** - 將系統設定為 Windows 服務
2. **增加告警功能** - Email/LINE 通知
3. **建立 Web 介面** - 查看即時影像和記錄
4. **增加其他模組** - 人臉辨識、異常偵測等

---

## 📞 取得協助

- 查看 README.md 詳細文件
- 查看 IMPLEMENTATION_PLAN.md 實作計畫
- 檢查 logs/ 目錄的日誌檔案

---

**注意**: 首次執行會下載 YOLO 模型和 EasyOCR 語言包，可能需要較長時間。
