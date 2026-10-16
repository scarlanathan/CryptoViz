import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque

import pandas as pd
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as aioredis

from src.config import Settings
from src.models import (
    RawMarketData,
    ProcessedData,
    Alert,
    AlertType,
    AlertSeverity,
    ProcessorStatus,
    ProcessingStatus,
    TechnicalIndicators,
    MarketAnalytics,
    PriceAnalytics
)
from src.indicators import TechnicalIndicatorsCalculator, prepare_dataframe, analyze_trend
from src.utils.logger import setup_logger


class DataProcessor:
    """Main data processor for cryptocurrency market data"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = setup_logger(__name__)

        # Kafka
        self.kafka_consumer: Optional[AIOKafkaConsumer] = None
        self.kafka_producer: Optional[AIOKafkaProducer] = None

        # MongoDB
        self.mongo_client: Optional[AsyncIOMotorClient] = None
        self.db = None

        # Redis
        self.redis_client: Optional[aioredis.Redis] = None

        # Technical indicators calculator
        self.indicators_calculator = TechnicalIndicatorsCalculator(settings)

        # Data buffers - store recent data for each symbol
        # Key: symbol, Value: deque of max 500 data points
        self.data_buffers: Dict[str, deque] = defaultdict(lambda: deque(maxlen=500))

        # Status tracking
        self.status = ProcessingStatus.IDLE
        self.messages_processed = 0
        self.alerts_generated = 0
        self.errors = 0
        self.start_time = time.time()
        self.last_processed_time: Optional[datetime] = None

        # Recent alerts cache (keep last 100 alerts)
        self.recent_alerts: deque = deque(maxlen=100)

        # Processing control
        self._running = False

    # ===== INITIALIZATION =====

    async def initialize(self):
        """Initialize all connections (Kafka, MongoDB, Redis)"""
        self.logger.info("Initializing Data Processor")

        try:
            # Initialize Kafka consumer
            self.kafka_consumer = AIOKafkaConsumer(
                self.settings.kafka_topic_raw_data,
                bootstrap_servers=self.settings.kafka_brokers_list,
                group_id=self.settings.kafka_group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True
            )
            await self.kafka_consumer.start()
            self.logger.info("Kafka consumer initialized")

            # Initialize Kafka producer
            self.kafka_producer = AIOKafkaProducer(
                bootstrap_servers=self.settings.kafka_brokers_list,
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8')
            )
            await self.kafka_producer.start()
            self.logger.info("Kafka producer initialized")

            # Initialize MongoDB
            self.mongo_client = AsyncIOMotorClient(self.settings.mongodb_connection_string)
            self.db = self.mongo_client[self.settings.mongodb_database]
            # Create indexes
            await self._create_mongo_indexes()
            self.logger.info("MongoDB initialized")

            # Initialize Redis
            self.redis_client = await aioredis.from_url(
                f"redis://{self.settings.redis_host}:{self.settings.redis_port}",
                password=self.settings.redis_password,
                db=self.settings.redis_db,
                encoding="utf-8",
                decode_responses=True
            )
            self.logger.info("Redis initialized")

            self.logger.info("Data Processor initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize Data Processor: {e}")
            raise

    async def _create_mongo_indexes(self):
        """Create MongoDB indexes for better query performance"""
        try:
            # Processed data collection
            await self.db.processed_data.create_index([("symbol", 1), ("timestamp", -1)])
            await self.db.processed_data.create_index([("exchange", 1)])

            # Analytics collection
            await self.db.analytics.create_index([("symbol", 1), ("timestamp", -1)])

            # Alerts collection
            await self.db.alerts.create_index([("symbol", 1), ("timestamp", -1)])
            await self.db.alerts.create_index([("alert_type", 1)])

            self.logger.info("MongoDB indexes created")
        except Exception as e:
            self.logger.warning(f"Failed to create indexes: {e}")

    # ===== MAIN PROCESSING LOOP =====

    async def start_processing(self):
        """Start the main processing loop"""
        self._running = True
        self.status = ProcessingStatus.PROCESSING
        self.logger.info("Starting data processing loop")

        try:
            async for message in self.kafka_consumer:
                if not self._running:
                    break

                try:
                    await self._process_message(message.value)
                    self.messages_processed += 1
                    self.last_processed_time = datetime.utcnow()

                except Exception as e:
                    self.errors += 1
                    self.logger.error(f"Error processing message: {e}", exc_info=True)

        except asyncio.CancelledError:
            self.logger.info("Processing loop cancelled")
        except Exception as e:
            self.status = ProcessingStatus.ERROR
            self.logger.error(f"Fatal error in processing loop: {e}", exc_info=True)
        finally:
            self._running = False
            self.status = ProcessingStatus.STOPPED

    async def _process_message(self, message: Dict[str, Any]):
        """
        Process a single message from Kafka

        Args:
            message: Kafka message containing market data
        """
        try:
            # Extract the actual data from the message envelope
            # Message structure: {"type": "market_data", "data": {...}, "timestamp": "..."}
            if 'data' not in message:
                self.logger.warning("Message does not contain 'data' field")
                return

            data = message['data']

            # Parse raw market data
            raw_data = self._parse_raw_data(data)
            if not raw_data:
                return

            symbol = raw_data['symbol']
            exchange = raw_data['exchange']

            # Add to data buffer
            self.data_buffers[symbol].append(raw_data)

            # Check if we have enough data to calculate indicators
            if len(self.data_buffers[symbol]) < 20:
                self.logger.debug(f"Not enough data for {symbol}, skipping indicators")
                return

            # Prepare DataFrame for calculations
            df = prepare_dataframe(list(self.data_buffers[symbol]))

            if df.empty:
                return

            # Calculate technical indicators
            indicators = self.indicators_calculator.calculate_all_indicators(
                df, symbol, datetime.utcnow()
            )

            if not indicators:
                return

            # Analyze trend
            trend, confidence = analyze_trend(indicators)

            # Calculate price analytics
            price_analytics = self._calculate_price_analytics(df, symbol)

            # Create market analytics
            analytics = MarketAnalytics(
                symbol=symbol,
                exchange=exchange,
                timestamp=datetime.utcnow(),
                price_analytics=price_analytics,
                technical_indicators=indicators,
                market_trend=trend,
                confidence_score=confidence
            )

            # Generate alerts
            alerts = self._generate_alerts(symbol, indicators, price_analytics)

            # Store processed data
            processed_data = ProcessedData(
                symbol=symbol,
                exchange=exchange,
                timestamp=datetime.utcnow(),
                raw_data=raw_data,
                analytics=analytics.dict(),
                indicators=indicators.dict(),
                alerts=alerts
            )

            # Save to MongoDB
            await self._store_in_mongodb(processed_data)

            # Publish to Kafka
            await self._publish_analytics(analytics, alerts)

            # Cache in Redis
            await self._cache_analytics(symbol, analytics, indicators)

            self.logger.debug(f"Processed data for {symbol}")

        except Exception as e:
            self.logger.error(f"Error in _process_message: {e}", exc_info=True)
            raise

    def _parse_raw_data(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse and validate raw market data"""
        try:
            required_fields = ['symbol', 'exchange', 'timestamp', 'close']
            for field in required_fields:
                if field not in data:
                    self.logger.warning(f"Missing required field: {field}")
                    return None

            # Handle volume field - use base_volume if volume is null
            if 'volume' not in data or data['volume'] is None:
                if 'base_volume' in data:
                    data['volume'] = data['base_volume']
                else:
                    self.logger.warning(f"Missing volume data for {data.get('symbol', 'unknown')}")
                    data['volume'] = 0.0

            # Convert timestamp if needed
            if isinstance(data['timestamp'], str):
                data['timestamp'] = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
            elif isinstance(data['timestamp'], (int, float)):
                data['timestamp'] = datetime.fromtimestamp(data['timestamp'] / 1000)

            return data

        except Exception as e:
            self.logger.error(f"Error parsing raw data: {e}")
            return None

    def _calculate_price_analytics(self, df: pd.DataFrame, symbol: str) -> PriceAnalytics:
        """Calculate price analytics from DataFrame"""
        current_price = float(df['close'].iloc[-1])

        # Calculate price changes
        prices = df['close']
        price_change_1h = 0.0
        price_change_24h = 0.0
        price_change_7d = None

        if len(prices) >= 12:  # Assuming 5-min intervals, 12 = 1 hour
            price_1h_ago = prices.iloc[-12]
            price_change_1h = ((current_price - price_1h_ago) / price_1h_ago) * 100

        if len(prices) >= 288:  # 24 hours
            price_24h_ago = prices.iloc[-288]
            price_change_24h = ((current_price - price_24h_ago) / price_24h_ago) * 100

        if len(prices) >= 2016:  # 7 days
            price_7d_ago = prices.iloc[-2016]
            price_change_7d = ((current_price - price_7d_ago) / price_7d_ago) * 100

        # Calculate 24h high and low
        high_24h = float(df['high'].tail(288).max()) if len(df) >= 288 else float(df['high'].max())
        low_24h = float(df['low'].tail(288).min()) if len(df) >= 288 else float(df['low'].min())

        # Calculate volatility (standard deviation of returns)
        returns = prices.pct_change().dropna()
        volatility = float(returns.std() * 100) if len(returns) > 0 else 0.0

        return PriceAnalytics(
            current_price=current_price,
            price_change_1h=price_change_1h,
            price_change_24h=price_change_24h,
            price_change_7d=price_change_7d,
            high_24h=high_24h,
            low_24h=low_24h,
            volatility=volatility,
            timestamp=datetime.utcnow()
        )

    def _generate_alerts(
        self,
        symbol: str,
        indicators: TechnicalIndicators,
        price_analytics: PriceAnalytics
    ) -> List[Alert]:
        """Generate alerts based on indicators and price analytics"""
        alerts = []

        # RSI alerts
        if indicators.rsi:
            if indicators.rsi.overbought:
                alert = Alert(
                    symbol=symbol,
                    alert_type=AlertType.RSI_OVERBOUGHT,
                    severity=AlertSeverity.MEDIUM,
                    message=f"{symbol} RSI is overbought at {indicators.rsi.value:.2f}",
                    value=indicators.rsi.value,
                    threshold=self.settings.rsi_overbought,
                    timestamp=datetime.utcnow()
                )
                alerts.append(alert)

            if indicators.rsi.oversold:
                alert = Alert(
                    symbol=symbol,
                    alert_type=AlertType.RSI_OVERSOLD,
                    severity=AlertSeverity.MEDIUM,
                    message=f"{symbol} RSI is oversold at {indicators.rsi.value:.2f}",
                    value=indicators.rsi.value,
                    threshold=self.settings.rsi_oversold,
                    timestamp=datetime.utcnow()
                )
                alerts.append(alert)

        # MACD alerts
        if indicators.macd:
            if indicators.macd.bullish_crossover:
                alert = Alert(
                    symbol=symbol,
                    alert_type=AlertType.MACD_BULLISH,
                    severity=AlertSeverity.HIGH,
                    message=f"{symbol} MACD bullish crossover detected",
                    value=indicators.macd.histogram,
                    threshold=0.0,
                    timestamp=datetime.utcnow()
                )
                alerts.append(alert)

            if indicators.macd.bearish_crossover:
                alert = Alert(
                    symbol=symbol,
                    alert_type=AlertType.MACD_BEARISH,
                    severity=AlertSeverity.HIGH,
                    message=f"{symbol} MACD bearish crossover detected",
                    value=indicators.macd.histogram,
                    threshold=0.0,
                    timestamp=datetime.utcnow()
                )
                alerts.append(alert)

        # Bollinger Bands alerts
        if indicators.bollinger_bands:
            if indicators.bollinger_bands.breakout_upper or indicators.bollinger_bands.breakout_lower:
                alert = Alert(
                    symbol=symbol,
                    alert_type=AlertType.BOLLINGER_BREAKOUT,
                    severity=AlertSeverity.HIGH,
                    message=f"{symbol} Bollinger Bands breakout detected",
                    value=indicators.bollinger_bands.percent_b,
                    threshold=1.0 if indicators.bollinger_bands.breakout_upper else 0.0,
                    timestamp=datetime.utcnow()
                )
                alerts.append(alert)

        # Price change alerts
        if abs(price_analytics.price_change_1h) > self.settings.price_change_alert_threshold:
            alert_type = AlertType.PRICE_SPIKE if price_analytics.price_change_1h > 0 else AlertType.PRICE_DROP
            severity = AlertSeverity.HIGH if abs(price_analytics.price_change_1h) > 10 else AlertSeverity.MEDIUM

            alert = Alert(
                symbol=symbol,
                alert_type=alert_type,
                severity=severity,
                message=f"{symbol} price changed {price_analytics.price_change_1h:+.2f}% in 1 hour",
                value=price_analytics.price_change_1h,
                threshold=self.settings.price_change_alert_threshold,
                timestamp=datetime.utcnow()
            )
            alerts.append(alert)

        # Volume spike alerts
        if indicators.volume_indicators and indicators.volume_indicators.volume_spike:
            alert = Alert(
                symbol=symbol,
                alert_type=AlertType.VOLUME_SPIKE,
                severity=AlertSeverity.MEDIUM,
                message=f"{symbol} volume spike detected (ratio: {indicators.volume_indicators.volume_ratio:.2f}x)",
                value=indicators.volume_indicators.volume_ratio,
                threshold=self.settings.volume_spike_threshold,
                timestamp=datetime.utcnow()
            )
            alerts.append(alert)

        # Store alerts in recent cache
        for alert in alerts:
            self.recent_alerts.append(alert)
            self.alerts_generated += 1

        return alerts

    # ===== STORAGE =====

    async def _store_in_mongodb(self, processed_data: ProcessedData):
        """Store processed data in MongoDB"""
        try:
            # Store in processed_data collection
            await self.db.processed_data.insert_one(processed_data.dict())

            # Store analytics separately
            analytics_doc = {
                "symbol": processed_data.symbol,
                "exchange": processed_data.exchange,
                "timestamp": processed_data.timestamp,
                "analytics": processed_data.analytics,
                "indicators": processed_data.indicators
            }
            await self.db.analytics.insert_one(analytics_doc)

            # Store alerts separately
            if processed_data.alerts:
                for alert in processed_data.alerts:
                    await self.db.alerts.insert_one(alert.dict())

        except Exception as e:
            self.logger.error(f"Error storing in MongoDB: {e}")

    async def _publish_analytics(self, analytics: MarketAnalytics, alerts: List[Alert]):
        """Publish analytics and alerts to Kafka topics"""
        try:
            # Publish analytics
            await self.kafka_producer.send_and_wait(
                self.settings.kafka_topic_analytics,
                value=analytics.dict()
            )

            # Publish alerts
            if alerts:
                for alert in alerts:
                    await self.kafka_producer.send_and_wait(
                        self.settings.kafka_topic_alerts,
                        value=alert.dict()
                    )

        except Exception as e:
            self.logger.error(f"Error publishing to Kafka: {e}")

    async def _cache_analytics(
        self,
        symbol: str,
        analytics: MarketAnalytics,
        indicators: TechnicalIndicators
    ):
        """Cache analytics in Redis"""
        try:
            # Cache current analytics
            cache_key = f"analytics:{symbol}"
            await self.redis_client.setex(
                cache_key,
                self.settings.redis_ttl,
                json.dumps(analytics.dict(), default=str)
            )

            # Cache indicators
            indicators_key = f"indicators:{symbol}"
            await self.redis_client.setex(
                indicators_key,
                self.settings.redis_ttl,
                json.dumps(indicators.dict(), default=str)
            )

        except Exception as e:
            self.logger.error(f"Error caching in Redis: {e}")

    # ===== API METHODS =====

    async def health_check(self) -> bool:
        """Check if the processor is healthy"""
        try:
            # Check Kafka
            if not self.kafka_consumer or not self.kafka_producer:
                return False

            # Check MongoDB
            if not self.mongo_client:
                return False
            await self.mongo_client.admin.command('ping')

            # Check Redis
            if not self.redis_client:
                return False
            await self.redis_client.ping()

            return True

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False

    async def get_status(self) -> ProcessorStatus:
        """Get processor status"""
        uptime = time.time() - self.start_time
        symbols = list(self.data_buffers.keys())
        processing_rate = self.messages_processed / uptime if uptime > 0 else 0.0

        return ProcessorStatus(
            status=self.status,
            messages_processed=self.messages_processed,
            alerts_generated=self.alerts_generated,
            errors=self.errors,
            last_processed_time=self.last_processed_time,
            uptime_seconds=uptime,
            symbols_tracked=symbols,
            processing_rate=processing_rate
        )

    async def get_current_analytics(self) -> List[Dict[str, Any]]:
        """Get current analytics from cache"""
        try:
            analytics = []
            keys = await self.redis_client.keys("analytics:*")

            for key in keys:
                data = await self.redis_client.get(key)
                if data:
                    analytics.append(json.loads(data))

            return analytics

        except Exception as e:
            self.logger.error(f"Error getting current analytics: {e}")
            return []

    async def get_analytics_history(
        self,
        symbol: str,
        timeframe: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get analytics history from MongoDB"""
        try:
            cursor = self.db.analytics.find(
                {"symbol": symbol}
            ).sort("timestamp", -1).limit(limit)

            history = await cursor.to_list(length=limit)

            # Remove MongoDB _id field
            for item in history:
                if '_id' in item:
                    del item['_id']

            return history

        except Exception as e:
            self.logger.error(f"Error getting analytics history: {e}")
            return []

    async def get_technical_indicators(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get technical indicators for a symbol"""
        try:
            # Try cache first
            cache_key = f"indicators:{symbol}"
            cached = await self.redis_client.get(cache_key)

            if cached:
                return json.loads(cached)

            # Fall back to MongoDB
            result = await self.db.analytics.find_one(
                {"symbol": symbol},
                sort=[("timestamp", -1)]
            )

            if result and 'indicators' in result:
                if '_id' in result['indicators']:
                    del result['indicators']['_id']
                return result['indicators']

            return None

        except Exception as e:
            self.logger.error(f"Error getting technical indicators: {e}")
            return None

    async def get_recent_alerts(self) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        return [alert.dict() for alert in self.recent_alerts]

    # ===== CLEANUP =====

    async def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up Data Processor")
        self._running = False

        try:
            if self.kafka_consumer:
                await self.kafka_consumer.stop()

            if self.kafka_producer:
                await self.kafka_producer.stop()

            if self.mongo_client:
                self.mongo_client.close()

            if self.redis_client:
                await self.redis_client.close()

            self.logger.info("Data Processor cleanup completed")

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
