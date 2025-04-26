import pandas as pd
from datetime import datetime
from strategies.moving_average import MovingAverageCrossover
from backtesting.engine import BacktestEngine
from backtesting.metrics import format_metrics
from utils.config import get_config

def run_backtest():
    # Load configuration
    config = get_config()
    
    # Create strategy with parameters
    strategy_params = {
        'short_window': 20,
        'long_window': 50,
        'signal_threshold': 0.01
    }
    strategy = MovingAverageCrossover(strategy_params)
    
    # Load historical data
    # In a real implementation, this would fetch data from your data source
    # For this example, we'll create sample data
    dates = pd.date_range(
        start=config['BACKTEST_START_DATE'],
        end=config['BACKTEST_END_DATE'],
        freq='D'
    )
    data = pd.DataFrame({
        'open': 100 + pd.Series(range(len(dates))) * 0.1,
        'high': 100 + pd.Series(range(len(dates))) * 0.1 + 1,
        'low': 100 + pd.Series(range(len(dates))) * 0.1 - 1,
        'close': 100 + pd.Series(range(len(dates))) * 0.1,
        'volume': 1000000
    }, index=dates)
    
    # Create and run backtest
    engine = BacktestEngine(
        strategy=strategy,
        initial_capital=config['BACKTEST_INITIAL_CAPITAL']
    )
    
    results = engine.run(data, commission=config['BACKTEST_COMMISSION'])
    
    # Print results
    print("\nBacktest Results")
    print("=" * 50)
    
    # Print metrics
    formatted_metrics = format_metrics(results['metrics'])
    for metric, value in formatted_metrics.items():
        print(f"{metric}: {value}")
    
    # Print trade summary
    print("\nTrade Summary")
    print("=" * 50)
    print(f"Total Trades: {len(results['trades']) // 2}")
    
    # Print equity curve summary
    print("\nEquity Curve Summary")
    print("=" * 50)
    initial_equity = results['equity_curve'][0]['equity']
    final_equity = results['equity_curve'][-1]['equity']
    total_return = (final_equity - initial_equity) / initial_equity
    print(f"Initial Equity: ${initial_equity:,.2f}")
    print(f"Final Equity: ${final_equity:,.2f}")
    print(f"Total Return: {total_return:.2%}")

if __name__ == "__main__":
    run_backtest() 