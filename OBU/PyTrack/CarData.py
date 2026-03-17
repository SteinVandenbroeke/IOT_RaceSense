import time
from pycoproc import Pycoproc
from L76GNSS import L76GNSS

class CarData:
    def __init__(self, pycoproc):
        self.gps = L76GNSS(pycoproc, timeout=30)
    
    def __get_position(self):
        coord = self.gps.coordinates()
        if coord == (None, None):
            print("Searching for satellites... (Make sure you have a clear view of the sky)")
        else:
            latitude, longitude = coord
            print("Location Fixed! -> Latitude: {}, Longitude: {}".format(latitude, longitude))
        return coord
    
    def get(self):
        car_data = {
            "gps": self.__get_position(),
        }

        return car_data