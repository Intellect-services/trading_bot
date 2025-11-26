"""Feature engineering for AI trading strategies.

This module provides utilities to create feature-ready datasets from market data,
news, sentiment, and fundamental data for ML model training.
"""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Creates feature-ready datasets for ML model training."""

    def __init__(self) -> None:
        """Initialize the feature engineer."""
        self.logger = logging.getLogger(__name__)

    def create_features(
        self,
        market_data: pd.DataFrame,
        news_data: pd.DataFrame | None = None,
        sentiment_data: pd.DataFrame | None = None,
        fundamental_data: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        """Create a feature-ready dataset from multiple data sources.

        Args:
            market_data: DataFrame with OHLCV data (must have timestamp index)
            news_data: Optional DataFrame with news articles (columns: timestamp, sentiment, relevance)
            sentiment_data: Optional DataFrame with sentiment scores (columns: timestamp, score)
            fundamental_data: Optional DataFrame with fundamental metrics (columns: timestamp, pe, pb, etc.)

        Returns:
            DataFrame with engineered features ready for ML training
        """
        if market_data.empty:
            self.logger.warning("Empty market data provided")
            return pd.DataFrame()

        features = market_data.copy()

        # Add technical indicators as features
        features = self._add_technical_indicators(features)

        # Add price-based features
        features = self._add_price_features(features)

        # Add volume-based features
        features = self._add_volume_features(features)

        # Add time-based features
        features = self._add_time_features(features)

        # Merge news/sentiment data if available
        if news_data is not None and not news_data.empty:
            features = self._merge_news_features(features, news_data)

        if sentiment_data is not None and not sentiment_data.empty:
            features = self._merge_sentiment_features(features, sentiment_data)

        # Merge fundamental data if available
        if fundamental_data is not None and not fundamental_data.empty:
            features = self._merge_fundamental_features(features, fundamental_data)

        # Add lagged features for time-series context
        features = self._add_lagged_features(features, windows=[1, 2, 5, 10, 20])

        # Add rolling statistics
        features = self._add_rolling_statistics(features)

        # Remove NaN values from the start (due to rolling windows)
        return features.dropna()

    def _add_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators as features.

        Args:
            data: Market data DataFrame

        Returns:
            DataFrame with technical indicator columns added
        """
        df = data.copy()

        # RSI
        if "close" in df.columns:
            df["rsi"] = self._calculate_rsi(df["close"], window=14)

        # MACD
        if "close" in df.columns:
            macd, signal, histogram = self._calculate_macd(df["close"])
            df["macd"] = macd
            df["macd_signal"] = signal
            df["macd_histogram"] = histogram

        # Moving averages
        if "close" in df.columns:
            df["sma_10"] = df["close"].rolling(window=10).mean()
            df["sma_20"] = df["close"].rolling(window=20).mean()
            df["sma_50"] = df["close"].rolling(window=50).mean()
            df["ema_12"] = df["close"].ewm(span=12, adjust=False).mean()
            df["ema_26"] = df["close"].ewm(span=26, adjust=False).mean()

        # Bollinger Bands
        if "close" in df.columns:
            sma = df["close"].rolling(window=20).mean()
            std = df["close"].rolling(window=20).std()
            df["bb_upper"] = sma + (std * 2)
            df["bb_lower"] = sma - (std * 2)
            df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / sma
            df["bb_position"] = (df["close"] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"])

        return df

    def _add_price_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add price-based features.

        Args:
            data: Market data DataFrame

        Returns:
            DataFrame with price features added
        """
        df = data.copy()

        if "close" not in df.columns:
            return df

        # Returns
        df["returns"] = df["close"].pct_change()
        df["log_returns"] = np.log(df["close"] / df["close"].shift(1))
        df["returns_5d"] = df["close"].pct_change(5)
        df["returns_10d"] = df["close"].pct_change(10)
        df["returns_20d"] = df["close"].pct_change(20)

        # Price position within high-low range
        if all(col in df.columns for col in ["high", "low", "close"]):
            df["price_position"] = (df["close"] - df["low"]) / (df["high"] - df["low"] + 1e-8)

        # Volatility
        df["volatility_5d"] = df["returns"].rolling(window=5).std()
        df["volatility_20d"] = df["returns"].rolling(window=20).std()

        # High-low spread
        if all(col in df.columns for col in ["high", "low"]):
            df["hl_spread"] = (df["high"] - df["low"]) / df["close"]
            df["hl_spread_pct"] = df["hl_spread"] * 100

        return df

    def _add_volume_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add volume-based features.

        Args:
            data: Market data DataFrame

        Returns:
            DataFrame with volume features added
        """
        df = data.copy()

        if "volume" not in df.columns:
            return df

        # Volume moving averages
        df["volume_sma_10"] = df["volume"].rolling(window=10).mean()
        df["volume_sma_20"] = df["volume"].rolling(window=20).mean()

        # Volume ratio (current vs average)
        df["volume_ratio"] = df["volume"] / (df["volume_sma_20"] + 1e-8)

        # Volume-price trend
        if "close" in df.columns:
            df["vpt"] = (df["volume"] * df["returns"]).cumsum()

        # On-balance volume
        if "close" in df.columns:
            df["obv"] = (df["volume"] * np.sign(df["close"].diff())).fillna(0).cumsum()

        return df

    def _add_time_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add time-based features.

        Args:
            data: Market data DataFrame with datetime index

        Returns:
            DataFrame with time features added
        """
        df = data.copy()

        if not isinstance(df.index, pd.DatetimeIndex):
            return df

        # Day of week (0=Monday, 6=Sunday)
        df["day_of_week"] = df.index.dayofweek

        # Day of month
        df["day_of_month"] = df.index.day

        # Month
        df["month"] = df.index.month

        # Quarter
        df["quarter"] = df.index.quarter

        # Is market open (simplified - assumes weekdays)
        df["is_weekday"] = (df.index.dayofweek < 5).astype(int)

        # Cyclical encoding for day of week
        df["day_of_week_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
        df["day_of_week_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)

        return df

    def _add_lagged_features(self, data: pd.DataFrame, windows: list[int]) -> pd.DataFrame:
        """Add lagged features for time-series context.

        Args:
            data: Feature DataFrame
            windows: List of lag windows to create

        Returns:
            DataFrame with lagged features
        """
        df = data.copy()

        # Key features to lag
        lag_features = ["close", "volume", "returns"]
        if "rsi" in df.columns:
            lag_features.append("rsi")
        if "macd" in df.columns:
            lag_features.append("macd")

        for feature in lag_features:
            if feature in df.columns:
                for window in windows:
                    df[f"{feature}_lag_{window}"] = df[feature].shift(window)

        return df

    def _add_rolling_statistics(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add rolling window statistics.

        Args:
            data: Feature DataFrame

        Returns:
            DataFrame with rolling statistics
        """
        df = data.copy()

        if "close" not in df.columns:
            return df

        windows = [5, 10, 20]
        for window in windows:
            df[f"close_rolling_mean_{window}"] = df["close"].rolling(window=window).mean()
            df[f"close_rolling_std_{window}"] = df["close"].rolling(window=window).std()
            df[f"close_rolling_min_{window}"] = df["close"].rolling(window=window).min()
            df[f"close_rolling_max_{window}"] = df["close"].rolling(window=window).max()

        return df

    def _merge_news_features(self, features: pd.DataFrame, news_data: pd.DataFrame) -> pd.DataFrame:
        """Merge news data into features.

        Args:
            features: Feature DataFrame
            news_data: News DataFrame with timestamp index

        Returns:
            DataFrame with news features merged
        """
        if not isinstance(features.index, pd.DatetimeIndex):
            return features

        news_df = news_data.copy()
        if not isinstance(news_df.index, pd.DatetimeIndex) and "timestamp" in news_df.columns:
            news_df["timestamp"] = pd.to_datetime(news_df["timestamp"])
            news_df.set_index("timestamp", inplace=True)

        # Aggregate news by time period (daily)
        if "sentiment" in news_df.columns:
            daily_sentiment = news_df["sentiment"].resample("D").mean()
            features["news_sentiment"] = daily_sentiment.reindex(features.index, method="ffill")

        if "relevance" in news_df.columns:
            daily_relevance = news_df["relevance"].resample("D").mean()
            features["news_relevance"] = daily_relevance.reindex(features.index, method="ffill")

        # News count per day
        news_df["count"] = 1
        daily_count = news_df["count"].resample("D").sum()
        features["news_count"] = daily_count.reindex(features.index, method="ffill").fillna(0)

        return features

    def _merge_sentiment_features(
        self, features: pd.DataFrame, sentiment_data: pd.DataFrame
    ) -> pd.DataFrame:
        """Merge sentiment data into features.

        Args:
            features: Feature DataFrame
            sentiment_data: Sentiment DataFrame with timestamp index

        Returns:
            DataFrame with sentiment features merged
        """
        if not isinstance(features.index, pd.DatetimeIndex):
            return features

        sentiment_df = sentiment_data.copy()
        if (
            not isinstance(sentiment_df.index, pd.DatetimeIndex)
            and "timestamp" in sentiment_df.columns
        ):
            sentiment_df["timestamp"] = pd.to_datetime(sentiment_df["timestamp"])
            sentiment_df.set_index("timestamp", inplace=True)

        if "score" in sentiment_df.columns:
            # Resample to match feature frequency
            daily_sentiment = sentiment_df["score"].resample("D").mean()
            features["sentiment_score"] = daily_sentiment.reindex(features.index, method="ffill")
            features["sentiment_score_ma"] = features["sentiment_score"].rolling(window=5).mean()

        return features

    def _merge_fundamental_features(
        self, features: pd.DataFrame, fundamental_data: pd.DataFrame
    ) -> pd.DataFrame:
        """Merge fundamental data into features.

        Args:
            features: Feature DataFrame
            fundamental_data: Fundamental DataFrame with timestamp index

        Returns:
            DataFrame with fundamental features merged
        """
        if not isinstance(features.index, pd.DatetimeIndex):
            return features

        fund_df = fundamental_data.copy()
        if not isinstance(fund_df.index, pd.DatetimeIndex) and "timestamp" in fund_df.columns:
            fund_df["timestamp"] = pd.to_datetime(fund_df["timestamp"])
            fund_df.set_index("timestamp", inplace=True)

        # Forward fill fundamental data (updated quarterly)
        fundamental_cols = ["pe", "pb", "debt_to_equity", "roe", "roa"]
        for col in fundamental_cols:
            if col in fund_df.columns:
                features[col] = fund_df[col].reindex(features.index, method="ffill")

        return features

    @staticmethod
    def _calculate_rsi(prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate RSI indicator.

        Args:
            prices: Price series
            window: RSI window period

        Returns:
            RSI series
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / (loss + 1e-8)
        return 100 - (100 / (1 + rs))

    @staticmethod
    def _calculate_macd(
        prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD indicator.

        Args:
            prices: Price series
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line period

        Returns:
            Tuple of (MACD line, Signal line, Histogram)
        """
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        return macd, signal_line, histogram

    def create_label_for_classification(
        self,
        features: pd.DataFrame,
        forward_window: int = 5,
        profit_threshold: float = 0.02,
    ) -> pd.Series:
        """Create classification labels (buy/hold/sell) for training.

        Args:
            features: Feature DataFrame
            forward_window: Number of periods to look ahead
            profit_threshold: Minimum profit threshold to trigger buy/sell signal

        Returns:
            Series with labels: 1=buy, 0=hold, -1=sell
        """
        if "close" not in features.columns:
            raise ValueError("Features must contain 'close' column")

        labels = pd.Series(0, index=features.index, dtype=int)

        # Calculate forward returns
        forward_returns = features["close"].shift(-forward_window) / features["close"] - 1

        # Buy signal: forward return > threshold
        labels[forward_returns > profit_threshold] = 1

        # Sell signal: forward return < -threshold
        labels[forward_returns < -profit_threshold] = -1

        return labels

    def create_label_for_regression(
        self,
        features: pd.DataFrame,
        forward_window: int = 5,
    ) -> pd.Series:
        """Create regression labels (expected return) for training.

        Args:
            features: Feature DataFrame
            forward_window: Number of periods to look ahead

        Returns:
            Series with expected returns
        """
        if "close" not in features.columns:
            raise ValueError("Features must contain 'close' column")

        return features["close"].shift(-forward_window) / features["close"] - 1
