import os
import tensorflow as tf
from config import (
    INPUT_SIZE, BATCH_SIZE,
    AUG_FLIP_PROB, AUG_BRIGHTNESS, AUG_CONTRAST
)


def load_and_preprocess(img_path, mask_path):
    # 1. Load and process the Image
    img_raw = tf.io.read_file(img_path)
    img = tf.image.decode_jpeg(img_raw, channels=3)
    img = tf.image.convert_image_dtype(img, tf.float32)
    img = tf.image.resize(img, INPUT_SIZE)

    # 2. Load and process the Mask
    mask_raw = tf.io.read_file(mask_path)
    mask = tf.image.decode_png(mask_raw, channels=1)

    # CRITICAL: Use Nearest Neighbor so 0s and 1s don't become grey decimals
    mask = tf.image.resize(mask, INPUT_SIZE, method=tf.image.ResizeMethod.NEAREST_NEIGHBOR)

    # Ensure mask is strictly binary (0.0 or 1.0)
    mask = tf.cast(mask > 0, tf.float32)

    return img, mask


def augment(img, mask):
    # If we flip the image, we MUST flip the mask exactly the same way
    if tf.random.uniform(()) < AUG_FLIP_PROB:
        img = tf.image.flip_left_right(img)
        mask = tf.image.flip_left_right(mask)

    # Image-only augmentations (doesn't affect the mask)
    img = tf.image.random_brightness(img, AUG_BRIGHTNESS)
    img = tf.image.random_contrast(img, 1 - AUG_CONTRAST, 1 + AUG_CONTRAST)
    img = tf.clip_by_value(img, 0.0, 1.0)

    return img, mask


def build_segmentation_dataset(img_dir, mask_dir, augment_data=True):
    # Grab all paths and sort them so Image 1 matches Mask 1 exactly
    img_paths = sorted([os.path.join(img_dir, f) for f in os.listdir(img_dir) if f.endswith(('.jpg', '.png'))])
    mask_paths = sorted([os.path.join(mask_dir, f) for f in os.listdir(mask_dir) if f.endswith('.png')])

    print(f"  Found {len(img_paths)} images and {len(mask_paths)} masks in {img_dir}")

    ds = tf.data.Dataset.from_tensor_slices((img_paths, mask_paths))
    ds = ds.map(load_and_preprocess, num_parallel_calls=tf.data.AUTOTUNE)

    if augment_data:
        ds = ds.map(augment, num_parallel_calls=tf.data.AUTOTUNE)
        ds = ds.shuffle(buffer_size=len(img_paths))

    ds = ds.batch(BATCH_SIZE)
    ds = ds.prefetch(tf.data.AUTOTUNE)

    return ds


# Quick test
if __name__ == "__main__":
    from config import TRAIN_IMG_DIR, TRAIN_MASK_DIR

    ds = build_segmentation_dataset(TRAIN_IMG_DIR, TRAIN_MASK_DIR, augment_data=True)
    for imgs, masks in ds.take(1):
        print("Image batch shape:", imgs.shape)
        print("Mask batch shape:", masks.shape)