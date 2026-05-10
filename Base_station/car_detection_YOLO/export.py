"""
export_yolo.py — Edge TPU Quantization and Export
"""
from ultralytics import YOLO

def main():
    model_path = '../../runs/pose/carla_yolo_dataset/run_1-2/weights/best.pt'
    model = YOLO(model_path)

    # We are adding int8=True explicitly, and setting half=False
    # to prevent mixed-precision bugs before calibration.
    print("Exporting and compiling for Coral Edge TPU...")
    model.export(
        format='edgetpu',
        imgsz=320,
        data='carla_yolo_dataset/carla_dataset.yaml',
        int8=True,       # Force INT8 calibration explicitly
        half=False,       # Don't use FP16 as an intermediate step
        simplify = True,
        nms=False
    )

if __name__ == '__main__':
    main()