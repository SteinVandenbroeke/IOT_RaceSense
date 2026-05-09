"""
train_yolo.py — YOLOv8 Pose Fine-Tuning
"""
from ultralytics import YOLO


def main():
    # Load the pre-trained YOLOv8 Nano Pose model (it will download automatically)
    print("Loading pre-trained YOLOv8n-pose model...")
    model = YOLO('yolov8n-pose.pt')

    # Train the model
    # This combines your old Phase 1 and Phase 2 into one highly optimized loop
    print("Starting training...")
    results = model.train(
        data='carla_pose.yaml',  # Points to your dataset config
        epochs=20,  # Combined epochs from your old config
        imgsz=320,  # 320x320 optimal for Edge TPU
        batch=16,  # Batch size
        pose=2.0,  # Equivalent to your LAMBDA_KPT=2.0
        project='carla_models',  # Folder where weights will be saved
        name='run_1',  # Subfolder for this specific training run
        device='0'  # Use '0' for GPU, or 'cpu' if running on a laptop without CUDA
    )

    print("Training complete! Best weights saved to: carla_models/run_1/weights/best.pt")


if __name__ == '__main__':
    main()