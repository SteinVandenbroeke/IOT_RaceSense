import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
import tensorflow as tf
import glob
import matplotlib.pyplot as plt
# ==========================================
# 1. SETUP DATA PIPELINE
# ==========================================
BASE_DIR = '../manual_dataset/manual_road_dataset'
IMG_SIZE = 224
BATCH_SIZE = 8


def process_path(img_path, mask_path):
    img = tf.io.read_file(img_path)
    img = tf.image.decode_jpeg(img, channels=3)
    img = tf.image.resize(img, [IMG_SIZE, IMG_SIZE])
    img = tf.keras.applications.mobilenet_v2.preprocess_input(img)

    mask = tf.io.read_file(mask_path)
    mask = tf.image.decode_png(mask, channels=1)
    mask = tf.image.resize(mask, [IMG_SIZE, IMG_SIZE], method='nearest')
    mask = tf.cast(mask > 0, tf.float32)

    return img, mask


def augment(img, mask):
    k = tf.random.uniform(shape=[], minval=0, maxval=4, dtype=tf.int32)
    img = tf.image.rot90(img, k)
    mask = tf.image.rot90(mask, k)

    seed = tf.random.uniform([2], minval=0, maxval=9999999, dtype=tf.int32)
    img = tf.image.stateless_random_flip_left_right(img, seed)
    mask = tf.image.stateless_random_flip_left_right(mask, seed)

    seed2 = tf.random.uniform([2], minval=0, maxval=9999999, dtype=tf.int32)
    img = tf.image.stateless_random_flip_up_down(img, seed2)
    mask = tf.image.stateless_random_flip_up_down(mask, seed2)

    img = tf.image.random_brightness(img, max_delta=0.2)
    img = tf.image.random_contrast(img, lower=0.8, upper=1.2)
    img = tf.clip_by_value(img, -1.0, 1.0)

    return img, mask


def create_dataset(rgb_dir, mask_dir, is_training=False):
    rgb_files = sorted(glob.glob(os.path.join(rgb_dir, '*.*')))
    mask_files = sorted(glob.glob(os.path.join(mask_dir, '*.*')))

    if len(rgb_files) == 0:
        raise ValueError(f"Could not find any RGB images in: {rgb_dir}")
    if len(rgb_files) != len(mask_files):
        raise ValueError(f"Dataset mismatch! Found {len(rgb_files)} RGB but {len(mask_files)} Masks.")

    dataset = tf.data.Dataset.from_tensor_slices((rgb_files, mask_files))
    dataset = dataset.map(process_path, num_parallel_calls=tf.data.AUTOTUNE)

    if is_training:
        dataset = dataset.map(augment, num_parallel_calls=tf.data.AUTOTUNE)
        dataset = dataset.shuffle(buffer_size=100)

    return dataset.batch(BATCH_SIZE).prefetch(tf.data.AUTOTUNE)


train_dataset = create_dataset(os.path.join(BASE_DIR, 'rgb/train'), os.path.join(BASE_DIR, 'masks/train'), is_training=True)
val_dataset = create_dataset(os.path.join(BASE_DIR, 'rgb/val'), os.path.join(BASE_DIR, 'masks/val'), is_training=False)


# ==========================================
# 2. DEFINE ARCHITECTURE & LOSS FOR MIGRATION (FIXED FOR LOGITS)
# ==========================================
def bce_dice_loss(y_true, y_pred_logits):
    """
    FIX 1: Updated to handle raw logits natively using from_logits=True
    and internal sigmoid mapping for stable training.
    """
    bce = tf.keras.losses.binary_crossentropy(y_true, y_pred_logits, from_logits=True)
    bce_loss = tf.reduce_mean(bce)

    # Apply sigmoid strictly for structural overlap calculation
    y_pred = tf.math.sigmoid(y_pred_logits)

    y_true_f = tf.reshape(y_true, [-1])
    y_pred_f = tf.reshape(y_pred, [-1])
    intersection = tf.reduce_sum(y_true_f * y_pred_f)
    smooth = 1.0
    dice_coef = (2.0 * intersection + smooth) / (tf.reduce_sum(y_true_f) + tf.reduce_sum(y_pred_f) + smooth)
    dice_loss = 1.0 - dice_coef
    return bce_loss + dice_loss


