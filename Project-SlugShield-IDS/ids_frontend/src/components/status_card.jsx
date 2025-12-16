// Display overall health of system
import React from 'react';

// Helper function that takes system status string and return object with text and colors
function get_system_health(status) {
    if (status == 'Ok') {
        return {text: 'Ok', color: '#16a34a'};
    }
    else {
        return {text: 'Alert', color: '#dc2626'};
    }
}

// Top-of-page summary card for system health
export default function StatusCard({ status = 'Ok', last_checked = null, active_alerts = []}) {
    const health = get_system_health(status);

    // Show number of active alerts
    const alerts_summary = active_alerts.length ? `${active_alerts.length} alert(s)` : 'No active alerts';

    // What the webpage will show
    return (
        <div className="status-card" style={{borderLeft: `6px solid ${health.color}`}}>
            <div className = "status-left">
                <div className = "status-health" style = {{background: health.color}}>{health.text}</div>
                <h2>System Status</h2>
                <div className = "status-sub">{alerts_summary}</div>
            </div>
            <div className="status-right">
                <div>Last checked</div>
                <div className = "timestamp">{last_checked || '-'}</div>
            </div>
        </div>
    );
}