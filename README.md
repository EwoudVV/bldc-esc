# BLDC ESC

## A custom STM32 motor controller for BLDC and PMSM motors.

I want to build a small vesc like controller, with hall sensors, current sensing, regen, and enough hardware to try FOC later. The first motor is a 26 V Groschopp gearmotor, but the board should be useful for other motors too.

## status

the first placement is done. the board is 116 x 112 mm for now, with all 449 parts on top. the power stage, shunts and current amplifiers are grouped together, with the capacitor bank on the left and the control connectors around the edges

found a pretty important mistake: the XT60 nets were backwards compared to the footprint's polarity marks. thats fixed now, and there's a separate check for it. **don't manufacture the devlog 03 snapshot (`dcad1e4`) or use its old input wiring**

changed the ADC reference to 2.5V with a 1.25V current-sense bias. the logic supply is now about 3.36V, with a supervisor watching the filtered analog rail. that closes the reference headroom problem on paper. startup, brownouts and supply switching still need scope tests

ERC is clean and the schematic and pcb connections match. checked the 112 different part numbers and corrected the SWD header and USB fuse footprints. connector drawings are checked, but physical fit and stock still need checking before assembly

the saved pcb matches the schematic again. a PCB update had introduced 61 wrong pad assignments, so those were corrected from a fresh schematic export before placing anything. reopen the saved project before doing another update from schematic

there are no courtyard overlaps or copper-clearance errors. two XT60 silkscreen lines extend past the board edge and still need trimming for production. the temporary ground pour is removed. there are no tracks or vias yet

next is placement review and routing. PCBWay is the planned fab, but the exact copper/dielectric stackup is still needed. the outline, mounting details and thermal design aren't a fabrication release

placement notes are in [engineering/placement-review.md](engineering/placement-review.md), with the saved checks in [engineering/placement-checks.json](engineering/placement-checks.json). the electrical review is in [engineering/review_m04.md](engineering/review_m04.md)

Progress is in [journal.md](journal.md).

## specs

- 12-30V input, mainly for 6S batteries and 24V systems
- 15A RMS phase current with passive cooling, 20A with airflow or a heat spreader
- Around 40A peak, with the allowed duration still to be worked out
- 60V MOSFETs and 63V DC-link capacitors
- 4 layers, 2 oz outer copper and 1 oz inner copper
- XT60 power input, MT60 motor connection, and JST-GH signal connectors

the current ratings are targets until thermal testing is done

## planned hardware

- STM32G474VET6 MCU
- DRV8353S gate driver and six external MOSFETs
- 3 1 milliohm Kelvin shunts, INA241A2 current amplifiers, and voltage/temperature sensing
- Hardware overcurrent shutdown and an external watchdog
- Brake chopper for an external dump resistor
- Hall sensors and quadrature encoder inputs
- Analog throttle, RC PWM, brake, direction, and enable inputs
- CAN FD, UART, USB-C, and SWD
- EEPROM for configuration and debug LEDs

The initial parts and alternatives are in [engineering/parts.csv](engineering/parts.csv), with references in [engineering/sources.csv](engineering/sources.csv)

## block diagram

![Controller block diagram](engineering/architecture.svg)
(made this in inkscape!)

## test motor

Groschopp / Blue-White BL6560-PS2120:

- Blue-White #90010-338, P/N 930-23-9002
- 26 V, 0.75 A nameplate
- 10 W reducer output, 125 RPM, 6.68 in-lb torque
- 20:1 gearbox
- 3 phase leads P1, P2, and P3, and a separate sensor thingy

motor data and measurements are in [engineering/motor.csv](engineering/motor.csv) and [engineering/measurements.csv](engineering/measurements.csv).

## roadmap

- [x] Research the motor family and choose the initial architecture
- [x] Set up the repo, KiCad project, calculations, and draft pinmap
- [x] Draw the complete schematic and assign footprints
- [x] First review of protection, power-up behavior, current sensing, and regen
- [x] Close the reference headroom, part-number and connector drawing checks
- [ ] Review the updated schematic and freeze it for placement
- [x] Place the components and check the first board outline
- [ ] Review placement and route the PCB
- [ ] Review the layout and make production files
- [ ] Bring up the MCU, telemetry, Hall inputs, and gate driver
- [ ] Run sensored six-step with current limiting, then speed control
- [ ] Test regen and current control
- [ ] Add sensored FOC, then a sensorless observer and startup

## repo structure

- `bldc-esc.kicad_pro` / `.kicad_sch` / `.kicad_pcb`: main KiCad project
- `schematic/`: 16 circuit subsheets
- `engineering/`: requirements, parts, sources, calculations, pinmap, and review checks
- `journal.md`: devlogs
- `production/`: will be added when there are fabrication files
