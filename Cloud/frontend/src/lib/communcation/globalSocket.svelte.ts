export type CornerData = {
	FL: number;
	FR: number;
	RL: number;
	RR: number;
};

export interface CarTelemetry {
	CarId?: number;
	Time?: any[];
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

	// 1. The Garage: Store telemetry for ALL active cars by their CarId
	cars = $state<Record<number, CarTelemetry>>({});

	// 2. The Selector: Which car is the dashboard currently looking at?
	selectedCarId = $state<number>(0);

	// 3. The Magic Getter: The existing UI reads this, completely unaware
	// that it's dynamically switching between different cars in the garage!
	get telemetry(): CarTelemetry {
		return this.cars[this.selectedCarId] || {};
	}

	private socket: WebSocket | null = null;
	private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

	private readonly WS_URL =
		typeof window !== 'undefined' ? `wss://${window.location.host}/ws/ui` : '';

	// Inject fake cars for UI testing
	loadDemoFleet() {
		this.cars = {
			0: { Speed: 245, TempAndHumidity: { temp: 85, humidity: 40, timestamp: [] }, RPM: 6200 },
			4: { Speed: 312, TempAndHumidity: { temp: 92, humidity: 42, timestamp: [] }, RPM: 7400 },
			7: { Speed: 0, TempAndHumidity: { temp: 60, humidity: 45, timestamp: [] }, RPM: 0 },
			99: { Speed: 180, TempAndHumidity: { temp: 78, humidity: 39, timestamp: [] }, RPM: 5000 }
		};
		this.selectedCarId = 4; // Auto-select Car 4
	}

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
				const rawMessage: IncomingPayload = JSON.parse(event.data);
				const pv = rawMessage.processed_value;

				if (pv) {
					// Extract the CarId (default to 0 if missing)
					const incomingCarId = pv.CarId ?? 0;

					// Update ONLY that specific car's data in the garage
					this.cars[incomingCarId] = {
						...this.cars[incomingCarId],
						...pv
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
