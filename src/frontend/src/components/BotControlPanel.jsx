import React, { useState, useEffect } from 'react';
import { Play, Square, RefreshCw, Clock as ClockIcon } from 'lucide-react';
import BotStatusBadge from './BotStatusBadge';
import { api } from '../services/api';
import './BotControlPanel.css';

const BotControlPanel = () => {
    const [botStatus, setBotStatus] = useState('stopped');
    const [marketStatus, setMarketStatus] = useState('closed');
    const [marketInfo, setMarketInfo] = useState({
        next_open: null,
        next_close: null,
        current_time: null
    });
    const [loading, setLoading] = useState(false);
    const [lastUpdate, setLastUpdate] = useState(null);

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 3000);
        return () => clearInterval(interval);
    }, []);

    const formatNextOpenTime = (nextOpen) => {
        if (!nextOpen) return null;

        try {
            const nextOpenDate = new Date(nextOpen);
            const now = new Date();
            const diffMs = nextOpenDate - now;

            if (diffMs <= 0) return 'Market opens soon';

            const days = Math.floor(diffMs / (1000 * 60 * 60 * 24));
            const hours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));

            // Format in CET timezone
            const dateStr = nextOpenDate.toLocaleDateString('en-US', {
                weekday: 'short',
                month: 'short',
                day: 'numeric',
                timeZone: 'Europe/Berlin'
            });

            const timeStr = nextOpenDate.toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit',
                hour12: false,
                timeZone: 'Europe/Berlin'
            });

            let countdownStr = '';
            if (days > 0) {
                countdownStr = `${days}D ${hours}H`;
            } else if (hours > 0) {
                countdownStr = `${hours}H ${minutes}M`;
            } else {
                countdownStr = `${minutes}M`;
            }

            return { date: dateStr, time: timeStr, countdown: countdownStr };
        } catch (e) {
            return { date: nextOpen, time: '', countdown: '' };
        }
    };

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

            // Update market status
            if (data.market_status) {
                setMarketStatus(data.market_status);
            }

            // Update market info
            if (data.next_open || data.next_close || data.current_time) {
                setMarketInfo({
                    next_open: data.next_open,
                    next_close: data.next_close,
                    current_time: data.current_time
                });
            }

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
            {/* Main Content */}
            <div className="control-main-content">
                {/* Status and Market Info */}
                <div className="status-group">
                    <BotStatusBadge status={botStatus} size="large" />

                    <div className="market-info-group">
                        <div className="market-status">
                            <ClockIcon size={18} />
                            <span className="market-label">Market:</span>
                            <span className={`market-value ${marketStatus}`}>
                                {marketStatus.toUpperCase()}
                            </span>
                        </div>

                        {marketStatus === 'closed' && marketInfo.next_open && (() => {
                            const timing = formatNextOpenTime(marketInfo.next_open);
                            if (typeof timing === 'string') {
                                return (
                                    <div className="market-timing">
                                        <span className="timing-label">Opens:</span>
                                        <span className="timing-value">{timing}</span>
                                    </div>
                                );
                            }
                            return (
                                <div className="market-timing">
                                    <span className="timing-label">Opens:</span>
                                    <span className="timing-date-time">{timing.date} {timing.time} CET</span>
                                    <span className="timing-countdown">{timing.countdown}</span>
                                </div>
                            );
                        })()}

                        {marketStatus === 'open' && marketInfo.next_close && (() => {
                            const timing = formatNextOpenTime(marketInfo.next_close);
                            if (typeof timing === 'string') {
                                return (
                                    <div className="market-timing">
                                        <span className="timing-label">Closes:</span>
                                        <span className="timing-value">{timing}</span>
                                    </div>
                                );
                            }
                            return (
                                <div className="market-timing">
                                    <span className="timing-label">Closes:</span>
                                    <span className="timing-date-time">{timing.date} {timing.time} CET</span>
                                    <span className="timing-countdown">{timing.countdown}</span>
                                </div>
                            );
                        })()}
                    </div>
                </div>

                {/* Control Buttons */}
                <div className="control-actions">
                    {botStatus === 'stopped' && (
                        <button
                            className="btn-control btn-start"
                            onClick={handleStart}
                            disabled={loading}
                        >
                            <Play size={20} fill="currentColor" />
                            <span>Start Bot</span>
                        </button>
                    )}

                    {botStatus === 'running' && (
                        <button
                            className="btn-control btn-stop"
                            onClick={handleStop}
                            disabled={loading}
                        >
                            <Square size={20} fill="currentColor" />
                            <span>Stop Bot</span>
                        </button>
                    )}

                    {botStatus === 'error' && (
                        <button
                            className="btn-control btn-restart"
                            onClick={handleRestart}
                            disabled={loading}
                        >
                            <RefreshCw size={20} />
                            <span>Restart Bot</span>
                        </button>
                    )}

                    {(botStatus === 'starting' || botStatus === 'stopping') && (
                        <button className="btn-control btn-loading" disabled>
                            <RefreshCw size={20} className="spin" />
                            <span>{botStatus === 'starting' ? 'Starting...' : 'Stopping...'}</span>
                        </button>
                    )}
                </div>
            </div>

            {/* Footer */}
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
