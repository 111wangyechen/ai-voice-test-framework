"""
配置管理模块
"""
import json
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class AIConfig(BaseSettings):
    """AI分析配置"""
    mode: str = "rule_based"  # rule_based 或 claude_api
    claude_api_enabled: bool = False
    claude_api_key: str = ""
    claude_model: str = "claude-3-5-sonnet-20241022"


class DeviceConfig(BaseSettings):
    """设备配置"""
    ip: str = "10.7.187.15:5555"
    adb_path: str = "adb"


class MonitoringConfig(BaseSettings):
    """监控配置"""
    log_sampling_rate: int = 100  # 每秒最多推送日志数
    performance_sampling_interval: int = 2  # 性能采样间隔(秒)


class WebSocketConfig(BaseSettings):
    """WebSocket配置"""
    host: str = "127.0.0.1"
    port: int = 8765


class DatabaseConfig(BaseSettings):
    """数据库配置"""
    path: str = "data/test_results.db"


class Settings(BaseSettings):
    """全局配置"""
    device: DeviceConfig = DeviceConfig()
    ai_analysis: AIConfig = AIConfig()
    monitoring: MonitoringConfig = MonitoringConfig()
    websocket: WebSocketConfig = WebSocketConfig()
    database: DatabaseConfig = DatabaseConfig()

    @classmethod
    def load_from_file(cls, config_path: Optional[Path] = None) -> "Settings":
        """从文件加载配置"""
        if config_path is None:
            config_path = Path(__file__).parent / "default_config.json"

        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            return cls(**config_data)

        return cls()

    def save_to_file(self, config_path: Path):
        """保存配置到文件"""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.dict(), f, indent=2, ensure_ascii=False)


# 全局配置实例
settings = Settings.load_from_file()
