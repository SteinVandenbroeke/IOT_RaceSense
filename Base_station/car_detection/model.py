"""
model.py — MobileNetV2 SSD Backbone + Custom Heads
"""
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Conv2D, Reshape, Concatenate, Input
from config import INPUT_SIZE, NUM_CLASSES, NUM_ANCHORS, NUM_KPT_COORDS


def build_model(input_shape=(INPUT_SIZE[0], INPUT_SIZE[1], 3)):
    inputs = Input(shape=input_shape)

    # 1. Backbone: MobileNetV2 (pretrained on ImageNet)
    backbone = MobileNetV2(
        input_tensor=inputs,
        include_top=False,
        weights='imagenet'
    )

    # Extract feature maps at different scales (standard SSD approach)
    # 10x10 and 5x5 feature maps for different sized objects
    feature_map_1 = backbone.get_layer('block_13_expand_relu').output
    feature_map_2 = backbone.get_layer('out_relu').output

    feature_maps = [feature_map_1, feature_map_2]

    cls_outputs = []
    box_outputs = []
    kpt_outputs = []

    # 2. Prediction Heads
    for fm in feature_maps:
        # Classification Head (Background vs Car)
        cls_conv = Conv2D(NUM_ANCHORS * NUM_CLASSES, kernel_size=3, padding='same', activation='sigmoid')(fm)
        cls_reshaped = Reshape((-1, NUM_CLASSES))(cls_conv)
        cls_outputs.append(cls_reshaped)

        # Bounding Box Head (xc, yc, w, h)
        box_conv = Conv2D(NUM_ANCHORS * 4, kernel_size=3, padding='same')(fm)
        box_reshaped = Reshape((-1, 4))(box_conv)
        box_outputs.append(box_reshaped)

        # Keypoint Head (16 values: 8 x,y pairs)
        kpt_conv = Conv2D(NUM_ANCHORS * NUM_KPT_COORDS, kernel_size=3, padding='same')(fm)
        kpt_reshaped = Reshape((-1, NUM_KPT_COORDS))(kpt_conv)
        kpt_outputs.append(kpt_reshaped)

    # 3. Concatenate predictions from all feature maps
    predictions_cls = Concatenate(axis=1, name='cls_output')(cls_outputs)
    predictions_box = Concatenate(axis=1, name='box_output')(box_outputs)
    predictions_kpt = Concatenate(axis=1, name='kpt_output')(kpt_outputs)

    model = tf.keras.Model(
        inputs=inputs,
        outputs=[predictions_cls, predictions_box, predictions_kpt]
    )

    return model, backbone