#include "board.h"
#include "measurements.h"

UART_HandleTypeDef console_uart;
SPI_HandleTypeDef driver_spi;
static ADC_HandleTypeDef converters[5];
static bool adc_ready[5];
static bool driver_awake;

analog_sample_t analog_samples[] = {
    {"bus",       1, ADC_CHANNEL_1,  0, false},
    {"phase_a",   1, ADC_CHANNEL_3,  0, false},
    {"phase_b",   1, ADC_CHANNEL_4,  0, false},
    {"phase_c",   2, ADC_CHANNEL_6,  0, false},
    {"current_a", 1, ADC_CHANNEL_2,  0, false},
    {"current_b", 2, ADC_CHANNEL_4,  0, false},
    {"current_c", 3, ADC_CHANNEL_12, 0, false},
    {"drv_a",     3, ADC_CHANNEL_1,  0, false},
    {"drv_b",     2, ADC_CHANNEL_11, 0, false},
    {"drv_c",     2, ADC_CHANNEL_12, 0, false},
    {"dump_i",    2, ADC_CHANNEL_3,  0, false},
    {"rail_3v3",  2, ADC_CHANNEL_5,  0, false},
    {"throttle",  1, ADC_CHANNEL_8,  0, false},
    {"aux",       1, ADC_CHANNEL_9,  0, false},
    {"ntc_dump",  3, ADC_CHANNEL_4,  0, false},
    {"ntc_bridge",4, ADC_CHANNEL_12, 0, false},
    {"ntc_pcb",   4, ADC_CHANNEL_13, 0, false},
    {"ntc_motor", 5, ADC_CHANNEL_7,  0, false}
};
const size_t analog_sample_count = sizeof analog_samples / sizeof analog_samples[0];


void board_force_off(void) {
    PWM_PORT->BSRR = (uint32_t)PWM_PINS << 16;
    ARM_PORT->BSRR = (uint32_t)ARM_PIN << 16;
    DUMP_PORT->BSRR = (uint32_t)DUMP_PIN << 16;
    WAKE_PORT->BSRR = (uint32_t)WAKE_PIN << 16;
    SENSOR_PORT->BSRR = (uint32_t)SENSOR_PIN << 16;
    ENCODER_PORT->BSRR = (uint32_t)ENCODER_PIN << 16;
    driver_awake = false;
}

void board_panic(void) {
    __disable_irq();
    board_early_safe();
    for (;;) __NOP();
}

static void gpio(GPIO_TypeDef *port, uint32_t pins, uint32_t mode, uint32_t alternate) {
    GPIO_InitTypeDef init = {0};
    init.Pin = pins; init.Mode = mode; init.Pull = GPIO_NOPULL;
    init.Speed = GPIO_SPEED_FREQ_LOW; init.Alternate = alternate;
    HAL_GPIO_Init(port, &init);
}

static bool clock_init(void) {
    RCC_OscInitTypeDef oscillator = {0};
    oscillator.OscillatorType = RCC_OSCILLATORTYPE_HSI;
    oscillator.HSIState = RCC_HSI_ON;
    oscillator.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
    oscillator.PLL.PLLState = RCC_PLL_NONE;
    if (HAL_RCC_OscConfig(&oscillator) != HAL_OK) return false;
    RCC_ClkInitTypeDef clock = {0};
    clock.ClockType = RCC_CLOCKTYPE_SYSCLK | RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    clock.SYSCLKSource = RCC_SYSCLKSOURCE_HSI;
    clock.AHBCLKDivider = RCC_SYSCLK_DIV1;
    clock.APB1CLKDivider = RCC_HCLK_DIV1;
    clock.APB2CLKDivider = RCC_HCLK_DIV1;
    if (HAL_RCC_ClockConfig(&clock, FLASH_LATENCY_0) != HAL_OK) return false;
    RCC_PeriphCLKInitTypeDef peripheral = {0};
    peripheral.PeriphClockSelection = RCC_PERIPHCLK_ADC12 | RCC_PERIPHCLK_ADC345 | RCC_PERIPHCLK_USART3;
    peripheral.Adc12ClockSelection = RCC_ADC12CLKSOURCE_SYSCLK;
    peripheral.Adc345ClockSelection = RCC_ADC345CLKSOURCE_SYSCLK;
    peripheral.Usart3ClockSelection = RCC_USART3CLKSOURCE_PCLK1;
    return HAL_RCCEx_PeriphCLKConfig(&peripheral) == HAL_OK;
}

