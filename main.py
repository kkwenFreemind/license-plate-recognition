"""主程式 - 多攝影機處理"""

import sys
import signal
import threading
from pathlib import Path

# 加入專案路徑
sys.path.insert(0, str(Path(__file__).parent))

from utils.config_manager import ConfigManager
from utils.logger import setup_logger
from core.system import MultiModalRecognitionSystem
from modules.license_plate import LicensePlateRecognizer
from database.handler import DatabaseHandler


def main():
    """主程式"""
    print("=" * 60)
    print("License Plate Recognition System")
    print("=" * 60)
    
    # 載入配置
    try:
        config = ConfigManager('config/config.yaml')
    except FileNotFoundError as e:
        print(f"\n❌ 錯誤: {e}")
        print("\n請先設定配置檔:")
        print("  copy config\\config.example.yaml config\\config.yaml")
        print("  copy .env.example .env")
        return
    
    # 設定日誌
    logger = setup_logger('Main', config.get_logging_config())
    logger.info("系統啟動中...")
    
    # 初始化資料庫
    db_config = config.get('database', {})
    if db_config.get('enabled', True):
        try:
            db_handler = DatabaseHandler(db_config, logger)
            logger.info("✓ 資料庫連接成功")
        except Exception as e:
            logger.error(f"資料庫連接失敗: {e}")
            logger.warning("系統將在沒有資料庫的情況下運行")
            db_handler = None
    else:
        db_handler = None
        logger.info("資料庫功能已停用")
    
    # 初始化辨識系統
    system = MultiModalRecognitionSystem(config.config, logger)
    
    # 註冊車牌辨識模組
    plate_config = config.get_module_config('license_plate')
    if plate_config.get('enabled', True):
        try:
            plate_recognizer = LicensePlateRecognizer(plate_config, logger)
            system.register_recognizer(plate_recognizer)
        except Exception as e:
            logger.error(f"車牌辨識模組載入失敗: {e}")
            logger.error("請確認 EasyOCR 是否正確安裝")
            return
    
    # 取得啟用的攝影機
    cameras = config.get_enabled_cameras()
    
    if not cameras:
        logger.error("沒有啟用的攝影機!")
        logger.info("請編輯 config/config.yaml 設定攝影機資訊")
        return
    
    logger.info(f"找到 {len(cameras)} 個啟用的攝影機")
    
    # 定義回調函數
    def on_detection(camera_id: str, results):
        """偵測結果回調"""
        # 儲存到資料庫
        if db_handler:
            db_handler.save_detection(camera_id, results)
    
    # 為每個攝影機建立執行緒
    threads = []
    
    # 處理中斷信號
    stop_event = threading.Event()
    
    def signal_handler(sig, frame):
        logger.info("\n接收到中斷信號,正在停止...")
        stop_event.set()
        system.stop()
        if db_handler:
            db_handler.close()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    for cam in cameras:
        camera_id = cam['id']
        rtsp_url = cam['rtsp_url']
        interval = cam.get('process_interval', 2.0)
        
        logger.info(f"啟動攝影機: {camera_id} ({cam.get('name', camera_id)})")
        
        # 建立執行緒 (不使用 daemon，這樣可以正確處理中斷)
        thread = threading.Thread(
            target=system.process_rtsp,
            args=(rtsp_url, camera_id, interval, on_detection),
            daemon=False
        )
        thread.start()
        threads.append(thread)
    
    logger.info("\n系統運行中... (按 Ctrl+C 停止)")
    logger.info("=" * 60)
    
    # 等待所有執行緒
    try:
        while not stop_event.is_set():
            # 使用短暫的 timeout 讓 Ctrl+C 能夠被捕捉
            for thread in threads:
                thread.join(timeout=0.5)
                if not thread.is_alive():
                    threads.remove(thread)
            if not threads:
                break
    except KeyboardInterrupt:
        logger.info("\n使用者中斷")
        system.stop()
        if db_handler:
            db_handler.close()
        # 等待執行緒結束
        for thread in threads:
            thread.join(timeout=2.0)


if __name__ == "__main__":
    main()
