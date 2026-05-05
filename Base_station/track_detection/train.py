import tensorflow as tf
from dataset import build_segmentation_dataset
from model import build_deeplab
from config import *


def train():
    print("Loading datasets...")
    train_ds = build_segmentation_dataset(TRAIN_IMG_DIR, TRAIN_MASK_DIR, augment_data=True)
    val_ds = build_segmentation_dataset(VAL_IMG_DIR, VAL_MASK_DIR, augment_data=False)

    print("Building DeepLabV3 Model...")
    model, backbone = build_deeplab()

    # We use Binary Crossentropy because each pixel is either 0 (Background) or 1 (Track)
    loss_fn = tf.keras.losses.BinaryFocalCrossentropy(
        alpha=0.95,
        gamma=2.0,
        from_logits=False
    )

    eval_metrics = [tf.keras.metrics.BinaryIoU(target_class_ids=[1], name='track_iou')]

    # --- PHASE 1: Train DeepLab Head Only ---
    print("\n" + "=" * 40)
    print("PHASE 1: Freezing MobileNetV2 Backbone")
    print("=" * 40)
    backbone.trainable = False

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=LR_PHASE1),
        loss=loss_fn,
        metrics=eval_metrics,
        jit_compile = False
    )

    model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS_PHASE1
    )

    # --- PHASE 2: Fine-Tune Entire Model ---
    print("\n" + "=" * 40)
    print("PHASE 2: Unfreezing Backbone for Fine-Tuning")
    print("=" * 40)
    backbone.trainable = True

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=LR_PHASE2),
        loss=loss_fn,
        metrics=eval_metrics,
        jit_compile=False
    )

    model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS_PHASE2
    )

    # Save the model using the native Keras format
    save_path = f"{CHECKPOINT_DIR}/final_model.keras"
    model.save(save_path)
    print(f"\n✅ Training complete! Model saved to {save_path}")


if __name__ == "__main__":
    train()