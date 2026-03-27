import time
from LIS2HH12 import LIS2HH12
from SI7006A20 import SI7006A20
from MPL3115A2 import MPL3115A2, ALTITUDE, PRESSURE
import _thread
import math
from .Sensor import Sensor
import time_tracker

class TempAndHumidity(Sensor):
    def __init__(self, pycoproc):
        self.tempAndHumidity = SI7006A20(pycoproc)
        self.name = "TempAndHumidity"

    def get(self):
        temp = self.tempAndHumidity.temperature()
        humidity = self.tempAndHumidity.humidity()
        data = {
            "timestamp": time_tracker.check_uptime(),
            "temp": temp,
            "humidity": humidity
        }
        return data