export type CornerData = {
	FL: number;
	FR: number;
	RL: number;
	RR: number;
};

export interface CarTelemetry {
	time?: any[];
	Accelerometer?: {
		timestamp: any[];
		roll: number;
		pitch: number;
		g_force: number;
		acceleration: number[];
	};
	PressureAndAltitude?: {
		altitude: number;
		timestamp: any[];
		pressure: number;
	};
	TempAndHumidity?: {
		humidity: number;
		timestamp: any[];
		temp: number;
	};
	Speed?: CornerData | number;
	RPM?: number;
}

// 2. Define the new outer wrapper that the Coral is sending
interface IncomingPayload {
	device_topic?: string;
	processed_value?: CarTelemetry;
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
				// 1. Parse the incoming JSON
				const rawMessage: IncomingPayload = JSON.parse(event.data);

				// 2. Measure Latency (if the time property exists)
				const timeVal = rawMessage.processed_value?.time;
				if (typeof timeVal === 'string') {
					const messageTime = new Date(timeVal).getTime(); // Time the sensor took the reading
					const browserTime = Date.now(); // Exact time right now
					const latencyMs = browserTime - messageTime;

					console.log(`⏱️ Latency: ${latencyMs}ms | Data:`, rawMessage.processed_value);
				} else {
					console.log('RAW MESSAGE:', rawMessage);
				}

				// 3. Feed the UI
				if (rawMessage.processed_value) {
					this.telemetry = {
						...this.telemetry,
						...rawMessage.processed_value
					};
				}
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
