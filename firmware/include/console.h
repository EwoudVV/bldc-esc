#ifndef ESC_CONSOLE_H
#define ESC_CONSOLE_H
#include <stdbool.h>
#include <stdint.h>
void console_write(const char *text);
void console_u32(uint32_t value);
void console_i32(int32_t value);
void console_hex16(uint16_t value);
bool console_poll(char *line, unsigned capacity);
#endif
