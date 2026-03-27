import time
from LIS2HH12 import LIS2HH12
from SI7006A20 import SI7006A20
from MPL3115A2 import MPL3115A2, ALTITUDE, PRESSURE
import _thread
import math
from .Sensor import Sensor
import time_tracker

class Accelerometer(Sensor):
    def __init__(self, pycoproc):
        self.accelerometer =  LIS2HH12(pycoproc)
        self.name = "Accelerometer"

    def get(self):
        acceleration = self.accelerometer.acceleration()
        roll = self.accelerometer.roll()
        pitch = self.accelerometer.pitch()

        x, y, z = acceleration
        g_force = math.sqrt(x**2 + y**2 + z**2)
        
        data = {
            "timestamp": time_tracker.check_uptime(),
            "acceleration": acceleration,
            "roll": roll,
            "pitch": pitch,
            "g_force": g_force
        }
        return data
