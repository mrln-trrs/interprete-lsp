import unittest
from flask import Flask
from src.backend.frame_api import register_frame_api
from src.backend.sessions import SessionManager, register_sessions
from test_api import frame_url


class TestSessions(unittest.TestCase):
    def setUp(self):
        self.now = 0.0
        self.manager = SessionManager("x" * 40, {"http://localhost"}, lambda: self.now)
        self.app = Flask(__name__)
        register_frame_api(self.app, lambda data: {"frame": frame_url(), "hands": [], "keypoints": [0.0] * 126}, self.manager.acquire)
        register_sessions(self.app, self.manager)
        self.client = self.app.test_client()
        self.headers = {"Origin": "http://localhost", "Authorization": "Bearer " + "x" * 40}

    def create(self):
        response = self.client.post("/api/v1/sessions", json={}, headers=self.headers)
        self.assertEqual(response.status_code, 201)
        return response.json["data"]["session_id"]

    def frame(self, token, frame_id=0, **kwargs):
        headers = {"Origin": "http://localhost", "Authorization": "Bearer " + token}
        return self.client.post("/api/v1/process-frame", json={"session_id": token, "frame_id": frame_id,
            "captured_at_ms": frame_id, "frame": frame_url(), **kwargs}, headers=headers)

    def test_origin_and_authorization(self):
        self.assertEqual(self.client.post("/api/v1/sessions", json={}).status_code, 403)
        wrong = {**self.headers, "Authorization": "Bearer invalid"}
        self.assertEqual(self.client.post("/api/v1/sessions", json={}, headers=wrong).status_code, 401)
        self.assertEqual(self.frame("z" * 32).status_code, 401)

    def test_capacity_order_and_expiration(self):
        token = self.create()
        self.assertEqual(self.client.post("/api/v1/sessions", json={}, headers=self.headers).status_code, 503)
        self.assertEqual(self.frame(token).status_code, 200)
        self.assertEqual(self.frame(token).status_code, 409)
        self.now = 301
        self.assertEqual(self.frame(token, 1).status_code, 401)
        self.create()

    def test_quota_and_delete(self):
        token = self.create()
        for index in range(15):
            self.assertEqual(self.frame(token, index).status_code, 200)
        response = self.frame(token, 15)
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.headers["Retry-After"], "1")
        self.now += 1.01
        self.assertEqual(self.frame(token, 16).status_code, 200)
        headers = {**self.headers, "Authorization": "Bearer " + token}
        self.assertEqual(self.client.delete("/api/v1/sessions/" + token, headers=headers).status_code, 204)
        self.assertEqual(self.frame(token, 17).status_code, 401)
        new_token = self.create()
        self.assertNotEqual(new_token, token)
        self.assertEqual(self.frame(new_token).status_code, 200)

    def test_busy_has_no_queue(self):
        token = self.create()
        self.manager.lock.acquire()
        try:
            self.assertEqual(self.frame(token).status_code, 503)
        finally:
            self.manager.lock.release()

    def test_missing_configuration_fails_closed(self):
        self.manager.access_key = None
        self.assertEqual(self.client.post("/api/v1/sessions", json={}, headers=self.headers).status_code, 503)

    def test_creation_rate_limit_and_security_headers(self):
        headers = {**self.headers, "Authorization": "Bearer invalid"}
        for _ in range(30):
            self.assertEqual(self.client.post("/api/v1/sessions", json={}, headers=headers).status_code, 401)
        response = self.client.post("/api/v1/sessions", json={}, headers=headers)
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.headers["Referrer-Policy"], "no-referrer")
        self.now = 61
        self.create()
