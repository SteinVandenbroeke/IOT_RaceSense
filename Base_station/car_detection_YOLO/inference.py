import cv2
from ultralytics import YOLO
from flask import Flask, Response

# Initialize the web app
app = Flask(__name__)

# Pre-load the model globally so we don't reload it every time you refresh the page
MODEL_PATH = 'best_edgetpu.tflite'
print(f"Loading Coral-optimized model: {MODEL_PATH}")
model = YOLO(MODEL_PATH, task='pose')


@app.route('/')
def serve_inference_image():
    """This function runs whenever you visit http://192.168.100.2:4664/"""

    image_path = '../test_images/Angled_Street_ClearNoon_mkz_2020_BWD_2664.png'
    print(f"Running inference and serving to browser...")

    # 1. Run Inference
    results = model(image_path)
    result = results[0]

    # 2. Get the annotated image
    # YOLO's .plot() method automatically draws the keypoints/boxes
    # and returns a clean Numpy array, saving us from writing OpenCV drawing math!
    annotated_image = result.plot()

    # 3. Encode the image into JPEG format so a web browser can read it
    success, encoded_image = cv2.imencode('.jpg', annotated_image)
    if not success:
        return "Failed to encode image", 500

    # 4. Send the image bytes to the web browser
    return Response(encoded_image.tobytes(), mimetype='image/jpeg')


if __name__ == "__main__":
    # Host the server on all network interfaces (0.0.0.0) on port 4664
    print("\nStarting Web Server...")
    print("Open your PC's browser and go to: http://192.168.100.2:4664/")
    app.run(host='0.0.0.0', port=4664, debug=False)