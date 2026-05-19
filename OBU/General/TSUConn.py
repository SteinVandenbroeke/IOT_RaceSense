from network import WLAN
import machine
import json
import time
import time_tracker
import CarId

# Import the Pycom MQTT client you just added to your lib folder
from mqtt import MQTTClient 

class TSUConn:
    def __init__(self, ssid, password):
        self.ssid = ssid
        self.password = password
        self.wlan = WLAN(mode=WLAN.STA)
        self.mqtt_client = None
        self.bussy_sending = False
        self.topic_callbacks = {}

    def connect_wifi(self):
        """Connects to the specified WiFi network."""
        print("Connecting to WiFi network..", self.ssid)

        self.wlan.connect(ssid=self.ssid, auth=(WLAN.WPA2, self.password))
        while not self.wlan.isconnected():
            self.wlan.connect(ssid=self.ssid, auth=(WLAN.WPA2, self.password))
            for i in range(10):
                if self.wlan.isconnected():
                    break
                print(".")
                time.sleep(0.5) 
            
        print("WiFi connected successfully")
        time_tracker.get_RTCTime().sync()
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

            if self.mqtt_client is not None:
                print("Added master clallback")
                self.mqtt_client.set_callback(self._master_callback)

            return True
        except Exception as e:
            print("MQTT connection failed:", e)
            return False

    def send_mqtt(self, topic, data_dict, drop_if_bussy=False):
        """Converts a dictionary to JSON and publishes it to an MQTT topic."""
        if self.mqtt_client is None:
            print("Error: MQTT is not connected.")
            return False
        
        if drop_if_bussy and self.bussy_sending:
            return False
        elif not drop_if_bussy and self.bussy_sending:
            while self.bussy_sending:
                time.sleep(0.1)
        self.bussy_sending = True
            
        try:
            # 1. Convert dictionary to JSON string
            json_payload = json.dumps(data_dict)
            
            # 2. Publish to the broker
            # Note: Pycom's MQTT library handles normal strings, so we do not 
            # need to encode them to bytes like the other library required!
            self.mqtt_client.publish(topic + "/OBU/" + str(CarId.getCarId()), json_payload)
            #print("Published")
            self.bussy_sending = False
            return True
            
        except Exception as e:
            print("Failed to publish MQTT message:", e)
            self.bussy_sending = False
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
    
    def add_topic_callback(self, topic, callback_func):
        """Registers a specific function to run for a specific topic."""
        self.subscribe(topic=topic)
        if topic in self.topic_callbacks.keys():
            self.topic_callbacks[topic].append(callback_func)
        else:
            self.topic_callbacks[topic] = [callback_func]
        print("Registered callback for topic: " + str(topic))

    def _master_callback(self, topic, msg):
        """The single function the MQTT client actually calls."""
        # MicroPython umqtt returns topic and msg as bytes, so we decode them
        topic_str = topic.decode('utf-8')
        print("master callback")
        # Look up if we have a function assigned to this specific topic
        if topic_str in self.topic_callbacks:
            # Run the specific function, passing it the message
            for callback in self.topic_callbacks[topic_str]:
                callback(topic, msg)
        else:
            print("Message received on unhandled topi" + str(topic_str) + str(msg))

    def subscribe(self, topic):
        """Subscribes to an MQTT topic."""
        if self.mqtt_client is not None:
            self.mqtt_client.subscribe(topic)
            print("Subscribed to topic:")

    def check_messages(self):
        """Non-blocking check for incoming messages. Put this in your main loop."""
        if self.mqtt_client is not None:
            try:
                # check_msg() peeks for new data. If it finds some, it triggers the callback.
                self.mqtt_client.check_msg()
            except Exception as e:
                print("Error checking messages:", e)