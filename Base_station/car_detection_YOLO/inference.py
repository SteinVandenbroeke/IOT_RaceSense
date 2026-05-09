import cv2
from ultralytics import YOLO
from flask import Flask, Response

app = Flask(__name__)

MODEL_PATH = 'best_edgetpu.tflite'
model = YOLO(MODEL_PATH, task='pose')


@app.route('/')
def serve_inference_image():
    image_path = '../test_images/Angled_Street_ClearNoon_mkz_2020_BWD_2664.png'

    # 1. Read the image and extract its dimensions
    image = cv2.imread(image_path)
    if image is None:
        return "Image not found", 404

    img_h, img_w = image.shape[:2]  # Get image height and width

    # 2. Run inference (Don't forget imgsz=320 if your Coral requires it!)
    results = model(image, imgsz=320)

    # 3. Process results
    for result in results:
        boxes = result.boxes.xyxy.cpu().numpy()
        keypoints = result.keypoints.data.cpu().numpy()

        for i in range(len(boxes)):
            # Draw Bounding Box
            x1, y1, x2, y2 = map(int, boxes[i])
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # Draw 8 Keypoints
            pts = keypoints[i]
            for j, pt in enumerate(pts):
                px, py, conf = pt

                # --- THE FIX ---
                # Check if the coordinates are normalized fractions (0.0 to 1.0).
                # If they are, multiply them by the image dimensions!
                if 0.0 < px <= 1.0 and 0.0 < py <= 1.0:
                    px = px * img_w
                    py = py * img_h
                # ---------------

                if conf > 0.4 and (px > 0 or py > 0):
                    ix, iy = int(px), int(py)

                    cv2.circle(image, (ix, iy), 5, (0, 0, 255), -1)
                    cv2.putText(image, str(j), (ix + 5, iy - 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

    # 4. Encode and serve
    success, encoded_image = cv2.imencode('.jpg', image)
    if not success:
        return "Failed to encode image", 500

    return Response(encoded_image.tobytes(), mimetype='image/jpeg')


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)