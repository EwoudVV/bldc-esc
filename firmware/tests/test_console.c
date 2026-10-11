#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <string.h>
#include "board.h"
#include "commands.h"
#include "console.h"
UART_HandleTypeDef console_uart;
GPIO_TypeDef mock_e;
static const char *input;
static unsigned remaining;
static unsigned force_off_calls;
static bool tx_failure;
void board_force_off(void) { ++force_off_calls; }
void HAL_GPIO_TogglePin(GPIO_TypeDef *port,uint16_t pin) { (void)port;(void)pin; }
HAL_StatusTypeDef HAL_UART_Transmit(UART_HandleTypeDef *u,const uint8_t *p,uint16_t n,uint32_t t) {
    (void)u;(void)p;(void)n;(void)t;return tx_failure ? HAL_ERROR : HAL_OK;
}
HAL_StatusTypeDef HAL_UART_Receive(UART_HandleTypeDef *u,uint8_t *p,uint16_t n,uint32_t t) {
    (void)u;(void)n;(void)t;if (!remaining) return HAL_TIMEOUT;
    *p=(uint8_t)*input++;--remaining;return HAL_OK;
}
static unsigned feed(const char *text,char *line,unsigned capacity,command_t expected) {
    input=text;remaining=(unsigned)strlen(text);unsigned commands=0;
    while (remaining) if (console_poll(line,capacity)) { assert(command_parse(line)==expected);++commands; }
    return commands;
}
int main(void) {
    char line[48];
    assert(feed("status\r\n",line,sizeof line,CMD_STATUS)==1);
    assert(feed("driver onn\b\r",line,sizeof line,CMD_WAKE_ON)==1);
    assert(feed("arm\n",line,sizeof line,CMD_UNKNOWN)==1);
    char overflow[160];memset(overflow,'x',sizeof overflow);memcpy(overflow,"driver on",9);overflow[158]='\n';overflow[159]=0;
    assert(feed(overflow,line,sizeof line,CMD_WAKE_ON)==0);
    assert(feed("driver off\n",line,sizeof line,CMD_WAKE_OFF)==1);
    tx_failure=true;console_write("test");assert(force_off_calls==1);
    return 0;
}
