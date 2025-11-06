# 🚀 快速啟動指南

## 📝 批次檔說明

本專案提供了多個 `.bat` 批次檔，方便您快速執行各種操作。

---

## 🎯 使用順序

### 第一次安裝

```batch
1. install.bat        # 安裝所有依賴
2. install_gpu.bat    # (可選) 安裝 GPU 版本 PyTorch
3. verify.bat         # 驗證安裝是否成功
4. init_db.bat        # 初始化資料庫
5. start.bat          # 啟動系統
```

### 日常使用

```batch
start.bat            # 直接啟動系統
```

---

## 📂 批次檔清單

### 🔧 install.bat - 安裝依賴
**功能：** 建立虛擬環境並安裝所有 Python 套件

**使用方式：**
```batch
雙擊 install.bat
```

**或命令列：**
```cmd
install.bat
```

---

### ⚡ install_gpu.bat - 安裝 GPU 加速
**功能：** 安裝 CUDA 版本的 PyTorch，啟用 GPU 加速

**使用方式：**
```batch
雙擊 install_gpu.bat
```

**注意：**
- 需要 NVIDIA GPU
- 下載約 2.8 GB，需要時間
- 執行後會自動驗證 CUDA 是否可用

---

### ✅ verify.bat - 驗證安裝
**功能：** 檢查所有套件是否正確安裝

**使用方式：**
```batch
雙擊 verify.bat
```

**應該看到：**
```
✓ NumPy
✓ OpenCV
✓ Ultralytics (YOLO)
✓ PyTorch
✓ EasyOCR
✓ PostgreSQL Driver
🎉 所有必要套件已安裝!
```

---

### 🗄️ init_db.bat - 初始化資料庫
**功能：** 建立資料庫表格結構

**使用方式：**
```batch
雙擊 init_db.bat
```

**前置條件：**
- PostgreSQL 已安裝並執行
- `config.yaml` 已設定
- `.env` 已填入資料庫密碼

---

### 🚀 start.bat - 啟動系統（命令列模式）
**功能：** 啟動車牌辨識系統（命令列輸出）

**使用方式：**
```batch
雙擊 start.bat
```

**或命令列：**
```cmd
start.bat
```

**停止方式：**
- 按 `Ctrl + C`
- 或直接關閉視窗

---

### 🌐 start_web.bat - 啟動系統（網頁展示模式）⭐
**功能：** 啟動網頁展示介面，適合 Demo 展示

**使用方式：**
```batch
雙擊 start_web.bat
```

**特色：**
- 📺 即時影像串流 + YOLO 框選
- 🎯 車牌辨識結果即時顯示
- 📊 統計資料（偵測數、成功率）
- 🎨 精美的視覺化介面

**訪問網址：**
```
http://localhost:5000
```

**停止方式：**
- 按 `Ctrl + C`
- 或直接關閉視窗

---

## 🔧 首次設定流程

### 1. 安裝依賴
```batch
install.bat
```

### 2. 設定配置檔案
```batch
# 複製配置範本
copy config\config.example.yaml config\config.yaml
copy .env.example .env

# 編輯配置
notepad .env              # 填入資料庫密碼
notepad config\config.yaml  # 設定攝影機 RTSP URL
```

### 3. (可選) 安裝 GPU 支援
```batch
install_gpu.bat
```

### 4. 驗證安裝
```batch
verify.bat
```

### 5. 初始化資料庫
```batch
init_db.bat
```

### 6. 啟動系統
```batch
start.bat
```

---

## 💡 常見問題

### Q: 雙擊批次檔沒反應？
**A:** 右鍵點擊 → 以系統管理員身分執行

### Q: 出現「找不到 Python」錯誤？
**A:** 確認 Python 已安裝並加入 PATH

### Q: 虛擬環境啟動失敗？
**A:** 
1. 刪除 `venv` 資料夾
2. 重新執行 `install.bat`

### Q: GPU 版本安裝失敗？
**A:** 
1. 確認有 NVIDIA GPU
2. 使用 CPU 版本：編輯 `config.yaml`
   ```yaml
   yolo:
     device: "cpu"
   modules:
     license_plate:
       gpu: false
   ```

---

## 🎯 進階使用

### 在命令列中使用

```cmd
# 進入專案目錄
cd D:\SideProject\cctv\license-plate-recognition

# 執行任一批次檔
start.bat
```

### 建立桌面捷徑

1. 右鍵點擊 `start.bat`
2. 選擇「建立捷徑」
3. 將捷徑移到桌面
4. 雙擊捷徑即可啟動系統

---

## 📞 取得協助

- 查看 `QUICKSTART.md` - 完整安裝指南
- 查看 `IMPLEMENTATION_PLAN.md` - 實作計畫
- 查看 `logs/system.log` - 系統日誌

---

**建議：** 第一次安裝請依照順序執行所有批次檔，確保系統正確設定。
