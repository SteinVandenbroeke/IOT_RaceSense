// src/lib/state/socket.svelte.ts

export interface CarTelemetry {
	VirtualTime?: { rtc_time: any[]; timestamp: number };
	Accelerometer?: {
		timestamp: number;
		roll: number;
		pitch: number;
		g_force: number;
		acceleration: number[]; // [x, y, z]
	};
	PressureAndAltitude?: { altitude: number; timestamp: number; pressure: number };
	TempAndHumidity?: { humidity: number; timestamp: number; temp: number };
	time?: number;
	// We add these back as optional in case you still want to mock them later
	Speed?: number;
	RPM?: number;
}

class GlobalSocket {
	isConnected = $state(false);
	telemetry = $state<CarTelemetry>({});

	private socket: WebSocket | null = null;
	private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

	private readonly WS_URL =
		typeof window !== 'undefined' ? `wss://${window.location.host}/ws/ui` : '';

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
				const payload: CarTelemetry = JSON.parse(event.data);
				console.log('LIVE DATA:', payload);

				this.telemetry = {
					...this.telemetry,
					...payload
				};
			} catch (error) {
				console.error('Failed to parse sensor data:', error);
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
		if (this.reconnectTimer) return;
		console.log('Connection lost. Retrying in 3 seconds...');
		this.reconnectTimer = setTimeout(() => {
			this.reconnectTimer = null;
			this.connect();
		}, 3000);
	}
}

export const globalSocket = new GlobalSocket();
