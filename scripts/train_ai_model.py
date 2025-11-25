#!/usr/bin/env python3
"""CLI script for training AI trading models.

Usage:
    python scripts/train_ai_model.py --symbol AAPL --model-type classification --output-dir models/
"""

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.alpaca_service import AlpacaService
from src.core.data_cache import DataCache
from src.core.data_provider import DataProvider
from src.ml.feature_engineering import FeatureEngineer
from src.ml.model_registry import ModelRegistry
from src.ml.models import SklearnClassificationModel, SklearnRegressionModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def train_model(
    symbol: str,
    model_type: str,
    output_dir: str,
    lookback_days: int = 365,
    min_confidence: float = 0.65,
) -> None:
    """Train an AI trading model.

    Args:
        symbol: Stock symbol to train on
        model_type: 'classification' or 'regression'
        output_dir: Directory to save model
        lookback_days: Number of days of historical data
        min_confidence: Minimum confidence threshold
    """
    logger.info(f"Training {model_type} model for {symbol}")

    # Initialize data provider
    alpaca_service = None  # Will use free providers if Alpaca not available
    try:
        from src.utils.config import Config

        config = Config()
        if config.alpaca_api_key_id and config.alpaca_api_secret_key:
            alpaca_service = AlpacaService(
                api_key=config.alpaca_api_key_id,
                secret_key=config.alpaca_api_secret_key,
                trading_mode=config.trading_mode or "paper",
            )
            logger.info("Using Alpaca service for data")
    except Exception as e:
        logger.warning(f"Could not initialize Alpaca service: {e}. Using free data sources.")

    cache = DataCache()
    data_provider = DataProvider(alpaca_service=alpaca_service, cache=cache)

    # Fetch historical data
    logger.info(f"Fetching {lookback_days} days of data for {symbol}")
    from datetime import datetime, timedelta

    end = datetime.now()
    start = end - timedelta(days=lookback_days)

    bars = data_provider.get_historical_bars(
        symbol=symbol,
        timeframe="1Day",
        start=start,
        end=end,
    )

    if not bars:
        logger.error(f"Failed to fetch data for {symbol}")
        sys.exit(1)

    # Convert to DataFrame
    df = pd.DataFrame(bars)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)
    else:
        logger.error("Data missing timestamp column")
        sys.exit(1)

    # Ensure required columns
    required_cols = ["open", "high", "low", "close", "volume"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        sys.exit(1)

    logger.info(f"Loaded {len(df)} bars")

    # Create features
    logger.info("Creating features...")
    feature_engineer = FeatureEngineer()
    features = feature_engineer.create_features(market_data=df)

    if features.empty:
        logger.error("Failed to create features")
        sys.exit(1)

    logger.info(f"Created {len(features.columns)} features")

    # Create labels
    logger.info("Creating labels...")
    if model_type == "classification":
        labels = feature_engineer.create_label_for_classification(
            features, forward_window=5, profit_threshold=0.02
        )
    else:  # regression
        labels = feature_engineer.create_label_for_regression(features, forward_window=5)

    # Remove rows with NaN labels
    valid_mask = ~labels.isna()
    features = features[valid_mask]
    labels = labels[valid_mask]

    if len(features) == 0:
        logger.error("No valid data after label creation")
        sys.exit(1)

    logger.info(f"Created {len(features)} labeled samples")
    logger.info(f"Label distribution: {labels.value_counts().to_dict()}")

    # Prepare feature matrix (exclude non-feature columns)
    exclude_cols = ["symbol", "timestamp"] if "symbol" in features.columns else ["timestamp"]
    feature_cols = [col for col in features.columns if col not in exclude_cols]

    X = features[feature_cols].copy()
    y = labels

    # Train model
    logger.info(f"Training {model_type} model...")
    if model_type == "classification":
        model = SklearnClassificationModel(
            model_id=f"{symbol}_{model_type}",
            version="1.0.0",
            n_estimators=100,
            max_depth=10,
        )
    else:
        model = SklearnRegressionModel(
            model_id=f"{symbol}_{model_type}",
            version="1.0.0",
            n_estimators=100,
            max_depth=10,
        )

    metrics = model.train(X, y, test_size=0.2)
    logger.info(f"Training metrics: {metrics}")

    # Save model
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    model_filename = f"{symbol}_{model_type}_v1.0.0.pkl"
    model_path = output_path / model_filename
    model.save(model_path)
    logger.info(f"Saved model to {model_path}")

    # Register in registry
    registry = ModelRegistry(registry_path=output_path / "registry.json")
    registry.register_model(
        model_id=f"{symbol}_{model_type}",
        version="1.0.0",
        model_path=str(model_path),
        model_type=model_type,
        training_metrics=metrics,
        feature_set=feature_cols,
        metadata={"symbol": symbol, "min_confidence": min_confidence},
    )
    logger.info("Registered model in registry")

    logger.info("Training complete!")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Train AI trading model")
    parser.add_argument("--symbol", required=True, help="Stock symbol (e.g., AAPL)")
    parser.add_argument(
        "--model-type",
        choices=["classification", "regression"],
        default="classification",
        help="Model type",
    )
    parser.add_argument("--output-dir", default="models", help="Output directory for models")
    parser.add_argument("--lookback-days", type=int, default=365, help="Days of historical data")
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.65,
        help="Minimum confidence threshold",
    )

    args = parser.parse_args()

    try:
        train_model(
            symbol=args.symbol.upper(),
            model_type=args.model_type,
            output_dir=args.output_dir,
            lookback_days=args.lookback_days,
            min_confidence=args.min_confidence,
        )
    except KeyboardInterrupt:
        logger.info("Training interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
