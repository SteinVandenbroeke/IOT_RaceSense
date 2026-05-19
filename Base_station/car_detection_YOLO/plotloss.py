import pandas as pd
import matplotlib.pyplot as plt
import os

# --- Configuration ---
# Point this to the CSV file YOLO automatically generates
CSV_PATH = '../../runs/pose/carla_yolo_dataset/run_1-2/results.csv'
SAVE_PATH = 'yolo_training_graphs.png'


def plot_yolo_results():
    if not os.path.exists(CSV_PATH):
        print(f"Error: Could not find {CSV_PATH}. Make sure training has finished!")
        return

    print("Generating custom YOLO presentation graphs...")

    # Load the data and strip YOLO's weird column spacing
    df = pd.read_csv(CSV_PATH)
    df.columns = df.columns.str.strip()

    # Create a figure with two side-by-side subplots
    plt.figure(figsize=(14, 5))

    # --- Plot 1: Bounding Box Loss ---
    plt.subplot(1, 2, 1)
    plt.plot(df['epoch'], df['train/box_loss'], label='Train Box Loss', color='blue', linewidth=2)
    plt.plot(df['epoch'], df['val/box_loss'], label='Val Box Loss', color='orange', linewidth=2)
    plt.title('YOLOv8 Bounding Box Loss', fontsize=14)
    plt.xlabel('Epoch', fontsize=12)
    plt.ylabel('Loss', fontsize=12)
    plt.legend(loc='upper right')
    plt.grid(True, linestyle='--', alpha=0.7)

    # --- Plot 2: Pose (Keypoint) Loss ---
    plt.subplot(1, 2, 2)
    plt.plot(df['epoch'], df['train/pose_loss'], label='Train Pose Loss', color='blue', linewidth=2)
    plt.plot(df['epoch'], df['val/pose_loss'], label='Val Pose Loss', color='orange', linewidth=2)
    plt.title('YOLOv8 Pose (Keypoint) Loss', fontsize=14)
    plt.xlabel('Epoch', fontsize=12)
    plt.ylabel('Loss', fontsize=12)
    plt.legend(loc='upper right')
    plt.grid(True, linestyle='--', alpha=0.7)

    # Adjust layout and save
    plt.tight_layout()
    plt.savefig(SAVE_PATH, dpi=300)
    print(f"Successfully saved clean presentation graphs to '{SAVE_PATH}'")


if __name__ == '__main__':
    plot_yolo_results()