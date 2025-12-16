// Handles real time data updates through websocket connection
export function create_alert_socket(on_message) {
    const url = 'ws://127.0.0.1:8080/websocket/alerts';
    // const url = `${import.meta.env.VITE_API_BASE_URL.replace('http', 'ws')}/websocket/alerts`; // use env variable for flexibility
    let websocket = new WebSocket(url); // create new websocket connection to the endpoint of the fastapi above

    // Connection success
    websocket.onopen = () => {
        console.log('websocket connected');
    };

    // Handle messages received from server
    websocket.onmessage = (evt) => {
        try {
            // Parse the raw message string sent from backend
            const data = JSON.parse(evt.data);
            // Call user callback with parsed message
            on_message(data)
        } catch (e) {
            // Error in parsing 
            console.error('websocket parsing error:', e);
        }
    };

    // When connection closes -> log connection closed and reason as well as trying reconnecting
    websocket.onclose = (e) => {
        console.log('websocket closed, reconnecting in 2 seconds', e.reason);
        setTimeout(() => create_alert_socket(on_message), 2000);
    };

    // Runtime errors during connection
    websocket.onerror = (err) => {
        console.error('websocket error', err);
        websocket.close();
    };

    return websocket;
}