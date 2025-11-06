"""統一日誌管理"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict


def setup_logger(name: str, config: Dict = None) -> logging.Logger:
    """
    建立日誌記錄器
    
    Args:
        name: 記錄器名稱
        config: 日誌配置 (從 ConfigManager 取得)
    
    Returns:
        logging.Logger: 配置好的日誌記錄器
    """
    if config is None:
        config = {
            'level': 'INFO',
            'file': 'logs/system.log',
            'max_size': 10485760,
            'backup_count': 5
        }
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.get('level', 'INFO')))
    
    # 避免重複添加 handler
    if logger.handlers:
        return logger
    
    # 格式設定
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台輸出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 檔案輸出
    log_file = Path(config.get('file', 'logs/system.log'))
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=config.get('max_size', 10485760),
        backupCount=config.get('backup_count', 5),
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger
