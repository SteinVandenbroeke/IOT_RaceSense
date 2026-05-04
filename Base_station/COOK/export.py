"""
export.py — TFLite Export & Full Integer Quantization
"""
import tensorflow as tf
import os
from dataset import build_dataset
from config import CHECKPOINT_DIR, EXPORT_DIR, TRAIN_IMG_DIR, TRAIN_LBL_DIR, NUM_CALIB_SAMPLES


def representative_data_gen():
    """
    Yields samples from the training dataset for the converter
    to calculate INT8 activation ranges.
    """
    calib_ds = build_dataset(TRAIN_IMG_DIR, TRAIN_LBL_DIR, augment=False)

    sample_count = 0
    for images, _, _, _, _ in calib_ds:
        # Loop through the batch and yield exactly ONE image at a time
        for i in range(images.shape[0]):
            # Isolate the image and add the batch dimension back so it's [1, 320, 320, 3]
            single_image = tf.expand_dims(images[i], axis=0)

            yield [single_image]

            sample_count += 1
            if sample_count >= NUM_CALIB_SAMPLES:
                return  # Stop the generator completely once we hit our limit

def export_to_edgetpu():
    model_path = f"{CHECKPOINT_DIR}/final_model.keras"
    print(f"Loading trained model from {model_path}...")
    model = tf.keras.models.load_model(model_path)

    # =================================================================
    # THE FIX: Bypass Keras 3 bugs by creating a raw ConcreteFunction
    # =================================================================
    print("Extracting raw TensorFlow graph...")

    # Wrap the model in a basic tf.function
    run_model = tf.function(lambda x: model(x))

    # Define the exact input shape (Batch=1, Height=320, Width=320, Channels=3)
    # Note: If you changed INPUT_SIZE in your config.py, update the 320s here!
    concrete_func = run_model.get_concrete_function(
        tf.TensorSpec([1, 320, 320, 3], tf.float32)
    )

    print("Configuring TFLite Converter for Full Integer Quantization...")
    # Use from_concrete_functions instead of from_keras_model
    converter = tf.lite.TFLiteConverter.from_concrete_functions([concrete_func])
    # =================================================================

    # 1. Enforce INT8 operations only
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]

    # 2. Provide the calibration data
    converter.representative_dataset = representative_data_gen

    # 3. Force input and output tensors to be INT8
    converter.inference_input_type = tf.int8
    converter.inference_output_type = tf.int8

    print("Quantizing model (this may take a few minutes)...")
    tflite_quant_model = converter.convert()

    # Save the quantized model
    tflite_path = os.path.join(EXPORT_DIR, "model_quantized.tflite")
    with open(tflite_path, "wb") as f:
        f.write(tflite_quant_model)

    print(f"Successfully saved quantized model to: {tflite_path}")

if __name__ == "__main__":
    export_to_edgetpu()