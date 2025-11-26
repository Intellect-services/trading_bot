"""AI-Enhanced Trading Strategy with confidence thresholds and safeguards."""

import logging
from typing import Any

import numpy as np
import pandas as pd

from src.core.strategy import Strategy
from src.ml.feature_engineering import FeatureEngineer
from src.ml.model_interface import MLModel

logger = logging.getLogger(__name__)


class AIStrategyConfig:
    """Configuration for AI Strategy."""

    def __init__(
        self,
        model: MLModel,
        min_confidence: float = 0.65,  # Minimum confidence threshold (conservative default)
        max_position_size: float = 0.05,  # Max 5% of portfolio per trade (conservative)
        fallback_enabled: bool = True,
        fallback_strategy: Strategy | None = None,
        enable_risk_checks: bool = True,
        max_daily_trades: int = 5,  # Limit trading frequency
        model_version: str = "1.0.0",
    ) -> None:
        """Initialize AI Strategy configuration.

        Args:
            model: Trained ML model
            min_confidence: Minimum prediction confidence to execute trade
            max_position_size: Maximum position size as fraction of portfolio
            fallback_enabled: Enable fallback to classical strategy
            fallback_strategy: Fallback strategy instance
            enable_risk_checks: Enable additional risk validation
            max_daily_trades: Maximum number of trades per day
            model_version: Model version string
        """
        self.model = model
        self.min_confidence = min_confidence
        self.max_position_size = max_position_size
        self.fallback_enabled = fallback_enabled
        self.fallback_strategy = fallback_strategy
        self.enable_risk_checks = enable_risk_checks
        self.max_daily_trades = max_daily_trades
        self.model_version = model_version


