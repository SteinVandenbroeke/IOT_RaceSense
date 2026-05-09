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

    # 2. Run inference
    results = model(image, imgsz=320)

    # 3. Process results
    for result in results:
        # Check if normalized coordinates exist (common in TFLite/EdgeTPU)
        # result.keypoints.xyn is [N, 8, 2] - only X and Y, no confidence
        # result.keypoints.conf is [N, 8] - the confidence scores

        has_xyn = result.keypoints.xyn is not None and len(result.keypoints.xyn[0]) > 0

        boxes = result.boxes.xyxy.cpu().numpy()

        # We will try to pull from .xyn first, then fallback to .data
        if has_xyn:
            kpts_to_use = result.keypoints.xyn.cpu().numpy()
            confs_to_use = result.keypoints.conf.cpu().numpy()
            is_normalized = True
        else:
            kpts_to_use = result.keypoints.data.cpu().numpy()
            is_normalized = False  # We'll check this per-point below

        for i in range(len(boxes)):
            print(f"\n--- Object {i} Raw Data ---")

            # Draw Box
            x1, y1, x2, y2 = map(int, boxes[i])
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)

            for j in range(len(kpts_to_use[i])):
                # Extract x, y (and confidence if using .data)
                if has_xyn:
                    px, py = kpts_to_use[i][j]
                    conf = confs_to_use[i][j]
                else:
                    px, py, conf = kpts_to_use[i][j]

                # LOGGING: See exactly what the Coral is saying
                print(f"Point {j} Raw: x={px:.6f}, y={py:.6f}, conf={conf:.2f}")

                # FORCE SCALING: If the values are small, scale them
                # Even if px is 0.0, it might be a valid point at the edge
                if is_normalized or (px <= 1.0 and py <= 1.0 and (px > 0 or py > 0)):
                    px_final = px * img_w
                    py_final = py * img_h
                else:
                    px_final = px
                    py_final = py

                if conf > 0.25:  # Lowered threshold for EdgeTPU debugging
                    ix, iy = int(px_final), int(py_final)
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