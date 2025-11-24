import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Mail, ArrowLeft, TrendingUp, CheckCircle, AlertCircle } from 'lucide-react';
import { authAPI } from '../services/api';
import './Login.css';

const ForgotPassword = () => {
    const [email, setEmail] = useState('');
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess(false);

        if (!email.trim()) {
            setError('Please enter your email address');
            return;
        }

        setLoading(true);
        try {
            const response = await authAPI.forgotPassword(email);
            if (response.data.status === 'success') {
                setSuccess(true);
            } else {
                setError(response.data.message || 'Failed to send password reset email');
            }
        } catch (err) {
            setError(err.response?.data?.message || 'Failed to send password reset email');
        } finally {
            setLoading(false);
        }
    };

    return (
        <>
            {/* Sticky Header */}
            <header className="auth-page-header">
                <div className="auth-header-content">
                    <Link to="/" className="auth-logo">
                        <TrendingUp size={24} />
                        <span>IntellectScout</span>
                    </Link>
                </div>
            </header>

            <div className="login-container">
                {/* Background Elements */}
                <div className="login-background">
                    <div className="gradient-orb orb-1"></div>
                    <div className="gradient-orb orb-2"></div>
                    <div className="grid-pattern"></div>
                </div>

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, ease: 'easeOut' }}
                    className="login-card"
                    style={{ maxWidth: '480px' }}
                >
                    {/* Brand Header */}
                    <div className="login-header">
                        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.75rem' }}>
                            <TrendingUp size={48} style={{ color: '#a78bfa' }} />
                            <span style={{
                                fontSize: '2rem',
                                fontWeight: '700',
                                color: '#f9fafb',
                                textShadow: '0 2px 8px rgba(102, 126, 234, 0.3)',
                                letterSpacing: '-0.02em'
                            }}>
                                IntellectScout
                            </span>
                        </div>
                    </div>

                    {/* Welcome Section */}
                    <div className="welcome-section">
                        <h2>Reset Password</h2>
                        <p>Enter your email address and we'll send you a link to reset your password</p>
                    </div>

                    {/* Success Message */}
                    {success && (
                        <motion.div
                            initial={{ opacity: 0, y: -10 }}
                            animate={{ opacity: 1, y: 0 }}
                            style={{
                                padding: '1.5rem',
                                borderRadius: 'var(--radius-md)',
                                background: 'rgba(34, 197, 94, 0.1)',
                                border: '1px solid rgba(34, 197, 94, 0.3)',
                                marginBottom: '1.5rem',
                                display: 'flex',
                                flexDirection: 'column',
                                gap: '1rem'
                            }}
                        >
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                <CheckCircle size={24} style={{ color: '#22c55e' }} />
                                <h3 style={{
                                    color: '#22c55e',
                                    fontSize: '1rem',
                                    fontWeight: '600',
                                    margin: 0
                                }}>
                                    Email Sent!
                                </h3>
                            </div>
                            <p style={{
                                color: 'var(--text-secondary)',
                                fontSize: '0.875rem',
                                margin: 0,
                                lineHeight: '1.6'
                            }}>
                                If an account exists with this email, a password reset link has been sent.
                                Please check your inbox and spam folder.
                            </p>
                            <div style={{
                                background: 'rgba(255, 255, 255, 0.05)',
                                border: '1px solid rgba(255, 255, 255, 0.1)',
                                borderRadius: 'var(--radius-sm)',
                                padding: '1rem',
                                marginTop: '0.5rem'
                            }}>
                                <p style={{
                                    color: 'var(--text-secondary)',
                                    fontSize: '0.75rem',
                                    margin: 0,
                                    lineHeight: '1.6'
                                }}>
                                    <strong style={{ color: 'var(--text-primary)' }}>Note:</strong> The reset link will expire in 1 hour.
                                    If you didn't request a password reset, you can safely ignore this email.
                                </p>
                            </div>
                        </motion.div>
                    )}

                    {/* Error Message */}
                    {error && !success && (
                        <motion.div
                            initial={{ opacity: 0, y: -10 }}
                            animate={{ opacity: 1, y: 0 }}
                            style={{
                                padding: '1rem',
                                borderRadius: 'var(--radius-md)',
                                background: 'rgba(239, 68, 68, 0.1)',
                                border: '1px solid rgba(239, 68, 68, 0.3)',
                                marginBottom: '1.5rem',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.75rem'
                            }}
                        >
                            <AlertCircle size={20} style={{ color: '#ef4444' }} />
                            <span style={{ color: '#ef4444', fontSize: '0.875rem' }}>{error}</span>
                        </motion.div>
                    )}

                    {/* Form */}
                    {!success && (
                        <form onSubmit={handleSubmit} className="login-form">
                            <div className="form-group">
                                <label htmlFor="email">Email Address</label>
                                <div className="input-wrapper">
                                    <Mail size={18} className="input-icon" />
                                    <input
                                        id="email"
                                        type="email"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        required
                                        placeholder="you@example.com"
                                        className="form-input"
                                        disabled={loading}
                                    />
                                </div>
                            </div>

                            <button
                                type="submit"
                                className="btn-submit"
                                disabled={loading}
                            >
                                {loading ? (
                                    <span className="loading-text">Sending...</span>
                                ) : (
                                    <>
                                        <span>Send Reset Link</span>
                                        <Mail size={18} />
                                    </>
                                )}
                            </button>
                        </form>
                    )}

                    {/* Back to Login */}
                    <div style={{
                        textAlign: 'center',
                        marginTop: '2rem',
                        paddingTop: '1.5rem',
                        borderTop: '1px solid rgba(255, 255, 255, 0.1)'
                    }}>
                        <Link
                            to="/login"
                            style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '0.5rem',
                                color: 'var(--accent-primary)',
                                textDecoration: 'none',
                                fontWeight: '600',
                                fontSize: '0.875rem',
                                transition: 'color var(--transition-fast)'
                            }}
                            onMouseEnter={(e) => e.target.style.color = 'var(--accent-secondary)'}
                            onMouseLeave={(e) => e.target.style.color = 'var(--accent-primary)'}
                        >
                            <ArrowLeft size={16} />
                            <span>Back to Sign In</span>
                        </Link>
                    </div>
                </motion.div>
            </div>

            {/* Sticky Footer */}
            <footer className="auth-page-footer">
                <p>© 2024 IntellectScout. All rights reserved.</p>
            </footer>
        </>
    );
};

export default ForgotPassword;
