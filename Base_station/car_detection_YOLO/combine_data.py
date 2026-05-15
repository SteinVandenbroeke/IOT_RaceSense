import os
import shutil
from pathlib import Path

# --- CONFIGURATION ---
DATASET_A_PATH = Path("")  # Class 0
DATASET_B_PATH = Path("path/to/lego_cars")  # Currently Class 0, will become Class 1
OUTPUT_PATH = Path("master_dataset")


def prepare_folders():
    for split in ['train', 'val']:
        (OUTPUT_PATH / 'images' / split).mkdir(parents=True, exist_ok=True)
        (OUTPUT_PATH / 'labels' / split).mkdir(parents=True, exist_ok=True)


def merge(src_path, class_offset, split):
    img_src = src_path / 'images' / split
    lbl_src = src_path / 'labels' / split

    img_dest = OUTPUT_PATH / 'images' / split
    lbl_dest = OUTPUT_PATH / 'labels' / split

    for img_file in img_src.glob('*'):
        if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png']:
            # Copy Image
            shutil.copy(img_file, img_dest / img_file.name)

            # Process Label
            label_file = lbl_src / (img_file.stem + '.txt')
            if label_file.exists():
                with open(label_file, 'r') as f:
                    lines = f.readlines()

                with open(lbl_dest / label_file.name, 'w') as f:
                    for line in lines:
                        parts = line.split()
                        # Change the class ID by adding the offset
                        new_class = int(parts[0]) + class_offset
                        f.write(f"{new_class} {' '.join(parts[1:])}\n")


# Run the process
prepare_folders()
print("Merging Real Cars (Class 0)...")
merge(DATASET_A_PATH, 0, 'train')
merge(DATASET_A_PATH, 0, 'val')

print("Merging Lego Cars (Class 1)...")
merge(DATASET_B_PATH, 1, 'train')
merge(DATASET_B_PATH, 1, 'val')

print(f"Done! Your combined dataset is at: {OUTPUT_PATH.absolute()}")