# AI-Enhanced Trading Strategies Guide

This guide explains how to use AI-enhanced trading strategies in the trading bot, focusing on safety and capital preservation.

## Overview

The AI-Enhanced Strategies feature adds machine learning capabilities to the trading bot while maintaining strict risk controls and safety mechanisms. The system is designed with **capital preservation as the top priority**.

### Key Safety Features

1. **Confidence Thresholds**: Only execute trades when model confidence exceeds a minimum threshold (default: 65%)
2. **Position Size Limits**: Maximum 5% of portfolio per trade by default
3. **Fallback Strategies**: Automatically falls back to classical strategies (e.g., RSI) when:
   - Model confidence is too low
   - Model fails to load
   - Model predictions are invalid
4. **Daily Trade Limits**: Prevent overtrading (default: 5 trades per day)
5. **Risk Validation**: Multiple layers of risk checks before executing trades

## Architecture

```
┌─────────────────┐
│  Market Data    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Feature Engineer│  ← Creates ML-ready features from OHLCV + news/sentiment
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   ML Model      │  ← Generates predictions with confidence scores
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  AI Strategy    │  ← Applies confidence thresholds & risk checks
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│StrategyManager  │  ← Integrates with existing strategy system
└─────────────────┘
```

## Components

### 1. Feature Engineering (`src/ml/feature_engineering.py`)

Creates ML-ready features from:
- **Technical Indicators**: RSI, MACD, Bollinger Bands, Moving Averages
- **Price Features**: Returns, volatility, high-low spreads
- **Volume Features**: Volume ratios, OBV, VPT
- **Time Features**: Day of week, month, cyclical encoding
- **External Data** (optional): News sentiment, fundamental metrics

### 2. Model Interface (`src/ml/model_interface.py`)

Abstract base classes for:
- **ClassificationModel**: Predicts buy/sell/hold signals
- **RegressionModel**: Predicts expected returns
- **EnsembleModel**: Combines multiple models

### 3. AI Strategy (`src/ml/ai_strategy.py`)

Trading strategy wrapper that:
- Loads trained ML models
- Validates predictions against confidence thresholds
- Applies risk management rules
- Falls back to classical strategies when needed

### 4. Model Registry (`src/ml/model_registry.py`)

Tracks:
- Model versions and metadata
- Training metrics
- Performance metrics in production
- Model comparison tools

## Quick Start

### Step 1: Train a Model

```bash
# Train a classification model for AAPL
python scripts/train_ai_model.py \
    --symbol AAPL \
    --model-type classification \
    --output-dir models/ \
    --lookback-days 365 \
    --min-confidence 0.65
```

This will:
1. Fetch historical data for the symbol
2. Create features using the FeatureEngineer
3. Generate labels (buy/sell/hold based on forward returns)
4. Train a Random Forest classifier
5. Save the model and register it

### Step 2: Configure AI Strategy in Database

Create a strategy entry in the database with:
```json
{
  "name": "AI Strategy for AAPL",
  "type": "ai",
  "parameters": {
    "model_id": "AAPL_classification",
    "model_version": "1.0.0",
    "model_path": "models/AAPL_classification_v1.0.0.pkl",
    "min_confidence": 0.65,
    "max_position_size": 0.05,
    "fallback_enabled": true,
    "fallback_strategy_type": "rsi",
    "max_daily_trades": 5
  }
}
```

### Step 3: Enable Strategy

The strategy will be automatically loaded by StrategyManager when active.

## Configuration Parameters

### AI Strategy Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `model_id` | Required | Unique identifier for the model |
| `model_version` | "1.0.0" | Model version string |
| `model_path` | Optional | Path to model file (if not in registry) |
| `min_confidence` | 0.65 | Minimum confidence to execute trade (0-1) |
| `max_position_size` | 0.05 | Maximum position size as fraction of portfolio |
| `fallback_enabled` | true | Enable fallback to classical strategies |
| `fallback_strategy_type` | "rsi" | Type of fallback strategy |
| `max_daily_trades` | 5 | Maximum trades per day |

### Conservative Defaults

All defaults are set conservatively to protect capital:
- **65% confidence threshold**: Only high-confidence trades
- **5% max position size**: Limits exposure per trade
- **5 trades/day limit**: Prevents overtrading
- **Fallback enabled**: Always have a backup strategy

## Model Training

### Training Process

1. **Data Collection**: Historical OHLCV data (minimum 365 days recommended)
2. **Feature Engineering**: Creates 50+ features from raw market data
3. **Label Generation**:
   - Classification: Labels based on forward returns (5-day lookahead)
   - Regression: Direct forward return prediction
4. **Model Training**: Random Forest (can be extended to other models)
5. **Validation**: Train/test split (80/20) with metrics tracking
6. **Registration**: Model saved and registered in registry

### Feature Sets

The default feature set includes:
- Technical indicators (RSI, MACD, Bollinger Bands)
- Price patterns (returns, volatility)
- Volume patterns (volume ratios, OBV)
- Time-based features (day of week, month)
- Lagged features (1, 2, 5, 10, 20 periods)
- Rolling statistics (mean, std, min, max)

### Adding External Data

You can extend the feature set with:
- News sentiment (Alpaca News API)
- Social media sentiment
- Fundamental data (P/E, P/B, debt ratios)
- Economic indicators

