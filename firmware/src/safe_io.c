#include "board.h"

static void raw_output(GPIO_TypeDef *port, uint32_t pins) {
    port->OTYPER &= ~pins;
    for (unsigned pin = 0; pin < 16; ++pin) {
        if (pins & (1U << pin)) {
            const uint32_t shift = pin * 2U;
            port->PUPDR &= ~(3U << shift);
            port->OSPEEDR &= ~(3U << shift);
            port->MODER = (port->MODER & ~(3U << shift)) | (1U << shift);
        }
    }
}

void board_early_safe(void) {
    RCC->AHB2ENR |= RCC_AHB2ENR_GPIOAEN | RCC_AHB2ENR_GPIOBEN | RCC_AHB2ENR_GPIOCEN |
                   RCC_AHB2ENR_GPIODEN | RCC_AHB2ENR_GPIOEEN | RCC_AHB2ENR_GPIOFEN;
    RCC->APB1ENR1 |= RCC_APB1ENR1_PWREN;
    (void)RCC->AHB2ENR;
    (void)RCC->APB1ENR1;
    /* PB4 is the fault input. Disable Rd before PA10 goes high. */
    PWR->CR3 |= PWR_CR3_UCPD_DBDIS;
    __DSB();
    GPIOE->BSRR = (PWM_PINS | ARM_PIN | DUMP_PIN | SENSOR_PIN |
                    STATUS_LED_PIN | COMM_LED_PIN) << 16;
    WAKE_PORT->BSRR = (uint32_t)WAKE_PIN << 16;
    ENCODER_PORT->BSRR = (uint32_t)ENCODER_PIN << 16;
    HEARTBEAT_PORT->BSRR = (uint32_t)HEARTBEAT_PIN << 16;
    CAN_STANDBY_PORT->BSRR = CAN_STANDBY_PIN;
    GPIOB->BSRR = DRIVER_CS_PIN | EEPROM_WP_PIN;
    raw_output(GPIOE, PWM_PINS | ARM_PIN | DUMP_PIN | SENSOR_PIN | STATUS_LED_PIN | COMM_LED_PIN);
    raw_output(WAKE_PORT, WAKE_PIN);
    raw_output(ENCODER_PORT, ENCODER_PIN);
    raw_output(HEARTBEAT_PORT, HEARTBEAT_PIN);
    raw_output(CAN_STANDBY_PORT, CAN_STANDBY_PIN);
    raw_output(GPIOB, DRIVER_CS_PIN | EEPROM_WP_PIN);
}
