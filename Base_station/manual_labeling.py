import xml.etree.ElementTree as ET
import os

# 1. Setup paths for your new folder structure
BASE_DIR = 'car_detection/manual_dataset'
xml_file = os.path.join(BASE_DIR, 'annotations.xml')  # Make sure your XML is named this!
output_dir = os.path.join(BASE_DIR, 'labels')

# Create the labels folder if it doesn't already exist
os.makedirs(output_dir, exist_ok=True)

# 2. Parse the XML
try:
    tree = ET.parse(xml_file)
    root = tree.getroot()
except FileNotFoundError:
    print(
        f"Error: Could not find {xml_file}. Make sure the file is named correctly and inside the '{BASE_DIR}' folder.")
    exit()

CLASS_ID = 0  # 0 is standard for 'Car'

print(f"Processing {len(root.findall('image'))} images from CVAT XML...")

# 3. Loop through each image tag in the XML
for image in root.findall('image'):
    image_name = image.get('name')
    img_w = float(image.get('width'))
    img_h = float(image.get('height'))

    points_tag = image.find('points')
    if points_tag is None:
        continue  # Skip if you accidentally left an image blank

    points_str = points_tag.get('points')

    # CVAT formats points as "x1,y1;x2,y2;..."
    raw_points = [p.split(',') for p in points_str.split(';')]

    x_coords = [float(p[0]) for p in raw_points]
    y_coords = [float(p[1]) for p in raw_points]

    # 4. Calculate 2D Bounding Box (Min/Max limits of your clicks)
    x_min, x_max = min(x_coords), max(x_coords)
    y_min, y_max = min(y_coords), max(y_coords)

    # 5. Normalize Bounding Box (Convert to 0.0 - 1.0 scale)
    center_x = ((x_min + x_max) / 2) / img_w
    center_y = ((y_min + y_max) / 2) / img_h
    box_width = (x_max - x_min) / img_w
    box_height = (y_max - y_min) / img_h

    # 6. Build the YOLO string starting with BBox info
    yolo_line = f"{CLASS_ID} {center_x:.6f} {center_y:.6f} {box_width:.6f} {box_height:.6f}"

    # 7. Add normalized keypoints with visibility = 2
    for x, y in zip(x_coords, y_coords):
        norm_x = x / img_w
        norm_y = y / img_h
        yolo_line += f" {norm_x:.6f} {norm_y:.6f} 2"

    # 8. Save to individual .txt file inside the labels folder
    txt_filename = os.path.splitext(image_name)[0] + '.txt'
    with open(os.path.join(output_dir, txt_filename), 'w') as f:
        f.write(yolo_line + '\n')

print(f"Done! Saved perfectly formatted YOLO labels to the '{output_dir}' folder.")