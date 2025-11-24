import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Binoculars, Mail, Lock, User, AlertCircle, CheckCircle, TrendingUp, ArrowRight } from 'lucide-react';
import './Login.css';

const Register = () => {
    const [formData, setFormData] = useState({
        name: '',
        email: '',
        password: '',
        confirmPassword: ''
    });
    const [errors, setErrors] = useState({});
    const [loading, setLoading] = useState(false);
    const { register } = useAuth();
    const navigate = useNavigate();

    const validateForm = () => {
        const newErrors = {};

        if (!formData.name.trim()) {
            newErrors.name = 'Name is required';
        }

        if (!formData.email.trim()) {
            newErrors.email = 'Email is required';
        } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
            newErrors.email = 'Email is invalid';
        }

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

        if (!validateForm()) return;

        setLoading(true);
        try {
            await register(formData.email, formData.password, formData.name);
            // Redirect to verification page with email
            navigate(`/verify-email?email=${encodeURIComponent(formData.email)}`);
        } catch (error) {
            setErrors({ submit: error.message || 'Registration failed' });
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
                    <h2>Create Account</h2>
                    <p>Join IntellectScout and start trading smarter</p>
                </div>

                {/* Error Message */}
                {errors.submit && (
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
                        <AlertCircle size={20} color="var(--danger)" />
                        <span style={{ color: 'var(--danger)', fontSize: '0.875rem' }}>{errors.submit}</span>
                    </motion.div>
                )}

                {/* Form */}
                <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                    {/* Name Field */}
                    <div>
                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', fontSize: '0.875rem' }}>
                            Full Name
                        </label>
                        <div style={{ position: 'relative' }}>
                            <User size={20} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                            <input
                                type="text"
                                name="name"
                                value={formData.name}
                                onChange={handleChange}
                                placeholder="John Doe"
                                style={{
                                    width: '100%',
                                    padding: '0.875rem 1rem 0.875rem 3rem',
                                    background: 'rgba(255, 255, 255, 0.05)',
                                    border: `1px solid ${errors.name ? 'var(--danger)' : 'var(--glass-border)'}`,
                                    borderRadius: 'var(--radius-md)',
                                    color: 'white',
                                    fontSize: '1rem',
                                    outline: 'none',
                                    transition: 'border-color var(--transition-fast)'
                                }}
                                onFocus={(e) => e.target.style.borderColor = 'var(--accent-primary)'}
                                onBlur={(e) => e.target.style.borderColor = errors.name ? 'var(--danger)' : 'var(--glass-border)'}
                            />
                        </div>
                        {errors.name && (
                            <span style={{ color: 'var(--danger)', fontSize: '0.75rem', marginTop: '0.25rem', display: 'block' }}>
                                {errors.name}
                            </span>
                        )}
                    </div>

                    {/* Email Field */}
                    <div>
                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', fontSize: '0.875rem' }}>
                            Email Address
                        </label>
                        <div style={{ position: 'relative' }}>
                            <Mail size={20} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                            <input
                                type="email"
                                name="email"
                                value={formData.email}
                                onChange={handleChange}
                                placeholder="you@example.com"
                                style={{
                                    width: '100%',
                                    padding: '0.875rem 1rem 0.875rem 3rem',
                                    background: 'rgba(255, 255, 255, 0.05)',
                                    border: `1px solid ${errors.email ? 'var(--danger)' : 'var(--glass-border)'}`,
                                    borderRadius: 'var(--radius-md)',
                                    color: 'white',
                                    fontSize: '1rem',
                                    outline: 'none',
                                    transition: 'border-color var(--transition-fast)'
                                }}
                                onFocus={(e) => e.target.style.borderColor = 'var(--accent-primary)'}
                                onBlur={(e) => e.target.style.borderColor = errors.email ? 'var(--danger)' : 'var(--glass-border)'}
                            />
                        </div>
                        {errors.email && (
                            <span style={{ color: 'var(--danger)', fontSize: '0.75rem', marginTop: '0.25rem', display: 'block' }}>
                                {errors.email}
                            </span>
                        )}
                    </div>

                    {/* Password Field */}
                    <div>
                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', fontSize: '0.875rem' }}>
                            Password
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
                            <CheckCircle size={20} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
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
                            <span className="loading-text">Creating Account...</span>
                        ) : (
                            <>
                                <span>Create Account</span>
                                <ArrowRight size={18} />
                            </>
                        )}
                    </button>
                </form>

                {/* Login Link */}
                <div style={{ textAlign: 'center', marginTop: '2rem' }}>
                    <span style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                        Already have an account?{' '}
                        <Link
                            to="/login"
                            style={{
                                color: 'var(--accent-primary)',
                                textDecoration: 'none',
                                fontWeight: '600',
                                transition: 'color var(--transition-fast)'
                            }}
                            onMouseEnter={(e) => e.target.style.color = 'var(--accent-secondary)'}
                            onMouseLeave={(e) => e.target.style.color = 'var(--accent-primary)'}
                        >
                            Sign in
                        </Link>
                    </span>
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

export default Register;
