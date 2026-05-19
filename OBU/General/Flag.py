import pycom
import CarId

class Flag():
    def __init__(self, conn):
        self.conn = conn
        self.conn.add_topic_callback("flag/TSU", self.flag_received)

        pycom.heartbeat(False)
        self.flag_color = "-"

    def check(self):
        self.conn.check_messages()

    def get_flag(self):
        return self.flag_color
    
    def get_hex_color(self):
        if self.flag_color == "RED":
            return 0xFF0000
        elif self.flag_color == "YELLOW":
            return 0xf7ef09
        elif self.flag_color == "GREEN":
            return 0x00FF00
        return 0xF0F0F0

    def set_flag(self, color):
        if color != "RED" or color != "GREEN" or color != "YELLOW":
            assert ValueError("Not a valid color, color should be 'RED', 'GREEN', 'YELLOW'")
        data = {"car": CarId.getCarId(), "color": color}
        self.conn.send_mqtt(topic="flag", data_dict=data)
        self.flag_color = color

    def flag_received(self, topic, msg):
        # Decode the bytes into normal strings
        print("flag incomming")
        decoded_topic = topic.decode('utf-8')
        if "flag/" not in decoded_topic:
            return
        
        decoded_msg = msg.decode('utf-8')
        
        print("\n--- INCOMING DIRECTIVE ---")
        print("Topic:" + str(decoded_topic))
        print("FLAG STATUS:" + str(decoded_msg))
        print("--------------------------\n")
        
        # Example logic: Change an LED or set a speed limit based on the flag
        if decoded_msg == "RED":
            pycom.rgbled(0xFF0000)
            print("ACTION: Stopping car!")
            self.flag_color = "RED"
        elif decoded_msg == "YELLOW":
            pycom.rgbled(0xf7ef09)
            print("ACTION: Slowing down!")
            self.flag_color = "YELLOW"
        elif decoded_msg == "GREEN":
            pycom.rgbled(0x00FF00)
            print("ACTION: Full speed permitted!")
            self.flag_color = "GREEN"