"""
src/inference/media_bank.py
Motor de reconocimiento basado en banco de prototipos posturales y temporales
extraídos de medios reales (C:\\proyectos\\media) y reglas de abreviación conversacional.

Soporta incremento modular:
  - Paso 1: Números (1 al 20)
  - Paso 2: Abecedario (A a Z + Ñ)
  - Paso 3: Meses del año (ENERO a DICIEMBRE, variante completa en video y abreviada con rotación)
"""
from collections import deque
import json
from pathlib import Path
import numpy as np

from config.actions import EXTENDED_INVERSE_LABEL_MAP
from src.vision.normalization import finite_array, normalize_hand_landmarks


def canonical_hand_pose(coords_21x3: np.ndarray) -> np.ndarray:
    """
    Normaliza una mano (21, 3) garantizando invarianza a traslación, escala y mano dominante (izq/der).
    Para comparar posturas unimanuales sin importar si el usuario usa mano izquierda o derecha,
    orienta el eje X según el vector muñeca(0) -> base índice(5) vs base meñique(17).
    """
    hand = finite_array(coords_21x3, (21, 3)).copy()
    if np.all(hand == 0):
        return np.zeros(78, dtype=np.float32)

    norm = normalize_hand_landmarks(hand).astype(np.float64)
    # Orientación canónica palmar: producto cruz 2D entre (mcp_indice - muñeca) y (mcp_meñique - muñeca)
    v_idx = norm[5, :2]
    v_pnk = norm[17, :2]
    cross_z = v_idx[0] * v_pnk[1] - v_idx[1] * v_pnk[0]
    if cross_z < 0:
        norm[:, 0] = -norm[:, 0]

    # 1. ratios de extensión de los 5 dedos: ||tip - wrist|| / (||pip - wrist|| + 1e-4)
    tips = [4, 8, 12, 16, 20]
    pips = [3, 6, 10, 14, 18]
    ext_ratios = [
        float(np.linalg.norm(norm[t]) / (np.linalg.norm(norm[p]) + 1e-4))
        for t, p in zip(tips, pips)
    ]

    # 2. distancias desde la punta del pulgar (4) a las otras 4 puntas (8, 12, 16, 20) y nudillos
    thumb_tip = norm[4]
    thumb_dists = [
        float(np.linalg.norm(thumb_tip - norm[idx]))
        for idx in (8, 12, 16, 20, 6, 10, 14, 18)
    ]

    # 3. diferencias verticales (dy) de cada punta respecto a su MCP (útil para mano invertida como M, N, P, Q)
    mcps = [2, 5, 9, 13, 17]
    tip_dy = [float(norm[t, 1] - norm[m, 1]) for t, m in zip(tips, mcps)]

    features = np.concatenate([
        norm.flatten(),                       # 63D
        np.asarray(ext_ratios) * 0.6,         # 5D
        np.asarray(thumb_dists) * 0.8,        # 8D
        np.asarray(tip_dy) * 0.6,             # 5D -> Total = 81D
    ])
    norm_factor = np.linalg.norm(features)
    if norm_factor > 1e-6:
        features = features / norm_factor
    return features.astype(np.float32)


def extract_active_hands(raw_vector_126):
    """Extrae la mano primaria (mayor energía/presencia) y secundaria de un vector 126D."""
    pts = finite_array(raw_vector_126, (126,)).reshape(2, 21, 3)
    active = []
    for slot in (0, 1):
        hand = pts[slot]
        if np.any(hand != 0):
            palm = float(np.linalg.norm(hand[9, :2] - hand[0, :2]))
            if palm >= 0.015:
                active.append((palm, hand))
    active.sort(key=lambda item: item[0], reverse=True)
    primary = active[0][1] if len(active) >= 1 else np.zeros((21, 3), dtype=np.float32)
    secondary = active[1][1] if len(active) >= 2 else np.zeros((21, 3), dtype=np.float32)
    return primary, secondary, len(active)