Example:
```python
features = feature_engineer.create_features(
    market_data=market_df,
    news_data=news_df,  # Optional
    sentiment_data=sentiment_df,  # Optional
    fundamental_data=fundamental_df,  # Optional
)
```

## Model Monitoring

### Performance Tracking

The ModelMonitor tracks:
- Prediction accuracy (classification)
- MSE/RMSE (regression)
- Precision/Recall for buy signals
- Cumulative PnL
- Confidence distribution

### Accessing Metrics

```python
from src.ml.model_registry import ModelRegistry, ModelMonitor

registry = ModelRegistry()
monitor = ModelMonitor(registry)

# Get model info
info = registry.get_model_info("AAPL_classification", "1.0.0")

# Calculate metrics
metrics = monitor.calculate_metrics("AAPL_classification", "1.0.0", min_confidence=0.65)
print(f"Accuracy: {metrics.get('accuracy')}")
print(f"Precision: {metrics.get('precision')}")
print(f"Recall: {metrics.get('recall')}")
```

## Risk Management Integration

AI strategies integrate with the existing RiskManager:

1. **Position Sizing**: Model confidence scales position size
2. **Stop Loss**: Default 2% stop loss on all positions
3. **Take Profit**: Default 4% take profit target
4. **Drawdown Limits**: Respected by all strategies
5. **Daily Loss Limits**: Trading halts if exceeded

### Confidence-Based Position Sizing

Position size is calculated as:
```
base_size = max_position_size (default: 5%)
confidence_multiplier = (confidence - min_confidence) / (1.0 - min_confidence)
position_size = base_size * confidence_multiplier
```

This means:
- 65% confidence → ~0% position (at threshold)
- 80% confidence → ~43% of max (moderate)
- 95% confidence → ~86% of max (high confidence)

## Fallback Mechanisms

When AI model cannot generate valid signals, the system automatically falls back to classical strategies:

1. **Low Confidence**: If model confidence < threshold → use fallback
2. **Model Load Failure**: If model file not found → use fallback
3. **Invalid Predictions**: If predictions are NaN/invalid → use fallback
4. **Data Insufficient**: If not enough data for features → use fallback

### Fallback Strategy Options

Currently supported:
- RSI Strategy (default)
- MACD Strategy
- Bollinger Bands Strategy
- Moving Average Crossover

## Best Practices

### Model Training

1. **Use Sufficient Data**: Minimum 1 year of daily data
2. **Validate Thoroughly**: Check train/test metrics
3. **Monitor Performance**: Track metrics in production
4. **Version Control**: Tag models with semantic versions
5. **A/B Testing**: Compare new models before deploying

### Strategy Configuration

1. **Start Conservative**: Use high confidence thresholds (0.70+)
2. **Small Positions**: Start with 2-3% max position size
3. **Enable Fallback**: Always have a backup strategy
4. **Monitor Daily**: Check performance metrics regularly
5. **Limit Trades**: Use daily trade limits to prevent overtrading

### Risk Management

1. **Never Disable Risk Checks**: Always keep `enable_risk_checks=True`
2. **Respect Drawdown Limits**: System will halt if exceeded
3. **Diversify**: Don't rely on a single AI model
4. **Regular Retraining**: Retrain models monthly/quarterly
5. **Backtest Thoroughly**: Always backtest before live trading

## Troubleshooting

### Model Not Loading

**Problem**: Strategy fails to load model
**Solutions**:
- Check model path is correct
- Verify model file exists
- Check model registry for correct version
- Ensure fallback is enabled

### Low Signal Generation

**Problem**: Strategy generates very few signals
**Solutions**:
- Lower confidence threshold (carefully!)
- Check if sufficient data for features
- Verify model is trained correctly
- Review label generation logic

### Poor Performance

**Problem**: Model predictions not profitable
**Solutions**:
- Retrain with more data
- Adjust feature set
- Try different model hyperparameters
- Compare with fallback strategy performance
- Consider ensemble models

## Future Enhancements

Planned improvements:
1. **More Model Types**: XGBoost, LightGBM, LSTM
2. **Online Learning**: Update models with new data
3. **Ensemble Strategies**: Combine multiple models
4. **News Integration**: Real-time news sentiment analysis
5. **Automated Retraining**: Scheduled model updates
6. **MLflow Integration**: Advanced model versioning

## API Reference

### AIStrategyConfig

```python
from src.ml import AIStrategyConfig

config = AIStrategyConfig(
    model=trained_model,
    min_confidence=0.65,
    max_position_size=0.05,
    fallback_enabled=True,
    fallback_strategy=fallback_strategy,
    enable_risk_checks=True,
    max_daily_trades=5,
    model_version="1.0.0",
)
```

### FeatureEngineer

```python
from src.ml.feature_engineering import FeatureEngineer

engineer = FeatureEngineer()
features = engineer.create_features(market_data=df)
labels = engineer.create_label_for_classification(features, forward_window=5)
```

### Model Training

```python
from src.ml.models import SklearnClassificationModel

model = SklearnClassificationModel(
    model_id="AAPL_model",
    version="1.0.0",
    n_estimators=100,
    max_depth=10,
)

metrics = model.train(X_train, y_train)
model.save("models/model.pkl")
```

## Support

For issues or questions:
1. Check this guide first
2. Review model registry logs
3. Check strategy manager logs
4. Verify risk manager settings
5. Test with fallback strategy

Remember: **Capital preservation is the top priority**. When in doubt, use more conservative settings.
