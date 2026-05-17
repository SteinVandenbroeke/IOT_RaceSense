import asyncio
import json
import aiomqtt
import websockets
import cv2
import base64
import threading
import time
import vision

# --- Configuration ---
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
MQTT_TOPIC = "#"
WS_URL = "wss://racesense.dcsteen.com/ws/coral"

# Globals to share data between the camera thread and network async loop
latest_frame_b64 = None
latest_detection_status = "SCANNING" # Default state
latest_violation_b64 = None


def camera_worker():
    """Runs in a background thread so OpenCV and ML don't block the async network loop."""
    global latest_frame_b64, latest_detection_status

    print("Initializing Vision Pipeline...")
    pipeline = vision.VisionPipeline()

    print("Initializing Camera...")
    camera = cv2.VideoCapture(1, cv2.CAP_V4L2)

    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1240)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    while True:
        success, frame = camera.read()
        if success:
            # 1. Unpack the tuple from vision.py
            status, violation_frame = pipeline.process_frame(frame)
            latest_detection_status = status

            # 2. If we have a violation frame, use it! Otherwise, use the normal frame.
            frame_to_encode = violation_frame if violation_frame is not None else frame

            # 3. Boost the JPEG quality if it's a violation so the masks look sharp
            img_quality = 80 if violation_frame is not None else 40

            ret, buffer = cv2.imencode('.jpg', frame_to_encode, [cv2.IMWRITE_JPEG_QUALITY, img_quality])
            if ret:
                latest_frame_b64 = base64.b64encode(buffer).decode('utf-8')

            # 3. If a violation occurred, encode the transparent overlay!
            if violation_frame is not None:
                # You can use a higher quality for the violation snapshot since it happens rarely
                v_ret, v_buffer = cv2.imencode('.jpg', violation_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if v_ret:
                    latest_violation_b64 = base64.b64encode(v_buffer).decode('utf-8')


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
        async with mqtt_client.messages() as messages:
            async for msg in messages:
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
    global latest_frame_b64, latest_detection_status, latest_violation_b64 # <-- Add to global

    try:
        while True:
            # 1. Prioritize sending a violation image if one exists
            if latest_violation_b64:
                payload = {
                    "type": "violation_event",   # A special type your server can listen for
                    "image": latest_violation_b64,
                    "detection": "VIOLATION"
                }
                await ws.send(json.dumps(payload))
                latest_violation_b64 = None  # Clear it so we don't send it twice

            # 2. Send the normal live stream
            elif latest_frame_b64:
                payload = {
                    "type": "video_frame",
                    "image": latest_frame_b64,
                    "detection": latest_detection_status
                }
                await ws.send(json.dumps(payload))

            # Send at roughly 10 FPS
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