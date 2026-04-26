import asyncio
import websockets
import json

# Notice the token in the URL! This matches your docker-compose environment variable.
URI = "ws://localhost:8000/ws/coral?token=coral_secure_123"

async def simulate_coral():
    print(f"Connecting to {URI}...")
    try:
        async with websockets.connect(URI) as websocket:
            print("Connected! Sending fake sensor data...")
            
            # Create a fake payload that matches what your backend expects
            payload = {
                "sensor_type": "wheel_speed",
                "value": 125.5
            }
            
            # Send the data
            await websocket.send(json.dumps(payload))
            print(f"Sent: {payload}")
            
            # Keep connection open for a moment to ensure it processes
            await asyncio.sleep(2)
            print("Closing connection.")
            
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(simulate_coral())