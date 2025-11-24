import React, { useState } from 'react';
import { Shield, AlertTriangle, Play, Square } from 'lucide-react';
import { botAPI } from '../services/api';

const StrategyControls = ({ status, onStatusChange }) => {
    const [riskLevel, setRiskLevel] = useState('Medium');
    const [stopLoss, setStopLoss] = useState(5);
    const [loading, setLoading] = useState(false);

    const isRunning = status === 'running';

    const handleToggleBot = async () => {
        setLoading(true);
        try {
            if (isRunning) {
                await botAPI.stop();
            } else {
                await botAPI.start();
            }
            // Status update will come via WebSocket or next poll
            if (onStatusChange) onStatusChange();
        } catch (error) {
            console.error('Failed to toggle bot:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="glass-card" style={{ padding: '1.5rem', gridColumn: 'span 1' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <h3 style={{ fontSize: '1.125rem', fontWeight: '600' }}>Strategy Controls</h3>
                <Shield size={20} color="var(--accent-secondary)" />
            </div>

            <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', color: 'var(--text-secondary)', marginBottom: '0.75rem', fontSize: '0.875rem' }}>Risk Level</label>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.5rem', background: 'rgba(255,255,255,0.05)', padding: '0.25rem', borderRadius: 'var(--radius-md)' }}>
                    {['Low', 'Medium', 'High'].map((level) => (
                        <button
                            key={level}
                            onClick={() => setRiskLevel(level)}
                            style={{
                                background: riskLevel === level ? 'var(--accent-secondary)' : 'transparent',
                                color: riskLevel === level ? 'white' : 'var(--text-muted)',
                                border: 'none',
                                padding: '0.5rem',
                                borderRadius: 'var(--radius-sm)',
                                fontSize: '0.75rem',
                                fontWeight: '500',
                                cursor: 'pointer',
                                transition: 'all 0.2s'
                            }}
                        >
                            {level}
                        </button>
                    ))}
                </div>
            </div>

            <div style={{ marginBottom: '2rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <label style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>Global Stop Loss</label>
                    <span style={{ color: 'var(--accent-primary)', fontWeight: '600', fontSize: '0.875rem' }}>{stopLoss}%</span>
                </div>
                <input
                    type="range"
                    min="1"
                    max="20"
                    value={stopLoss}
                    onChange={(e) => setStopLoss(e.target.value)}
                    style={{ width: '100%', accentColor: 'var(--accent-primary)' }}
                />
            </div>

            <div style={{ display: 'grid', gap: '1rem' }}>
                <button
                    className="btn-primary"
                    onClick={handleToggleBot}
                    disabled={loading}
                    style={{
                        width: '100%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '0.5rem',
                        background: isRunning
                            ? 'linear-gradient(135deg, var(--warning), #d97706)'
                            : 'linear-gradient(135deg, var(--success), #059669)'
                    }}
                >
                    {loading ? 'Processing...' : isRunning ? (
                        <>
                            <Square size={18} fill="currentColor" /> Stop Trading Agent
                        </>
                    ) : (
                        <>
                            <Play size={18} fill="currentColor" /> Start Trading Agent
                        </>
                    )}
                </button>

                <button
                    className="btn-glass"
                    style={{
                        width: '100%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '0.5rem',
                        color: 'var(--danger)',
                        borderColor: 'rgba(239, 68, 68, 0.3)'
                    }}
                >
                    <AlertTriangle size={18} />
                    Emergency Liquidate
                </button>
            </div>
        </div>
    );
};

export default StrategyControls;
