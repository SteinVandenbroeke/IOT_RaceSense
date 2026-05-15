import numpy as np
import tensorflow as tf
import matplotlib

matplotlib.use('Agg')  # Forces headless mode
import matplotlib.pyplot as plt
from PIL import Image
import cv2
import glob
import os
import random
import io
from flask import Flask, send_file

# --- Configuration ---
MODEL_PATH = "mobilenetv2_tpu_segmentation.tflite"
TEST_IMAGE_DIR = "../../test_images"
IMG_SIZE = 224

# --- Initialize Flask ---
app = Flask(__name__)

# --- Load the TFLite Model ---
# Note: If running on the actual Coral TPU later, you'd use tflite_runtime
# and load the libedgetpu delegate here.
interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()[0]
output_details = interpreter.get_output_details()[0]

input_scale, input_zero_point = input_details['quantization']
output_scale, output_zero_point = output_details['quantization']


def preprocess_image(image_path):
    img = Image.open(image_path).convert('RGB')
    img_resized = img.resize((IMG_SIZE, IMG_SIZE), Image.Resampling.BILINEAR)

    input_data = np.array(img_resized, dtype=np.float32)
    input_data = (input_data / 127.5) - 1.0

    if input_scale != 0:
        input_data = (input_data / input_scale) + input_zero_point
        input_data = np.clip(input_data, -128, 127).astype(np.int8)

    return np.expand_dims(input_data, axis=0), img_resized



def predict_mask(input_tensor):
    interpreter.set_tensor(input_details['index'], input_tensor)
    interpreter.invoke()

    output_data = interpreter.get_tensor(output_details['index'])[0]

    if output_scale != 0:
        output_data = (output_data.astype(np.float32) - output_zero_point) * output_scale

    output_data = np.squeeze(output_data)
    binary_mask = (output_data > 0.5).astype(np.uint8)
    return binary_mask


def post_process_mask(binary_mask):
    kernel_v = np.ones((35, 5), np.uint8)
    closed_v = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel_v)

    kernel_h = np.ones((5, 35), np.uint8)
    closed_h = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel_h)

    combined_mask = cv2.bitwise_or(closed_v, closed_h)
    return combined_mask


def create_result_buffer(original_img, raw_mask, processed_mask):
    """Draws a 5-panel comparison and returns it as an in-memory byte buffer."""
    raw_visual = raw_mask * 255
    proc_visual = processed_mask * 255

    overlay = np.array(original_img).copy()
    overlay[processed_mask == 1] = [255, 0, 0]

    plt.figure(figsize=(20, 3))

    plt.subplot(1, 5, 1)
    plt.title("Original Image")
    plt.imshow(original_img)
    plt.axis('off')

    plt.subplot(1, 5, 2)
    plt.title("Raw Prediction")
    plt.imshow(raw_visual, cmap='gray')
    plt.axis('off')

    plt.subplot(1, 5, 3)
    plt.title("Processed (Closed gaps)")
    plt.imshow(proc_visual, cmap='gray')
    plt.axis('off')

    plt.subplot(1, 5, 4)
    plt.title("Final Overlay")
    plt.imshow(overlay)
    plt.axis('off')

    plt.tight_layout()

    # Save to a memory buffer instead of the disk
    img_io = io.BytesIO()
    plt.savefig(img_io, format='png')
    img_io.seek(0)
    plt.close()

    return img_io


# --- Flask Routes ---
@app.route('/')
def serve_inference_image():
    all_files = glob.glob(os.path.join(TEST_IMAGE_DIR, "*.*"))
    test_images = [f for f in all_files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    if not test_images:
        return "No test images found in the configured directory!", 404

    # Pick a random image on every page refresh
    img_path = random.choice(test_images)
    filename = os.path.basename(img_path)
    base_name = os.path.splitext(filename)[0]


    print(f"Serving inference for: {filename}")

    # Run Pipeline
    input_tensor, original_resized = preprocess_image(img_path)
    raw_predicted_mask = predict_mask(input_tensor)
    processed_mask = post_process_mask(raw_predicted_mask)

    # Generate Image Buffer
    img_buffer = create_result_buffer(original_resized, raw_predicted_mask, processed_mask)

    # Serve the image directly to the browser
    return send_file(img_buffer, mimetype='image/png')


if __name__ == "__main__":
    print("\nStarting Web Server on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)