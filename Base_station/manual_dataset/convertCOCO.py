import json
import cv2
import numpy as np
import os

# Set the exact path to the folder containing your JSON and images
data_dir = os.path.join("My second project.coco", "train")
json_path = os.path.join(data_dir, "_annotations.coco.json")

# Create a folder called 'masks' right next to your script
output_dir = "manual_car_dataset/masks"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

print(f"Reading data from: {json_path}")

# Open the COCO JSON file
with open(json_path) as f:
    coco_data = json.load(f)

# Loop through every image in your dataset
for image_info in coco_data['images']:
    img_id = image_info['id']
    file_name = image_info['file_name']
    width = image_info['width']
    height = image_info['height']

    # Create a pitch-black background based on the exact image size
    mask = np.zeros((height, width), dtype=np.uint8)

    # Find all the polygons (annotations) that belong to this specific image
    for ann in coco_data['annotations']:
        if ann['image_id'] == img_id and 'segmentation' in ann:
            for seg in ann['segmentation']:
                # Convert the flat list [x1, y1, x2, y2...] into pairs [[x1, y1], [x2, y2]...]
                poly = np.array(seg, np.int32).reshape((-1, 1, 2))

                # Fill the polygon with pure white (255)
                cv2.fillPoly(mask, [poly], 255)

    # Safely swap the complex Roboflow .jpg extension for a .png extension
    base_name = file_name.rsplit('.', 1)[0]
    mask_filename = os.path.join(output_dir, base_name + '.png')

    # Save the resulting black-and-white mask
    cv2.imwrite(mask_filename, mask)
    print(f"Created mask: {base_name}.png")

print("\nDone! Check the 'masks' folder in your manual_dataset directory.")