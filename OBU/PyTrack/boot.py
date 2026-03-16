from pycoproc import Pycoproc
from L76GNSS import L76GNSS
# boot.py -- run on boot-up
# 1. Initialize the Pytrack 2 board using the coprocessor library
print("Initializing Pytrack 2...")
py = Pycoproc()

# 2. Initialize the GPS module 
print("Initializing GPS...")
l76 = L76GNSS(py, timeout=30)

print("Done boot")