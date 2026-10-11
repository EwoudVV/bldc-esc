#ifndef ESC_MEASUREMENTS_H
#define ESC_MEASUREMENTS_H
#include <stdbool.h>
#include <stdint.h>
#define ADC_REFERENCE_MV 2500U
#define ADC_FULL_SCALE 4095U
uint32_t adc_pin_mv(uint16_t raw);
uint32_t bus_mv(uint16_t raw);
int32_t phase_current_ma(uint16_t raw, uint16_t zero_raw);
bool diagnostic_wake_allowed(bool bus_ok, bool sample_valid, uint32_t measured_bus_mv);
#endif
