import numpy as np
import cv2
import time
from PIL import Image
from tflite_runtime.interpreter import Interpreter, load_delegate

# --- Model Paths (Make sure these are correct!) ---
ROAD_MODEL_PATH = "models/mobilenetv2_tpu_segmentation_road_real.tflite"
CAR_MODEL_PATH = "models/mobilenetv2_tpu_segmentation_car_real.tflite"
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
        # 1. Fast resize using OpenCV
        img_resized = cv2.resize(frame_rgb, (IMG_SIZE, IMG_SIZE), interpolation=cv2.INTER_LINEAR)

        # 2. INT8 FAST PATH: Bypass all float32 division!
        # If your model takes int8 (-128 to 127) and the image is uint8 (0 to 255):
        if self.input_details['dtype'] == np.int8:
            # Shift the uint8 range down to int8 range using fast numpy integer math
            input_data = np.clip(img_resized.astype(np.int16) - 128, -128, 127).astype(np.int8)
            return np.expand_dims(input_data, axis=0)

        # 3. UINT8 FAST PATH (if your model takes 0-255 natively)
        elif self.input_details['dtype'] == np.uint8:
            return np.expand_dims(img_resized, axis=0)

        # Fallback (Only if you are accidentally using an unquantized float model)
        else:
            input_data = np.array(img_resized, dtype=np.float32)
            input_data = (input_data / 127.5) - 1.0
            return np.expand_dims(input_data, axis=0)

        return np.expand_dims(input_data, axis=0)

    def predict(self, input_tensor):
        self.interpreter.set_tensor(self.input_details['index'], input_tensor)

        # --- TIMING BLOCK ---
        start_time = time.perf_counter()
        self.interpreter.invoke()
        end_time = time.perf_counter()

        ms_taken = (end_time - start_time) * 1000
        print(f"Model Execution Time: {ms_taken:.2f} ms")
        # --------------------

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

    def __init__(self, road_update_interval=100, overlap_threshold=0.05):
        self.road_model = EdgeTPUSegmentationModel(ROAD_MODEL_PATH)
        self.car_model = EdgeTPUSegmentationModel(CAR_MODEL_PATH)

        # Caching variables
        self.cached_road_mask = None
        self.frame_counter = 0
        self.road_update_interval = road_update_interval
        self.overlap_threshold = overlap_threshold

    def process_frame(self, frame_bgr):
        # 1. Convert OpenCV BGR to RGB
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

        # 2. Process CAR first (Runs every frame)
        in_car = self.car_model.preprocess(frame_rgb)
        raw_car = self.car_model.predict(in_car)
        # final_car = post_process_mask(raw_car)

        # 3. Early Exit: If no car, don't waste time on the road model!
        # (Using cv2.countNonZero is slightly faster than np.count_nonzero)
        car_pixels = cv2.countNonZero(raw_car)
        if car_pixels <= 10:
            self.frame_counter += 1
            return "SCANNING"

        # 4. Process ROAD only if missing OR if it's time for an update
        if self.cached_road_mask is None or self.frame_counter % self.road_update_interval == 0:
            in_road = self.road_model.preprocess(frame_rgb)
            raw_road = self.road_model.predict(in_road)
            self.cached_road_mask = post_process_mask(raw_road)

        self.frame_counter += 1

        # 5. Check status against the cached road mask
        overlap = cv2.bitwise_and(self.cached_road_mask, raw_car)
        overlap_pixels = cv2.countNonZero(overlap)

        overlap_ratio = overlap_pixels / car_pixels

        if overlap_ratio <= self.overlap_threshold:
            return "VIOLATION"

        return "CLEAR"