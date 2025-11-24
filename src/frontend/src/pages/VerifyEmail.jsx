import React, { useState } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Mail, CheckCircle, ArrowRight, TrendingUp, RefreshCw } from 'lucide-react';
import { authAPI } from '../services/api';
import './Login.css';

const VerifyEmail = () => {
    const [searchParams] = useSearchParams();
    const email = searchParams.get('email') || '';
    const [resending, setResending] = useState(false);
    const [resendSuccess, setResendSuccess] = useState(false);
    const [resendError, setResendError] = useState('');
    const navigate = useNavigate();

    const handleResend = async () => {
        if (!email) return;

        setResending(true);
        setResendError('');
        setResendSuccess(false);

        try {
            const response = await authAPI.resendVerification(email);
            if (response.data.status === 'success') {
                setResendSuccess(true);
                setTimeout(() => setResendSuccess(false), 5000);
            } else {
                setResendError(response.data.message || 'Failed to resend verification email');
            }
        } catch (err) {
            setResendError(err.response?.data?.message || 'Failed to resend verification email');
        } finally {
            setResending(false);
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
                    style={{ maxWidth: '500px' }}
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

                    {/* Icon */}
                    <div style={{
                        display: 'flex',
                        justifyContent: 'center',
                        marginBottom: '2rem',
                        marginTop: '1rem'
                    }}>
                        <div style={{
                            width: '80px',
                            height: '80px',
                            borderRadius: '50%',
                            background: 'rgba(34, 197, 94, 0.1)',
                            border: '2px solid rgba(34, 197, 94, 0.3)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center'
                        }}>
                            <Mail size={40} style={{ color: '#22c55e' }} />
                        </div>
                    </div>

                    {/* Title */}
                    <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
                        <h2 style={{
                            fontSize: '1.75rem',
                            fontWeight: '700',
                            marginBottom: '0.5rem',
                            color: 'var(--text-primary)'
                        }}>
                            Check Your Email
                        </h2>
                        <p style={{
                            color: 'var(--text-secondary)',
                            fontSize: '1rem',
                            lineHeight: '1.6'
                        }}>
                            We've sent a verification link to
                        </p>
                        {email && (
                            <p style={{
                                color: 'var(--accent-primary)',
                                fontSize: '1rem',
                                fontWeight: '600',
                                marginTop: '0.5rem',
                                wordBreak: 'break-all'
                            }}>
                                {email}
                            </p>
                        )}
                    </div>

                    {/* Instructions */}
                    <div style={{
                        background: 'rgba(255, 255, 255, 0.05)',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                        borderRadius: 'var(--radius-md)',
                        padding: '1.5rem',
                        marginBottom: '1.5rem'
                    }}>
                        <div style={{
                            color: 'var(--text-secondary)',
                            fontSize: '0.875rem',
                            lineHeight: '1.8'
                        }}>
                            <p style={{ marginBottom: '0.75rem' }}>
                                <strong style={{ color: 'var(--text-primary)' }}>Next steps:</strong>
                            </p>
                            <ol style={{
                                paddingLeft: '1.25rem',
                                margin: 0,
                                display: 'flex',
                                flexDirection: 'column',
                                gap: '0.5rem'
                            }}>
                                <li>Check your inbox (and spam folder)</li>
                                <li>Click the verification link in the email</li>
                                <li>Return here to sign in</li>
                            </ol>
                        </div>
                    </div>

                    {/* Resend Email Section */}
                    <div style={{ marginBottom: '1.5rem' }}>
                        <p style={{
                            color: 'var(--text-secondary)',
                            fontSize: '0.875rem',
                            textAlign: 'center',
                            marginBottom: '1rem'
                        }}>
                            Didn't receive the email?
                        </p>

                        {resendSuccess && (
                            <motion.div
                                initial={{ opacity: 0, y: -10 }}
                                animate={{ opacity: 1, y: 0 }}
                                style={{
                                    padding: '0.75rem',
                                    borderRadius: 'var(--radius-md)',
                                    background: 'rgba(34, 197, 94, 0.1)',
                                    border: '1px solid rgba(34, 197, 94, 0.3)',
                                    color: '#22c55e',
                                    fontSize: '0.875rem',
                                    textAlign: 'center',
                                    marginBottom: '1rem',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    gap: '0.5rem'
                                }}
                            >
                                <CheckCircle size={16} />
                                <span>Verification email sent!</span>
                            </motion.div>
                        )}

                        {resendError && (
                            <motion.div
                                initial={{ opacity: 0, y: -10 }}
                                animate={{ opacity: 1, y: 0 }}
                                style={{
                                    padding: '0.75rem',
                                    borderRadius: 'var(--radius-md)',
                                    background: 'rgba(239, 68, 68, 0.1)',
                                    border: '1px solid rgba(239, 68, 68, 0.3)',
                                    color: '#ef4444',
                                    fontSize: '0.875rem',
                                    textAlign: 'center',
                                    marginBottom: '1rem'
                                }}
                            >
                                {resendError}
                            </motion.div>
                        )}

                        <button
                            onClick={handleResend}
                            disabled={resending || !email}
                            style={{
                                width: '100%',
                                padding: '0.875rem',
                                background: resending || !email
                                    ? 'rgba(255, 255, 255, 0.05)'
                                    : 'rgba(255, 255, 255, 0.1)',
                                border: '1px solid rgba(255, 255, 255, 0.2)',
                                borderRadius: 'var(--radius-md)',
                                color: resending || !email
                                    ? 'var(--text-muted)'
                                    : 'var(--text-primary)',
                                fontSize: '0.875rem',
                                fontWeight: '500',
                                cursor: resending || !email ? 'not-allowed' : 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '0.5rem',
                                transition: 'all var(--transition-base)'
                            }}
                            onMouseEnter={(e) => {
                                if (!resending && email) {
                                    e.target.style.background = 'rgba(255, 255, 255, 0.15)';
                                }
                            }}
                            onMouseLeave={(e) => {
                                if (!resending && email) {
                                    e.target.style.background = 'rgba(255, 255, 255, 0.1)';
                                }
                            }}
                        >
                            {resending ? (
                                <>
                                    <RefreshCw size={16} style={{ animation: 'spin 1s linear infinite' }} />
                                    <span>Sending...</span>
                                </>
                            ) : (
                                <>
                                    <RefreshCw size={16} />
                                    <span>Resend Verification Email</span>
                                </>
                            )}
                        </button>
                    </div>

                    {/* Back to Login */}
                    <div style={{
                        textAlign: 'center',
                        paddingTop: '1.5rem',
                        borderTop: '1px solid rgba(255, 255, 255, 0.1)'
                    }}>
                        <p style={{
                            color: 'var(--text-secondary)',
                            fontSize: '0.875rem',
                            marginBottom: '1rem'
                        }}>
                            Already verified your email?
                        </p>
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
                            <span>Go to Sign In</span>
                            <ArrowRight size={16} />
                        </Link>
                    </div>
                </motion.div>
            </div>

            {/* Sticky Footer */}
            <footer className="auth-page-footer">
                <p>© 2024 IntellectScout. All rights reserved.</p>
            </footer>

            <style>{`
                @keyframes spin {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
            `}</style>
        </>
    );
};

export default VerifyEmail;
