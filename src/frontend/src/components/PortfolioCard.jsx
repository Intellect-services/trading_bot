import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, DollarSign, Wallet } from 'lucide-react';

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
            icon: DollarSign,
            gradient: 'var(--gradient-primary)',
            highlight: true
        },
        {
            label: 'Daily P&L',
            value: dailyChange,
            percent: dailyChangePercent,
            icon: isPositive ? TrendingUp : TrendingDown,
            gradient: isPositive ? 'var(--gradient-success)' : 'var(--gradient-danger)',
            isChange: true
        },
        {
            label: 'Buying Power',
            value: buyingPower,
            icon: Wallet,
            gradient: 'var(--gradient-secondary)'
        },
        {
            label: 'Cash',
            value: cash,
            icon: DollarSign,
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
                            {/* Icon */}
                            <div style={{
                                width: '48px',
                                height: '48px',
                                borderRadius: '12px',
                                background: stat.gradient,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                marginBottom: '1rem',
                                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.2)'
                            }}>
                                <Icon size={24} color="white" />
                            </div>

                            {/* Label */}
                            <p style={{
                                fontSize: '0.875rem',
                                color: 'var(--text-muted)',
                                marginBottom: '0.5rem',
                                fontWeight: '500',
                                letterSpacing: '0.025em'
                            }}>
                                {stat.label}
                            </p>

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
