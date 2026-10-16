import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    
    # Application settings
    app_name: str = Field(default="crypto-viz-data-processor", alias="APP_NAME")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")

    # Service configuration
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8002)

    # Kafka configuration
    kafka_brokers: str = Field(default="kafka:9092", alias="KAFKA_BROKERS")
    kafka_client_id: str = Field(default="crypto-viz-processor", alias="KAFKA_CLIENT_ID")
    kafka_group_id: str = Field(default="crypto-viz-processor-group", alias="KAFKA_GROUP_ID")

    # Kafka topics
    kafka_topic_raw_data: str = Field(default="crypto-raw-data", alias="KAFKA_TOPIC_RAW_DATA")
    kafka_topic_analytics: str = Field(default="crypto-analytics", alias="KAFKA_TOPIC_ANALYTICS")
    kafka_topic_alerts: str = Field(default="crypto-alerts", alias="KAFKA_TOPIC_ALERTS")
    kafka_topic_processed: str = Field(default="crypto-processed-data", alias="KAFKA_TOPIC_PROCESSED_DATA")

    # MongoDB configuration
    mongodb_uri: str = Field(default="mongodb://mongo:27017/cryptoviz", alias="MONGODB_URI")
    mongodb_database: str = Field(default="cryptoviz", alias="MONGODB_DATABASE")
    mongodb_user: str = Field(default="cryptoviz_user", alias="MONGODB_USER")
    mongodb_password: str = Field(default="cryptoviz_password", alias="MONGODB_PASSWORD")

    # Redis configuration
    redis_host: str = Field(default="redis", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_password: str = Field(default="redis_password", alias="REDIS_PASSWORD")
    redis_db: int = Field(default=0)
    redis_ttl: int = Field(default=300)  # 5 minutes

    # Processing windows (in seconds)
    analytics_window_short: int = Field(default=300, alias="ANALYTICS_WINDOW_SHORT")  # 5 minutes
    analytics_window_medium: int = Field(default=3600, alias="ANALYTICS_WINDOW_MEDIUM")  # 1 hour
    analytics_window_long: int = Field(default=86400, alias="ANALYTICS_WINDOW_LONG")  # 24 hours

    # Alert thresholds
    price_change_alert_threshold: float = Field(default=5.0, alias="PRICE_CHANGE_ALERT_THRESHOLD")
    volume_spike_threshold: float = Field(default=2.0, alias="VOLUME_SPIKE_THRESHOLD")
    sentiment_alert_threshold: float = Field(default=0.8, alias="SENTIMENT_ALERT_THRESHOLD")

    # Technical indicators settings
    rsi_period: int = Field(default=14)
    rsi_overbought: float = Field(default=70.0)
    rsi_oversold: float = Field(default=30.0)

    macd_fast_period: int = Field(default=12)
    macd_slow_period: int = Field(default=26)
    macd_signal_period: int = Field(default=9)

    bollinger_period: int = Field(default=20)
    bollinger_std_dev: float = Field(default=2.0)

    ema_periods: List[int] = Field(default=[12, 26, 50, 200])
    sma_periods: List[int] = Field(default=[20, 50, 100, 200])

    # Data retention
    data_retention_days: int = Field(default=30, alias="DATA_RETENTION_DAYS")

    # Processing settings
    batch_size: int = Field(default=100)
    processing_interval: int = Field(default=5)  # seconds
    max_workers: int = Field(default=4)

    # Monitoring
    enable_metrics: bool = Field(default=True, alias="ENABLE_METRICS")
    metrics_port: int = Field(default=9091, alias="METRICS_PORT")

    @property
    def kafka_brokers_list(self) -> List[str]:
        """Parse Kafka brokers string into list"""
        return [broker.strip() for broker in self.kafka_brokers.split(",")]

    @property
    def mongodb_connection_string(self) -> str:
        """Build MongoDB connection string"""
        # If URI already contains credentials (has @ symbol), use it as-is
        if '@' in self.mongodb_uri:
            return self.mongodb_uri
        # Otherwise, add credentials if available
        if self.mongodb_user and self.mongodb_password:
            from urllib.parse import quote_plus
            user = quote_plus(self.mongodb_user)
            password = quote_plus(self.mongodb_password)
            return f"mongodb://{user}:{password}@{self.mongodb_uri.replace('mongodb://', '')}"
        return self.mongodb_uri

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
