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
    ArrowDownRight,
    Target,
    BarChart3,
    RefreshCw,
    Filter,
    Info
} from 'lucide-react';
import { botAPI, socket } from '../services/api';
import '../components/LiveTradingActivity.css';

const TradingActivity = () => {
    const [activities, setActivities] = useState([]);
    const [positions, setPositions] = useState([]);
    const [orders, setOrders] = useState([]);
    const [stats, setStats] = useState({
        totalSignals: 0,
        totalOrders: 0,
        totalTrades: 0,
        activePositions: 0,
        totalPnL: 0,
        todayPnL: 0,
        winRate: 0
    });
    const [isLive, setIsLive] = useState(false);
    const [filter, setFilter] = useState('all'); // all, signals, orders, trades
    const [loading, setLoading] = useState(true);
    const containerRef = useRef(null);

    useEffect(() => {
        fetchAllData();

        // Poll for status every 2 seconds
        const interval = setInterval(fetchAllData, 2000);

        // Listen for Socket.IO updates
        socket.on('status_update', handleStatusUpdate);
        socket.on('dashboard_update', handleDashboardUpdate);

        return () => {
            clearInterval(interval);
            socket.off('status_update');
            socket.off('dashboard_update');
        };
    }, []);

    const fetchAllData = async () => {
        try {
            // Fetch bot status
            const statusResponse = await botAPI.getStatus();
            if (statusResponse.data.status_messages) {
                processStatusMessages(statusResponse.data.status_messages);
                setIsLive(statusResponse.data.is_running || false);
            }

            // Fetch dashboard data for positions and stats
            const dashboardResponse = await botAPI.getDashboardData();
            if (dashboardResponse.data.status === 'success') {
                setPositions(dashboardResponse.data.positions || []);

                // Calculate stats
                const account = dashboardResponse.data.account || {};
                const performance = dashboardResponse.data.performance || {};

                setStats(prev => ({
                    ...prev,
                    activePositions: dashboardResponse.data.positions?.length || 0,
                    totalPnL: performance.total_pnl || 0,
                    todayPnL: performance.daily_pnl || 0,
                    winRate: performance.win_rate || 0
                }));
            }

            setLoading(false);
        } catch (error) {
            console.error('Error fetching trading data:', error);
            setLoading(false);
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
            setPositions(data.positions || []);
            setStats(prev => ({
                ...prev,
                activePositions: data.positions.length || 0
            }));
        }
        if (data.account) {
            const performance = data.performance || {};
            setStats(prev => ({
                ...prev,
                totalPnL: performance.total_pnl || prev.totalPnL,
                todayPnL: performance.daily_pnl || prev.todayPnL,
                winRate: performance.win_rate || prev.winRate
            }));
        }
    };

    const processStatusMessages = (messages) => {
        // Filter and process trading-related messages ONLY
        const tradingMessages = messages
            .filter(msg => {
                const msgLower = msg.message.toLowerCase();
                // Only include actual trading events, not system messages
                return (
                    msgLower.includes('executing') ||
                    msgLower.includes('order') ||
                    msgLower.includes('signal') ||
                    msgLower.includes('buy') ||
                    msgLower.includes('sell') ||
                    msgLower.includes('trade') ||
                    msgLower.includes('position') ||
                    msg.level === 'trade' ||
                    msg.level === 'signal'
                ) && !msgLower.includes('error fetching data') &&
                   !msgLower.includes('market data') &&
                   !msgLower.includes('database') &&
                   !msgLower.includes('initialized') &&
                   !msgLower.includes('connected');
            })
            .slice(-100) // Keep last 100 trading activities
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

        setStats(prev => ({
            ...prev,
            totalSignals: signals,
            totalOrders: orders,
            totalTrades: trades
        }));

        setActivities(tradingMessages);
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
        let formatted = message;

        // Highlight symbols (uppercase 2-5 letter codes)
        formatted = formatted.replace(/\b([A-Z]{2,5})\b/g, '<strong>$1</strong>');

        // Highlight prices
        formatted = formatted.replace(/\$(\d+\.?\d*)/g, '<span class="highlight-price">$$1</span>');

        // Highlight quantities
        formatted = formatted.replace(/(\d+)\s*(?:shares|share)/gi, '<span class="highlight-qty">$1 shares</span>');

        return formatted;
    };

    const filteredActivities = activities.filter(activity => {
        if (filter === 'all') return true;
        const type = getActivityType(activity.message);
        return filter === type || (filter === 'orders' && type === 'order');
    });

    // Show only the last 10 events
    const displayedActivities = filteredActivities.slice(0, 10);

    const formatCurrency = (value) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(value);
    };

    if (loading) {
        return (
            <div className="flex-center" style={{ height: '100%', minHeight: '400px' }}>
                <div style={{
                    width: '40px',
                    height: '40px',
                    border: '3px solid rgba(99, 102, 241, 0.3)',
                    borderTopColor: 'var(--accent-primary)',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite'
                }} />
                <style>{`
                    @keyframes spin {
                        to { transform: rotate(360deg); }
                    }
                `}</style>
            </div>
        );
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
        >
            {/* Header */}
            <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                style={{ marginBottom: '2rem' }}
            >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
                    <div>
                        <h1 style={{
                            fontSize: '1.75rem',
                            marginBottom: '0.5rem',
                            fontWeight: '600',
                            letterSpacing: '-0.025em',
                            color: 'var(--text-primary)',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.75rem'
                        }}>
                            <Activity size={28} className={isLive ? "pulse" : ""} />
                            Trading Activity
                            {isLive && (
                                <span style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '0.5rem',
                                    fontSize: '0.875rem',
                                    fontWeight: '600',
                                    color: '#10b981',
                                    background: 'rgba(16, 185, 129, 0.1)',
                                    padding: '0.25rem 0.75rem',
                                    borderRadius: '1rem'
                                }}>
                                    <span style={{
                                        width: '8px',
                                        height: '8px',
                                        background: '#10b981',
                                        borderRadius: '50%',
                                        animation: 'pulse 2s infinite'
                                    }}></span>
                                    LIVE
                                </span>
                            )}
                        </h1>
                        <p style={{ color: 'var(--text-secondary)', fontSize: '1rem' }}>
                            Real-time trading signals, orders, and trade executions
                        </p>
                    </div>
                    <button
                        onClick={fetchAllData}
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            padding: '0.5rem 1rem',
                            background: 'rgba(99, 102, 241, 0.1)',
                            border: '1px solid rgba(99, 102, 241, 0.3)',
                            borderRadius: 'var(--radius-md)',
                            color: 'var(--accent-primary)',
                            cursor: 'pointer',
                            fontSize: '0.875rem',
                            fontWeight: '500'
                        }}
                    >
                        <RefreshCw size={16} />
                        Refresh
                    </button>
                </div>
            </motion.div>

            {/* Trading Stats Cards */}
            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '1rem',
                marginBottom: '2rem'
            }}>
                <div className="glass-card" style={{ padding: '1.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                        <Zap size={20} style={{ color: '#f59e0b' }} />
                        <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Signals</span>
                    </div>
                    <div style={{ fontSize: '1.5rem', fontWeight: '600', color: 'var(--text-primary)' }}>
                        {stats.totalSignals}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                        Generated today
                    </div>
                </div>

                <div className="glass-card" style={{ padding: '1.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                        <CheckCircle2 size={20} style={{ color: '#6366f1' }} />
                        <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Orders</span>
                    </div>
                    <div style={{ fontSize: '1.5rem', fontWeight: '600', color: 'var(--text-primary)' }}>
                        {stats.totalOrders}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                        Placed today
                    </div>
                </div>

                <div className="glass-card" style={{ padding: '1.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                        <Activity size={20} style={{ color: '#10b981' }} />
                        <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Trades</span>
                    </div>
                    <div style={{ fontSize: '1.5rem', fontWeight: '600', color: 'var(--text-primary)' }}>
                        {stats.totalTrades}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                        Executed today
                    </div>
                </div>

                <div className="glass-card" style={{ padding: '1.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                        <Target size={20} style={{ color: '#8b5cf6' }} />
                        <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Positions</span>
                    </div>
                    <div style={{ fontSize: '1.5rem', fontWeight: '600', color: 'var(--text-primary)' }}>
                        {stats.activePositions}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                        Currently open
                    </div>
                </div>

                <div className="glass-card" style={{ padding: '1.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                        <TrendingUp size={20} style={{ color: stats.todayPnL >= 0 ? '#10b981' : '#ef4444' }} />
                        <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Today P&L</span>
                    </div>
                    <div style={{ fontSize: '1.5rem', fontWeight: '600', color: stats.todayPnL >= 0 ? '#10b981' : '#ef4444' }}>
                        {formatCurrency(stats.todayPnL)}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                        Daily performance
                    </div>
                </div>

                <div className="glass-card" style={{ padding: '1.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                        <BarChart3 size={20} style={{ color: '#6366f1' }} />
                        <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Win Rate</span>
                    </div>
                    <div style={{ fontSize: '1.5rem', fontWeight: '600', color: 'var(--text-primary)' }}>
                        {(stats.winRate * 100).toFixed(1)}%
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                        Success rate
                    </div>
                </div>
            </div>

            {/* Main Content Grid */}
            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(12, 1fr)',
                gap: '1.5rem'
            }}>
                {/* Live Activity Feed - Left Side */}
                <div style={{ gridColumn: 'span 8' }}>
                    <div className="glass-card" style={{ padding: '1.5rem', height: '100%', display: 'flex', flexDirection: 'column' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                            <h3 style={{ fontSize: '1.125rem', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                <Activity size={20} />
                                Live Activity Feed
                            </h3>
                            <div style={{ display: 'flex', gap: '0.5rem', background: 'rgba(255, 255, 255, 0.05)', borderRadius: 'var(--radius-md)', padding: '0.25rem' }}>
                                {['all', 'signals', 'orders', 'trades'].map((f) => (
                                    <button
                                        key={f}
                                        onClick={() => setFilter(f)}
                                        style={{
                                            background: filter === f ? 'var(--accent-primary)' : 'transparent',
                                            color: filter === f ? 'white' : 'var(--text-muted)',
                                            border: 'none',
                                            padding: '0.375rem 0.75rem',
                                            borderRadius: 'var(--radius-sm)',
                                            fontSize: '0.75rem',
                                            fontWeight: '500',
                                            cursor: 'pointer',
                                            transition: 'all 0.2s',
                                            textTransform: 'capitalize'
                                        }}
                                    >
                                        {f === 'all' ? 'All' : f}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="activity-list" ref={containerRef} style={{ flex: 1, overflow: 'visible' }}>
                            <AnimatePresence>
                                {filteredActivities.length === 0 ? (
                                    <motion.div
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        className="activity-empty"
                                        style={{ minHeight: '300px' }}
                                    >
                                        <Activity size={48} style={{ opacity: 0.3, marginBottom: '1rem' }} />
                                        <p>No trading activity yet</p>
                                        <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                                            {isLive
                                                ? "Activity will appear here when the bot generates signals and executes trades"
                                                : "Start the bot to see trading activity"
                                            }
                                        </p>
                                    </motion.div>
                                ) : (
                                    displayedActivities.map((activity, index) => {
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
                                                            {new Date(activity.timestamp).toLocaleString()}
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

                            {filteredActivities.length > 10 && (
                                <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--glass-border)', textAlign: 'center' }}>
                                    <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                                        Showing last 10 of {filteredActivities.length} activities
                                    </p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Current Positions - Right Side */}
                <div style={{ gridColumn: 'span 4' }}>
                    <div className="glass-card" style={{ padding: '1.5rem', height: '100%', display: 'flex', flexDirection: 'column' }}>
                        <h3 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <Target size={20} />
                            Current Positions
                        </h3>

                        {positions.length === 0 ? (
                            <div style={{ textAlign: 'center', padding: '2rem 0', color: 'var(--text-secondary)' }}>
                                <Target size={48} style={{ opacity: 0.3, marginBottom: '1rem' }} />
                                <p style={{ fontSize: '0.875rem' }}>No open positions</p>
                                <p style={{ fontSize: '0.75rem', opacity: 0.7, marginTop: '0.5rem' }}>
                                    Positions will appear here when trades are executed
                                </p>
                            </div>
                        ) : (
                            <div style={{ flex: 1, overflow: 'visible' }}>
                                {positions.map((position, index) => {
                                    const pnl = parseFloat(position.unrealized_pl || position.pl || 0);
                                    const pnlPercent = parseFloat(position.unrealized_plpc || position.plpc || 0) * 100;

                                    return (
                                        <motion.div
                                            key={position.symbol || index}
                                            initial={{ opacity: 0, y: 10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            className="glass-card"
                                            style={{
                                                padding: '1rem',
                                                marginBottom: '0.75rem',
                                                border: `1px solid ${pnl >= 0 ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
                                                background: pnl >= 0 ? 'rgba(16, 185, 129, 0.05)' : 'rgba(239, 68, 68, 0.05)'
                                            }}
                                        >
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '0.5rem' }}>
                                                <div>
                                                    <div style={{ fontSize: '1rem', fontWeight: '600', color: 'var(--text-primary)' }}>
                                                        {position.symbol}
                                                    </div>
                                                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                                                        {parseFloat(position.qty || 0).toFixed(2)} shares @ ${parseFloat(position.avg_entry_price || 0).toFixed(2)}
                                                    </div>
                                                </div>
                                                <div style={{ textAlign: 'right' }}>
                                                    <div style={{
                                                        fontSize: '0.875rem',
                                                        fontWeight: '600',
                                                        color: pnl >= 0 ? '#10b981' : '#ef4444'
                                                    }}>
                                                        {pnl >= 0 ? '+' : ''}{formatCurrency(pnl)}
                                                    </div>
                                                    <div style={{
                                                        fontSize: '0.75rem',
                                                        color: pnl >= 0 ? '#10b981' : '#ef4444'
                                                    }}>
                                                        {pnlPercent >= 0 ? '+' : ''}{pnlPercent.toFixed(2)}%
                                                    </div>
                                                </div>
                                            </div>
                                            <div style={{
                                                fontSize: '0.75rem',
                                                color: 'var(--text-muted)',
                                                display: 'flex',
                                                justifyContent: 'space-between'
                                            }}>
                                                <span>Current: ${parseFloat(position.current_price || position.market_value || 0).toFixed(2)}</span>
                                                <span>Value: {formatCurrency(parseFloat(position.market_value || position.cost_basis || 0))}</span>
                                            </div>
                                        </motion.div>
                                    );
                                })}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Info Section */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 }}
                className="glass-panel"
                style={{
                    marginTop: '2rem',
                    padding: '1.5rem',
                    background: 'rgba(99, 102, 241, 0.05)',
                    border: '1px solid rgba(99, 102, 241, 0.2)'
                }}
            >
                <div style={{ display: 'flex', alignItems: 'start', gap: '1rem' }}>
                    <Info size={20} style={{ color: 'var(--accent-primary)', flexShrink: 0, marginTop: '0.125rem' }} />
                    <div>
                        <h4 style={{ fontSize: '1rem', fontWeight: '600', marginBottom: '0.5rem' }}>
                            Understanding Trading Activity
                        </h4>
                        <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                            <p style={{ marginBottom: '0.5rem' }}>
                                <strong>Signals:</strong> Trading signals generated by your active strategies. These indicate when the bot identifies potential buy or sell opportunities.
                            </p>
                            <p style={{ marginBottom: '0.5rem' }}>
                                <strong>Orders:</strong> Orders placed with the broker (Alpaca). These include market orders, limit orders, and advanced order types like bracket orders.
                            </p>
                            <p style={{ marginBottom: '0.5rem' }}>
                                <strong>Trades:</strong> Successfully executed trades that result in new positions or closed positions.
                            </p>
                            <p>
                                <strong>Positions:</strong> Currently open positions showing unrealized profit/loss. Positions are updated in real-time as market prices change.
                            </p>
                        </div>
                    </div>
                </div>
            </motion.div>
        </motion.div>
    );
};

export default TradingActivity;
