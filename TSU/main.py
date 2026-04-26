from typing import Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.cars: list[WebSocket] = []
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast_str(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

    async def broadcast_json(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)


manager = ConnectionManager()

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

@app.post("/postCar")
async def receive_data(payload: Dict[str, Any]):
    """
    Receives a JSON payload (dictionary) from the Pycom board.
    """
    # print("--- New Data Received ---")
    # print("Payload:", payload)
    # print("-------------------------")
    await manager.broadcast_json(payload)

    # You can process your data here (save to database, trigger events, etc.)

    # The dictionary you return here will automatically be converted to JSON
    # and sent back to the Pycom board as the HTTP response.
    return {"status": "success", "message": "Data received perfectly!"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print(websocket)
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            #await manager.send_personal_message(f"You wrote: {data}", websocket)
            print(data)
            await manager.broadcast(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client # left the chat")