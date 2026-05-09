import numpy as np
import cv2
import tflite_runtime.interpreter as tflite

interpreter = tflite.Interpreter(
    model_path="best_edgetpu.tflite",
    experimental_delegates=[tflite.load_delegate("/usr/lib/aarch64-linux-gnu/libedgetpu.so.1")]
)
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Prepare input
img = cv2.imread("../test_images/Angled_Street_ClearNoon_mkz_2020_BWD_2664.png")
img = cv2.resize(img, (320, 320))
img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

# Apply input quantization
in_scale, in_zp = input_details[0]['quantization']
img_q = (img / in_scale + in_zp).astype(np.uint8)
interpreter.set_tensor(input_details[0]['index'], img_q[np.newaxis])

interpreter.invoke()

# Print every output tensor with its quantization params
for i, out in enumerate(output_details):
    raw = interpreter.get_tensor(out['index'])
    scale, zp = out['quantization']
    dequant = (raw.astype(np.float32) - zp) * scale
    print(f"Output {i}: shape={raw.shape}, scale={scale:.6f}, zp={zp}, min={dequant.min():.4f}, max={dequant.max():.4f}")
    print(dequant)