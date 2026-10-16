"""
Data models for the Data Collector Service
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field


class ServiceStatus(str, Enum):
    """Service status enumeration"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    STARTING = "starting"
    STOPPING = "stopping"


class CollectionStatus(str, Enum):
    """Collection status enumeration"""
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


class HealthResponse(BaseModel):
    """Health check response model"""
    status: ServiceStatus
    service: str
    version: str
    timestamp: float


class CollectorStatus(BaseModel):
    """Collector status response model"""
    status: CollectionStatus
    active_exchanges: List[str]
    symbols_count: int
    last_collection: Optional[datetime]
    collections_today: int
    errors_count: int
    uptime_seconds: float


class MarketData(BaseModel):
    """Market data model"""
    symbol: str
    exchange: str
    timestamp: datetime
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    close: Optional[float]
    volume: Optional[float]
    bid: Optional[float]
    ask: Optional[float]
    bid_volume: Optional[float]
    ask_volume: Optional[float]
    vwap: Optional[float]  # Volume Weighted Average Price
    change: Optional[float]
    percentage: Optional[float]
    average: Optional[float]
    base_volume: Optional[float]
    quote_volume: Optional[float]


class OrderBookData(BaseModel):
    """Order book data model"""
    symbol: str
    exchange: str
    timestamp: datetime
    bids: List[List[float]]  # [price, amount]
    asks: List[List[float]]  # [price, amount]
    nonce: Optional[int]


class TradeData(BaseModel):
    """Trade data model"""
    symbol: str
    exchange: str
    timestamp: datetime
    id: str
    side: str  # 'buy' or 'sell'
    amount: float
    price: float
    cost: float
    fee: Optional[Dict[str, Any]]


class OHLCVData(BaseModel):
    """OHLCV (candlestick) data model"""
    symbol: str
    exchange: str
    timeframe: str  # '1m', '5m', '1h', '1d', etc.
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class ExchangeInfo(BaseModel):
    """Exchange information model"""
    id: str
    name: str
    countries: List[str]
    urls: Dict[str, Any]
    version: Optional[str]
    certified: bool
    pro: bool
    has: Dict[str, Any]  # Exchange capabilities


class SymbolInfo(BaseModel):
    """Symbol information model"""
    id: str
    symbol: str
    base: str
    quote: str
    settle: Optional[str]
    type: str  # 'spot', 'future', 'option', etc.
    spot: bool
    margin: bool
    future: bool
    option: bool
    active: bool
    contract: bool
    linear: Optional[bool]
    inverse: Optional[bool]
    taker: Optional[float]
    maker: Optional[float]
    contract_size: Optional[float]
    expiry: Optional[datetime]
    expiry_datetime: Optional[datetime]
    strike: Optional[float]
    option_type: Optional[str]
    precision: Dict[str, Any]
    limits: Dict[str, Any]
    info: Dict[str, Any]


class CollectionMetrics(BaseModel):
    """Collection metrics model"""
    total_collections: int
    successful_collections: int
    failed_collections: int
    exchanges_active: int
    symbols_collected: int
    avg_collection_time: float
    last_error: Optional[str]
    error_rate: float


class KafkaMessage(BaseModel):
    """Kafka message wrapper"""
    topic: str
    key: Optional[str]
    value: Dict[str, Any]
    timestamp: datetime
    headers: Optional[Dict[str, str]]


class RateLimitInfo(BaseModel):
    """Rate limit information"""
    requests_made: int
    requests_limit: int
    window_start: datetime
    window_end: datetime
    remaining: int
    reset_time: datetime