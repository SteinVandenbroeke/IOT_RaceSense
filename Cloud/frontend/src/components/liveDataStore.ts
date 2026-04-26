import { writable } from 'svelte/store';

// Define the shape of our incoming IoT data
interface SensorData {
    sensor_type: string;
    value: number;
}

// Create a writable store initialized with a default value
export const sensorData = writable<SensorData>({ sensor_type: 'waiting...', value: 0 });

export function connectWebSocket() {
    // Connect to the UI endpoint we just built
    const socket = new WebSocket('ws://localhost:8000/ws/ui');

    socket.onopen = () => {
        console.log('Connected to IoT Backend via WebSocket!');
    };

    socket.onmessage = (event) => {
        // Parse the incoming JSON data from the Coral Dev Board
        const data: SensorData = JSON.parse(event.data);
        
        // Update the Svelte store! Any component listening will instantly react.
        sensorData.set(data);
    };

    socket.onclose = () => {
        console.log('WebSocket connection closed. We should probably reconnect here!');
        // Note: We'll add auto-reconnect logic here later for extra points!
    };
}