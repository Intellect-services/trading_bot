import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, DollarSign, Wallet, CircleDollarSign } from 'lucide-react';

const PortfolioCard = ({ data }) => {
    const portfolioValue = data?.portfolio_value || 0;
    const cash = data?.cash || 0;
    const buyingPower = data?.buying_power || 0;
    const equity = data?.equity || 0;
    const lastEquity = data?.last_equity || 0;

    const dailyChange = equity - lastEquity;
    const dailyChangePercent = lastEquity > 0 ? ((dailyChange / lastEquity) * 100) : 0;
    const isPositive = dailyChange >= 0;

    const stats = [
        {
            label: 'Total Balance',
            value: portfolioValue,
            icon: CircleDollarSign,
            iconColor: '#6366f1',
            iconBg: 'rgba(99, 102, 241, 0.15)',
            gradient: 'var(--gradient-primary)',
            highlight: true
        },
        {
            label: 'Daily P&L',
            value: dailyChange,
            percent: dailyChangePercent,
            icon: isPositive ? TrendingUp : TrendingDown,
            iconColor: isPositive ? '#10b981' : '#ef4444',
            iconBg: isPositive ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
            gradient: isPositive ? 'var(--gradient-success)' : 'var(--gradient-danger)',
            isChange: true
        },
        {
            label: 'Buying Power',
            value: buyingPower,
            icon: Wallet,
            iconColor: '#8b5cf6',
            iconBg: 'rgba(139, 92, 246, 0.15)',
            gradient: 'var(--gradient-secondary)'
        },
        {
            label: 'Cash',
            value: cash,
            icon: DollarSign,
            iconColor: '#06b6d4',
            iconBg: 'rgba(6, 182, 212, 0.15)',
            gradient: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)'
        }
    ];

    return (
        <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: '1.5rem',
            marginBottom: '2rem'
        }}>
            {stats.map((stat, index) => {
                const Icon = stat.icon;
                return (
                    <motion.div
                        key={stat.label}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.4, delay: index * 0.1 }}
                        className={stat.highlight ? "premium-card" : "glass-card"}
                        style={{
                            padding: '1.5rem',
                            position: 'relative',
                            overflow: 'hidden'
                        }}
                    >
                        {/* Background Gradient Glow */}
                        <div style={{
                            position: 'absolute',
                            top: '-50%',
                            right: '-50%',
                            width: '200%',
                            height: '200%',
                            background: stat.gradient,
                            opacity: 0.05,
                            borderRadius: '50%',
                            pointerEvents: 'none'
                        }} />

                        <div style={{ position: 'relative', zIndex: 1 }}>
                            {/* Icon and Label */}
                            <div style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.75rem',
                                marginBottom: '1rem'
                            }}>
                                <Icon
                                    size={20}
                                    style={{
                                        color: stat.iconColor || '#6366f1',
                                        strokeWidth: 2
                                    }}
                                />
                                <p style={{
                                    fontSize: '0.875rem',
                                    color: 'var(--text-secondary)',
                                    fontWeight: '500',
                                    margin: 0
                                }}>
                                    {stat.label}
                                </p>
                            </div>

                            {/* Value */}
                            <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem' }}>
                                <motion.h2
                                    initial={{ scale: 0.8 }}
                                    animate={{ scale: 1 }}
                                    transition={{ duration: 0.3, delay: index * 0.1 + 0.2 }}
                                    style={{
                                        fontSize: stat.highlight ? '2rem' : '1.75rem',
                                        fontWeight: '700',
                                        color: stat.isChange ? (isPositive ? 'var(--success)' : 'var(--danger)') : 'var(--text-primary)'
                                    }}
                                >
                                    {stat.isChange && (isPositive ? '+' : '')}
                                    ${Math.abs(stat.value).toLocaleString(undefined, {
                                        minimumFractionDigits: 2,
                                        maximumFractionDigits: 2
                                    })}
                                </motion.h2>

                                {stat.percent !== undefined && (
                                    <span style={{
                                        fontSize: '1rem',
                                        fontWeight: '600',
                                        color: isPositive ? 'var(--success-light)' : 'var(--danger-light)'
                                    }}>
                                        ({isPositive ? '+' : ''}{stat.percent.toFixed(2)}%)
                                    </span>
                                )}
                            </div>
                        </div>
                    </motion.div>
                );
            })}
        </div>
    );
};

export default PortfolioCard;
