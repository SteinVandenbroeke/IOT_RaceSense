import os

# ── Paths ──────────────────────────────────────────────────────────────────────
# Make sure to split your track_dataset into train and val folders!
TRAIN_IMG_DIR  = "carla_dataset_road/rgb/train"
TRAIN_MASK_DIR = "carla_dataset_road/masks/train"
VAL_IMG_DIR    = "carla_dataset_road/rgb/val"
VAL_MASK_DIR   = "carla_dataset_road/masks/val"
CHECKPOINT_DIR = "checkpoints"
EXPORT_DIR     = "export"

os.makedirs(CHECKPOINT_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR,     exist_ok=True)

# ── Model ──────────────────────────────────────────────────────────────────────
NUM_CLASSES    = 1          # 1 channel output (Binary: Track vs Background)
INPUT_SIZE     = (160, 160) # High resolution for static camera masking

# ── Training ───────────────────────────────────────────────────────────────────
BATCH_SIZE     = 8          # Lower batch size because 512x512 takes a lot of VRAM
EPOCHS_PHASE1  = 15         # Backbone frozen, only DeepLab head trains
EPOCHS_PHASE2  = 30         # Full fine-tune

LR_PHASE1      = 1e-3
LR_PHASE2      = 1e-4

# ── Augmentation ───────────────────────────────────────────────────────────────
AUG_FLIP_PROB    = 0.5
AUG_BRIGHTNESS   = 0.2
AUG_CONTRAST     = 0.2

# ── Quantization calibration ───────────────────────────────────────────────────
NUM_CALIB_SAMPLES = 100     # Masks are less complex than objects, 100 is plenty