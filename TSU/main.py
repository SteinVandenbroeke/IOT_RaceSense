import paho.mqtt.client as mqtt
import websocket
import json

# --- Configuration ---
# The Mosquitto broker is running on the same Coral board
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
MQTT_TOPIC = "sensors/pycom/#"  # The '#' wildcard listens to all sub-topics

# Your Digital Ocean WebSocket endpoint
WS_URL = "ws://racesense.dcsteen.com:6969/ws"

# Initialize WebSocket connection
ws = websocket.WebSocket()


def connect_websocket():
    try:
        ws.connect(WS_URL)
        print("Connected to Digital Ocean WebSocket")
    except Exception as e:
        print(f"Failed to connect to WebSocket: {e}")


# --- MQTT Callbacks ---
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to Local Mosquitto Broker!")
        # Subscribe to the Pycom data topic
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"Failed to connect, return code {rc}")


def on_message(client, userdata, msg):
    # 1. Receive data from Pycom
    raw_payload = msg.payload.decode('utf-8')
    print(f"Received from {msg.topic}: {raw_payload}")

    # 2. PROCESS DATA HERE (e.g., Edge TPU inference, math, formatting)
    # Example: Let's assume we just wrap it in a JSON object for now
    processed_data = {
        "device_topic": msg.topic,
        "processed_value": raw_payload,
        "status": "verified_by_coral"
    }

    # 3. Send processed data to Digital Ocean via WebSocket
    try:
        ws.send(json.dumps(processed_data))
        print("Forwarded processed data to cloud.")
    except Exception as e:
        print(f"WebSocket send failed: {e}. Attempting to reconnect...")
        connect_websocket()


# --- Main Execution ---
if __name__ == "__main__":
    connect_websocket()

    # Set up the MQTT Client
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    # Connect to the local broker and start listening
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)

    print("Starting Coral Edge Processor...")
    # This keeps the script running forever, listening for incoming Pycom messages
    mqtt_client.loop_forever()