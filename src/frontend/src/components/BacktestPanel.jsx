import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Play, TrendingUp, TrendingDown, Activity, DollarSign } from 'lucide-react';
import './BacktestPanel.css';

const BacktestPanel = ({ strategyId, strategyName }) => {
    const [formData, setFormData] = useState({
        start_date: '2024-01-01',
        end_date: '2024-12-31',
        initial_capital: 100000
    });
    const [running, setRunning] = useState(false);
    const [results, setResults] = useState(null);

    const runBacktest = async () => {
        setRunning(true);

        try {
            const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5002';
            const response = await fetch(`${API_URL}/api/strategies/${strategyId}/backtest`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            const data = await response.json();
            if (data.status === 'success') {
                setResults(data.backtest);
            }
        } catch (error) {
            console.error('Error running backtest:', error);
        } finally {
            setRunning(false);
        }
    };

    const formatCurrency = (value) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2
        }).format(value);
    };

    const formatPercent = (value) => {
        return `${(value * 100).toFixed(2)}%`;
    };

    return (
        <div className="backtest-panel">
            <div className="panel-header">
                <h3>Backtest: {strategyName}</h3>
            </div>

            <div className="backtest-form">
                <div className="form-row">
                    <div className="form-field">
                        <label>Start Date</label>
                        <input
                            type="date"
                            value={formData.start_date}
                            onChange={(e) => setFormData(prev => ({ ...prev, start_date: e.target.value }))}
                        />
                    </div>

                    <div className="form-field">
                        <label>End Date</label>
                        <input
                            type="date"
                            value={formData.end_date}
                            onChange={(e) => setFormData(prev => ({ ...prev, end_date: e.target.value }))}
                        />
                    </div>
                </div>

                <div className="form-field">
                    <label>Initial Capital</label>
                    <input
                        type="number"
                        value={formData.initial_capital}
                        onChange={(e) => setFormData(prev => ({ ...prev, initial_capital: parseFloat(e.target.value) }))}
                        min="1000"
                        step="1000"
                    />
                </div>

                <motion.button
                    className="btn-run-backtest"
                    onClick={runBacktest}
                    disabled={running}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                >
                    <Play size={20} />
                    {running ? 'Running Backtest...' : 'Run Backtest'}
                </motion.button>
            </div>

            {results && (
                <motion.div
                    className="backtest-results"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <h4>Results</h4>

                    <div className="results-grid">
                        <div className="result-card">
                            <div className="result-icon">
                                <DollarSign size={24} />
                            </div>
                            <div className="result-content">
                                <span className="result-label">Final Capital</span>
                                <span className="result-value">{formatCurrency(results.final_capital)}</span>
                            </div>
                        </div>

                        <div className="result-card">
                            <div className={`result-icon ${results.total_return >= 0 ? 'positive' : 'negative'}`}>
                                {results.total_return >= 0 ? <TrendingUp size={24} /> : <TrendingDown size={24} />}
                            </div>
                            <div className="result-content">
                                <span className="result-label">Total Return</span>
                                <span className={`result-value ${results.total_return >= 0 ? 'positive' : 'negative'}`}>
                                    {formatPercent(results.total_return)}
                                </span>
                            </div>
                        </div>

                        <div className="result-card">
                            <div className="result-icon">
                                <Activity size={24} />
                            </div>
                            <div className="result-content">
                                <span className="result-label">Sharpe Ratio</span>
                                <span className="result-value">{results.sharpe_ratio.toFixed(2)}</span>
                            </div>
                        </div>

                        <div className="result-card">
                            <div className="result-icon negative">
                                <TrendingDown size={24} />
                            </div>
                            <div className="result-content">
                                <span className="result-label">Max Drawdown</span>
                                <span className="result-value negative">{formatPercent(results.max_drawdown)}</span>
                            </div>
                        </div>

                        <div className="result-card">
                            <div className="result-icon">
                                <Activity size={24} />
                            </div>
                            <div className="result-content">
                                <span className="result-label">Win Rate</span>
                                <span className="result-value">{formatPercent(results.win_rate)}</span>
                            </div>
                        </div>

                        <div className="result-card">
                            <div className="result-icon">
                                <Activity size={24} />
                            </div>
                            <div className="result-content">
                                <span className="result-label">Total Trades</span>
                                <span className="result-value">{results.total_trades}</span>
                            </div>
                        </div>
                    </div>

                    {results.metrics && (
                        <div className="additional-metrics">
                            <h5>Additional Metrics</h5>
                            <div className="metrics-list">
                                {Object.entries(results.metrics).map(([key, value]) => (
                                    <div key={key} className="metric-item">
                                        <span className="metric-key">{key.replace(/_/g, ' ')}</span>
                                        <span className="metric-value">
                                            {typeof value === 'number' ? value.toFixed(2) : value}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </motion.div>
            )}
        </div>
    );
};

export default BacktestPanel;
