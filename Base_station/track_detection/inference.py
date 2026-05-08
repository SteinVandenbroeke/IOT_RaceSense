import cv2
import numpy as np
import tensorflow as tf
import os

# --- Configuration ---
MODEL_PATH = "export/track_mask_quantized.tflite"
TEST_IMG_PATH = "../test_images/High_Curve_ClearNoon_model3_BWD_6577.png"
INPUT_SIZE = 320  # Must match the config.py used during training
THRESHOLD = 0.7  # Probability threshold to consider a pixel as "Track"


def main():
    # 1. Load TFLite Model
    interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()[0]
    output_details = interpreter.get_output_details()[0]

    # 2. Load and Preprocess Image
    original_img = cv2.imread(TEST_IMG_PATH)
    if original_img is None:
        raise FileNotFoundError(f"Could not find image at {TEST_IMG_PATH}")

    # Keep a copy of the original dimensions to resize the mask later
    orig_h, orig_w = original_img.shape[:2]

    # Resize image for the model
    img = cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB)
    img_resized = cv2.resize(img, (INPUT_SIZE, INPUT_SIZE))
    img_float = img_resized.astype(np.float32) / 255.0
    input_data = np.expand_dims(img_float, axis=0)

    # Handle INT8 Quantization Input
    if input_details['dtype'] == np.int8:
        scale, zero_point = input_details['quantization']
        input_data = (input_data / scale + zero_point).astype(np.int8)

    # 3. Run Inference
    interpreter.set_tensor(input_details['index'], input_data)
    interpreter.invoke()

    # 4. Extract and Dequantize Output Mask
    mask_data = interpreter.get_tensor(output_details['index'])[0]  # Remove batch dimension

    if output_details['dtype'] == np.int8:
        scale, zero_point = output_details['quantization']
        mask_data = (mask_data.astype(np.float32) - zero_point) * scale

    # The mask is shape (512, 512, 1). Squeeze it to (512, 512)
    mask_data = np.squeeze(mask_data)

    # 5. Process the Mask
    # Create a binary mask: pixels > 0.5 become 255 (white), else 0 (black)
    binary_mask = (mask_data > THRESHOLD).astype(np.uint8) * 255

    # Blow the 512x512 mask back up to the original camera resolution
    # We use NEAREST interpolation to keep the mask edges sharp
    full_res_mask = cv2.resize(binary_mask, (orig_w, orig_h), interpolation=cv2.INTER_NEAREST)

    # 6. Draw Results (Create a green overlay for the track limits)
    # Create a solid green image the same size as the original
    green_overlay = np.zeros_like(original_img)
    green_overlay[:, :] = (0, 255, 0)  # BGR format: Green

    # Use the binary mask to only keep the green where the track is
    track_highlight = cv2.bitwise_and(green_overlay, green_overlay, mask=full_res_mask)

    # Blend the highlight over the original image (50% transparency)
    # We only apply the blend where the mask is present to keep the rest of the image untouched
    alpha = 0.5
    cv2.addWeighted(track_highlight, alpha, original_img, 1 - alpha, 0, original_img)

    # 7. Show the Image
    cv2.namedWindow("Track Limits Detection", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Track Limits Detection", 1280, 720)
    cv2.imshow("Track Limits Detection", original_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()