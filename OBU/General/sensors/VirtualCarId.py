import time
from LIS2HH12 import LIS2HH12
from SI7006A20 import SI7006A20
from MPL3115A2 import MPL3115A2, ALTITUDE, PRESSURE
import _thread
import math
from .Sensor import Sensor
import time_tracker
from machine import RTC
import time_tracker
import CarId

class VirtualCarId(Sensor):
    def __init__(self, pycoproc):
        self.name = "CarId"

    def get(self):
        data = CarId.getCarId()
        return data
