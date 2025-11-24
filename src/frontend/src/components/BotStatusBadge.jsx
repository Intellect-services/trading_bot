import React from 'react';
import { Activity, AlertCircle, CheckCircle, Clock, XCircle } from 'lucide-react';
import './BotStatusBadge.css';

const BotStatusBadge = ({ status, size = 'medium' }) => {
    const getStatusConfig = () => {
        switch (status) {
            case 'running':
                return {
                    icon: <Activity size={size === 'large' ? 24 : 16} />,
                    label: 'RUNNING',
                    className: 'status-running',
                    description: 'Bot is actively trading'
                };
            case 'stopped':
                return {
                    icon: <XCircle size={size === 'large' ? 24 : 16} />,
                    label: 'STOPPED',
                    className: 'status-stopped',
                    description: 'Bot is not running'
                };
            case 'starting':
                return {
                    icon: <Clock size={size === 'large' ? 24 : 16} />,
                    label: 'STARTING',
                    className: 'status-starting',
                    description: 'Initializing bot...'
                };
            case 'stopping':
                return {
                    icon: <Clock size={size === 'large' ? 24 : 16} />,
                    label: 'STOPPING',
                    className: 'status-stopping',
                    description: 'Shutting down...'
                };
            case 'paused':
                return {
                    icon: <AlertCircle size={size === 'large' ? 24 : 16} />,
                    label: 'PAUSED',
                    className: 'status-paused',
                    description: 'Bot is paused'
                };
            case 'error':
                return {
                    icon: <XCircle size={size === 'large' ? 24 : 16} />,
                    label: 'ERROR',
                    className: 'status-error',
                    description: 'Bot encountered an error'
                };
            default:
                return {
                    icon: <AlertCircle size={size === 'large' ? 24 : 16} />,
                    label: 'UNKNOWN',
                    className: 'status-unknown',
                    description: 'Status unknown'
                };
        }
    };

    const config = getStatusConfig();

    return (
        <div className={`bot-status-badge ${config.className} badge-${size}`}>
            <div className="status-icon">
                {config.icon}
            </div>
            <div className="status-content">
                <span className="status-label">{config.label}</span>
                {size === 'large' && (
                    <span className="status-description">{config.description}</span>
                )}
            </div>
            {(status === 'running' || status === 'starting' || status === 'stopping') && (
                <div className="status-pulse"></div>
            )}
        </div>
    );
};

export default BotStatusBadge;
