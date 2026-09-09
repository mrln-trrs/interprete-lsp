"""
src/vision/normalization.py
Funciones de normalización de coordenadas espaciales y centrado de puntos clave
para el intérprete de Lengua de Señas Peruana (LSP).
"""

import numpy as np


def normalize_hand_landmarks(coords_21x3: np.ndarray) -> np.ndarray:
    """
    Normaliza las coordenadas 3D de una mano (21 landmarks x 3 coordenadas):
    1. Centrado (Invarianza de Traslación): Resta la coordenada de la muñeca (Landmark 0)
       a todos los puntos, colocando el origen en la muñeca.
    2. Escalamiento (Invarianza de Escala): Divide todas las coordenadas por la distancia
       máxima respecto a la muñeca (o distancia muñeca-nudillo medio), asegurando que el
       tamaño relativo de la mano sea uniforme independientemente de la cercanía a la cámara.

    Args:
        coords_21x3: Matriz numpy de forma (21, 3) con coordenadas (x, y, z).

    Returns:
        Matriz numpy de forma (21, 3) normalizada. Si la mano no tiene datos (ceros), retorna ceros.
    """
    if np.all(coords_21x3 == 0):
        return coords_21x3.copy()

    # 1. Centrado en la muñeca (punto 0)
    wrist = coords_21x3[0, :].copy()
    centered = coords_21x3 - wrist

    # 2. Factor de escala: distancia euclidiana entre muñeca y nudillo del dedo medio (punto 9)
    # Si esa distancia es muy pequeña, usar la distancia máxima al origen
    scale_ref = np.linalg.norm(centered[9, :])
    if scale_ref < 1e-4:
        scale_ref = np.max(np.linalg.norm(centered, axis=1))

    if scale_ref > 1e-4:
        normalized = centered / scale_ref
    else:
        normalized = centered

    return normalized.astype(np.float32)


def normalize_keypoints_vector(keypoints_126: np.ndarray) -> np.ndarray:
    """
    Aplica la normalización espacial al vector plano de 126 dimensiones:
    - Primeros 63 valores: Mano Izquierda (21 x 3).
    - Siguientes 63 valores: Mano Derecha (21 x 3).

    Args:
        keypoints_126: Array 1D de tamaño (126,) con coordenadas de ambas manos.

    Returns:
        Array 1D de tamaño (126,) con coordenadas normalizadas.
    """
    if len(keypoints_126) != 126:
        raise ValueError(f"Se esperaba un vector de 126 valores, pero se recibió {len(keypoints_126)}")

    left_raw = keypoints_126[:63].reshape(21, 3)
    right_raw = keypoints_126[63:].reshape(21, 3)

    left_norm = normalize_hand_landmarks(left_raw).flatten()
    right_norm = normalize_hand_landmarks(right_raw).flatten()

    return np.concatenate([left_norm, right_norm]).astype(np.float32)

