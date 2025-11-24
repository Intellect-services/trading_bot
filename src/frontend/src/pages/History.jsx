import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { botAPI } from '../services/api';
import { History as HistoryIcon, ArrowUpRight, ArrowDownRight, Clock } from 'lucide-react';

const History = () => {
    const [orders, setOrders] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchHistory = async () => {
            try {
                const response = await botAPI.getHistory();
                if (response.data.status === 'success') {
                    setOrders(response.data.orders);
                } else {
                    setError(response.data.message);
                }
            } catch (err) {
                console.error('Error fetching history:', err);
                setError('Failed to load trade history');
            } finally {
                setLoading(false);
            }
        };

        fetchHistory();
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
                    <HistoryIcon size={24} />
                </div>
                <div>
                    <h1 style={{ fontSize: '1.875rem', marginBottom: '0.25rem' }}>Trade History</h1>
                    <p style={{ color: 'var(--text-secondary)' }}>View your past trading activity.</p>
                </div>
            </div>

            <div className="glass-card" style={{ overflow: 'hidden' }}>
                <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                        <thead>
                            <tr style={{ borderBottom: '1px solid var(--glass-border)', background: 'rgba(255,255,255,0.02)' }}>
                                <th style={{ textAlign: 'left', padding: '1rem 1.5rem', color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: '600', letterSpacing: '0.05em' }}>DATE</th>
                                <th style={{ textAlign: 'left', padding: '1rem 1.5rem', color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: '600', letterSpacing: '0.05em' }}>SYMBOL</th>
                                <th style={{ textAlign: 'left', padding: '1rem 1.5rem', color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: '600', letterSpacing: '0.05em' }}>SIDE</th>
                                <th style={{ textAlign: 'right', padding: '1rem 1.5rem', color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: '600', letterSpacing: '0.05em' }}>QTY</th>
                                <th style={{ textAlign: 'right', padding: '1rem 1.5rem', color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: '600', letterSpacing: '0.05em' }}>PRICE</th>
                                <th style={{ textAlign: 'right', padding: '1rem 1.5rem', color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: '600', letterSpacing: '0.05em' }}>STATUS</th>
                            </tr>
                        </thead>
                        <tbody>
                            {orders.length > 0 ? (
                                orders.map((order) => (
                                    <tr key={order.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.02)', transition: 'background 0.2s' }} className="hover:bg-white/5">
                                        <td style={{ padding: '1rem 1.5rem', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                                <Clock size={14} />
                                                {new Date(order.created_at).toLocaleDateString()} <span style={{ color: 'var(--text-muted)' }}>{new Date(order.created_at).toLocaleTimeString()}</span>
                                            </div>
                                        </td>
                                        <td style={{ padding: '1rem 1.5rem', fontWeight: '600' }}>{order.symbol}</td>
                                        <td style={{ padding: '1rem 1.5rem' }}>
                                            <span style={{
                                                display: 'inline-flex',
                                                alignItems: 'center',
                                                gap: '0.25rem',
                                                color: order.side === 'buy' ? 'var(--success)' : 'var(--danger)',
                                                fontWeight: '600',
                                                fontSize: '0.875rem',
                                                textTransform: 'uppercase'
                                            }}>
                                                {order.side === 'buy' ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                                                {order.side}
                                            </span>
                                        </td>
                                        <td style={{ textAlign: 'right', padding: '1rem 1.5rem', fontWeight: '500' }}>{order.filled_qty || order.qty}</td>
                                        <td style={{ textAlign: 'right', padding: '1rem 1.5rem', fontWeight: '500' }}>
                                            ${(order.filled_avg_price || order.limit_price || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                        </td>
                                        <td style={{ textAlign: 'right', padding: '1rem 1.5rem' }}>
                                            <span style={{
                                                padding: '0.25rem 0.75rem',
                                                borderRadius: '1rem',
                                                fontSize: '0.75rem',
                                                fontWeight: '600',
                                                background: order.status === 'filled' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(255, 255, 255, 0.1)',
                                                color: order.status === 'filled' ? 'var(--success)' : 'var(--text-secondary)',
                                                textTransform: 'capitalize'
                                            }}>
                                                {order.status}
                                            </span>
                                        </td>
                                    </tr>
                                ))
                            ) : (
                                <tr>
                                    <td colSpan="6" style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                                        No trade history available
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

export default History;
