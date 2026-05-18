from pycoproc import Pycoproc
from sensors.Accelerometer import Accelerometer
from sensors.TempAndHumidity import TempAndHumidity
from sensors.PressureAndAltitude import PressureAndAltitude
from sensors.VirtualPyCom import VirtualPyCom
from sensors.VirtualCarId import VirtualCarId
from sensors.GpsSensor import GPSSensor
from CarData import CarData
from CrashDetection import State_NoSpeed
from CrashDetection import Crash_HardCarFlip
import time_tracker
import CarId
from internalCommunication import InternalCommunication
from TSUConn import TSUConn
# boot.py -- run on boot-up
# 1. Initialize the Pytrack 2 board using the coprocessor library
pycoproc = Pycoproc()
board_id = pycoproc.read_product_id()
board_type = None

cardata = CarData(pycoproc)

print("Boardid", board_id)
print("Time ticks", time_tracker.check_uptime())


if board_id == 61458:
    print("Pysense connected!")
    board_type = "PYSENSE"
    cardata.addSensor(Accelerometer(pycoproc=pycoproc))
    cardata.addSensor(TempAndHumidity(pycoproc=pycoproc))
    cardata.addSensor(PressureAndAltitude(pycoproc=pycoproc))
    cardata.addSensor(VirtualCarId(pycoproc=pycoproc))
    cardata.crashDetection.add_crash_sequense(Crash_HardCarFlip())
    CarId.setCarId(1)

    # int_comm = InternalCommunication(False)
    # Initialize Pysense-specific sensors here (e.g., SI7006A20, LTR329ALS01)
    
elif board_id == 61459:
    print("Pytrack connected!")
    board_type = "PYTRACK"
    cardata.addSensor(Accelerometer(pycoproc=pycoproc))
    gpssens = GPSSensor(pycoproc=pycoproc)
    cardata.addSensor(gpssens)
    cardata.addSensor(VirtualCarId(pycoproc=pycoproc))
    cardata.crashDetection.add_crash_sequense(Crash_HardCarFlip())
    CarId.setCarId(0)
    #int_comm = InternalCommunication(True)
    #cardata.addSensor(VirtualPyCom(pycoproc=pycoproc, comm=int_comm))
    # Initialize Pytrack-specific sensors here (e.g., L76GNSS)
    
else:
    print("Unknown board or Pyscan connected. Product ID:", board_id)