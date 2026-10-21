"""
src/hardware/serial_controller.py
Controlador de comunicación serial con microcontrolador Arduino vía PySerial.

Protocolo V1 (docs/hardware/SERIAL-PROTOCOL.md): trama ASCII `V1|SEQ|CMD|ARG\n` de hasta 64 bytes.
El host nunca bloquea la captura: guarda solo la salida más reciente y la envía desde un hilo propio.
"""
import threading
import time

from config.actions import ACTIONS

VERSION = "V1"
MAX_FRAME_BYTES = 64          # Incluye el LF final
MAX_SEQ = 65535
GLOSS_IDS = range(len(ACTIONS))  # V1 solo transmite el vocabulario base versionado (0–8)
COMMANDS = ("PING", "GLOSS", "CLEAR")
ERROR_CODES = ("FORMAT", "VERSION", "RANGE", "COMMAND", "BUSY")


class ProtocolError(ValueError):
    def __init__(self, code, seq=None):
        super().__init__(code)
        self.code, self.seq = code, seq


def encode_frame(seq, command, arg=None):
    if type(seq) is not int or not 0 <= seq <= MAX_SEQ:
        raise ValueError("SEQ fuera de rango")
    if command == "GLOSS":
        if type(arg) is not int or arg not in GLOSS_IDS:
            raise ValueError("Glosa fuera del vocabulario V1")
        value = str(arg)
    elif command in ("PING", "CLEAR") and arg is None:
        value = "-"
    else:
        raise ValueError("Comando o argumento inválido")
    return f"{VERSION}|{seq}|{command}|{value}\n".encode("ascii")


def _decimal(text, limit, seq=None):
    if not text.isdigit() or len(text) > 5:
        raise ProtocolError("FORMAT", seq)
    value = int(text)
    if value > limit:
        raise ProtocolError("RANGE", seq)
    return value


def parse_frame(line):
    """Valida una trama completa (con LF) y devuelve (seq, cmd, arg); arg es int en GLOSS y None si no."""
    if len(line) > MAX_FRAME_BYTES or not line.endswith(b"\n") or any(b < 0x20 or b > 0x7E for b in line[:-1]):
        raise ProtocolError("FORMAT")
    fields = line[:-1].decode("ascii").split("|")
    if len(fields) != 4:
        raise ProtocolError("FORMAT")
    version, seq_text, command, arg = fields
    hint = int(seq_text) if seq_text.isdigit() and len(seq_text) <= 5 and int(seq_text) <= MAX_SEQ else None
    if version != VERSION:
        raise ProtocolError("VERSION", hint)
    seq = _decimal(seq_text, MAX_SEQ)
    if command not in COMMANDS:
        raise ProtocolError("COMMAND", seq)
    if command == "GLOSS":
        return seq, command, _decimal(arg, GLOSS_IDS[-1], seq)
    if arg != "-":
        raise ProtocolError("FORMAT", seq)
    return seq, command, None


def parse_reply(line):
    """Respuesta del firmware: (seq|None, 'ACK'|'ERR', code|None)."""
    parts = line.rstrip(b"\n").decode("ascii", "replace").split("|")
    if len(parts) != 4 or parts[0] != VERSION or parts[2] not in ("ACK", "ERR"):
        raise ProtocolError("FORMAT")
    seq = int(parts[1]) if parts[1].isdigit() else None
    if parts[2] == "ACK":
        return seq, "ACK", None
    if parts[3] not in ERROR_CODES:
        raise ProtocolError("FORMAT")
    return seq, "ERR", parts[3]


class FirmwareSimulator:
    """Referencia ejecutable del firmware (.ino): misma máquina de estados para pruebas de loopback."""

    def __init__(self):
        self.buffer, self.overflow = bytearray(), False
        self.last = None  # (seq, cmd, arg) de la última trama válida
        self.effects = []

    def feed(self, data):
        replies = []
        for byte in data:
            if self.overflow:
                if byte == 0x0A:
                    self.overflow = False
                    replies.append(b"V1|-|ERR|FORMAT\n")
                continue
            self.buffer.append(byte)
            if byte == 0x0A:
                replies.append(self.handle(bytes(self.buffer)))
                self.buffer.clear()
            elif len(self.buffer) >= MAX_FRAME_BYTES:
                self.buffer.clear()
                self.overflow = True  # Descarta hasta el próximo LF sin crecer en memoria
        return replies

    def handle(self, line):
        try:
            seq, command, arg = parse_frame(line)
        except ProtocolError as error:
            return f"V1|{'-' if error.seq is None else error.seq}|ERR|{error.code}\n".encode("ascii")
        if command == "PING":
            self.last = (seq, command, arg)  # Handshake: reinicia la deduplicación
            return f"V1|{seq}|ACK|-\n".encode("ascii")
        if self.last is not None and self.last[0] == seq:
            if self.last != (seq, command, arg):
                return f"V1|{seq}|ERR|FORMAT\n".encode("ascii")
            return f"V1|{seq}|ACK|-\n".encode("ascii")  # Repetida: ACK sin repetir efecto
        self.last = (seq, command, arg)
        self.effects.append((command, arg))
        return f"V1|{seq}|ACK|-\n".encode("ascii")


