import base64
from contextlib import nullcontext
import json
import unittest

from flask import Flask
from src.backend.frame_api import MAX_BODY, register_frame_api


def frame_url(width=640, height=480):
    # Header fixture only; the native decoder is intentionally substituted in API tests.
    data = b"\xff\xd8\xff\xc0\x00\x0b\x08" + height.to_bytes(2, "big") + width.to_bytes(2, "big")
    data += b"\x01\x01\x11\x00\xff\xd9"
    return "data:image/jpeg;base64," + base64.b64encode(data).decode()


class TestFrameAPI(unittest.TestCase):
    def setUp(self):
        self.calls = []
        def processor(data):
            self.calls.append(data)
            return {"frame": frame_url(), "hands": [], "keypoints": [0.0] * 126}
        self.app = Flask(__name__)
        register_frame_api(self.app, processor, lambda frame: nullcontext())
        self.client = self.app.test_client()
        self.payload = {"session_id": "a" * 32, "frame_id": 0, "captured_at_ms": 0,
                        "frame": frame_url()}

    def test_success_contract(self):
        response = self.client.post("/api/v1/process-frame", json=self.payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json["data"]["keypoints"]), 126)
        self.assertIsNone(response.json["data"]["prediction"])
        self.assertFalse(response.json["data"]["normalized"])
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_bad_fields_and_types_never_reach_processor(self):
        cases = [{**self.payload, "extra": 1}, {**self.payload, "frame_id": True},
                 {**self.payload, "captured_at_ms": float("nan")},
                 {**self.payload, "frame": "data:image/jpeg;base64,%%%%"},
                 {**self.payload, "frame": frame_url(1281, 720)}]
        for payload in cases:
            with self.subTest(payload=payload):
                response = self.client.post("/api/v1/process-frame", json=payload)
                self.assertIn(response.status_code, (400, 413))
                self.assertEqual(response.mimetype, "application/problem+json")
        self.assertEqual(self.calls, [])

    def test_duplicate_keys_and_wrong_media_type(self):
        response = self.client.post("/api/v1/process-frame", data='{"frame_id":0,"frame_id":1}', content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.post("/api/v1/process-frame", data="{}").status_code, 415)

    def test_limits_and_dimensions(self):
        response = self.client.post("/api/v1/process-frame", data=b" " * (MAX_BODY + 1), content_type="application/json")
        self.assertEqual(response.status_code, 413)
        self.payload["frame"] = frame_url(1280, 720)
        self.assertEqual(self.client.post("/api/v1/process-frame", json=self.payload).status_code, 200)

    def test_processor_failure_hides_internal_details(self):
        app = Flask("failure")
        def fail(data):
            raise RuntimeError("private-internal-detail")
        register_frame_api(app, fail, lambda frame: nullcontext())
        response = app.test_client().post("/api/v1/process-frame", json=self.payload)
        self.assertEqual(response.status_code, 500)
        self.assertNotIn("private-internal-detail", response.get_data(as_text=True))

    def test_unconfigured_service_fails_closed(self):
        app = Flask("unconfigured")
        register_frame_api(app, None)
        response = app.test_client().post("/api/v1/process-frame", json=self.payload)
        self.assertEqual(response.status_code, 503)


if __name__ == "__main__":
    unittest.main()
