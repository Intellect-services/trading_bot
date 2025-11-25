import React from 'react';
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';
import StockLogo from './StockLogo';

const ActiveTrades = ({ trades }) => {
    // trades is expected to be a list of positions from Alpaca

    return (
        <div className="glass-card" style={{ padding: '1.5rem', gridColumn: 'span 1', overflow: 'hidden' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <h3 style={{ fontSize: '1.125rem', fontWeight: '600' }}>Active Positions</h3>
                <span style={{
                    fontSize: '0.75rem',
                    background: 'rgba(99, 102, 241, 0.1)',
                    color: 'var(--accent-primary)',
                    padding: '0.25rem 0.5rem',
                    borderRadius: '1rem',
                    fontWeight: '600'
                }}>
                    {trades?.length || 0} Active
                </span>
            </div>

            <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                        <tr style={{ borderBottom: '1px solid var(--glass-border)' }}>
                            <th style={{ textAlign: 'left', padding: '0.75rem 0.5rem', color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: '500' }}>SYMBOL</th>
                            <th style={{ textAlign: 'right', padding: '0.75rem 0.5rem', color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: '500' }}>QTY</th>
                            <th style={{ textAlign: 'right', padding: '0.75rem 0.5rem', color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: '500' }}>ENTRY</th>
                            <th style={{ textAlign: 'right', padding: '0.75rem 0.5rem', color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: '500' }}>CURRENT</th>
                            <th style={{ textAlign: 'right', padding: '0.75rem 0.5rem', color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: '500' }}>MARKET VALUE</th>
                            <th style={{ textAlign: 'right', padding: '0.75rem 0.5rem', color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: '500' }}>P&L</th>
                            <th style={{ textAlign: 'right', padding: '0.75rem 0.5rem', color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: '500' }}>P&L %</th>
                        </tr>
                    </thead>
                    <tbody>
                        {trades && trades.length > 0 ? (
                            trades.map((trade) => {
                                const pnl = parseFloat(trade.unrealized_pl || trade.pl || 0);
                                const pnlPercent = parseFloat(trade.unrealized_plpc || trade.plpc || 0) * 100;
                                const marketValue = parseFloat(trade.market_value || trade.current_price || 0) * parseFloat(trade.qty || 0);
                                const isPositive = pnl >= 0;
                                const side = parseFloat(trade.qty || 0) >= 0 ? 'Long' : 'Short';

                                return (
                                    <tr key={trade.symbol} style={{ borderBottom: '1px solid rgba(255,255,255,0.02)' }}>
                                        <td style={{ padding: '1rem 0.5rem' }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                                <StockLogo symbol={trade.symbol} size={40} />
                                                <div style={{ display: 'flex', flexDirection: 'column' }}>
                                                    <span style={{ fontWeight: '600', fontSize: '0.875rem' }}>{trade.symbol}</span>
                                                    <span style={{ fontSize: '0.75rem', color: side === 'Long' ? 'var(--success)' : 'var(--danger)' }}>
                                                        {side}
                                                    </span>
                                                </div>
                                            </div>
                                        </td>
                                        <td style={{ textAlign: 'right', padding: '1rem 0.5rem', fontWeight: '500' }}>
                                            {Math.abs(parseFloat(trade.qty || 0)).toFixed(2)}
                                        </td>
                                        <td style={{ textAlign: 'right', padding: '1rem 0.5rem' }}>
                                            <span style={{ fontWeight: '500' }}>
                                                ${parseFloat(trade.avg_entry_price || 0).toFixed(2)}
                                            </span>
                                        </td>
                                        <td style={{ textAlign: 'right', padding: '1rem 0.5rem' }}>
                                            <span style={{ fontWeight: '500' }}>
                                                ${parseFloat(trade.current_price || trade.last_price || 0).toFixed(2)}
                                            </span>
                                        </td>
                                        <td style={{ textAlign: 'right', padding: '1rem 0.5rem' }}>
                                            <span style={{ fontWeight: '500' }}>
                                                ${marketValue.toFixed(2)}
                                            </span>
                                        </td>
                                        <td style={{ textAlign: 'right', padding: '1rem 0.5rem' }}>
                                            <div style={{
                                                display: 'inline-flex',
                                                alignItems: 'center',
                                                gap: '0.25rem',
                                                color: isPositive ? 'var(--success)' : 'var(--danger)',
                                                fontWeight: '600'
                                            }}>
                                                {isPositive ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                                                ${Math.abs(pnl).toFixed(2)}
                                            </div>
                                        </td>
                                        <td style={{ textAlign: 'right', padding: '1rem 0.5rem' }}>
                                            <span style={{
                                                color: isPositive ? 'var(--success)' : 'var(--danger)',
                                                fontWeight: '600'
                                            }}>
                                                {isPositive ? '+' : ''}{pnlPercent.toFixed(2)}%
                                            </span>
                                        </td>
                                    </tr>
                                );
                            })
                        ) : (
                            <tr>
                                <td colSpan="7" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                                    No active positions
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default ActiveTrades;
