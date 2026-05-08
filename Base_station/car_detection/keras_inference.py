import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # Forces TensorFlow to use the CPU

import cv2
import numpy as np
import tensorflow as tf

# --- Configuration ---
MODEL_PATH = "checkpoints/model_phase2.keras"  # Point to your Keras model!
TEST_IMG_PATH = "carla_dataset/images/train/Angled_Street_ClearNoon_mkz_2020_BWD_2662.png"
INPUT_SIZE = 320
CONFIDENCE_THRESHOLD = 0.5
IOU_THRESHOLD = 0.4


def generate_anchors(fm_sizes=[20, 10], scales=[0.2, 0.5, 0.9]):
    """Re-generate the 3000 anchors for decoding."""
    anchors = []
    for k, fm_size in enumerate(fm_sizes):
        scale, next_scale = scales[k], scales[k + 1]
        step = 1.0 / fm_size
        x = np.linspace(step / 2.0, 1.0 - step / 2.0, fm_size)
        y = np.linspace(step / 2.0, 1.0 - step / 2.0, fm_size)
        xv, yv = np.meshgrid(x, y)
        cx, cy = xv.ravel(), yv.ravel()

        widths, heights = [], []
        widths.extend([scale, np.sqrt(scale * next_scale)])
        heights.extend([scale, np.sqrt(scale * next_scale)])
        for ar in [2.0, 0.5, 3.0, 0.3333]:
            widths.append(scale * np.sqrt(ar))
            heights.append(scale / np.sqrt(ar))

        for i in range(len(cx)):
            for j in range(6):
                cw, ch = widths[j], heights[j]
                anchors.append([cx[i] - cw / 2, cy[i] - ch / 2, cx[i] + cw / 2, cy[i] + ch / 2])
    return np.clip(anchors, 0.0, 1.0)


def decode_boxes(pred_offsets, anchors):
    """Convert network offsets back into image coordinates."""
    a_w = anchors[:, 2] - anchors[:, 0]
    a_h = anchors[:, 3] - anchors[:, 1]
    a_cx = anchors[:, 0] + a_w / 2.0
    a_cy = anchors[:, 1] + a_h / 2.0

    # SSD decoding math
    pred_cx = (pred_offsets[:, 0] / 10.0) * a_w + a_cx
    pred_cy = (pred_offsets[:, 1] / 10.0) * a_h + a_cy
    pred_w = np.exp(pred_offsets[:, 2] / 5.0) * a_w
    pred_h = np.exp(pred_offsets[:, 3] / 5.0) * a_h

    xmin = pred_cx - pred_w / 2.0
    ymin = pred_cy - pred_h / 2.0
    xmax = pred_cx + pred_w / 2.0
    ymax = pred_cy + pred_h / 2.0

    return np.stack([ymin, xmin, ymax, xmax], axis=-1)


def main():
    # 1. Load the Keras Model
    # compile=False is used because we don't need the custom loss function for inference
    print(f"Loading model from {MODEL_PATH}...")
    model = tf.keras.models.load_model(MODEL_PATH, compile=False)

    # 2. Load and Preprocess Image
    original_img = cv2.imread(TEST_IMG_PATH)
    if original_img is None:
        raise FileNotFoundError(f"Could not find image at {TEST_IMG_PATH}")

    # Scale down massive images for UI visibility
    MAX_DIMENSION = 1280
    h, w = original_img.shape[:2]
    if max(h, w) > MAX_DIMENSION:
        scale = MAX_DIMENSION / max(h, w)
        original_img = cv2.resize(original_img, (int(w * scale), int(h * scale)))

    img_h, img_w, _ = original_img.shape

    img = cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (INPUT_SIZE, INPUT_SIZE))
    img_float = img.astype(np.float32) / 255.0
    input_data = np.expand_dims(img_float, axis=0)

    # 3. Run Inference
    print("Running inference...")
    preds = model.predict(input_data, verbose=0)

    # Keras models usually return a list/tuple of outputs.
    # Assuming your model outputs: [Classification, BoundingBox, Keypoints]
    pred_cls = preds[0][0]  # Remove batch dimension
    pred_box = preds[1][0]
    pred_kpt = preds[2][0]

    # Flatten classification scores
    pred_cls = pred_cls.flatten()

    # 4. Decode Anchors and Filter
    anchors = generate_anchors()
    decoded_boxes = decode_boxes(pred_box, anchors)

    # Apply Non-Maximum Suppression (NMS)
    selected_indices = tf.image.non_max_suppression(
        boxes=decoded_boxes,
        scores=pred_cls,
        max_output_size=10,
        iou_threshold=IOU_THRESHOLD,
        score_threshold=CONFIDENCE_THRESHOLD
    ).numpy()

    print(f"Detected {len(selected_indices)} cars!")

    # 5. Draw Results
    for idx in selected_indices:
        score = pred_cls[idx]
        box = decoded_boxes[idx]
        kpts = pred_kpt[idx]

        # Convert box from normalized [ymin, xmin, ymax, xmax] to pixel [xmin, ymin, xmax, ymax]
        ymin, xmin, ymax, xmax = box
        pix_xmin = int(xmin * img_w)
        pix_ymin = int(ymin * img_h)
        pix_xmax = int(xmax * img_w)
        pix_ymax = int(ymax * img_h)
        pix_w = pix_xmax - pix_xmin
        pix_h = pix_ymax - pix_ymin

        # Draw Bounding Box
        cv2.rectangle(original_img, (pix_xmin, pix_ymin), (pix_xmax, pix_ymax), (0, 255, 0), 2)

        # --- UI Fix: Draw a black background for the text ---
        text = f"{score:.2f}"
        (text_w, text_h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
        cv2.rectangle(original_img, (pix_xmin, pix_ymin - 20), (pix_xmin + text_w, pix_ymin), (0, 0, 0), -1)

        # Draw the bright green text over the black box
        cv2.putText(original_img, text, (pix_xmin, pix_ymin - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Decode and Draw Keypoints (Now expecting 4 keypoints!)
        for i in range(4):
            kx_rel = kpts[i * 2]
            ky_rel = kpts[i * 2 + 1]

            # Standard clean math (No hacks required)
            pix_kx = int(kx_rel * pix_w + pix_xmin)
            pix_ky = int(ky_rel * pix_h + pix_ymin)

            cv2.circle(original_img, (pix_kx, pix_ky), radius=4, color=(0, 0, 255), thickness=-1)

    # 6. Show the Image
    cv2.namedWindow("Keras Detection Results", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Keras Detection Results", 1280, 720)
    cv2.imshow("Keras Detection Results", original_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()