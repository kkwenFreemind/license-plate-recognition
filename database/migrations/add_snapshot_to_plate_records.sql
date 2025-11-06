-- 為 plate_records 表格新增截圖欄位
-- 用於儲存車牌辨識時的截圖 (base64 格式)

ALTER TABLE plate_records 
ADD COLUMN IF NOT EXISTS snapshot_base64 TEXT;

-- 新增註解
COMMENT ON COLUMN plate_records.snapshot_base64 IS '車牌辨識截圖 (base64 編碼)';
