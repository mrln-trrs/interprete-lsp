import math
from pathlib import Path
import shutil
import subprocess
from config.actions import ACTIONS


def valid_prediction(class_id, confidence, stable_frames):
    return (type(class_id) is int and 0 <= class_id < len(ACTIONS)
            and type(confidence) in (int, float) and math.isfinite(confidence)
            and 0.85 <= confidence <= 1
            and type(stable_frames) is int and stable_frames >= 10)


def prolog_accepts(class_id, confidence, stable_frames):
    if type(class_id) is not int or type(stable_frames) is not int or type(confidence) not in (int, float) or not math.isfinite(confidence) or not 0 <= confidence <= 1:
        return False
    executable = shutil.which("swipl")
    if not executable:
        raise RuntimeError("SWI-Prolog no está disponible; referencia Python exploratoria")
    rules = Path(__file__).with_name("lsp_rules.pl")
    goal = f"valid_prediction({class_id},{confidence:.17f},{stable_frames}),halt"
    try:
        result = subprocess.run([executable, "-q", "-s", str(rules), "-g", goal, "-t", "halt(1)"],
                                capture_output=True, timeout=0.05, check=False)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False


class GlossValidator:
    def __init__(self):
        self.class_id = None
        self.count = 0
        self.emitted_class = None
        self.last_frame = -1
        self.last_time = -1
        self.rest_start = None

    def reset_candidate(self):
        self.class_id, self.count = None, 0
        self.rest_start = None

    def update(self, prediction, frame_id, timestamp_ms):
        if type(frame_id) is not int or frame_id <= self.last_frame or not math.isfinite(timestamp_ms) or timestamp_ms <= self.last_time:
            self.reset_candidate()
            return {"status": "rejected", "stable_frames": 0, "gloss": None}
        if self.last_time >= 0 and timestamp_ms - self.last_time > 200:
            self.reset_candidate()
        self.last_frame, self.last_time = frame_id, timestamp_ms
        if not prediction:
            self.reset_candidate()
            return {"status": "rejected", "stable_frames": 0, "gloss": None}
        class_id, confidence = prediction.get("class_id"), prediction.get("confidence")
        if not valid_prediction(class_id, confidence, 10):
            self.reset_candidate()
            return {"status": "rejected", "stable_frames": 0, "gloss": None}
        self.count = self.count + 1 if class_id == self.class_id else 1
        self.class_id = class_id
        if class_id == 0:
            if self.rest_start is None:
                self.rest_start = timestamp_ms
            if self.count >= 10 and timestamp_ms - self.rest_start >= 500:
                self.emitted_class = None
                return {"status": "rest", "stable_frames": self.count, "gloss": None}
            return {"status": "candidate", "stable_frames": self.count, "gloss": None}
        self.rest_start = None
        if self.count < 10 or class_id == self.emitted_class:
            return {"status": "candidate", "stable_frames": self.count, "gloss": None}
        self.emitted_class = class_id
        return {"status": "accepted", "stable_frames": self.count, "gloss": ACTIONS[class_id]}
