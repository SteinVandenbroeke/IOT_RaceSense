import cv2
import os
from ultralytics import YOLO

# ---------------------------------------------------------------------------
# Global Initialization
# ---------------------------------------------------------------------------
# We load the Edge TPU model ONCE globally.
# Loading the model takes time, so we don't want to do it on every single image.
EDGETPU_MODEL_PATH = 'best_full_integer_quant.tflite'

try:
    print(f"Loading Edge TPU model from {EDGETPU_MODEL_PATH}...")
    # task='pose' ensures Ultralytics expects keypoints, not just bounding boxes
    coral_model = YOLO(EDGETPU_MODEL_PATH, task='pose')
    print("Model loaded successfully.")
except FileNotFoundError:
    print(f"CRITICAL ERROR: Could not find {EDGETPU_MODEL_PATH}.")
    print("Did you remember to export your .pt model to .tflite format?")


# ---------------------------------------------------------------------------
# The Callable Function
# ---------------------------------------------------------------------------
def process_and_visualize(image_path, output_dir='coral_results'):
    """
    Runs inference on the Coral TPU, draws keypoints/wireframes, and saves the image.

    Args:
        image_path (str): The path to the input image.
        output_dir (str): The folder where the processed image will be saved.

    Returns:
        str: The path to the saved image, or None if it failed.
    """
    # 1. Setup and load image
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.basename(image_path)

    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not read image at {image_path}")
        return None

    # Rotate 90 degrees clockwise as requested in original script
    img_rotated = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)

    # 2. Run Inference on the Edge TPU
    # verbose=False keeps the console clean
    results = coral_model(img_rotated, imgsz=800, verbose=False)

    # Define the 3D bounding box edges based on CARLA's coordinate order
    edges = [
        (0, 1), (1, 3), (3, 2), (2, 0),  # Bottom plane
        (4, 5), (5, 7), (7, 6), (6, 4),  # Top plane
        (0, 4), (1, 5), (2, 6), (3, 7)  # Vertical pillars
    ]

    # 3. Draw keypoints and edges
    if results[0].keypoints is not None:
        all_keypoints = results[0].keypoints.xy.cpu().numpy()

        for car_keypoints in all_keypoints:
            if len(car_keypoints) == 8:

                # Draw Edges (Wireframe) in Blue
                for start_idx, end_idx in edges:
                    pt1 = (int(car_keypoints[start_idx][0]), int(car_keypoints[start_idx][1]))
                    pt2 = (int(car_keypoints[end_idx][0]), int(car_keypoints[end_idx][1]))

                    if pt1 != (0, 0) and pt2 != (0, 0):
                        cv2.line(img_rotated, pt1, pt2, color=(255, 100, 0), thickness=2)

                # Draw Dots (Red) and Numbers (Green)
                for idx, pt in enumerate(car_keypoints):
                    x, y = int(pt[0]), int(pt[1])

                    if x != 0 and y != 0:
                        cv2.circle(img_rotated, (x, y), radius=5, color=(0, 0, 255), thickness=-1)
                        cv2.putText(img_rotated, str(idx), (x + 8, y - 8),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # 4. Save the image
    output_path = os.path.join(output_dir, filename)
    cv2.imwrite(output_path, img_rotated, [cv2.IMWRITE_PNG_COMPRESSION, 9])

    print(f"Processed and saved: {output_path}")
    return output_path


# ---------------------------------------------------------------------------
# Example Usage
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    # You can just call the function like this from anywhere in your code
    test_image = "test_image.jpeg"

    if os.path.exists(test_image):
        final_image_path = process_and_visualize(test_image)
        print(f"Success! You can view the image at: {final_image_path}")
    else:
        print(f"Please place an image at {test_image} to test the script.")