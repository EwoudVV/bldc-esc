#ifndef ESC_BOARD_H
#define ESC_BOARD_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include "stm32g4xx_hal.h"

#define PWM_PORT GPIOE
#define PWM_PINS (GPIO_PIN_8 | GPIO_PIN_9 | GPIO_PIN_10 | GPIO_PIN_11 | GPIO_PIN_12 | GPIO_PIN_13)
#define ARM_PORT GPIOE
#define ARM_PIN GPIO_PIN_1
#define DUMP_PORT GPIOE
#define DUMP_PIN GPIO_PIN_0
#define WAKE_PORT GPIOC
#define WAKE_PIN GPIO_PIN_12
#define SENSOR_PORT GPIOE
#define SENSOR_PIN GPIO_PIN_4
#define ENCODER_PORT GPIOF
#define ENCODER_PIN GPIO_PIN_9
#define HEARTBEAT_PORT GPIOD
#define HEARTBEAT_PIN GPIO_PIN_2
#define DRIVER_CS_PORT GPIOB
#define DRIVER_CS_PIN GPIO_PIN_12
#define CAN_STANDBY_PORT GPIOA
#define CAN_STANDBY_PIN GPIO_PIN_10
#define EEPROM_WP_PORT GPIOB
#define EEPROM_WP_PIN GPIO_PIN_7
#define STATUS_LED_PORT GPIOE
#define STATUS_LED_PIN GPIO_PIN_2
#define COMM_LED_PORT GPIOE
#define COMM_LED_PIN GPIO_PIN_3

extern UART_HandleTypeDef console_uart;
extern SPI_HandleTypeDef driver_spi;
void board_early_safe(void);
void board_force_off(void);
bool board_init(void);
bool board_driver_wake(bool enabled);
bool board_driver_read(uint8_t address, uint16_t *value);
uint32_t board_status_bits(void);
void board_heartbeat(void);
void board_led_tick(void);
void board_panic(void) __attribute__((noreturn));

typedef struct {
    const char *name;
    uint8_t converter;
    uint32_t channel;
    uint16_t raw;
    bool valid;
} analog_sample_t;
extern analog_sample_t analog_samples[];
extern const size_t analog_sample_count;
void board_sample_analog(void);
#endif
