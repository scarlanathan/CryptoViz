"""
Configuration settings for Data Collector Service
"""

import os
from typing import List, Optional

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""

    # Application
    app_name: str = Field(default="crypto-data-collector", env="APP_NAME")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    debug: bool = Field(default=False, env="DEBUG")

    # Kafka
    kafka_brokers: str = Field(default="localhost:9092", env="KAFKA_BROKERS")
    kafka_topic_raw_data: str = Field(default="crypto-raw-data", env="KAFKA_TOPIC_RAW_DATA")
    kafka_client_id: str = Field(default="data-collector", env="KAFKA_CLIENT_ID")

    # Redis
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    redis_db: int = Field(default=0, env="REDIS_DB")

    # Collection settings
    collection_interval: int = Field(default=30, env="COLLECTION_INTERVAL")  # seconds
    symbols_to_collect: List[str] = Field(
        default=["BTC/USDT", "ETH/USDT", "BNB/USDT", "ADA/USDT", "SOL/USDT"],
        env="SYMBOLS_TO_COLLECT"
    )
    exchanges_to_use: List[str] = Field(
        default=["binance", "coinbase", "kraken", "okx"],
        env="EXCHANGES_TO_USE"
    )

    # API Keys (optional for public endpoints)
    binance_api_key: Optional[str] = Field(default=None, env="BINANCE_API_KEY")
    binance_secret: Optional[str] = Field(default=None, env="BINANCE_SECRET")
    coinbase_api_key: Optional[str] = Field(default=None, env="COINBASE_API_KEY")
    coinbase_secret: Optional[str] = Field(default=None, env="COINBASE_SECRET")
    kraken_api_key: Optional[str] = Field(default=None, env="KRAKEN_API_KEY")
    kraken_secret: Optional[str] = Field(default=None, env="KRAKEN_SECRET")

    # Rate limiting
    max_requests_per_minute: int = Field(default=100, env="MAX_REQUESTS_PER_MINUTE")
    rate_limit_window: int = Field(default=60, env="RATE_LIMIT_WINDOW")  # seconds

    # Health check
    health_check_interval: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")  # seconds

    # Data retention
    cache_ttl: int = Field(default=300, env="CACHE_TTL")  # 5 minutes

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()