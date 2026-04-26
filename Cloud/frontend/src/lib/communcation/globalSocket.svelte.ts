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
    // Svelte 5 reactive state
    isConnected = $state(false);
    latestData = $state<SensorPayload | null>(null);
    
    private socket: WebSocket | null = null;
    private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    private readonly WS_URL = 'ws://localhost/ws/ui';
    
    connect() {
        // Prevent SSR execution
        if (typeof window === 'undefined') return; 
        
        // Don't open multiple connections
        if (this.socket?.readyState === WebSocket.OPEN) return;

        console.log(`Attempting connection to ${this.WS_URL}...`);
        this.socket = new WebSocket(this.WS_URL);

        this.socket.onopen = () => {
            console.log('✅ Connected to IoT Backend');
            this.isConnected = true;
            if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
        };

        this.socket.onmessage = (event) => {
            try {
                // Parse the incoming string from FastAPI
                const payload: SensorPayload = JSON.parse(event.data);
                
                // Update our reactive state. Any Svelte component looking 
                // at `globalSocket.latestData` will instantly re-render!
                this.latestData = payload;
            } catch (error) {
                console.error("Failed to parse sensor data:", error);
            }
        };

        this.socket.onclose = () => {
            console.log('❌ Disconnected from backend.');
            this.isConnected = false;
            this.scheduleReconnect();
        };

        this.socket.onerror = (error) => {
            console.error('WebSocket Error:', error);
            this.socket?.close(); // Force close to trigger the onclose/reconnect logic
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