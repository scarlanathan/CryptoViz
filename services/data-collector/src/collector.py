"""
Main data collector class using asyncio and ccxt
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

import ccxt.async_support as ccxt
import redis.asyncio as aioredis
from aiokafka import AIOKafkaProducer

from .config import Settings
from .models import (
    CollectorStatus, CollectionStatus, MarketData,
    ExchangeInfo, SymbolInfo, CollectionMetrics
)
from .utils.rate_limiter import RateLimiter
from .utils.logger import setup_logger


class DataCollector:
    """Main data collector class"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = setup_logger(__name__)

        # State
        self.is_running = False
        self.start_time = time.time()
        self.exchanges: Dict[str, ccxt.Exchange] = {}
        self.collection_count = 0
        self.error_count = 0
        self.last_collection_time: Optional[datetime] = None

        # Async components
        self.kafka_producer: Optional[AIOKafkaProducer] = None
        self.redis_client: Optional[aioredis.Redis] = None
        self.rate_limiter: Optional[RateLimiter] = None

        # Tasks
        self.collection_task: Optional[asyncio.Task] = None
        self.health_check_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize the data collector"""
        self.logger.info("Initializing Data Collector")

        try:
            # Initialize Redis
            self.redis_client = aioredis.from_url(
                f"redis://:{self.settings.redis_password}@{self.settings.redis_host}:{self.settings.redis_port}/{self.settings.redis_db}",
                encoding="utf-8",
                decode_responses=True
            )

            # Initialize Kafka producer with retry logic
            max_retries = 5
            retry_delay = 2
            for attempt in range(max_retries):
                try:
                    self.kafka_producer = AIOKafkaProducer(
                        bootstrap_servers=self.settings.kafka_brokers,
                        client_id=self.settings.kafka_client_id,
                        value_serializer=lambda v: v.encode('utf-8') if isinstance(v, str) else v
                    )
                    await self.kafka_producer.start()
                    self.logger.info(f"Connected to Kafka at {self.settings.kafka_brokers}")
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        self.logger.warning(
                            f"Failed to connect to Kafka (attempt {attempt + 1}/{max_retries}): {e}. "
                            f"Retrying in {retry_delay}s..."
                        )
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        self.logger.error(f"Failed to connect to Kafka after {max_retries} attempts")
                        raise

            # Initialize rate limiter
            self.rate_limiter = RateLimiter(
                max_requests=self.settings.max_requests_per_minute,
                window_seconds=self.settings.rate_limit_window
            )

            # Initialize exchanges
            await self._initialize_exchanges()

            # Start health check task
            self.health_check_task = asyncio.create_task(self._health_check_loop())

            self.logger.info("Data Collector initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize Data Collector: {e}")
            raise

    async def _initialize_exchanges(self):
        """Initialize cryptocurrency exchanges"""
        for exchange_id in self.settings.exchanges_to_use:
            try:
                # Create exchange instance
                exchange_class = getattr(ccxt, exchange_id)

                # Configure exchange
                config = {
                    'apiKey': getattr(self.settings, f"{exchange_id}_api_key", None),
                    'secret': getattr(self.settings, f"{exchange_id}_secret", None),
                    'timeout': 30000,
                    'rateLimit': 1200,  # ms
                    'enableRateLimit': True,
                    'sandbox': False,
                }

                # Remove None values
                config = {k: v for k, v in config.items() if v is not None}

                exchange = exchange_class(config)

                # Test connection
                await exchange.load_markets()

                self.exchanges[exchange_id] = exchange
                self.logger.info(f"Initialized exchange: {exchange_id}")

            except Exception as e:
                self.logger.error(f"Failed to initialize exchange {exchange_id}: {e}")

    async def start_collection(self):
        """Start data collection"""
        if self.is_running:
            self.logger.warning("Collection is already running")
            return

        self.logger.info("Starting data collection")
        self.is_running = True

        # Start collection task
        self.collection_task = asyncio.create_task(self._collection_loop())

    async def stop_collection(self):
        """Stop data collection"""
        if not self.is_running:
            self.logger.warning("Collection is not running")
            return

        self.logger.info("Stopping data collection")
        self.is_running = False

        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass

    async def _collection_loop(self):
        """Main collection loop"""
        while self.is_running:
            try:
                start_time = time.time()

                # Collect data from all exchanges
                tasks = []
                for exchange_id, exchange in self.exchanges.items():
                    task = asyncio.create_task(
                        self._collect_from_exchange(exchange_id, exchange)
                    )
                    tasks.append(task)

                # Wait for all collections to complete
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)

                self.collection_count += 1
                self.last_collection_time = datetime.utcnow()

                collection_time = time.time() - start_time
                self.logger.info(f"Collection cycle completed in {collection_time:.2f}s")

                # Wait for next collection
                await asyncio.sleep(self.settings.collection_interval)

            except asyncio.CancelledError:
                self.logger.info("Collection loop cancelled")
                break
            except Exception as e:
                self.error_count += 1
                self.logger.error(f"Error in collection loop: {e}")
                await asyncio.sleep(5)  # Short delay before retry

    async def _collect_from_exchange(self, exchange_id: str, exchange: ccxt.Exchange):
        """Collect data from a specific exchange"""
        try:
            # Apply rate limiting
            await self.rate_limiter.acquire()

            for symbol in self.settings.symbols_to_collect:
                try:
                    # Check if symbol exists on this exchange
                    if symbol not in exchange.markets:
                        continue

                    # Fetch ticker data
                    ticker = await exchange.fetch_ticker(symbol)

                    # Create market data object
                    market_data = MarketData(
                        symbol=symbol,
                        exchange=exchange_id,
                        timestamp=datetime.utcnow(),
                        open=ticker.get('open'),
                        high=ticker.get('high'),
                        low=ticker.get('low'),
                        close=ticker.get('close'),
                        volume=ticker.get('volume'),
                        bid=ticker.get('bid'),
                        ask=ticker.get('ask'),
                        bid_volume=ticker.get('bidVolume'),
                        ask_volume=ticker.get('askVolume'),
                        vwap=ticker.get('vwap'),
                        change=ticker.get('change'),
                        percentage=ticker.get('percentage'),
                        average=ticker.get('average'),
                        base_volume=ticker.get('baseVolume'),
                        quote_volume=ticker.get('quoteVolume')
                    )

                    # Send to Kafka
                    await self._send_to_kafka(market_data)

                    # Cache in Redis
                    await self._cache_data(market_data)

                except Exception as e:
                    self.logger.error(f"Error collecting {symbol} from {exchange_id}: {e}")

        except Exception as e:
            self.logger.error(f"Error collecting from exchange {exchange_id}: {e}")

    async def _send_to_kafka(self, data: MarketData):
        """Send data to Kafka"""
        try:
            import json

            # Use Pydantic's model_dump with mode='json' to handle datetime serialization
            message = {
                "type": "market_data",
                "data": data.model_dump(mode='json'),
                "timestamp": datetime.utcnow().isoformat()
            }

            await self.kafka_producer.send(
                self.settings.kafka_topic_raw_data,
                key=f"{data.exchange}_{data.symbol}".encode('utf-8'),
                value=json.dumps(message).encode('utf-8')
            )

        except Exception as e:
            self.logger.error(f"Error sending to Kafka: {e}")

    async def _cache_data(self, data: MarketData):
        """Cache data in Redis"""
        try:
            key = f"market_data:{data.exchange}:{data.symbol}"
            value = data.json()

            await self.redis_client.setex(
                key,
                self.settings.cache_ttl,
                value
            )

        except Exception as e:
            self.logger.error(f"Error caching data: {e}")

    async def _health_check_loop(self):
        """Health check loop"""
        while True:
            try:
                await asyncio.sleep(self.settings.health_check_interval)

                # Check Redis connection
                await self.redis_client.ping()

                # Check Kafka connection
                # (AIOKafkaProducer doesn't have a simple ping method)

                # Check exchanges
                for exchange_id, exchange in self.exchanges.items():
                    try:
                        await exchange.fetch_status()
                    except Exception as e:
                        self.logger.warning(f"Exchange {exchange_id} health check failed: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health check error: {e}")

    async def health_check(self) -> bool:
        """Perform health check"""
        try:
            # Check Redis
            await self.redis_client.ping()

            # Check if at least one exchange is working
            if not self.exchanges:
                return False

            return True

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False

    async def get_status(self) -> CollectorStatus:
        """Get collector status"""
        uptime = time.time() - self.start_time

        return CollectorStatus(
            status=CollectionStatus.RUNNING if self.is_running else CollectionStatus.STOPPED,
            active_exchanges=list(self.exchanges.keys()),
            symbols_count=len(self.settings.symbols_to_collect),
            last_collection=self.last_collection_time,
            collections_today=self.collection_count,
            errors_count=self.error_count,
            uptime_seconds=uptime
        )

    async def get_exchanges(self) -> List[str]:
        """Get list of available exchanges"""
        return list(self.exchanges.keys())

    async def get_symbols(self, exchange_id: str) -> List[str]:
        """Get available symbols for an exchange"""
        if exchange_id not in self.exchanges:
            raise ValueError(f"Exchange {exchange_id} not available")

        exchange = self.exchanges[exchange_id]
        return list(exchange.markets.keys())

    async def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up Data Collector")

        # Stop collection
        await self.stop_collection()

        # Cancel health check task
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass

        # Close exchanges
        for exchange in self.exchanges.values():
            await exchange.close()

        # Close Kafka producer
        if self.kafka_producer:
            await self.kafka_producer.stop()

        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()

        self.logger.info("Data Collector cleanup completed")