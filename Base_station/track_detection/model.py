import tensorflow as tf
from tensorflow.keras.layers import Input, Conv2D, UpSampling2D, Concatenate, GlobalAveragePooling2D, Reshape, \
    BatchNormalization, Activation
from config import INPUT_SIZE, NUM_CLASSES


def ASPP_block(inputs):
    """Atrous Spatial Pyramid Pooling - The brain of DeepLab"""
    # 1x1 Convolution
    b0 = Conv2D(256, (1, 1), padding="same", use_bias=False)(inputs)
    b0 = BatchNormalization()(b0)
    b0 = Activation("relu")(b0)

    # Dilated Convolutions (The "Zoom Lenses")
    b1 = Conv2D(256, (3, 3), dilation_rate=(6, 6), padding="same", use_bias=False)(inputs)
    b1 = BatchNormalization()(b1)
    b1 = Activation("relu")(b1)

    b2 = Conv2D(256, (3, 3), dilation_rate=(12, 12), padding="same", use_bias=False)(inputs)
    b2 = BatchNormalization()(b2)
    b2 = Activation("relu")(b2)

    # Global Average Pooling
    b3 = GlobalAveragePooling2D()(inputs)
    b3 = Reshape((1, 1, inputs.shape[-1]))(b3)
    b3 = Conv2D(256, (1, 1), padding="same", use_bias=False)(b3)
    b3 = BatchNormalization()(b3)
    b3 = Activation("relu")(b3)
    b3 = UpSampling2D(size=(inputs.shape[1], inputs.shape[2]), interpolation="bilinear")(b3)

    # Combine
    x = Concatenate()([b0, b1, b2, b3])
    x = Conv2D(256, (1, 1), padding="same", use_bias=False)(x)
    x = BatchNormalization()(x)
    return Activation("relu")(x)


def build_deeplab():
    input_shape = (INPUT_SIZE[0], INPUT_SIZE[1], 3)
    inputs = Input(shape=input_shape)

    # 1. The Encoder (MobileNetV2)
    backbone = tf.keras.applications.MobileNetV2(
        weights='imagenet',
        include_top=False,
        input_tensor=inputs
    )

    image_features = backbone.get_layer('block_13_expand_relu').output

    # 2. The DeepLab ASPP Brain
    x = ASPP_block(image_features)

    # 3. The Decoder
    # Predict our mask channels (e.g., 1 channel with Sigmoid for binary)
    x = Conv2D(NUM_CLASSES, (1, 1), padding="same", activation="sigmoid")(x)

    # Resize back to original INPUT_SIZE
    outputs = UpSampling2D(
        size=(input_shape[0] // x.shape[1], input_shape[1] // x.shape[2]),
        interpolation="bilinear",
        name="segmentation_output"
    )(x)

    model = tf.keras.Model(inputs=inputs, outputs=outputs)
    return model, backbone