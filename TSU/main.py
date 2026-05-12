import asyncio
import json
import aiomqtt
import websockets

# --- Configuration ---
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
MQTT_TOPIC = "#"

WS_URL = "wss://racesense.dcsteen.com/ws/coral"


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

async def main():
    """Main loop handling connections and automatic reconnections."""
    while True:
        try:
            print(f"Connecting to WebSocket at {WS_URL}...")
            async with websockets.connect(WS_URL) as ws:
                print("Connected to Digital Ocean WebSocket!")

                print(f"Connecting to MQTT Broker at {MQTT_BROKER}...")
                async with aiomqtt.Client(MQTT_BROKER, port=MQTT_PORT) as mqtt_client:
                    print("Connected to Local Mosquitto Broker!")
                    await mqtt_client.subscribe(MQTT_TOPIC)

                    # Create concurrent tasks for both listeners
                    ws_task = asyncio.create_task(listen_to_ws(ws, mqtt_client))
                    mqtt_task = asyncio.create_task(listen_to_mqtt(ws, mqtt_client))

                    # Run both tasks until ONE of them finishes/fails (e.g., a connection drops)
                    done, pending = await asyncio.wait(
                        [ws_task, mqtt_task],
                        return_when=asyncio.FIRST_COMPLETED
                    )

                    # If one connection drops, cancel the other task so we can cleanly restart both
                    for task in pending:
                        task.cancel()

        except (websockets.exceptions.WebSocketException, aiomqtt.MqttError, OSError) as e:
            print(f"Connection dropped/failed: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

        print("Reconnecting in 5 seconds...\n")
        await asyncio.sleep(5)


# --- Main Execution ---
if __name__ == "__main__":
    # Gracefully handle KeyboardInterrupt (Ctrl+C)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")