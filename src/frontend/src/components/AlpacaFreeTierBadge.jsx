import React from 'react';
import { Info } from 'lucide-react';
import './AlpacaFreeTierBadge.css';

const AlpacaFreeTierBadge = ({ showTooltip = true, size = 'default' }) => {
    return (
        <span
            className={`alpaca-free-badge ${size}`}
            title={showTooltip ? "Uses FREE Alpaca API endpoint - No subscription required for paper trading" : undefined}
        >
            <Info size={size === 'small' ? 12 : 14} />
            <span>FREE</span>
        </span>
    );
};

export default AlpacaFreeTierBadge;
