import React, { useState, useEffect } from 'react';
import { Play, Pause, Square, RefreshCw, TrendingUp, Clock as ClockIcon } from 'lucide-react';
import BotStatusBadge from './BotStatusBadge';
import { api } from '../services/api';
import './BotControlPanel.css';

const BotControlPanel = () => {
    const [botStatus, setBotStatus] = useState('stopped');
    const [marketStatus, setMarketStatus] = useState('closed');
    const [stats, setStats] = useState({
        activeStrategies: 0,
        openPositions: 0,
        todayOrders: 0
    });
    const [loading, setLoading] = useState(false);
    const [lastUpdate, setLastUpdate] = useState(null);

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 3000);
        return () => clearInterval(interval);
    }, []);

    const fetchStatus = async () => {
        try {
            const response = await api.get('/api/status');
            const data = response.data;

            // Determine bot status
            if (data.is_running) {
                setBotStatus('running');
            } else {
                setBotStatus('stopped');
            }

            // Update stats
            setStats({
                activeStrategies: data.strategies_loaded || 0,
                openPositions: data.open_positions || 0,
                todayOrders: data.today_orders || 0
            });

            setLastUpdate(new Date());
        } catch (error) {
            console.error('Error fetching status:', error);
            setBotStatus('error');
        }
    };

    const handleStart = async () => {
        setLoading(true);
        setBotStatus('starting');
        try {
            const response = await api.post('/api/start');
            if (response.data.status === 'success') {
                setBotStatus('running');
                setTimeout(fetchStatus, 1000);
            } else {
                setBotStatus('error');
            }
        } catch (error) {
            console.error('Error starting bot:', error);
            setBotStatus('error');
        } finally {
            setLoading(false);
        }
    };

    const handleStop = async () => {
        if (!window.confirm('Are you sure you want to stop the trading bot?')) {
            return;
        }

        setLoading(true);
        setBotStatus('stopping');
        try {
            const response = await api.post('/api/stop');
            if (response.data.status === 'success') {
                setBotStatus('stopped');
                setTimeout(fetchStatus, 1000);
            } else {
                setBotStatus('error');
            }
        } catch (error) {
            console.error('Error stopping bot:', error);
            setBotStatus('error');
        } finally {
            setLoading(false);
        }
    };

    const handleRestart = async () => {
        await handleStop();
        setTimeout(handleStart, 2000);
    };

    return (
        <div className="bot-control-panel glass-card">
            {/* Status Section */}
            <div className="control-section status-section">
                <BotStatusBadge status={botStatus} size="large" />

                <div className="market-status">
                    <ClockIcon size={16} />
                    <span className="market-label">Market:</span>
                    <span className={`market-value ${marketStatus}`}>
                        {marketStatus.toUpperCase()}
                    </span>
                </div>
            </div>

            {/* Quick Stats */}
            <div className="control-section stats-section">
                <div className="stat-item">
                    <div className="stat-icon">📊</div>
                    <div className="stat-content">
                        <span className="stat-value">{stats.activeStrategies}</span>
                        <span className="stat-label">Strategies</span>
                    </div>
                </div>
                <div className="stat-item">
                    <div className="stat-icon">💼</div>
                    <div className="stat-content">
                        <span className="stat-value">{stats.openPositions}</span>
                        <span className="stat-label">Positions</span>
                    </div>
                </div>
                <div className="stat-item">
                    <div className="stat-icon">📈</div>
                    <div className="stat-content">
                        <span className="stat-value">{stats.todayOrders}</span>
                        <span className="stat-label">Orders</span>
                    </div>
                </div>
            </div>

            {/* Control Buttons */}
            <div className="control-section actions-section">
                {botStatus === 'stopped' && (
                    <button
                        className="btn-control btn-start"
                        onClick={handleStart}
                        disabled={loading}
                    >
                        <Play size={20} fill="currentColor" />
                        Start Bot
                    </button>
                )}

                {botStatus === 'running' && (
                    <>
                        <button
                            className="btn-control btn-stop"
                            onClick={handleStop}
                            disabled={loading}
                        >
                            <Square size={20} fill="currentColor" />
                            Stop Bot
                        </button>
                    </>
                )}

                {botStatus === 'error' && (
                    <button
                        className="btn-control btn-restart"
                        onClick={handleRestart}
                        disabled={loading}
                    >
                        <RefreshCw size={20} />
                        Restart Bot
                    </button>
                )}

                {(botStatus === 'starting' || botStatus === 'stopping') && (
                    <button className="btn-control btn-loading" disabled>
                        <RefreshCw size={20} className="spin" />
                        {botStatus === 'starting' ? 'Starting...' : 'Stopping...'}
                    </button>
                )}
            </div>

            {/* Last Update */}
            {lastUpdate && (
                <div className="control-footer">
                    <span className="last-update-text">
                        Last updated: {lastUpdate.toLocaleTimeString()}
                    </span>
                </div>
            )}
        </div>
    );
};

export default BotControlPanel;
