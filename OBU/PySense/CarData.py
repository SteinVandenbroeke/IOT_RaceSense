import time
from LIS2HH12 import LIS2HH12
from SI7006A20 import SI7006A20
from MPL3115A2 import MPL3115A2, ALTITUDE, PRESSURE
import _thread
import math
from sensors.Accelerometer import Accelerometer
from sensors.TempAndHumidity import TempAndHumidity
from sensors.PressureAndAltitude import PressureAndAltitude

class CarData:
    def __init__(self, pycoproc):
        self.inf_fetching = False
        self.sensors = []

    def addSensor(self, sensor):
        self.sensors.append(sensor)

    def __infUpdateSensorData(self, sensor):
        while self.inf_fetching:
            self.sensorData[sensor.name] = sensor.get()
        print("__infGetAccelerometer done")
        while self.inf_fetching:
            self.PressureAndAltitudeData = self.pressureAndAltitudeData.get()
            time.sleep(0.1)
        print("__infGetgetPressureAndAltitude done")
    
    def off_threaded_sensor_fetching(self, state):
        if state:
            self.inf_fetching = True
            self.sensorData = {}
            for sensor in self.sensors:
                _thread.start_new_thread(self.__infUpdateSensorData, (sensor,))
        else:
            self.inf_fetching = False
            self.stop_signal.set()
    
    def get(self):
        if self.inf_fetching:
            self.sensorData["time"] = time.localtime()
            car_data = self.sensorData
        else:
            car_data = {
                "time": time.localtime(),
                "Accelerometer": self.__getAccelerometer(),
                "TempAndHumidity": self.__getTempAndHumidity(),
                "PressureAndAltitude": self.__getPressureAndAltitude()
            }
    
        return car_data