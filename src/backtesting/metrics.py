import numpy as np
import pandas as pd
from typing import Dict, Any, List

def calculate_metrics(returns: pd.Series, trades: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate performance metrics for a strategy"""
    metrics = {}
    
    # Basic return metrics
    metrics['total_return'] = (returns + 1).prod() - 1
    metrics['annual_return'] = (1 + metrics['total_return']) ** (252 / len(returns)) - 1
    
    # Risk metrics
    metrics['volatility'] = returns.std() * np.sqrt(252)
    metrics['sharpe_ratio'] = metrics['annual_return'] / metrics['volatility'] if metrics['volatility'] != 0 else 0
    
    # Drawdown metrics
    cum_returns = (1 + returns).cumprod()
    running_max = cum_returns.expanding().max()
    drawdowns = (cum_returns - running_max) / running_max
    metrics['max_drawdown'] = drawdowns.min()
    metrics['avg_drawdown'] = drawdowns[drawdowns < 0].mean()
    
    # Trade metrics
    if trades:
        win_trades = [t for t in trades if t['type'] == 'sell' and t['price'] > t.get('entry_price', 0)]
        loss_trades = [t for t in trades if t['type'] == 'sell' and t['price'] <= t.get('entry_price', 0)]
        
        metrics['total_trades'] = len(trades) // 2  # Each trade has a buy and sell
        metrics['win_rate'] = len(win_trades) / (len(win_trades) + len(loss_trades)) if (len(win_trades) + len(loss_trades)) > 0 else 0
        
        # Calculate average win/loss
        if win_trades:
            metrics['avg_win'] = np.mean([t['price'] / t.get('entry_price', t['price']) - 1 for t in win_trades])
        if loss_trades:
            metrics['avg_loss'] = np.mean([t['price'] / t.get('entry_price', t['price']) - 1 for t in loss_trades])
        
        # Calculate profit factor
        total_profit = sum([t['price'] - t.get('entry_price', t['price']) for t in win_trades])
        total_loss = abs(sum([t['price'] - t.get('entry_price', t['price']) for t in loss_trades]))
        metrics['profit_factor'] = total_profit / total_loss if total_loss != 0 else float('inf')
    
    return metrics

def format_metrics(metrics: Dict[str, float]) -> Dict[str, str]:
    """Format metrics for display"""
    formatted = {}
    for key, value in metrics.items():
        if key in ['total_return', 'annual_return', 'volatility', 'avg_win', 'avg_loss', 'max_drawdown', 'avg_drawdown']:
            formatted[key] = f"{value:.2%}"
        elif key in ['sharpe_ratio', 'profit_factor']:
            formatted[key] = f"{value:.2f}"
        elif key in ['win_rate']:
            formatted[key] = f"{value:.1%}"
        elif key in ['total_trades']:
            formatted[key] = f"{int(value)}"
        else:
            formatted[key] = str(value)
    return formatted 