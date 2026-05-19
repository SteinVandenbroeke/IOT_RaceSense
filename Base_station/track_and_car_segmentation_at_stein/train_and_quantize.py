import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
import tensorflow as tf
import glob
import ssl
import matplotlib.pyplot as plt
import urllib.request
import numpy as np

ssl._create_default_https_context = ssl._create_unverified_context

# ==========================================
# 1. SETUP DATA PIPELINE
# ==========================================
BASE_DIR = 'carla_road_dataset'
IMG_SIZE = 224
BATCH_SIZE = 16


def process_path(img_path, mask_path):
    # Image
    print("path", img_path)
    img = tf.io.read_file(img_path)
    img = tf.image.decode_jpeg(img, channels=3)
    img = tf.image.resize(img, [IMG_SIZE, IMG_SIZE])
    img = tf.keras.applications.mobilenet_v2.preprocess_input(img)

    # Mask
    mask = tf.io.read_file(mask_path)
    mask = tf.image.decode_png(mask, channels=1)
    mask = tf.image.resize(mask, [IMG_SIZE, IMG_SIZE], method='nearest')
    mask = tf.cast(mask > 0, tf.float32)

    return img, mask

def augment(img, mask):
    """
    Applies random augmentations on the fly.
    This function is executed fresh every single epoch for every single image.
    """
    # 1. Random Rotations (0, 90, 180, or 270 degrees)
    # tf.random.uniform generates a new number per execution in the tf.data pipeline
    k = tf.random.uniform(shape=[], minval=0, maxval=4, dtype=tf.int32)
    img = tf.image.rot90(img, k)
    mask = tf.image.rot90(mask, k)

    # 2. Random Horizontal Flip (50% chance)
    if tf.random.uniform(()) > 0.5:
        img = tf.image.flip_left_right(img)
        mask = tf.image.flip_left_right(mask)

    # 3. Random Vertical Flip (50% chance)
    if tf.random.uniform(()) > 0.5:
        img = tf.image.flip_up_down(img)
        mask = tf.image.flip_up_down(mask)

    return img, mask

def create_dataset(rgb_dir, mask_dir, is_training=False):
    # Find files
    rgb_files = sorted(glob.glob(os.path.join(rgb_dir, '*.*')))
    mask_files = sorted(glob.glob(os.path.join(mask_dir, '*.*')))

    # 🛑 SAFEGUARD: Check if files actually exist
    if len(rgb_files) == 0:
        raise ValueError(f"Could not find any RGB images in: {rgb_dir}")
    if len(mask_files) == 0:
        raise ValueError(f"Could not find any Mask images in: {mask_dir}")
    if len(rgb_files) != len(mask_files):
        raise ValueError(f"Dataset mismatch! Found {len(rgb_files)} RGB but {len(mask_files)} Masks.")

    # Create dataset
    dataset = tf.data.Dataset.from_tensor_slices((rgb_files, mask_files))
    dataset = dataset.map(process_path, num_parallel_calls=tf.data.AUTOTUNE)

    # Apply Augmentation and Shuffling ONLY if it is the training set
    if is_training:
        dataset = dataset.map(augment, num_parallel_calls=tf.data.AUTOTUNE)
        # Shuffles the data so epochs don't see the exact same order
        dataset = dataset.shuffle(buffer_size=200)

    return dataset.batch(BATCH_SIZE).prefetch(tf.data.AUTOTUNE)


# Initialize with the is_training flag
train_dataset = create_dataset(os.path.join(BASE_DIR, 'rgb/train'), os.path.join(BASE_DIR, 'masks/train'),
                               is_training=True)
val_dataset = create_dataset(os.path.join(BASE_DIR, 'rgb/val'), os.path.join(BASE_DIR, 'masks/val'), is_training=False)

# ==========================================
# 2. BUILD EDGE TPU-SAFE U-NET
# ==========================================
def tpu_upsample_block(filters, kernel_size):
    result = tf.keras.Sequential()
    # Bilinear mapping perfectly targets the Edge TPU's native RESIZE_BILINEAR op
    result.add(tf.keras.layers.UpSampling2D(size=(2, 2), interpolation='bilinear'))
    result.add(tf.keras.layers.Conv2D(
        filters, kernel_size, padding='same', use_bias=True))
    result.add(tf.keras.layers.ReLU())
    return result


