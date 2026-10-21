// Compila el firmware real en el host: lee bytes de stdin, escribe respuestas en stdout y efectos en stderr.
#define LSP_HOST_TEST
#include "../../arduino/lsp_display_controller/lsp_display_controller.ino"

void sendReply(const char *text) {
  fputs(text, stdout);
}

void showEffect(char cmd, long arg) {
  fprintf(stderr, "%s %ld\n", cmd == 'G' ? "GLOSS" : "CLEAR", arg);
}

int main() {
  int value;
  while ((value = getchar()) != EOF) {
    feedByte((char)value);
  }
  return 0;
}
