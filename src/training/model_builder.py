"""
src/training/model_builder.py
Definición de la arquitectura de la red neuronal recurrente (LSTM / GRU).
"""
from config.actions import NUM_CLASSES


def validate_configuration(input_shape=(30, 126), num_classes=NUM_CLASSES, recurrent="lstm", dropout=0.3, classes=None):
    """classes=None exige las nueve glosas base; con un vocabulario propio, num_classes debe coincidir con él."""
    if tuple(input_shape) != (30, 126):
        raise ValueError("El esquema provisional requiere input_shape=(30,126)")
    expected = len(classes) if classes is not None else NUM_CLASSES
    if type(num_classes) is not int or num_classes != expected or num_classes < 2:
        raise ValueError("El número de clases no coincide con el vocabulario del encoder")
    if recurrent not in ("lstm", "gru"):
        raise ValueError("Solo se admite LSTM o GRU")
    if type(dropout) not in (int, float) or not 0 <= dropout < 1:
        raise ValueError("Dropout fuera de rango")


def build_lstm_model(input_shape=(30, 126), num_classes=NUM_CLASSES, recurrent="lstm", dropout=0.3, classes=None,
                     units=64, dense_units=32, l2=1e-4, learning_rate=1e-3):
    validate_configuration(input_shape, num_classes, recurrent, dropout, classes)
    try:
        import tensorflow as tf
        layers = tf.keras.layers
    except ImportError as error:
        raise RuntimeError("Keras no está disponible; resolver ENV-03 antes de entrenar") from error
    recurrent_layer = layers.LSTM if recurrent == "lstm" else layers.GRU
    model = tf.keras.Sequential([
        layers.Input(shape=input_shape),
        recurrent_layer(units, kernel_regularizer=tf.keras.regularizers.l2(l2)),
        layers.Dropout(dropout),
        layers.Dense(dense_units, activation="relu"),
        layers.Dense(num_classes, activation="softmax"),
    ], name=f"lsp_{recurrent}_baseline")
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
                  loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    return model