class AIStrategy(Strategy):
    """AI-Enhanced trading strategy with safety mechanisms.

    This strategy uses ML models to generate trading signals while implementing
    multiple safeguards to protect capital:
    - Confidence thresholds
    - Position size limits
    - Fallback to classical strategies
    - Risk validation checks
    - Trading frequency limits
    """

    def __init__(self, config: AIStrategyConfig) -> None:
        """Initialize AI Strategy.

        Args:
            config: AI Strategy configuration
        """
        super().__init__()
        self.config = config
        self.feature_engineer = FeatureEngineer()
        self.logger = logging.getLogger(self.__class__.__name__)

        # Track daily trade count
        self.daily_trades: dict[str, int] = {}  # date -> count

        # Performance tracking
        self.signal_history: list[dict[str, Any]] = []

        self.logger.info(
            f"Initialized AI Strategy with model version {config.model_version}, "
            f"min_confidence={config.min_confidence}"
        )

    def generate_signals(self, bars: pd.DataFrame) -> list[dict[str, Any]]:
        """Generate trading signals using AI model with safety checks.

        Args:
            bars: DataFrame containing OHLCV price data

        Returns:
            List of signal dictionaries
        """
        if bars.empty or len(bars) < 50:  # Need minimum data for features
            self.logger.warning("Insufficient data for AI strategy")
            return []

        signals: list[dict[str, Any]] = []

        try:
            # Create features from market data
            features = self.feature_engineer.create_features(market_data=bars)

            if features.empty:
                self.logger.warning("Failed to create features")
                return self._try_fallback(bars)

            # Get latest features for prediction
            latest_features = features.iloc[[-1]].copy()

            # Remove NaN values
            latest_features = latest_features.ffill().fillna(0)

            # Get model predictions
            predictions = self.config.model.predict(latest_features)
            probabilities = self.config.model.predict_proba(latest_features)

            # Extract prediction and confidence
            if len(predictions.shape) > 1:
                prediction = predictions[0, 0] if predictions.shape[1] > 0 else predictions[0]
            else:
                prediction = predictions[0]

            # Calculate confidence from probabilities
            if probabilities.ndim == 2:
                # Classification: use max probability as confidence
                confidence = float(np.max(probabilities[0]))
                predicted_class = int(np.argmax(probabilities[0]))
            else:
                # Regression: use prediction magnitude normalized
                confidence = float(abs(prediction)) if abs(prediction) <= 1.0 else 1.0
                predicted_class = 1 if prediction > 0 else -1

            # Check confidence threshold
            if confidence < self.config.min_confidence:
                self.logger.info(
                    f"Signal rejected: confidence {confidence:.3f} < threshold {self.config.min_confidence}"
                )
                return self._try_fallback(bars)

            # Check daily trade limit
            today = pd.Timestamp.now().date().isoformat()
            if self._exceeded_daily_limit(today):
                self.logger.warning(f"Daily trade limit reached ({self.config.max_daily_trades})")
                return []

            # Generate signal based on prediction
            latest_bar = bars.iloc[-1]
            price = float(latest_bar.get("close", 0))

            if price <= 0:
                self.logger.warning("Invalid price in signal generation")
                return []

            # Determine action
            if predicted_class == 1 or (isinstance(prediction, (int, float)) and prediction > 0.1):
                action = "buy"
            elif predicted_class == -1 or (
                isinstance(prediction, (int, float)) and prediction < -0.1
            ):
                action = "sell"
            else:
                action = "hold"

            if action == "hold":
                return []

            # Calculate position size based on confidence
            position_size = self._calculate_position_size(confidence, price)

            # Create signal
            signal = {
                "symbol": bars.get("symbol", ["UNKNOWN"])[-1]
                if "symbol" in bars.columns
                else "UNKNOWN",
                "action": action,
                "side": "long" if action == "buy" else "short",
                "price": price,
                "strength": confidence * 100,  # Convert to 0-100 scale
                "confidence": confidence,
                "model_prediction": float(prediction),
                "model_version": self.config.model_version,
                "timestamp": bars.index[-1]
                if isinstance(bars.index, pd.DatetimeIndex)
                else pd.Timestamp.now(),
                "size": position_size,
                "source": "ai_model",
            }

            # Risk checks
            if self.config.enable_risk_checks and not self._validate_signal(signal):
                self.logger.warning("Signal failed risk validation")
                return self._try_fallback(bars)

            # Record signal
            self.signal_history.append(signal.copy())
            self._increment_daily_trade_count(today)

            signals.append(signal)

            self.logger.info(
                f"Generated AI signal: {action} at {price:.2f} "
                f"(confidence: {confidence:.3f}, prediction: {prediction:.3f})"
            )

        except Exception as e:
            self.logger.error(f"Error generating AI signals: {e}", exc_info=True)
            return self._try_fallback(bars)

        return signals

    def _calculate_position_size(self, confidence: float, _price: float) -> float:
        """Calculate position size based on confidence and price.

        Args:
            confidence: Prediction confidence (0-1)
            price: Current price

        Returns:
            Position size as fraction of portfolio
        """
        # Scale position size by confidence, capped at max_position_size
        base_size = self.config.max_position_size
        confidence_multiplier = (confidence - self.config.min_confidence) / (
            1.0 - self.config.min_confidence + 1e-8
        )
        position_size = base_size * confidence_multiplier

        # Ensure we don't exceed max
        position_size = min(position_size, self.config.max_position_size)

        # Minimum position size threshold
        min_size = 0.01  # 1% minimum
        if position_size < min_size:
            return 0.0

        return position_size

    def _validate_signal(self, signal: dict[str, Any]) -> bool:
        """Validate signal against risk criteria.

        Args:
            signal: Signal dictionary

        Returns:
            True if signal passes validation
        """
        # Check position size
        position_size = signal.get("size", 0)
        if position_size > self.config.max_position_size:
            self.logger.warning(
                f"Position size {position_size} exceeds max {self.config.max_position_size}"
            )
            return False

        # Check confidence
        confidence = signal.get("confidence", 0)
        return confidence >= self.config.min_confidence

    def _exceeded_daily_limit(self, date: str) -> bool:
        """Check if daily trade limit is exceeded.

        Args:
            date: Date string

        Returns:
            True if limit exceeded
        """
        count = self.daily_trades.get(date, 0)
        return count >= self.config.max_daily_trades

    def _increment_daily_trade_count(self, date: str) -> None:
        """Increment daily trade count.

        Args:
            date: Date string
        """
        self.daily_trades[date] = self.daily_trades.get(date, 0) + 1

    def _try_fallback(self, bars: pd.DataFrame) -> list[dict[str, Any]]:
        """Try fallback strategy if enabled.

        Args:
            bars: Market data

        Returns:
            List of signals from fallback strategy or empty list
        """
        if not self.config.fallback_enabled or self.config.fallback_strategy is None:
            self.logger.debug("No fallback strategy configured")
            return []

        try:
            self.logger.info("Using fallback strategy")
            fallback_signals = self.config.fallback_strategy.generate_signals(bars)
            # Mark signals as from fallback
            for signal in fallback_signals:
                signal["source"] = "fallback"
                signal["model_version"] = "fallback"
            return fallback_signals
        except Exception as e:
            self.logger.error(f"Fallback strategy failed: {e}")
            return []

    def calculate_position_size(self, price: float, risk_amount: float) -> float:
        """Calculate position size based on risk.

        Args:
            price: Current price
            risk_amount: Amount of capital to risk

        Returns:
            Position size in shares
        """
        if price <= 0:
            return 0.0
        return risk_amount / price

    def should_open_position(self, _price: float) -> bool:
        """Check if position should be opened (not used in AI strategy).

        Args:
            price: Current price

        Returns:
            Always False (signals handled in generate_signals)
        """
        return False

    def should_close_position(self, _price: float) -> bool:
        """Check if position should be closed (not used in AI strategy).

        Args:
            price: Current price

        Returns:
            Always False (signals handled in generate_signals)
        """
        return False

    def get_stop_loss(self, price: float) -> float | None:
        """Calculate stop loss price.

        Args:
            price: Entry price

        Returns:
            Stop loss price (2% below entry for buys)
        """
        return price * 0.98  # 2% stop loss

    def get_take_profit(self, price: float) -> float | None:
        """Calculate take profit price.

        Args:
            price: Entry price

        Returns:
            Take profit price (4% above entry for buys)
        """
        return price * 1.04  # 4% take profit

    def reset_daily_counters(self) -> None:
        """Reset daily trade counters (call at start of each trading day)."""
        self.daily_trades.clear()

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get performance metrics for the AI strategy.

        Returns:
            Dictionary with performance metrics
        """
        if not self.signal_history:
            return {"total_signals": 0}

        signals_df = pd.DataFrame(self.signal_history)
        avg_confidence = (
            float(signals_df["confidence"].mean()) if "confidence" in signals_df.columns else 0.0
        )
        buy_signals = len(signals_df[signals_df["action"] == "buy"])
        sell_signals = len(signals_df[signals_df["action"] == "sell"])

        return {
            "total_signals": len(self.signal_history),
            "avg_confidence": avg_confidence,
            "buy_signals": buy_signals,
            "sell_signals": sell_signals,
            "model_version": self.config.model_version,
        }
