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

	position?: number;
	gapToAhead?: string;
	gapToLeader?: string;
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
			4: { position: 1, gapToAhead: 'Leader', gapToLeader: 'Leader' },
			7: { position: 2, gapToAhead: '+1.204', gapToLeader: '+1.204' },
			0: { position: 3, gapToAhead: '+0.850', gapToLeader: '+2.054' },
			99: { position: 4, gapToAhead: '+4.100', gapToLeader: '+6.154' },
			12: { position: 5, gapToAhead: '+0.300', gapToLeader: '+6.454' },
			33: { position: 6, gapToAhead: '+1.100', gapToLeader: '+7.554' },
			55: { position: 7, gapToAhead: '+0.500', gapToLeader: '+8.054' },
			8: { position: 8, gapToAhead: '+2.200', gapToLeader: '+10.254' },
			42: { position: 9, gapToAhead: '+1.150', gapToLeader: '+11.404' },
			23: { position: 10, gapToAhead: '+5.000', gapToLeader: '+16.404' }
		};
		this.selectedCarId = 4;
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
