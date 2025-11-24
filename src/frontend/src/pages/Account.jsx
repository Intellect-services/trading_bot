import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { accountAPI } from '../services/api';
import { User, Shield, Key, Mail, Camera, Settings, CheckCircle, XCircle, AlertCircle } from 'lucide-react';

const Account = () => {
    const { user } = useAuth();
    const [activeTab, setActiveTab] = useState('profile');
    const [profileData, setProfileData] = useState({
        name: user?.name || ''
    });
    const [passwordData, setPasswordData] = useState({
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
    });
    const [message, setMessage] = useState(null);
    const [saving, setSaving] = useState(false);
    const [credentials, setCredentials] = useState(null);
    const [credentialsLoading, setCredentialsLoading] = useState(false);
    const [credentialsData, setCredentialsData] = useState({
        alpaca_api_key: '',
        alpaca_secret_key: '',
        trading_mode: 'paper'
    });
    const [testingConnection, setTestingConnection] = useState(false);

    const handleProfileSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        setMessage(null);

        try {
            const response = await accountAPI.updateProfile(profileData);
            if (response.data.status === 'success') {
                setMessage({ type: 'success', text: 'Profile updated successfully' });
                // Update will be reflected via AuthContext
            } else {
                setMessage({ type: 'error', text: response.data.message || 'Failed to update profile' });
            }
        } catch (err) {
            console.error('Error updating profile:', err);
            setMessage({ type: 'error', text: err.response?.data?.message || 'Failed to update profile' });
        } finally {
            setSaving(false);
        }
    };

    const handlePasswordSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        setMessage(null);

        // Validate passwords match
        if (passwordData.newPassword !== passwordData.confirmPassword) {
            setMessage({ type: 'error', text: 'New passwords do not match' });
            setSaving(false);
            return;
        }

        // Validate password length
        if (passwordData.newPassword.length < 6) {
            setMessage({ type: 'error', text: 'Password must be at least 6 characters' });
            setSaving(false);
            return;
        }

        try {
            const response = await accountAPI.updatePassword(
                passwordData.currentPassword,
                passwordData.newPassword
            );
            if (response.data.status === 'success') {
                setMessage({ type: 'success', text: 'Password updated successfully' });
                setPasswordData({
                    currentPassword: '',
                    newPassword: '',
                    confirmPassword: ''
                });
            } else {
                setMessage({ type: 'error', text: response.data.message || 'Failed to update password' });
            }
        } catch (err) {
            console.error('Error updating password:', err);
            setMessage({ type: 'error', text: err.response?.data?.message || 'Failed to update password' });
        } finally {
            setSaving(false);
        }
    };

    useEffect(() => {
        if (activeTab === 'credentials') {
            loadCredentials();
        }
    }, [activeTab]);

    const loadCredentials = async () => {
        setCredentialsLoading(true);
        try {
            const response = await accountAPI.getCredentials();
            if (response.data.status === 'success') {
                setCredentials(response.data.credentials);
                if (response.data.credentials) {
                    // Don't load actual keys for security, just show status
                    setCredentialsData({
                        alpaca_api_key: '',
                        alpaca_secret_key: '',
                        trading_mode: response.data.credentials.trading_mode || 'paper'
                    });
                }
            }
        } catch (err) {
            console.error('Error loading credentials:', err);
        } finally {
            setCredentialsLoading(false);
        }
    };

    const handleCredentialsSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        setMessage(null);

        if (!credentialsData.alpaca_api_key || !credentialsData.alpaca_secret_key) {
            setMessage({ type: 'error', text: 'API key and secret key are required' });
            setSaving(false);
            return;
        }

        try {
            const response = await accountAPI.saveCredentials(
                credentialsData.alpaca_api_key,
                credentialsData.alpaca_secret_key,
                credentialsData.trading_mode
            );
            if (response.data.status === 'success') {
                setMessage({ type: 'success', text: 'Credentials saved successfully' });
                setCredentials(response.data.credentials);
                // Clear the form fields for security
                setCredentialsData({
                    alpaca_api_key: '',
                    alpaca_secret_key: '',
                    trading_mode: response.data.credentials.trading_mode
                });
            } else {
                setMessage({ type: 'error', text: response.data.message || 'Failed to save credentials' });
            }
        } catch (err) {
            console.error('Error saving credentials:', err);
            setMessage({ type: 'error', text: err.response?.data?.message || 'Failed to save credentials' });
        } finally {
            setSaving(false);
        }
    };

    const handleTestConnection = async () => {
        setTestingConnection(true);
        setMessage(null);

        try {
            const response = await accountAPI.testCredentials(
                credentialsData.alpaca_api_key || undefined,
                credentialsData.alpaca_secret_key || undefined,
                credentialsData.trading_mode
            );
            if (response.data.status === 'success') {
                setMessage({
                    type: 'success',
                    text: `Connection successful! Account status: ${response.data.account_status}`
                });
                // Reload credentials to update verification status
                loadCredentials();
            } else {
                setMessage({ type: 'error', text: response.data.message || 'Connection test failed' });
            }
        } catch (err) {
            console.error('Error testing connection:', err);
            setMessage({ type: 'error', text: err.response?.data?.message || 'Connection test failed' });
        } finally {
            setTestingConnection(false);
        }
    };

    const handleDeleteCredentials = async () => {
        if (!window.confirm('Are you sure you want to delete your trading credentials? This will disable trading.')) {
            return;
        }

        setSaving(true);
        setMessage(null);

        try {
            const response = await accountAPI.deleteCredentials();
            if (response.data.status === 'success') {
                setMessage({ type: 'success', text: 'Credentials deleted successfully' });
                setCredentials(null);
                setCredentialsData({
                    alpaca_api_key: '',
                    alpaca_secret_key: '',
                    trading_mode: 'paper'
                });
            } else {
                setMessage({ type: 'error', text: response.data.message || 'Failed to delete credentials' });
            }
        } catch (err) {
            console.error('Error deleting credentials:', err);
            setMessage({ type: 'error', text: err.response?.data?.message || 'Failed to delete credentials' });
        } finally {
            setSaving(false);
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            style={{ maxWidth: '1000px', margin: '0 auto' }}
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
                    <User size={24} />
                </div>
                <div>
                    <h1 style={{ fontSize: '1.875rem', marginBottom: '0.25rem' }}>Account Settings</h1>
                    <p style={{ color: 'var(--text-secondary)' }}>Manage your profile and security preferences.</p>
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

            <div style={{ display: 'grid', gridTemplateColumns: '250px 1fr', gap: '2rem' }}>
                {/* Sidebar Navigation */}
                <div className="glass-card" style={{ padding: '1rem', height: 'fit-content' }}>
                    <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                        <button
                            onClick={() => {
                                setActiveTab('profile');
                                setMessage(null);
                            }}
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.75rem',
                                padding: '0.75rem 1rem',
                                borderRadius: 'var(--radius-md)',
                                background: activeTab === 'profile' ? 'rgba(99, 102, 241, 0.1)' : 'transparent',
                                color: activeTab === 'profile' ? 'var(--accent-primary)' : 'var(--text-secondary)',
                                border: 'none',
                                cursor: 'pointer',
                                textAlign: 'left',
                                transition: 'all 0.2s'
                            }}
                        >
                            <User size={18} />
                            Profile Information
                        </button>
                        <button
                            onClick={() => {
                                setActiveTab('security');
                                setMessage(null);
                            }}
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.75rem',
                                padding: '0.75rem 1rem',
                                borderRadius: 'var(--radius-md)',
                                background: activeTab === 'security' ? 'rgba(99, 102, 241, 0.1)' : 'transparent',
                                color: activeTab === 'security' ? 'var(--accent-primary)' : 'var(--text-secondary)',
                                border: 'none',
                                cursor: 'pointer',
                                textAlign: 'left',
                                transition: 'all 0.2s'
                            }}
                        >
                            <Shield size={18} />
                            Security
                        </button>
                        <button
                            onClick={() => {
                                setActiveTab('credentials');
                                setMessage(null);
                            }}
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.75rem',
                                padding: '0.75rem 1rem',
                                borderRadius: 'var(--radius-md)',
                                background: activeTab === 'credentials' ? 'rgba(99, 102, 241, 0.1)' : 'transparent',
                                color: activeTab === 'credentials' ? 'var(--accent-primary)' : 'var(--text-secondary)',
                                border: 'none',
                                cursor: 'pointer',
                                textAlign: 'left',
                                transition: 'all 0.2s'
                            }}
                        >
                            <Settings size={18} />
                            Trading Credentials
                        </button>
                    </nav>
                </div>

                {/* Content Area */}
                <div className="glass-card" style={{ padding: '2rem' }}>
                    {activeTab === 'profile' && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ duration: 0.3 }}
                        >
                            <h2 style={{ fontSize: '1.25rem', marginBottom: '1.5rem', borderBottom: '1px solid var(--glass-border)', paddingBottom: '1rem' }}>Profile Information</h2>

                            <div style={{ display: 'flex', alignItems: 'center', gap: '2rem', marginBottom: '2rem' }}>
                                <div style={{ position: 'relative' }}>
                                    <div style={{
                                        width: '100px',
                                        height: '100px',
                                        borderRadius: '50%',
                                        background: 'var(--accent-primary)',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        fontSize: '2.5rem',
                                        fontWeight: '600',
                                        color: 'white',
                                        border: '4px solid var(--glass-border)'
                                    }}>
                                        {user?.avatar ? (
                                            <img src={user.avatar} alt={user.name} style={{ width: '100%', height: '100%', borderRadius: '50%', objectFit: 'cover' }} />
                                        ) : (
                                            user?.name?.[0] || 'U'
                                        )}
                                    </div>
                                    <button style={{
                                        position: 'absolute',
                                        bottom: '0',
                                        right: '0',
                                        background: 'var(--bg-card)',
                                        border: '1px solid var(--glass-border)',
                                        borderRadius: '50%',
                                        width: '32px',
                                        height: '32px',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        cursor: 'pointer',
                                        color: 'var(--text-primary)'
                                    }}>
                                        <Camera size={14} />
                                    </button>
                                </div>
                                <div>
                                    <h3 style={{ fontSize: '1.25rem', marginBottom: '0.25rem' }}>{user?.name || 'User'}</h3>
                                    <p style={{ color: 'var(--text-secondary)' }}>Pro Trader</p>
                                </div>
                            </div>

                            <form onSubmit={handleProfileSubmit}>
                                <div style={{ display: 'grid', gap: '1.5rem' }}>
                                    <div>
                                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Full Name</label>
                                        <div style={{ position: 'relative' }}>
                                            <User size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                                            <input
                                                type="text"
                                                value={profileData.name}
                                                onChange={(e) => setProfileData({ ...profileData, name: e.target.value })}
                                                style={{
                                                    width: '100%',
                                                    padding: '0.75rem 1rem 0.75rem 2.75rem',
                                                    background: 'rgba(255, 255, 255, 0.05)',
                                                    border: '1px solid var(--glass-border)',
                                                    borderRadius: 'var(--radius-md)',
                                                    color: 'white',
                                                    outline: 'none'
                                                }}
                                            />
                                        </div>
                                    </div>

                                    <div>
                                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Email Address</label>
                                        <div style={{ position: 'relative' }}>
                                            <Mail size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                                            <input
                                                type="email"
                                                value={user?.email}
                                                disabled
                                                style={{
                                                    width: '100%',
                                                    padding: '0.75rem 1rem 0.75rem 2.75rem',
                                                    background: 'rgba(255, 255, 255, 0.02)',
                                                    border: '1px solid var(--glass-border)',
                                                    borderRadius: 'var(--radius-md)',
                                                    color: 'var(--text-muted)',
                                                    outline: 'none',
                                                    cursor: 'not-allowed'
                                                }}
                                            />
                                        </div>
                                    </div>

                                    <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1rem' }}>
                                        <button
                                            type="submit"
                                            className="btn-primary"
                                            disabled={saving}
                                        >
                                            {saving ? 'Saving...' : 'Save Changes'}
                                        </button>
                                    </div>
                                </div>
                            </form>
                        </motion.div>
                    )}

                    {activeTab === 'security' && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ duration: 0.3 }}
                        >
                            <h2 style={{ fontSize: '1.25rem', marginBottom: '1.5rem', borderBottom: '1px solid var(--glass-border)', paddingBottom: '1rem' }}>Security Settings</h2>

                            <form onSubmit={handlePasswordSubmit}>
                                <div style={{ display: 'grid', gap: '1.5rem' }}>
                                    <div>
                                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Current Password</label>
                                        <div style={{ position: 'relative' }}>
                                            <Key size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                                            <input
                                                type="password"
                                                placeholder="Enter current password"
                                                value={passwordData.currentPassword}
                                                onChange={(e) => setPasswordData({ ...passwordData, currentPassword: e.target.value })}
                                                style={{
                                                    width: '100%',
                                                    padding: '0.75rem 1rem 0.75rem 2.75rem',
                                                    background: 'rgba(255, 255, 255, 0.05)',
                                                    border: '1px solid var(--glass-border)',
                                                    borderRadius: 'var(--radius-md)',
                                                    color: 'white',
                                                    outline: 'none'
                                                }}
                                            />
                                        </div>
                                    </div>

                                    <div>
                                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>New Password</label>
                                        <div style={{ position: 'relative' }}>
                                            <Key size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                                            <input
                                                type="password"
                                                placeholder="Enter new password"
                                                value={passwordData.newPassword}
                                                onChange={(e) => setPasswordData({ ...passwordData, newPassword: e.target.value })}
                                                style={{
                                                    width: '100%',
                                                    padding: '0.75rem 1rem 0.75rem 2.75rem',
                                                    background: 'rgba(255, 255, 255, 0.05)',
                                                    border: '1px solid var(--glass-border)',
                                                    borderRadius: 'var(--radius-md)',
                                                    color: 'white',
                                                    outline: 'none'
                                                }}
                                            />
                                        </div>
                                    </div>

                                    <div>
                                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Confirm New Password</label>
                                        <div style={{ position: 'relative' }}>
                                            <Key size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                                            <input
                                                type="password"
                                                placeholder="Confirm new password"
                                                value={passwordData.confirmPassword}
                                                onChange={(e) => setPasswordData({ ...passwordData, confirmPassword: e.target.value })}
                                                style={{
                                                    width: '100%',
                                                    padding: '0.75rem 1rem 0.75rem 2.75rem',
                                                    background: 'rgba(255, 255, 255, 0.05)',
                                                    border: '1px solid var(--glass-border)',
                                                    borderRadius: 'var(--radius-md)',
                                                    color: 'white',
                                                    outline: 'none'
                                                }}
                                            />
                                        </div>
                                    </div>

                                    <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1rem' }}>
                                        <button
                                            type="submit"
                                            className="btn-primary"
                                            disabled={saving}
                                        >
                                            {saving ? 'Updating...' : 'Update Password'}
                                        </button>
                                    </div>
                                </div>
                            </form>
                        </motion.div>
                    )}

                    {activeTab === 'credentials' && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ duration: 0.3 }}
                        >
                            <h2 style={{ fontSize: '1.25rem', marginBottom: '1.5rem', borderBottom: '1px solid var(--glass-border)', paddingBottom: '1rem' }}>Trading Credentials</h2>

                            {credentialsLoading ? (
                                <p style={{ color: 'var(--text-secondary)' }}>Loading credentials...</p>
                            ) : credentials ? (
                                <div style={{ marginBottom: '2rem', padding: '1rem', background: 'rgba(16, 185, 129, 0.1)', borderRadius: 'var(--radius-md)', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                                        {credentials.is_active ? (
                                            <CheckCircle size={20} color="var(--success)" />
                                        ) : (
                                            <AlertCircle size={20} color="var(--warning)" />
                                        )}
                                        <strong style={{ color: credentials.is_active ? 'var(--success)' : 'var(--warning)' }}>
                                            {credentials.is_active ? 'Credentials Configured & Verified' : 'Credentials Configured (Not Verified)'}
                                        </strong>
                                    </div>
                                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '0.5rem' }}>
                                        Trading Mode: <strong>{credentials.trading_mode === 'paper' ? 'Paper Trading' : 'Live Trading'}</strong>
                                    </p>
                                    {credentials.last_verified_at && (
                                        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                                            Last verified: {new Date(credentials.last_verified_at).toLocaleString()}
                                        </p>
                                    )}
                                    {!credentials.is_active && (
                                        <p style={{ color: 'var(--warning)', fontSize: '0.875rem', marginTop: '0.5rem' }}>
                                            Please test your connection to verify your credentials.
                                        </p>
                                    )}
                                </div>
                            ) : (
                                <div style={{ marginBottom: '2rem', padding: '1rem', background: 'rgba(239, 68, 68, 0.1)', borderRadius: 'var(--radius-md)', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                                        <XCircle size={20} color="var(--danger)" />
                                        <strong style={{ color: 'var(--danger)' }}>No Credentials Configured</strong>
                                    </div>
                                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                                        Configure your Alpaca API credentials to enable automated trading.
                                    </p>
                                </div>
                            )}

                            <form onSubmit={handleCredentialsSubmit}>
                                <div style={{ display: 'grid', gap: '1.5rem' }}>
                                    <div>
                                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Alpaca API Key</label>
                                        <div style={{ position: 'relative' }}>
                                            <Key size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                                            <input
                                                type="password"
                                                placeholder={credentials ? "Enter new API key to update" : "Enter your Alpaca API key"}
                                                value={credentialsData.alpaca_api_key}
                                                onChange={(e) => setCredentialsData({ ...credentialsData, alpaca_api_key: e.target.value })}
                                                style={{
                                                    width: '100%',
                                                    padding: '0.75rem 1rem 0.75rem 2.75rem',
                                                    background: 'rgba(255, 255, 255, 0.05)',
                                                    border: '1px solid var(--glass-border)',
                                                    borderRadius: 'var(--radius-md)',
                                                    color: 'white',
                                                    outline: 'none'
                                                }}
                                            />
                                        </div>
                                    </div>

                                    <div>
                                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Alpaca Secret Key</label>
                                        <div style={{ position: 'relative' }}>
                                            <Key size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                                            <input
                                                type="password"
                                                placeholder={credentials ? "Enter new secret key to update" : "Enter your Alpaca secret key"}
                                                value={credentialsData.alpaca_secret_key}
                                                onChange={(e) => setCredentialsData({ ...credentialsData, alpaca_secret_key: e.target.value })}
                                                style={{
                                                    width: '100%',
                                                    padding: '0.75rem 1rem 0.75rem 2.75rem',
                                                    background: 'rgba(255, 255, 255, 0.05)',
                                                    border: '1px solid var(--glass-border)',
                                                    borderRadius: 'var(--radius-md)',
                                                    color: 'white',
                                                    outline: 'none'
                                                }}
                                            />
                                        </div>
                                    </div>

                                    <div>
                                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Trading Mode</label>
                                        <div style={{ display: 'flex', gap: '1rem' }}>
                                            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                                                <input
                                                    type="radio"
                                                    name="trading_mode"
                                                    value="paper"
                                                    checked={credentialsData.trading_mode === 'paper'}
                                                    onChange={(e) => setCredentialsData({ ...credentialsData, trading_mode: e.target.value })}
                                                    style={{ cursor: 'pointer' }}
                                                />
                                                <span>Paper Trading</span>
                                            </label>
                                            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                                                <input
                                                    type="radio"
                                                    name="trading_mode"
                                                    value="live"
                                                    checked={credentialsData.trading_mode === 'live'}
                                                    onChange={(e) => setCredentialsData({ ...credentialsData, trading_mode: e.target.value })}
                                                    style={{ cursor: 'pointer' }}
                                                />
                                                <span>Live Trading</span>
                                            </label>
                                        </div>
                                    </div>

                                    <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end', marginTop: '1rem' }}>
                                        {credentials && (
                                            <button
                                                type="button"
                                                onClick={handleDeleteCredentials}
                                                className="btn-secondary"
                                                disabled={saving}
                                                style={{ background: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', border: '1px solid rgba(239, 68, 68, 0.2)' }}
                                            >
                                                Delete Credentials
                                            </button>
                                        )}
                                        <button
                                            type="button"
                                            onClick={handleTestConnection}
                                            className="btn-secondary"
                                            disabled={testingConnection || (!credentialsData.alpaca_api_key && !credentials)}
                                        >
                                            {testingConnection ? 'Testing...' : 'Test Connection'}
                                        </button>
                                        <button
                                            type="submit"
                                            className="btn-primary"
                                            disabled={saving}
                                        >
                                            {saving ? 'Saving...' : credentials ? 'Update Credentials' : 'Save Credentials'}
                                        </button>
                                    </div>
                                </div>
                            </form>
                        </motion.div>
                    )}
                </div>
            </div>
        </motion.div>
    );
};

export default Account;
