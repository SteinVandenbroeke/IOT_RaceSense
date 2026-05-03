// src/lib/state/socket.svelte.ts
import { WebSocketModel } from '$lib/communcation/WebSocket.svelte';

// We create ONE instance here and export it.
// Every component that imports 'globalSocket' will share this exact same connection.

export interface SensorPayload {
    sensor_type: string;
    value: number;
    timestamp?: string;
}

class GlobalSocket {
    isConnected = $state(false);
    
    // NEW: A dictionary holding the latest value for every sensor type
    telemetry = $state<Record<string, number>>({
        wheel_speed: 0,
        engine_rpm: 0,
        track_temp: 0,
        g_force_x: 0,
        g_force_y: 0,
        g_force_z: 0,
        roll: 0,
        pitch: 0,
    });
    
    private socket: WebSocket | null = null;
    private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    
    // Remember to use your actual domain here if you aren't using a relative path!
    // Since we are using Caddy, a relative path is safest so it works locally and on the server.
    private readonly WS_URL = typeof window !== 'undefined' 
        ? `wss://${window.location.host}/ws/ui` 
        : '';

    connect() {
        if (typeof window === 'undefined') return; 
        if (this.socket?.readyState === WebSocket.OPEN) return;

        this.socket = new WebSocket(this.WS_URL);

        this.socket.onopen = () => {
            this.isConnected = true;
            if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
        };

        this.socket.onmessage = (event) => {
            try {
                const payload: SensorPayload = JSON.parse(event.data);
                
                // Dynamically update the specific sensor key
                if (payload.sensor_type) {
                    this.telemetry[payload.sensor_type] = payload.value;
                }
            } catch (error) {
                console.error("Failed to parse sensor data:", error);
            }
        };

        this.socket.onclose = () => {
            this.isConnected = false;
            this.scheduleReconnect();
        };
    }

    disconnect() {
        if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
    }

    private scheduleReconnect() {
        if (this.reconnectTimer) return; // Already scheduling
        console.log('Retrying in 3 seconds...');
        this.reconnectTimer = setTimeout(() => {
            this.reconnectTimer = null;
            this.connect();
        }, 3000);
    }
}

// Export a single instance to share across the entire app
export const globalSocket = new GlobalSocket();