static void adc_init(void) {
    __HAL_RCC_ADC12_CLK_ENABLE();
    __HAL_RCC_ADC345_CLK_ENABLE();
    ADC_TypeDef *instances[] = {ADC1, ADC2, ADC3, ADC4, ADC5};
    for (unsigned i = 0; i < 5; ++i) {
        ADC_HandleTypeDef *adc = &converters[i];
        adc->Instance = instances[i];
        adc->Init.ClockPrescaler = ADC_CLOCK_ASYNC_DIV4;
        adc->Init.Resolution = ADC_RESOLUTION_12B;
        adc->Init.DataAlign = ADC_DATAALIGN_RIGHT;
        adc->Init.GainCompensation = 0;
        adc->Init.ScanConvMode = ADC_SCAN_DISABLE;
        adc->Init.EOCSelection = ADC_EOC_SINGLE_CONV;
        adc->Init.LowPowerAutoWait = DISABLE;
        adc->Init.ContinuousConvMode = DISABLE;
        adc->Init.NbrOfConversion = 1;
        adc->Init.DiscontinuousConvMode = DISABLE;
        adc->Init.ExternalTrigConv = ADC_SOFTWARE_START;
        adc->Init.ExternalTrigConvEdge = ADC_EXTERNALTRIGCONVEDGE_NONE;
        adc->Init.DMAContinuousRequests = DISABLE;
        adc->Init.Overrun = ADC_OVR_DATA_OVERWRITTEN;
        adc->Init.OversamplingMode = DISABLE;
        adc_ready[i] = HAL_ADC_Init(adc) == HAL_OK;
        if (adc_ready[i]) adc_ready[i] = HAL_ADCEx_Calibration_Start(adc, ADC_SINGLE_ENDED) == HAL_OK;
    }
}

