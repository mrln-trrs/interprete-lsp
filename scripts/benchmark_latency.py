"""T-PERF-01: RTT de /api/v1/process-frame contra un servidor en marcha (p50/p95).

Uso: python -m scripts.benchmark_latency --url http://127.0.0.1:5000 --seconds 300 --fps 12
Sin LSP_ACCESS_KEY en el servidor no hace falta --key. El frame es sintético (sin manos)
salvo que se pase --image; sin manos MediaPipe trabaja menos, así que no acredita el peor caso.
"""
import argparse
import base64
import json
import platform
import statistics
import time
import urllib.request
from pathlib import Path

import cv2
import numpy as np


def post(url, origin, payload, bearer=None):
    headers = {"Content-Type": "application/json", "Origin": origin}
    if bearer:
        headers["Authorization"] = "Bearer " + bearer
    request = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=5) as response:
        body = response.read()
        return response.status, json.loads(body) if body else None


def percentile(values, q):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round(q / 100 * (len(ordered) - 1)))]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:5000")
    parser.add_argument("--origin", default=None, help="Por defecto, el mismo --url")
    parser.add_argument("--key", default=None)
    parser.add_argument("--seconds", type=float, default=300)
    parser.add_argument("--fps", type=float, default=12)
    parser.add_argument("--image", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    origin = args.origin or args.url.rstrip("/")

    image = cv2.imread(str(args.image)) if args.image else np.zeros((480, 640, 3), np.uint8)
    ok, jpeg = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 70])
    if not ok:
        raise SystemExit("No se pudo codificar el frame")
    frame = "data:image/jpeg;base64," + base64.b64encode(jpeg).decode()

    status, created = post(args.url + "/api/v1/sessions", origin, {}, args.key)
    session_id = created["data"]["session_id"]
    rtts, errors, frame_id = [], {}, 0
    start = time.monotonic()
    try:
        while time.monotonic() - start < args.seconds:
            tick = time.monotonic()
            try:
                post(args.url + "/api/v1/process-frame", origin, {"session_id": session_id, "frame_id": frame_id,
                     "captured_at_ms": int((tick - start) * 1000) + frame_id, "frame": frame}, session_id)
                rtts.append((time.monotonic() - tick) * 1000)
            except Exception as error:  # Se cuentan, no se ocultan.
                key = type(error).__name__ + ":" + str(getattr(error, "code", ""))
                errors[key] = errors.get(key, 0) + 1
            frame_id += 1
            time.sleep(max(0.0, 1 / args.fps - (time.monotonic() - tick)))
    finally:
        request = urllib.request.Request(args.url + "/api/v1/sessions/" + session_id, method="DELETE",
                                         headers={"Origin": origin, "Authorization": "Bearer " + session_id})
        urllib.request.urlopen(request, timeout=5).close()

    result = {
        "test": "T-PERF-01", "frames_sent": frame_id, "frames_ok": len(rtts), "errors": errors,
        "seconds": round(time.monotonic() - start, 1), "target_fps": args.fps,
        "rtt_ms": {"p50": round(percentile(rtts, 50), 1), "p95": round(percentile(rtts, 95), 1),
                   "max": round(max(rtts), 1), "mean": round(statistics.fmean(rtts), 1)} if rtts else None,
        "frame": str(args.image) if args.image else "sintético 640x480 sin manos, JPEG q70",
        "jpeg_bytes": len(jpeg), "client": platform.platform(), "python": platform.python_version(),
    }
    text = json.dumps(result, ensure_ascii=False, indent=1)
    print(text)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
