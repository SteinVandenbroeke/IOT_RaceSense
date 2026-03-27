import time
from LIS2HH12 import LIS2HH12
from SI7006A20 import SI7006A20
from MPL3115A2 import MPL3115A2, ALTITUDE, PRESSURE
import _thread
import math
from .Sensor import Sensor
import time_tracker
import struct

class VirtualPyCom(Sensor):
    def __init__(self, pycoproc, comm):
        self.name = "VirtualPyCom"
        self.comm = comm

    def get(self):
        msg = self.comm.read()
        print('msg', self.decode_efficient_bytes(msg))
        time.sleep(0.1)
        return msg

    def decode_efficient_bytes(self, byte_stream):
        """Unpacks the self-describing byte stream back into a list of numbers"""
        decoded_values = []

        if byte_stream is None:
            return None
        
        # 1. Safety Check: If the read() method accidentally decoded it into a string, 
        # force it back into raw bytes.
        if isinstance(byte_stream, str):
            # We use 'latin1' because it preserves raw binary exactly 1-to-1
            byte_stream = byte_stream.encode('latin1') 
            
        # Step through the stream in 5-byte chunks
        for i in range(0, len(byte_stream), 5):
            chunk = byte_stream[i:i+5]
            
            # Safety check: make sure we have a full 5-byte chunk
            if len(chunk) == 5: 
                # 2. Slice the first byte instead of indexing. 
                # This safely gives us b'f' or b'i' without needing chr()
                data_type = chunk[0:1] 
                
                # The remaining 4 bytes are the actual data
                raw_data = chunk[1:]      
                
                # Unpack based on the byte marker
                if data_type == b'f':
                    val = struct.unpack('f', raw_data)[0]
                    decoded_values.append(val)
                elif data_type == b'i':
                    val = struct.unpack('i', raw_data)[0]
                    decoded_values.append(val)
                    
        return decoded_values