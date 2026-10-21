import os
from pathlib import Path
import select
import shutil
import subprocess
import tempfile
import threading
import time
import unittest
import numpy as np
from config.actions import ACTIONS
from src.inference.pipeline import TranslationPipeline
from src.hardware.serial_controller import FirmwareSimulator, ProtocolError, SerialController, encode_frame, parse_frame

ROOT = Path(__file__).resolve().parents[1]


class Loopback:
    """Puerto simulado sobre FirmwareSimulator con fallas inyectables."""

    def __init__(self, device=None, drop_replies=0, fail_write=False):
        self.device = device or FirmwareSimulator()
        self.drop_replies, self.fail_write = drop_replies, fail_write
        self.replies, self.writes, self.closed = [], [], False

    def write(self, frame):
        if self.fail_write:
            raise OSError("cable desconectado")
        self.writes.append(frame)
        for reply in self.device.feed(frame):
            if self.drop_replies:
                self.drop_replies -= 1
            else:
                self.replies.append(reply)

    def readline(self):
        return self.replies.pop(0) if self.replies else b""

    def close(self):
        self.closed = True


def frame(seq, cmd, arg):
    return f"V1|{seq}|{cmd}|{arg}\n".encode()


class TestProtocol(unittest.TestCase):
    def test_hw_t01_valid_commands_ack_and_effect_once(self):
        device = FirmwareSimulator()
        replies = device.feed(frame(0, "PING", "-") + frame(1, "GLOSS", 3) + frame(2, "CLEAR", "-"))
        self.assertEqual(replies, [b"V1|0|ACK|-\n", b"V1|1|ACK|-\n", b"V1|2|ACK|-\n"])
        self.assertEqual(device.effects, [("GLOSS", 3), ("CLEAR", None)])

    def test_hw_t02_seq_boundaries(self):
        for seq, valid in (("-1", False), ("0", True), ("65535", True), ("65536", False)):
            with self.subTest(seq=seq):
                reply = FirmwareSimulator().feed(frame(seq, "CLEAR", "-"))[0]
                self.assertEqual(reply.split(b"|")[2] == b"ACK", valid)
        with self.assertRaises(ValueError):
            encode_frame(65536, "PING")

    def test_hw_t03_gloss_boundaries(self):
        for gloss, expected in (("-1", b"V1|1|ERR|FORMAT\n"), ("0", b"V1|1|ACK|-\n"), ("8", b"V1|1|ACK|-\n"), ("9", b"V1|1|ERR|RANGE\n")):
            with self.subTest(gloss=gloss):
                self.assertEqual(FirmwareSimulator().feed(frame(1, "GLOSS", gloss)), [expected])

    def test_hw_t04_length_boundaries(self):
        prefix = b"V1|7|PING|"
        for total, accepted in ((63, True), (64, True), (65, False)):
            with self.subTest(total=total):
                padding = b"-" + b" " * (total - len(prefix) - 2)  # Mismo número de campos; el ARG inválido no importa aquí
                line = prefix + padding + b"\n"
                self.assertEqual(len(line), total)
                reply = FirmwareSimulator().feed(line)
                # Admitida = la firmware llega a validar campos (responde con SEQ); rechazada por longitud = SEQ "-"
                self.assertEqual(reply[0].startswith(b"V1|7|"), accepted)
        device = FirmwareSimulator()
        self.assertEqual(device.feed(b"V1|1|PING|-" + b"x" * 80 + b"\n" + frame(2, "PING", "-")),
                         [b"V1|-|ERR|FORMAT\n", b"V1|2|ACK|-\n"])  # Tras overflow vacía hasta LF y sigue sano

    def test_hw_t05_malformed_frames_no_effect(self):
        cases = {b"V1|1|PING\n": b"V1|-|ERR|FORMAT\n", b"V1|1|PING|-|x\n": b"V1|-|ERR|FORMAT\n",
                 b"V2|1|PING|-\n": b"V1|1|ERR|VERSION\n", b"V1|1|BLINK|-\n": b"V1|1|ERR|COMMAND\n",
                 b"V1|1|CLEAR|x\n": b"V1|1|ERR|FORMAT\n", b"V1|1|GLO\x01SS|2\n": b"V1|-|ERR|FORMAT\n",
                 b"V1||PING|-\n": b"V1|-|ERR|FORMAT\n"}
        for line, expected in cases.items():
            with self.subTest(line=line):
                device = FirmwareSimulator()
                self.assertEqual(device.feed(line), [expected])
                self.assertEqual(device.effects, [])
        device = FirmwareSimulator()
        self.assertEqual(device.feed(b"V1|1|GLOSS|2"), [])  # Sin LF: no responde; el host vence por timeout
        self.assertEqual(device.effects, [])
        with self.assertRaises(ProtocolError):
            parse_frame(b"V1|1|PING|-")

    def test_hw_t07_idempotence(self):
        device = FirmwareSimulator()
        replies = device.feed(frame(5, "GLOSS", 2) + frame(5, "GLOSS", 2) + frame(5, "GLOSS", 4))
        self.assertEqual(replies, [b"V1|5|ACK|-\n", b"V1|5|ACK|-\n", b"V1|5|ERR|FORMAT\n"])
        self.assertEqual(device.effects, [("GLOSS", 2)])