def compute_window_descriptor(raw_vectors):
    """
    Resume una ventana temporal de vectores 126D en un descriptor estructurado:
      - pose_mean (81D): postura media de la mano dominante
      - pose_start (81D): postura en la primera mitad de la ventana
      - pose_end (81D): postura en la segunda mitad de la ventana
      - secondary_mean (81D): postura media de la segunda mano (si es bimanual)
      - pose_change (float): magnitud de cambio postural entre inicio y fin (p. ej. 11-20, J, K, Z)
      - finger_jitter (float): desviación estándar articular en el tiempo
      - wrist_range_x, wrist_range_y (float): rango de movimiento de muñeca (normalizado por palma)
      - wrist_reversals (int): cambios de dirección horizontal/rotacional de muñeca
      - bimanual_ratio (float): fracción de cuadros con 2 manos activas
    """
    poses = []
    sec_poses = []
    wrists = []
    palms = []
    bimanual_count = 0

    for vec in raw_vectors:
        primary, secondary, count = extract_active_hands(vec)
        if count == 0:
            continue
        poses.append(canonical_hand_pose(primary))
        if count >= 2:
            bimanual_count += 1
            sec_poses.append(canonical_hand_pose(secondary))
        wrists.append(primary[0, :2].copy())
        palms.append(max(0.03, float(np.linalg.norm(primary[9, :2] - primary[0, :2]))))

    if not poses:
        return None

    poses_arr = np.stack(poses)
    mid = max(1, len(poses_arr) // 2)
    pose_mean = poses_arr.mean(axis=0)
    pose_start = poses_arr[:mid].mean(axis=0)
    pose_end = poses_arr[mid:].mean(axis=0) if len(poses_arr) > 1 else pose_start.copy()

    for vec in (pose_mean, pose_start, pose_end):
        n = np.linalg.norm(vec)
        if n > 1e-6:
            vec /= n

    if sec_poses:
        secondary_mean = np.stack(sec_poses).mean(axis=0)
        sn = np.linalg.norm(secondary_mean)
        if sn > 1e-6:
            secondary_mean /= sn
    else:
        secondary_mean = np.zeros_like(pose_mean)

    pose_change = float(np.linalg.norm(pose_end - pose_start))
    finger_jitter = float(np.mean(np.std(poses_arr[:, :63], axis=0)))

    wrists_arr = np.stack(wrists)
    mean_palm = float(np.mean(palms))
    wrist_range_x = float(np.ptp(wrists_arr[:, 0]) / mean_palm)
    wrist_range_y = float(np.ptp(wrists_arr[:, 1]) / mean_palm)

    # Contar oscilaciones / giros horizontales de la muñeca (para Ñ o meses inicializados rotados)
    xs = wrists_arr[:, 0] / mean_palm
    direction = 0
    reversals = 0
    anchor = extreme = xs[0]
    for x in xs[1:]:
        if direction == 0:
            if abs(x - anchor) >= 0.18:
                direction = 1 if x > anchor else -1
                extreme = x
        elif (x - extreme) * direction >= 0:
            extreme = x
        elif (extreme - x) * direction >= 0.18:
            reversals += 1
            direction *= -1
            extreme = x

    bimanual_ratio = float(bimanual_count / len(poses_arr))

    return {
        "pose_mean": pose_mean.tolist(),
        "pose_start": pose_start.tolist(),
        "pose_end": pose_end.tolist(),
        "secondary_mean": secondary_mean.tolist(),
        "pose_change": round(pose_change, 4),
        "finger_jitter": round(finger_jitter, 4),
        "wrist_range_x": round(wrist_range_x, 4),
        "wrist_range_y": round(wrist_range_y, 4),
        "wrist_reversals": int(reversals),
        "bimanual_ratio": round(bimanual_ratio, 4),
    }


def score_descriptor_against_prototype(desc, proto):
    """Calcula la similitud [0, 1] entre una ventana observada y un prototipo del banco."""
    p_mean = np.asarray(desc["pose_mean"], dtype=np.float32)
    p_start = np.asarray(desc["pose_start"], dtype=np.float32)
    p_end = np.asarray(desc["pose_end"], dtype=np.float32)

    t_mean = np.asarray(proto["pose_mean"], dtype=np.float32)
    t_start = np.asarray(proto["pose_start"], dtype=np.float32)
    t_end = np.asarray(proto["pose_end"], dtype=np.float32)

    sim_mean = float(np.dot(p_mean, t_mean))
    sim_start = float(np.dot(p_start, t_start))
    sim_end = float(np.dot(p_end, t_end))

    kind = proto.get("motion_kind", "static")
    if kind == "static":
        # En señas estáticas (ej. 1-10, letras estáticas), prima la postura media y baja agitación
        pose_sim = 0.6 * sim_mean + 0.2 * sim_start + 0.2 * sim_end
        motion_penalty = max(0.0, (desc["pose_change"] - 0.35) * 0.25)
        bimanual_penalty = 0.20 if desc["bimanual_ratio"] > 0.5 else 0.0
        raw_score = pose_sim - motion_penalty - bimanual_penalty
    elif kind == "dynamic_transition":
        # En señas de transición/repetición (ej. 11-20, J, K, Q, X, Z)
        pose_sim = 0.40 * sim_mean + 0.30 * sim_start + 0.30 * sim_end
        has_motion = desc["pose_change"] >= 0.08 or desc["finger_jitter"] >= 0.012 or desc["wrist_range_x"] >= 0.15 or desc["wrist_range_y"] >= 0.15
        motion_bonus = 0.04 if has_motion else -0.10
        bimanual_penalty = 0.15 if (proto.get("bimanual_ratio", 0.0) < 0.3 and desc["bimanual_ratio"] > 0.6) else 0.0
        raw_score = pose_sim + motion_bonus - bimanual_penalty
    elif kind == "rotated_initial":
        # Variante conversacional/abreviada de meses (configuración manual + giro/oscilación de muñeca)
        pose_sim = 0.70 * sim_mean + 0.15 * sim_start + 0.15 * sim_end
        rotated = desc["wrist_reversals"] >= 1 or desc["wrist_range_x"] >= 0.22 or desc["pose_change"] >= 0.12
        motion_bonus = 0.06 if rotated else -0.14
        raw_score = pose_sim + motion_bonus
    else:
        # Dinámica / Bimanual (ej. meses completos en video)
        pose_sim = 0.40 * sim_mean + 0.30 * sim_start + 0.30 * sim_end
        if proto.get("bimanual_ratio", 0.0) >= 0.35:
            p_sec = np.asarray(desc["secondary_mean"], dtype=np.float32)
            t_sec = np.asarray(proto["secondary_mean"], dtype=np.float32)
            sec_sim = float(np.dot(p_sec, t_sec)) if desc["bimanual_ratio"] >= 0.25 else 0.0
            pose_sim = 0.65 * pose_sim + 0.35 * sec_sim
        raw_score = pose_sim

    return float(np.clip(raw_score, 0.0, 1.0))


class MediaSignBankEngine:
    """
    Motor de inferencia en tiempo real sobre bancos de prototipos extraídos de C:\\proyectos\\media.
    Compatible con TranslationPipeline y GlossValidator.
    """
    immediate_translation = True

    def __init__(self, categories=("numbers", "alphabet", "months"), bank_paths=None, min_similarity=0.85):
        base_dir = Path(__file__).resolve().parents[2] / "models" / "gestures"
        default_Map = {
            "numbers": base_dir / "numbers_bank.json",
            "alphabet": base_dir / "alphabet_bank.json",
            "months": base_dir / "months_bank.json",
        }
        if bank_paths is None:
            bank_paths = [default_Map[c] for c in categories if c in default_Map and default_Map[c].is_file()]
        self.categories = tuple(categories)
        self.prototypes = []
        versions = []
        for path in bank_paths:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            versions.append(data.get("version", Path(path).stem))
            self.prototypes.extend(data.get("prototypes", []))

        self.predictor = bool(self.prototypes)
        self.model_version = "+".join(versions) if versions else "media-bank-empty"
        self.min_similarity = float(min_similarity)
        self.window_ms = 1000.0
        self.max_gap_ms = 350.0
        self.reset()

    def reset(self):
        self.frames = deque(maxlen=60)
        self.last_frame_id = -1
        self.last_timestamp = -1

    def push(self, frame_id, timestamp_ms, raw_vector):
        if type(frame_id) is not int or frame_id <= self.last_frame_id or not np.isfinite(timestamp_ms) or timestamp_ms <= self.last_timestamp:
            raise ValueError("Frame/timestamp no monotónico")
        vec = finite_array(raw_vector, (126,)).astype(np.float32)
        gap = self.last_timestamp >= 0 and (timestamp_ms - self.last_timestamp) > self.max_gap_ms
        if gap:
            self.frames.clear()
        self.last_frame_id, self.last_timestamp = frame_id, timestamp_ms

        _, _, active_count = extract_active_hands(vec)
        if active_count == 0:
            self.frames.clear()
            return {
                "state": "Partial",
                "reason": None,
                "prediction": {
                    "class_id": 0,
                    "gloss": "REPOSO",
                    "confidence": 1.0,
                    "confidence_kind": "rule_match",
                    "model_version": self.model_version,
                    "frame_id": frame_id,
                    "status": "candidate",
                },
            }

        self.frames.append((timestamp_ms, vec))
        while len(self.frames) > 2 and self.frames[0][0] < timestamp_ms - self.window_ms:
            self.frames.popleft()

        if not self.prototypes or len(self.frames) < 4:
            return {"state": "Partial", "reason": "WINDOW_INCOMPLETE", "prediction": None}

        desc = compute_window_descriptor([item[1] for item in self.frames])
        if desc is None:
            return {"state": "Partial", "reason": "WINDOW_INCOMPLETE", "prediction": None}

        best_gloss = None
        best_score = -1.0
        for proto in self.prototypes:
            score = score_descriptor_against_prototype(desc, proto)
            if score > best_score:
                best_score = score
                best_gloss = proto["gloss"]

        if best_gloss is None or best_score < self.min_similarity:
            return {"state": "Partial", "reason": "LOW_CONFIDENCE", "prediction": None}

        class_id = EXTENDED_INVERSE_LABEL_MAP[best_gloss]
        confidence = float(np.clip(0.85 + 0.15 * ((best_score - self.min_similarity) / max(1e-4, 1.0 - self.min_similarity)), 0.85, 0.99))
        return {
            "state": "Success",
            "reason": None,
            "prediction": {
                "class_id": class_id,
                "gloss": best_gloss,
                "confidence": confidence,
                "confidence_kind": "rule_match",
                "model_version": self.model_version,
                "frame_id": frame_id,
                "status": "candidate",
            },
        }
