from datetime import datetime
from typing import List, Optional, Tuple
import pandas as pd
import numpy as np
from pandas import DataFrame, Series

from src.models import (
    RSIIndicator,
    MACDIndicator,
    BollingerBands,
    MovingAverages,
    VolumeIndicators,
    TechnicalIndicators
)
from src.config import Settings


class TechnicalIndicatorsCalculator:
    """Calculate technical indicators for market data"""

    def __init__(self, settings: Settings):
        self.settings = settings

    # ===== RSI (Relative Strength Index) =====

    def calculate_rsi(
        self,
        prices: Series,
        period: Optional[int] = None,
        timestamp: Optional[datetime] = None
    ) -> Optional[RSIIndicator]:
        """
        Calculate RSI (Relative Strength Index)

        Args:
            prices: Series of closing prices
            period: RSI period (default from settings)
            timestamp: Current timestamp

        Returns:
            RSIIndicator object or None if insufficient data
        """
        if period is None:
            period = self.settings.rsi_period

        if len(prices) < period + 1:
            return None

        # Calculate price changes
        delta = prices.diff()

        # Separate gains and losses
        gains = delta.where(delta > 0, 0.0)
        losses = -delta.where(delta < 0, 0.0)

        # Calculate average gains and losses
        avg_gains = gains.rolling(window=period, min_periods=period).mean()
        avg_losses = losses.rolling(window=period, min_periods=period).mean()

        # Calculate RS and RSI
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))

        current_rsi = rsi.iloc[-1]

        if pd.isna(current_rsi):
            return None

        return RSIIndicator(
            value=float(current_rsi),
            period=period,
            overbought=current_rsi > self.settings.rsi_overbought,
            oversold=current_rsi < self.settings.rsi_oversold,
            timestamp=timestamp or datetime.utcnow()
        )

    # ===== MACD (Moving Average Convergence Divergence) =====

    def calculate_macd(
        self,
        prices: Series,
        fast_period: Optional[int] = None,
        slow_period: Optional[int] = None,
        signal_period: Optional[int] = None,
        timestamp: Optional[datetime] = None
    ) -> Optional[MACDIndicator]:
        """
        Calculate MACD indicator

        Args:
            prices: Series of closing prices
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line period
            timestamp: Current timestamp

        Returns:
            MACDIndicator object or None if insufficient data
        """
        fast = fast_period or self.settings.macd_fast_period
        slow = slow_period or self.settings.macd_slow_period
        signal = signal_period or self.settings.macd_signal_period

        if len(prices) < slow + signal:
            return None

        # Calculate EMAs
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()

        # Calculate MACD line
        macd_line = ema_fast - ema_slow

        # Calculate signal line
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()

        # Calculate histogram
        histogram = macd_line - signal_line

        # Detect crossovers
        bullish_crossover = False
        bearish_crossover = False

        if len(histogram) >= 2:
            prev_hist = histogram.iloc[-2]
            curr_hist = histogram.iloc[-1]
            bullish_crossover = prev_hist < 0 and curr_hist > 0
            bearish_crossover = prev_hist > 0 and curr_hist < 0

        return MACDIndicator(
            macd_line=float(macd_line.iloc[-1]),
            signal_line=float(signal_line.iloc[-1]),
            histogram=float(histogram.iloc[-1]),
            bullish_crossover=bullish_crossover,
            bearish_crossover=bearish_crossover,
            timestamp=timestamp or datetime.utcnow()
        )

    # ===== Bollinger Bands =====

    def calculate_bollinger_bands(
        self,
        prices: Series,
        period: Optional[int] = None,
        std_dev: Optional[float] = None,
        timestamp: Optional[datetime] = None
    ) -> Optional[BollingerBands]:
        """
        Calculate Bollinger Bands

        Args:
            prices: Series of closing prices
            period: Period for moving average
            std_dev: Number of standard deviations
            timestamp: Current timestamp

        Returns:
            BollingerBands object or None if insufficient data
        """
        period = period or self.settings.bollinger_period
        std_dev = std_dev or self.settings.bollinger_std_dev

        if len(prices) < period:
            return None

        # Calculate middle band (SMA)
        middle_band = prices.rolling(window=period).mean()

        # Calculate standard deviation
        std = prices.rolling(window=period).std()

        # Calculate upper and lower bands
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)

        current_price = prices.iloc[-1]
        current_middle = middle_band.iloc[-1]
        current_upper = upper_band.iloc[-1]
        current_lower = lower_band.iloc[-1]

        if pd.isna(current_middle):
            return None

        # Calculate bandwidth and %B
        bandwidth = (current_upper - current_lower) / current_middle
        percent_b = (current_price - current_lower) / (current_upper - current_lower)

        # Detect breakouts
        breakout_upper = current_price > current_upper
        breakout_lower = current_price < current_lower

        return BollingerBands(
            upper_band=float(current_upper),
            middle_band=float(current_middle),
            lower_band=float(current_lower),
            bandwidth=float(bandwidth),
            percent_b=float(percent_b),
            breakout_upper=breakout_upper,
            breakout_lower=breakout_lower,
            timestamp=timestamp or datetime.utcnow()
        )

    # ===== Moving Averages (EMA and SMA) =====

    def calculate_moving_averages(
        self,
        prices: Series,
        timestamp: Optional[datetime] = None
    ) -> Optional[MovingAverages]:
        """
        Calculate various moving averages (EMA and SMA)

        Args:
            prices: Series of closing prices
            timestamp: Current timestamp

        Returns:
            MovingAverages object or None if insufficient data
        """
        if len(prices) < max(self.settings.ema_periods + self.settings.sma_periods):
            return None

        # Calculate EMAs
        emas = {}
        for period in self.settings.ema_periods:
            if len(prices) >= period:
                ema = prices.ewm(span=period, adjust=False).mean().iloc[-1]
                emas[f"ema_{period}"] = float(ema) if not pd.isna(ema) else None

        # Calculate SMAs
        smas = {}
        for period in self.settings.sma_periods:
            if len(prices) >= period:
                sma = prices.rolling(window=period).mean().iloc[-1]
                smas[f"sma_{period}"] = float(sma) if not pd.isna(sma) else None

        # Detect golden cross and death cross
        golden_cross = False
        death_cross = False

        if len(prices) >= 200:
            ema_50_series = prices.ewm(span=50, adjust=False).mean()
            ema_200_series = prices.ewm(span=200, adjust=False).mean()

            if len(ema_50_series) >= 2 and len(ema_200_series) >= 2:
                prev_50 = ema_50_series.iloc[-2]
                curr_50 = ema_50_series.iloc[-1]
                prev_200 = ema_200_series.iloc[-2]
                curr_200 = ema_200_series.iloc[-1]

                golden_cross = prev_50 < prev_200 and curr_50 > curr_200
                death_cross = prev_50 > prev_200 and curr_50 < curr_200

        return MovingAverages(
            ema_12=emas.get("ema_12"),
            ema_26=emas.get("ema_26"),
            ema_50=emas.get("ema_50"),
            ema_200=emas.get("ema_200"),
            sma_20=smas.get("sma_20"),
            sma_50=smas.get("sma_50"),
            sma_100=smas.get("sma_100"),
            sma_200=smas.get("sma_200"),
            golden_cross=golden_cross,
            death_cross=death_cross,
            timestamp=timestamp or datetime.utcnow()
        )

    # ===== Volume Indicators =====

    def calculate_volume_indicators(
        self,
        volumes: Series,
        prices: Series,
        timestamp: Optional[datetime] = None
    ) -> Optional[VolumeIndicators]:
        """
        Calculate volume-based indicators

        Args:
            volumes: Series of trading volumes
            prices: Series of closing prices (for OBV)
            timestamp: Current timestamp

        Returns:
            VolumeIndicators object or None if insufficient data
        """
        if len(volumes) < 20:
            return None

        current_volume = volumes.iloc[-1]
        avg_volume = volumes.rolling(window=20).mean().iloc[-1]

        if pd.isna(avg_volume) or avg_volume == 0:
            return None

        volume_ratio = current_volume / avg_volume
        volume_spike = volume_ratio > self.settings.volume_spike_threshold

        # Calculate On-Balance Volume (OBV)
        obv = None
        if len(prices) == len(volumes):
            price_changes = prices.diff()
            obv_values = volumes.copy()
            obv_values[price_changes < 0] = -obv_values[price_changes < 0]
            obv_values[price_changes == 0] = 0
            obv = float(obv_values.cumsum().iloc[-1])

        return VolumeIndicators(
            current_volume=float(current_volume),
            avg_volume=float(avg_volume),
            volume_ratio=float(volume_ratio),
            volume_spike=volume_spike,
            on_balance_volume=obv,
            timestamp=timestamp or datetime.utcnow()
        )

    # ===== Calculate All Indicators =====

    def calculate_all_indicators(
        self,
        df: DataFrame,
        symbol: str,
        timestamp: Optional[datetime] = None
    ) -> Optional[TechnicalIndicators]:
        """
        Calculate all technical indicators for a symbol

        Args:
            df: DataFrame with OHLCV data (columns: open, high, low, close, volume)
            symbol: Trading pair symbol
            timestamp: Current timestamp

        Returns:
            TechnicalIndicators object with all calculated indicators
        """
        if df is None or len(df) == 0:
            return None

        timestamp = timestamp or datetime.utcnow()

        # Extract price and volume series
        prices = df['close']
        volumes = df['volume']

        # Calculate all indicators
        rsi = self.calculate_rsi(prices, timestamp=timestamp)
        macd = self.calculate_macd(prices, timestamp=timestamp)
        bollinger = self.calculate_bollinger_bands(prices, timestamp=timestamp)
        moving_avgs = self.calculate_moving_averages(prices, timestamp=timestamp)
        volume_indicators = self.calculate_volume_indicators(volumes, prices, timestamp=timestamp)

        return TechnicalIndicators(
            symbol=symbol,
            timestamp=timestamp,
            rsi=rsi,
            macd=macd,
            bollinger_bands=bollinger,
            moving_averages=moving_avgs,
            volume_indicators=volume_indicators
        )


