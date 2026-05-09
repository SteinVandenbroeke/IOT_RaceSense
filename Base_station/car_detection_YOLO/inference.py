import cv2
from ultralytics import YOLO


def main():
    # 1. Load the model
    # You can test with your PC model ('best.pt') or the Coral model ('best_edgetpu.tflite')
    model_path = '../../runs/best_int8.tflite'
    image_path = '../test_images/Angled_Street_ClearNoon_mkz_2020_BWD_2664.png'  # Replace with your image

    print(f"Loading model: {model_path}")
    model = YOLO(model_path)

    # 2. Run Inference
    # YOLO automatically resizes the image, scales the points, and handles the math
    print(f"Running inference on: {image_path}")
    results = model(image_path)

    # Grab the first result (since we only passed one image)
    result = results[0]

    # ==========================================
    # METHOD A: Let YOLO draw and show the image
    # ==========================================
    print("Opening visualization window... (Press any key to close)")
    result.show()  # This pops open a window with the box and all 8 points drawn

    # ==========================================
    # METHOD B: Extract the raw data for your track math
    # ==========================================
    print("\n--- Raw Data Extraction ---")

    # Check if any cars were detected
    if len(result.boxes) == 0:
        print("No cars detected in this image.")
        return

    # Loop through every detected car (in case there is more than 1)
    for i, box in enumerate(result.boxes):
        print(f"\nCar #{i + 1}:")

        # Get bounding box coordinates (Top-Left and Bottom-Right)
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        print(f"  Bounding Box: Top-Left({int(x1)}, {int(y1)}) to Bottom-Right({int(x2)}, {int(y2)})")
        print(f"  Confidence: {box.conf[0]:.2f}")

        # Extract the 8 keypoints for this specific car
        # .xy returns a tensor of shape [1, 8, 2] (1 car, 8 points, X/Y pairs)
        keypoints = result.keypoints.xy[i].tolist()

        for kpt_index, (x, y) in enumerate(keypoints):
            # If x and y are 0, the model thinks the point is hidden/occluded
            if x == 0 and y == 0:
                print(f"  Point {kpt_index + 1}: Not visible")
            else:
                print(f"  Point {kpt_index + 1}: X={int(x)}, Y={int(y)}")


if __name__ == "__main__":
    main()