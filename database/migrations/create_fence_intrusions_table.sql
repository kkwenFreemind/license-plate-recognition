-- 創建電子圍籬入侵事件表
CREATE TABLE IF NOT EXISTS fence_intrusions (
    id SERIAL PRIMARY KEY,
    fence_id VARCHAR(50) NOT NULL,
    fence_name VARCHAR(100) NOT NULL,
    object_class VARCHAR(50) NOT NULL,
    confidence FLOAT NOT NULL,
    bbox_x1 INTEGER,
    bbox_y1 INTEGER,
    bbox_x2 INTEGER,
    bbox_y2 INTEGER,
    camera_id VARCHAR(100),
    camera_name VARCHAR(100),
    snapshot_base64 TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 創建索引以提升查詢效能
CREATE INDEX IF NOT EXISTS idx_fence_intrusions_fence_id ON fence_intrusions(fence_id);
CREATE INDEX IF NOT EXISTS idx_fence_intrusions_timestamp ON fence_intrusions(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_fence_intrusions_object_class ON fence_intrusions(object_class);
CREATE INDEX IF NOT EXISTS idx_fence_intrusions_camera_id ON fence_intrusions(camera_id);

-- 添加註解
COMMENT ON TABLE fence_intrusions IS '電子圍籬入侵事件記錄表';
COMMENT ON COLUMN fence_intrusions.id IS '主鍵ID';
COMMENT ON COLUMN fence_intrusions.fence_id IS '圍籬ID';
COMMENT ON COLUMN fence_intrusions.fence_name IS '圍籬名稱';
COMMENT ON COLUMN fence_intrusions.object_class IS '物件類型 (person, car, etc.)';
COMMENT ON COLUMN fence_intrusions.confidence IS '信心度 (0.0-1.0)';
COMMENT ON COLUMN fence_intrusions.bbox_x1 IS '邊界框左上角X座標';
COMMENT ON COLUMN fence_intrusions.bbox_y1 IS '邊界框左上角Y座標';
COMMENT ON COLUMN fence_intrusions.bbox_x2 IS '邊界框右下角X座標';
COMMENT ON COLUMN fence_intrusions.bbox_y2 IS '邊界框右下角Y座標';
COMMENT ON COLUMN fence_intrusions.camera_id IS '攝影機ID';
COMMENT ON COLUMN fence_intrusions.camera_name IS '攝影機名稱';
COMMENT ON COLUMN fence_intrusions.snapshot_base64 IS '入侵當下的影像截圖 (Base64編碼)';
COMMENT ON COLUMN fence_intrusions.timestamp IS '入侵時間';
COMMENT ON COLUMN fence_intrusions.created_at IS '記錄建立時間';
