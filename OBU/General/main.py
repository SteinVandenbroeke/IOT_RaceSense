import time
from CarData import CarData
from TSUConn import TSUConn
# 1. Initialize the Pytrack 2 board using the coprocessor library
print("Initializing Pytrack 2...")
cardata.off_threaded_sensor_fetching(True)
time.sleep(5)
conn = TSUConn("racesense", "racesense")
conn.connect_wifi()

CORAL_IP = "10.12.45.168" 
conn.connect_mqtt(broker_ip=CORAL_IP, client_id="pycom_car_1")

print("Started")
print("New version")
if board_type == "PYTRACK":
    while True:
        print(gpssens.get())
        #print(cardata.get())
        #SEND DATA TO TSU's
        time.sleep(0.5)
elif board_type == "PYSENSE":
    while True:
        #print(cardata.get())
        #int_comm.write(cardata.get_efficient_bytes())
        conn.send_mqtt(topic="sensors/pycom/car1", data_dict=cardata.get())
        #send data to pytrack over internal comm channel
        time.sleep(0.01)