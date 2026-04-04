import cv2
import os
import glob
from ultralytics import YOLO

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# Path to your trained model weights (default Ultralytics save location)
WEIGHTS_PATH = 'model/train/weights/best.pt'

INPUT_DIR = 'test_images/'
OUTPUT_DIR = 'test_images/results'


def run_inference():
    # Create the output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. Load your custom trained YOLO model
    print(f"Loading model from {WEIGHTS_PATH}...")
    try:
        model = YOLO(WEIGHTS_PATH)
    except FileNotFoundError:
        print(f"Error: Could not find model weights at {WEIGHTS_PATH}. Check the path!")
        return

    # 2. Gather all images from the input directory
    image_paths = glob.glob(os.path.join(INPUT_DIR, '*.png')) + \
                  glob.glob(os.path.join(INPUT_DIR, '*.jpeg'))

    if not image_paths:
        print(f"No images found in {INPUT_DIR}.")
        return

    print(f"Found {len(image_paths)} images. Running inference...")

    # Define the 3D bounding box edges based on CARLA's coordinate order
    edges = [
        # Bottom plane edges
        (0, 1), (1, 3), (3, 2), (2, 0),
        # Top plane edges
        (4, 5), (5, 7), (7, 6), (6, 4),
        # Vertical pillars connecting bottom to top
        (0, 4), (1, 5), (2, 6), (3, 7)
    ]

    # 3. Process each image
    for img_path in image_paths:
        filename = os.path.basename(img_path)

        # Run the model on the image
        # verbose=False keeps the console clean when processing many images
        results = model(img_path, imgsz=800, verbose=False)

        # Load the image with OpenCV for drawing
        img = cv2.imread(img_path)

        # Rotate the image 90 degrees clockwise
        img_rotated = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)

        # Pass the ROTATED image to the model
        results = model(img_rotated, imgsz=800, verbose=False)

        # YOLO can detect multiple cars in one image. We loop through all detections.
        # results[0] contains the predictions for the first (and in this case, only) image passed
        if results[0].keypoints is not None:
            # Extract the keypoints tensor (Shape: [Num_Cars, 8_Keypoints, 2_Coordinates])
            all_keypoints = results[0].keypoints.xy.cpu().numpy()

            for car_keypoints in all_keypoints:
                # Ensure we actually got 8 points for this detection
                if len(car_keypoints) == 8:

                    # --- Draw Edges (Wireframe) ---
                    for start_idx, end_idx in edges:
                        pt1 = (int(car_keypoints[start_idx][0]), int(car_keypoints[start_idx][1]))
                        pt2 = (int(car_keypoints[end_idx][0]), int(car_keypoints[end_idx][1]))

                        if pt1 != (0, 0) and pt2 != (0, 0):
                            # Changed to BGR for Blue: (255, 100, 0)
                            cv2.line(img_rotated, pt1, pt2, color=(255, 100, 0), thickness=2)

                    # --- Draw Dots and Numbers ---
                    for idx, pt in enumerate(car_keypoints):
                        x, y = int(pt[0]), int(pt[1])

                        if x != 0 and y != 0:
                            # Changed to BGR for Red: (0, 0, 255)
                            cv2.circle(img_rotated, (x, y), radius=5, color=(0, 0, 255), thickness=-1)

                            # Green stays the same in BGR: (0, 255, 0)
                            cv2.putText(img_rotated, str(idx), (x + 8, y - 8),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                    # 4. Save the visualized image with high compression
                output_path = os.path.join(OUTPUT_DIR, filename)

                # This tells OpenCV to use maximum compression (0-9 scale, 9 is highest)
                cv2.imwrite(output_path, img_rotated, [cv2.IMWRITE_PNG_COMPRESSION, 9])
                print(f"Saved: {output_path}")

    print("\nInference complete! Check the output folder to see your model's predictions.")


if __name__ == '__main__':
    run_inference()