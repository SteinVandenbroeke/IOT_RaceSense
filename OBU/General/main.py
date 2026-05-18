import time
from CarData import CarData
from TSUConn import TSUConn
from Flag import Flag
import CarId
# 1. Initialize the Pytrack 2 board using the coprocessor library
print("Initializing...")

time.sleep(5)
conn = TSUConn("racesense", "racesense")
conn.connect_wifi()

cardata.off_threaded_sensor_fetching(True)

CORAL_IP = "172.23.157.168" 
conn.connect_mqtt(broker_ip=CORAL_IP, client_id="pycom_" + str(CarId.getCarId()))

flag = Flag(conn)
cardata.crashDetection.add_flag(flag)
cardata.crashDetection.add_conn(conn)
print("Started")
print("New version 1")
if board_type == "PYTRACK":
    #while True:
    #    print(gpssens.get())
    #    #print(cardata.get())
    #    #SEND DATA TO TSU's
    #    time.sleep(0.5)
    while True:
        flag.check()
        #print(cardata.get())
        #int_comm.write(cardata.get_efficient_bytes())
        conn.send_mqtt(topic="sensors", data_dict=cardata.get(), drop_if_bussy=True)
        #send data to pytrack over internal comm channel
        time.sleep(0.2)
        
elif board_type == "PYSENSE":
    while True:
        flag.check()
        #print(cardata.get())
        #int_comm.write(cardata.get_efficient_bytes())
        conn.send_mqtt(topic="sensors", data_dict=cardata.get(), drop_if_bussy=True)
        #send data to pytrack over internal comm channel
        time.sleep(0.2)