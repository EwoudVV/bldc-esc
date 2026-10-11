#include "measurements.h"
uint32_t adc_pin_mv(uint16_t raw) {
    return ((uint32_t)raw * ADC_REFERENCE_MV + ADC_FULL_SCALE / 2U) / ADC_FULL_SCALE;
}
uint32_t bus_mv(uint16_t raw) {
    return ((uint32_t)raw * ADC_REFERENCE_MV * 21U + ADC_FULL_SCALE / 2U) / ADC_FULL_SCALE;
}
int32_t phase_current_ma(uint16_t raw, uint16_t zero_raw) {
    /* INA241A2 gain 20, 1 milliohm shunt. Zero offset must be measured. */
    return ((int32_t)raw - zero_raw) * (int32_t)ADC_REFERENCE_MV * 50 / (int32_t)ADC_FULL_SCALE;
}
bool diagnostic_wake_allowed(bool bus_ok, bool sample_valid, uint32_t measured_bus_mv) {
    return bus_ok && sample_valid && measured_bus_mv >= 12000U && measured_bus_mv <= 30000U;
}
