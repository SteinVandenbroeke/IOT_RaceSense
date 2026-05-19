import numpy as np
import tensorflow as tf
import matplotlib

matplotlib.use('Agg')  # Forces headless mode to save files
import matplotlib.pyplot as plt
from PIL import Image
import cv2  # OpenCV for post-processing
import glob
import os

# --- Configuration ---
MODEL_PATH = "../../TSU/models/mobilenetv2_tpu_segmentation_car_real.tflite"
TEST_IMAGE_DIR = "../manual_dataset/manual_car_dataset/rgb/val"
TEST_MASK_DIR = "../manual_dataset/manual_car_dataset/masks/val"
IMG_SIZE = 224

# --- 1. Load the TFLite Model ---
interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()[0]
output_details = interpreter.get_output_details()[0]

input_scale, input_zero_point = input_details['quantization']
output_scale, output_zero_point = output_details['quantization']


def preprocess_image(image_path):
    """Loads and formats the image exactly like the training pipeline."""
    img = Image.open(image_path).convert('RGB')
    img_resized = img.resize((IMG_SIZE, IMG_SIZE), Image.Resampling.BILINEAR)

    input_data = np.array(img_resized, dtype=np.float32)
    input_data = (input_data / 127.5) - 1.0

    if input_scale != 0:
        input_data = (input_data / input_scale) + input_zero_point
        input_data = np.clip(input_data, -128, 127).astype(np.int8)

    return np.expand_dims(input_data, axis=0), img_resized


def load_ground_truth(mask_path):
    """Loads and binarizes the actual ground truth mask."""
    if not os.path.exists(mask_path):
        return None

    mask = Image.open(mask_path).convert('L')
    mask_resized = mask.resize((IMG_SIZE, IMG_SIZE), Image.Resampling.NEAREST)
    mask_array = np.array(mask_resized)
    return (mask_array > 0).astype(np.uint8)


def predict_mask(input_tensor):
    """Runs inference and dequantizes the output."""
    interpreter.set_tensor(input_details['index'], input_tensor)
    interpreter.invoke()

    output_data = interpreter.get_tensor(output_details['index'])[0]

    if output_scale != 0:
        output_data = (output_data.astype(np.float32) - output_zero_point) * output_scale

    output_data = np.squeeze(output_data)
    binary_mask = (output_data > 0.5).astype(np.uint8)
    return binary_mask


def post_process_mask(binary_mask):
    """
    Applies Multi-Directional Morphological Closing to connect broken segments
    regardless of whether the road goes vertically or horizontally.
    """
    # 1. Vertical Kernel (Catches lines going up/down)
    kernel_v = np.ones((35, 5), np.uint8)
    closed_v = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel_v)

    # 2. Horizontal Kernel (Catches lines going left/right)
    kernel_h = np.ones((5, 35), np.uint8)
    closed_h = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel_h)

    # 3. Combine them!
    # cv2.bitwise_or keeps a pixel if it was fixed by EITHER the vertical or horizontal pass.
    combined_mask = cv2.bitwise_or(closed_v, closed_h)

    return combined_mask


def display_results(original_img, ground_truth, raw_mask, processed_mask, save_path):
    """Draws a 5-panel comparison and saves it to a file."""
    # Scale masks to 0-255 for visualization
    raw_visual = raw_mask * 255
    proc_visual = processed_mask * 255
    gt_visual = ground_truth * 255 if ground_truth is not None else np.zeros((IMG_SIZE, IMG_SIZE))

    # Create the overlay using the FINAL processed mask
    overlay = np.array(original_img).copy()
    overlay[processed_mask == 1] = [255, 0, 0]  # Red for predicted lines

    # Create a wider figure for 5 panels
    plt.figure(figsize=(20, 4))

    plt.subplot(1, 5, 1)
    plt.title("Original Image")
    plt.imshow(original_img)
    plt.axis('off')

    plt.subplot(1, 5, 2)
    plt.title("Ground Truth Mask")
    plt.imshow(gt_visual, cmap='gray')
    plt.axis('off')

    plt.subplot(1, 5, 3)
    plt.title("Raw Prediction")
    plt.imshow(raw_visual, cmap='gray')
    plt.axis('off')

    plt.subplot(1, 5, 4)
    plt.title("Processed (Closed gaps)")
    plt.imshow(proc_visual, cmap='gray')
    plt.axis('off')

    plt.subplot(1, 5, 5)
    plt.title("Final Overlay")
    plt.imshow(overlay)
    plt.axis('off')

    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()


# --- 2. Run Test on Sample Images ---
all_files = glob.glob(os.path.join(TEST_IMAGE_DIR, "*.*"))
test_images = [f for f in all_files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

if not test_images:
    print(f"No test images found in {TEST_IMAGE_DIR}!")
else:
    for img_path in test_images:
        filename = os.path.basename(img_path)
        print(f"Testing: {filename}")

        base_name = os.path.splitext(filename)[0]
        mask_path = os.path.join(TEST_MASK_DIR, filename)
        if not os.path.exists(mask_path):
            mask_path = os.path.join(TEST_MASK_DIR, base_name + ".png")

        # 1. Process inputs
        input_tensor, original_resized = preprocess_image(img_path)
        ground_truth_mask = load_ground_truth(mask_path)

        # 2. Get predictions
        raw_predicted_mask = predict_mask(input_tensor)

        # 3. Post-process
        processed_mask = post_process_mask(raw_predicted_mask)

        if ground_truth_mask is None:
            print(f"  -> Warning: No matching ground truth mask found at {mask_path}")

        # 4. Save output
        save_name = f"output/result_5panel_{base_name}.png"
        display_results(original_resized, ground_truth_mask, raw_predicted_mask, processed_mask, save_name)
        print(f"  -> Saved prediction to {save_name}")