import tflite_runtime.interpreter as tflite

print("Attempting to connect to the Edge TPU...")
try:
    # This explicitly asks for the Edge TPU hardware driver
    delegate = tflite.load_delegate('libedgetpu.so.1')
    print("SUCCESS: The TPU driver is installed and accessible!")
except Exception as e:
    print(f"FAILURE: The TPU cannot be reached. Error: {e}")