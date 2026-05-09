"""
export_yolo.py — Edge TPU Quantization and Export
"""
from ultralytics import YOLO

def main():
    # Load your fine-tuned model from the training run
    model_path = '../../runs/pose/run_12/weights/best.pt'
    print(f"Loading trained model from {model_path}...")
    model = YOLO(model_path)

    # Export to Edge TPU format
    # By passing the 'data' argument, YOLO automatically grabs images
    # from your dataset to calibrate the INT8 quantization (replacing your representative_data_gen)
    print("Exporting and compiling for Coral Edge TPU...")
    model.export(format='edgetpu', imgsz=320, data='carla_pose.yaml')

    print("Export complete! You will find the _edgetpu.tflite file in the same folder as your weights.")

if __name__ == '__main__':
    main()