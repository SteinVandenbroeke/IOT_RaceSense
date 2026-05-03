from ultralytics import YOLO
import os

BASE_STATION_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = os.path.join(BASE_STATION_DIR, 'finetuned_models')

# model = YOLO('models/yolo11n-pose.pt')
model = YOLO('models/train/weights/best.pt')

results = model.train(
    data='manual_dataset/dataset.yaml',
    project=SAVE_DIR,
    name='train',
    exist_ok=True,
    plots=True,

    epochs=20,                  # Number of times it views the whole carla_dataset

    imgsz=800,                   # Matches your CARLA camera resolution
    batch=4,                    # How many images it processes at once
    workers=2,
    device=0,                    # 0 uses your first GPU. Change to 'cpu' if no GPU.
    lr0=0.1,
    lrf=0.1,

    degrees=90.0                # ROTATE IMAGES
)


print("Training Complete! The best weights are saved in 'runs/pose/train/weights/best.pt'")
print(results)