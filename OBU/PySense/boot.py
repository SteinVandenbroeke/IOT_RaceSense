from pycoproc import Pycoproc
from sensors.Accelerometer import Accelerometer
from sensors.TempAndHumidity import TempAndHumidity
from sensors.PressureAndAltitude import PressureAndAltitude
from sensors.GpsSensor import GPSSensor
from CarData import CarData

# boot.py -- run on boot-up
# 1. Initialize the Pytrack 2 board using the coprocessor library
pycoproc = Pycoproc()
board_id = pycoproc.read_product_id()
board_type = None

cardata = CarData(pycoproc)

print("Boardid", board_id)
if board_id == 61458:
    print("Pysense connected!")
    board_type = "PYSENSE"
    cardata.addSensor(Accelerometer(pycoproc=pycoproc))
    cardata.addSensor(TempAndHumidity(pycoproc=pycoproc))
    cardata.addSensor(PressureAndAltitude(pycoproc=pycoproc))
    # Initialize Pysense-specific sensors here (e.g., SI7006A20, LTR329ALS01)
    
elif board_id == 61459:
    print("Pytrack connected!")
    board_type = "PYTRACK"
    cardata.addSensor(Accelerometer(pycoproc=pycoproc))
    cardata.addSensor(GPSSensor(pycoproc=pycoproc))
    # Initialize Pytrack-specific sensors here (e.g., L76GNSS)
    
else:
    print("Unknown board or Pyscan connected. Product ID:", board_id)