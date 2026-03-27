import time
from LIS2HH12 import LIS2HH12
from SI7006A20 import SI7006A20
from MPL3115A2 import MPL3115A2, ALTITUDE, PRESSURE
import _thread
import math
from sensors.Accelerometer import Accelerometer
from sensors.TempAndHumidity import TempAndHumidity
from sensors.PressureAndAltitude import PressureAndAltitude
from CrashDetection import CarStateDetection
import time_tracker
import struct

class CarData:
    def __init__(self, pycoproc):
        self.inf_fetching = False
        self.sensors = []
        self.crashDetection = CarStateDetection()

    def addSensor(self, sensor):
        self.sensors.append(sensor)

    def __infUpdateData(self, sensor, crash_detector: CarStateDetection):
        """
        Infinitly updates sensor data + uses this data to check state of car (crashdetection)
        """
        while self.inf_fetching:
            self.sensorData[sensor.name] = sensor.get()
            crash_detector.checkAndProcess(self.sensorData)

        print("__infGetAccelerometer done")

    def off_threaded_sensor_fetching(self, state):
        if state:
            self.inf_fetching = True
            self.sensorData = {}
            for sensor in self.sensors:
                _thread.start_new_thread(self.__infUpdateData, (sensor, self.crashDetection,))
        else:
            self.inf_fetching = False
            self.stop_signal.set()
    
    def get(self):
        if self.inf_fetching:
            self.sensorData["time"] = time_tracker.check_uptime()
            car_data = self.sensorData
        else:
            car_data = {
                "time": time_tracker.check_uptime(),
                "Accelerometer": self.__getAccelerometer(),
                "TempAndHumidity": self.__getTempAndHumidity(),
                "PressureAndAltitude": self.__getPressureAndAltitude()
            }
    
        return car_data
    
    def dict_to_byte_stream(self, data):
        new_data = []
        for d_key, d_value in data.items():
            if type(d_value) is dict:
                new_data = new_data + self.dict_to_byte_stream(d_value)
            elif type(d_value) is tuple:
                t_data = []
                for t_value in d_value:
                    t_data.append(t_value)
                new_data = new_data + t_data
            else:
                new_data.append(d_value)
        return new_data

    
    def get_efficient_bytes(self):
        list_of_values = self.dict_to_byte_stream(self.get())
        byteEncodedList = b''
        for item in list_of_values:
            if isinstance(item, float):
                byteEncodedList += b'f' + struct.pack('f', item) 
            elif isinstance(item, int):
                byteEncodedList += b'i' + struct.pack('i', item)
                
        return byteEncodedList
    
    def __dict_to_template(self, data):
        new_data = {}
        for d_key, d_value in data.items():
            if type(d_value) is dict:
                new_data[d_key] = self.__dict_to_template(d_value)
            elif type(d_value) is tuple:
                t_data = []
                for _ in d_value:
                    t_data.append(None)
                new_data[d_key] = + t_data
            else:
                new_data[d_key] = None
        return new_data

    def get_dict_template(self):
        return self.__dict_to_template()
