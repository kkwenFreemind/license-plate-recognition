# License Plate Recognition System

基於 YOLO 和 EasyOCR 的車牌辨識系統，支援 RTSP 串流處理與 PostgreSQL 資料庫整合。

## 功能特色

✅ **YOLO 物件偵測** - 自動偵測車輛 (汽車、卡車、公車、機車)  
✅ **車牌辨識** - 支援台灣車牌格式 (ABC-1234, 1234-AB, ABC-123)  
✅ **多區域搜尋** - 提高辨識準確率  
✅ **RTSP 串流處理** - 支援多攝影機同時處理  
✅ **非同步架構** - 多執行緒處理，效能優異  
✅ **資料庫整合** - PostgreSQL 儲存所有辨識結果  
✅ **模組化設計** - 易於擴展新功能  

## 系統架構

```
RTSP 串流 → YOLO 偵測 → 車牌辨識 → 資料庫儲存
              ↓
         多執行緒處理
              ↓
         效能監控 & 日誌
```

## 快速開始

### 1. 安裝依賴

```powershell
# 建立虛擬環境 (建議)
python -m venv venv
.\venv\Scripts\Activate.ps1

# 安裝套件
pip install -r requirements.txt
```

### 2. 設定配置

```powershell
# 複製配置範本
copy config\config.example.yaml config\config.yaml
copy .env.example .env

# 編輯 .env 填入資料庫密碼
notepad .env

# 編輯 config.yaml 設定攝影機資訊
notepad config\config.yaml
```

### 3. 初始化資料庫

```powershell
python database\init_db.py
```

### 4. 驗證安裝

```powershell
python tests\verify_installation.py
```

### 5. 執行系統

```powershell
python main.py
```

## 配置說明

### config/config.yaml

```yaml
yolo:
  model_path: "yolov8n.pt"      # YOLO 模型
  confidence_threshold: 0.5      # 信心度閾值
  device: "cpu"                  # 或 "cuda:0"

cameras:
  - id: "CAM_001"
    name: "大門入口"
    rtsp_url: "rtsp://..."       # RTSP URL
    enabled: true
    modules: ["license_plate"]
    process_interval: 2.0        # 處理間隔(秒)

database:
  enabled: true
  host: "localhost"
  port: 5432
  database: "surveillance"
  user: "postgres"
  password: "${DB_PASSWORD}"     # 從 .env 讀取

modules:
  license_plate:
    enabled: true
    min_confidence: 0.3
    multi_zone_search: true      # 多區域搜尋
```

### .env

```env
DB_PASSWORD=your_password_here
```

## 資料庫結構

### detections (偵測記錄)
- `id` - 主鍵
- `camera_id` - 攝影機 ID
- `timestamp` - 時間戳記
- `object_class` - 物件類別
- `confidence` - 信心度
- `bbox` - 邊界框 (JSON)
- `details` - 細部資訊 (JSON)

### plate_records (車牌記錄)
- `id` - 主鍵
- `detection_id` - 偵測記錄 ID
- `plate_number` - 車牌號碼
- `is_valid` - 是否有效格式
- `confidence` - 信心度
- `first_seen` - 首次出現
- `last_seen` - 最後出現
- `count` - 出現次數

## 專案結構

```
license-plate-recognition/
├── config/              # 配置檔案
├── core/                # 核心系統
│   ├── base_detector.py
│   ├── recognizer_base.py
│   └── system.py
├── modules/             # 辨識模組
│   └── license_plate.py
├── database/            # 資料庫
│   ├── handler.py
│   └── init_db.py
├── utils/               # 工具
│   ├── config_manager.py
│   ├── logger.py
│   └── performance.py
├── tests/               # 測試
├── logs/                # 日誌
├── main.py              # 主程式
└── requirements.txt
```

## 擴展功能

### 增加新的辨識模組

1. 繼承 `DetailRecognizer` 基類
2. 實作必要方法
3. 在 `main.py` 中註冊模組

範例：

```python
from core.recognizer_base import DetailRecognizer

class CustomRecognizer(DetailRecognizer):
    @property
    def name(self):
        return "custom_module"
    
    @property
    def target_classes(self):
        return ['person']
    
    def initialize(self):
        # 載入模型
        pass
    
    def recognize(self, image, detection):
        # 執行辨識
        return {'result': 'data'}
```

## 常見問題

### Q: RTSP 連線失敗？
A: 檢查 RTSP URL 是否正確，網路是否通暢

### Q: 車牌辨識率低？
A: 
- 調整 `min_confidence` 參數
- 啟用 `multi_zone_search`
- 改善攝影機角度和光線條件

### Q: 記憶體使用過高？
A: 
- 降低攝影機數量
- 增加 `process_interval` 間隔
- 減小 `frame_queue` 大小

### Q: 安裝 EasyOCR 失敗？
A: 
```powershell
# 手動安裝
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install easyocr
```

## 效能指標

- **處理速度**: ~0.5-2 FPS per camera (CPU)
- **記憶體使用**: ~500MB-1GB per camera
- **車牌辨識率**: > 80% (良好光線條件)
- **延遲**: < 3 秒

## 授權

MIT License

## 作者

CCTV License Plate Recognition Team

## 版本

v1.0.0 - 2025/11/06

---

**注意**: 使用前請確保符合當地法律規範，尊重個人隱私。
