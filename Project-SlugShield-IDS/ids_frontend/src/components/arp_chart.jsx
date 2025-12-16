// Renders live ARP spoofing detection chart with modern dark theme
import React from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from 'recharts';

export default function ArpChart({ stats = [], baseline = [] }) {
    // Filter stats for ARP spoofing attempts only
    const arpStats = stats.filter(s => s.metric === "arp_spoofing_attempts_per_second");

    // Map to chart points
    const points = arpStats.map(s => ({
        time: new Date(s.timestamp * 1000).toLocaleTimeString(),
        value: s.value
    }));

    // Map baseline values (rolling average)
    const baselineMap = new Map(
        baseline.map(b => [new Date(b.timestamp * 1000).toLocaleTimeString(), b.value])
    );

    const data = points.map(p => ({
        ...p,
        baseline: baselineMap.get(p.time) ?? null
    }));

    // Calculate current and baseline values for display
    const currentValue = points.length > 0 ? points[points.length - 1].value : 0;
    const baselineValue = baseline.length > 0 ? baseline[baseline.length - 1].value : 0;

    // Custom tooltip styling
    const CustomTooltip = ({ active, payload }) => {
        if (active && payload && payload.length) {
            return (
                <div style={{
                    backgroundColor: '#2a2a2a',
                    border: '1px solid #444',
                    padding: '10px',
                    borderRadius: '6px'
                }}>
                    <p style={{ color: '#fff', fontSize: '12px', margin: '0 0 4px 0' }}>
                        {payload[0].payload.time}
                    </p>
                    {payload.map((entry, index) => (
                        <p key={index} style={{ 
                            color: entry.color, 
                            fontSize: '12px', 
                            margin: '2px 0' 
                        }}>
                            {entry.name}: {entry.value?.toFixed(2)} attempts/s
                        </p>
                    ))}
                </div>
            );
        }
        return null;
    };

    return (
        <div className="chart-card">
            <div className="chart-header">
                <div className="chart-title">
                    <div className="chart-indicator"></div>
                    ARP Spoofing Detection
                </div>
                <div className="chart-stats">
                    <div className="stat-item">
                        <strong>Current:</strong> {currentValue?.toFixed(1)} attempts/s
                    </div>
                    <div className="stat-item">
                        <strong>Baseline:</strong> {baselineValue?.toFixed(1)} attempts/s
                    </div>
                </div>
            </div>
            
            <div className="chart-container">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={data} margin={{ top: 5, right: 5, left: 0, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                        <XAxis 
                            dataKey="time" 
                            minTickGap={30}
                            stroke="#888"
                            style={{ fontSize: '11px' }}
                        />
                        <YAxis 
                            stroke="#888"
                            style={{ fontSize: '11px' }}
                        />
                        <Tooltip content={<CustomTooltip />} />
                        <Line
                            type="monotone"
                            dataKey="value"
                            stroke="#4CAF50"
                            strokeWidth={2}
                            dot={false}
                            isAnimationActive={false}
                            name="Attempts/s"
                        />
                        <Line
                            type="monotone"
                            dataKey="baseline"
                            stroke="#FF9800"
                            strokeWidth={2}
                            dot={false}
                            strokeDasharray="5 5"
                            isAnimationActive={false}
                            name="Baseline"
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>

            <div className="chart-legend">
                <div className="legend-item">
                    <div className="legend-color green"></div>
                    Attempts/Second
                </div>
                <div className="legend-item">
                    <div className="legend-color orange"></div>
                    Baseline (Rolling Avg)
                </div>
            </div>
        </div>
    );
}