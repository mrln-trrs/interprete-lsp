// arduino/lsp_display_controller/lsp_display_controller.ino
// Controlador de pantalla / leds para el intérprete LSP

void setup() {
  Serial.begin(9600);
}

void loop() {
  if (Serial.available() > 0) {
    String msg = Serial.readStringUntil('\n');
    // Procesar mensaje recibido
  }
}
