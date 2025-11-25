import React, { useState, useEffect, useRef, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Activity, AlertCircle, Info, TrendingUp, Clock } from 'lucide-react';
import { botAPI } from '../services/api';
import './BotMonitor.css';

const BotMonitor = () => {
    const [logs, setLogs] = useState([]);
    const [stats, setStats] = useState({
        lastUpdate: null
    });
    const logsContainerRef = useRef(null);
    const previousLogsLength = useRef(0);

    useEffect(() => {
        // Fetch status immediately on mount
        fetchStatus();

        // Poll for bot status every 2 seconds
        const interval = setInterval(fetchStatus, 2000);
        return () => clearInterval(interval);
    }, []);

    const fetchStatus = async () => {
        try {
            const response = await botAPI.getStatus();
            const data = response.data;

            if (data.status_messages && data.status_messages.length > 0) {
                // Filter to show only system/technical events (exclude trading events)
                const systemLogs = data.status_messages
                    .filter(msg => {
                        const msgLower = msg.message.toLowerCase();
                        // Exclude trading events - those belong to Trading Activity page
                        const isTradingEvent =
                            msgLower.includes('executing') ||
                            msgLower.includes('buy order') ||
                            msgLower.includes('sell order') ||
                            msgLower.includes('signal') ||
                            msgLower.includes('generated') ||
                            msg.level === 'trade' ||
                            msg.level === 'signal';

                        // Include system events: errors, warnings, initialization, database, connections, market status
                        const isSystemEvent =
                            msgLower.includes('error') ||
                            msgLower.includes('failed') ||
                            msgLower.includes('database') ||
                            msgLower.includes('connected') ||
                            msgLower.includes('initialized') ||
                            msgLower.includes('started') ||
                            msgLower.includes('stopped') ||
                            msgLower.includes('market') ||
                            msgLower.includes('closed') ||
                            msgLower.includes('open') ||
                            msgLower.includes('data') ||
                            msgLower.includes('api') ||
                            msg.level === 'error' ||
                            msg.level === 'warning' ||
                            (msg.level === 'info' && !isTradingEvent);

                        return isSystemEvent && !isTradingEvent;
                    })
                    .slice(-10) // Show only last 10 system messages
                    .reverse(); // Most recent first

                // Only update if logs actually changed
                setLogs(prevLogs => {
                    // Check if logs are actually different
                    if (JSON.stringify(prevLogs) === JSON.stringify(systemLogs)) {
                        return prevLogs; // Don't trigger re-render
                    }
                    return systemLogs;
                });

                setStats({
                    lastUpdate: new Date().toISOString()
                });
            }
        } catch (error) {
            console.error('Error fetching bot status:', error);
        }
    };

    // Memoize log icon function
    const getLogIcon = useMemo(() => (level) => {
        switch (level) {
            case 'signal':
                return <TrendingUp size={16} className="log-icon signal" />;
            case 'trade':
                return <Activity size={16} className="log-icon trade" />;
            case 'error':
                return <AlertCircle size={16} className="log-icon error" />;
            case 'warning':
                return <AlertCircle size={16} className="log-icon warning" />;
            case 'info':
            default:
                return <Info size={16} className="log-icon info" />;
        }
    }, []);

    return (
        <div className="bot-monitor">
            <div className="monitor-header">
                <h3>
                    <Activity size={20} className={logs.length > 0 ? "pulse" : ""} />
                    Bot Monitor
                </h3>
                <div className="monitor-stats">
                    <div className="stat">
                        <span className="stat-label">System Events</span>
                        <span className="stat-value">{logs.length}</span>
                    </div>
                </div>
            </div>

            <div className="logs-container" ref={logsContainerRef}>
                {logs.length === 0 ? (
                    <div className="logs-empty">
                        <Clock size={32} />
                        <p>No system events</p>
                        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                            System and technical events will appear here
                        </p>
                        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem', fontStyle: 'italic' }}>
                            Trading events are shown on the Trading Activity page
                        </p>
                    </div>
                ) : (
                    <div className="logs-list">
                        {logs.map((log, index) => (
                            <div
                                key={`${log.timestamp}-${index}`}
                                className={`log-entry log-${log.level}`}
                            >
                                {getLogIcon(log.level)}
                                <span className="log-timestamp">
                                    {new Date(log.timestamp).toLocaleTimeString()}
                                </span>
                                <span className="log-message">{log.message}</span>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {stats.lastUpdate && (
                <div className="monitor-footer">
                    <span className="last-update">
                        Last update: {new Date(stats.lastUpdate).toLocaleTimeString()}
                    </span>
                </div>
            )}
        </div>
    );
};

export default React.memo(BotMonitor);
