import tensorflow as tf

print("Num GPUs Available: ", len(tf.config.list_physical_devices('GPU')))
if tf.config.list_physical_devices('GPU'):
    print("GPU Details:", tf.config.list_physical_devices('GPU'))
else:
    print("TensorFlow is still blind to the GPU.")