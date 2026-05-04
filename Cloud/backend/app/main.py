import os
import json
import asyncpg
import asyncio
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

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
        #. Create the Sessions table
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS sessions(
                id SERIAL PRIMARY KEY,
                status VARCHAR(20) DEFAULT 'Active',
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        #. Create the Upgraded Telemetry table (now linked to sessions and cars)
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS telemetry_raw (
                id SERIAL PRIMARY KEY,
                session_id INTEGER REFERENCES sessions(id),
                car_id INTEGER,
                payload JSONB,
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    yield
    await app.state.db_pool.close()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

def pycom_rtc_to_iso(rtc_array):
    if isinstance(rtc_array, list) and len(rtc_array) >= 7:
        try:
            dt = datetime(
                year=rtc_array[0], month=rtc_array[1], day=rtc_array[2],
                hour=rtc_array[3], minute=rtc_array[4], second=rtc_array[5],
                microsecond=rtc_array[6], tzinfo=timezone.utc
            )
            return dt.isoformat()
        except Exception:
            pass
    return rtc_array


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
    await websocket.accept()
    pool = app.state.db_pool

    try:
        while True:
            data_text = await websocket.receive_text()
            payload = json.loads(data_text)
            car_id = 0 # Default fallback

            if "processed_value" in payload:
                pv = payload["processed_value"]
                # Extract CarId from the payload
                car_id = pv.get("CarId", 0)

                # Fix timestamps
                if "time" in pv: pv["time"] = pycom_rtc_to_iso(pv["time"])
                for sensor in ["TempAndHumidity", "Accelerometer", "PressureAndAltitude"]:
                    if sensor in pv and "timestamp" in pv[sensor]:
                        pv[sensor]["timestamp"] = pycom_rtc_to_iso(pv[sensor]["timestamp"])

            clean_data_text = json.dumps(payload)

            # --- DATABASE TRANSACTIONS ---
            async with pool.acquire() as connection:
                #. Check for stale sessions (1 minute timeout)
                await connection.execute("""
                    UPDATE sessions 
                    SET status = 'Completed' 
                    WHERE status = 'Active' AND last_activity < NOW() - INTERVAL '1 minute'
                """)

                #. Find the current Active session
                session_row = await connection.fetchrow("""
                    SELECT id FROM sessions WHERE status = 'Active' LIMIT 1
                """)

                if not session_row:
                    # Create a brand new session!
                    session_id = await connection.fetchval("""
                        INSERT INTO sessions (status) VALUES ('Active') RETURNING id
                    """)
                    print(f"New Session Started: {session_id}")
                else:
                    session_id = session_row['id']
                    # Keep the session alive
                    await connection.execute("""
                        UPDATE sessions SET last_activity = NOW() WHERE id = $1
                    """, session_id)

                #. Save the telemetry with foreign keys
                await connection.execute("""
                    INSERT INTO telemetry_raw (session_id, car_id, payload) 
                    VALUES ($1, $2, $3::jsonb)
                """, session_id, car_id, clean_data_text)

            # --- BROADCAST ---
            await manager.broadcast_to_ui(clean_data_text)

    except WebSocketDisconnect:
        print("Coral Dev Board disconnected.")
    except Exception as e:
        print(f"Error processing message: {e}")