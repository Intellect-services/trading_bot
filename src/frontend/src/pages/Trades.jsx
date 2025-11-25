import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { botAPI, socket } from '../services/api';
import { TrendingUp, ArrowUpRight, ArrowDownRight } from 'lucide-react';

const Trades = () => {
    const [positions, setPositions] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await botAPI.getDashboardData();
                if (response.data.status === 'success') {
                    setPositions(response.data.positions || []);
                }
            } catch (err) {
                console.error('Error fetching trades:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchData();

        socket.on('dashboard_update', (newData) => {
            if (newData.status === 'success' && newData.positions) {
                setPositions(newData.positions);
            }
        });

        return () => {
            socket.off('dashboard_update');
        };
    }, []);

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
            <div style={{ marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <div style={{
                    width: '48px',
                    height: '48px',
                    borderRadius: '12px',
                    background: 'rgba(99, 102, 241, 0.1)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'var(--accent-primary)'
                }}>
                    <TrendingUp size={24} />
                </div>
                <div>
                    <h1 style={{ fontSize: '1.875rem', marginBottom: '0.25rem' }}>Positions</h1>
                    <p style={{ color: 'var(--text-secondary)' }}>Monitor and manage your open positions.</p>
                </div>
            </div>

            <div className="glass-card" style={{ overflow: 'hidden' }}>
                <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                        <thead>
                            <tr style={{ borderBottom: '1px solid var(--glass-border)', background: 'rgba(255,255,255,0.02)' }}>
                                <th style={{ textAlign: 'left', padding: '1rem 1.5rem', color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: '600', letterSpacing: '0.05em' }}>SYMBOL</th>
                                <th style={{ textAlign: 'right', padding: '1rem 1.5rem', color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: '600', letterSpacing: '0.05em' }}>QTY</th>
                                <th style={{ textAlign: 'right', padding: '1rem 1.5rem', color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: '600', letterSpacing: '0.05em' }}>AVG ENTRY</th>
                                <th style={{ textAlign: 'right', padding: '1rem 1.5rem', color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: '600', letterSpacing: '0.05em' }}>CURRENT</th>
                                <th style={{ textAlign: 'right', padding: '1rem 1.5rem', color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: '600', letterSpacing: '0.05em' }}>MARKET VALUE</th>
                                <th style={{ textAlign: 'right', padding: '1rem 1.5rem', color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: '600', letterSpacing: '0.05em' }}>TODAY'S CHANGE</th>
                                <th style={{ textAlign: 'right', padding: '1rem 1.5rem', color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: '600', letterSpacing: '0.05em' }}>TOTAL P&L</th>
                            </tr>
                        </thead>
                        <tbody>
                            {positions.length > 0 ? (
                                positions.map((trade) => {
                                    const pnl = parseFloat(trade.unrealized_pl);
                                    const isPositive = pnl >= 0;
                                    const change = parseFloat(trade.change_today);
                                    const isChangePositive = change >= 0;

                                    return (
                                        <tr key={trade.symbol} style={{ borderBottom: '1px solid rgba(255,255,255,0.02)', transition: 'background 0.2s' }} className="hover:bg-white/5">
                                            <td style={{ padding: '1rem 1.5rem' }}>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                                    <div style={{
                                                        width: '36px',
                                                        height: '36px',
                                                        borderRadius: '8px',
                                                        background: 'rgba(255,255,255,0.05)',
                                                        display: 'flex',
                                                        alignItems: 'center',
                                                        justifyContent: 'center',
                                                        fontWeight: '600',
                                                        fontSize: '0.75rem'
                                                    }}>
                                                        {trade.symbol}
                                                    </div>
                                                    <span style={{ fontWeight: '600', fontSize: '1rem' }}>{trade.symbol}</span>
                                                </div>
                                            </td>
                                            <td style={{ textAlign: 'right', padding: '1rem 1.5rem', fontWeight: '500' }}>{trade.qty}</td>
                                            <td style={{ textAlign: 'right', padding: '1rem 1.5rem', color: 'var(--text-secondary)' }}>
                                                ${parseFloat(trade.avg_entry_price).toFixed(2)}
                                            </td>
                                            <td style={{ textAlign: 'right', padding: '1rem 1.5rem', fontWeight: '600' }}>
                                                ${parseFloat(trade.current_price).toFixed(2)}
                                            </td>
                                            <td style={{ textAlign: 'right', padding: '1rem 1.5rem', fontWeight: '500' }}>
                                                ${parseFloat(trade.market_value).toLocaleString()}
                                            </td>
                                            <td style={{ textAlign: 'right', padding: '1rem 1.5rem' }}>
                                                <span style={{ color: isChangePositive ? 'var(--success)' : 'var(--danger)' }}>
                                                    {(change * 100).toFixed(2)}%
                                                </span>
                                            </td>
                                            <td style={{ textAlign: 'right', padding: '1rem 1.5rem' }}>
                                                <div style={{
                                                    display: 'inline-flex',
                                                    alignItems: 'center',
                                                    gap: '0.25rem',
                                                    color: isPositive ? 'var(--success)' : 'var(--danger)',
                                                    fontWeight: '600'
                                                }}>
                                                    {isPositive ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />}
                                                    ${Math.abs(pnl).toFixed(2)}
                                                </div>
                                            </td>
                                        </tr>
                                    );
                                })
                            ) : (
                                <tr>
                                    <td colSpan="7" style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                                        No active positions
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </motion.div>
    );
};

export default Trades;
