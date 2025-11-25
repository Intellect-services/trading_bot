import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    TrendingUp,
    TrendingDown,
    DollarSign,
    Activity,
    CheckCircle2,
    Clock,
    AlertCircle,
    Zap,
    ArrowUpRight,
    ArrowDownRight
} from 'lucide-react';
import { botAPI, socket } from '../services/api';
import './LiveTradingActivity.css';

const LiveTradingActivity = () => {
    const [activities, setActivities] = useState([]);
    const [stats, setStats] = useState({
        totalSignals: 0,
        totalOrders: 0,
        totalTrades: 0,
        activePositions: 0
    });
    const [isLive, setIsLive] = useState(false);
    const containerRef = useRef(null);

    useEffect(() => {
        // Fetch initial bot status
        fetchBotStatus();

        // Poll for status every 2 seconds
        const interval = setInterval(fetchBotStatus, 2000);

        // Listen for Socket.IO updates
        socket.on('status_update', handleStatusUpdate);
        socket.on('dashboard_update', handleDashboardUpdate);

        return () => {
            clearInterval(interval);
            socket.off('status_update');
            socket.off('dashboard_update');
        };
    }, []);

    const fetchBotStatus = async () => {
        try {
            const response = await botAPI.getStatus();
            if (response.data.status_messages) {
                processStatusMessages(response.data.status_messages);
                setIsLive(response.data.is_running || false);
            }
        } catch (error) {
            console.error('Error fetching bot status:', error);
        }
    };

    const handleStatusUpdate = (data) => {
        if (data.status_messages) {
            processStatusMessages(data.status_messages);
        }
        setIsLive(data.is_running || false);
    };

    const handleDashboardUpdate = (data) => {
        if (data.positions) {
            setStats(prev => ({
                ...prev,
                activePositions: data.positions.length || 0
            }));
        }
    };

    const processStatusMessages = (messages) => {
        // Filter and process trading-related messages
        const tradingMessages = messages
            .filter(msg => {
                const msgLower = msg.message.toLowerCase();
                return msgLower.includes('executing') ||
                       msgLower.includes('order') ||
                       msgLower.includes('signal') ||
                       msgLower.includes('buy') ||
                       msgLower.includes('sell') ||
                       msgLower.includes('trade') ||
                       msgLower.includes('position') ||
                       msg.level === 'trade' ||
                       msg.level === 'signal';
            })
            .slice(-30) // Keep last 30 trading activities
            .reverse(); // Most recent first

        // Extract stats
        const signals = tradingMessages.filter(m =>
            m.message.toLowerCase().includes('signal') || m.level === 'signal'
        ).length;
        const orders = tradingMessages.filter(m =>
            m.message.toLowerCase().includes('order') || m.level === 'trade'
        ).length;
        const trades = tradingMessages.filter(m =>
            m.message.toLowerCase().includes('executing') ||
            (m.level === 'trade' && !m.message.toLowerCase().includes('order'))
        ).length;

        setStats({
            totalSignals: signals,
            totalOrders: orders,
            totalTrades: trades,
            activePositions: stats.activePositions
        });

        setActivities(tradingMessages);

        // Auto-scroll to top for new activities
        if (containerRef.current) {
            containerRef.current.scrollTop = 0;
        }
    };

    const getActivityType = (message) => {
        const msg = message.toLowerCase();
        if (msg.includes('buy') || msg.includes('executing buy')) {
            return 'buy';
        }
        if (msg.includes('sell') || msg.includes('executing sell')) {
            return 'sell';
        }
        if (msg.includes('signal')) {
            return 'signal';
        }
        if (msg.includes('order')) {
            return 'order';
        }
        return 'info';
    };

    const getActivityIcon = (type, level) => {
        switch (type) {
            case 'buy':
                return <ArrowUpRight size={18} className="activity-icon buy" />;
            case 'sell':
                return <ArrowDownRight size={18} className="activity-icon sell" />;
            case 'signal':
                return <Zap size={18} className="activity-icon signal" />;
            case 'order':
                return level === 'trade' ?
                    <CheckCircle2 size={18} className="activity-icon order-filled" /> :
                    <Clock size={18} className="activity-icon order-pending" />;
            default:
                return <Activity size={18} className="activity-icon info" />;
        }
    };

    const formatActivityMessage = (message) => {
        // Highlight symbol names, prices, and quantities
        let formatted = message;

        // Highlight symbols (uppercase 2-5 letter codes)
        formatted = formatted.replace(/\b([A-Z]{2,5})\b/g, '<strong>$1</strong>');

        // Highlight prices
        formatted = formatted.replace(/\$(\d+\.?\d*)/g, '<span class="highlight-price">$$1</span>');

        // Highlight quantities
        formatted = formatted.replace(/(\d+)\s*(?:shares|share)/gi, '<span class="highlight-qty">$1 shares</span>');

        return formatted;
    };

    return (
        <div className="live-trading-activity">
            <div className="activity-header">
                <div className="header-left">
                    <Activity size={20} className={isLive ? "pulse" : ""} />
                    <h3>Live Trading Activity</h3>
                    {isLive && (
                        <span className="live-indicator">
                            <span className="live-dot"></span>
                            LIVE
                        </span>
                    )}
                </div>
                <div className="activity-stats">
                    <div className="stat-item">
                        <Zap size={14} />
                        <span>{stats.totalSignals}</span>
                        <span className="stat-label">Signals</span>
                    </div>
                    <div className="stat-item">
                        <Clock size={14} />
                        <span>{stats.totalOrders}</span>
                        <span className="stat-label">Orders</span>
                    </div>
                    <div className="stat-item">
                        <CheckCircle2 size={14} />
                        <span>{stats.totalTrades}</span>
                        <span className="stat-label">Trades</span>
                    </div>
                    <div className="stat-item">
                        <DollarSign size={14} />
                        <span>{stats.activePositions}</span>
                        <span className="stat-label">Positions</span>
                    </div>
                </div>
            </div>

            <div className="activity-list" ref={containerRef}>
                <AnimatePresence>
                    {activities.length === 0 ? (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="activity-empty"
                        >
                            <Activity size={48} style={{ opacity: 0.3, marginBottom: '1rem' }} />
                            <p>Waiting for trading activity...</p>
                            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                                {isLive
                                    ? "Bot is running - activity will appear here when signals are generated"
                                    : "Start the bot to see trading activity"
                                }
                            </p>
                        </motion.div>
                    ) : (
                        activities.map((activity, index) => {
                            const type = getActivityType(activity.message);
                            const isImportant = type === 'buy' || type === 'sell' || activity.level === 'trade';

                            return (
                                <motion.div
                                    key={`${activity.timestamp}-${index}`}
                                    initial={{ opacity: 0, x: -20, scale: 0.95 }}
                                    animate={{ opacity: 1, x: 0, scale: 1 }}
                                    exit={{ opacity: 0, x: 20, scale: 0.95 }}
                                    transition={{ duration: 0.3 }}
                                    className={`activity-item activity-${type} ${isImportant ? 'activity-important' : ''}`}
                                >
                                    <div className="activity-icon-wrapper">
                                        {getActivityIcon(type, activity.level)}
                                    </div>
                                    <div className="activity-content">
                                        <div className="activity-message"
                                            dangerouslySetInnerHTML={{
                                                __html: formatActivityMessage(activity.message)
                                            }}
                                        />
                                        <div className="activity-meta">
                                            <span className="activity-time">
                                                {new Date(activity.timestamp).toLocaleTimeString()}
                                            </span>
                                            {activity.level && (
                                                <span className={`activity-level activity-level-${activity.level}`}>
                                                    {activity.level.toUpperCase()}
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                </motion.div>
                            );
                        })
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
};

export default LiveTradingActivity;
