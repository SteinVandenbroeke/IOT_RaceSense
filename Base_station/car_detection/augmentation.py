import cv2
import numpy as np
import tensorflow as tf
from dataset import build_dataset
from config import TRAIN_IMG_DIR, TRAIN_LBL_DIR, INPUT_SIZE


def visualize_augmented_batch():
    print("Building dataset with augmentations...")
    # Make sure to set augment=True!
    dataset = build_dataset(TRAIN_IMG_DIR, TRAIN_LBL_DIR, augment=True)

    # Grab exactly one batch of data
    for imgs, boxes, kpts, vis, valid in dataset.take(1):
        imgs = imgs.numpy()
        boxes = boxes.numpy()
        kpts = kpts.numpy()
        valid = valid.numpy()

        # Let's show the first 4 images in this batch
        for b in range(min(4, imgs.shape[0])):
            # Convert TF image [0, 1] RGB back to OpenCV [0, 255] BGR
            img = (imgs[b] * 255.0).astype(np.uint8)
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            img_h, img_w = img.shape[:2]

            # Loop through all max_objects in this image
            for i in range(boxes.shape[1]):
                if valid[b, i] == 0:
                    continue  # Skip padded empty slots

                # 1. Decode the Fixed Bounding Box
                xmin, ymin, xmax, ymax = boxes[b, i]

                pix_xmin = int(xmin * img_w)
                pix_ymin = int(ymin * img_h)
                pix_xmax = int(xmax * img_w)
                pix_ymax = int(ymax * img_h)

                # Draw the green box
                cv2.rectangle(img, (pix_xmin, pix_ymin), (pix_xmax, pix_ymax), (0, 255, 0), 2)

                # 2. Decode the Fixed Keypoints
                true_w = xmax - xmin
                true_h = ymax - ymin

                for k in range(4):
                    # Check visibility before drawing! (Optional, but cleaner)
                    if vis[b, i, k] == 0:
                        continue

                    kx_rel = kpts[b, i, k, 0]
                    ky_rel = kpts[b, i, k, 1]

                    # Reverse the bbox-relative math back to image-normalized
                    kx_img = (kx_rel * true_w) + xmin
                    ky_img = (ky_rel * true_h) + ymin

                    # Map to actual pixels
                    pix_kx = int(kx_img * img_w)
                    pix_ky = int(ky_img * img_h)

                    # Draw the red dot
                    cv2.circle(img, (pix_kx, pix_ky), radius=4, color=(0, 0, 255), thickness=-1)

                    # --- ADDED: Draw the Keypoint Index ---
                    # We offset it by 5 pixels so it doesn't cover the dot.
                    # Color is (0, 255, 255) which is Yellow in BGR.
                    cv2.putText(img, str(k), (pix_kx + 5, pix_ky - 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)

            # Show the result
            cv2.imshow(f"Augmented Image {b + 1}", img)

        print("Images loaded! Press any key on the image windows to close them.")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        break  # We only need to check one batch


if __name__ == "__main__":
    visualize_augmented_batch()