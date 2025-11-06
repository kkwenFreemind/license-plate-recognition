"""修正資料庫時區問題 - 將 TIMESTAMP 改為 TIMESTAMPTZ"""

import psycopg2
import sys
import os

# 添加專案根目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config_manager import ConfigManager


def fix_timezone():
    """修正資料庫時區"""
    
    # 載入配置
    config_manager = ConfigManager()
    db_config = config_manager.config['database']
    
    print("=" * 50)
    print("資料庫時區修正工具")
    print("=" * 50)
    
    try:
        # 連接資料庫
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password']
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("\n✓ 資料庫連接成功")
        
        # 1. 檢查當前時區設定
        cursor.execute("SHOW timezone;")
        current_tz = cursor.fetchone()[0]
        print(f"\n目前資料庫時區: {current_tz}")
        
        # 2. 設定 PostgreSQL 時區為 Asia/Taipei (UTC+8)
        print("\n設定資料庫時區為 Asia/Taipei...")
        cursor.execute("SET timezone = 'Asia/Taipei';")
        print("✓ 時區設定完成")
        
        # 3. 更新 detections 表格的 timestamp 欄位為 TIMESTAMPTZ
        print("\n正在更新 detections 表格...")
        cursor.execute("""
            ALTER TABLE detections 
            ALTER COLUMN timestamp TYPE TIMESTAMPTZ 
            USING timestamp AT TIME ZONE 'UTC';
        """)
        print("✓ detections.timestamp 已更新為 TIMESTAMPTZ")
        
        # 4. 更新 plate_records 表格
        print("\n正在更新 plate_records 表格...")
        cursor.execute("""
            ALTER TABLE plate_records 
            ALTER COLUMN first_seen TYPE TIMESTAMPTZ 
            USING first_seen AT TIME ZONE 'UTC';
        """)
        cursor.execute("""
            ALTER TABLE plate_records 
            ALTER COLUMN last_seen TYPE TIMESTAMPTZ 
            USING last_seen AT TIME ZONE 'UTC';
        """)
        print("✓ plate_records 時間欄位已更新為 TIMESTAMPTZ")
        
        # 5. 更新 fence_intrusions 表格
        print("\n正在更新 fence_intrusions 表格...")
        cursor.execute("""
            ALTER TABLE fence_intrusions 
            ALTER COLUMN timestamp TYPE TIMESTAMPTZ 
            USING timestamp AT TIME ZONE 'UTC';
        """)
        print("✓ fence_intrusions.timestamp 已更新為 TIMESTAMPTZ")
        
        # 6. 顯示範例資料驗證
        print("\n" + "=" * 50)
        print("驗證資料 (顯示最近 3 筆記錄)")
        print("=" * 50)
        
        cursor.execute("""
            SELECT id, camera_id, timestamp, object_class 
            FROM detections 
            ORDER BY timestamp DESC 
            LIMIT 3
        """)
        
        rows = cursor.fetchall()
        if rows:
            print("\ndetections 表格:")
            for row in rows:
                print(f"  ID: {row[0]}, 攝影機: {row[1]}, 時間: {row[2]}, 類型: {row[3]}")
        else:
            print("\ndetections 表格暫無資料")
        
        cursor.execute("""
            SELECT id, fence_name, timestamp, object_class 
            FROM fence_intrusions 
            ORDER BY timestamp DESC 
            LIMIT 3
        """)
        
        rows = cursor.fetchall()
        if rows:
            print("\nfence_intrusions 表格:")
            for row in rows:
                print(f"  ID: {row[0]}, 圍籬: {row[1]}, 時間: {row[2]}, 類型: {row[3]}")
        else:
            print("\nfence_intrusions 表格暫無資料")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 50)
        print("✓ 時區修正完成！")
        print("=" * 50)
        print("\n注意事項:")
        print("1. 所有時間欄位已轉換為 TIMESTAMPTZ (含時區資訊)")
        print("2. 現有的 UTC 時間已調整為台灣時間 (UTC+8)")
        print("3. 未來儲存的時間會自動包含時區資訊")
        print("4. 請重新啟動 web_server.py 使變更生效")
        
    except Exception as e:
        print(f"\n✗ 錯誤: {e}")
        return False
    
    return True


if __name__ == "__main__":
    success = fix_timezone()
    sys.exit(0 if success else 1)
