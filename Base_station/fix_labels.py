import os
import glob

LABELS_DIR = '/Base_station/carla_dataset/labels/train/'

def fix_negative_labels(directory):
    # Find all .txt files in the specified directory
    txt_files = glob.glob(os.path.join(directory, '*.txt'))

    if not txt_files:
        print(f"No .txt files found in {directory}")
        return

    print(f"Scanning {len(txt_files)} files for negative values...")
    fixed_count = 0

    for file_path in txt_files:
        with open(file_path, 'r') as file:
            lines = file.readlines()

        new_lines = []
        file_modified = False

        for line in lines:
            # Split the line by spaces into individual strings
            parts = line.strip().split()
            new_parts = []

            for part in parts:
                try:
                    # Convert string to float to check if it's negative
                    val = float(part)
                    if val < 0:
                        # Replace negative value with formatted zero
                        new_parts.append("0.000000")
                        file_modified = True
                    else:
                        # Keep the original value as a string
                        new_parts.append(part)
                except ValueError:
                    # If it's not a number (shouldn't happen in YOLO labels), just append it
                    new_parts.append(part)

            # Reconstruct the line with spaces
            new_lines.append(" ".join(new_parts) + "\n")

        # Only overwrite the file if we actually changed something
        if file_modified:
            with open(file_path, 'w') as file:
                file.writelines(new_lines)
            fixed_count += 1
            print(f"Fixed: {os.path.basename(file_path)}")

    print(f"\nDone! Fixed negative values in {fixed_count} file(s).")


if __name__ == '__main__':
    fix_negative_labels(LABELS_DIR)