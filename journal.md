# Journal

## devlogs for progress

## Total time spent: 4 hours

### Devlog 01: research and project setup

Date: Sep 27, 2026  
Time spent: 4  hours
Lapse: no lapse

Started the motor controller project for my 26 V, 0.75 A Groschopp / Blue-White gearmotor. i want the board to be useful for bigger motors later too

The current target is 12-30 V input, 15 A RMS phase current with passive cooling, and 20 A with some extra cooling

my choices are an STM32G474, a DRV8353S gate driver, six MOSFETs, and three current shunts. Hall and encoder inputs, CAN, USB, and a brake chopper are planned too. I want to get sensored six step working first, then move on to FOC.

Found Groschopp's standard Hall wiring diagram. The pinout on this OEM motor still needs checking, and the higher ratings of other BL6560 motors don't apply to this winding.

A few stuffs changed when i looked at the datasheets:

- Chose INA241A2 amplifiers for better accuracy at low current.
- Changed the ADC reference to 3.0 V and kept the driver's reference input at 3.3 V.
- Increased the candidate capacitor bank to account for ripple current.
- Calculated that the capacitors only absorb about 0.18 J between 26 V and 31 V. The dump resistor still needs to handle the braking energy.

Set up the repo and KiCad project with seven subsheets. The parts list, source links, calculations, measurement table, and draft 100-pin MCU allocation are in `engineering/`