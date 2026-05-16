import numpy as np
import cv2
from PIL import Image

try:
    from tflite_runtime.interpreter import Interpreter, load_delegate
except ImportError:
    import tensorflow as tf

    Interpreter = tf.lite.Interpreter
    load_delegate = tf.lite.experimental.load_delegate

# --- Model Paths (Make sure these are correct!) ---
ROAD_MODEL_PATH = "mobilenetv2_tpu_segmentation_road_real.tflite"
CAR_MODEL_PATH = "your_car_model.tflite"
IMG_SIZE = 224


class EdgeTPUSegmentationModel:
    def __init__(self, model_path):
        print(f"Loading model: {model_path}...")
        try:
            delegate = load_delegate('libedgetpu.so.1.0')
            self.interpreter = Interpreter(model_path=model_path, experimental_delegates=[delegate])
        except (ValueError, OSError) as e:
            print(f"Warning: Edge TPU delegate not found ({e}). Falling back to CPU.")
            self.interpreter = Interpreter(model_path=model_path)

        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()[0]
        self.output_details = self.interpreter.get_output_details()[0]
        self.input_scale, self.input_zero_point = self.input_details['quantization']
        self.output_scale, self.output_zero_point = self.output_details['quantization']

    def preprocess(self, frame_rgb):
        """Converts an OpenCV live frame (RGB array) into the TFLite tensor."""
        img = Image.fromarray(frame_rgb)
        img_resized = img.resize((IMG_SIZE, IMG_SIZE), Image.Resampling.BILINEAR)

        input_data = np.array(img_resized, dtype=np.float32)
        input_data = (input_data / 127.5) - 1.0

        if self.input_scale != 0:
            input_data = (input_data / self.input_scale) + self.input_zero_point
            input_data = np.clip(input_data, -128, 127).astype(np.int8)

        return np.expand_dims(input_data, axis=0)

    def predict(self, input_tensor):
        self.interpreter.set_tensor(self.input_details['index'], input_tensor)
        self.interpreter.invoke()
        output_data = self.interpreter.get_tensor(self.output_details['index'])[0]

        if self.output_scale != 0:
            output_data = (output_data.astype(np.float32) - self.output_zero_point) * self.output_scale

        output_data = np.squeeze(output_data)
        return (output_data > 0.5).astype(np.uint8)


def post_process_mask(binary_mask):
    kernel_v = np.ones((35, 5), np.uint8)
    closed_v = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel_v)
    kernel_h = np.ones((5, 35), np.uint8)
    closed_h = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel_h)
    return cv2.bitwise_or(closed_v, closed_h)


class VisionPipeline:
    """Wrapper class to be imported into main.py"""

    def __init__(self):
        self.road_model = EdgeTPUSegmentationModel(ROAD_MODEL_PATH)
        self.car_model = EdgeTPUSegmentationModel(CAR_MODEL_PATH)

    def process_frame(self, frame_bgr):
        # 1. Convert OpenCV BGR to RGB
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

        # 2. Preprocess & Predict
        in_road = self.road_model.preprocess(frame_rgb)
        in_car = self.car_model.preprocess(frame_rgb)

        raw_road = self.road_model.predict(in_road)
        raw_car = self.car_model.predict(in_car)

        # 3. Post Process
        final_road = post_process_mask(raw_road)
        final_car = post_process_mask(raw_car)

        # 4. Check status
        if np.count_nonzero(final_car) == 0:
            return "NO_CAR"

        overlap = cv2.bitwise_and(final_road, final_car)
        if np.count_nonzero(overlap) == 0:
            return "VIOLATION"

        return "CLEAR"  # Changed from "OK" to "CLEAR" to match your UI states