bool board_init(void) {
    board_early_safe();
    SystemCoreClockUpdate();
    if (HAL_Init() != HAL_OK) return false;
    __enable_irq();
    if (!clock_init()) return false;
    /* An external 2.5 V reference drives VREF+. Leave the internal buffer off. */
    __HAL_RCC_SYSCFG_CLK_ENABLE();
    VREFBUF->CSR &= ~VREFBUF_CSR_ENVR;
    VREFBUF->CSR |= VREFBUF_CSR_HIZ;
    gpio(GPIOA, GPIO_PIN_0 | GPIO_PIN_1 | GPIO_PIN_2 | GPIO_PIN_3 | GPIO_PIN_4 |
                GPIO_PIN_5 | GPIO_PIN_6 | GPIO_PIN_7, GPIO_MODE_ANALOG, 0);
    gpio(GPIOB, GPIO_PIN_0 | GPIO_PIN_1 | GPIO_PIN_2, GPIO_MODE_ANALOG, 0);
    gpio(GPIOC, GPIO_PIN_0 | GPIO_PIN_1 | GPIO_PIN_2 | GPIO_PIN_3 | GPIO_PIN_4 | GPIO_PIN_5, GPIO_MODE_ANALOG, 0);
    gpio(GPIOD, GPIO_PIN_8 | GPIO_PIN_9 | GPIO_PIN_10 | GPIO_PIN_12, GPIO_MODE_ANALOG, 0);
    gpio(GPIOE, GPIO_PIN_7, GPIO_MODE_ANALOG, 0);
    gpio(GPIOA, GPIO_PIN_8 | GPIO_PIN_9, GPIO_MODE_INPUT, 0);
    gpio(GPIOB, GPIO_PIN_4 | GPIO_PIN_5 | GPIO_PIN_10, GPIO_MODE_INPUT, 0);
    gpio(GPIOC, GPIO_PIN_6 | GPIO_PIN_7 | GPIO_PIN_8 | GPIO_PIN_9 | GPIO_PIN_13, GPIO_MODE_INPUT, 0);
    gpio(GPIOD, GPIO_PIN_3 | GPIO_PIN_4 | GPIO_PIN_7 | GPIO_PIN_11 | GPIO_PIN_13 |
                GPIO_PIN_14 | GPIO_PIN_15, GPIO_MODE_INPUT, 0);
    gpio(GPIOE, GPIO_PIN_5 | GPIO_PIN_6 | GPIO_PIN_15, GPIO_MODE_INPUT, 0);
    gpio(GPIOF, GPIO_PIN_2 | GPIO_PIN_10, GPIO_MODE_INPUT, 0);
    __HAL_RCC_USART3_CLK_ENABLE();
    gpio(GPIOC, GPIO_PIN_10 | GPIO_PIN_11, GPIO_MODE_AF_PP, GPIO_AF7_USART3);
    console_uart.Instance = USART3;
    console_uart.Init.BaudRate = 115200;
    console_uart.Init.WordLength = UART_WORDLENGTH_8B;
    console_uart.Init.StopBits = UART_STOPBITS_1;
    console_uart.Init.Parity = UART_PARITY_NONE;
    console_uart.Init.Mode = UART_MODE_TX_RX;
    console_uart.Init.HwFlowCtl = UART_HWCONTROL_NONE;
    console_uart.Init.OverSampling = UART_OVERSAMPLING_16;
    console_uart.Init.OneBitSampling = UART_ONE_BIT_SAMPLE_DISABLE;
    console_uart.Init.ClockPrescaler = UART_PRESCALER_DIV1;
    console_uart.AdvancedInit.AdvFeatureInit = UART_ADVFEATURE_NO_INIT;
    if (HAL_UART_Init(&console_uart) != HAL_OK) return false;
    __HAL_RCC_SPI2_CLK_ENABLE();
    gpio(GPIOB, GPIO_PIN_13 | GPIO_PIN_14 | GPIO_PIN_15, GPIO_MODE_AF_PP, GPIO_AF5_SPI2);
    driver_spi.Instance = SPI2;
    driver_spi.Init.Mode = SPI_MODE_MASTER;
    driver_spi.Init.Direction = SPI_DIRECTION_2LINES;
    driver_spi.Init.DataSize = SPI_DATASIZE_16BIT;
    driver_spi.Init.CLKPolarity = SPI_POLARITY_LOW;
    driver_spi.Init.CLKPhase = SPI_PHASE_2EDGE;
    driver_spi.Init.NSS = SPI_NSS_SOFT;
    driver_spi.Init.BaudRatePrescaler = SPI_BAUDRATEPRESCALER_32;
    driver_spi.Init.FirstBit = SPI_FIRSTBIT_MSB;
    driver_spi.Init.TIMode = SPI_TIMODE_DISABLE;
    driver_spi.Init.CRCCalculation = SPI_CRCCALCULATION_DISABLE;
    driver_spi.Init.CRCPolynomial = 7;
    driver_spi.Init.CRCLength = SPI_CRC_LENGTH_DATASIZE;
    driver_spi.Init.NSSPMode = SPI_NSS_PULSE_DISABLE;
    if (HAL_SPI_Init(&driver_spi) != HAL_OK) return false;
    adc_init();
    board_force_off();
    return true;
}

