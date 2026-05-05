"""
train.py — Two-Phase Training Loop
"""
import tensorflow as tf
from model import build_model
from dataset import build_dataset
from config import *
import numpy as np
import os

def generate_anchors():
    """
    Generates 3000 SSD anchors for MobileNetV2 feature maps.
    - Feature map 1: 20x20 grid (400 cells * 6 anchors = 2400)
    - Feature map 2: 10x10 grid (100 cells * 6 anchors = 600)
    Total = 3000 anchors.
    """
    feature_map_sizes = [20, 10]
    scales = [0.2, 0.5, 0.9]  # Min and max scales (zoom levels) for the boxes

    # Standard SSD aspect ratios for 6 anchors per cell
    aspect_ratios = [1.0, 2.0, 0.5, 3.0, 0.3333]

    anchors = []

    for k, fm_size in enumerate(feature_map_sizes):
        scale = scales[k]
        next_scale = scales[k + 1]

        # Grid center coordinates (normalized 0.0 to 1.0)
        step = 1.0 / fm_size
        x = np.linspace(step / 2.0, 1.0 - step / 2.0, fm_size)
        y = np.linspace(step / 2.0, 1.0 - step / 2.0, fm_size)
        xv, yv = np.meshgrid(x, y)

        cx = xv.ravel()
        cy = yv.ravel()

        # Define the 6 anchor dimensions for this feature map
        widths = []
        heights = []

        # 1. Aspect ratio 1.0 (Standard)
        widths.append(scale)
        heights.append(scale)

        # 2. Aspect ratio 1.0 (Larger scale for smooth transition)
        larger_scale = np.sqrt(scale * next_scale)
        widths.append(larger_scale)
        heights.append(larger_scale)

        # 3-6. Other aspect ratios (Wide and Tall boxes)
        for ar in [2.0, 0.5, 3.0, 0.3333]:
            widths.append(scale * np.sqrt(ar))
            heights.append(scale / np.sqrt(ar))

        # Create anchors for every grid center
        for i in range(len(cx)):
            for j in range(6):
                cw = widths[j]
                ch = heights[j]

                # Convert center, width, height to xmin, ymin, xmax, ymax
                xmin = cx[i] - (cw / 2.0)
                ymin = cy[i] - (ch / 2.0)
                xmax = cx[i] + (cw / 2.0)
                ymax = cy[i] + (ch / 2.0)

                anchors.append([xmin, ymin, xmax, ymax])

    # Clip anchors to stay within the image boundaries
    anchors = np.clip(anchors, 0.0, 1.0)

    # Return as a TensorFlow constant
    return tf.constant(anchors, dtype=tf.float32)

def calculate_iou(gt_boxes, anchors):
    """
    Calculates the Intersection over Union (IoU) between batched ground truth boxes and anchors.
    gt_boxes: [Batch, Num_Objects, 4]  (format: xmin, ymin, xmax, ymax)
    anchors:  [Num_Anchors, 4]         (format: xmin, ymin, xmax, ymax)
    Returns:  [Batch, Num_Objects, Num_Anchors]
    """
    # Expand dimensions for broadcasting
    gt_boxes = tf.expand_dims(gt_boxes, axis=2)  # [B, N, 1, 4]
    anchors = tf.expand_dims(tf.expand_dims(anchors, axis=0), axis=0)  # [1, 1, A, 4]

    # Get intersections
    inter_ymin = tf.maximum(gt_boxes[..., 1], anchors[..., 1])
    inter_xmin = tf.maximum(gt_boxes[..., 0], anchors[..., 0])
    inter_ymax = tf.minimum(gt_boxes[..., 3], anchors[..., 3])
    inter_xmax = tf.minimum(gt_boxes[..., 2], anchors[..., 2])

    inter_h = tf.maximum(0.0, inter_ymax - inter_ymin)
    inter_w = tf.maximum(0.0, inter_xmax - inter_xmin)
    intersection = inter_h * inter_w

    # Get areas
    gt_area = tf.maximum(0.0, gt_boxes[..., 3] - gt_boxes[..., 1]) * tf.maximum(0.0,
                                                                                gt_boxes[..., 2] - gt_boxes[..., 0])
    anchor_area = tf.maximum(0.0, anchors[..., 3] - anchors[..., 1]) * tf.maximum(0.0,
                                                                                  anchors[..., 2] - anchors[..., 0])

    union = gt_area + anchor_area - intersection
    iou = intersection / tf.maximum(union, 1e-8)

    return iou  # Shape: [Batch, Max_Objects, Num_Anchors]