# ===== Utility Functions =====

def prepare_dataframe(data: List[dict]) -> DataFrame:
    """
    Prepare DataFrame from raw data

    Args:
        data: List of OHLCV data dictionaries

    Returns:
        Pandas DataFrame with proper index and columns
    """
    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    # Ensure required columns exist
    required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    for col in required_cols:
        if col not in df.columns:
            return pd.DataFrame()

    # Convert timestamp to datetime
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)

    # Sort by timestamp
    df.sort_index(inplace=True)

    return df


def analyze_trend(indicators: TechnicalIndicators) -> Tuple[str, float]:
    """
    Analyze market trend based on technical indicators

    Args:
        indicators: TechnicalIndicators object

    Returns:
        Tuple of (trend: str, confidence: float)
        trend can be "bullish", "bearish", or "neutral"
        confidence is a score from 0 to 1
    """
    bullish_signals = 0
    bearish_signals = 0
    total_signals = 0

    # RSI signals
    if indicators.rsi:
        total_signals += 1
        if indicators.rsi.oversold:
            bullish_signals += 1
        elif indicators.rsi.overbought:
            bearish_signals += 1

    # MACD signals
    if indicators.macd:
        total_signals += 1
        if indicators.macd.histogram > 0:
            bullish_signals += 1
        elif indicators.macd.histogram < 0:
            bearish_signals += 1

        if indicators.macd.bullish_crossover:
            bullish_signals += 1
            total_signals += 1
        elif indicators.macd.bearish_crossover:
            bearish_signals += 1
            total_signals += 1

    # Moving averages signals
    if indicators.moving_averages:
        if indicators.moving_averages.golden_cross:
            bullish_signals += 2
            total_signals += 1
        elif indicators.moving_averages.death_cross:
            bearish_signals += 2
            total_signals += 1

    # Bollinger Bands signals
    if indicators.bollinger_bands:
        total_signals += 1
        if indicators.bollinger_bands.percent_b < 0.2:
            bullish_signals += 1
        elif indicators.bollinger_bands.percent_b > 0.8:
            bearish_signals += 1

    # Determine trend
    if total_signals == 0:
        return "neutral", 0.0

    bullish_ratio = bullish_signals / total_signals
    bearish_ratio = bearish_signals / total_signals

    if bullish_ratio > 0.6:
        return "bullish", bullish_ratio
    elif bearish_ratio > 0.6:
        return "bearish", bearish_ratio
    else:
        return "neutral", max(bullish_ratio, bearish_ratio)