def build_tpu_unet():
    inputs = tf.keras.layers.Input(shape=[IMG_SIZE, IMG_SIZE, 3])

    # Encoder (MobileNetV2)
    base_model = tf.keras.applications.MobileNetV2(
        input_shape=[IMG_SIZE, IMG_SIZE, 3], include_top=False, weights='imagenet')

    layer_names = [
        'block_1_expand_relu',  # 112x112
        'block_3_expand_relu',  # 56x56
        'block_6_expand_relu',  # 28x28
        'block_13_expand_relu',  # 14x14
        'block_16_project',  # 7x7
    ]
    base_model_outputs = [base_model.get_layer(name).output for name in layer_names]
    down_stack = tf.keras.Model(inputs=base_model.input, outputs=base_model_outputs)
    down_stack.trainable = False

    skips = down_stack(inputs)
    x = skips[-1]
    skips = reversed(skips[:-1])

    # Decoder (Edge TPU Safe)
    up_stack = [
        tpu_upsample_block(256, 3),  # 7x7 -> 14x14
        tpu_upsample_block(128, 3),  # 14x14 -> 28x28
        tpu_upsample_block(64, 3),  # 28x28 -> 56x56
        tpu_upsample_block(32, 3),  # 56x56 -> 112x112
    ]

    for up in up_stack:
        x = up(x)

        # Use bilinear upsampling here as well
    x = tf.keras.layers.UpSampling2D(size=(2, 2), interpolation='bilinear')(x)
    x = tf.keras.layers.Conv2D(16, 3, padding='same', activation='relu')(x)

    # Prediction layer (raw logits for stable loss, as fixed previously)
    last = tf.keras.layers.Conv2D(
        1, 1,
        padding='same',
        activation=None
    )
    x = last(x)

    return tf.keras.Model(inputs=inputs, outputs=x)


model = build_tpu_unet()

# ==========================================
# 3. TRAIN THE MODEL
# ==========================================
def bce_dice_loss(y_true, y_pred_logits):
    """
    Updated to accept RAW LOGITS from the model.
    Applies sigmoid activation internally for stable mathematical calculations.
    """
    # 1. Compute standard Binary Cross Entropy safely from logits
    bce = tf.keras.losses.binary_crossentropy(y_true, y_pred_logits, from_logits=True)
    bce_loss = tf.reduce_mean(bce)

    # 2. Apply Sigmoid internally JUST for the Dice Loss calculation
    y_pred = tf.math.sigmoid(y_pred_logits)

    # Flatten tensors to compute overlap
    y_true_f = tf.reshape(y_true, [-1])
    y_pred_f = tf.reshape(y_pred, [-1])

    intersection = tf.reduce_sum(y_true_f * y_pred_f)
    smooth = 1.0  # Prevents division by zero errors

    dice_coef = (2.0 * intersection + smooth) / (tf.reduce_sum(y_true_f) + tf.reduce_sum(y_pred_f) + smooth)
    dice_loss = 1.0 - dice_coef

    # Combine both losses
    return bce_loss + dice_loss

# Compile using our new loss function
model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
    loss=bce_dice_loss,
    metrics=[tf.keras.metrics.BinaryIoU(target_class_ids=[1], threshold=0.0, name='road_iou')]
)

callbacks = [
    tf.keras.callbacks.ModelCheckpoint(
        filepath='road_simulator_model.keras',
        monitor='val_road_iou',
        mode='max',
        save_best_only=True,
        verbose=1
    )
]

print("Training model...")
history = model.fit(train_dataset, epochs=120, validation_data=val_dataset, callbacks=callbacks)

model.save('road_simulator_model_final.keras')
print("Saved unquantized Keras models: 'simulator_model.keras' (Best) and 'simulator_model_final.keras' (Last Epoch)")


print("Generating training graphs...")

# Create a figure with two subplots (1 row, 2 columns)
plt.figure(figsize=(14, 5))

# --- Plot 1: Loss ---
plt.subplot(1, 2, 1)
plt.plot(history.history['loss'], label='Training Loss', color='blue', linewidth=2)
plt.plot(history.history['val_loss'], label='Validation Loss', color='orange', linewidth=2)
plt.title('Training and Validation Loss', fontsize=14)
plt.xlabel('Epoch', fontsize=12)
plt.ylabel('Loss (BCE + Dice)', fontsize=12)
plt.legend(loc='upper right')
plt.grid(True, linestyle='--', alpha=0.7)

# --- Plot 2: Intersection over Union (IoU) ---
plt.subplot(1, 2, 2)
# Note: The metric name matches the one defined in model.compile
plt.plot(history.history['road_iou'], label='Training IoU', color='blue', linewidth=2)
plt.plot(history.history['val_road_iou'], label='Validation IoU', color='orange', linewidth=2)
plt.title('Training and Validation Road IoU', fontsize=14)
plt.xlabel('Epoch', fontsize=12)
plt.ylabel('IoU Score', fontsize=12)
plt.legend(loc='lower right')
plt.grid(True, linestyle='--', alpha=0.7)

# Adjust layout and save as a high-resolution image
plt.tight_layout()
plt.savefig('training_graphs.png', dpi=300)
print("Successfully saved training graphs to 'training_graphs.png'")