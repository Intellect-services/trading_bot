import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { TestTube, Zap, AlertTriangle } from 'lucide-react';
import { accountAPI } from '../services/api';
import './TradingModeToggle.css';

const TradingModeToggle = () => {
    const [tradingMode, setTradingMode] = useState('paper');
    const [loading, setLoading] = useState(true);
    const [showConfirm, setShowConfirm] = useState(false);
    const [pendingMode, setPendingMode] = useState(null);

    useEffect(() => {
        loadTradingMode();
    }, []);

    const loadTradingMode = async () => {
        try {
            const response = await accountAPI.getCredentials();
            if (response.data.status === 'success' && response.data.credentials) {
                setTradingMode(response.data.credentials.trading_mode || 'paper');
            }
        } catch (error) {
            console.error('Error loading trading mode:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleModeChange = (newMode) => {
        if (newMode === tradingMode) return;

        if (newMode === 'live') {
            setPendingMode('live');
            setShowConfirm(true);
        } else {
            updateTradingMode(newMode);
        }
    };

    const confirmLiveMode = () => {
        if (pendingMode) {
            updateTradingMode(pendingMode);
        }
        setShowConfirm(false);
        setPendingMode(null);
    };

    const cancelModeChange = () => {
        setShowConfirm(false);
        setPendingMode(null);
    };

    const updateTradingMode = async (newMode) => {
        try {
            // Get current credentials
            const credResponse = await accountAPI.getCredentials();
            if (credResponse.data.status === 'success' && credResponse.data.credentials) {
                const creds = credResponse.data.credentials;

                // Update with same credentials but new mode
                const updateResponse = await accountAPI.saveCredentials(
                    creds.alpaca_api_key || '',
                    creds.alpaca_secret_key || '',
                    newMode
                );

                if (updateResponse.data.status === 'success') {
                    setTradingMode(newMode);
                    // Reload page to ensure all components use new mode
                    window.location.reload();
                }
            }
        } catch (error) {
            console.error('Error updating trading mode:', error);
            alert('Failed to update trading mode. Please check your credentials in Account Settings.');
        }
    };

    if (loading) {
        return (
            <div className="trading-mode-toggle loading">
                <div className="toggle-skeleton"></div>
            </div>
        );
    }

    return (
        <>
            <div className="trading-mode-toggle">
                <div className="mode-indicator">
                    {tradingMode === 'paper' ? (
                        <TestTube size={16} className="mode-icon paper" />
                    ) : (
                        <Zap size={16} className="mode-icon live" />
                    )}
                    <span className="mode-label">
                        {tradingMode === 'paper' ? 'Paper Trading' : 'Live Trading'}
                    </span>
                </div>

                <div className="mode-switch">
                    <button
                        className={`mode-button ${tradingMode === 'paper' ? 'active' : ''}`}
                        onClick={() => handleModeChange('paper')}
                        disabled={loading}
                    >
                        <TestTube size={14} />
                        Paper
                    </button>
                    <button
                        className={`mode-button ${tradingMode === 'live' ? 'active' : ''}`}
                        onClick={() => handleModeChange('live')}
                        disabled={loading}
                    >
                        <Zap size={14} />
                        Live
                    </button>
                </div>
            </div>

            <AnimatePresence>
                {showConfirm && (
                    <motion.div
                        className="mode-confirm-overlay"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={cancelModeChange}
                    >
                        <motion.div
                            className="mode-confirm-modal"
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.9, opacity: 0 }}
                            onClick={(e) => e.stopPropagation()}
                        >
                            <div className="confirm-header">
                                <AlertTriangle size={24} className="warning-icon" />
                                <h3>Switch to Live Trading?</h3>
                            </div>
                            <div className="confirm-content">
                                <p>
                                    <strong>Warning:</strong> Live trading uses real money.
                                    All trades will be executed with your actual funds.
                                </p>
                                <p>
                                    Make sure you understand the risks before switching to live mode.
                                </p>
                            </div>
                            <div className="confirm-actions">
                                <button
                                    className="btn-cancel"
                                    onClick={cancelModeChange}
                                >
                                    Cancel
                                </button>
                                <button
                                    className="btn-confirm"
                                    onClick={confirmLiveMode}
                                >
                                    Switch to Live
                                </button>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </>
    );
};

export default TradingModeToggle;
