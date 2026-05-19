import os
import glob
import numpy as np
import cv2
from PIL import Image

# For Coral Dev Board, it is recommended to use tflite_runtime
try:
    from tflite_runtime.interpreter import Interpreter
    from tflite_runtime.interpreter import load_delegate
except ImportError:
    # Fallback for standard tensorflow
    import tensorflow as tf

    Interpreter = tf.lite.Interpreter
    load_delegate = tf.lite.experimental.load_delegate

# --- Configuration ---
ROAD_MODEL_PATH = "../../TSU/models/mobilenetv2_tpu_segmentation_road_real.tflite"
CAR_MODEL_PATH = "../../TSU/models/mobilenetv2_tpu_segmentation_car_real.tflite"
TEST_IMAGE_DIR = "../manual_dataset/manual_road_dataset/rgb/val"
IMG_SIZE = 224


class EdgeTPUSegmentationModel:
    def __init__(self, model_path):
        """Initializes the TFLite interpreter with the Edge TPU delegate."""
        print(f"Loading model: {model_path}...")
        try:
            # Load the Edge TPU delegate (libedgetpu.so.1.0 is standard on Coral)
            delegate = load_delegate('libedgetpu.so.1.0')
            self.interpreter = Interpreter(model_path=model_path, experimental_delegates=[delegate])
        except (ValueError, OSError) as e:  # <-- ADDED OSError HERE
            print(f"Warning: Edge TPU delegate not found ({e}). Falling back to CPU.")
            self.interpreter = Interpreter(model_path=model_path)

        self.interpreter.allocate_tensors()

        self.input_details = self.interpreter.get_input_details()[0]
        self.output_details = self.interpreter.get_output_details()[0]

        self.input_scale, self.input_zero_point = self.input_details['quantization']
        self.output_scale, self.output_zero_point = self.output_details['quantization']

    def preprocess(self, image_path):
        """Loads and formats the image for the model."""
        img = Image.open(image_path).convert('RGB')
        img_resized = img.resize((IMG_SIZE, IMG_SIZE), Image.Resampling.BILINEAR)

        input_data = np.array(img_resized, dtype=np.float32)
        input_data = (input_data / 127.5) - 1.0

        if self.input_scale != 0:
            input_data = (input_data / self.input_scale) + self.input_zero_point
            input_data = np.clip(input_data, -128, 127).astype(np.int8)

        return np.expand_dims(input_data, axis=0)

    def predict(self, input_tensor):
        """Runs inference and dequantizes the output."""
        self.interpreter.set_tensor(self.input_details['index'], input_tensor)
        self.interpreter.invoke()

        output_data = self.interpreter.get_tensor(self.output_details['index'])[0]

        if self.output_scale != 0:
            output_data = (output_data.astype(np.float32) - self.output_zero_point) * self.output_scale

        output_data = np.squeeze(output_data)
        binary_mask = (output_data > 0.5).astype(np.uint8)
        return binary_mask


def post_process_mask(binary_mask):
    """
    Applies Multi-Directional Morphological Closing to connect broken segments.
    (Kept exactly as you defined it in your test script)
    """
    # 1. Vertical Kernel
    kernel_v = np.ones((35, 5), np.uint8)
    closed_v = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel_v)

    # 2. Horizontal Kernel
    kernel_h = np.ones((5, 35), np.uint8)
    closed_h = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel_h)

    # 3. Combine them
    combined_mask = cv2.bitwise_or(closed_v, closed_h)
    return combined_mask


def check_track_violation(road_mask, car_mask):
    """
    Checks track status based on road and car masks.
    Returns:
        "NO_CAR" if no car is detected.
        "VIOLATION" if the car is detected but has no intersection with the road.
        "OK" if the car is detected and overlaps with the road.
    """
    # 1. Check if a car is even detected in the image
    if np.count_nonzero(car_mask) == 0:
        return "NO_CAR"

    # 2. Check for overlap
    # Bitwise AND keeps pixels where BOTH car AND road are 1 (overlapping)
    overlap = cv2.bitwise_and(road_mask, car_mask)

    # 3. If car exists but overlap is 0, it has left the track completely
    if np.count_nonzero(overlap) == 0:
        return "VIOLATION"

    return "OK"


def main():
    # 1. Initialize both models
    road_model = EdgeTPUSegmentationModel(ROAD_MODEL_PATH)
    car_model = EdgeTPUSegmentationModel(CAR_MODEL_PATH)

    # 2. Gather test images
    all_files = glob.glob(os.path.join(TEST_IMAGE_DIR, "*.*"))
    test_images = [f for f in all_files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    if not test_images:
        print(f"No test images found in {TEST_IMAGE_DIR}!")
        return

    print("\n--- Starting Track Violation Analysis ---")

    # 3. Process each image
    for img_path in test_images:
        filename = os.path.basename(img_path)

        # Preprocess input (assuming both models take the exact same 224x224 input)
        # We only need to read and format the image once if the scaling logic is the same.
        # But to be safe with different quantizations, we preprocess through one of the models:
        input_tensor_road = road_model.preprocess(img_path)
        input_tensor_car = car_model.preprocess(img_path)

        # Predict raw masks
        raw_road_mask = road_model.predict(input_tensor_road)
        raw_car_mask = car_model.predict(input_tensor_car)

        # Post-process both masks
        final_road_mask = post_process_mask(raw_road_mask)
        final_car_mask = post_process_mask(raw_car_mask)

        # Check for intersection / status
        status = check_track_violation(final_road_mask, final_car_mask)

        # Print result based on the 3 states
        if status == "NO_CAR":
            print(f"[?] {filename} : NO CAR DETECTED")
        elif status == "VIOLATION":
            print(f"[!] {filename} : TRACK VIOLATION (Car off road)")
        elif status == "OK":
            print(f"[✓] {filename} : Track OK (Car overlapping road)")


if __name__ == "__main__":
    main()