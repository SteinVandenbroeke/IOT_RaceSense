import cv2
from ultralytics import YOLO
from flask import Flask, Response

# Initialize the web app
app = Flask(__name__)

# Pre-load the model globally
MODEL_PATH = 'best_int8.tflite'
# MODEL_PATH = '../../runs/pose/run_12/weights/best.pt'
print(f"Loading Coral-optimized model: {MODEL_PATH}")
model = YOLO(MODEL_PATH, task='pose')


@app.route('/')
def serve_inference_image():
    image_path = '../test_images/Angled_Street_ClearNoon_mkz_2020_BWD_2664.png'
    print(f"Running inference and serving to browser...")

    # 1. Read the image with OpenCV first so we have a canvas to draw on
    image = cv2.imread(image_path)
    h, w = image.shape[:2]

    # 2. Run Inference (passing the OpenCV image directly instead of the path)
    # Don't forget the imgsz=320 fix we just added!
    results = model(image, imgsz=320, conf=0.1)
    result = results[0]

    print(f"Using device: {result.speed}")

    print(f"Cars detected: {len(result.boxes)}")
    if result.keypoints is not None:
        print(f"Raw Keypoint Array Shape: {result.keypoints.xy.shape}")
        print(f"First car keypoints: {result.keypoints.data[0].tolist()}")

    # 3. Manually draw the keypoints as dots
    # Check if the model actually detected any keypoints
    if result.keypoints is not None and len(result.keypoints) > 0:
        for i in range(len(result.keypoints)):
            keypoints = result.keypoints.xy[i].tolist()

            for (x, y) in keypoints:
                if x != 0 and y != 0:
                    # Scale from 320x320 model space to actual image space
                    px = int(x * w / 320)
                    py = int(y * h / 320)
                    cv2.circle(image, (px, py), radius=5, color=(0, 255, 0), thickness=-1)

    print(f"Input image size: {image.shape}")  # e.g. (720, 1280, 3)
    print(f"Keypoint xy range: {result.keypoints.xy.min()}, {result.keypoints.xy.max()}")

    # 4. Encode the manually annotated image into JPEG format
    success, encoded_image = cv2.imencode('.jpg', image)
    if not success:
        return "Failed to encode image", 500

    # 5. Send the image bytes to the web browser
    return Response(encoded_image.tobytes(), mimetype='image/jpeg')


if __name__ == "__main__":
    # Using port 5000 to avoid the "Address already in use" error from earlier
    print("\nStarting Web Server...")
    app.run(host='0.0.0.0', port=5000, debug=False)