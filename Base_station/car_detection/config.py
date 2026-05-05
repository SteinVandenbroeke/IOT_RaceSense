import os

# ── Paths ──────────────────────────────────────────────────────────────────────
TRAIN_IMG_DIR  = "carla_dataset/images/train"
TRAIN_LBL_DIR  = "carla_dataset/labels/train"
VAL_IMG_DIR    = "carla_dataset/images/val"
VAL_LBL_DIR    = "carla_dataset/labels/val"
CHECKPOINT_DIR = "checkpoints"
EXPORT_DIR     = "export"

os.makedirs(CHECKPOINT_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR,     exist_ok=True)

# ── Model ──────────────────────────────────────────────────────────────────────
NUM_CLASSES    = 1          # number of object classes (excluding background)
NUM_KEYPOINTS  = 4          # keypoints per object
NUM_KPT_COORDS = NUM_KEYPOINTS * 2   # 16 output values (x,y pairs, bbox-relative)

INPUT_SIZE     = (320, 320) # (H, W) — must be multiple of 32, 320 is optimal for Edge TPU
NUM_ANCHORS    = 6          # anchors per feature map cell (SSD default)

# ── Training ───────────────────────────────────────────────────────────────────
BATCH_SIZE     = 16
EPOCHS_PHASE1  = 20         # backbone frozen, only heads train
EPOCHS_PHASE2  = 20         # full fine-tune

LR_PHASE1      = 1e-3
LR_PHASE2      = 1e-4

# Loss weighting
LAMBDA_KPT     = 2.0        # weight on keypoint regression loss
                            # higher = prioritise kpt accuracy over box accuracy
                            # tune if one loss dominates the other

# ── Augmentation ───────────────────────────────────────────────────────────────
AUG_FLIP_PROB    = 0.5
AUG_BRIGHTNESS   = 0.2
AUG_CONTRAST     = 0.2
AUG_SCALE_RANGE  = (0.8, 1.2)

# ── Quantization calibration ───────────────────────────────────────────────────
NUM_CALIB_SAMPLES = 200     # images used for post-training quantization calibration
