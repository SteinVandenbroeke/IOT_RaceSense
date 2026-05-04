"""
dataset.py — tf.data pipeline for YOLO-style keypoint labels.

Label format (one object per line):
  class xc yc w h  kx1 ky1 v1  kx2 ky2 v2 ... kx8 ky8 v8
  (all values normalised to [0,1] relative to image size)

Keypoints are stored bbox-relative in the returned tensors so the
regression head only needs to predict small offsets.
"""

import os
import tensorflow as tf
import numpy as np
from config import (
    TRAIN_IMG_DIR, TRAIN_LBL_DIR,
    VAL_IMG_DIR,   VAL_LBL_DIR,
    INPUT_SIZE, BATCH_SIZE, NUM_KEYPOINTS,
    AUG_FLIP_PROB, AUG_BRIGHTNESS, AUG_CONTRAST,
)

# ── Label parsing ──────────────────────────────────────────────────────────────

def parse_label_file(label_path: str):
    """
    Reads a single .txt label file and returns numpy arrays.

    Returns
    -------
    boxes   : (N, 4)  float32  [xc, yc, w, h]  image-normalised
    kpts    : (N, 8, 2) float32 [kx, ky]        bbox-relative
    vis     : (N, 8)  float32  visibility flags  {0, 1, 2} → binary mask
    classes : (N,)    int32
    """
    boxes, kpts_list, vis_list, classes = [], [], [], []

    with open(label_path, "r") as f:
        for line in f:
            vals = list(map(float, line.strip().split()))
            if len(vals) < 5 + NUM_KEYPOINTS * 3:
                continue  # skip malformed lines

            cls  = int(vals[0])
            xc, yc, w, h = vals[1], vals[2], vals[3], vals[4]

            kpt_vals = vals[5:]
            kp_xy, kp_v = [], []
            for i in range(NUM_KEYPOINTS):
                kx_img = kpt_vals[i * 3]
                ky_img = kpt_vals[i * 3 + 1]
                v      = kpt_vals[i * 3 + 2]

                # convert from image-normalised → bbox-relative
                # so the model predicts offsets within the box
                if w > 0 and h > 0:
                    kx_rel = (kx_img - (xc - w / 2)) / w
                    ky_rel = (ky_img - (yc - h / 2)) / h
                else:
                    kx_rel, ky_rel = 0.0, 0.0

                kp_xy.append([kx_rel, ky_rel])
                kp_v.append(1.0 if v > 0 else 0.0)  # binary: visible / invisible

            boxes.append([xc, yc, w, h])
            kpts_list.append(kp_xy)
            vis_list.append(kp_v)
            classes.append(cls)

    if not boxes:
        return (
            np.zeros((0, 4),         dtype=np.float32),
            np.zeros((0, NUM_KEYPOINTS, 2), dtype=np.float32),
            np.zeros((0, NUM_KEYPOINTS),    dtype=np.float32),
            np.zeros((0,),           dtype=np.int32),
        )

    return (
        np.array(boxes,      dtype=np.float32),
        np.array(kpts_list,  dtype=np.float32),
        np.array(vis_list,   dtype=np.float32),
        np.array(classes,    dtype=np.int32),
    )


# ── tf.data pipeline ───────────────────────────────────────────────────────────

def load_sample(img_path: str, lbl_path: str, augment: bool = False):
    """
    Loads one image + its labels, resizes, optionally augments.

    Returns
    -------
    image  : (H, W, 3)  float32  scaled to [0, 1]
    boxes  : (N, 4)     float32  [xc, yc, w, h]  image-normalised
    kpts   : (N, 8, 2)  float32  bbox-relative
    vis    : (N, 8)     float32  visibility mask
    """
    # Image
    img_raw = tf.io.read_file(img_path)
    img     = tf.image.decode_image(img_raw, channels=3, expand_animations=False)
    img     = tf.cast(img, tf.float32) / 255.0
    img     = tf.image.resize(img, INPUT_SIZE)

    # Labels (loaded in numpy via py_function for file I/O)
    boxes, kpts, vis, _ = tf.py_function(
        lambda p: parse_label_file(p.numpy().decode()),
        [lbl_path],
        [tf.float32, tf.float32, tf.float32, tf.int32],
    )
    boxes.set_shape([None, 4])
    kpts.set_shape([None, NUM_KEYPOINTS, 2])
    vis.set_shape([None, NUM_KEYPOINTS])

    # Augmentation
    if augment:
        img, boxes, kpts = _augment(img, boxes, kpts)

    return img, boxes, kpts, vis


