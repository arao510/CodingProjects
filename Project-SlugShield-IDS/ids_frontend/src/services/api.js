// Helper functions to fetch data from backend rest api
const base = 'http://127.0.0.1:8080'; // Update this if backend ever updates
// const base = import.meta.env.VITE_API_BASE_URL; // Updated so now uses env variable for flexibility

// Fetch recent alerts from backend
export async function fetch_alerts(limit = 100) {
    try {
        const response = await fetch(`${base}/api/alerts?limit=${limit}`);
        const json_response = await response.json();
        // Return json response or [] if and only if field missing
        return json_response.alerts || [];
    } catch (e) {
        // Just in case of errors
        console.error('fetch_alerts error', e);
        return [];
    }
}

// Fetch icmp packet-rate statistics for charting
export async function fetch_icmp_stats(interval = 60) {
    try {
        const response = await fetch(`${base}/api/stats/icmp?interval=${interval}`);
        const json_response = await response.json();
        // Return json response or [] if and only if field missing
        return json_response.stats || [];
    } catch (e) {
        // Once again, just in case of errors
        console.error('fetch_icmp_stats error', e);
        return [];
    }
}

// Create WebSocket connection for real-time alerts and stats
export function create_alert_socket(callback) {
    const ws = new WebSocket('ws://127.0.0.1:8080/websocket/alerts');
    // const ws = new WebSocket(`${base.replace('http', 'ws')}/websocket/alerts`); // Adjusted for env variable usage
    
    ws.onmessage = (event) => {
        try {
            const message = JSON.parse(event.data);
            callback(message);
        } catch (e) {
            console.error('WebSocket message parse error', e);
        }
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error', error);
    };
    
    ws.onclose = () => {
        console.log('WebSocket connection closed');
    };
    
    return ws;
}