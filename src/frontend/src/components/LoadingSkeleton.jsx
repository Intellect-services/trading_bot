import React from 'react';
import './LoadingSkeleton.css';

export const CardSkeleton = () => (
    <div className="glass-card" style={{ padding: '1.5rem' }}>
        <div className="skeleton skeleton-icon" style={{ marginBottom: '1rem' }} />
        <div className="skeleton skeleton-text" style={{ width: '60%', marginBottom: '0.5rem' }} />
        <div className="skeleton skeleton-title" style={{ width: '80%' }} />
    </div>
);

export const ChartSkeleton = () => (
    <div className="glass-card" style={{ padding: '1.5rem', gridColumn: '1 / -1' }}>
        <div className="skeleton skeleton-text" style={{ width: '30%', marginBottom: '1rem' }} />
        <div className="skeleton" style={{ width: '100%', height: '300px', borderRadius: 'var(--radius-md)' }} />
    </div>
);

export const TableSkeleton = () => (
    <div className="glass-card" style={{ padding: '1.5rem' }}>
        <div className="skeleton skeleton-text" style={{ width: '40%', marginBottom: '1rem' }} />
        {[...Array(5)].map((_, i) => (
            <div key={i} style={{ display: 'flex', gap: '1rem', marginBottom: '0.75rem' }}>
                <div className="skeleton" style={{ width: '20%', height: '20px' }} />
                <div className="skeleton" style={{ width: '30%', height: '20px' }} />
                <div className="skeleton" style={{ width: '25%', height: '20px' }} />
                <div className="skeleton" style={{ width: '25%', height: '20px' }} />
            </div>
        ))}
    </div>
);
