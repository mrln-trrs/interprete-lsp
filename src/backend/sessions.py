"""One authorized session, no unbounded queues or shared tracking history."""
from collections import deque
from contextlib import contextmanager
import hmac
import secrets
import threading
import time

from flask import jsonify, request
from src.backend.frame_api import ApiError, strict_json_request


class SessionManager:
    def __init__(self, access_key, allowed_origins, clock=time.monotonic):
        self.access_key = access_key
        self.allowed_origins = frozenset(allowed_origins)
        self.clock = clock
        self.lock = threading.Lock()
        self.session = None
        self.create_attempts = deque()

    def check_origin(self):
        if request.headers.get("Origin") not in self.allowed_origins:
            raise ApiError(403, "ORIGIN_DENIED", "El origen no está autorizado.")
        if request.headers.get("Sec-Fetch-Site") == "cross-site":
            raise ApiError(403, "ORIGIN_DENIED", "El origen no está autorizado.")

    @staticmethod
    def bearer():
        value = request.headers.get("Authorization", "")
        if not value.startswith("Bearer ") or len(value) > 512:
            raise ApiError(401, "UNAUTHORIZED", "Se requiere autorización.")
        return value[7:]

    @contextmanager
    def exclusive(self):
        if not self.lock.acquire(blocking=False):
            raise ApiError(503, "BUSY", "El procesador está ocupado.")
        try:
            if self.session and self.clock() - self.session["last_activity"] >= 300:
                self.session = None
            yield
        finally:
            self.lock.release()

    def create(self):
        self.check_origin()
        payload = strict_json_request()
        if payload:
            raise ApiError(400, "INVALID_FIELDS", "La apertura de sesión no requiere campos.")
        if not self.access_key or len(self.access_key) < 32:
            raise ApiError(503, "NOT_CONFIGURED", "El acceso no está configurado.")
        with self.exclusive():
            now = self.clock()
            while self.create_attempts and now - self.create_attempts[0] >= 60:
                self.create_attempts.popleft()
            if len(self.create_attempts) >= 30:
                raise ApiError(429, "RATE_LIMIT", "Espere antes de volver a intentar.")
            self.create_attempts.append(now)
            if not hmac.compare_digest(self.bearer().encode(), self.access_key.encode()):
                raise ApiError(401, "UNAUTHORIZED", "La clave no es válida.")
            if self.session:
                raise ApiError(503, "CAPACITY", "Ya hay una sesión activa.")
            token = secrets.token_urlsafe(32)
            self.session = {"id": token, "last_activity": now, "frame_id": -1,
                            "timestamp": -1, "requests": deque()}
            return token

    def authorized_session(self, session_id):
        session = self.session
        bearer = self.bearer()
        if not session or not hmac.compare_digest(session_id.encode(), session["id"].encode()) or not hmac.compare_digest(bearer.encode(), session["id"].encode()):
            raise ApiError(401, "UNAUTHORIZED", "La sesión no está autorizada.")
        return session

    @contextmanager
    def acquire(self, frame):
        self.check_origin()
        with self.exclusive():
            session = self.authorized_session(frame.session_id)
            now = self.clock()
            requests = session["requests"]
            while requests and now - requests[0] >= 1:
                requests.popleft()
            if len(requests) >= 15:
                raise ApiError(429, "RATE_LIMIT", "La sesión alcanzó el límite de frames.")
            requests.append(now)
            if frame.frame_id <= session["frame_id"] or frame.captured_at_ms <= session["timestamp"]:
                raise ApiError(409, "FRAME_ORDER", "El frame está duplicado o fuera de orden.")
            # Consume IDs even on decoder failure; a retry must carry a new frame.
            session["frame_id"] = frame.frame_id
            session["timestamp"] = frame.captured_at_ms
            session["last_activity"] = now
            yield

    def delete(self, session_id):
        self.check_origin()
        with self.exclusive():
            self.authorized_session(session_id)
            self.session = None


def register_sessions(app, manager):
    @app.before_request
    def protected_origin():
        if request.path.startswith("/api/v1/") and request.method in ("POST", "DELETE"):
            manager.check_origin()

    @app.post("/api/v1/sessions")
    def create_session():
        token = manager.create()
        return jsonify(success=True, data={"session_id": token, "expires_after_idle_seconds": 300}, error=None), 201

    @app.delete("/api/v1/sessions/<session_id>")
    def delete_session(session_id):
        manager.delete(session_id)
        return "", 204

    @app.after_request
    def security_headers(response):
        if response.status_code in (429, 503):
            response.headers["Retry-After"] = "1"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(self), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; font-src 'self'; frame-ancestors 'none'; base-uri 'none'"
        return response
