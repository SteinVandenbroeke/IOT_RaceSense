import time
from CarData import CarData

# 1. Initialize the Pytrack 2 board using the coprocessor library
print("Initializing Pytrack 2...")
cardata.off_threaded_sensor_fetching(True)

while True:
    print(cardata.get())
    #time.sleep(0.01)
    time.sleep(0.01)