class TestController(unittest.TestCase):
    def connected(self, **kwargs):
        port = Loopback(**kwargs)
        controller = SerialController(transport_factory=lambda: port)
        self.assertTrue(controller.connect())
        return controller, port

    def test_latest_output_wins_and_extended_classes_skipped(self):
        controller, port = self.connected()
        self.assertFalse(controller.submit(20))  # Números/letras/meses no viajan en V1
        controller.submit(1)
        controller.submit(2)
        controller.submit(None)
        self.assertTrue(controller.process_pending())
        self.assertFalse(controller.process_pending())
        self.assertEqual(port.device.effects, [("CLEAR", None)])

    def test_retry_once_after_timeout_without_repeating_effect(self):
        controller, port = self.connected()
        port.drop_replies = 1
        controller.submit(3)
        self.assertTrue(controller.process_pending())
        self.assertEqual(len(port.writes), 3)  # PING + GLOSS + reintento
        self.assertEqual(port.device.effects, [("GLOSS", 3)])

    def test_hw_t06_disconnect_degrades_and_reconnect_discards_old(self):
        controller, port = self.connected()
        port.fail_write = True
        controller.submit(4)
        self.assertFalse(controller.process_pending())
        self.assertEqual((controller.state, controller.last_error), ("Partial", "OSError"))
        self.assertTrue(port.closed)
        controller.submit(5)  # Salida antigua mientras está degradado: no se reproduce tras reconectar
        port.fail_write = False
        self.assertTrue(controller.reconnect(attempts=1))
        self.assertFalse(controller.process_pending())
        self.assertEqual(port.device.effects, [])

    def test_two_timeouts_degrade_without_blocking(self):
        controller, port = self.connected()
        port.drop_replies = 2
        controller.submit(1)
        self.assertFalse(controller.process_pending())
        self.assertEqual(controller.last_error, "TimeoutError")

    def test_missing_port_keeps_system_working(self):
        def missing():
            raise OSError("no existe COM3")
        controller = SerialController(transport_factory=missing)
        self.assertFalse(controller.reconnect(attempts=2, backoff=0))
        self.assertEqual(controller.state, "Partial")

    def test_worker_thread_sends_without_blocking_caller(self):
        controller, port = self.connected()
        controller.start()
        try:
            started = time.monotonic()
            controller.submit(6)
            self.assertLess(time.monotonic() - started, 0.05)
            deadline = time.monotonic() + 2
            while not port.device.effects and time.monotonic() < deadline:
                time.sleep(0.01)
        finally:
            controller.close()
        self.assertEqual(port.device.effects, [("GLOSS", 6)])
        self.assertEqual(controller.state, "Disabled")