print("Loading fine-tuned Keras 3 weights into Legacy architecture...")
# This will load the new base model architecture cleanly
model = tf.keras.models.load_model('road_simulator_model.keras', compile=False)

# ==========================================
# 3. FINE-TUNE THE MODEL
# ==========================================
model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=1e-4),
    loss=bce_dice_loss,
    metrics=[tf.keras.metrics.BinaryIoU(target_class_ids=[1], threshold=0.0, name='road_iou')]
)

callbacks = [
    tf.keras.callbacks.EarlyStopping(monitor='val_road_iou', patience=15, mode='max', restore_best_weights=True)
]
print("Fine-tuning on real data...")

# 1. Capture the history object here
history = model.fit(train_dataset, epochs=150, validation_data=val_dataset, callbacks=callbacks)

model.save('road_real_finetuned_model.keras')

# 2. Add the plotting code right after saving the model
print("Generating fine-tuning graphs...")

plt.figure(figsize=(14, 5))

# --- Plot 1: Loss ---
plt.subplot(1, 2, 1)
plt.plot(history.history['loss'], label='Training Loss', color='blue', linewidth=2)
plt.plot(history.history['val_loss'], label='Validation Loss', color='orange', linewidth=2)
plt.title('Fine-tuning: Training and Validation Loss', fontsize=14)
plt.xlabel('Epoch', fontsize=12)
plt.ylabel('Loss (BCE + Dice)', fontsize=12)
plt.legend(loc='upper right')
plt.grid(True, linestyle='--', alpha=0.7)

# --- Plot 2: Intersection over Union (IoU) ---
plt.subplot(1, 2, 2)
plt.plot(history.history['road_iou'], label='Training IoU', color='blue', linewidth=2)
plt.plot(history.history['val_road_iou'], label='Validation IoU', color='orange', linewidth=2)
plt.title('Fine-tuning: Training and Validation Road IoU', fontsize=14)
plt.xlabel('Epoch', fontsize=12)
plt.ylabel('IoU Score', fontsize=12)
plt.legend(loc='lower right')
plt.grid(True, linestyle='--', alpha=0.7)

# Adjust layout and save
plt.tight_layout()
plt.savefig('finetuning_graphs.png', dpi=300)
print("Successfully saved fine-tuning graphs to 'finetuning_graphs.png'")

# Also recurse into sub-models (the MobileNetV2 encoder)
for layer in model.layers:
    if hasattr(layer, 'layers'):
        for sublayer in layer.layers:
            if isinstance(sublayer, tf.keras.layers.BatchNormalization):
                sublayer.trainable = False


model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=1e-4),
    loss=bce_dice_loss,
    metrics=[tf.keras.metrics.BinaryIoU(target_class_ids=[1], threshold=0.0, name='road_iou')]
)

print("All BN layers frozen for export.")

# ==========================================
# 4. QUANTIZE FOR EDGE TPU (INT8)
# ==========================================
print("Quantizing model to INT8...")

def representative_data_gen():
    for input_value, _ in train_dataset.unbatch().batch(1).take(80):
        yield [tf.cast(input_value, tf.float32)]

clean_export_model = tf.keras.models.load_model('road_real_finetuned_model.keras', compile=False)

# Load directly from Keras instead of going through SavedModel export
converter = tf.lite.TFLiteConverter.from_keras_model(clean_export_model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.representative_dataset = representative_data_gen
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
converter.inference_input_type = tf.int8
converter.inference_output_type = tf.int8

tflite_quant_model = converter.convert()

with open("../../TSU/models/mobilenetv2_tpu_segmentation_road_real.tflite", "wb") as f:
    f.write(tflite_quant_model)

print("Saved quantized model.")

# Check which ops are in the model
interpreter = tf.lite.Interpreter(model_content=tflite_quant_model)
interpreter.allocate_tensors()

# List all ops — anything that's not INT8 TFLITE_BUILTIN will fail on Edge TPU
details = interpreter.get_tensor_details()
print(f"Number of tensors: {len(details)}")

# Also useful: check op types
runner = interpreter.get_signature_runner()