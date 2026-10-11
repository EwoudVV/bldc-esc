# bring-up firmware

This build reads the board's inputs and gate-driver registers over UART. It does not drive a motor. The board has not been assembled or tested yet.

## build

Requires CMake 3.20 or newer and the GNU Arm Embedded toolchain (`arm-none-eabi-gcc`, `objcopy` and `size`). GCC 16.1.0 was used for the initial build. The required ST HAL and CMSIS files are included under `vendor/`; their versions are in `vendor-lock.json`.

From the repository root:

```sh
cmake -S firmware -B firmware/build -DCMAKE_TOOLCHAIN_FILE=cmake/arm-gcc.cmake -DCMAKE_BUILD_TYPE=Release
cmake --build firmware/build
```

Outputs are `firmware/build/esc_bringup.elf` and `firmware/build/esc_bringup.bin`. The binary starts at `0x08000000` on the STM32G474VET6.

## software tests

Requires a host C compiler with AddressSanitizer and UndefinedBehaviorSanitizer:

```sh
cmake -S firmware/tests -B firmware/build/host
cmake --build firmware/build/host
ctest --test-dir firmware/build/host --output-on-failure
```

These cover command parsing, voltage/current calculations, reset GPIO settings and UART line handling. They do not verify the physical board.

## connections

Use an SWD probe on J501: pin 1 is the 3.3 V target reference, pin 2 SWDIO, pin 3 GND, pin 4 SWCLK and pin 10 NRST. Power the target separately and use a probe that senses its voltage. Check connector orientation against the schematic before connecting it.

The console is on J702: pin 1 GND, pin 2 TX, pin 3 RX and pin 4 3.3 V. It uses USART3 on PC10 (TX) and PC11 (RX), at 115200 baud, 8N1 and 3.3 V logic. Connect adapter RX to board TX, adapter TX to board RX, and common ground. Leave the adapter's power pin disconnected.

## commands

| Command | Result |
| --- | --- |
| `help` | Command list |
| `status` | Raw input levels for faults, bus status, Hall, encoder and controls |
| `adc` | Raw ADC readings, pin voltages, bus voltage and nominal phase currents |
| `driver on` | Wakes the gate driver for SPI reads if BUS_OK is high and measured bus voltage is 12-30 V |
| `driver` | Reads DRV8353 registers 0 through 6 |
| `driver off` | Returns the gate driver to sleep |

ARM, all six PWM outputs and brake PWM stay low. Sensor and encoder power remain off. No command arms the bridge or changes driver registers. Driver wake is removed if the periodic bus check fails. An unexpected interrupt stops the heartbeat and drives the control outputs low.

The ADC uses the external 2.5 V reference. Current offsets and voltage scales need measurement and calibration. NTC readings are voltages, not temperatures. USB, CAN, motor commutation and FOC are not implemented in this build.

Start bring-up with the motor disconnected. Power rails, fault behavior and gate outputs still need bench checks before motor-control firmware is used.
