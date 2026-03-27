import time
from CarData import CarData

# 1. Initialize the Pytrack 2 board using the coprocessor library
print("Initializing Pytrack 2...")
cardata.off_threaded_sensor_fetching(True)

time.sleep(5)
if board_type == "PYTRACK":
    while True:
        print(cardata.get())
        #SEND DATA TO TSU's
        time.sleep(0.01)
elif board_type == "PYSENSE":
    while True:
        print(cardata.get())
        int_comm.write(cardata.get_efficient_bytes())
        #send data to pytrack over internal comm channel
        time.sleep(0.01)