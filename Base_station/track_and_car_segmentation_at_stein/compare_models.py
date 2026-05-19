import numpy as np
import tensorflow as tf
import matplotlib

matplotlib.use('Agg')  # Forces headless mode to save files
import matplotlib.pyplot as plt
from PIL import Image
import cv2
import glob
import os

# --- Configuration ---
# UPDATE THESE PATHS TO YOUR ACTUAL MODELS
BASELINE_MODEL_PATH = "mobilenetv2_tpu_segmentation_road.tflite"
FINETUNED_MODEL_PATH = "../../TSU/models/mobilenetv2_tpu_segmentation_road_real.tflite"

TEST_IMAGE_DIR = "../manual_dataset/manual_road_dataset/rgb/val"
TEST_MASK_DIR = "../manual_dataset/manual_road_dataset/masks/val"
IMG_SIZE = 224


# --- 1. Load the TFLite Models ---
def load_model(model_path):
    interpreter = tf.lite.Interpreter(model_path=model_path)
    interpreter.allocate_tensors()
    return interpreter


baseline_interpreter = load_model(BASELINE_MODEL_PATH)
finetuned_interpreter = load_model(FINETUNED_MODEL_PATH)


def preprocess_image(image_path, interpreter):
    """Loads and formats the image using the quantization parameters of the given model."""
    input_details = interpreter.get_input_details()[0]
    input_scale, input_zero_point = input_details['quantization']

    img = Image.open(image_path).convert('RGB')
    img_resized = img.resize((IMG_SIZE, IMG_SIZE), Image.Resampling.BILINEAR)

    input_data = np.array(img_resized, dtype=np.float32)
    input_data = (input_data / 127.5) - 1.0

    if input_scale != 0:
        input_data = (input_data / input_scale) + input_zero_point
        input_data = np.clip(input_data, -128, 127).astype(np.int8)

    return np.expand_dims(input_data, axis=0), img_resized


def load_ground_truth(mask_path):
    if not os.path.exists(mask_path):
        return None
    mask = Image.open(mask_path).convert('L')
    mask_resized = mask.resize((IMG_SIZE, IMG_SIZE), Image.Resampling.NEAREST)
    return (np.array(mask_resized) > 0).astype(np.uint8)


def predict_mask(interpreter, input_tensor):
    """Runs inference and dequantizes the output."""
    input_details = interpreter.get_input_details()[0]
    output_details = interpreter.get_output_details()[0]
    output_scale, output_zero_point = output_details['quantization']

    interpreter.set_tensor(input_details['index'], input_tensor)
    interpreter.invoke()
    output_data = interpreter.get_tensor(output_details['index'])[0]

    if output_scale != 0:
        output_data = (output_data.astype(np.float32) - output_zero_point) * output_scale

    output_data = np.squeeze(output_data)
    return (output_data > 0.5).astype(np.uint8)




def calculate_iou(y_true, y_pred):
    """Calculates the Intersection over Union (Accuracy metric)"""
    if y_true is None:
        return 0.0
    intersection = np.logical_and(y_true, y_pred).sum()
    union = np.logical_or(y_true, y_pred).sum()
    if union == 0:
        return 1.0 if intersection == 0 else 0.0
    return intersection / union


def display_comparison(original_img, ground_truth, base_mask, fine_mask, base_iou, fine_iou, save_path):
    """Draws a 4-panel comparison showing exact differences in accuracy."""

    # Create the overlays
    base_overlay = np.array(original_img).copy()
    base_overlay[base_mask == 1] = [255, 0, 0]  # Red for baseline predictions

    fine_overlay = np.array(original_img).copy()
    fine_overlay[fine_mask == 1] = [0, 255, 0]  # Green for finetuned predictions

    gt_visual = ground_truth * 255 if ground_truth is not None else np.zeros((IMG_SIZE, IMG_SIZE))

    plt.figure(figsize=(20, 5))

    # Panel 1: Original Image
    plt.subplot(1, 4, 1)
    plt.title("Original Image")
    plt.imshow(original_img)
    plt.axis('off')

    # Panel 2: Ground Truth
    plt.subplot(1, 4, 2)
    plt.title("Ground Truth Mask")
    plt.imshow(gt_visual, cmap='gray')
    plt.axis('off')

    # Panel 3: Baseline Overlay + Accuracy
    plt.subplot(1, 4, 3)
    plt.title(f"Baseline Overlay\nIoU Accuracy: {base_iou:.2%}", color='red' if base_iou < fine_iou else 'black')
    plt.imshow(base_overlay)
    plt.axis('off')

    # Panel 4: Finetuned Overlay + Accuracy
    plt.subplot(1, 4, 4)
    plt.title(f"Finetuned Overlay\nIoU Accuracy: {fine_iou:.2%}", color='green' if fine_iou >= base_iou else 'black')
    plt.imshow(fine_overlay)
    plt.axis('off')

    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()


# --- 2. Run Test on Sample Images ---
os.makedirs("output/comparisons", exist_ok=True)
all_files = glob.glob(os.path.join(TEST_IMAGE_DIR, "*.*"))
test_images = [f for f in all_files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

if not test_images:
    print(f"No test images found in {TEST_IMAGE_DIR}!")
else:
    total_base_iou = 0
    total_fine_iou = 0
    valid_images = 0

    for img_path in test_images:
        filename = os.path.basename(img_path)
        base_name = os.path.splitext(filename)[0]

        mask_path = os.path.join(TEST_MASK_DIR, filename)
        if not os.path.exists(mask_path):
            mask_path = os.path.join(TEST_MASK_DIR, base_name + ".png")

        # 1. Ground Truth
        ground_truth_mask = load_ground_truth(mask_path)
        if ground_truth_mask is None:
            continue

        valid_images += 1

        # 2. Baseline Prediction
        base_input_tensor, original_resized = preprocess_image(img_path, baseline_interpreter)
        raw_base_mask = predict_mask(baseline_interpreter, base_input_tensor)
        base_iou = calculate_iou(ground_truth_mask, raw_base_mask)

        # 3. Finetuned Prediction
        fine_input_tensor, _ = preprocess_image(img_path, finetuned_interpreter)
        raw_fine_mask = predict_mask(finetuned_interpreter, fine_input_tensor)
        fine_iou = calculate_iou(ground_truth_mask, raw_fine_mask)

        # Track totals
        total_base_iou += base_iou
        total_fine_iou += fine_iou

        # 4. Save output
        save_name = f"output/comparisons/comparison_{base_name}.png"
        display_comparison(original_resized, ground_truth_mask, raw_base_mask, raw_fine_mask, base_iou, fine_iou,
                           save_name)
        print(f"[{base_name}] Baseline IoU: {base_iou:.2%} | Finetuned IoU: {fine_iou:.2%} -> Saved to {save_name}")

    # Final Summary
    if valid_images > 0:
        print("\n=== FINAL DATASET SUMMARY ===")
        print(f"Average Baseline Accuracy (IoU)  : {total_base_iou / valid_images:.2%}")
        print(f"Average Finetuned Accuracy (IoU) : {total_fine_iou / valid_images:.2%}")