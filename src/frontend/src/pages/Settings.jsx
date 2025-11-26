import React, { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { botAPI, emailAPI } from '../services/api';
import { Settings as SettingsIcon, Save, RefreshCw, Mail, Shield } from 'lucide-react';

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
    const [preferences, setPreferences] = useState(null);
    const [prefLoading, setPrefLoading] = useState(true);
    const [prefSaving, setPrefSaving] = useState(false);
    const [prefMessage, setPrefMessage] = useState(null);

    useEffect(() => {
        fetchSettings();
        fetchPreferences();
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

    const fetchPreferences = async () => {
        setPrefLoading(true);
        try {
            const response = await emailAPI.getPreferences();
            if (response.data.status === 'success') {
                setPreferences(response.data.data);
            }
        } catch (error) {
            console.error('Failed to load email preferences', error);
            setPrefMessage({ type: 'error', text: 'Unable to load email preferences' });
        } finally {
            setPrefLoading(false);
        }
    };

    const handlePreferenceToggle = async () => {
        if (!preferences) {
            return;
        }
        setPrefSaving(true);
        setPrefMessage(null);
        try {
            const response = await emailAPI.updatePreferences({
                marketing_opt_in: !preferences.marketing_opt_in
            });
            if (response.data.status === 'success') {
                setPreferences(response.data.data);
                setPrefMessage({
                    type: 'success',
                    text: response.data.data.marketing_opt_in
                        ? 'Marketing emails enabled'
                        : 'Marketing emails disabled'
                });
            } else {
                setPrefMessage({
                    type: 'error',
                    text: response.data.message || 'Unable to update preference'
                });
            }
        } catch (error) {
            console.error('Failed to update preference', error);
            setPrefMessage({ type: 'error', text: 'Unable to update preference' });
        } finally {
            setPrefSaving(false);
        }
    };

    const lastSendLabel = useMemo(() => {
        if (!preferences?.last_sent_at) {
            return 'No marketing emails sent yet';
        }
        const formatted = new Date(preferences.last_sent_at).toLocaleString();
        return `Last campaign received on ${formatted}`;
    }, [preferences]);

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

                <div className="glass-card" style={{ padding: '2rem', marginBottom: '2rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                        <div style={{ width: 40, height: 40, borderRadius: '50%', background: 'rgba(99, 102, 241, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <Mail size={20} color="var(--accent-primary)" />
                        </div>
                        <div>
                            <h2 style={{ fontSize: '1.25rem', margin: 0 }}>Email Preferences</h2>
                            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Control branded marketing communications.</p>
                        </div>
                    </div>

                    {prefMessage && (
                        <div style={{
                            padding: '0.75rem 1rem',
                            borderRadius: 'var(--radius-md)',
                            marginBottom: '1.5rem',
                            background: prefMessage.type === 'success' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                            color: prefMessage.type === 'success' ? 'var(--success)' : 'var(--danger)',
                            border: `1px solid ${prefMessage.type === 'success' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)'}`
                        }}>
                            {prefMessage.text}
                        </div>
                    )}

                    {prefLoading ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', color: 'var(--text-muted)' }}>
                            <div style={{ width: '28px', height: '28px', border: '3px solid rgba(99, 102, 241, 0.2)', borderTopColor: 'var(--accent-primary)', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
                            Loading email preferences...
                            <style>{`
                                @keyframes spin {
                                    to { transform: rotate(360deg); }
                                }
                            `}</style>
                        </div>
                    ) : (
                        <>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
                                <div>
                                    <p style={{ margin: 0, fontWeight: 600 }}>Branded marketing updates</p>
                                    <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                                        Receive onboarding guides, product drops, and market briefings.
                                    </p>
                                </div>
                                <button
                                    type="button"
                                    onClick={handlePreferenceToggle}
                                    className={preferences?.marketing_opt_in ? 'btn-primary' : 'btn-glass'}
                                    disabled={prefSaving}
                                    style={{ minWidth: '180px' }}
                                >
                                    {prefSaving
                                        ? 'Updating...'
                                        : preferences?.marketing_opt_in
                                            ? 'Disable emails'
                                            : 'Enable emails'}
                                </button>
                            </div>
                            <div style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.6rem',
                                padding: '0.9rem 1rem',
                                borderRadius: 'var(--radius-md)',
                                background: 'rgba(255,255,255,0.03)',
                                border: '1px solid var(--glass-border)'
                            }}>
                                <Shield size={18} color="var(--text-muted)" />
                                <div>
                                    <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                                        {lastSendLabel}
                                    </p>
                                    <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                                        Use the unsubscribe links inside every campaign to opt out instantly.
                                    </p>
                                </div>
                            </div>
                        </>
                    )}
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
