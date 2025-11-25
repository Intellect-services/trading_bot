import React from 'react';
import { motion } from 'framer-motion';
import { Info, Activity, Layers, Shield, TrendingUp, BarChart3 } from 'lucide-react';
import './StrategyExplanation.css';

const StrategyExplanation = () => {
    return (
        <motion.div
            className="strategy-explanation"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
        >
            <div className="explanation-header">
                <Info size={24} />
                <h3>How Multiple Strategies Work</h3>
            </div>

            <div className="explanation-content">
                <p className="intro-text">
                    When you activate multiple strategies, the bot orchestrates them intelligently to maximize trading opportunities while managing risk.
                </p>

                <div className="explanation-steps">
                    <div className="step-card">
                        <div className="step-icon">
                            <Activity size={20} />
                        </div>
                        <div className="step-content">
                            <h4>1. Independent Execution</h4>
                            <p>Each strategy runs independently, analyzing market data and generating signals for its configured symbols.</p>
                        </div>
                    </div>

                    <div className="step-card">
                        <div className="step-icon">
                            <Layers size={20} />
                        </div>
                        <div className="step-content">
                            <h4>2. Signal Aggregation</h4>
                            <p>The bot aggregates signals from all active strategies. If multiple strategies agree on a trade, signal strength increases.</p>
                        </div>
                    </div>

                    <div className="step-card">
                        <div className="step-icon">
                            <TrendingUp size={20} />
                        </div>
                        <div className="step-content">
                            <h4>3. Trade Execution</h4>
                            <p>Trades are executed based on combined signal strength. Each strategy can trade different symbols or the same symbol independently.</p>
                        </div>
                    </div>

                    <div className="step-card">
                        <div className="step-icon">
                            <Shield size={20} />
                        </div>
                        <div className="step-content">
                            <h4>4. Risk Management</h4>
                            <p>The risk manager ensures total portfolio exposure limits are respected across all strategies. Position sizing is calculated to maintain risk parameters.</p>
                        </div>
                    </div>
                </div>

                <div className="examples-section">
                    <h4>Example Scenarios</h4>
                    <div className="example-cards">
                        <div className="example-card">
                            <BarChart3 size={18} />
                            <div>
                                <strong>Multiple Symbols:</strong>
                                <p>RSI strategy trades AAPL, MACD trades MSFT, Bollinger trades GOOGL simultaneously.</p>
                            </div>
                        </div>
                        <div className="example-card">
                            <BarChart3 size={18} />
                            <div>
                                <strong>Same Symbol:</strong>
                                <p>Both RSI and MACD trade AAPL. Stronger signals when both agree, reduced risk when they conflict.</p>
                            </div>
                        </div>
                        <div className="example-card">
                            <BarChart3 size={18} />
                            <div>
                                <strong>AI + Classical:</strong>
                                <p>AI strategy provides primary signals, falls back to RSI if model confidence is low.</p>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="recommendation-box">
                    <Info size={20} />
                    <div>
                        <strong>Recommendation:</strong>
                        <p>Start with 2-3 strategies on different symbols to diversify. Test strategies with backtesting before activating. Monitor performance and adjust as needed.</p>
                    </div>
                </div>
            </div>
        </motion.div>
    );
};

export default StrategyExplanation;
