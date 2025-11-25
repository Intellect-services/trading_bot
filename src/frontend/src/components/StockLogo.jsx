import React, { useState, useEffect } from 'react';

const StockLogo = ({ symbol, size = 40 }) => {
    const [logoLoaded, setLogoLoaded] = useState(false);
    const [logoError, setLogoError] = useState(false);

    useEffect(() => {
        if (!symbol) return;
        setLogoLoaded(false);
        setLogoError(false);
    }, [symbol]);

    // Generate a beautiful deterministic color gradient based on symbol
    const getSymbolGradient = (sym) => {
        if (!sym) return ['#6366f1', '#8b5cf6'];
        const hash1 = sym.charCodeAt(0) * 137.508;
        const hash2 = (sym.charCodeAt(sym.length > 1 ? 1 : 0) * 137.508) + 60;
        const hue1 = Math.abs(hash1) % 360;
        const hue2 = Math.abs(hash2) % 360;

        // Use complementary colors for better gradients
        const colors = [
            `hsl(${hue1}, 70%, 55%)`,
            `hsl(${hue2}, 70%, 50%)`
        ];
        return colors;
    };

    const colors = getSymbolGradient(symbol);
    const initials = symbol.substring(0, 2).toUpperCase();

    // Always show a beautiful gradient badge - simpler and more consistent
    return (
        <div style={{
            width: `${size}px`,
            height: `${size}px`,
            borderRadius: '12px',
            background: `linear-gradient(135deg, ${colors[0]}, ${colors[1]})`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: '700',
            fontSize: `${Math.max(size * 0.4, 14)}px`,
            color: 'white',
            flexShrink: 0,
            boxShadow: `
                0 4px 12px rgba(0,0,0,0.15),
                inset 0 1px 0 rgba(255,255,255,0.2)
            `,
            border: '2px solid rgba(255,255,255,0.15)',
            position: 'relative',
            overflow: 'hidden'
        }}>
            {/* Subtle shine effect */}
            <div style={{
                position: 'absolute',
                top: '-50%',
                left: '-50%',
                width: '200%',
                height: '200%',
                background: 'linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%)',
                transform: 'rotate(45deg)',
                pointerEvents: 'none'
            }} />
            <span style={{
                position: 'relative',
                zIndex: 1,
                textShadow: '0 1px 2px rgba(0,0,0,0.2)',
                letterSpacing: '-0.5px'
            }}>
                {initials}
            </span>
        </div>
    );
};

export default StockLogo;
