import time
from pycoproc import Pycoproc
from L76GNSS import L76GNSS

class GPSSensor():
    def __init__(self, pycoproc):
            self.name = "GPS"
            self.gps = L76GNSS(pycoproc, timeout=30)

    def get(self):
        data = {
            "gps": self.gps.coordinates(),
        }
        return data