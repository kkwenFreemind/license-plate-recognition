"""執行資料庫遷移 - 為 plate_records 新增截圖欄位"""

import psycopg2
import sys
from pathlib import Path

# 加入專案路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_manager import ConfigManager


def main():
    """執行 migration"""
    print("=" * 60)
    print("資料庫遷移: 新增 plate_records.snapshot_base64")
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
        
        # 讀取 migration 檔案
        print("\n3. 讀取 migration 檔案...")
        migration_file = Path(__file__).parent / 'migrations' / 'add_snapshot_to_plate_records.sql'
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        print(f"✓ 已載入: {migration_file.name}")
        
        # 執行 migration
        print("\n4. 執行 migration...")
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        print("✓ Migration 執行成功")
        
        # 驗證欄位
        print("\n5. 驗證新欄位...")
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'plate_records' 
            AND column_name = 'snapshot_base64'
        """)
        
        result = cursor.fetchone()
        if result:
            print(f"✓ 欄位已建立: {result[0]} ({result[1]})")
        else:
            print("⚠️  警告: 未找到新欄位")
        
        # 關閉連線
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("✓ 資料庫遷移完成!")
        print("=" * 60)
        print("\n說明:")
        print("  - plate_records 表格已新增 snapshot_base64 欄位")
        print("  - 車牌辨識成功時將儲存車輛局部截圖")
        print("  - 截圖格式: JPEG (base64 編碼)")
        print("  - 截圖範圍: 車輛邊界框 + 10% 邊距")
        
    except FileNotFoundError as e:
        print(f"\n❌ 錯誤: {e}")
        print("\n請確認:")
        print("  1. migration 檔案是否存在")
        print("  2. 配置檔案是否正確")
        sys.exit(1)
    except psycopg2.Error as e:
        print(f"\n❌ 資料庫錯誤: {e}")
        print("\n請檢查:")
        print("  1. PostgreSQL 是否正在執行")
        print("  2. 資料庫配置是否正確")
        print("  3. 資料庫使用者權限")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 未預期的錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
