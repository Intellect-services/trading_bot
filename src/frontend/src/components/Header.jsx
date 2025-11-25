import React, { useState, useRef, useEffect } from 'react';
import { Bell, Search, ChevronDown, LogOut, User, Settings } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import TradingModeToggle from './TradingModeToggle';
import NotificationPanel from './NotificationPanel';

const Header = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [showDropdown, setShowDropdown] = useState(false);
    const dropdownRef = useRef(null);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setShowDropdown(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, []);

    const handleLogout = async () => {
        await logout();
        navigate('/login');
    };

    return (
        <header style={{
            height: '80px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 2rem',
            borderBottom: '1px solid var(--glass-border)',
            background: 'rgba(10, 10, 15, 0.5)',
            backdropFilter: 'blur(10px)',
            position: 'sticky',
            top: 0,
            zIndex: 40
        }}>
            <div style={{ position: 'relative', width: '300px' }}>
                <Search size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                <input
                    type="text"
                    placeholder="Search markets, assets..."
                    style={{
                        width: '100%',
                        padding: '0.625rem 1rem 0.625rem 2.5rem',
                        background: 'rgba(255, 255, 255, 0.05)',
                        border: '1px solid var(--glass-border)',
                        borderRadius: 'var(--radius-md)',
                        color: 'white',
                        outline: 'none',
                        fontSize: '0.875rem'
                    }}
                    onFocus={(e) => e.target.style.borderColor = 'var(--accent-primary)'}
                    onBlur={(e) => e.target.style.borderColor = 'var(--glass-border)'}
                />
            </div>

            <div className="flex-center" style={{ gap: '1.5rem' }}>
                <TradingModeToggle />

                <NotificationPanel />

                <div
                    ref={dropdownRef}
                    style={{ position: 'relative' }}
                >
                    <div
                        className="flex-center"
                        style={{
                            gap: '0.75rem',
                            cursor: 'pointer',
                            padding: '0.5rem 1rem',
                            borderRadius: 'var(--radius-md)',
                            transition: 'all 0.2s',
                            background: showDropdown ? 'rgba(255, 255, 255, 0.05)' : 'transparent'
                        }}
                        onClick={() => setShowDropdown(!showDropdown)}
                        onMouseEnter={(e) => {
                            if (!showDropdown) e.currentTarget.style.background = 'rgba(255, 255, 255, 0.03)';
                        }}
                        onMouseLeave={(e) => {
                            if (!showDropdown) e.currentTarget.style.background = 'transparent';
                        }}
                    >
                        {user?.avatar ? (
                            <img
                                src={user.avatar}
                                alt={user.name}
                                style={{
                                    width: '40px',
                                    height: '40px',
                                    borderRadius: '50%',
                                    border: '2px solid var(--accent-primary)',
                                    boxShadow: '0 0 0 2px rgba(99, 102, 241, 0.1)'
                                }}
                            />
                        ) : (
                            <div style={{
                                width: '40px',
                                height: '40px',
                                borderRadius: '50%',
                                border: '2px solid var(--accent-primary)',
                                background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                color: 'white',
                                fontWeight: '600',
                                fontSize: '1rem',
                                boxShadow: '0 0 0 2px rgba(99, 102, 241, 0.1)'
                            }}>
                                {user?.name?.[0] || 'U'}
                            </div>
                        )}
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
                            <span style={{ fontSize: '0.875rem', fontWeight: '600', color: 'var(--text-primary)' }}>{user?.name}</span>
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Pro Trader</span>
                        </div>
                        <ChevronDown
                            size={16}
                            color="var(--text-muted)"
                            style={{
                                transform: showDropdown ? 'rotate(180deg)' : 'rotate(0)',
                                transition: 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                                marginLeft: '0.25rem'
                            }}
                        />
                    </div>

                    {showDropdown && (
                        <div style={{
                            position: 'absolute',
                            top: 'calc(100% + 0.75rem)',
                            right: 0,
                            width: '260px',
                            background: 'rgba(17, 24, 39, 0.95)',
                            backdropFilter: 'blur(20px)',
                            border: '1px solid rgba(99, 102, 241, 0.2)',
                            borderRadius: 'var(--radius-lg)',
                            padding: '0.75rem',
                            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.2), 0 0 0 1px rgba(99, 102, 241, 0.1)',
                            zIndex: 50,
                            animation: 'dropdownSlideIn 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                            transformOrigin: 'top right'
                        }}>
                            {/* User Info Section */}
                            <div style={{
                                padding: '1rem',
                                marginBottom: '0.5rem',
                                background: 'rgba(99, 102, 241, 0.05)',
                                borderRadius: 'var(--radius-md)',
                                border: '1px solid rgba(99, 102, 241, 0.1)'
                            }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                                    {user?.avatar ? (
                                        <img
                                            src={user.avatar}
                                            alt={user.name}
                                            style={{
                                                width: '48px',
                                                height: '48px',
                                                borderRadius: '50%',
                                                border: '2px solid var(--accent-primary)'
                                            }}
                                        />
                                    ) : (
                                        <div style={{
                                            width: '48px',
                                            height: '48px',
                                            borderRadius: '50%',
                                            border: '2px solid var(--accent-primary)',
                                            background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            color: 'white',
                                            fontWeight: '600',
                                            fontSize: '1.25rem'
                                        }}>
                                            {user?.name?.[0] || 'U'}
                                        </div>
                                    )}
                                    <div style={{ flex: 1 }}>
                                        <div style={{ fontSize: '0.9375rem', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '0.125rem' }}>
                                            {user?.name}
                                        </div>
                                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                            {user?.email}
                                        </div>
                                    </div>
                                </div>
                                <div style={{
                                    display: 'inline-flex',
                                    alignItems: 'center',
                                    gap: '0.375rem',
                                    padding: '0.25rem 0.625rem',
                                    background: 'rgba(99, 102, 241, 0.15)',
                                    borderRadius: 'var(--radius-sm)',
                                    fontSize: '0.6875rem',
                                    fontWeight: '600',
                                    color: 'var(--accent-primary)',
                                    border: '1px solid rgba(99, 102, 241, 0.2)'
                                }}>
                                    <div style={{
                                        width: '6px',
                                        height: '6px',
                                        borderRadius: '50%',
                                        background: 'var(--accent-primary)',
                                        boxShadow: '0 0 6px var(--accent-primary)'
                                    }} />
                                    PRO TRADER
                                </div>
                            </div>

                            {/* Menu Items */}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                                <button
                                    onClick={() => {
                                        navigate('/account');
                                        setShowDropdown(false);
                                    }}
                                    style={{
                                        width: '100%',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '0.75rem',
                                        padding: '0.75rem 1rem',
                                        background: 'transparent',
                                        border: 'none',
                                        color: 'var(--text-primary)',
                                        cursor: 'pointer',
                                        borderRadius: 'var(--radius-md)',
                                        fontSize: '0.875rem',
                                        fontWeight: '500',
                                        textAlign: 'left',
                                        transition: 'all 0.2s'
                                    }}
                                    onMouseEnter={(e) => {
                                        e.currentTarget.style.background = 'rgba(99, 102, 241, 0.1)';
                                        e.currentTarget.style.transform = 'translateX(4px)';
                                        e.currentTarget.querySelector('svg').style.color = 'var(--accent-primary)';
                                    }}
                                    onMouseLeave={(e) => {
                                        e.currentTarget.style.background = 'transparent';
                                        e.currentTarget.style.transform = 'translateX(0)';
                                        e.currentTarget.querySelector('svg').style.color = 'var(--text-secondary)';
                                    }}
                                >
                                    <User size={18} style={{ color: 'var(--text-secondary)', transition: 'color 0.2s' }} />
                                    <span>My Account</span>
                                </button>
                                <button
                                    onClick={() => {
                                        navigate('/settings');
                                        setShowDropdown(false);
                                    }}
                                    style={{
                                        width: '100%',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '0.75rem',
                                        padding: '0.75rem 1rem',
                                        background: 'transparent',
                                        border: 'none',
                                        color: 'var(--text-primary)',
                                        cursor: 'pointer',
                                        borderRadius: 'var(--radius-md)',
                                        fontSize: '0.875rem',
                                        fontWeight: '500',
                                        textAlign: 'left',
                                        transition: 'all 0.2s'
                                    }}
                                    onMouseEnter={(e) => {
                                        e.currentTarget.style.background = 'rgba(99, 102, 241, 0.1)';
                                        e.currentTarget.style.transform = 'translateX(4px)';
                                        e.currentTarget.querySelector('svg').style.color = 'var(--accent-primary)';
                                    }}
                                    onMouseLeave={(e) => {
                                        e.currentTarget.style.background = 'transparent';
                                        e.currentTarget.style.transform = 'translateX(0)';
                                        e.currentTarget.querySelector('svg').style.color = 'var(--text-secondary)';
                                    }}
                                >
                                    <Settings size={18} style={{ color: 'var(--text-secondary)', transition: 'color 0.2s' }} />
                                    <span>Settings</span>
                                </button>
                            </div>

                            {/* Divider */}
                            <div style={{
                                height: '1px',
                                background: 'linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.3), transparent)',
                                margin: '0.75rem 0'
                            }} />

                            {/* Logout Button */}
                            <button
                                onClick={handleLogout}
                                style={{
                                    width: '100%',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '0.75rem',
                                    padding: '0.75rem 1rem',
                                    background: 'transparent',
                                    border: 'none',
                                    color: 'var(--danger)',
                                    cursor: 'pointer',
                                    borderRadius: 'var(--radius-md)',
                                    fontSize: '0.875rem',
                                    fontWeight: '600',
                                    textAlign: 'left',
                                    transition: 'all 0.2s'
                                }}
                                onMouseEnter={(e) => {
                                    e.currentTarget.style.background = 'rgba(239, 68, 68, 0.15)';
                                    e.currentTarget.style.transform = 'translateX(4px)';
                                }}
                                onMouseLeave={(e) => {
                                    e.currentTarget.style.background = 'transparent';
                                    e.currentTarget.style.transform = 'translateX(0)';
                                }}
                            >
                                <LogOut size={18} />
                                <span>Logout</span>
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </header>
    );
};

export default Header;
