#include "commands.h"
static int equal(const char *a, const char *b) {
    while (*a && *a == *b) { ++a; ++b; }
    return *a == *b;
}
command_t command_parse(const char *line) {
    if (!line || !*line) return CMD_EMPTY;
    if (equal(line, "help")) return CMD_HELP;
    if (equal(line, "status")) return CMD_STATUS;
    if (equal(line, "adc")) return CMD_ADC;
    if (equal(line, "driver")) return CMD_DRIVER;
    if (equal(line, "driver on")) return CMD_WAKE_ON;
    if (equal(line, "driver off")) return CMD_WAKE_OFF;
    return CMD_UNKNOWN;
}
