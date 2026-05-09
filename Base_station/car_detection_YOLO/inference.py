import cv2
import numpy as np
from ultralytics import YOLO
from flask import Flask, Response

# Initialize the web app
app = Flask(__name__)

# Pre-load the model globally
MODEL_PATH = 'best_float32_edgetpu.tflite'
# MODEL_PATH = '../../runs/pose/run_12/weights/best.pt'
print(f"Loading Coral-optimized model: {MODEL_PATH}")
model = YOLO(MODEL_PATH, task='pose')

print("Forcing the backend to load into memory...")
try:
    # 1. Create a fake, blank 320x320 image
    dummy_img = np.zeros((320, 320, 3), dtype=np.uint8)

    # 2. Run a dummy inference. It will crash because of the missing metadata,
    # but it successfully forces the TFLite runtime to load!
    model(dummy_img, imgsz=320, verbose=False)
except Exception:
    pass  # We expect it to crash, so we just ignore it!

# --- THE METADATA INJECTION ---
# 3. Now that the backend actually exists, we can inject our data directly into it!
model.predictor.model.names = {0: 'car'}
model.predictor.model.kpt_shape = [8, 3]
print("Metadata successfully injected!")


# ----------------------------------------

@app.route('/')
def serve_inference_image():
    image_path = '../test_images/Angled_Street_ClearNoon_mkz_2020_BWD_2664.png'
    print(f"Running inference and serving to browser...")

    image = cv2.imread(image_path)

    # Run Inference
    results = model(image, imgsz=320, conf=0.1)
    result = results[0]

    print(f"Using device: {result.speed}")
    print(f"Cars detected: {len(result.boxes)}")

    # --- OPTION A: Let YOLO draw everything perfectly for you (Recommended) ---
    # This single line replaces all your manual drawing code!
    image = result.plot(kpt_radius=5, boxes=True)

    # Encode the annotated image
    success, encoded_image = cv2.imencode('.jpg', image)
    if not success:
        return "Failed to encode image", 500

    return Response(encoded_image.tobytes(), mimetype='image/jpeg')


if __name__ == "__main__":
    print("\nStarting Web Server...")
    app.run(host='0.0.0.0', port=5000, debug=False)