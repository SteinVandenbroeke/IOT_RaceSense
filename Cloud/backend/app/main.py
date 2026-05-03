import os
import json
import asyncpg
import asyncio  # Added missing asyncio import for your retry loop!
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

# --- Database Setup ---
DB_URL = os.getenv("DATABASE_URL")


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Attempting to connect to PostgreSQL...")
    for _ in range(5):
        try:
            app.state.db_pool = await asyncpg.create_pool(DB_URL)
            print("Successfully connected to the database!")
            break
        except Exception as e:
            print(f"Database not ready yet, retrying in 2 seconds... ({e})")
            await asyncio.sleep(2)
    else:
        raise Exception("Failed to connect to the database after 5 attempts.")

    async with app.state.db_pool.acquire() as connection:
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS telemetry_raw
            (
                id          SERIAL PRIMARY KEY,
                payload     JSONB,
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    yield
    await app.state.db_pool.close()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Since you are in hardware testing, open CORS up entirely for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- WebSocket Connection Manager ---
class ConnectionManager:
    def __init__(self):
        self.active_ui_connections: list[WebSocket] = []

    async def connect_ui(self, websocket: WebSocket):
        await websocket.accept()
        self.active_ui_connections.append(websocket)

    def disconnect_ui(self, websocket: WebSocket):
        self.active_ui_connections.remove(websocket)

    async def broadcast_to_ui(self, message: str):
        for connection in self.active_ui_connections:
            await connection.send_text(message)


manager = ConnectionManager()


# --- Helper: Convert Pycom RTC to Standard ISO Time ---
def pycom_rtc_to_iso(rtc_array):
    """Converts a Pycom RTC array like [2026, 5, 3, 18, 47, 48, 383241, null] into an ISO string."""
    if isinstance(rtc_array, list) and len(rtc_array) >= 7:
        try:
            dt = datetime(
                year=rtc_array[0],
                month=rtc_array[1],
                day=rtc_array[2],
                hour=rtc_array[3],
                minute=rtc_array[4],
                second=rtc_array[5],
                microsecond=rtc_array[6],
                tzinfo=timezone.utc
            )
            return dt.isoformat()
        except Exception:
            pass
    return rtc_array


# --- Endpoints ---

@app.websocket("/ws/ui")
async def websocket_ui_endpoint(websocket: WebSocket):
    await manager.connect_ui(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_ui(websocket)


@app.websocket("/ws/coral")
async def websocket_coral_endpoint(websocket: WebSocket):
    """Endpoint for the Coral Dev Board to push data."""
    await websocket.accept()
    pool = app.state.db_pool

    try:
        while True:
            data_text = await websocket.receive_text()
            payload = json.loads(data_text)

            # --- 1. DATA CLEANUP ---
            # Intercept the payload and fix the Pycom array timestamps
            if "processed_value" in payload:
                pv = payload["processed_value"]

                # Fix global time
                if "time" in pv:
                    pv["time"] = pycom_rtc_to_iso(pv["time"])

                # Fix all sensor sub-timestamps
                for sensor in ["TempAndHumidity", "Accelerometer", "PressureAndAltitude"]:
                    if sensor in pv and "timestamp" in pv[sensor]:
                        pv[sensor]["timestamp"] = pycom_rtc_to_iso(pv[sensor]["timestamp"])

            # Re-serialize the cleaned dictionary back into a JSON string
            clean_data_text = json.dumps(payload)

            # --- 2. DATABASE ---
            # Save the CLEANED payload directly into PostgreSQL as JSONB
            async with pool.acquire() as connection:
                await connection.execute(
                    "INSERT INTO telemetry_raw (payload) VALUES ($1::jsonb)",
                    clean_data_text
                )

            # --- 3. BROADCAST ---
            # Forward the standard, clean JSON to the UI
            await manager.broadcast_to_ui(clean_data_text)

    except WebSocketDisconnect:
        print("Coral Dev Board disconnected.")
    except Exception as e:
        print(f"Error processing message: {e}")