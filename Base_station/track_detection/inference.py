from flask import Flask, Response
import cv2
import numpy as np
import tensorflow as tf
import os

app = Flask(__name__)

# --- Configuration ---
MODEL_PATH = "export/track_mask_quantized.tflite"
TEST_IMG_PATH = "../test_images/High_Curve_ClearNoon_model3_BWD_6577.png"
INPUT_SIZE = 320  # Must match the config.py used during training
THRESHOLD = 0.7  # Probability threshold to consider a pixel as "Track"

# 1. Load TFLite Model (Initialized globally for performance)
interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()[0]
output_details = interpreter.get_output_details()[0]


@app.route('/')
def serve_inference_image():
    # 2. Load and Preprocess Image
    original_img = cv2.imread(TEST_IMG_PATH)
    if original_img is None:
        return f"Error: Could not find image at {TEST_IMG_PATH}", 404

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
    mask_data = interpreter.get_tensor(output_details['index'])[0]

    if output_details['dtype'] == np.int8:
        scale, zero_point = output_details['quantization']
        mask_data = (mask_data.astype(np.float32) - zero_point) * scale

    mask_data = np.squeeze(mask_data)

    # 5. Process the Mask
    binary_mask = (mask_data > THRESHOLD).astype(np.uint8) * 255
    full_res_mask = cv2.resize(binary_mask, (orig_w, orig_h), interpolation=cv2.INTER_NEAREST)

    # 6. Draw Results (Create a green overlay)
    green_overlay = np.zeros_like(original_img)
    green_overlay[:, :] = (0, 255, 0)  # Green in BGR

    track_highlight = cv2.bitwise_and(green_overlay, green_overlay, mask=full_res_mask)

    alpha = 0.5
    cv2.addWeighted(track_highlight, alpha, original_img, 1 - alpha, 0, original_img)

    # Convert the processed image to JPEG bytes
    success, encoded_image = cv2.imencode('.jpg', original_img)
    if not success:
        return "Error: Could not encode image", 500

    # 7. Send the image bytes to the web browser
    return Response(encoded_image.tobytes(), mimetype='image/jpeg')


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)