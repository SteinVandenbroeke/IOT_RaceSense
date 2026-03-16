import time
from LIS2HH12 import LIS2HH12
from SI7006A20 import SI7006A20
from MPL3115A2 import MPL3115A2, ALTITUDE, PRESSURE
import _thread
import math
from .Sensor import Sensor

class PressureAndAltitude(Sensor):
    def __init__(self, pycoproc):
        self.pressure = MPL3115A2(pycoproc, mode = PRESSURE)
        self.altitude = MPL3115A2(pycoproc, mode = ALTITUDE)
        self.name = "PressureAndAltitude"

    def get(self):
        pressuere = self.pressure.pressure()
        altitude = self.altitude.altitude()
        data = {
            "timestamp": time.localtime(),
            "pressuere": pressuere,
            "altitude": altitude
        }
        return data
