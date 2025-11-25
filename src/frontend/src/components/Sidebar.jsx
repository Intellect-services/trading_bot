import React from 'react';
import { NavLink, Link } from 'react-router-dom';
import { LayoutDashboard, TrendingUp, History, Settings, LogOut, Activity, Binoculars, Sparkles, Zap, Wallet } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Sidebar = () => {
    const { logout } = useAuth();

    const navItems = [
        { icon: LayoutDashboard, label: 'Dashboard', path: '/' },
        { icon: Zap, label: 'Trading Activity', path: '/trading-activity' },
        { icon: Wallet, label: 'Positions', path: '/trades' },
        { icon: Activity, label: 'Strategies', path: '/strategies' },
        { icon: History, label: 'History', path: '/history' },
        { icon: Sparkles, label: 'Features', path: '/features' },
        { icon: Settings, label: 'Settings', path: '/settings' },
    ];

    return (
        <aside style={{
            width: '260px',
            height: '100vh',
            position: 'fixed',
            left: 0,
            top: 0,
            background: 'rgba(10, 10, 15, 0.8)',
            backdropFilter: 'blur(20px)',
            borderRight: '1px solid var(--glass-border)',
            display: 'flex',
            flexDirection: 'column',
            padding: '1.5rem',
            zIndex: 50
        }}>
            <div className="sidebar-header" style={{ marginBottom: '3rem' }}>
                <Link
                    to="/"
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '0.75rem',
                        textDecoration: 'none',
                        transition: 'opacity 0.2s ease'
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.opacity = '0.8'}
                    onMouseLeave={(e) => e.currentTarget.style.opacity = '1'}
                >
                    <TrendingUp size={32} style={{ color: '#a78bfa' }} />
                    <span style={{
                        fontSize: '1.5rem',
                        fontWeight: '700',
                        color: 'var(--text-primary)',
                        letterSpacing: '-0.02em'
                    }}>
                        IntellectScout
                    </span>
                </Link>
            </div>

            <nav style={{ flex: 1 }}>
                <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {navItems.map((item) => (
                        <li key={item.path}>
                            <NavLink
                                to={item.path}
                                style={({ isActive }) => ({
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '0.75rem',
                                    padding: '0.75rem 1rem',
                                    borderRadius: 'var(--radius-md)',
                                    color: isActive ? 'white' : 'var(--text-secondary)',
                                    background: isActive ? 'rgba(99, 102, 241, 0.1)' : 'transparent',
                                    border: isActive ? '1px solid rgba(99, 102, 241, 0.2)' : '1px solid transparent',
                                    textDecoration: 'none',
                                    transition: 'all 0.2s ease',
                                    fontWeight: isActive ? 500 : 400
                                })}
                            >
                                <item.icon size={20} />
                                {item.label}
                            </NavLink>
                        </li>
                    ))}
                </ul>
            </nav>

            <button
                onClick={logout}
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    padding: '0.75rem 1rem',
                    borderRadius: 'var(--radius-md)',
                    color: 'var(--text-muted)',
                    background: 'transparent',
                    border: 'none',
                    cursor: 'pointer',
                    transition: 'color 0.2s ease',
                    marginTop: 'auto'
                }}
                onMouseEnter={(e) => e.target.style.color = 'var(--danger)'}
                onMouseLeave={(e) => e.target.style.color = 'var(--text-muted)'}
            >
                <LogOut size={20} />
                Sign Out
            </button>
        </aside>
    );
};

export default Sidebar;