@unittest.skipUnless(hasattr(os, "openpty"), "Puerto virtual pty solo en Linux/macOS")
class TestPySerialVirtualPort(unittest.TestCase):
    """pyserial real contra un puerto virtual cuyo otro extremo ejecuta FirmwareSimulator."""

    def test_real_pyserial_handshake_and_gloss(self):
        import serial  # noqa: F401  (pyserial debe estar instalado)
        master, slave = os.openpty()
        device, stop = FirmwareSimulator(), threading.Event()

        def firmware():
            while not stop.is_set():
                ready, _, _ = select.select([master], [], [], 0.05)
                if ready:
                    for reply in device.feed(os.read(master, 256)):
                        os.write(master, reply)

        worker = threading.Thread(target=firmware, daemon=True)
        worker.start()
        controller = SerialController(os.ttyname(slave), 9600, timeout=0.5)
        try:
            self.assertTrue(controller.connect(), controller.last_error)
            controller.submit(2)
            self.assertTrue(controller.process_pending())
            controller.submit(None)
            self.assertTrue(controller.process_pending())
        finally:
            controller.close()
            stop.set()
            worker.join(1)
            os.close(master)
            os.close(slave)
        self.assertEqual(device.effects, [("GLOSS", 2), ("CLEAR", None)])


class StubEngine:
    predictor = object()

    def __init__(self, class_id):
        self.class_id = class_id

    def push(self, frame_id, timestamp_ms, raw_vector):
        return {"state": "Success", "reason": None,
                "prediction": {"class_id": self.class_id, "gloss": ACTIONS[self.class_id], "confidence": 0.99,
                               "model_version": "stub", "frame_id": frame_id, "status": "candidate"}}


class TestPipelineOutput(unittest.TestCase):
    def test_only_validated_gloss_reaches_device(self):
        sent = []
        pipeline = TranslationPipeline(StubEngine(1), on_gloss=sent.append)
        for frame_id in range(9):  # Por debajo de STABILITY_FRAMES: candidato, no salida
            pipeline.push(frame_id, frame_id * 33.0, np.zeros(126))
        self.assertEqual(sent, [])
        for frame_id in range(9, 40):
            pipeline.push(frame_id, frame_id * 33.0, np.zeros(126))
        self.assertEqual(sent, [1])  # Una sola salida por seña estable (deduplicada por el validador)


@unittest.skipUnless(shutil.which("g++"), "Requiere g++ para compilar el firmware en el host")
class TestFirmwareParity(unittest.TestCase):
    """El .ino real, compilado en el host, responde igual que FirmwareSimulator."""

    def test_firmware_matches_simulator(self):
        stream = b"".join([
            frame(0, "PING", "-"), frame(1, "GLOSS", 0), frame(1, "GLOSS", 0), frame(1, "GLOSS", 8),
            frame(2, "GLOSS", 8), frame(3, "GLOSS", 9), frame(4, "GLOSS", "-1"), frame(5, "CLEAR", "-"),
            frame(65535, "PING", "-"), frame(65536, "PING", "-"), frame("-1", "PING", "-"), frame("", "PING", "-"),
            frame("123456", "PING", "-"), b"V2|9|PING|-\n", b"V2|x|PING|-\n", b"V1|9|BLINK|-\n", b"V1|9|PING|x\n",
            b"V1|9|PING\n", b"V1|9|PING|-|x\n", b"V1|9|GL\x7fOSS|1\n", b"\n", b"|||\n",
            b"V1|10|PING|" + b"-" * 52 + b"\n", b"V1|11|PING|-" + b" " * 51 + b"\n",
            b"V1|12|PING|-" + b"y" * 70 + b"\n", frame(13, "GLOSS", 7), frame(13, "CLEAR", "-"), b"V1|14|GLOSS|2",
        ])
        simulator = FirmwareSimulator()
        expected = b"".join(simulator.feed(stream))
        effects = "".join(f"{cmd} {-1 if arg is None else arg}\n" for cmd, arg in simulator.effects)
        with tempfile.TemporaryDirectory() as folder:
            binary = Path(folder) / "firmware"
            subprocess.run(["g++", "-std=c++11", "-Wall", "-Werror", "-o", str(binary),
                            str(ROOT / "tests" / "firmware" / "host_driver.cpp")], check=True)
            result = subprocess.run([str(binary)], input=stream, capture_output=True, timeout=10, check=True)
        self.assertEqual(result.stdout.decode().splitlines(), expected.decode().splitlines())
        self.assertEqual(result.stderr.decode(), effects)
        self.assertGreater(len(expected.splitlines()), 25)


if __name__ == "__main__":
    unittest.main()
