import os
import json
import glob
import random
import shutil

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
JSON_DIR = 'output_keypoints/keypoints'
IMAGE_DIR = 'output_keypoints/rgb'
DATASET_DIR = 'Dataset'

IMAGE_WIDTH = 800.0
IMAGE_HEIGHT = 600.0
CLASS_ID = 0  # 0 represents 'car' in our dataset
SPLIT_RATIO = 0.8  # 80% for training, 20% for validation


def create_yolo_dataset():
    dirs_to_make = [
        os.path.join(DATASET_DIR, 'images', 'train'),
        os.path.join(DATASET_DIR, 'images', 'val'),
        os.path.join(DATASET_DIR, 'labels', 'train'),
        os.path.join(DATASET_DIR, 'labels', 'val')
    ]
    for d in dirs_to_make:
        os.makedirs(d, exist_ok=True)

    # 2. Gather all valid image and json pairs
    json_files = glob.glob(os.path.join(JSON_DIR, '*.json'))
    valid_pairs = []

    for json_path in json_files:
        base_name = os.path.splitext(os.path.basename(json_path))[0]
        img_path = os.path.join(IMAGE_DIR, f"{base_name}.png")

        # Ensure the corresponding image actually exists
        if os.path.exists(img_path):
            valid_pairs.append((json_path, img_path, base_name))
        else:
            print(f"Warning: No matching image found for {base_name}.json")

    # 3. Shuffle and split 80/20
    random.shuffle(valid_pairs)
    split_idx = int(len(valid_pairs) * SPLIT_RATIO)

    train_pairs = valid_pairs[:split_idx]
    val_pairs = valid_pairs[split_idx:]

    print(f"Found {len(valid_pairs)} valid image-label pairs.")
    print(f"Splitting: {len(train_pairs)} Training | {len(val_pairs)} Validation\n")

    # 4. Helper function to process and route the files
    def process_split(pairs, split_name):
        converted_count = 0
        for json_path, img_path, base_name in pairs:
            with open(json_path, 'r') as f:
                keypoints = json.load(f)

            # Skip if the projection missed points
            if len(keypoints) != 8:
                print(f"Skipping {base_name} - Expected 8 points, got {len(keypoints)}")
                continue

            # --- Bounding Box Math ---
            xs = [pt[0] for pt in keypoints]
            ys = [pt[1] for pt in keypoints]

            xmin, xmax = min(xs), max(xs)
            ymin, ymax = min(ys), max(ys)

            bbox_w = xmax - xmin
            bbox_h = ymax - ymin
            center_x = xmin + (bbox_w / 2.0)
            center_y = ymin + (bbox_h / 2.0)

            norm_cx = center_x / IMAGE_WIDTH
            norm_cy = center_y / IMAGE_HEIGHT
            norm_w = bbox_w / IMAGE_WIDTH
            norm_h = bbox_h / IMAGE_HEIGHT

            # Initialize the YOLO string
            yolo_str = f"{CLASS_ID} {norm_cx:.6f} {norm_cy:.6f} {norm_w:.6f} {norm_h:.6f}"

            # --- Keypoints Math ---
            for pt in keypoints:
                norm_px = pt[0] / IMAGE_WIDTH
                norm_py = pt[1] / IMAGE_HEIGHT

                # Check if point is inside the camera view bounds
                if 0 <= pt[0] <= IMAGE_WIDTH and 0 <= pt[1] <= IMAGE_HEIGHT:
                    visibility = 2  # Visible
                else:
                    visibility = 1  # Occluded / Out of bounds

                yolo_str += f" {norm_px:.6f} {norm_py:.6f} {visibility}"

            # --- Save Files to Dataset Folders ---
            # 1. Write the .txt label
            txt_dest = os.path.join(DATASET_DIR, 'labels', split_name, f"{base_name}.txt")
            with open(txt_dest, 'w') as f:
                f.write(yolo_str + '\n')

            # 2. Copy the .png image
            img_dest = os.path.join(DATASET_DIR, 'images', split_name, f"{base_name}.png")
            shutil.copy(img_path, img_dest)

            converted_count += 1

        return converted_count

    # Execute the split processing
    train_count = process_split(train_pairs, 'train')
    val_count = process_split(val_pairs, 'val')

    # 5. Automatically generate the dataset.yaml file
    yaml_content = f"""path: {os.path.abspath(DATASET_DIR)}
train: images/train
val: images/val

# Classes
names:
  0: car

# Keypoints setup
kpt_shape: [8, 3] # [number of keypoints, number of dimensions (x, y, visibility)]
"""
    yaml_path = os.path.join(DATASET_DIR, 'dataset.yaml')
    with open(yaml_path, 'w') as f:
        f.write(yaml_content)

    print(f"Success! Built dataset with {train_count} train samples and {val_count} val samples.")
    print(f"Your configuration file is ready at: {yaml_path}")
    print("\nYou can now start training using:")
    print("model.train(data='dataset/dataset.yaml', epochs=100, imgsz=800)")


def fix_yolo_labels(dataset_dir='dataset/'):
    # Find all .txt files in both train and val label folders
    label_files = glob.glob(os.path.join(dataset_dir, 'labels', '**', '*.txt'), recursive=True)
    fixed_count = 0

    for file_path in label_files:
        with open(file_path, 'r') as f:
            lines = f.readlines()

        new_lines = []
        file_was_fixed = False

        for line in lines:
            parts = line.strip().split()
            if len(parts) < 5:
                continue

            class_id = parts[0]
            cx, cy, w, h = map(float, parts[1:5])

            # 1. Fix Bounding Box (Clip to 0.0 - 1.0)
            xmin = max(0.0, cx - w / 2.0)
            ymin = max(0.0, cy - h / 2.0)
            xmax = min(1.0, cx + w / 2.0)
            ymax = min(1.0, cy + h / 2.0)

            new_w = xmax - xmin
            new_h = ymax - ymin
            new_cx = xmin + new_w / 2.0
            new_cy = ymin + new_h / 2.0

            if cx != new_cx or cy != new_cy or w != new_w or h != new_h:
                file_was_fixed = True

            new_line = f"{class_id} {new_cx:.6f} {new_cy:.6f} {new_w:.6f} {new_h:.6f}"

            # 2. Fix Keypoints (Zero-out if out of bounds)
            keypoints = parts[5:]
            for i in range(0, len(keypoints), 3):
                kx = float(keypoints[i])
                ky = float(keypoints[i + 1])
                kv = int(keypoints[i + 2])

                # If keypoint is outside the 0.0 - 1.0 range
                if kx < 0.0 or kx > 1.0 or ky < 0.0 or ky > 1.0:
                    kx, ky, kv = 0.0, 0.0, 0  # 0 visibility means YOLO ignores it
                    file_was_fixed = True

                new_line += f" {kx:.6f} {ky:.6f} {kv}"

            new_lines.append(new_line + '\n')

        # Overwrite the file if we made corrections
        if file_was_fixed:
            with open(file_path, 'w') as f:
                f.writelines(new_lines)
            fixed_count += 1

    print(f"Dataset cleaned! Fixed {fixed_count} files containing out-of-bounds coordinates.")


if __name__ == '__main__':
    # create_yolo_dataset()
    fix_yolo_labels()