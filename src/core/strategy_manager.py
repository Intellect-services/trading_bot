"""Strategy Manager for multi-strategy execution and signal aggregation."""

import logging
from datetime import datetime
from typing import Any, cast

import pandas as pd

from src.business.strategy.models import Strategy
from src.core.bot_persistence import TradingBotPersistence

logger = logging.getLogger(__name__)


class StrategyManager:
    """Manages multiple trading strategies and aggregates their signals."""

    def __init__(self, persistence: TradingBotPersistence):
        """Initialize StrategyManager.

        Args:
            persistence: Database persistence helper
        """
        self.persistence = persistence
        self.logger = logging.getLogger(__name__)
        self.active_strategies: dict[int, Any] = {}  # strategy_id -> strategy instance
        self.strategy_configs: dict[int, Strategy] = {}  # strategy_id -> config

    def load_active_strategies(self) -> list[Strategy]:
        """Load active strategies from database.

        Returns:
            List of active Strategy models
        """
        try:
            from src.business.strategy.repositories import StrategyRepository
            from src.infrastructure import db_config

            with db_config.get_session() as session:
                strategy_repo = StrategyRepository(session)
                user_id = self.persistence.user_id

                # Get active strategies for user
                strategies = strategy_repo.get_active_strategies(user_id)

                self.logger.info(f"Loaded {len(strategies)} active strategies")

                # Store configs
                for strategy in strategies:
                    raw_id = getattr(strategy, "id", None)
                    if raw_id is None:
                        continue
                    strategy_id = int(raw_id)
                    self.strategy_configs[strategy_id] = strategy

                return strategies

        except Exception as e:
            self.logger.error(f"Error loading strategies: {e}")
            return []

    def execute_strategy(
        self, strategy_config: Strategy, symbol: str, market_data: pd.DataFrame
    ) -> list[dict[str, Any]]:
        """Execute a single strategy.

        Args:
            strategy_config: Strategy configuration from database
            market_data: Market data for strategy execution

        Returns:
            List of signals generated
        """
        try:
            raw_id = getattr(strategy_config, "id", None)
            if raw_id is None:
                return []
            strategy_id = int(raw_id)

            # Get or create strategy instance
            if strategy_id not in self.active_strategies:
                # Instantiate strategy based on type
                strategy_instance = self._create_strategy_instance(strategy_config)
                if strategy_instance:
                    self.active_strategies[strategy_id] = strategy_instance
                else:
                    return []

            strategy = self.active_strategies[strategy_id]

            raw_signals = strategy.generate_signals(market_data)
            processed_iterable: list[dict[str, Any]] = []
            if isinstance(raw_signals, pd.DataFrame):
                processed_iterable.extend(
                    cast("list[dict[str, Any]]", raw_signals.to_dict("records"))
                )
            else:
                for signal in raw_signals:
                    normalized_signal: dict[str, Any] = {}
                    for key, value in dict(signal).items():
                        normalized_signal[str(key)] = value
                    processed_iterable.append(normalized_signal)
            normalized_signals: list[dict[str, Any]] = []

            for signal in processed_iterable:
                normalized = dict(signal)
                normalized["strategy_id"] = strategy_id
                normalized["strategy_name"] = strategy_config.name
                normalized["symbol"] = symbol
                direction = (
                    normalized.get("action") or normalized.get("side") or normalized.get("type")
                )
                if direction:
                    direction_lower = str(direction).lower()
                    if direction_lower in {"buy", "long"}:
                        normalized["action"] = "buy"
                        normalized["side"] = "long"
                    elif direction_lower in {"sell", "short"}:
                        normalized["action"] = "sell"
                        normalized["side"] = "short"
                price = normalized.get("price")
                if price is None:
                    normalized["price"] = self._extract_price(market_data)
                normalized.setdefault("strength", 50.0)
                normalized_signals.append(normalized)

            self.logger.debug(
                f"Strategy '{strategy_config.name}' generated {len(normalized_signals)} signals"
            )

            return normalized_signals

        except Exception as e:
            self.logger.error(f"Error executing strategy {strategy_config.name}: {e}")
            return []

    def execute_all_strategies(
        self, market_data: dict[str, pd.DataFrame]
    ) -> dict[str, dict[str, Any]]:
        """Execute all active strategies and aggregate signals.

        Args:
            market_data: Market data for strategy execution

        Returns:
            Dictionary of aggregated signals by symbol
        """
        try:
            if not market_data:
                return {}

            # Load strategies if not loaded
            if not self.strategy_configs:
                self.load_active_strategies()

            all_signals: list[dict[str, Any]] = []

            # Execute each strategy for every symbol in the market data
            for symbol, data in market_data.items():
                for strategy_config in self.strategy_configs.values():
                    signals = self.execute_strategy(strategy_config, symbol, data)
                    all_signals.extend(signals)

            # Aggregate signals by symbol
            aggregated = self.aggregate_signals(all_signals)

            # Save signals to database
            self.save_signals(all_signals)

            return aggregated

        except Exception as e:
            self.logger.error(f"Error executing strategies: {e}")
            return {}

    def aggregate_signals(self, signals: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """Aggregate signals from multiple strategies.

        Signal aggregation logic:
        - Same direction: Average the strength
        - Opposite direction: Net the strength
        - Threshold: Only execute if net strength > 50

        Args:
            signals: List of signals from all strategies

        Returns:
            Dictionary of aggregated signals by symbol
        """
        try:
            # Group signals by symbol
            symbol_signals: dict[str, list[dict[str, Any]]] = {}

            for signal in signals:
                symbol = signal.get("symbol")
                if symbol:
                    if symbol not in symbol_signals:
                        symbol_signals[symbol] = []
                    symbol_signals[symbol].append(signal)

            # Aggregate signals for each symbol
            aggregated = {}

            for symbol, sig_list in symbol_signals.items():
                # Separate buy and sell signals
                buy_signals = [s for s in sig_list if s.get("action") == "buy"]
                sell_signals = [s for s in sig_list if s.get("action") == "sell"]

                buy_strength = sum(s.get("strength", 50) for s in buy_signals)
                sell_strength = sum(s.get("strength", 50) for s in sell_signals)

                # Calculate net signal
                if buy_strength > sell_strength:
                    net_strength = buy_strength - sell_strength
                    if net_strength > 50:  # Threshold
                        aggregated[symbol] = {
                            "action": "buy",
                            "side": "long",
                            "strength": min(100, net_strength),
                            "strategy_count": len(buy_signals),
                            "strategies": [s.get("strategy_name") for s in buy_signals],
                            "price": self._average_price(buy_signals),
                            "symbol": symbol,
                        }
                elif sell_strength > buy_strength:
                    net_strength = sell_strength - buy_strength
                    if net_strength > 50:  # Threshold
                        aggregated[symbol] = {
                            "action": "sell",
                            "side": "short",
                            "strength": min(100, net_strength),
                            "strategy_count": len(sell_signals),
                            "strategies": [s.get("strategy_name") for s in sell_signals],
                            "price": self._average_price(sell_signals),
                            "symbol": symbol,
                        }

            self.logger.info(
                f"Aggregated {len(aggregated)} signals from {len(signals)} raw signals"
            )
            return aggregated

        except Exception as e:
            self.logger.error(f"Error aggregating signals: {e}")
            return {}

    def save_signals(self, signals: list[dict[str, Any]]) -> None:
        """Save signals to database.

        Args:
            signals: List of signals to save
        """
        try:
            from src.business.strategy.repositories import SignalRepository
            from src.infrastructure import db_config

            with db_config.get_session() as session:
                signal_repo = SignalRepository(session)

                for signal in signals:
                    try:
                        signal_repo.create(
                            strategy_id=signal.get("strategy_id"),
                            symbol=signal.get("symbol"),
                            signal_type=signal.get("action"),
                            strength=signal.get("strength", 50),
                            price=signal.get("price", 0),
                            indicators=signal.get("indicators", {}),
                            generated_at=datetime.utcnow(),
                            executed=False,
                        )
                    except Exception as e:
                        self.logger.error(f"Error saving signal: {e}")

        except Exception as e:
            self.logger.error(f"Error saving signals: {e}")

    def track_performance(
        self, strategy_id: int, signal: dict[str, Any], outcome: dict[str, Any]
    ) -> None:
        """Track strategy performance.

        Args:
            strategy_id: Strategy ID
            signal: Original signal
            outcome: Trade outcome (profit/loss)
        """
        try:
            # This would update strategy performance metrics
            # For now, just log
            self.logger.info(
                f"Strategy {strategy_id} signal outcome: "
                f"{signal.get('action')} {signal.get('symbol')} -> "
                f"P&L: {outcome.get('pnl', 0)}"
            )

            # In production, would update strategy metrics in database
            # - Win rate
            # - Average profit/loss
            # - Sharpe ratio
            # - Max drawdown

        except Exception as e:
            self.logger.error(f"Error tracking performance: {e}")

    def _extract_price(self, data: pd.DataFrame) -> float | None:
        """Extract the most recent close price from market data."""
        if isinstance(data, pd.DataFrame) and not data.empty and "close" in data.columns:
            try:
                return float(data["close"].iloc[-1])
            except (KeyError, TypeError, ValueError):
                return None
        return None

    def _average_price(self, signals: list[dict[str, Any]]) -> float:
        """Calculate the average price from a list of signals."""
        prices = [
            float(signal.get("price", 0.0)) for signal in signals if signal.get("price") is not None
        ]
        return sum(prices) / len(prices) if prices else 0.0

    def enable_strategy(self, strategy_id: int) -> bool:
        """Enable a strategy.

        Args:
            strategy_id: Strategy ID

        Returns:
            True if successful
        """
        try:
            from src.business.strategy.repositories import StrategyRepository
            from src.infrastructure import db_config

            with db_config.get_session() as session:
                strategy_repo = StrategyRepository(session)
                strategy = strategy_repo.update(strategy_id, is_active=True)

                if strategy:
                    self.logger.info(f"Enabled strategy {strategy_id}")
                    # Reload strategies
                    self.load_active_strategies()
                    return True

                return False

        except Exception as e:
            self.logger.error(f"Error enabling strategy: {e}")
            return False

    def disable_strategy(self, strategy_id: int) -> bool:
        """Disable a strategy.

        Args:
            strategy_id: Strategy ID

        Returns:
            True if successful
        """
        try:
            from src.business.strategy.repositories import StrategyRepository
            from src.infrastructure import db_config

            with db_config.get_session() as session:
                strategy_repo = StrategyRepository(session)
                strategy = strategy_repo.update(strategy_id, is_active=False)

                if strategy:
                    self.logger.info(f"Disabled strategy {strategy_id}")
                    # Remove from active strategies
                    self.active_strategies.pop(strategy_id, None)
                    self.strategy_configs.pop(strategy_id, None)
                    return True

                return False

        except Exception as e:
            self.logger.error(f"Error disabling strategy: {e}")
            return False

    def _create_strategy_instance(self, config: Strategy) -> Any | None:
        """Create strategy instance from configuration.

        Args:
            config: Strategy configuration

        Returns:
            Strategy instance or None
        """
        try:
            # Map strategy types to classes
            strategy_map = {
                "moving_average": "MovingAverageCrossover",
                "mean_reversion": "MeanReversionStrategy",
                "momentum": "MomentumStrategy",
                "rsi": "RSIStrategy",
            }

            strategy_type = str(getattr(config, "type", ""))
            strategy_class_name = strategy_map.get(strategy_type)

            if not strategy_class_name:
                self.logger.warning(f"Unknown strategy type: {strategy_type}")
                return None

            # Import strategy class dynamically
            # For now, return None (would need actual strategy implementations)
            self.logger.warning(f"Strategy instantiation not implemented for {config.type}")
            return None

        except Exception as e:
            self.logger.error(f"Error creating strategy instance: {e}")
            return None

    def get_strategy_statistics(self) -> dict[str, Any]:
        """Get statistics for all strategies.

        Returns:
            Dictionary of strategy statistics
        """
        try:
            strategies_info: list[dict[str, Any]] = []

            for strategy_id, config in self.strategy_configs.items():
                strategies_info.append(
                    {
                        "id": strategy_id,
                        "name": str(getattr(config, "name", "")),
                        "type": str(getattr(config, "type", "")),
                        "is_active": bool(getattr(config, "is_active", False)),
                    }
                )

            return {
                "total_strategies": len(self.strategy_configs),
                "active_strategies": len(self.active_strategies),
                "strategies": strategies_info,
            }

        except Exception as e:
            self.logger.error(f"Error getting strategy statistics: {e}")
            return {}
