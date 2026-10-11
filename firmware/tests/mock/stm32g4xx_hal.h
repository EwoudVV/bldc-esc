#ifndef MOCK_HAL_H
#define MOCK_HAL_H
#include <stdint.h>
typedef struct { volatile uint32_t MODER,OTYPER,OSPEEDR,PUPDR,BSRR; } GPIO_TypeDef;
typedef struct { volatile uint32_t AHB2ENR,APB1ENR1; } RCC_TypeDef;
typedef struct { volatile uint32_t CR3; } PWR_TypeDef;
typedef struct { unsigned unused; } UART_HandleTypeDef;
typedef struct { unsigned unused; } SPI_HandleTypeDef;
typedef enum { HAL_OK=0,HAL_ERROR,HAL_BUSY,HAL_TIMEOUT } HAL_StatusTypeDef;
extern GPIO_TypeDef mock_a,mock_b,mock_c,mock_d,mock_e,mock_f;
extern RCC_TypeDef mock_rcc;
extern PWR_TypeDef mock_pwr;
GPIO_TypeDef *checked_gpioa(void);
#define GPIOA checked_gpioa()
#define GPIOB (&mock_b)
#define GPIOC (&mock_c)
#define GPIOD (&mock_d)
#define GPIOE (&mock_e)
#define GPIOF (&mock_f)
#define RCC (&mock_rcc)
#define PWR (&mock_pwr)
#define __DSB() ((void)0)
#define RCC_AHB2ENR_GPIOAEN (1U<<0)
#define RCC_AHB2ENR_GPIOBEN (1U<<1)
#define RCC_AHB2ENR_GPIOCEN (1U<<2)
#define RCC_AHB2ENR_GPIODEN (1U<<3)
#define RCC_AHB2ENR_GPIOEEN (1U<<4)
#define RCC_AHB2ENR_GPIOFEN (1U<<5)
#define RCC_APB1ENR1_PWREN (1U<<28)
#define PWR_CR3_UCPD_DBDIS (1U<<14)
#define GPIO_PIN_0 (1U << 0)
#define GPIO_PIN_1 (1U << 1)
#define GPIO_PIN_2 (1U << 2)
#define GPIO_PIN_3 (1U << 3)
#define GPIO_PIN_4 (1U << 4)
#define GPIO_PIN_5 (1U << 5)
#define GPIO_PIN_6 (1U << 6)
#define GPIO_PIN_7 (1U << 7)
#define GPIO_PIN_8 (1U << 8)
#define GPIO_PIN_9 (1U << 9)
#define GPIO_PIN_10 (1U << 10)
#define GPIO_PIN_11 (1U << 11)
#define GPIO_PIN_12 (1U << 12)
#define GPIO_PIN_13 (1U << 13)
#define GPIO_PIN_14 (1U << 14)
#define GPIO_PIN_15 (1U << 15)
HAL_StatusTypeDef HAL_UART_Transmit(UART_HandleTypeDef *,const uint8_t *,uint16_t,uint32_t);
HAL_StatusTypeDef HAL_UART_Receive(UART_HandleTypeDef *,uint8_t *,uint16_t,uint32_t);
void HAL_GPIO_TogglePin(GPIO_TypeDef *,uint16_t);
#endif
