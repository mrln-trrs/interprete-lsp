// arduino/lsp_display_controller/lsp_display_controller.ino
// Controlador de pantalla / leds para el intérprete LSP
// Protocolo V1 (docs/hardware/SERIAL-PROTOCOL.md): `V1|SEQ|CMD|ARG\n`, máximo 64 bytes con LF.
// Respuesta `V1|SEQ|ACK|-` o `V1|SEQ|ERR|CODE`. Sin String dinámico: buffer fijo, sin fragmentar memoria.
// La misma lógica se compila en el host (LSP_HOST_TEST) y se compara con FirmwareSimulator.

#include <stdint.h>
#include <stdio.h>
#include <string.h>

const uint8_t MAX_FRAME = 64;    // Incluye LF
const long MAX_SEQ = 65535;
const long GLOSS_MAX = 8;        // Vocabulario base V1: IDs 0–8

char lineBuf[MAX_FRAME];
uint8_t lineLen = 0;
bool overflow = false;

bool hasLast = false;            // Última trama válida, para deduplicar por SEQ
long lastSeq = 0;
char lastCmd = 0;                // 'P' PING, 'G' GLOSS, 'C' CLEAR
long lastArg = -1;
long currentGloss = -1;          // Indicador mostrado; -1 = vacío

void sendReply(const char *text);
void showEffect(char cmd, long arg);

void reply(long seq, const char *kind, const char *code) {
  char out[32];
  if (seq < 0) {
    snprintf(out, sizeof(out), "V1|-|%s|%s\n", kind, code);
  } else {
    snprintf(out, sizeof(out), "V1|%ld|%s|%s\n", seq, kind, code);
  }
  sendReply(out);
}

// 0 = válido, 1 = FORMAT, 2 = RANGE
uint8_t parseDecimal(const char *text, uint8_t length, long limit, long *value) {
  if (length == 0 || length > 5) return 1;
  long result = 0;
  for (uint8_t i = 0; i < length; i++) {
    if (text[i] < '0' || text[i] > '9') return 1;
    result = result * 10 + (text[i] - '0');
  }
  if (result > limit) return 2;
  *value = result;
  return 0;
}

bool fieldIs(const char *field, uint8_t length, const char *expected) {
  return length == strlen(expected) && strncmp(field, expected, length) == 0;
}

void handleLine(const char *line, uint8_t length) {  // length sin LF
  uint8_t starts[4], lengths[4], count = 0, start = 0;
  for (uint8_t i = 0; i < length; i++) {
    if (line[i] < 0x20 || line[i] > 0x7E) { reply(-1, "ERR", "FORMAT"); return; }
  }
  for (uint8_t i = 0; i <= length; i++) {
    if (i == length || line[i] == '|') {
      if (count == 4) { reply(-1, "ERR", "FORMAT"); return; }
      starts[count] = start;
      lengths[count] = i - start;
      count++;
      start = i + 1;
    }
  }
  if (count != 4) { reply(-1, "ERR", "FORMAT"); return; }

  long seq = -1, hint = -1, arg = -1;
  parseDecimal(line + starts[1], lengths[1], MAX_SEQ, &hint);
  if (!fieldIs(line + starts[0], lengths[0], "V1")) { reply(hint, "ERR", "VERSION"); return; }
  uint8_t status = parseDecimal(line + starts[1], lengths[1], MAX_SEQ, &seq);
  if (status) { reply(-1, "ERR", status == 1 ? "FORMAT" : "RANGE"); return; }

  const char *command = line + starts[2];
  const char *argument = line + starts[3];
  char cmd;
  if (fieldIs(command, lengths[2], "PING")) cmd = 'P';
  else if (fieldIs(command, lengths[2], "GLOSS")) cmd = 'G';
  else if (fieldIs(command, lengths[2], "CLEAR")) cmd = 'C';
  else { reply(seq, "ERR", "COMMAND"); return; }

  if (cmd == 'G') {
    status = parseDecimal(argument, lengths[3], GLOSS_MAX, &arg);
    if (status) { reply(seq, "ERR", status == 1 ? "FORMAT" : "RANGE"); return; }
  } else if (!fieldIs(argument, lengths[3], "-")) {
    reply(seq, "ERR", "FORMAT");
    return;
  }

  if (cmd == 'P') {  // Handshake: reinicia la deduplicación
    hasLast = true; lastSeq = seq; lastCmd = cmd; lastArg = arg;
    reply(seq, "ACK", "-");
    return;
  }
  if (hasLast && lastSeq == seq) {
    // Misma SEQ: ACK sin repetir efecto si el contenido coincide; si no, error
    reply(seq, lastCmd == cmd && lastArg == arg ? "ACK" : "ERR", lastCmd == cmd && lastArg == arg ? "-" : "FORMAT");
    return;
  }
  hasLast = true; lastSeq = seq; lastCmd = cmd; lastArg = arg;
  currentGloss = cmd == 'G' ? arg : -1;
  showEffect(cmd, arg);
  reply(seq, "ACK", "-");
}

void feedByte(char byte) {
  if (overflow) {  // Descarta hasta el próximo LF sin crecer en memoria
    if (byte == '\n') { overflow = false; reply(-1, "ERR", "FORMAT"); }
    return;
  }
  lineBuf[lineLen++] = byte;
  if (byte == '\n') {
    handleLine(lineBuf, lineLen - 1);
    lineLen = 0;
  } else if (lineLen >= MAX_FRAME) {
    lineLen = 0;
    overflow = true;
  }
}

#ifndef LSP_HOST_TEST
void sendReply(const char *text) {
  Serial.print(text);
}

void showEffect(char cmd, long arg) {
  // Placa y pantalla aún sin elegir: el LED integrado indica que hay una glosa vigente.
  (void)arg;  // El ID queda en currentGloss para la pantalla futura
  digitalWrite(LED_BUILTIN, cmd == 'G' ? HIGH : LOW);
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
  Serial.begin(9600);
}

void loop() {
  while (Serial.available() > 0) {
    feedByte((char)Serial.read());
  }
}
#endif
