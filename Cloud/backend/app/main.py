import os
import json
import asyncpg
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query

# --- Database Setup ---
DB_URL = os.getenv("DATABASE_URL")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create a database connection pool with a retry mechanism
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
    
    # Initialize your table if it doesn't exist
    async with app.state.db_pool.acquire() as connection:
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS sensor_data (
                id SERIAL PRIMARY KEY,
                sensor_type VARCHAR(50),
                value FLOAT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    yield
    # Shutdown: Close the pool
    await app.state.db_pool.close()

app = FastAPI(lifespan=lifespan)

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

# --- Security Dependency ---
CORAL_TOKEN = os.getenv("CORAL_SECRET_TOKEN")

def verify_coral_token(token: str = Query(...)):
    if token != CORAL_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid authentication token")
    return token

# --- Endpoints ---

@app.websocket("/ws/ui")
async def websocket_ui_endpoint(websocket: WebSocket):
    """Endpoint for the Dashboard UI to listen to live data."""
    await manager.connect_ui(websocket)
    try:
        while True:
            # Keep connection open and wait for UI to send heartbeat/commands
            data = await websocket.receive_text()
            # You can handle UI commands here
    except WebSocketDisconnect:
        manager.disconnect_ui(websocket)


@app.websocket("/ws/coral")
async def websocket_coral_endpoint(websocket: WebSocket, token: str = Query(...)):
    """Endpoint for the Coral Dev Board to push data."""
    # Basic Authentication check
    if token != CORAL_TOKEN:
        await websocket.close(code=1008) # Policy Violation
        return

    await websocket.accept()
    pool = app.state.db_pool

    try:
        while True:
            # Receive data from Coral (assuming JSON)
            data_text = await websocket.receive_text()
            payload = json.loads(data_text)
            
            # 1. Save to PostgreSQL using raw SQL
            async with pool.acquire() as connection:
                await connection.execute(
                    "INSERT INTO sensor_data (sensor_type, value) VALUES ($1, $2)",
                    payload.get("sensor_type", "unknown"),
                    payload.get("value", 0.0)
                )

            # 2. Forward data to any listening UI clients
            await manager.broadcast_to_ui(data_text)

    except WebSocketDisconnect:
        print("Coral Dev Board disconnected.")