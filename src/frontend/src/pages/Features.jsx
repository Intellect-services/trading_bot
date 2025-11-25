import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, XCircle, AlertCircle, Info, ExternalLink, Zap, Database, TrendingUp, Settings, Activity } from 'lucide-react';
import { api } from '../services/api';
import './Features.css';

const Features = () => {
    const [features, setFeatures] = useState(null);
    const [marketInfo, setMarketInfo] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchFeaturesStatus();
    }, []);

    const fetchFeaturesStatus = async () => {
        try {
            const response = await api.get('/api/features/status');
            if (response.data.status === 'success') {
                setFeatures(response.data.features);
                setMarketInfo(response.data.market);
            } else {
                setError(response.data.message || 'Failed to load features');
            }
        } catch (err) {
            console.error('Error fetching features:', err);
            setError('Failed to load features status');
        } finally {
            setLoading(false);
        }
    };

    const getStatusIcon = (implemented, worksWhenClosed) => {
        if (implemented) {
            return <CheckCircle2 size={20} className="status-icon implemented" />;
        }
        return <XCircle size={20} className="status-icon not-implemented" />;
    };

    const categorizeFeatures = () => {
        if (!features) return {};

        const categories = {
            trading: [],
            data: [],
            strategy: [],
            advanced: []
        };

        Object.entries(features).forEach(([key, feature]) => {
            if (key.includes('order') || key.includes('position')) {
                categories.trading.push({ key, ...feature });
            } else if (key.includes('portfolio') || key.includes('account') || key.includes('data')) {
                categories.data.push({ key, ...feature });
            } else if (key.includes('strategy') || key.includes('ai') || key.includes('backtest')) {
                categories.strategy.push({ key, ...feature });
            } else {
                categories.advanced.push({ key, ...feature });
            }
        });

        return categories;
    };

    const FeatureCard = ({ featureKey, feature }) => (
        <motion.div
            className="feature-card"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
        >
            <div className="feature-header">
                <div className="feature-status">
                    {getStatusIcon(feature.implemented, feature.works_when_closed)}
                    <span className="feature-name">{featureKey.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                </div>
                {feature.implemented && feature.works_when_closed && (
                    <span className="badge badge-works-closed">Works When Closed</span>
                )}
            </div>

            <p className="feature-description">{feature.description}</p>

            <div className="feature-meta">
                <div className="meta-item">
                    <span className="meta-label">UI Location:</span>
                    <span className="meta-value">{feature.ui_location || 'Not exposed'}</span>
                </div>
            </div>
        </motion.div>
    );

    if (loading) {
        return (
            <div className="features-page">
                <div className="loading-container">
                    <Activity className="loading-spinner" size={48} />
                    <p>Loading features...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="features-page">
                <div className="error-container">
                    <AlertCircle size={48} />
                    <p>{error}</p>
                </div>
            </div>
        );
    }

    const categories = categorizeFeatures();

    return (
        <div className="features-page">
            <div className="features-header">
                <h1>Platform Features & Capabilities</h1>
                <p className="subtitle">
                    Comprehensive overview of all implemented features and their availability
                </p>
            </div>

            {marketInfo && (
                <motion.div
                    className="market-info-banner"
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <div className="banner-content">
                        <div className="market-status-display">
                            <Activity size={20} />
                            <div>
                                <strong>Market Status:</strong>
                                <span className={marketInfo.is_open ? 'status-open' : 'status-closed'}>
                                    {marketInfo.is_open ? 'OPEN' : 'CLOSED'}
                                </span>
                            </div>
                        </div>
                        {marketInfo.next_open && (
                            <div className="market-detail">
                                <strong>Next Open:</strong> {new Date(marketInfo.next_open).toLocaleString()}
                            </div>
                        )}
                        <div className="market-detail">
                            <strong>Hours:</strong> {marketInfo.market_hours || 'Monday-Friday, 9:30 AM - 4:00 PM ET'}
                        </div>
                    </div>
                </motion.div>
            )}

            <div className="features-summary">
                <div className="summary-card">
                    <Zap size={24} />
                    <div>
                        <div className="summary-value">{Object.values(features || {}).filter(f => f.implemented).length}</div>
                        <div className="summary-label">Total Features</div>
                    </div>
                </div>
                <div className="summary-card">
                    <CheckCircle2 size={24} />
                    <div>
                        <div className="summary-value">
                            {Object.values(features || {}).filter(f => f.implemented && f.works_when_closed).length}
                        </div>
                        <div className="summary-label">Available When Market Closed</div>
                    </div>
                </div>
                <div className="summary-card">
                    <Database size={24} />
                    <div>
                        <div className="summary-value">
                            {Object.values(features || {}).filter(f => f.implemented && f.ui_location !== 'Not exposed').length}
                        </div>
                        <div className="summary-label">Exposed in UI</div>
                    </div>
                </div>
            </div>

            <div className="alpaca-free-tier-section">
                <div className="section-header">
                    <Info size={24} />
                    <h2>Alpaca Free Tier Features</h2>
                </div>
                <div className="free-tier-info">
                    <p>
                        The following features use <strong>FREE</strong> Alpaca API endpoints available in the free tier for paper trading.
                        No subscription required!
                    </p>
                    <ul>
                        <li>All order types (Market, Limit, Stop, Trailing Stop, Bracket)</li>
                        <li>Portfolio history and account activities</li>
                        <li>WebSocket streaming for market data (paper trading)</li>
                        <li>Account management, positions, and order management</li>
                    </ul>
                </div>
            </div>

            <div className="features-categories">
                <div className="category-section">
                    <div className="section-header">
                        <TrendingUp size={24} />
                        <h2>Trading Features</h2>
                    </div>
                    <div className="features-grid">
                        {categories.trading.map(({ key, ...feature }) => (
                            <FeatureCard key={key} featureKey={key} feature={feature} />
                        ))}
                    </div>
                </div>

                <div className="category-section">
                    <div className="section-header">
                        <Database size={24} />
                        <h2>Data Features</h2>
                    </div>
                    <div className="features-grid">
                        {categories.data.map(({ key, ...feature }) => (
                            <FeatureCard key={key} featureKey={key} feature={feature} />
                        ))}
                    </div>
                </div>

                <div className="category-section">
                    <div className="section-header">
                        <Settings size={24} />
                        <h2>Strategy Features</h2>
                    </div>
                    <div className="features-grid">
                        {categories.strategy.map(({ key, ...feature }) => (
                            <FeatureCard key={key} featureKey={key} feature={feature} />
                        ))}
                    </div>
                </div>

                <div className="category-section">
                    <div className="section-header">
                        <Zap size={24} />
                        <h2>Advanced Features</h2>
                    </div>
                    <div className="features-grid">
                        {categories.advanced.map(({ key, ...feature }) => (
                            <FeatureCard key={key} featureKey={key} feature={feature} />
                        ))}
                    </div>
                </div>
            </div>

            <div className="features-footer">
                <Info size={20} />
                <p>
                    All features listed above are implemented in the backend. Features marked "Not exposed" have APIs available
                    but are not yet integrated into the UI. Check the roadmap for upcoming UI additions.
                </p>
            </div>
        </div>
    );
};

export default Features;
