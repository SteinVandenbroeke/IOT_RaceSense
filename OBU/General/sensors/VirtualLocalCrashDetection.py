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

class VirtualLocalCrashDetection(Sensor):
    def __init__(self, pycoproc):
        self.name = "VirtualTime"
        self.rtc = RTC()
        self.rtc.ntp_sync("pool.ntp.org")
        while not self.rtc.synced():
            print("Waiting for clock sync...")
            time.sleep(1)
        print("Clock synced! Current time:", self.rtc.now())

    def get(self):
        data = {
            "timestamp": time_tracker.check_uptime(),
            "rtc_time": self.rtc.now()
        }
        return data
