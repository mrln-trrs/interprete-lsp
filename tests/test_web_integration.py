import base64
import unittest
import cv2
import numpy as np
from src.backend.sessions import SessionManager
from src.inference.engine import InferenceEngine
from src.inference.pipeline import TranslationPipeline
import web_server


class TestWebIntegration(unittest.TestCase):
    def test_real_decoder_detector_without_fake_translation(self):
        manager = web_server._sessions
        old = (manager.access_key, manager.allowed_origins, manager.session, web_server._detector)
        try:
            manager.access_key = "integration-test-key-" + "0" * 32
            manager.allowed_origins = frozenset({"http://localhost"})
            manager.session = None
            detector = web_server.HandDetector()
            web_server._detector = detector
            client = web_server.app.test_client()
            authorization = {"Origin": "http://localhost", "Authorization": "Bearer " + manager.access_key}
            response = client.post("/api/v1/sessions", json={}, headers=authorization)
            self.assertEqual(response.status_code, 201)
            token = response.json["data"]["session_id"]
            ok, jpeg = cv2.imencode(".jpg", np.zeros((480, 640, 3), np.uint8))
            self.assertTrue(ok)
            frame = "data:image/jpeg;base64," + base64.b64encode(jpeg).decode()
            response = client.post("/api/v1/process-frame", json={"session_id": token, "frame_id": 0,
                "captured_at_ms": 0, "frame": frame}, headers={"Origin": "http://localhost", "Authorization": "Bearer " + token})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.json["data"]["keypoints"]), 126)
            self.assertIsNone(response.json["data"]["prediction"])
            self.assertFalse(response.json["data"]["model_available"])
            self.assertEqual(response.json["data"]["confirmed_text"], "")
            self.assertEqual(client.post("/process_frame", json={"frame": frame}).status_code, 410)
            with client.get("/static/app.js") as static_response:
                self.assertEqual(static_response.status_code, 200)
            self.assertEqual(client.get("/").status_code, 200)
        finally:
            if web_server._detector is not old[3]:
                web_server._detector.hands.close()
            manager.access_key, manager.allowed_origins, manager.session, web_server._detector = old
