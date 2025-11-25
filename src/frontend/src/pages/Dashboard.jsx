import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { botAPI, socket } from '../services/api';
import PortfolioCard from '../components/PortfolioCard';
import StockChart from '../components/StockChart';
import ActiveTrades from '../components/ActiveTrades';
import BotControlPanel from '../components/BotControlPanel';
import BotMonitor from '../components/BotMonitor';
import { CardSkeleton, ChartSkeleton, TableSkeleton } from '../components/LoadingSkeleton';

const Dashboard = () => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchData = async () => {
        try {
            const response = await botAPI.getDashboardData();
            if (response.data.status === 'success') {
                setData(response.data);
                setError(null); // Clear any previous errors
            } else {
                // Check if it's a "not configured" message - this is informational, not an error
                if (response.data.message && response.data.message.includes('not configured')) {
                    // Still set the data, but show a warning message
                    setData(response.data);
                    setError(null);
                } else {
                    setError(response.data.message || 'Failed to load dashboard data');
                }
            }
        } catch (err) {
            console.error('Error fetching dashboard data:', err);
            // Only set error if it's a real error (network, 500, etc.)
            if (err.response && err.response.status >= 500) {
                setError('Failed to load dashboard data');
            } else {
                // For 401/403, let the auth system handle it
                setError(null);
            }
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();

        // Listen for real-time updates
        socket.on('dashboard_update', (newData) => {
            console.log('Received dashboard update:', newData);
            if (newData.status === 'success') {
                setData(newData);
            }
        });

        socket.on('status_update', (statusData) => {
            console.log('Received status update:', statusData);
            setData((prev) => prev ? { ...prev, ...statusData } : prev);
        });

        return () => {
            socket.off('dashboard_update');
            socket.off('status_update');
        };
    }, []);

    if (loading) {
        return (
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.3 }}
            >
                <div style={{ marginBottom: '2rem' }}>
                    <div className="skeleton skeleton-title" style={{ width: '200px', marginBottom: '0.5rem' }} />
                    <div className="skeleton skeleton-text" style={{ width: '300px' }} />
                </div>

                <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
                    gap: '1.5rem',
                    marginBottom: '2rem'
                }}>
                    <CardSkeleton />
                    <CardSkeleton />
                    <CardSkeleton />
                    <CardSkeleton />
                </div>

                <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
                    gap: '1.5rem'
                }}>
                    <ChartSkeleton />
                    <TableSkeleton />
                    <div className="glass-card" style={{ padding: '1.5rem' }}>
                        <div className="skeleton skeleton-text" style={{ width: '50%', marginBottom: '1rem' }} />
                        <div className="skeleton" style={{ width: '100%', height: '200px' }} />
                    </div>
                </div>
            </motion.div>
        );
    }

    if (error) {
        return (
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="glass-panel"
                style={{
                    padding: '3rem',
                    textAlign: 'center',
                    maxWidth: '500px',
                    margin: '4rem auto'
                }}
            >
                <div style={{
                    width: '64px',
                    height: '64px',
                    borderRadius: '50%',
                    background: 'var(--gradient-danger)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto 1.5rem',
                    opacity: 0.8
                }}>
                    <span style={{ fontSize: '2rem' }}>⚠️</span>
                </div>
                <h3 style={{ marginBottom: '1rem', fontSize: '1.5rem' }}>Error Loading Dashboard</h3>
                <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>{error}</p>
                <button
                    className="btn-primary"
                    onClick={fetchData}
                >
                    Retry
                </button>
            </motion.div>
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
                transition={{ duration: 0.4 }}
                style={{ marginBottom: '2rem' }}
            >
                <h1 style={{
                    fontSize: '1.75rem',
                    marginBottom: '0.5rem',
                    fontWeight: '600',
                    letterSpacing: '-0.025em',
                    color: 'var(--text-primary)'
                }}>
                    Dashboard
                </h1>
                <p style={{ color: 'var(--text-secondary)', fontSize: '1rem' }}>
                    Welcome back, here's your portfolio overview.
                </p>
            </motion.div>

            {/* Bot Not Configured Warning */}
            {data?.message && data.message.includes('not configured') && (
                <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="glass-panel"
                    style={{
                        padding: '1.5rem',
                        marginBottom: '2rem',
                        background: 'rgba(255, 193, 7, 0.1)',
                        border: '1px solid rgba(255, 193, 7, 0.3)',
                        borderRadius: 'var(--radius-md)'
                    }}
                >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                        <span style={{ fontSize: '1.5rem' }}>⚠️</span>
                        <div style={{ flex: 1 }}>
                            <h3 style={{ marginBottom: '0.5rem', fontSize: '1rem', fontWeight: '600' }}>
                                Trading Bot Not Configured
                            </h3>
                            <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', margin: 0 }}>
                                Please configure your Alpaca API credentials in{' '}
                                <a href="/account" style={{ color: 'var(--accent-primary)', textDecoration: 'underline' }}>
                                    Account Settings
                                </a>{' '}
                                to start trading.
                            </p>
                        </div>
                    </div>
                </motion.div>
            )}

            {/* Portfolio Cards */}
            <PortfolioCard data={data?.account || {}} />

            {/* Main Content Grid */}
            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(12, 1fr)',
                gap: '1.5rem'
            }}>
                {/* Bot Control Panel (1/4) and Portfolio Performance (3/4) on same row */}
                <div style={{ gridColumn: 'span 3' }}>
                    <BotControlPanel />
                </div>
                <div style={{ gridColumn: 'span 9' }}>
                    <StockChart data={data?.performance?.history || []} />
                </div>

                {/* Active Positions - Full Width */}
                <div style={{ gridColumn: '1 / -1' }}>
                    <ActiveTrades trades={data?.positions || []} />
                </div>

                {/* Bot Monitor - Full Width */}
                <div style={{ gridColumn: '1 / -1' }}>
                    <BotMonitor />
                </div>
            </div>
        </motion.div>
    );
};

export default Dashboard;
