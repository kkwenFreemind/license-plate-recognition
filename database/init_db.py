"""初始化資料庫表格"""

import psycopg2
from psycopg2 import sql
import sys
from pathlib import Path

# 加入專案路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_manager import ConfigManager
from utils.logger import setup_logger


def create_tables(conn):
    """建立所有必要的表格"""
    cursor = conn.cursor()
    
    # 1. 偵測記錄表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detections (
            id SERIAL PRIMARY KEY,
            camera_id VARCHAR(50) NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            object_class VARCHAR(50) NOT NULL,
            confidence FLOAT,
            bbox JSONB,
            details JSONB
        );
    """)
    
    # 2. 建立索引
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_camera_time 
        ON detections(camera_id, timestamp DESC);
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_class 
        ON detections(object_class);
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_timestamp 
        ON detections(timestamp DESC);
    """)
    
    # 3. 車牌記錄表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS plate_records (
            id SERIAL PRIMARY KEY,
            detection_id INTEGER REFERENCES detections(id),
            plate_number VARCHAR(20) NOT NULL,
            is_valid BOOLEAN DEFAULT TRUE,
            confidence FLOAT,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            count INTEGER DEFAULT 1,
            first_seen_date DATE DEFAULT CURRENT_DATE
        );
    """)
    
    # 3.1 建立唯一約束（使用 first_seen_date 欄位）
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_plate_unique_per_day 
        ON plate_records(plate_number, first_seen_date);
    """)
    
    # 4. 車牌索引
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_plate_number 
        ON plate_records(plate_number);
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_plate_time 
        ON plate_records(first_seen DESC);
    """)
    
    # 5. 攝影機資訊表 (可選)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cameras (
            camera_id VARCHAR(50) PRIMARY KEY,
            camera_name VARCHAR(100),
            rtsp_url VARCHAR(255),
            location VARCHAR(100),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    conn.commit()
    print("✓ 資料庫表格建立完成")


def insert_sample_cameras(conn, config):
    """插入攝影機資訊 (從配置檔讀取)"""
    cursor = conn.cursor()
    
    cameras = config.get_cameras()
    
    for cam in cameras:
        try:
            cursor.execute("""
                INSERT INTO cameras (camera_id, camera_name, rtsp_url, is_active)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (camera_id) DO UPDATE
                SET camera_name = EXCLUDED.camera_name,
                    rtsp_url = EXCLUDED.rtsp_url,
                    is_active = EXCLUDED.is_active
            """, (
                cam['id'],
                cam.get('name', cam['id']),
                cam.get('rtsp_url', ''),
                cam.get('enabled', True)
            ))
        except Exception as e:
            print(f"⚠️  警告: 無法插入攝影機 {cam['id']}: {e}")
    
    conn.commit()
    print(f"✓ 已同步 {len(cameras)} 個攝影機資訊")


def main():
    """主程式"""
    print("=" * 60)
    print("初始化資料庫")
    print("=" * 60)
    
    try:
        # 載入配置
        print("\n1. 載入配置...")
        config = ConfigManager('config/config.yaml')
        db_config = config.get_db_config()
        
        # 連接資料庫
        print("\n2. 連接資料庫...")
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password']
        )
        print(f"✓ 已連接到: {db_config['host']}:{db_config['port']}/{db_config['database']}")
        
        # 建立表格
        print("\n3. 建立表格...")
        create_tables(conn)
        
        # 同步攝影機資訊
        print("\n4. 同步攝影機資訊...")
        insert_sample_cameras(conn, config)
        
        # 關閉連線
        conn.close()
        
        print("\n" + "=" * 60)
        print("✓ 資料庫初始化完成!")
        print("=" * 60)
        
    except FileNotFoundError as e:
        print(f"\n❌ 錯誤: {e}")
        print("\n請先設定配置檔:")
        print("  1. copy config\\config.example.yaml config\\config.yaml")
        print("  2. copy .env.example .env")
        print("  3. 編輯 .env 填入資料庫密碼")
        sys.exit(1)
    except psycopg2.Error as e:
        print(f"\n❌ 資料庫錯誤: {e}")
        print("\n請檢查:")
        print("  1. PostgreSQL 是否正在執行")
        print("  2. 資料庫配置是否正確 (config.yaml)")
        print("  3. 資料庫密碼是否正確 (.env)")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 未預期的錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
