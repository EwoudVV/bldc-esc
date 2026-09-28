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

### Devlog 02: schematics

Date: Sep 28, 2026  
Time spent: 8 hours
Lapse: no lapse

now have the first full schematic done. there's 13 subsheets now because the analog inputs, safety stuff, voltage sensing, current protection, gate driver and USB needed their own pages

The bridge, current sensing, power supplies, mcu, hall and encoder inputs, CAN, USB, and brake chopper are all in there. also assigned the footprints and put them on the pcb. theyre just in a grid for now, no placement or routing yet

A few things changed:

- moved the i2c clock off PB8 because thats also the boot pin
- added a hardware current trip and arm latch, so a fault stops the bridge and it needs to be armed again
- added a service jumper for programming. it turns off the watchdog but also holds the bridge off
- gave the brake chopper its own overcurrent protection
- changed the capacitor bank to 10 matching 100uF hybrids after checking the ripple current sharing
- used bigger packages for some chips because the smaller footprints needed 0.15mm clearance

Made local footprints for the gate driver and shunts too. the generic gate driver footprint had the wrong exposed pad size

went back through the drawings because too much of it was just parts connected by labels. wired the local circuits properly, split the amplifiers and comparators into their individual units, and cleaned up the labels and spacing. its a lot easier to follow the filters and protection circuits now

the first pass was still way too spread out. moved the circuit groups closer together and shortened the wire runs. the input and CAN sheets fit on A4 now, and most of the rest fit on A3. the red crosses are DNP parts, like the optional chassis link and snubbers

ERC has 0 errors and 0 warnings. the exported connections and pcb pad nets were checked too, with no schematic/pcb mismatches

next is going through the power and protection circuits again before layout. the usb connector hole clearance and buck regulator thermal vias still need checking against the fab rules
