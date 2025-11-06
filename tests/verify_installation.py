"""驗證所有套件是否正確安裝"""

import sys


def check_package(package_name, import_name=None):
    """檢查套件是否可以匯入"""
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        print(f"✓ {package_name}")
        return True
    except ImportError as e:
        print(f"✗ {package_name} - {e}")
        return False


def main():
    print("=" * 60)
    print("驗證安裝")
    print("=" * 60)
    
    print("\n檢查必要套件...")
    print("-" * 60)
    
    required = {
        'NumPy': 'numpy',
        'OpenCV': 'cv2',
        'Ultralytics (YOLO)': 'ultralytics',
        'PyTorch': 'torch',
        'EasyOCR': 'easyocr',
        'PostgreSQL Driver': 'psycopg2',
        'PyYAML': 'yaml',
        'Python-dotenv': 'dotenv',
    }
    
    results = []
    for name, import_name in required.items():
        results.append(check_package(name, import_name))
    
    print("-" * 60)
    
    if all(results):
        print("\n🎉 所有必要套件已安裝!")
    else:
        print("\n⚠️  部分套件未安裝，請執行:")
        print("   pip install -r requirements.txt")
        return False
    
    # 檢查選用套件
    print("\n檢查選用套件...")
    print("-" * 60)
    check_package('Face Recognition', 'face_recognition')
    print("-" * 60)
    
    # 測試 YOLO 模型下載
    print("\n下載 YOLO 模型...")
    try:
        from ultralytics import YOLO
        print("正在下載 yolov8n.pt...")
        model = YOLO('yolov8n.pt')
        print("✓ YOLO 模型下載成功")
    except Exception as e:
        print(f"✗ YOLO 模型下載失敗: {e}")
        return False
    
    # 檢查配置檔案
    print("\n檢查配置檔案...")
    print("-" * 60)
    from pathlib import Path
    
    config_file = Path('config/config.yaml')
    env_file = Path('.env')
    
    if config_file.exists():
        print("✓ config/config.yaml 存在")
    else:
        print("✗ config/config.yaml 不存在")
        print("  請執行: copy config\\config.example.yaml config\\config.yaml")
    
    if env_file.exists():
        print("✓ .env 存在")
    else:
        print("✗ .env 不存在")
        print("  請執行: copy .env.example .env")
    
    print("-" * 60)
    
    print("\n" + "=" * 60)
    print("✓ 驗證完成!")
    print("=" * 60)
    print("\n下一步:")
    print("  1. 編輯 config/config.yaml 設定攝影機資訊")
    print("  2. 編輯 .env 填入資料庫密碼")
    print("  3. 執行: python database/init_db.py")
    print("  4. 執行: python main.py")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
