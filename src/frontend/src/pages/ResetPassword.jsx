import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Lock, CheckCircle, AlertCircle, TrendingUp, ArrowRight } from 'lucide-react';
import { authAPI } from '../services/api';
import './Login.css';

const ResetPassword = () => {
    const [searchParams] = useSearchParams();
    const token = searchParams.get('token');
    const [formData, setFormData] = useState({
        password: '',
        confirmPassword: ''
    });
    const [errors, setErrors] = useState({});
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
        if (!token) {
            setError('Invalid reset link. Please request a new password reset.');
        }
    }, [token]);

    const validateForm = () => {
        const newErrors = {};

        if (!formData.password) {
            newErrors.password = 'Password is required';
        } else if (formData.password.length < 6) {
            newErrors.password = 'Password must be at least 6 characters';
        }

        if (formData.password !== formData.confirmPassword) {
            newErrors.confirmPassword = 'Passwords do not match';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const getPasswordStrength = () => {
        const password = formData.password;
        if (!password) return { strength: 0, label: '', color: '' };

        let strength = 0;
        if (password.length >= 6) strength++;
        if (password.length >= 10) strength++;
        if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
        if (/\d/.test(password)) strength++;
        if (/[^a-zA-Z\d]/.test(password)) strength++;

        const labels = ['', 'Weak', 'Fair', 'Good', 'Strong', 'Very Strong'];
        const colors = ['', '#ef4444', '#f59e0b', '#eab308', '#10b981', '#059669'];

        return { strength, label: labels[strength], color: colors[strength] };
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!validateForm() || !token) return;

        setLoading(true);
        setError('');

        try {
            const response = await authAPI.resetPassword(token, formData.password);
            if (response.data.status === 'success') {
                setSuccess(true);
                // Redirect to login after 3 seconds
                setTimeout(() => {
                    navigate('/login?password_reset=true');
                }, 3000);
            } else {
                setError(response.data.message || 'Failed to reset password');
            }
        } catch (err) {
            setError(err.response?.data?.message || 'Failed to reset password');
        } finally {
            setLoading(false);
        }
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
        // Clear error for this field
        if (errors[name]) {
            setErrors(prev => ({ ...prev, [name]: '' }));
        }
    };

    const passwordStrength = getPasswordStrength();

    if (!token) {
        return (
            <>
                <header className="auth-page-header">
                    <div className="auth-header-content">
                        <Link to="/" className="auth-logo">
                            <TrendingUp size={24} />
                            <span>IntellectScout</span>
                        </Link>
                    </div>
                </header>

                <div className="login-container">
                    <div className="login-background">
                        <div className="gradient-orb orb-1"></div>
                        <div className="gradient-orb orb-2"></div>
                        <div className="grid-pattern"></div>
                    </div>

                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="login-card"
                        style={{ maxWidth: '480px' }}
                    >
                        <div style={{
                            padding: '2rem',
                            textAlign: 'center'
                        }}>
                            <AlertCircle size={48} style={{ color: '#ef4444', marginBottom: '1rem' }} />
                            <h2 style={{ marginBottom: '1rem', color: 'var(--text-primary)' }}>
                                Invalid Reset Link
                            </h2>
                            <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>
                                This password reset link is invalid or has expired. Please request a new one.
                            </p>
                            <Link
                                to="/forgot-password"
                                className="btn-submit"
                                style={{ textDecoration: 'none', display: 'inline-block' }}
                            >
                                Request New Reset Link
                            </Link>
                        </div>
                    </motion.div>
                </div>
            </>
        );
    }

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
                        <p>Enter your new password below</p>
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
                                alignItems: 'center',
                                gap: '0.75rem'
                            }}
                        >
                            <CheckCircle size={24} style={{ color: '#22c55e' }} />
                            <div style={{ flex: 1 }}>
                                <h3 style={{
                                    color: '#22c55e',
                                    fontSize: '1rem',
                                    fontWeight: '600',
                                    margin: '0 0 0.5rem 0'
                                }}>
                                    Password Reset Successful!
                                </h3>
                                <p style={{
                                    color: 'var(--text-secondary)',
                                    fontSize: '0.875rem',
                                    margin: 0
                                }}>
                                    Redirecting to login page...
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
                        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                            {/* Password Field */}
                            <div>
                                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', fontSize: '0.875rem' }}>
                                    New Password
                                </label>
                                <div style={{ position: 'relative' }}>
                                    <Lock size={20} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                                    <input
                                        type="password"
                                        name="password"
                                        value={formData.password}
                                        onChange={handleChange}
                                        placeholder="••••••••"
                                        style={{
                                            width: '100%',
                                            padding: '0.875rem 1rem 0.875rem 3rem',
                                            background: 'rgba(255, 255, 255, 0.05)',
                                            border: `1px solid ${errors.password ? 'var(--danger)' : 'var(--glass-border)'}`,
                                            borderRadius: 'var(--radius-md)',
                                            color: 'white',
                                            fontSize: '1rem',
                                            outline: 'none',
                                            transition: 'border-color var(--transition-fast)'
                                        }}
                                        onFocus={(e) => e.target.style.borderColor = 'var(--accent-primary)'}
                                        onBlur={(e) => e.target.style.borderColor = errors.password ? 'var(--danger)' : 'var(--glass-border)'}
                                    />
                                </div>
                                {errors.password && (
                                    <span style={{ color: 'var(--danger)', fontSize: '0.75rem', marginTop: '0.25rem', display: 'block' }}>
                                        {errors.password}
                                    </span>
                                )}
                                {/* Password Strength Indicator */}
                                {formData.password && !errors.password && (
                                    <div style={{ marginTop: '0.5rem' }}>
                                        <div style={{ display: 'flex', gap: '0.25rem', marginBottom: '0.25rem' }}>
                                            {[...Array(5)].map((_, i) => (
                                                <div
                                                    key={i}
                                                    style={{
                                                        flex: 1,
                                                        height: '4px',
                                                        borderRadius: '2px',
                                                        background: i < passwordStrength.strength ? passwordStrength.color : 'rgba(255,255,255,0.1)',
                                                        transition: 'background var(--transition-base)'
                                                    }}
                                                />
                                            ))}
                                        </div>
                                        <span style={{ fontSize: '0.75rem', color: passwordStrength.color }}>
                                            {passwordStrength.label}
                                        </span>
                                    </div>
                                )}
                            </div>

                            {/* Confirm Password Field */}
                            <div>
                                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', fontSize: '0.875rem' }}>
                                    Confirm Password
                                </label>
                                <div style={{ position: 'relative' }}>
                                    <Lock size={20} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                                    <input
                                        type="password"
                                        name="confirmPassword"
                                        value={formData.confirmPassword}
                                        onChange={handleChange}
                                        placeholder="••••••••"
                                        style={{
                                            width: '100%',
                                            padding: '0.875rem 1rem 0.875rem 3rem',
                                            background: 'rgba(255, 255, 255, 0.05)',
                                            border: `1px solid ${errors.confirmPassword ? 'var(--danger)' : 'var(--glass-border)'}`,
                                            borderRadius: 'var(--radius-md)',
                                            color: 'white',
                                            fontSize: '1rem',
                                            outline: 'none',
                                            transition: 'border-color var(--transition-fast)'
                                        }}
                                        onFocus={(e) => e.target.style.borderColor = 'var(--accent-primary)'}
                                        onBlur={(e) => e.target.style.borderColor = errors.confirmPassword ? 'var(--danger)' : 'var(--glass-border)'}
                                    />
                                </div>
                                {errors.confirmPassword && (
                                    <span style={{ color: 'var(--danger)', fontSize: '0.75rem', marginTop: '0.25rem', display: 'block' }}>
                                        {errors.confirmPassword}
                                    </span>
                                )}
                            </div>

                            {/* Submit Button */}
                            <button
                                type="submit"
                                className="btn-submit"
                                disabled={loading}
                            >
                                {loading ? (
                                    <span className="loading-text">Resetting Password...</span>
                                ) : (
                                    <>
                                        <span>Reset Password</span>
                                        <ArrowRight size={18} />
                                    </>
                                )}
                            </button>
                        </form>
                    )}

                    {/* Back to Login */}
                    {!success && (
                        <div style={{
                            textAlign: 'center',
                            marginTop: '2rem'
                        }}>
                            <Link
                                to="/login"
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
                                Back to Sign In
                            </Link>
                        </div>
                    )}
                </motion.div>
            </div>

            {/* Sticky Footer */}
            <footer className="auth-page-footer">
                <p>© 2024 IntellectScout. All rights reserved.</p>
            </footer>
        </>
    );
};

export default ResetPassword;
