# 車牌辨識系統實作計畫

## 專案概述

建立一個模組化的 CCTV 物件辨識系統，採用 YOLO + 細部辨識的兩階段架構，支援 RTSP 串流處理與資料庫整合。

---

## Phase 0: 環境建置 (預計 0.5 天)

### ✅ PostgreSQL (已完成)

### 安裝 Python 套件

```powershell
# 啟動虛擬環境 (建議)
python -m venv venv
.\venv\Scripts\Activate.ps1

# 安裝所有依賴
pip install -r requirements.txt

# 驗證安裝
python tests/verify_installation.py
```

**檢查點:**
- [ ] 虛擬環境建立
- [ ] 所有套件安裝完成
- [ ] YOLO 模型下載成功
- [ ] PostgreSQL 連線測試通過

---

## Phase 1: 核心架構建立 (預計 1 天)

### 任務清單

1. **配置系統設定**
   - [ ] 複製 `config/config.example.yaml` 為 `config/config.yaml`
   - [ ] 複製 `.env.example` 為 `.env`
   - [ ] 填入實際的資料庫密碼和 RTSP URL

2. **初始化資料庫**
   ```powershell
   python database/init_db.py
   ```

3. **測試基礎功能**
   ```powershell
   # 測試 YOLO 偵測
   python tests/test_detector.py
   
   # 測試車牌辨識
   python tests/test_license_plate.py
   ```

**檢查點:**
- [ ] 配置檔案設定完成
- [ ] 資料庫表格建立成功
- [ ] 基礎偵測功能正常
- [ ] 車牌辨識模組正常

---

## Phase 2: RTSP 串流處理 (預計 0.5 天)

### 任務清單

1. **配置攝影機資訊**
   - 編輯 `config/config.yaml` 中的 cameras 區段
   - 填入正確的 RTSP URL

2. **測試 RTSP 連線**
   ```powershell
   python tests/test_rtsp.py
   ```

3. **執行主程式**
   ```powershell
   python main.py
   ```

**檢查點:**
- [ ] RTSP 連線成功
- [ ] 影像讀取正常
- [ ] 多執行緒運作穩定
- [ ] 結果正確寫入資料庫

---

## Phase 3: 測試與優化 (預計 1 天)

### 任務清單

1. **效能測試**
   - 監控 CPU/記憶體使用
   - 檢查處理速度 (FPS)
   - 調整 `process_interval` 參數

2. **辨識準確度測試**
   - 收集測試影像
   - 驗證車牌辨識準確率
   - 調整信心度閾值

3. **長時間運行測試**
   - 24 小時穩定性測試
   - 檢查記憶體洩漏
   - 檢查資料庫效能

**檢查點:**
- [ ] FPS 達到要求 (≥ 0.5 fps per camera)
- [ ] 車牌辨識率 > 80%
- [ ] 系統穩定運行 24 小時
- [ ] 資料庫查詢效能良好

---

## Phase 4: 部署與監控 (預計 0.5 天)

### 任務清單

1. **設定為 Windows 服務 (選用)**
   ```powershell
   python setup_service.py
   ```

2. **設定日誌輪替**
   - 已內建於系統中
   - 檢查 `logs/` 目錄

3. **監控儀表板 (選用)**
   - 安裝 Grafana + Prometheus
   - 或使用簡單的 Web 介面

**檢查點:**
- [ ] 系統自動啟動
- [ ] 日誌正常記錄
- [ ] 監控系統運作
- [ ] 告警機制設定

---

## 快速開始指令

```powershell
# 1. 安裝依賴
pip install -r requirements.txt

# 2. 設定配置
copy config\config.example.yaml config\config.yaml
copy .env.example .env
# 編輯 config.yaml 和 .env

# 3. 初始化資料庫
python database\init_db.py

# 4. 測試安裝
python tests\verify_installation.py

# 5. 執行系統
python main.py
```

---

## 目錄結構

```
license-plate-recognition/
├── config/
│   ├── config.yaml           # 主要配置
│   └── config.example.yaml   # 配置範本
├── core/
│   ├── base_detector.py      # YOLO 偵測器
│   ├── recognizer_base.py    # 辨識模組基類
│   └── system.py             # 主系統
├── modules/
│   ├── license_plate.py      # 車牌辨識
│   └── face_recognition.py   # 人臉辨識 (選用)
├── database/
│   ├── handler.py            # 資料庫處理
│   └── init_db.py            # 初始化腳本
├── utils/
│   ├── config_manager.py     # 配置管理
│   ├── performance.py        # 效能監控
│   └── logger.py             # 日誌工具
├── tests/
│   ├── verify_installation.py
│   ├── test_detector.py
│   └── test_license_plate.py
├── models/                   # YOLO 模型
├── logs/                     # 日誌檔案
├── main.py                   # 主程式
├── requirements.txt
├── .env.example
└── README.md
```

---

## 常見問題

### Q: RTSP 連線失敗？
```powershell
# 測試 RTSP URL
ffplay rtsp://your_rtsp_url
```

### Q: 車牌辨識率低？
- 調整 `min_confidence` (降低閾值)
- 啟用 `multi_zone_search`
- 改善攝影機角度和光線

### Q: 記憶體使用過高？
- 降低 `frame_queue` 大小
- 增加 `process_interval`
- 調整影像解析度

### Q: 資料庫寫入慢？
- 啟用批次寫入
- 增加資料庫連線池
- 檢查索引是否建立

---

## 後續擴展

- [ ] 增加人臉辨識模組
- [ ] 增加異常偵測 (人員跌倒、闖入等)
- [ ] Web 管理介面
- [ ] 即時告警功能 (Email/LINE)
- [ ] 影片錄製功能
- [ ] 多攝影機同步處理

---

## 技術支援

- YOLO 文件: https://docs.ultralytics.com/
- EasyOCR 文件: https://github.com/JaidedAI/EasyOCR
- OpenCV 文件: https://docs.opencv.org/
