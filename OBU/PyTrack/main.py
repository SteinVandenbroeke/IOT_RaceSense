import time
from pycoproc import Pycoproc
from L76GNSS import L76GNSS


print("Waiting for GPS fix. This might take a few minutes if cold-starting...")

# 3. Continuous loop to read coordinates
while True:
    coord = l76.coordinates()
    
    
    if coord == (None, None):
        print("Searching for satellites... (Make sure you have a clear view of the sky)")
    else:
        latitude, longitude = coord
        print("Location Fixed! -> Latitude: {}, Longitude: {}".format(latitude, longitude))
    
    time.sleep(5)