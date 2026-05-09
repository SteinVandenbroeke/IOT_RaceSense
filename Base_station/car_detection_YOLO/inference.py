import cv2
from ultralytics import YOLO
from flask import Flask, Response

# Initialize the web app
app = Flask(__name__)

# Pre-load the model globally
# MODEL_PATH = 'best_edgetpu.tflite'
MODEL_PATH = '../../runs/pose/carla_yolo_dataset/run_1-2/weights/best.pt'
print(f"Loading Coral-optimized model: {MODEL_PATH}")
model = YOLO(MODEL_PATH, task='pose')


@app.route('/')
def serve_inference_image():
    image_path = '../test_images/Angled_Street_ClearNoon_mkz_2020_BWD_2664.png'

    # 1. Read the image with OpenCV
    image = cv2.imread(image_path)
    if image is None:
        return "Image not found", 404

    # 2. Run inference
    # We pass the image directly to the model
    results = model(image, imgsz=320, conf=0.1)

    # 3. Process results and draw manually
    for result in results:
        # Get bounding boxes (xyxy format)
        boxes = result.boxes.xyxy.cpu().numpy()

        # Get keypoints (x, y coordinates and confidence)
        # result.keypoints.data is usually (N, 8, 3) for your custom model
        keypoints = result.keypoints.data.cpu().numpy()

        for i in range(len(boxes)):
            # Draw Bounding Box
            x1, y1, x2, y2 = map(int, boxes[i])
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # Draw 8 Keypoints
            pts = keypoints[i]
            for j, pt in enumerate(pts):
                px, py, conf = pt

                # Filter out points that were capped at 0 or have very low confidence
                if conf > 0.4 and (px > 0 or py > 0):
                    # Check our visibility/confidence logic
                    if conf > 0.4 and (px > 0 or py > 0):
                        ix, iy = int(px), int(py)
                        print(f"  Point {j}: x={ix}, y={iy} (Conf: {conf:.2f}) -> DRAWN")

                        # Draw point
                        cv2.circle(image, (ix, iy), 5, (0, 0, 255), -1)

                        # Draw label (0-7)
                        cv2.putText(image, str(j), (ix + 5, iy - 5),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                    else:
                        # Point is likely the [0,0] placeholder or model is highly uncertain
                        print(f"  Point {j}: x={int(px)}, y={int(py)} (Conf: {conf:.2f}) -> IGNORED (Out of bounds)")

    # 4. Encode the manually annotated image into JPEG format
    success, encoded_image = cv2.imencode('.jpg', image)
    if not success:
        return "Failed to encode image", 500

    # 5. Send the image bytes to the web browser
    return Response(encoded_image.tobytes(), mimetype='image/jpeg')


if __name__ == "__main__":
    print("\nStarting Web Server")
    app.run(host='0.0.0.0', port=5000, debug=False)