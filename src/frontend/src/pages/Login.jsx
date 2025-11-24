import React, { useState, useEffect } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { motion } from 'framer-motion';
import { Binoculars, Lock, Mail, ArrowRight, TrendingUp, CheckCircle } from 'lucide-react';
import './Login.css';

const Login = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();

    useEffect(() => {
        // Check for verification success
        if (searchParams.get('verified') === 'true') {
            setSuccess('Email verified successfully! You can now sign in.');
        }
        // Check for password reset success
        if (searchParams.get('password_reset') === 'true') {
            setSuccess('Password reset successfully! Please sign in with your new password.');
        }
    }, [searchParams]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        try {
            const result = await login(email, password);
            if (result.success) {
                navigate('/');
            } else {
                setError(result.error);
            }
        } catch (err) {
            setError('Failed to login');
        } finally {
            setIsLoading(false);
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

                {/* Welcome Message */}
                <div className="welcome-section">
                    <h2>Welcome Back</h2>
                    <p>Sign in to continue your trading journey</p>
                </div>

                {/* Success Message */}
                {success && (
                    <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="success-message"
                        style={{
                            background: 'rgba(34, 197, 94, 0.1)',
                            border: '1px solid rgba(34, 197, 94, 0.3)',
                            color: '#22c55e',
                            padding: '1rem',
                            borderRadius: 'var(--radius-md)',
                            marginBottom: '1.5rem',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem'
                        }}
                    >
                        <CheckCircle size={18} />
                        <span>{success}</span>
                    </motion.div>
                )}

                {/* Error Message */}
                {error && (
                    <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="error-message"
                    >
                        {error}
                    </motion.div>
                )}

                {/* Login Form */}
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
                                placeholder="name@example.com"
                                className="form-input"
                            />
                        </div>
                    </div>

                    <div className="form-group">
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                            <label htmlFor="password">Password</label>
                            <Link
                                to="/forgot-password"
                                style={{
                                    color: 'var(--accent-primary)',
                                    textDecoration: 'none',
                                    fontSize: '0.875rem',
                                    fontWeight: '500',
                                    transition: 'color var(--transition-fast)'
                                }}
                                onMouseEnter={(e) => e.target.style.color = 'var(--accent-secondary)'}
                                onMouseLeave={(e) => e.target.style.color = 'var(--accent-primary)'}
                            >
                                Forgot Password?
                            </Link>
                        </div>
                        <div className="input-wrapper">
                            <Lock size={18} className="input-icon" />
                            <input
                                id="password"
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                placeholder="••••••••"
                                className="form-input"
                            />
                        </div>
                    </div>

                    <button
                        type="submit"
                        className="btn-submit"
                        disabled={isLoading}
                    >
                        {isLoading ? (
                            <span className="loading-text">Signing in...</span>
                        ) : (
                            <>
                                <span>Sign In</span>
                                <ArrowRight size={18} />
                            </>
                        )}
                    </button>
                </form>

                {/* Register Link */}
                <div className="register-link">
                    <span>Don't have an account?</span>
                    <Link to="/register" className="link-primary">
                        Create account
                    </Link>
                </div>

                {/* Footer */}
                <div className="login-footer">
                    <p>Professional automated trading platform</p>
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

export default Login;
