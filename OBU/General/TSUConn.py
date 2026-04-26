from network import WLAN
import machine
import json
import time

# Import the Pycom MQTT client you just added to your lib folder
from mqtt import MQTTClient 

class TSUConn:
    def __init__(self, ssid, password):
        self.ssid = ssid
        self.password = password
        self.wlan = WLAN(mode=WLAN.STA)
        self.mqtt_client = None

    def connect_wifi(self):
        """Connects to the specified WiFi network."""
        print("Connecting to WiFi network..", self.ssid)
        self.wlan.connect(ssid=self.ssid, auth=(WLAN.WPA2, self.password))
        
        while not self.wlan.isconnected():
            time.sleep(1) 
            
        print("WiFi connected successfully")
        print("IP Configuration:", self.wlan.ifconfig())

    def connect_mqtt(self, broker_ip, client_id="pycom_sensor_1", port=1883):
        """Establishes a connection to the MQTT broker (Google Coral)."""
        if not self.wlan.isconnected():
            print("Error: Cannot connect to MQTT. WiFi is not connected.")
            self.connect_wifi()

        print("Connecting to MQTT Broker at...", broker_ip)
        try:
            # Initialize the Pycom MQTT Client
            self.mqtt_client = MQTTClient(client_id, broker_ip, port=port)
            self.mqtt_client.connect()
            print("MQTT connected successfully!")
            return True
        except Exception as e:
            print("MQTT connection failed:", e)
            return False

    def send_mqtt(self, topic, data_dict):
        """Converts a dictionary to JSON and publishes it to an MQTT topic."""
        if self.mqtt_client is None:
            print("Error: MQTT is not connected.")
            return False
            
        try:
            # 1. Convert dictionary to JSON string
            json_payload = json.dumps(data_dict)
            
            # 2. Publish to the broker
            # Note: Pycom's MQTT library handles normal strings, so we do not 
            # need to encode them to bytes like the other library required!
            self.mqtt_client.publish(topic, json_payload)
            print("Published")
            return True
            
        except Exception as e:
            print("Failed to publish MQTT message:", e)
            return False

    def disconnect(self):
        """Disconnects from MQTT and WiFi."""
        if self.mqtt_client is not None:
            try:
                self.mqtt_client.disconnect()
                print("MQTT disconnected.")
            except:
                pass
            
        if self.wlan.isconnected():
            self.wlan.disconnect()
            print("WiFi disconnected.")