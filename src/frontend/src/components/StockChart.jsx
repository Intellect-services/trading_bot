import React, { useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { TrendingUp } from 'lucide-react';

const StockChart = ({ data }) => {
    const [timeRange, setTimeRange] = useState('ALL');

    // Data is expected to be an array of { timestamp, portfolio_value }
    const rawData = data || [];

    // Filter data based on time range
    const filterDataByRange = (data, range) => {
        if (!data || data.length === 0) return [];
        if (range === 'ALL') return data;

        const now = new Date();
        let cutoffDate = new Date();

        switch (range) {
            case '1D':
                cutoffDate.setDate(now.getDate() - 1);
                break;
            case '1W':
                cutoffDate.setDate(now.getDate() - 7);
                break;
            case '1M':
                cutoffDate.setMonth(now.getMonth() - 1);
                break;
            case '3M':
                cutoffDate.setMonth(now.getMonth() - 3);
                break;
            case '1Y':
                cutoffDate.setFullYear(now.getFullYear() - 1);
                break;
            default:
                return data;
        }

        return data.filter(item => {
            const itemDate = new Date(item.timestamp);
            return itemDate >= cutoffDate;
        });
    };

    const chartData = filterDataByRange(rawData, timeRange);
    const hasData = chartData.length > 0;

    const CustomTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) {
            return (
                <div style={{
                    background: 'rgba(10, 10, 15, 0.95)',
                    border: '1px solid var(--glass-border)',
                    padding: '0.75rem 1rem',
                    borderRadius: 'var(--radius-md)',
                    boxShadow: '0 4px 20px rgba(0,0,0,0.5)'
                }}>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', marginBottom: '0.25rem' }}>
                        {new Date(label).toLocaleString()}
                    </p>
                    <p style={{ color: 'var(--accent-primary)', fontWeight: '600', fontSize: '1rem' }}>
                        ${payload[0].value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </p>
                </div>
            );
        }
        return null;
    };

    return (
        <div className="glass-card" style={{ padding: '1.5rem', gridColumn: 'span 2', minHeight: '400px', display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <h3 style={{ fontSize: '1.125rem', fontWeight: '600' }}>Portfolio Performance</h3>
                <div style={{ display: 'flex', background: 'rgba(255, 255, 255, 0.05)', borderRadius: 'var(--radius-md)', padding: '0.25rem' }}>
                    {['1D', '1W', '1M', '3M', '1Y', 'ALL'].map((range) => (
                        <button
                            key={range}
                            onClick={() => setTimeRange(range)}
                            style={{
                                background: timeRange === range ? 'var(--accent-primary)' : 'transparent',
                                color: timeRange === range ? 'white' : 'var(--text-muted)',
                                border: 'none',
                                padding: '0.25rem 0.75rem',
                                borderRadius: 'var(--radius-sm)',
                                fontSize: '0.75rem',
                                fontWeight: '500',
                                cursor: 'pointer',
                                transition: 'all 0.2s'
                            }}
                        >
                            {range}
                        </button>
                    ))}
                </div>
            </div>

            <div style={{ flex: 1, width: '100%', minHeight: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative' }}>
                {!hasData || chartData.length === 0 ? (
                    <div style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
                        <TrendingUp size={48} style={{ opacity: 0.3, marginBottom: '1rem' }} />
                        <p style={{ fontSize: '1rem', marginBottom: '0.5rem' }}>No Performance Data Yet</p>
                        <p style={{ fontSize: '0.875rem', opacity: 0.7 }}>
                            {rawData.length === 0
                                ? "Portfolio history will appear here once Alpaca has collected data."
                                : "Historical data will appear here as the bot trades."
                            }
                        </p>
                    </div>
                ) : chartData.length === 1 ? (
                    <div style={{ textAlign: 'center', color: 'var(--text-secondary)', width: '100%' }}>
                        <TrendingUp size={48} style={{ opacity: 0.3, marginBottom: '1rem' }} />
                        <p style={{ fontSize: '1rem', marginBottom: '0.5rem' }}>Current Portfolio Value</p>
                        <p style={{ fontSize: '1.5rem', fontWeight: '600', color: 'var(--accent-primary)', marginBottom: '0.5rem' }}>
                            ${chartData[0].portfolio_value?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
                        </p>
                        <p style={{ fontSize: '0.875rem', opacity: 0.7 }}>
                            Historical data will appear here as more data becomes available from Alpaca.
                        </p>
                    </div>
                ) : (
                    <div style={{ width: '100%', height: '100%', minHeight: '300px', minWidth: 0 }}>
                        <ResponsiveContainer width="100%" height="100%" minHeight={300} minWidth={0}>
                            <AreaChart
                                data={chartData}
                                margin={{ top: 10, right: 10, left: 0, bottom: 5 }}
                            >
                                <defs>
                                    <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="var(--accent-primary)" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="var(--accent-primary)" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                                <XAxis
                                    dataKey="timestamp"
                                    tickFormatter={(str) => {
                                        try {
                                            const date = new Date(str);
                                            if (isNaN(date.getTime())) return str;
                                            return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
                                        } catch {
                                            return str;
                                        }
                                    }}
                                    stroke="rgba(255,255,255,0.2)"
                                    strokeWidth={2}
                                    tickLine={false}
                                    axisLine={true}
                                    tick={{
                                        fill: 'rgba(255,255,255,0.7)',
                                        fontSize: '10px',
                                        fontWeight: '500',
                                        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
                                    }}
                                    style={{
                                        fontSize: '10px',
                                        fill: 'rgba(255,255,255,0.7)',
                                        fontWeight: '500',
                                        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
                                    }}
                                    tickMargin={6}
                                    height={30}
                                />
                                <YAxis
                                    domain={['auto', 'auto']}
                                    tickFormatter={(value) => {
                                        return `$${Math.round(value).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
                                    }}
                                    stroke="rgba(255,255,255,0.2)"
                                    strokeWidth={2}
                                    tickLine={false}
                                    axisLine={true}
                                    tick={{
                                        fill: 'rgba(255,255,255,0.7)',
                                        fontSize: '10px',
                                        fontWeight: '500',
                                        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
                                    }}
                                    style={{
                                        fontSize: '10px',
                                        fill: 'rgba(255,255,255,0.7)',
                                        fontWeight: '500',
                                        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
                                    }}
                                    tickMargin={8}
                                    width={75}
                                    allowDataOverflow={false}
                                />
                                <Tooltip content={<CustomTooltip />} />
                                <Area
                                    type="monotone"
                                    dataKey="portfolio_value"
                                    stroke="var(--accent-primary)"
                                    strokeWidth={2}
                                    fillOpacity={1}
                                    fill="url(#colorValue)"
                                    isAnimationActive={true}
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                )}
            </div>
        </div>
    );
};

export default StockChart;
