"""Opt-in geometric greeting, using raw image coordinates before normalization."""
from collections import deque
import json
from pathlib import Path
import numpy as np
from src.vision.normalization import finite_array


class WaveGreetingEngine:
    immediate_translation = True

    def __init__(self):
        path = Path(__file__).resolve().parents[2] / 'models/gestures/wave_hola.json'
        self.config = json.loads(path.read_text(encoding='utf-8'))
        # Availability marker for the shared pipeline, not a neural predictor.
        self.predictor = True
        self.model_version = self.config['version']
        self.reset()

    def reset(self):
        self.frames = deque(maxlen=80)
        self.last_frame_id = -1
        self.last_timestamp = -1
        self.previous_wrist = None
        self.latched_until = -1
        self.armed = True
        self.absent_since = None

    @staticmethod
    def open_hand(points):
        if not np.any(points):
            return False
        palm = np.linalg.norm(points[9, :2] - points[0, :2])
        if palm < 0.025:
            return False
        # Three extended fingers suffice; thumb is deliberately not required.
        extended = sum(np.linalg.norm(points[tip, :2] - points[0, :2]) >
                       1.15 * np.linalg.norm(points[pip, :2] - points[0, :2])
                       for tip, pip in ((8, 6), (12, 10), (16, 14), (20, 18)))
        return extended >= 3

    def waving(self):
        if len(self.frames) < 6:
            return False
        times, xs, ys = np.asarray(self.frames).T
        if times[-1] - times[0] < self.config['min_duration_ms']:
            return False
        if np.ptp(xs) < self.config['min_range'] or np.ptp(ys) > self.config['max_vertical_range']:
            return False
        direction, reversals = 0, 0
        anchor, extreme = xs[0], xs[0]
        for x in xs[1:]:
            if direction == 0:
                if abs(x - anchor) >= self.config['min_swing']:
                    direction = 1 if x > anchor else -1
                    extreme = x
            elif (x - extreme) * direction >= 0:
                extreme = x
            elif (extreme - x) * direction >= self.config['min_swing']:
                reversals += 1
                direction *= -1
                extreme = x
        return reversals >= self.config['reversals']

    def push(self, frame_id, timestamp_ms, raw_vector):
        if type(frame_id) is not int or frame_id <= self.last_frame_id or not np.isfinite(timestamp_ms) or timestamp_ms <= self.last_timestamp:
            raise ValueError('Frame/timestamp no monotónico')
        points = finite_array(raw_vector, (126,)).reshape(2, 21, 3)
        gap = self.last_timestamp >= 0 and timestamp_ms - self.last_timestamp > self.config['max_gap_ms']
        if gap:
            self.frames.clear()
            self.previous_wrist = None
            self.latched_until = -1
        self.last_frame_id, self.last_timestamp = frame_id, timestamp_ms
        hands = [hand for hand in points if self.open_hand(hand)]
        if not hands:
            self.frames.clear()
            self.previous_wrist = None
            if self.absent_since is None:
                self.absent_since = timestamp_ms
            if timestamp_ms - self.absent_since >= self.config['rearm_ms']:
                self.armed = True
        else:
            self.absent_since = None
            hand = min(hands, key=lambda h: np.linalg.norm(h[0, :2] - self.previous_wrist)) if self.previous_wrist is not None else hands[0]
            wrist = hand[0, :2]
            if self.previous_wrist is not None and np.linalg.norm(wrist - self.previous_wrist) > 0.25:
                self.frames.clear()
            self.previous_wrist = wrist.copy()
            self.frames.append((timestamp_ms, float(wrist[0]), float(wrist[1])))
            while self.frames and self.frames[0][0] < timestamp_ms - self.config['window_ms']:
                self.frames.popleft()
            if self.armed and self.waving():
                self.latched_until = timestamp_ms + self.config['hold_ms']
                self.armed = False
                self.frames.clear()
        matched = timestamp_ms < self.latched_until
        return {'state': 'Success' if matched else 'Partial', 'reason': None if matched else 'WAVE_PENDING',
                'prediction': {'class_id': 1 if matched else 0, 'gloss': 'HOLA' if matched else 'REPOSO',
                               'confidence': 1.0, 'confidence_kind': 'rule_match',
                               'model_version': self.model_version, 'frame_id': frame_id, 'status': 'candidate'}}
