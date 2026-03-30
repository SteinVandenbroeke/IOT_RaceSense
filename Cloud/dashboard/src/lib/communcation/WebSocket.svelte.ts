// WebSocketModel.svelte.ts

import type { Snippet } from 'svelte';

interface TempAndHumidity {
	humidity: number;
	timestamp: number;
	temp: number;
}

interface Accelerometer {
	timestamp: number;
	roll: number;
	pitch: number;
	g_force: number;
	acceleration: [number, number, number];
}

interface PressureAndAltitude {
	altitude: number;
	timestamp: number;
	pressuere: number;
}

interface CarTelemetry {
	TempAndHumidity: TempAndHumidity;
	time: number;
	Accelerometer: Accelerometer;
	PressureAndAltitude: PressureAndAltitude;
}

export class WebSocketModel<T = any> {
	private ws: WebSocket | null = null;
	private url: string;

	// Using Svelte 5 runes for reactive state
	current_data = $state<CarTelemetry>({
		TempAndHumidity: { humidity: 32.78403, timestamp: 854600, temp: 30.0275 },
		time: 854754,
		Accelerometer: {
			timestamp: 854733,
			roll: -0.4598613,
			pitch: -4.893205,
			g_force: 1.007488,
			acceleration: [0.008056641, 0.0859375, 1.003784]
		},
		PressureAndAltitude: { altitude: -63.0, timestamp: 854721, pressuere: 261892.0 }
	});
	messages = $state<T[]>([]);
	isConnected = $state(false);
	error = $state<string | null>(null);

	constructor(url: string) {
		this.url = url;
	}

	/** Opens the connection and sets up listeners */
	connect() {
		if (this.ws) return; // Prevent multiple connections

		this.ws = new WebSocket(this.url);

		this.ws.onopen = () => {
			this.isConnected = true;
			this.error = null;
		};

		this.ws.onmessage = (event) => {
			try {
				// Try parsing as JSON first
				const parsedData = JSON.parse(event.data);
				// In Svelte 5, state arrays are deeply reactive, so .push() triggers UI updates
				this.messages.push(parsedData);
				this.current_data = parsedData;
			} catch (e) {
				// Fallback for plain text messages
				this.messages.push(event.data);
			}
		};

		this.ws.onclose = () => {
			this.isConnected = false;
			this.ws = null;
		};

		this.ws.onerror = (err) => {
			this.error = 'A WebSocket error occurred.';
		};
	}

	/** Sends a payload to the server */
	send(data: any) {
		if (this.ws && this.isConnected) {
			const payload = typeof data === 'string' ? data : JSON.stringify(data);
			this.ws.send(payload);
		} else {
			console.warn('Cannot send message: WebSocket is not connected.');
		}
	}

	/** Closes the connection cleanly */
	disconnect() {
		if (this.ws) {
			this.ws.close();
			this.ws = null;
		}
	}
}