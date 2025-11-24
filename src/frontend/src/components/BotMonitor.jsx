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
                // Only update if logs actually changed
                setLogs(prevLogs => {
                    const newLogs = data.status_messages.slice(-50);
                    // Check if logs are actually different
                    if (JSON.stringify(prevLogs) === JSON.stringify(newLogs)) {
                        return prevLogs; // Don't trigger re-render
                    }
                    return newLogs;
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
                        <span className="stat-label">Messages</span>
                        <span className="stat-value">{logs.length}</span>
                    </div>
                </div>
            </div>

            <div className="logs-container" ref={logsContainerRef}>
                {logs.length === 0 ? (
                    <div className="logs-empty">
                        <Clock size={32} />
                        <p>Waiting for bot activity...</p>
                        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                            Checking status every 2 seconds
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
