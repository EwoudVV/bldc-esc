#ifndef ESC_COMMANDS_H
#define ESC_COMMANDS_H
#include <stddef.h>
typedef enum { CMD_EMPTY, CMD_HELP, CMD_STATUS, CMD_ADC, CMD_DRIVER, CMD_WAKE_ON, CMD_WAKE_OFF, CMD_UNKNOWN } command_t;
command_t command_parse(const char *line);
#endif
