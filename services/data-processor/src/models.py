from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field


# ===== ENUMS =====

class AlertType(str, Enum):
    """Alert types"""
    PRICE_SPIKE = "price_spike"
    PRICE_DROP = "price_drop"
    VOLUME_SPIKE = "volume_spike"
    RSI_OVERBOUGHT = "rsi_overbought"
    RSI_OVERSOLD = "rsi_oversold"
    MACD_BULLISH = "macd_bullish"
    MACD_BEARISH = "macd_bearish"
    BOLLINGER_BREAKOUT = "bollinger_breakout"


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ProcessingStatus(str, Enum):
    """Processing status"""
    IDLE = "idle"
    PROCESSING = "processing"
    ERROR = "error"
    STOPPED = "stopped"


# ===== RAW DATA MODELS =====

class RawMarketData(BaseModel):
    """Raw market data from Kafka"""
    symbol: str
    exchange: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    quote_volume: Optional[float] = None
    trades: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


# ===== TECHNICAL INDICATORS MODELS =====

class RSIIndicator(BaseModel):
    """RSI (Relative Strength Index) indicator"""
    value: float
    period: int = 14
    overbought: bool = False
    oversold: bool = False
    timestamp: datetime


class MACDIndicator(BaseModel):
    """MACD (Moving Average Convergence Divergence) indicator"""
    macd_line: float
    signal_line: float
    histogram: float
    bullish_crossover: bool = False
    bearish_crossover: bool = False
    timestamp: datetime


class BollingerBands(BaseModel):
    """Bollinger Bands indicator"""
    upper_band: float
    middle_band: float
    lower_band: float
    bandwidth: float
    percent_b: float
    breakout_upper: bool = False
    breakout_lower: bool = False
    timestamp: datetime


class MovingAverages(BaseModel):
    """Moving averages (EMA and SMA)"""
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None
    ema_50: Optional[float] = None
    ema_200: Optional[float] = None
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_100: Optional[float] = None
    sma_200: Optional[float] = None
    golden_cross: bool = False  # EMA50 crosses above EMA200
    death_cross: bool = False    # EMA50 crosses below EMA200
    timestamp: datetime


class VolumeIndicators(BaseModel):
    """Volume-based indicators"""
    current_volume: float
    avg_volume: float
    volume_ratio: float
    volume_spike: bool = False
    on_balance_volume: Optional[float] = None
    timestamp: datetime


class TechnicalIndicators(BaseModel):
    """Complete technical indicators for a symbol"""
    symbol: str
    timestamp: datetime
    rsi: Optional[RSIIndicator] = None
    macd: Optional[MACDIndicator] = None
    bollinger_bands: Optional[BollingerBands] = None
    moving_averages: Optional[MovingAverages] = None
    volume_indicators: Optional[VolumeIndicators] = None


# ===== ANALYTICS MODELS =====

class PriceAnalytics(BaseModel):
    """Price analytics"""
    current_price: float
    price_change_1h: float
    price_change_24h: float
    price_change_7d: Optional[float] = None
    high_24h: float
    low_24h: float
    volatility: float
    timestamp: datetime


class MarketAnalytics(BaseModel):
    """Complete market analytics for a symbol"""
    symbol: str
    exchange: str
    timestamp: datetime
    price_analytics: PriceAnalytics
    technical_indicators: TechnicalIndicators
    market_trend: str  # "bullish", "bearish", "neutral"
    confidence_score: float  # 0-1


# ===== ALERT MODELS =====

class Alert(BaseModel):
    """Alert model"""
    id: Optional[str] = None
    symbol: str
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    value: float
    threshold: float
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ===== PROCESSOR STATUS MODELS =====

class ProcessorStatus(BaseModel):
    """Data processor status"""
    status: ProcessingStatus
    messages_processed: int = 0
    alerts_generated: int = 0
    errors: int = 0
    last_processed_time: Optional[datetime] = None
    uptime_seconds: float = 0.0
    symbols_tracked: List[str] = Field(default_factory=list)
    processing_rate: float = 0.0  # messages per second


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
    timestamp: float
    details: Optional[Dict[str, Any]] = None


# ===== PROCESSED DATA MODELS =====

class ProcessedData(BaseModel):
    """Processed data to be published to Kafka and stored in MongoDB"""
    id: Optional[str] = None
    symbol: str
    exchange: str
    timestamp: datetime
    raw_data: Dict[str, Any]
    analytics: Dict[str, Any]
    indicators: Dict[str, Any]
    alerts: List[Alert] = Field(default_factory=list)
    processing_timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ===== TIME SERIES MODELS =====

class TimeSeriesData(BaseModel):
    """Time series data for historical analysis"""
    symbol: str
    timeframe: str  # "1m", "5m", "1h", "1d", etc.
    data: List[Dict[str, Any]]
    start_time: datetime
    end_time: datetime
    count: int


class HistoricalAnalytics(BaseModel):
    """Historical analytics data"""
    symbol: str
    timeframe: str
    analytics: List[Dict[str, Any]]
    indicators: List[Dict[str, Any]]
    start_time: datetime
    end_time: datetime
    count: int