def encode_box_targets(matched_gt_boxes, anchors):
    """
    Converts absolute bounding box coordinates into anchor-relative offsets.
    This is what the SSD model actually predicts!
    """
    # Convert corners to center, width, height
    gt_w = matched_gt_boxes[..., 2] - matched_gt_boxes[..., 0]
    gt_h = matched_gt_boxes[..., 3] - matched_gt_boxes[..., 1]
    gt_cx = matched_gt_boxes[..., 0] + (gt_w / 2.0)
    gt_cy = matched_gt_boxes[..., 1] + (gt_h / 2.0)

    a_w = anchors[..., 2] - anchors[..., 0]
    a_h = anchors[..., 3] - anchors[..., 1]
    a_cx = anchors[..., 0] + (a_w / 2.0)
    a_cy = anchors[..., 1] + (a_h / 2.0)

    # Encode to offsets (with scaling factors commonly used in SSD)
    tx = (gt_cx - a_cx) / a_w * 10.0
    ty = (gt_cy - a_cy) / a_h * 10.0
    tw = tf.math.log(tf.maximum(gt_w / a_w, 1e-8)) * 5.0
    th = tf.math.log(tf.maximum(gt_h / a_h, 1e-8)) * 5.0

    return tf.stack([tx, ty, tw, th], axis=-1)


def match_anchors(gt_boxes, gt_kpts, gt_valid, anchors, iou_threshold=0.5):
    """
    Assigns each anchor to the best ground truth object.
    """
    batch_size = tf.shape(gt_boxes)[0]
    num_anchors = tf.shape(anchors)[0]

    # 1. Calculate IoU [Batch, Num_Objects, Num_Anchors]
    iou_matrix = calculate_iou(gt_boxes, anchors)

    # Ignore padded/invalid objects by zeroing out their IoU
    valid_mask = tf.expand_dims(gt_valid, axis=-1)  # [Batch, Num_Objects, 1]
    iou_matrix = iou_matrix * tf.cast(valid_mask, tf.float32)

    # 2. Find the best ground truth box for EACH anchor
    # max_iou: [Batch, Num_Anchors] (The highest IoU score for each anchor)
    max_iou = tf.reduce_max(iou_matrix, axis=1)

    # best_gt_idx: [Batch, Num_Anchors] (The index of the object with that highest IoU)
    best_gt_idx = tf.argmax(iou_matrix, axis=1, output_type=tf.int32)

    # 3. Gather the actual box and keypoint values using those indices
    matched_gt_boxes = tf.gather(gt_boxes, best_gt_idx, batch_dims=1)
    matched_gt_kpts = tf.gather(gt_kpts, best_gt_idx, batch_dims=1)

    # 4. Create the Positive Mask (1 if IoU > threshold, 0 otherwise)
    mask_positive = tf.cast(max_iou > iou_threshold, tf.float32)

    # 5. Encode the targets (Boxes become offsets, classes become 1s)
    matched_box_targets = encode_box_targets(matched_gt_boxes, anchors)
    matched_cls_targets = tf.expand_dims(mask_positive, axis=-1)  # 1 for Car, 0 for Background

    return matched_cls_targets, matched_box_targets, matched_gt_kpts, mask_positive


