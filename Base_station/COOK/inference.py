import cv2
import numpy as np
import tensorflow as tf
import os

# --- Configuration ---
MODEL_PATH = "export/model_quantized.tflite"
TEST_IMG_PATH = "../test_images/c5087c45-3d15-442b-b6ad-1d4d6590fab4.jpeg"
INPUT_SIZE = 320
CONFIDENCE_THRESHOLD = 0.5
IOU_THRESHOLD = 0.4  # For NMS duplicate removal


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

    # SSD decoding math (reversing the targets)
    pred_cx = (pred_offsets[:, 0] / 10.0) * a_w + a_cx
    pred_cy = (pred_offsets[:, 1] / 10.0) * a_h + a_cy
    pred_w = np.exp(pred_offsets[:, 2] / 5.0) * a_w
    pred_h = np.exp(pred_offsets[:, 3] / 5.0) * a_h

    xmin = pred_cx - pred_w / 2.0
    ymin = pred_cy - pred_h / 2.0
    xmax = pred_cx + pred_w / 2.0
    ymax = pred_cy + pred_h / 2.0

    return np.stack([ymin, xmin, ymax, xmax], axis=-1)  # TF NMS expects ymin, xmin, ymax, xmax


def main():
    # 1. Load TFLite Model
    interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()[0]
    output_details = interpreter.get_output_details()

    # TFLite sometimes scrambles output order, so we map them by shape
    out_map = {}
    for d in output_details:
        shape = d['shape']
        if shape[-1] == 1:
            out_map['cls'] = d
        elif shape[-1] == 4:
            out_map['box'] = d
        elif shape[-1] == 16:
            out_map['kpt'] = d

    # 2. Load and Preprocess Image
    original_img = cv2.imread(TEST_IMG_PATH)
    if original_img is None:
        raise FileNotFoundError(f"Could not find image at {TEST_IMG_PATH}")

    img_h, img_w, _ = original_img.shape

    img = cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (INPUT_SIZE, INPUT_SIZE))
    img_float = img.astype(np.float32) / 255.0
    input_data = np.expand_dims(img_float, axis=0)

    # Handle INT8 Quantization Input
    if input_details['dtype'] == np.int8:
        scale, zero_point = input_details['quantization']
        input_data = (input_data / scale + zero_point).astype(np.int8)

    # 3. Run Inference
    interpreter.set_tensor(input_details['index'], input_data)
    interpreter.invoke()

    # Extract and Dequantize Outputs
    def get_output(name):
        detail = out_map[name]
        data = interpreter.get_tensor(detail['index'])[0]  # remove batch dim
        if detail['dtype'] == np.int8:
            scale, zero_point = detail['quantization']
            data = (data.astype(np.float32) - zero_point) * scale
        return data

    pred_cls = get_output('cls').flatten()
    pred_box = get_output('box')
    pred_kpt = get_output('kpt')

    # 4. Decode Anchors and Filter
    anchors = generate_anchors()
    decoded_boxes = decode_boxes(pred_box, anchors)

    # Apply Non-Maximum Suppression (NMS)
    selected_indices = tf.image.non_max_suppression(
        boxes=decoded_boxes,
        scores=pred_cls,
        max_output_size=10,  # Max cars to detect
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
        cv2.putText(original_img, f"{score:.2f}", (pix_xmin, pix_ymin - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Decode and Draw Keypoints
        for i in range(8):
            # Keypoints were trained bbox-relative [0 to 1], so we multiply by box size and add box x/y
            kx_rel = kpts[i * 2]
            ky_rel = kpts[i * 2 + 1]

            pix_kx = int(kx_rel * pix_w + pix_xmin)
            pix_ky = int(ky_rel * pix_h + pix_ymin)

            cv2.circle(original_img, (pix_kx, pix_ky), radius=4, color=(0, 0, 255), thickness=-1)

    # 6. Show the Image
    cv2.namedWindow("Detection Results", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Detection Results", 1280, 720)
    cv2.imshow("Detection Results", original_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()