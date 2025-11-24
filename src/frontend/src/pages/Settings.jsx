import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { botAPI } from '../services/api';
import { Settings as SettingsIcon, Save, RefreshCw } from 'lucide-react';

const Settings = () => {
    const [settings, setSettings] = useState({
        trading_symbols: [],
        trading_stop_loss: 0.02,
        risk_max_drawdown: 0.1,
        trading_mode: 'paper'
    });
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState(null);

    useEffect(() => {
        fetchSettings();
    }, []);

    const fetchSettings = async () => {
        try {
            const response = await botAPI.getSettings();
            if (response.data.status === 'success') {
                setSettings(response.data.settings);
            }
        } catch (err) {
            console.error('Error fetching settings:', err);
            setMessage({ type: 'error', text: 'Failed to load settings' });
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        setMessage(null);

        try {
            const response = await botAPI.updateSettings(settings);
            if (response.data.status === 'success') {
                setMessage({ type: 'success', text: 'Settings saved successfully' });
                setSettings(response.data.settings);
            } else {
                setMessage({ type: 'error', text: response.data.message || 'Failed to save settings' });
            }
        } catch (err) {
            console.error('Error saving settings:', err);
            setMessage({ type: 'error', text: 'Failed to save settings' });
        } finally {
            setSaving(false);
        }
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setSettings(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSymbolsChange = (e) => {
        setSettings(prev => ({
            ...prev,
            trading_symbols: e.target.value.split(',').map(s => s.trim())
        }));
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
            style={{ maxWidth: '800px', margin: '0 auto' }}
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
                    <SettingsIcon size={24} />
                </div>
                <div>
                    <h1 style={{ fontSize: '1.875rem', marginBottom: '0.25rem' }}>Settings</h1>
                    <p style={{ color: 'var(--text-secondary)' }}>Configure your trading bot parameters.</p>
                </div>
            </div>

            {message && (
                <div style={{
                    padding: '1rem',
                    borderRadius: 'var(--radius-md)',
                    marginBottom: '1.5rem',
                    background: message.type === 'success' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                    color: message.type === 'success' ? 'var(--success)' : 'var(--danger)',
                    border: `1px solid ${message.type === 'success' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)'}`
                }}>
                    {message.text}
                </div>
            )}

            <form onSubmit={handleSubmit}>
                <div className="glass-card" style={{ padding: '2rem', marginBottom: '2rem' }}>
                    <h2 style={{ fontSize: '1.25rem', marginBottom: '1.5rem', borderBottom: '1px solid var(--glass-border)', paddingBottom: '1rem' }}>Trading Configuration</h2>

                    <div style={{ marginBottom: '1.5rem' }}>
                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Trading Symbols</label>
                        <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>Comma separated list of symbols to trade (e.g. AAPL, MSFT, GOOGL)</p>
                        <input
                            type="text"
                            value={settings.trading_symbols.join(', ')}
                            onChange={handleSymbolsChange}
                            style={{
                                width: '100%',
                                padding: '0.75rem',
                                background: 'rgba(255, 255, 255, 0.05)',
                                border: '1px solid var(--glass-border)',
                                borderRadius: 'var(--radius-md)',
                                color: 'white',
                                outline: 'none'
                            }}
                        />
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                        <div>
                            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Stop Loss</label>
                            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>Decimal value (e.g. 0.02 for 2%)</p>
                            <input
                                type="number"
                                step="0.01"
                                name="trading_stop_loss"
                                value={settings.trading_stop_loss}
                                onChange={handleChange}
                                style={{
                                    width: '100%',
                                    padding: '0.75rem',
                                    background: 'rgba(255, 255, 255, 0.05)',
                                    border: '1px solid var(--glass-border)',
                                    borderRadius: 'var(--radius-md)',
                                    color: 'white',
                                    outline: 'none'
                                }}
                            />
                        </div>
                        <div>
                            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Max Drawdown</label>
                            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>Decimal value (e.g. 0.10 for 10%)</p>
                            <input
                                type="number"
                                step="0.01"
                                name="risk_max_drawdown"
                                value={settings.risk_max_drawdown}
                                onChange={handleChange}
                                style={{
                                    width: '100%',
                                    padding: '0.75rem',
                                    background: 'rgba(255, 255, 255, 0.05)',
                                    border: '1px solid var(--glass-border)',
                                    borderRadius: 'var(--radius-md)',
                                    color: 'white',
                                    outline: 'none'
                                }}
                            />
                        </div>
                    </div>

                    <div style={{ marginTop: '1.5rem' }}>
                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Trading Mode</label>
                        <div style={{ display: 'flex', gap: '1rem' }}>
                            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                                <input
                                    type="radio"
                                    name="trading_mode"
                                    value="paper"
                                    checked={settings.trading_mode === 'paper'}
                                    onChange={handleChange}
                                />
                                Paper Trading
                            </label>
                            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                                <input
                                    type="radio"
                                    name="trading_mode"
                                    value="live"
                                    checked={settings.trading_mode === 'live'}
                                    onChange={handleChange}
                                />
                                Live Trading
                            </label>
                        </div>
                    </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
                    <button
                        type="button"
                        onClick={fetchSettings}
                        className="btn-glass"
                        style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                    >
                        <RefreshCw size={18} /> Reset
                    </button>
                    <button
                        type="submit"
                        className="btn-primary"
                        disabled={saving}
                        style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                    >
                        {saving ? 'Saving...' : <><Save size={18} /> Save Changes</>}
                    </button>
                </div>
            </form>
        </motion.div>
    );
};

export default Settings;
