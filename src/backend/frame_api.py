"""Strict v1 frame boundary; native vision is injected, not imported here."""
from dataclasses import dataclass
import base64
import binascii
import json
import math
import re
import time
import uuid

from flask import jsonify, request
from werkzeug.exceptions import HTTPException

MAX_BODY = 1024 * 1024
MAX_WIDTH = 1280
MAX_HEIGHT = 720


class ApiError(Exception):
    def __init__(self, status, code, message):
        self.status, self.code, self.message = status, code, message
        super().__init__(message)


def jpeg_dimensions(data):
    """Inspect SOF before native decode; malformed compressed data still needs decode validation."""
    if not data.startswith(b"\xff\xd8") or not data.endswith(b"\xff\xd9"):
        raise ApiError(400, "INVALID_FRAME", "El frame no contiene un JPEG válido.")
    position = 2
    dimensions = None
    while position < len(data) - 2:
        if data[position] != 255:
            break
        while position < len(data) and data[position] == 255:
            position += 1
        if position >= len(data):
            break
        marker = data[position]
        position += 1
        if marker in (0xD8, 0xD9, 0xDA, 0):
            break
        if 0xD0 <= marker <= 0xD7 or marker == 0x01:
            continue
        if position + 2 > len(data):
            break
        length = int.from_bytes(data[position:position + 2], "big")
        if length < 2 or position + length > len(data):
            break
        if marker in (0xC0, 0xC1, 0xC2):
            if dimensions is not None:
                raise ApiError(400, "INVALID_FRAME", "La imagen tiene cabeceras contradictorias.")
            if length < 8:
                break
            height = int.from_bytes(data[position + 3:position + 5], "big")
            width = int.from_bytes(data[position + 5:position + 7], "big")
            if width < 1 or height < 1:
                break
            if width > MAX_WIDTH or height > MAX_HEIGHT:
                raise ApiError(413, "IMAGE_TOO_LARGE", "La imagen excede las dimensiones permitidas.")
            dimensions = (width, height)
        position += length
    if dimensions is not None:
        return dimensions
    raise ApiError(400, "INVALID_FRAME", "La cabecera JPEG no es válida.")


def decode_jpeg(value):
    if not isinstance(value, str) or not value.startswith("data:image/jpeg;base64,"):
        raise ApiError(400, "INVALID_FRAME", "Se requiere un JPEG en data URL.")
    if len(value) > MAX_BODY:
        raise ApiError(413, "PAYLOAD_TOO_LARGE", "La solicitud excede el límite permitido.")
    try:
        data = base64.b64decode(value.split(",", 1)[1], validate=True)
    except (ValueError, binascii.Error):
        raise ApiError(400, "INVALID_FRAME", "El contenido base64 no es válido.") from None
    jpeg_dimensions(data)
    return data


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def _constant(value):
    raise ValueError("non-finite JSON")


def strict_json_request():
    if request.mimetype != "application/json":
        raise ApiError(415, "UNSUPPORTED_MEDIA_TYPE", "Se requiere application/json.")
    # Bounded read also protects requests without a trusted Content-Length.
    if request.content_length is not None and request.content_length > MAX_BODY:
        raise ApiError(413, "PAYLOAD_TOO_LARGE", "La solicitud excede el límite permitido.")
    body = request.stream.read(MAX_BODY + 1)
    if len(body) > MAX_BODY:
        raise ApiError(413, "PAYLOAD_TOO_LARGE", "La solicitud excede el límite permitido.")
    try:
        payload = json.loads(body, object_pairs_hook=_object, parse_constant=_constant)
    except (ValueError, UnicodeError):
        raise ApiError(400, "INVALID_JSON", "El JSON no es válido.") from None
    if not isinstance(payload, dict):
        raise ApiError(400, "INVALID_PAYLOAD", "Se requiere un objeto JSON.")
    return payload


@dataclass(frozen=True)
class FrameRequest:
    session_id: str
    frame_id: int
    captured_at_ms: float
    jpeg: bytes

    @classmethod
    def parse(cls, payload):
        if set(payload) != {"session_id", "frame_id", "captured_at_ms", "frame"}:
            raise ApiError(400, "INVALID_FIELDS", "Los campos no corresponden al contrato.")
        session = payload["session_id"]
        frame_id = payload["frame_id"]
        timestamp = payload["captured_at_ms"]
        if not isinstance(session, str) or not re.fullmatch(r"[A-Za-z0-9_-]{16,128}", session):
            raise ApiError(400, "INVALID_SESSION", "La sesión no es válida.")
        if type(frame_id) is not int or not 0 <= frame_id <= 2**53 - 1:
            raise ApiError(400, "INVALID_FRAME_ID", "El identificador de frame no es válido.")
        if type(timestamp) not in (int, float) or not math.isfinite(timestamp) or timestamp < 0:
            raise ApiError(400, "INVALID_TIMESTAMP", "El timestamp no es válido.")
        return cls(session, frame_id, float(timestamp), decode_jpeg(payload["frame"]))


def validate_result(result):
    vector = result.get("keypoints")
    if not isinstance(vector, list) or len(vector) != 126:
        raise ValueError("Invalid processor vector")
    if any(type(value) not in (int, float) or not math.isfinite(value) for value in vector):
        raise ValueError("Non-finite processor vector")
    try:
        decode_jpeg(result.get("frame"))
    except ApiError:
        raise ValueError("Invalid processor image") from None
    hands = result.get("hands")
    if not isinstance(hands, list) or len(hands) > 2:
        raise ValueError("Invalid hands")
    for hand in hands:
        if set(hand) != {"side", "confidence"} or hand["side"] not in ("Left", "Right"):
            raise ValueError("Invalid hand metadata")
        confidence = hand["confidence"]
        if type(confidence) not in (int, float) or not math.isfinite(confidence) or not 0 <= confidence <= 1:
            raise ValueError("Invalid hand confidence")
    return {"frame": result["frame"], "hands": hands, "keypoints": vector,
            "feature_schema": "hands-126-v1", "normalized": False, "prediction": None}


def register_frame_api(app, processor, acquire_session=None):
    """acquire_session returns a context manager serializing an authorized session."""
    app.config["MAX_CONTENT_LENGTH"] = MAX_BODY

    def problem(error):
        response = jsonify({"type": "about:blank", "title": "Error de procesamiento",
                            "status": error.status, "detail": error.message,
                            "instance": request.path, "code": error.code,
                            "request_id": uuid.uuid4().hex})
        response.status_code = error.status
        response.mimetype = "application/problem+json"
        return response

    app.register_error_handler(ApiError, problem)

    @app.errorhandler(HTTPException)
    def http_error(error):
        return problem(ApiError(error.code, "HTTP_ERROR", error.name))

    @app.after_request
    def no_store(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.post("/api/v1/process-frame")
    def process_frame_v1():
        frame = FrameRequest.parse(strict_json_request())
        if acquire_session is None or processor is None:
            raise ApiError(503, "SERVICE_UNAVAILABLE", "El procesamiento no está disponible.")
        request_id = uuid.uuid4().hex
        start = time.perf_counter()
        try:
            with acquire_session(frame):
                result = validate_result(processor(frame.jpeg))
            result.update(frame_id=frame.frame_id, processing_ms=(time.perf_counter() - start) * 1000)
            return jsonify(success=True, data=result, error=None, request_id=request_id)
        except ApiError:
            raise
        except Exception:
            # Do not log exception strings, frames, tokens or derived features.
            app.logger.error("frame_failed request_id=%s", request_id)
            return problem(ApiError(500, "PROCESSING_FAILED", "No se pudo procesar el frame."))
