import cv2
from ultralytics import YOLO
from flask import Flask, Response

# Initialize the web app
app = Flask(__name__)

# Pre-load the model globally
MODEL_PATH = '../../runs/pose/best_edgetpu.tflite'
print(f"Loading Coral-optimized model: {MODEL_PATH}")
model = YOLO(MODEL_PATH, task='pose')


@app.route('/')
def serve_inference_image():
    image_path = '../test_images/42ab3ddc-0bcd-4b1a-bb85-9edb71d4e5c7.jpeg'
    print(f"Running inference and serving to browser...")

    # 1. Read the image with OpenCV first so we have a canvas to draw on
    image = cv2.imread(image_path)

    # 2. Run Inference (passing the OpenCV image directly instead of the path)
    # Don't forget the imgsz=320 fix we just added!
    results = model(image, imgsz=320)
    result = results[0]

    # 3. Manually draw the keypoints as dots
    # Check if the model actually detected any keypoints
    if result.keypoints is not None and len(result.keypoints) > 0:

        # Loop through every detected car
        for i in range(len(result.keypoints)):
            # Extract the points for this specific car
            keypoints = result.keypoints.xy[i].tolist()

            for (x, y) in keypoints:
                # If x and y are not 0 (meaning the point is visible)
                if x != 0 and y != 0:
                    # Draw a solid green circle (radius 5)
                    # Note: OpenCV colors are (Blue, Green, Red)
                    cv2.circle(image, (int(x), int(y)), radius=5, color=(0, 255, 0), thickness=-1)

    # 4. Encode the manually annotated image into JPEG format
    success, encoded_image = cv2.imencode('.jpg', image)
    if not success:
        return "Failed to encode image", 500

    # 5. Send the image bytes to the web browser
    return Response(encoded_image.tobytes(), mimetype='image/jpeg')


if __name__ == "__main__":
    # Using port 5000 to avoid the "Address already in use" error from earlier
    print("\nStarting Web Server...")
    print("Open your PC's browser and go to: http://192.168.100.2:5000/")
    app.run(host='0.0.0.0', port=5000, debug=False)