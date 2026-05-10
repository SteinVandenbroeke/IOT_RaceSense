import os
import tensorflow as tf
from dataset import build_segmentation_dataset
from config import *
import subprocess # Add this import

def representative_data_gen():
    """Yields single images for INT8 calibration."""
    # Load without augmentation
    calib_ds = build_segmentation_dataset(TRAIN_IMG_DIR, TRAIN_MASK_DIR, augment_data=False)

    sample_count = 0
    for images, _ in calib_ds:
        # TFLite needs exactly 1 image per batch for the Dev Board
        for i in range(images.shape[0]):
            single_image = tf.expand_dims(images[i], axis=0)  # Shape: [1, H, W, 3]
            yield [single_image]

            sample_count += 1
            if sample_count >= NUM_CALIB_SAMPLES:
                return


def export_to_edgetpu():
    model_path = f"{CHECKPOINT_DIR}/final_model.keras"
    print(f"Loading trained model from {model_path}...")
    model = tf.keras.models.load_model(model_path)

    print("Extracting raw TensorFlow graph to bypass Keras 3 exporter...")
    run_model = tf.function(lambda x: model(x))

    # Force the input shape to match your config (e.g., [1, 512, 512, 3])
    concrete_func = run_model.get_concrete_function(
        tf.TensorSpec([1, INPUT_SIZE[0], INPUT_SIZE[1], 3], tf.float32)
    )

    print("Configuring TFLite Converter for Full Integer Quantization...")
    converter = tf.lite.TFLiteConverter.from_concrete_functions([concrete_func])

    # 1. Enforce INT8 operations
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]

    # 2. Provide the calibration data
    converter.representative_dataset = representative_data_gen

    # 3. Force inputs and outputs to be INT8
    converter.inference_input_type = tf.int8
    converter.inference_output_type = tf.int8

    print(f"Quantizing model using {NUM_CALIB_SAMPLES} samples (this may take a minute)...")
    tflite_quant_model = converter.convert()

    # Save the standard TFLite model first
    tflite_path = os.path.join(EXPORT_DIR, "track_mask_quantized.tflite")
    with open(tflite_path, "wb") as f:
        f.write(tflite_quant_model)

    print(f"\n✅ Successfully saved quantized model to: {tflite_path}")
    print("=" * 60)

    # --- NEW AUTOMATION CODE ---
    print("Executing Edge TPU Compiler...")

    try:
        # Run the compiler and output it to the same EXPORT_DIR
        result = subprocess.run(
            ['edgetpu_compiler', tflite_path, '-o', EXPORT_DIR],
            capture_output=True,
            text=True,
            check=True  # Raises an exception if the command fails
        )
        print("✅ Edge TPU compilation successful!")
        print(result.stdout)  # Print the compiler's success message

    except subprocess.CalledProcessError as e:
        print("\n❌ Edge TPU compilation failed!")
        print("Error Output:")
        print(e.stdout)
        print(e.stderr)

    except FileNotFoundError:
        print("\n❌ Error: 'edgetpu_compiler' is not installed or not in your system PATH.")
        print("Please install it following the official Coral documentation.")


if __name__ == "__main__":
    export_to_edgetpu()