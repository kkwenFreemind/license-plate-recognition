# 時區修正說明文件

## 問題描述

資料庫中的時間欄位少了 8 小時，原因是：
- Python 使用 `datetime.now()` 產生本地時間（UTC+8，台灣時間）
- 但沒有包含時區資訊
- PostgreSQL 接收到時間時假設它是 UTC 時間
- 導致實際儲存的時間少了 8 小時

## 解決方案

### 1. 程式碼修正

修改以下檔案，使用時區感知的 datetime：

#### `core/system.py`
```python
# 修改前
'timestamp': datetime.now().isoformat()

# 修改後
'timestamp': datetime.now(timezone.utc).astimezone().isoformat()
```

#### `modules/virtual_fence.py`
```python
# 修改前
'timestamp': datetime.now().isoformat()

# 修改後
'timestamp': datetime.now(timezone.utc).astimezone().isoformat()
```

#### `database/handler.py`
```python
# 修改前
from datetime import datetime

# 修改後
from datetime import datetime, timezone

# 在 save_fence_intrusion 方法中
timestamp or datetime.now()  # 修改前
timestamp or datetime.now(timezone.utc).astimezone()  # 修改後
```

### 2. 資料庫結構修正

執行 `fix_timezone.bat` 或 `python database/fix_timezone.py` 來：

1. **設定 PostgreSQL 時區**
   ```sql
   SET timezone = 'Asia/Taipei';
   ```

2. **將 TIMESTAMP 改為 TIMESTAMPTZ**
   - `detections.timestamp`
   - `plate_records.first_seen`
   - `plate_records.last_seen`
   - `fence_intrusions.timestamp`

3. **轉換現有資料**
   ```sql
   ALTER TABLE detections 
   ALTER COLUMN timestamp TYPE TIMESTAMPTZ 
   USING timestamp AT TIME ZONE 'UTC';
   ```

## 執行步驟

### 方法一：使用批次檔（推薦）
```cmd
fix_timezone.bat
```

### 方法二：手動執行
```cmd
cd d:\SideProject\license-plate-recognition
venv\Scripts\activate
python database\fix_timezone.py
```

## 驗證

執行修正後，腳本會顯示最近 3 筆記錄的時間，確認時間已正確調整為台灣時間 (UTC+8)。

範例輸出：
```
驗證資料 (顯示最近 3 筆記錄)
==================================================
detections 表格:
  ID: 1234, 攝影機: bd687687..., 時間: 2025-11-06 16:30:45.123456+08:00, 類型: car
```

注意時間後面有 `+08:00` 表示包含時區資訊。

## 重要提醒

1. **執行修正腳本後，必須重新啟動 web_server.py**
2. **未來所有新記錄都會自動包含正確的時區資訊**
3. **現有記錄已從 UTC 時間調整為台灣時間**

## 技術細節

### 時區處理方式

修改後的程式使用：
```python
datetime.now(timezone.utc).astimezone()
```

這會：
1. 取得 UTC 時間
2. 自動轉換為本地時區（Asia/Taipei）
3. 包含時區資訊 (`+08:00`)
4. 儲存到 PostgreSQL 的 TIMESTAMPTZ 欄位

### ISO 8601 格式

時間格式範例：
- **修改前**: `2025-11-06T16:30:45.123456` (無時區)
- **修改後**: `2025-11-06T16:30:45.123456+08:00` (含時區)

## 相關檔案

- `database/fix_timezone.py` - 時區修正腳本
- `fix_timezone.bat` - Windows 批次檔
- `core/system.py` - 主系統時間戳記修正
- `modules/virtual_fence.py` - 圍籬模組時間戳記修正
- `database/handler.py` - 資料庫處理時間戳記修正
