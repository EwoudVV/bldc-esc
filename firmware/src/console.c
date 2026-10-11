#include "console.h"
#include "board.h"
static unsigned used;
static bool discard_line;
static bool previous_cr;
void console_write(const char *text) {
    unsigned length = 0;
    while (text[length]) ++length;
    if (length && HAL_UART_Transmit(&console_uart, (const uint8_t *)text, (uint16_t)length, 50) != HAL_OK)
        board_force_off();
}
void console_u32(uint32_t value) {
    char digits[11]; unsigned end = sizeof digits - 1; digits[end] = 0;
    do { digits[--end] = (char)('0' + value % 10U); value /= 10U; } while (value);
    console_write(&digits[end]);
}
void console_i32(int32_t value) {
    if (value < 0) { console_write("-"); console_u32((uint32_t)(-(int64_t)value)); }
    else console_u32((uint32_t)value);
}
void console_hex16(uint16_t value) {
    static const char alphabet[] = "0123456789ABCDEF";
    char digits[7] = "0x0000";
    for (unsigned i = 0; i < 4; ++i) digits[5 - i] = alphabet[(value >> (4 * i)) & 15U];
    console_write(digits);
}
bool console_poll(char *line, unsigned capacity) {
    uint8_t byte;
    if (!capacity || HAL_UART_Receive(&console_uart, &byte, 1, 0) != HAL_OK) return false;
    HAL_GPIO_TogglePin(COMM_LED_PORT, COMM_LED_PIN);
    if (previous_cr && byte == '\n') { previous_cr = false; return false; }
    previous_cr = byte == '\r';
    if (byte == '\r' || byte == '\n') {
        console_write("\r\n");
        if (discard_line) { used = 0; discard_line = false; console_write("line too long\r\nesc> "); return false; }
        line[used] = 0; used = 0; return true;
    }
    if (discard_line) return false;
    if (byte == 8 || byte == 127) {
        if (used) { --used; console_write("\b \b"); }
        return false;
    }
    if (byte < 32 || byte > 126) return false;
    if (used + 1 >= capacity) { discard_line = true; return false; }
    line[used++] = (char)byte;
    char echo[2] = {(char)byte, 0}; console_write(echo);
    return false;
}
