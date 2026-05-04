import paho.mqtt.client as mqtt
import websocket
import json

# --- Configuration ---
# The Mosquitto broker is running on the same Coral board
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
MQTT_TOPIC = "#"  # The '#' wildcard listens to all sub-topics

# Your Digital Ocean WebSocket endpoint
WS_URL = "wss://racesense.dcsteen.com/ws/coral"

# Initialize WebSocket connection
ws = websocket.WebSocket()


def connect_websocket():
    try:
        ws.connect(WS_URL)
        print("Connected to Digital Ocean WebSocket")
    except Exception as e:
        print(f"Failed to connect to WebSocket: {e}")


def listen_to_websocket():
    while True:
        try:
            # This waits (blocks) until a message arrives from Digital Ocean
            message = ws.recv()
            if message:
                cloud_data = json.loads(message)
                #print(f"Cloud sent: {cloud_data}")

                # Example: If cloud sends a command, forward it to MQTT
                # send_mqtt_message("commands/from_cloud", cloud_data)

        except Exception as e:
            print(f"WS Receiver Error: {e}. Reconnecting...")
            connect_websocket()

# --- MQTT Callbacks ---
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to Local Mosquitto Broker!")
        # Subscribe to the Pycom data topic
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"Failed to connect, return code {rc}")

def send_to_cloud(data: dict):
    try:
        ws.send(json.dumps(data))
        #print("Forwarded processed data to cloud.")
    except Exception as e:
        print(f"WebSocket send failed: {e}. Attempting to reconnect...")
        connect_websocket()

def on_message(client, userdata, msg):
    # 1. Receive data from Pycom
    print(msg.payload)
    raw_payload = msg.payload.decode('utf-8')
    #print(f"Received from {msg.topic}: {raw_payload}")
    printraw_payload)
    data = json.loads(raw_payload)
    print(msg.topic)

    if "sensors/OBU" in msg.topic:
        processed_data = {
            "device_topic": msg.topic,
            "processed_value": data
        }
        send_to_cloud(processed_data)
    elif "flag/OBU" in msg.topic:
        print("flag change data", data)
        input()
        #send_mqtt_message("flag/TSU", data["color"])

def send_mqtt_message(topic: str, data: str):
    mqtt_client.publish(topic, data)
    print(f"Sent command to Pycom on {topic}")


# --- Main Execution ---
if __name__ == "__main__":
    connect_websocket()

    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)

    # 1. Start MQTT in a background thread
    mqtt_client.loop_start()
    print("MQTT listening in background...")

    # 2. Use the main thread to listen for Cloud messages
    print("Starting Cloud listener...")
    listen_to_websocket()