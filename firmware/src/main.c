#include "board.h"
#include "commands.h"
#include "console.h"
#include "measurements.h"

static void print_help(void) {
    console_write("help | status | adc | driver | driver on | driver off\r\n"
                  "motor drive is disabled in this build. driver on wakes SPI only.\r\n"
                  "sensor power stays off. UART: 115200 8N1, 3.3 V logic.\r\n");
}
static void print_status(void) {
    static const char *names[] = {"drv_nfault", "bus_ok", "noc_hw", "nfault_latch", "nhw_enable",
        "wd_run", "brake_fault", "dump_active", "sensor_nfault", "encoder_nfault", "bus_selected",
        "usb_present", "hall1", "hall2", "hall3", "enc_a", "enc_b", "enc_z", "nbrake", "ndir", "rc_pwm", "button"};
    uint32_t bits = board_status_bits();
    console_write("raw input levels (n-prefixed faults assert low):\r\n");
    for (unsigned i = 0; i < sizeof names / sizeof names[0]; ++i) {
        console_write(names[i]); console_write("="); console_u32((bits >> i) & 1U);
        console_write((i % 4 == 3) ? "\r\n" : " ");
    }
    console_write("\r\narm=0 pwm=000000 dump_pwm=0\r\n");
}
static void print_analog(void) {
    board_sample_analog();
    console_write("nominal 2500 mV reference; NTC values are pin voltages, not temperatures.\r\n");
    for (size_t i = 0; i < analog_sample_count; ++i) {
        analog_sample_t *sample = &analog_samples[i];
        console_write(sample->name);
        if (!sample->valid) { console_write("=ADC_ERROR\r\n"); continue; }
        console_write(" raw="); console_u32(sample->raw);
        console_write(" pin_mv="); console_u32(adc_pin_mv(sample->raw));
        if (i == 0) { console_write(" bus_mv="); console_u32(bus_mv(sample->raw)); }
        if (i >= 4 && i <= 6) {
            console_write(" nominal_ma="); console_i32(phase_current_ma(sample->raw, 2048));
        }
        console_write("\r\n");
    }
    console_write("current zero offsets and voltage scales need bench calibration.\r\n");
}
static void print_driver(void) {
    console_write("driver register readbacks:\r\n");
    for (uint8_t address = 0; address <= 6; ++address) {
        uint16_t value;
        if (!board_driver_read(address, &value)) {
            console_write("driver asleep or SPI timed out. use driver on with a valid bus supply.\r\n");
            return;
        }
        console_write("reg "); console_u32(address); console_write("="); console_hex16(value); console_write("\r\n");
    }
    console_write("all-ones replies can mean missing power or an open SDO connection.\r\n");
}
int main(void) {
    if (!board_init()) board_panic();
    console_write("\r\nBLDC ESC bring-up v0.1\r\n"); print_help(); console_write("esc> ");
    char line[48];
    uint32_t heartbeat_at = HAL_GetTick(), sample_at = heartbeat_at, led_at = heartbeat_at;
    for (;;) {
        uint32_t now = HAL_GetTick();
        if ((uint32_t)(now - heartbeat_at) >= 20U) { board_heartbeat(); heartbeat_at = now; }
        if ((uint32_t)(now - sample_at) >= 100U) { board_sample_analog(); sample_at = now; }
        if ((uint32_t)(now - led_at) >= 500U) { board_led_tick(); led_at = now; }
        if (!console_poll(line, sizeof line)) continue;
        switch (command_parse(line)) {
        case CMD_EMPTY: break;
        case CMD_HELP: print_help(); break;
        case CMD_STATUS: print_status(); break;
        case CMD_ADC: print_analog(); break;
        case CMD_DRIVER: print_driver(); break;
        case CMD_WAKE_ON:
            console_write(board_driver_wake(true) ? "driver awake; bridge still disabled\r\n" : "wake refused: require BUS_OK and a valid 12-30 V reading\r\n");
            break;
        case CMD_WAKE_OFF: (void)board_driver_wake(false); console_write("driver asleep\r\n"); break;
        case CMD_UNKNOWN: console_write("unknown command; type help\r\n"); break;
        }
        console_write("esc> ");
    }
}
