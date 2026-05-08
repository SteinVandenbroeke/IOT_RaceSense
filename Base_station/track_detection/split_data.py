import os
import random
import shutil

# Configuration
BASE_DIR = "carla_dataset_road"
IMG_DIR = os.path.join(BASE_DIR, "rgb")
MASK_DIR = os.path.join(BASE_DIR, "masks")
SPLIT_RATIO = 0.8  # 80% for training, 20% for validation


def setup_directories():
    """Creates the target train/val directories."""
    dirs = [
        os.path.join(IMG_DIR, "train"),
        os.path.join(IMG_DIR, "val"),
        os.path.join(MASK_DIR, "train"),
        os.path.join(MASK_DIR, "val")
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    return dirs


def split_dataset():
    # 1. Get all images (ignoring any directories like 'train' or 'val' if they exist)
    all_images = [f for f in os.listdir(IMG_DIR) if os.path.isfile(os.path.join(IMG_DIR, f))]

    # 2. Shuffle them randomly
    random.shuffle(all_images)

    # 3. Calculate the split index
    split_index = int(len(all_images) * SPLIT_RATIO)
    train_images = all_images[:split_index]
    val_images = all_images[split_index:]

    print(f"Total images found: {len(all_images)}")
    print(f"Moving {len(train_images)} to train...")
    print(f"Moving {len(val_images)} to val...")

    # 4. Helper function to move files safely
    def move_pairs(file_list, target_split):
        for img_name in file_list:
            # We assume masks have the same name but a .png extension
            base_name = os.path.splitext(img_name)[0]
            mask_name = base_name + ".png"

            src_img = os.path.join(IMG_DIR, img_name)
            src_mask = os.path.join(MASK_DIR, mask_name)

            dst_img = os.path.join(IMG_DIR, target_split, img_name)
            dst_mask = os.path.join(MASK_DIR, target_split, mask_name)

            # Check if mask exists to prevent crashes
            if os.path.exists(src_mask):
                shutil.move(src_img, dst_img)
                shutil.move(src_mask, dst_mask)
            else:
                print(f"⚠️ Warning: Mask not found for {img_name}. Skipping.")

    # 5. Execute the move
    move_pairs(train_images, "train")
    move_pairs(val_images, "val")

    print("\n✅ Dataset successfully split and organized!")


if __name__ == "__main__":
    setup_directories()
    split_dataset()