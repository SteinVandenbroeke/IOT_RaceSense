import os
from PIL import Image

# Path to your training and validation images
TRAIN_IMG_DIR = "carla_dataset/images/train"
VAL_IMG_DIR = "carla_dataset/images/val"


def find_corrupted_images(directory):
    print(f"Scanning {directory} for corrupted images...")
    bad_files = []

    for filename in os.listdir(directory):
        # Skip hidden files or non-images
        if filename.startswith('.') or not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue

        file_path = os.path.join(directory, filename)

        try:
            # Attempt to open and verify the image headers
            with Image.open(file_path) as img:
                img.verify()
        except Exception as e:
            print(f"❌ Corrupted file found: {file_path} - {e}")
            bad_files.append(file_path)

    return bad_files


if __name__ == "__main__":
    # Scan both directories
    bad_train = find_corrupted_images(TRAIN_IMG_DIR)
    bad_val = find_corrupted_images(VAL_IMG_DIR)

    total_bad = len(bad_train) + len(bad_val)

    if total_bad == 0:
        print("✅ All images are healthy!")
    else:
        print(f"\nFound {total_bad} corrupted files.")
        print(
            "IMPORTANT: You must delete these image files AND their matching .txt files in the labels folder before restarting training.")