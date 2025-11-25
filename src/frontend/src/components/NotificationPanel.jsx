import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bell, X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react';
import { botAPI } from '../services/api';
import './NotificationPanel.css';

const NotificationPanel = () => {
    const [notifications, setNotifications] = useState([]);
    const [showPanel, setShowPanel] = useState(false);
    const [unreadCount, setUnreadCount] = useState(0);
    const panelRef = useRef(null);

    useEffect(() => {
        fetchNotifications();
        // Poll for new notifications every 10 seconds
        const interval = setInterval(fetchNotifications, 10000);
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (panelRef.current && !panelRef.current.contains(event.target)) {
                setShowPanel(false);
            }
        };

        if (showPanel) {
            document.addEventListener('mousedown', handleClickOutside);
        }

        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [showPanel]);

    const fetchNotifications = async () => {
        try {
            // Get bot status which may contain notifications
            const statusResponse = await botAPI.getStatus();
            const dashboardResponse = await botAPI.getDashboardData();

            const newNotifications = [];

            // Check for bot status messages
            if (statusResponse.data.message && statusResponse.data.message !== 'Trading bot not configured') {
                newNotifications.push({
                    id: `status-${Date.now()}`,
                    type: statusResponse.data.is_running ? 'success' : 'info',
                    title: 'Bot Status',
                    message: statusResponse.data.message,
                    timestamp: new Date(),
                    read: false
                });
            }

            // Check for error states
            if (statusResponse.data.error) {
                newNotifications.push({
                    id: `error-${Date.now()}`,
                    type: 'error',
                    title: 'Bot Error',
                    message: statusResponse.data.error,
                    timestamp: new Date(),
                    read: false
                });
            }

            // Update notifications list (deduplicate by ID)
            setNotifications(prev => {
                const existingIds = new Set(prev.map(n => n.id));
                const uniqueNew = newNotifications.filter(n => !existingIds.has(n.id));
                const updated = [...prev, ...uniqueNew].slice(-20); // Keep last 20

                // Update unread count
                const unread = updated.filter(n => !n.read).length;
                setUnreadCount(unread);

                return updated;
            });
        } catch (error) {
            console.error('Error fetching notifications:', error);
        }
    };

    const markAsRead = (notificationId) => {
        setNotifications(prev =>
            prev.map(n =>
                n.id === notificationId ? { ...n, read: true } : n
            )
        );
        setUnreadCount(prev => Math.max(0, prev - 1));
    };

    const markAllAsRead = () => {
        setNotifications(prev =>
            prev.map(n => ({ ...n, read: true }))
        );
        setUnreadCount(0);
    };

    const removeNotification = (notificationId) => {
        setNotifications(prev => {
            const notification = prev.find(n => n.id === notificationId);
            if (notification && !notification.read) {
                setUnreadCount(prevCount => Math.max(0, prevCount - 1));
            }
            return prev.filter(n => n.id !== notificationId);
        });
    };

    const getNotificationIcon = (type) => {
        switch (type) {
            case 'success':
                return <CheckCircle size={18} className="notification-icon success" />;
            case 'error':
                return <AlertTriangle size={18} className="notification-icon error" />;
            case 'warning':
                return <AlertCircle size={18} className="notification-icon warning" />;
            default:
                return <Info size={18} className="notification-icon info" />;
        }
    };

    const formatTimestamp = (timestamp) => {
        const now = new Date();
        const diff = now - new Date(timestamp);
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);

        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        if (days < 7) return `${days}d ago`;
        return new Date(timestamp).toLocaleDateString();
    };

    return (
        <div className="notification-panel" ref={panelRef}>
            <button
                className="notification-button"
                onClick={() => setShowPanel(!showPanel)}
                aria-label="Notifications"
            >
                <Bell size={20} />
                {unreadCount > 0 && (
                    <span className="notification-badge">{unreadCount > 9 ? '9+' : unreadCount}</span>
                )}
            </button>

            <AnimatePresence>
                {showPanel && (
                    <motion.div
                        className="notification-dropdown"
                        initial={{ opacity: 0, y: -10, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: -10, scale: 0.95 }}
                        transition={{ duration: 0.2 }}
                    >
                        <div className="notification-header">
                            <h3>Notifications</h3>
                            {unreadCount > 0 && (
                                <button
                                    className="mark-all-read"
                                    onClick={markAllAsRead}
                                >
                                    Mark all as read
                                </button>
                            )}
                        </div>

                        <div className="notification-list">
                            {notifications.length === 0 ? (
                                <div className="notification-empty">
                                    <Bell size={32} />
                                    <p>No notifications</p>
                                </div>
                            ) : (
                                notifications.map((notification) => (
                                    <motion.div
                                        key={notification.id}
                                        className={`notification-item ${notification.read ? 'read' : 'unread'}`}
                                        initial={{ opacity: 0, x: -10 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        onClick={() => markAsRead(notification.id)}
                                    >
                                        <div className="notification-icon-wrapper">
                                            {getNotificationIcon(notification.type)}
                                        </div>
                                        <div className="notification-content">
                                            <div className="notification-title-row">
                                                <h4>{notification.title}</h4>
                                                <button
                                                    className="notification-close"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        removeNotification(notification.id);
                                                    }}
                                                >
                                                    <X size={14} />
                                                </button>
                                            </div>
                                            <p>{notification.message}</p>
                                            <span className="notification-time">
                                                {formatTimestamp(notification.timestamp)}
                                            </span>
                                        </div>
                                    </motion.div>
                                ))
                            )}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default NotificationPanel;
