import io
import cv2
from flask import Flask, send_file
from ultralytics import YOLO

app = Flask(__name__)

# --- CONFIGURATION ---
# Change this to "yolov8n-pose_edgetpu.tflite" when running on the Coral
MODEL_PATH = "yolov8n-pose_saved_model/yolov8n-pose_full_integer_quant_edgetpu.tflite"
IMAGE_PATH = "../test_images/Stein_Pose.png"

print(f"Loading model: {MODEL_PATH}...")
model = YOLO(MODEL_PATH)


@app.route('/')
def serve_inference_image():
    # 1. Run inference
    results = model.predict(source=IMAGE_PATH, conf=0.25, imgsz=320)

    # 2. Extract the annotated image as a numpy array
    # .plot() automatically draws the boxes, labels, and pose keypoints
    annotated_image = results[0].plot()

    # 3. Encode the numpy array to a JPEG image in memory
    success, buffer = cv2.imencode('.jpg', annotated_image)
    if not success:
        return "Failed to encode image", 500

    # 4. Convert the buffer to a byte stream so Flask can send it
    img_io = io.BytesIO(buffer)

    # 5. Serve the image file directly to the browser
    return send_file(img_io, mimetype='image/jpeg')


if __name__ == "__main__":
    print("\nStarting Web Server...")
    print("-> If on your PC, open: http://localhost:5000")
    print("-> If on the Coral, open: http://<CORAL_IP_ADDRESS>:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)