class SerialController:
    """Envía glosas validadas sin bloquear la captura; degrada a Partial ante fallas y conserva el texto."""

    def __init__(self, port=None, baudrate=9600, timeout=0.2, transport_factory=None):
        self.port, self.baudrate, self.timeout = port, baudrate, timeout
        self.transport_factory = transport_factory or self._pyserial
        self.transport = None
        self.state = "Disabled"
        self.last_error = None
        self.seq = 0
        self._pending = None
        self._condition = threading.Condition()
        self._worker = None
        self._running = False

    def _pyserial(self):
        import serial  # pyserial; import tardío para que el hardware siga siendo opcional
        return serial.Serial(self.port, self.baudrate, timeout=self.timeout, write_timeout=self.timeout)

    def _next_seq(self):
        self.seq = (self.seq + 1) % (MAX_SEQ + 1)
        return self.seq

    def _degrade(self, reason):
        self.state, self.last_error = "Partial", reason
        transport, self.transport = self.transport, None
        if transport is not None:
            try:
                transport.close()
            except OSError:
                pass

    def _exchange(self, frame, seq):
        """Escribe y espera ACK; un reintento solo tras timeout (el firmware deduplica por SEQ)."""
        for _ in range(2):
            self.transport.write(frame)
            line = self.transport.readline()
            if not line:
                continue
            reply_seq, kind, code = parse_reply(line)
            if reply_seq != seq:
                raise ProtocolError("FORMAT")
            if kind == "ERR":
                raise ProtocolError(code, seq)
            return True
        raise TimeoutError("Sin ACK del dispositivo")

    def connect(self):
        """Abre el puerto y hace handshake PING; no reproduce salidas antiguas."""
        with self._condition:
            self._pending = None
        try:
            self.transport = self.transport_factory()
            self.seq = 0
            self._exchange(encode_frame(0, "PING"), 0)
        except Exception as error:  # Cualquier falla de puerto o handshake deja el sistema funcionando sin hardware
            self._degrade(getattr(error, "code", type(error).__name__))
            return False
        self.state, self.last_error = "Success", None
        return True

    def reconnect(self, attempts=3, backoff=0.5):
        for attempt in range(attempts):  # Acotado: nunca un bucle infinito
            if self.connect():
                return True
            time.sleep(backoff * (2 ** attempt))
        return False

    def submit(self, class_id=None):
        """Encola la salida más reciente (None = CLEAR); reemplaza la anterior si aún no salió."""
        if class_id is not None and (type(class_id) is not int or class_id not in GLOSS_IDS):
            return False  # Clases extendidas (números, letras, meses) quedan fuera de V1
        with self._condition:
            self._pending = ("GLOSS", class_id) if class_id is not None else ("CLEAR", None)
            self._condition.notify()
        return True

    def process_pending(self):
        with self._condition:
            item, self._pending = self._pending, None
        if item is None or self.state != "Success":
            return False
        seq = self._next_seq()
        try:
            return self._exchange(encode_frame(seq, *item), seq)
        except Exception as error:
            self._degrade(getattr(error, "code", type(error).__name__))
            return False

    def start(self):
        self._running = True
        self._worker = threading.Thread(target=self._loop, name="lsp-serial", daemon=True)
        self._worker.start()

    def _loop(self):
        while self._running:
            with self._condition:
                while self._running and self._pending is None:
                    self._condition.wait(0.5)
            if self._running:
                self.process_pending()

    def close(self):
        self._running = False
        with self._condition:
            self._condition.notify()
        if self._worker is not None:
            self._worker.join(timeout=1)
            self._worker = None
        if self.transport is not None:
            self.transport.close()
            self.transport = None
        self.state = "Disabled"
