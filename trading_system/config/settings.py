"""
系统配置模块
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """系统配置类"""
    
    # 数据源配置（远程TDX API）
    tdx_api_url: str = Field(default="http://43.138.33.77:8080", alias="TDX_API_URL")
    
    # 钉钉配置
    dingtalk_webhook_url: Optional[str] = Field(default=None, alias="DINGTALK_WEBHOOK_URL")
    dingtalk_secret: Optional[str] = Field(default=None, alias="DINGTALK_SECRET")
    
    # 飞书配置
    feishu_webhook_url: Optional[str] = Field(default=None, alias="FEISHU_WEBHOOK_URL")
    
    # OpenAI配置
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_api_base: str = Field(default="https://api.openai.com/v1", alias="OPENAI_API_BASE")
    openai_model: str = Field(default="gpt-4", alias="OPENAI_MODEL")
    
    # 交易参数
    max_loss_percent: float = Field(default=2.0, alias="MAX_LOSS_PERCENT")
    stop_loss_percent: float = Field(default=8.0, alias="STOP_LOSS_PERCENT")
    
    # 股票池配置
    stock_pool: str = Field(
        default="000001,000002,000333,000858,002594,300750,600000,600519,601012,601318",
        alias="STOCK_POOL"
    )
    index_code: str = Field(default="000001", alias="INDEX_CODE")
    
    # 系统配置
    data_dir: str = Field(default="./data", alias="DATA_DIR")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    schedule_day: int = Field(default=5, alias="SCHEDULE_DAY")  # 周五
    schedule_time: str = Field(default="15:30", alias="SCHEDULE_TIME")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def get_stock_list(self) -> List[str]:
        """获取股票列表"""
        return [code.strip() for code in self.stock_pool.split(",") if code.strip()]


# 全局配置实例
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """获取配置实例（单例模式）"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
