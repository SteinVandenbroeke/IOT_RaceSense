import time
from pycoproc import Pycoproc
from L76GNSS import L76GNSS
import time_tracker

class GPSSensor():
    def __init__(self, pycoproc):
            self.name = "GPS"
            self.gps = L76GNSS(pycoproc, timeout=30)

    def get(self):
        data = {
            "timestamp": time_tracker.check_uptime(),
            "gps": self.gps.coordinates(),
        }
        return data