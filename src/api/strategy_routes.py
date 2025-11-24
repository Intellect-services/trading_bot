"""Strategy API routes for IntellectTrader."""

import logging
from datetime import datetime
from typing import TypeAlias

from flask import Flask, Response, jsonify, request
from werkzeug.wrappers.response import Response as WerkzeugResponse

logger = logging.getLogger(__name__)

FlaskResponse: TypeAlias = (
    Response | WerkzeugResponse | tuple[Response, int] | tuple[WerkzeugResponse, int]
)


def register_strategy_routes(app: Flask) -> None:
    """Register strategy management routes."""

    @app.route("/api/strategies", methods=["GET"])
    def get_strategies() -> FlaskResponse:
        """Get all user strategies."""
        try:
            from src.business.strategy.repositories import StrategyRepository
            from src.infrastructure import db_config

            # Get user ID from session
            user_id = request.args.get("user_id", 1, type=int)  # Default to 1 for now

            with db_config.get_session() as session:
                strategy_repo = StrategyRepository(session)
                strategies = strategy_repo.get_by_user(user_id)

                return jsonify(
                    {
                        "status": "success",
                        "strategies": [
                            {
                                "id": s.id,
                                "name": s.name,
                                "description": s.description,
                                "type": s.type,
                                "parameters": s.parameters,
                                "is_active": s.is_active,
                                "created_at": s.created_at.isoformat() if s.created_at else None,
                            }
                            for s in strategies
                        ],
                    }
                )

        except Exception as e:
            logger.error(f"Error getting strategies: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route("/api/strategies", methods=["POST"])
    def create_strategy() -> FlaskResponse:
        """Create new strategy."""
        try:
            from src.business.strategy.repositories import StrategyRepository
            from src.infrastructure import db_config

            data = request.get_json()
            user_id = data.get("user_id", 1)  # Default to 1 for now

            # Validate required fields
            if not data.get("name") or not data.get("type"):
                return jsonify({"status": "error", "message": "Name and type are required"}), 400

            with db_config.get_session() as session:
                strategy_repo = StrategyRepository(session)

                strategy = strategy_repo.create(
                    user_id=user_id,
                    name=data["name"],
                    description=data.get("description", ""),
                    type=data["type"],
                    parameters=data.get("parameters", {}),
                    is_active=data.get("is_active", False),
                )

                return jsonify(
                    {
                        "status": "success",
                        "strategy": {
                            "id": strategy.id,
                            "name": strategy.name,
                            "description": strategy.description,
                            "type": strategy.type,
                            "parameters": strategy.parameters,
                            "is_active": strategy.is_active,
                        },
                    }
                ), 201

        except Exception as e:
            logger.error(f"Error creating strategy: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route("/api/strategies/<int:strategy_id>", methods=["PUT"])
    def update_strategy(strategy_id: int) -> FlaskResponse:
        """Update strategy."""
        try:
            from src.business.strategy.repositories import StrategyRepository
            from src.infrastructure import db_config

            data = request.get_json()

            with db_config.get_session() as session:
                strategy_repo = StrategyRepository(session)

                # Build update dict
                update_data = {}
                if "name" in data:
                    update_data["name"] = data["name"]
                if "description" in data:
                    update_data["description"] = data["description"]
                if "type" in data:
                    update_data["type"] = data["type"]
                if "parameters" in data:
                    update_data["parameters"] = data["parameters"]
                if "is_active" in data:
                    update_data["is_active"] = data["is_active"]

                strategy = strategy_repo.update(strategy_id, **update_data)

                if not strategy:
                    return jsonify({"status": "error", "message": "Strategy not found"}), 404

                return jsonify(
                    {
                        "status": "success",
                        "strategy": {
                            "id": strategy.id,
                            "name": strategy.name,
                            "description": strategy.description,
                            "type": strategy.type,
                            "parameters": strategy.parameters,
                            "is_active": strategy.is_active,
                        },
                    }
                )

        except Exception as e:
            logger.error(f"Error updating strategy: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route("/api/strategies/<int:strategy_id>", methods=["DELETE"])
    def delete_strategy(strategy_id: int) -> FlaskResponse:
        """Delete strategy."""
        try:
            from src.business.strategy.repositories import StrategyRepository
            from src.infrastructure import db_config

            with db_config.get_session() as session:
                strategy_repo = StrategyRepository(session)

                success = strategy_repo.delete(strategy_id)

                if not success:
                    return jsonify({"status": "error", "message": "Strategy not found"}), 404

                return jsonify({"status": "success", "message": "Strategy deleted"})

        except Exception as e:
            logger.error(f"Error deleting strategy: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route("/api/strategies/<int:strategy_id>/backtest", methods=["POST"])
    def run_backtest(strategy_id: int) -> FlaskResponse:
        """Run backtest for strategy."""
        try:
            from src.business.strategy.repositories import (
                BacktestResultRepository,
                StrategyRepository,
            )
            from src.infrastructure import db_config

            data = request.get_json()

            # Validate required fields
            required = ["start_date", "end_date", "initial_capital"]
            if not all(field in data for field in required):
                return jsonify(
                    {"status": "error", "message": f"Required fields: {', '.join(required)}"}
                ), 400

            with db_config.get_session() as session:
                strategy_repo = StrategyRepository(session)
                backtest_repo = BacktestResultRepository(session)

                strategy = strategy_repo.get_by_id(strategy_id)
                if not strategy:
                    return jsonify({"status": "error", "message": "Strategy not found"}), 404

                # TODO: Implement actual backtesting logic
                # For now, return mock results

                # Create backtest result
                result = backtest_repo.create(
                    strategy_id=strategy_id,
                    start_date=datetime.fromisoformat(data["start_date"]),
                    end_date=datetime.fromisoformat(data["end_date"]),
                    initial_capital=float(data["initial_capital"]),
                    final_value=float(data["initial_capital"]) * 1.15,  # Mock 15% return
                    total_return=0.15,
                    sharpe_ratio=1.5,
                    max_drawdown=0.08,
                    win_rate=0.65,
                    total_trades=50,
                    metrics={"avg_win": 250.0, "avg_loss": -150.0, "profit_factor": 1.67},
                )

                return jsonify(
                    {
                        "status": "success",
                        "backtest": {
                            "id": result.id,
                            "strategy_id": result.strategy_id,
                            "start_date": result.start_date.isoformat(),
                            "end_date": result.end_date.isoformat(),
                            "initial_capital": float(result.initial_capital),
                            "final_value": float(result.final_value),
                            "total_return": float(result.total_return),
                            "sharpe_ratio": float(result.sharpe_ratio),
                            "max_drawdown": float(result.max_drawdown),
                            "win_rate": float(result.win_rate),
                            "total_trades": result.total_trades,
                            "metrics": result.metrics,
                        },
                    }
                )

        except Exception as e:
            logger.error(f"Error running backtest: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route("/api/strategies/<int:strategy_id>/signals", methods=["GET"])
    def get_strategy_signals(strategy_id: int) -> FlaskResponse:
        """Get signals for a strategy."""
        try:
            from src.business.strategy.repositories import SignalRepository
            from src.infrastructure import db_config

            limit = request.args.get("limit", 100, type=int)

            with db_config.get_session() as session:
                signal_repo = SignalRepository(session)
                signals = signal_repo.get_by_strategy(strategy_id, limit=limit)

                return jsonify(
                    {
                        "status": "success",
                        "signals": [
                            {
                                "id": s.id,
                                "symbol": s.symbol,
                                "signal_type": s.signal_type,
                                "strength": float(s.strength) if s.strength else None,
                                "price": float(s.price) if s.price else None,
                                "indicators": s.indicators,
                                "generated_at": s.generated_at.isoformat()
                                if s.generated_at
                                else None,
                                "executed": s.executed,
                            }
                            for s in signals
                        ],
                    }
                )

        except Exception as e:
            logger.error(f"Error getting signals: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
