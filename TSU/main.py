import asyncio
import json
import aiomqtt
import websockets
import cv2
import base64
import threading
import time

# --- Configuration ---
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
MQTT_TOPIC = "#"

WS_URL = "wss://racesense.dcsteen.com/ws/coral"

latest_frame_b64 = None

def camera_worker():
    """Runs in a background thread so OpenCV doesn't block the async network loop."""
    global latest_frame_b64

    print("Initializing Camera...")
    # NOTE: If this gives you a white screen, change `0` to `gstreamer_pipeline, cv2.CAP_GSTREAMER`
    camera = cv2.VideoCapture(0)

    # Optional: Lower resolution to save bandwidth
    # camera.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    # camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

    while True:
        success, frame = camera.read()
        if success:
            # Compress the image to JPEG.
            # We lower the quality to 50% to prevent lagging out the WebSocket
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
            if ret:
                # Convert the raw bytes to a base64 string so it can be sent in JSON
                latest_frame_b64 = base64.b64encode(buffer).decode('utf-8')

        # Small sleep to prevent maxing out the CPU
        time.sleep(0.03)

    # --- WebSocket & MQTT Listeners ---


async def listen_to_ws(ws, mqtt_client):
    """Listens for incoming messages from the Digital Ocean WebSocket."""
    try:
        async for message in ws:
            cloud_data = json.loads(message)
            print(f"Cloud sent: {cloud_data}")


            if cloud_data['type'] == 'flag_change':
                await mqtt_client.publish("flag/TSU", payload=cloud_data["color"].upper())
            # Example: Forward cloud command to MQTT
            # await mqtt_client.publish("commands/from_cloud", payload=json.dumps(cloud_data))

    except websockets.exceptions.ConnectionClosed:
        print("WebSocket connection closed from the server.")
    except Exception as e:
        print(f"WS Receiver Error: {e}")


async def listen_to_mqtt(ws, mqtt_client):
    """Listens for incoming MQTT messages and forwards them to the WebSocket."""
    try:
        # FIX: In recent versions of aiomqtt, .messages is an async iterator property, not a method.
        # No need for the "async with" block here anymore.
        async for msg in mqtt_client.messages:
            raw_payload = msg.payload.decode('utf-8')
            topic = str(msg.topic)  # Convert aiomqtt Topic object to string

            try:
                data = json.loads(raw_payload)
            except json.JSONDecodeError:
                print(f"Failed to read JSON data on {topic}: {raw_payload}")
                continue

            if "flag/OBU" in topic:
                print("flag change data:", data)
                # Use await to safely publish back to MQTT
                color = (data.get("color", "")).upper()
                await mqtt_client.publish("flag/TSU", payload=color)
                processed_data = {
                    "type": "flag_change",
                    "color": color.title()
                }
                await ws.send(json.dumps(processed_data))
                print(f"Sent command to Pycom on flag/TSU")

            elif "sensors/OBU" in topic:
                #print(f"--> Forwarding sensor data from {topic}: {data}")
                processed_data = {
                    "device_topic": topic,
                    "processed_value": data
                }
                # Use await to safely send to the WebSocket
                await ws.send(json.dumps(processed_data))

    except websockets.exceptions.ConnectionClosed:
        print("WebSocket disconnected while trying to send data.")
    except Exception as e:
        print(f"MQTT Listener Error: {e}")


async def stream_camera_to_ws(ws):
    """Periodically grabs the latest camera frame and sends it to the cloud."""
    global latest_frame_b64

    vision_states = ["SCANNING", "CLEAR", "VIOLATION"]
    current_state_idx = 0
    last_switch_time = time.time()

    try:
        while True:
            if time.time() - last_switch_time > 3:
                current_state_idx = (current_state_idx + 1) % 3
                last_switch_time = time.time()

            if latest_frame_b64:
                payload = {
                    "type": "video_frame",
                    "image": latest_frame_b64,
                    "detection": vision_states[current_state_idx]
                }
                await ws.send(json.dumps(payload))

            # Send at roughly 10 FPS (0.1s delay) to avoid flooding the server
            await asyncio.sleep(0.1)

    except websockets.exceptions.ConnectionClosed:
        print("WebSocket disconnected while trying to send Video data.")
    except Exception as e:
        print(f"Camera Streamer Error: {e}")


async def main():
    # Start the camera thread BEFORE we start the network loop
    threading.Thread(target=camera_worker, daemon=True).start()

    while True:
        try:
            print(f"Connecting to WebSocket at {WS_URL}...")
            async with websockets.connect(WS_URL, max_size=None) as ws:
                print("Connected to Digital Ocean WebSocket!")

                print(f"Connecting to MQTT Broker at {MQTT_BROKER}...")
                async with aiomqtt.Client(MQTT_BROKER, port=MQTT_PORT) as mqtt_client:
                    print("Connected to Local Mosquitto Broker!")
                    await mqtt_client.subscribe(MQTT_TOPIC)

                    # Now we have THREE tasks running simultaneously
                    ws_task = asyncio.create_task(listen_to_ws(ws, mqtt_client))
                    mqtt_task = asyncio.create_task(listen_to_mqtt(ws, mqtt_client))
                    cam_task = asyncio.create_task(stream_camera_to_ws(ws))

                    done, pending = await asyncio.wait(
                        [ws_task, mqtt_task, cam_task],
                        return_when=asyncio.FIRST_COMPLETED
                    )

                    # If one connection drops, cancel the other task so we can cleanly restart both
                    for task in pending:
                        task.cancel()

        except Exception as e:
            print(f"Connection dropped/failed: {e}")

        print("Reconnecting in 5 seconds...\n")
        await asyncio.sleep(5)


# --- Main Execution ---
if __name__ == "__main__":
    # Gracefully handle KeyboardInterrupt (Ctrl+C)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")