def _augment(img, boxes, kpts):
    """
    Applies consistent augmentation to image + labels.
    Only operations that keep keypoints valid are used here.
    Geometric: random horizontal flip.
    Photometric: random brightness / contrast.
    """
    # Random horizontal flip
    if tf.random.uniform(()) < AUG_FLIP_PROB:
        img = tf.image.flip_left_right(img)

        # flip box x-centre: xc_new = 1 - xc
        xc = 1.0 - boxes[:, 0:1]
        boxes = tf.concat([xc, boxes[:, 1:]], axis=1)

        # flip keypoint x (bbox-relative): kx_new = 1 - kx
        kx = 1.0 - kpts[:, :, 0:1]
        kpts = tf.concat([kx, kpts[:, :, 1:2]], axis=2)

        # NOTE: if your keypoints have a semantic left/right pairing
        # (e.g. kp0=front-left-corner, kp1=front-right-corner) you need to
        # swap the paired indices here after flipping.
        # Example for 4-pair symmetric keypoints:
        #   indices = tf.constant([1,0, 3,2, 5,4, 7,6])
        #   kpts = tf.gather(kpts, indices, axis=1)

    # Photometric (image only, no label changes needed)
    img = tf.image.random_brightness(img, AUG_BRIGHTNESS)
    img = tf.image.random_contrast(img, 1 - AUG_CONTRAST, 1 + AUG_CONTRAST)
    img = tf.clip_by_value(img, 0.0, 1.0)

    return img, boxes, kpts


def _pad_to_fixed(img, boxes, kpts, vis, max_objects=20):
    """
    Pads boxes/kpts/vis to a fixed number of objects so tf.data
    can batch them. Real objects come first; padding is zeros.
    """
    n = tf.shape(boxes)[0]

    def pad(t, shape):
        pad_rows = max_objects - n
        padding  = tf.zeros([pad_rows] + shape[1:], dtype=t.dtype)
        return tf.concat([t, padding], axis=0)[:max_objects]

    boxes = pad(boxes, [max_objects, 4])
    kpts  = pad(kpts,  [max_objects, NUM_KEYPOINTS, 2])
    vis   = pad(vis,   [max_objects, NUM_KEYPOINTS])

    # Validity mask: 1 for real objects, 0 for padding
    valid = tf.concat(
        [tf.ones(n, dtype=tf.float32),
         tf.zeros(max_objects - n, dtype=tf.float32)],
        axis=0
    )[:max_objects]

    boxes.set_shape([max_objects, 4])
    kpts.set_shape([max_objects, NUM_KEYPOINTS, 2])
    vis.set_shape([max_objects, NUM_KEYPOINTS])
    valid.set_shape([max_objects])

    return img, boxes, kpts, vis, valid


def _collect_paths(img_dir: str, lbl_dir: str):
    img_paths, lbl_paths = [], []
    for fname in sorted(os.listdir(img_dir)):
        stem = os.path.splitext(fname)[0]
        lbl  = os.path.join(lbl_dir, stem + ".txt")
        if os.path.exists(lbl):
            img_paths.append(os.path.join(img_dir, fname))
            lbl_paths.append(lbl)
    return img_paths, lbl_paths


def build_dataset(img_dir: str, lbl_dir: str, augment: bool, max_objects: int = 20):
    """
    Returns a batched, prefetched tf.data.Dataset.

    Each batch yields:
      images : (B, H, W, 3)
      boxes  : (B, max_objects, 4)
      kpts   : (B, max_objects, 8, 2)
      vis    : (B, max_objects, 8)
      valid  : (B, max_objects)   — 1=real object, 0=padding
    """
    img_paths, lbl_paths = _collect_paths(img_dir, lbl_dir)
    print(f"  Found {len(img_paths)} samples in {img_dir}")

    ds = tf.data.Dataset.from_tensor_slices((img_paths, lbl_paths))

    if augment:
        ds = ds.shuffle(buffer_size=len(img_paths), reshuffle_each_iteration=True)

    ds = ds.map(
        lambda ip, lp: load_sample(ip, lp, augment),
        num_parallel_calls=tf.data.AUTOTUNE,
    )
    ds = ds.map(
        lambda img, b, k, v: _pad_to_fixed(img, b, k, v, max_objects),
        num_parallel_calls=tf.data.AUTOTUNE,
    )
    ds = ds.batch(BATCH_SIZE, drop_remainder=False)
    ds = ds.prefetch(tf.data.AUTOTUNE)
    return ds


# ── Quick smoke-test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Building train dataset...")
    train_ds = build_dataset(TRAIN_IMG_DIR, TRAIN_LBL_DIR, augment=True)
    for imgs, boxes, kpts, vis, valid in train_ds.take(1):
        print(f"  images : {imgs.shape}   dtype={imgs.dtype}")
        print(f"  boxes  : {boxes.shape}  dtype={boxes.dtype}")
        print(f"  kpts   : {kpts.shape}   dtype={kpts.dtype}")
        print(f"  vis    : {vis.shape}    dtype={vis.dtype}")
        print(f"  valid  : {valid.shape}  dtype={valid.dtype}")
    print("Dataset OK.")
