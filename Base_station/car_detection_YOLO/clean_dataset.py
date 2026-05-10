import os
import glob


input_folder = 'carla_yolo_dataset/labels/train'
output_folder = 'carla_yolo_dataset/labels/train_cleaned'

os.makedirs(output_folder, exist_ok=True)


def clean_yolo_pose_file(filepath, save_path):
    cleaned_lines = []

    with open(filepath, 'r') as f:
        lines = f.readlines()

    for line in lines:
        parts = line.strip().split()
        if len(parts) < 5: continue  # Skip empty lines

        # BBox: class, x_center, y_center, width, height
        # Ensure BBox stays within [0, 1]
        bbox = [max(0.0, min(1.0, float(x))) for x in parts[0:5]]

        # Keypoints: groups of 3 (x, y, visibility)
        kpts = parts[5:]
        cleaned_kpts = []

        for i in range(0, len(kpts), 3):
            kx = float(kpts[i])
            ky = float(kpts[i + 1])
            kv = int(kpts[i + 2])

            # If point is outside the image, set to 0, 0 and visibility 0
            if kx < 0.0 or kx > 1.0 or ky < 0.0 or ky > 1.0:
                cleaned_kpts.extend(["0.0", "0.0", "0"])
            else:
                cleaned_kpts.extend([str(kx), str(ky), str(kv)])

        # Reconstruct the line
        new_line = " ".join([str(int(bbox[0]))] + [f"{x:.6f}" for x in bbox[1:]] + cleaned_kpts)
        cleaned_lines.append(new_line)

    with open(save_path, 'w') as f:
        f.write("\n".join(cleaned_lines))


# Run the cleaning
txt_files = glob.glob(os.path.join(input_folder, "*.txt"))
print(f"Cleaning {len(txt_files)} files...")

for f in txt_files:
    clean_yolo_pose_file(f, os.path.join(output_folder, os.path.basename(f)))

print(f"Done! Cleaned files saved to: {output_folder}")