void board_sample_analog(void) {
    for (size_t i = 0; i < analog_sample_count; ++i) {
        analog_sample_t *sample = &analog_samples[i];
        ADC_HandleTypeDef *adc = &converters[sample->converter - 1U];
        sample->valid = false;
        if (!adc_ready[sample->converter - 1U]) continue;
        ADC_ChannelConfTypeDef channel = {0};
        channel.Channel = sample->channel; channel.Rank = ADC_REGULAR_RANK_1;
        channel.SamplingTime = ADC_SAMPLETIME_247CYCLES_5;
        channel.SingleDiff = ADC_SINGLE_ENDED;
        channel.OffsetNumber = ADC_OFFSET_NONE; channel.Offset = 0;
        if (HAL_ADC_ConfigChannel(adc, &channel) != HAL_OK) continue;
        if (HAL_ADC_Start(adc) != HAL_OK) continue;
        if (HAL_ADC_PollForConversion(adc, 5) == HAL_OK) {
            sample->raw = (uint16_t)HAL_ADC_GetValue(adc);
            sample->valid = true;
        }
        (void)HAL_ADC_Stop(adc);
    }
    /* A diagnostic wake never overrides a lost or out-of-range bus reading. */
    if (driver_awake && !diagnostic_wake_allowed(
        HAL_GPIO_ReadPin(GPIOC, GPIO_PIN_9) == GPIO_PIN_SET,
        analog_samples[0].valid, bus_mv(analog_samples[0].raw))) board_force_off();
}

bool board_driver_wake(bool enabled) {
    board_force_off();
    if (!enabled) return true;
    board_sample_analog();
    if (!diagnostic_wake_allowed(HAL_GPIO_ReadPin(GPIOC, GPIO_PIN_9) == GPIO_PIN_SET,
        analog_samples[0].valid, bus_mv(analog_samples[0].raw))) return false;
    /* Wake only the driver. ARM, all six PWM pins and DUMP_PWM remain low. */
    HAL_GPIO_WritePin(WAKE_PORT, WAKE_PIN, GPIO_PIN_SET);
    HAL_Delay(5);
    driver_awake = true;
    return true;
}

bool board_driver_read(uint8_t address, uint16_t *value) {
    if (!driver_awake || !value || address > 7U) return false;
    const uint16_t tx = (uint16_t)(0x8000U | ((uint16_t)address << 11));
    uint16_t rx = 0;
    HAL_GPIO_WritePin(DRIVER_CS_PORT, DRIVER_CS_PIN, GPIO_PIN_RESET);
    __DSB();
    HAL_StatusTypeDef result = HAL_SPI_TransmitReceive(&driver_spi, (uint8_t *)&tx, (uint8_t *)&rx, 1, 5);
    HAL_GPIO_WritePin(DRIVER_CS_PORT, DRIVER_CS_PIN, GPIO_PIN_SET);
    HAL_Delay(1);
    *value = rx & 0x07ffU;
    return result == HAL_OK;
}

uint32_t board_status_bits(void) {
    uint32_t result = 0;
    struct { GPIO_TypeDef *port; uint16_t pin; } inputs[] = {
        {GPIOB,GPIO_PIN_4}, {GPIOC,GPIO_PIN_9}, {GPIOA,GPIO_PIN_8},
        {GPIOE,GPIO_PIN_15}, {GPIOB,GPIO_PIN_10}, {GPIOB,GPIO_PIN_5},
        {GPIOE,GPIO_PIN_6}, {GPIOD,GPIO_PIN_11}, {GPIOE,GPIO_PIN_5},
        {GPIOF,GPIO_PIN_10}, {GPIOF,GPIO_PIN_2}, {GPIOA,GPIO_PIN_9},
        {GPIOC,GPIO_PIN_6}, {GPIOC,GPIO_PIN_7}, {GPIOC,GPIO_PIN_8},
        {GPIOD,GPIO_PIN_3}, {GPIOD,GPIO_PIN_4}, {GPIOD,GPIO_PIN_7},
        {GPIOD,GPIO_PIN_13}, {GPIOD,GPIO_PIN_14}, {GPIOD,GPIO_PIN_15}, {GPIOC,GPIO_PIN_13}
    };
    for (unsigned i = 0; i < sizeof inputs / sizeof inputs[0]; ++i)
        if (HAL_GPIO_ReadPin(inputs[i].port, inputs[i].pin) == GPIO_PIN_SET) result |= 1U << i;
    return result;
}
void board_heartbeat(void) { HAL_GPIO_TogglePin(HEARTBEAT_PORT, HEARTBEAT_PIN); }
void board_led_tick(void) { HAL_GPIO_TogglePin(STATUS_LED_PORT, STATUS_LED_PIN); }
