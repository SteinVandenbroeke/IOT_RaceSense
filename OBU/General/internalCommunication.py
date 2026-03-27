from network import Bluetooth
import time
import _thread
import json

# Unique UUIDs so your boards only talk to each other
SERVICE_UUID = b'1234567890123456' 
CHAR_UUID = b'abcdefghijklmnop'

class InternalCommunication:
    def __init__(self, act_as_reciever=False):
        self.is_master = not act_as_reciever
        self.bluetooth = Bluetooth()
        self.char = None
        self.connected = False
        self._buffer = b''
        # This list acts as our background inbox
        self.received_data = []

        if self.is_master:
            self._setup_master()
        else:
            self._setup_slave()

    def _setup_slave(self):
        """Sets up the board as a BLE Peripheral (Slave)"""
        print("Slave: Starting advertisement...")
        self.bluetooth.set_advertisement(name='PycomSlave', service_uuid=SERVICE_UUID)
        self.bluetooth.advertise(True)
        
        # Create BLE service and characteristic
        self.srv = self.bluetooth.service(uuid=SERVICE_UUID, isprimary=True)
        self.char = self.srv.characteristic(uuid=CHAR_UUID, value='init')
        
        # BLE natively supports background listening via Callbacks. 
        # This acts like a thread without the overhead.
        self.char.callback(trigger=Bluetooth.CHAR_WRITE_EVENT, handler=self._slave_rx_callback)
        self.connected = True
        print("Slave: Ready and waiting for Master.")

    def _setup_master(self):
        """Sets up the board as a BLE Central (Master)"""
        print("Master: Scanning for Slave...")
        self.bluetooth.start_scan(-1)
        
        target_mac = None
        while not target_mac:
            adv = self.bluetooth.get_adv()
            if adv:
                # Check if the device name matches our Slave
                if self.bluetooth.resolve_adv_data(adv.data, Bluetooth.ADV_NAME_CMPL) == 'PycomSlave':
                    target_mac = adv.mac
                    break
            time.sleep(0.1)

        self.bluetooth.stop_scan()
        print("Master: Found Slave! Connecting...")
        
        self.conn = self.bluetooth.connect(target_mac)
        
        # Find the matching service and characteristic
        services = self.conn.services()
        for s in services:
            if s.uuid() == SERVICE_UUID:
                for c in s.characteristics():
                    if c.uuid() == CHAR_UUID:
                        self.char = c
                        break
        
        self.connected = True
        print("Master: Connected!")
        
        # Start a background thread to constantly poll for new data
        _thread.start_new_thread(self._master_read_thread, ())

    def _slave_rx_callback(self, chr, data):
        """Reassembles chunks sent from the Master"""
        # Unpack the tuple Pycom secretly passes us into its two parts
        events, val = data 
        
        if events & Bluetooth.CHAR_WRITE_EVENT:
            if val:
                # 1. Add the new chunk to the buffer
                self._buffer += val
                
                # 2. Check if the end marker is now at the end of our buffer
                if self._buffer.endswith(b'<EOM>'):
                    # 3. Save it to the inbox, slicing off the 5-byte '<EOM>' marker
                    self.received_data.append(self._buffer[:-5])
                    self._buffer = b'' # Clear buffer for the next message

    def _master_read_thread(self):
        """Reassembles chunks sent from the Slave"""
        last_val = b'init'
        while self.connected:
            try:
                val = self.char.read()
                if val and val != last_val:
                    # 1. Add the new chunk to the buffer
                    self._buffer += val
                    
                    # 2. Check for the end marker
                    if self._buffer.endswith(b'<EOM>'):
                        # 3. Save and strip the marker
                        self.received_data.append(self._buffer[:-5])
                        self._buffer = b'' 
                        
                    last_val = val
            except Exception:
                pass
            time.sleep(0.01) # Poll very fast so we don't miss chunks

    def write(self, data):
        """Send data in safe 20-byte chunks with backpressure handling"""
        if not self.char:
            print("Error: Not connected!")
            return
        
        # 1. Convert dict/list to JSON string
        if isinstance(data, (dict, list)):
            data = json.dumps(data)
            
        # 2. Force to bytes
        if not isinstance(data, (bytes, bytearray)):
            data = str(data).encode('utf-8')
            
        # 3. Append the End Of Message marker directly to the payload
        data += b'<EOM>'
            
        # 4. Send data in chunks of 20 bytes
        for i in range(0, len(data), 20):
            chunk = data[i:i+20]
            
            # Keep trying to send the chunk until the hardware accepts it
            chunk_sent = False
            while not chunk_sent:
                try:
                    if self.is_master:
                        self.char.write(chunk)
                    else:
                        self.char.value(chunk)
                    
                    # If we reach this line, the write succeeded!
                    chunk_sent = True 
                    
                except OSError:
                    # The BLE hardware buffer is full. 
                    # Back off for 50ms and try this exact chunk again.
                    time.sleep(0.05)
                    
            # A tiny breather before throwing the next chunk at the queue
            time.sleep(0.02)

    def read(self):
        """Pull the oldest unread message and reconstruct dictionaries"""
        if self.received_data:
            raw_bytes = self.received_data.pop(0)
            
            try:
                # Step 1: Decode bytes back to a normal string
                decoded_str = raw_bytes.decode('utf-8')
                
                # Step 2: Try to parse it back into a dictionary
                try:
                    return json.loads(decoded_str)
                except ValueError:
                    # If it wasn't a dictionary to begin with, just return the string
                    return decoded_str
                    
            except Exception:
                # If it fails completely, just hand back the raw bytes
                return raw_bytes
                
        return None