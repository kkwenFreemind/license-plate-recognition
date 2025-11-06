# ✅ 安裝完成總結

## 🎉 成功安裝的套件 (Python 3.13)

所有套件都已成功安裝到虛擬環境：
```
D:\SideProject\cctv\license-plate-recognition\venv\Lib\site-packages\
```

**已安裝的核心套件：**
- ✅ **NumPy 2.2.6** - 數值運算
- ✅ **OpenCV 4.12.0** - 影像處理  
- ✅ **PyTorch 2.9.0+cpu** - 深度學習框架
- ✅ **Ultralytics 8.3.225** - YOLO v8
- ✅ **EasyOCR 1.7.2** - 車牌 OCR 辨識
- ✅ **psycopg2-binary 2.9.11** - PostgreSQL 驅動
- ✅ **PyYAML 6.0.3** - 配置管理
- ✅ **python-dotenv 1.2.1** - 環境變數

## 📁 已建立的檔案

- ✅ config.yaml - 主配置檔
- ✅ .env - 環境變數檔
- ✅ yolov8n.pt - YOLO 模型 (6.2 MB)

---

## 🚀 下一步操作

### 1. 編輯資料庫密碼 (必須)

```powershell
notepad .env
```

將以下內容改為您的 PostgreSQL 密碼：
```env
DB_PASSWORD=your_db_password_here  # ← 改成實際密碼
```

#### 2. 編輯攝影機設定 (如果要測試 RTSP)

```powershell
notepad config\config.yaml
```

修改 RTSP URL：
```yaml
cameras:
  - id: "CAM_001"
    name: "大門入口"
    rtsp_url: "rtsp://admin:password@192.168.1.100:554/stream1"  # ← 改成實際 URL
    enabled: true  # ← 如果沒有攝影機可以先設為 false
```

#### 3. 初始化資料庫

```powershell
python database\init_db.py
```

#### 4. 執行系統

```powershell
python main.py
```

---

### 💡 重要提醒

1. **虛擬環境啟動**：每次開啟新終端都需要執行
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
   提示符應該顯示 `(venv)`

2. **套件位置**：所有套件都在 venv 資料夾內，不會影響系統 Python

3. **YOLO 模型**：首次執行會自動下載語言模型（可能較大）

4. **測試模式**：如果還沒有 RTSP 攝影機，可以先用圖片測試

---

### 🎯 快速測試（無攝影機）



Made changes.