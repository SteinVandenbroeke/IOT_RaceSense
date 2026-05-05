import os
import glob


def convert_yolo_to_ssd_line(yolo_line):
    """Converts a single YOLO pose line to SSD format."""
    parts = yolo_line.strip().split()

    if len(parts) < 29:
        # 1 class + 4 bbox + 24 keypoints (8 points * 3) = 29
        return yolo_line

    class_id = parts[0]
    cx = float(parts[1])
    cy = float(parts[2])
    w = float(parts[3])
    h = float(parts[4])

    # Convert center coordinates to corner coordinates
    xmin = cx - (w / 2)
    xmax = cx + (w / 2)
    ymin = cy - (h / 2)
    ymax = cy + (h / 2)

    # Extract the 8 keypoints (remaining 24 values)
    keypoints = parts[5:]

    # Format the bounding box to 6 decimal places to match your original data
    bbox_str = f"{xmin:.6f} {ymin:.6f} {xmax:.6f} {ymax:.6f}"
    keypoints_str = " ".join(keypoints)

    return f"{class_id} {bbox_str} {keypoints_str}\n"


def convert_dataset(input_dir, output_dir):
    """Processes all .txt files in a directory."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    txt_files = glob.glob(os.path.join(input_dir, "*.txt"))

    for file_path in txt_files:
        filename = os.path.basename(file_path)
        output_path = os.path.join(output_dir, filename)

        with open(file_path, 'r') as infile, open(output_path, 'w') as outfile:
            for line in infile:
                converted_line = convert_yolo_to_ssd_line(line)
                outfile.write(converted_line)

    print(f"Successfully converted {len(txt_files)} files. Saved to {output_dir}")


if __name__ == "__main__":
    convert_dataset("car_detection/manual_dataset/labels/train", "manual/1_labels/train")