def custom_ssd_loss(y_true, y_pred, anchors):
    gt_boxes, gt_kpts, gt_vis, gt_valid = y_true
    pred_cls, pred_box, pred_kpt = y_pred

    # Run the matcher!
    matched_cls_targets, matched_box_targets, matched_kpt_targets, mask_positive = match_anchors(
        gt_boxes, gt_kpts, gt_valid, anchors, iou_threshold=0.5
    )

    # Classification Loss (Binary Crossentropy)
    loss_cls = tf.keras.losses.binary_crossentropy(matched_cls_targets, pred_cls)

    # Bounding Box Loss (Huber)
    loss_box = tf.keras.losses.huber(matched_box_targets, pred_box)
    loss_box = loss_box * mask_positive

    # Keypoint Loss (Huber)
    # We flatten the keypoints so the Huber loss compares the 16 values easily
    pred_kpt_flat = tf.reshape(pred_kpt, [tf.shape(pred_kpt)[0], tf.shape(pred_kpt)[1], 8])
    gt_kpt_flat = tf.reshape(matched_kpt_targets,
                             [tf.shape(matched_kpt_targets)[0], tf.shape(matched_kpt_targets)[1], 8])

    loss_kpt = tf.keras.losses.huber(gt_kpt_flat, pred_kpt_flat)
    loss_kpt = loss_kpt * mask_positive * LAMBDA_KPT

    # Calculate means, ignoring the massive amount of negative anchors for box/kpt loss
    num_positives = tf.maximum(1.0, tf.reduce_sum(mask_positive))

    total_cls_loss = tf.reduce_mean(loss_cls)  # Background is penalized here
    total_box_loss = tf.reduce_sum(loss_box) / num_positives
    total_kpt_loss = tf.reduce_sum(loss_kpt) / num_positives

    return total_cls_loss + total_box_loss + total_kpt_loss


# --- Update the train_step to accept the anchors ---
@tf.function
def train_step(model, optimizer, batch, anchors):
    images, boxes, kpts, vis, valid = batch
    y_true = (boxes, kpts, vis, valid)

    with tf.GradientTape() as tape:
        y_pred = model(images, training=True)
        # Pass the anchors into the custom loss function we wrote earlier
        loss = custom_ssd_loss(y_true, y_pred, anchors)

    gradients = tape.gradient(loss, model.trainable_variables)
    optimizer.apply_gradients(zip(gradients, model.trainable_variables))
    return loss


# --- Update the main train loop ---
def train():
    train_ds = build_dataset(TRAIN_IMG_DIR, TRAIN_LBL_DIR, augment=True)
    val_ds = build_dataset(VAL_IMG_DIR, VAL_LBL_DIR, augment=False)

    model, backbone = build_model()

    # 🌟 GENERATE THE ANCHORS HERE (Just once!)
    anchors = generate_anchors()

    # Define a distinct path for the Phase 1 checkpoint
    phase1_checkpoint_path = f"{CHECKPOINT_DIR}/model_phase1.keras"

    # --- PHASE 1: Checkpoint Check or Train ---
    if os.path.exists(phase1_checkpoint_path):
        print(f"Checkpoint found! Loading Phase 1 weights from {phase1_checkpoint_path}...")
        # Load weights to keep the 'backbone' variable perfectly linked to the model layers
        model.load_weights(phase1_checkpoint_path)
    else:
        print("Starting Phase 1: Freezing backbone...")
        backbone.trainable = False
        optimizer_p1 = tf.keras.optimizers.Adam(learning_rate=LR_PHASE1)

        for epoch in range(EPOCHS_PHASE1):
            for batch in train_ds:
                loss = train_step(model, optimizer_p1, batch, anchors)
            model.save(f"{CHECKPOINT_DIR}/model_phase1.keras")
            print(f"Phase 1 - Epoch {epoch + 1}/{EPOCHS_PHASE1}, Loss: {loss.numpy():.4f}")

        print("Phase 1 complete and saved.")

    # --- PHASE 2: Fine-tune Full Model ---
    print("Starting Phase 2: Unfreezing backbone...")
    backbone.trainable = True
    optimizer_p2 = tf.keras.optimizers.Adam(learning_rate=LR_PHASE2)

    for epoch in range(EPOCHS_PHASE2):
        for batch in train_ds:
            loss = train_step(model, optimizer_p2, batch, anchors)
        model.save(f"{CHECKPOINT_DIR}/model_phase2.keras")
        print(f"Phase 2 - Epoch {epoch + 1}/{EPOCHS_PHASE2}, Loss: {loss.numpy():.4f}")

    print("Training complete.")


if __name__ == "__main__":
    train()