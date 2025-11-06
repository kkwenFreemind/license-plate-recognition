"""配置管理器 - 支援 YAML 和環境變數"""

import yaml
import os
from typing import Any, Dict, List
from pathlib import Path
from dotenv import load_dotenv


class ConfigManager:
    """統一配置管理"""
    
    def __init__(self, config_path: str = 'config/config.yaml'):
        # 載入環境變數
        load_dotenv()
        
        # 載入 YAML 配置
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(
                f"配置檔案不存在: {config_path}\n"
                f"請複製 config/config.example.yaml 為 config/config.yaml"
            )
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # 替換環境變數
        self._replace_env_vars(self.config)
        
    def _replace_env_vars(self, obj: Any) -> Any:
        """遞迴替換 ${VAR} 格式的環境變數"""
        if isinstance(obj, dict):
            return {k: self._replace_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._replace_env_vars(item) for item in obj]
        elif isinstance(obj, str) and obj.startswith('${') and obj.endswith('}'):
            var_name = obj[2:-1]
            value = os.getenv(var_name)
            if value is None:
                print(f"⚠️  警告: 環境變數 {var_name} 未設定")
                return obj
            return value
        return obj
    
    def get(self, path: str, default=None) -> Any:
        """
        取得配置值
        
        Examples:
            config.get('database.host')
            config.get('modules.license_plate.enabled')
        """
        keys = path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_cameras(self) -> List[Dict]:
        """取得所有攝影機配置"""
        return self.config.get('cameras', [])
    
    def get_enabled_cameras(self) -> List[Dict]:
        """取得啟用的攝影機"""
        cameras = self.get_cameras()
        return [cam for cam in cameras if cam.get('enabled', True)]
    
    def get_db_config(self) -> Dict[str, Any]:
        """取得資料庫配置"""
        db = self.config.get('database', {})
        return {
            'host': db.get('host', 'localhost'),
            'port': db.get('port', 5432),
            'database': db.get('database', 'surveillance'),
            'user': db.get('user', 'postgres'),
            'password': db.get('password', ''),
        }
    
    def get_module_config(self, module_name: str) -> Dict[str, Any]:
        """取得模組配置"""
        modules = self.config.get('modules', {})
        return modules.get(module_name, {})
    
    def get_yolo_config(self) -> Dict[str, Any]:
        """取得 YOLO 配置"""
        return self.config.get('yolo', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """取得日誌配置"""
        return self.config.get('logging', {})
    
    def get_performance_config(self) -> Dict[str, Any]:
        """取得效能配置"""
        return self.config.get('performance', {})
