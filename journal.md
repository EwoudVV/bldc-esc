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

### Devlog 03: schematic review

Date: Sep 28, 2026

Time spent: 4 hours
Lapse: no lapse

went back through the schematic with the datasheets. found some things that erc wouldnt find

the dump resistor diode had the wrong package assigned, the buck input capacitors needed 1210 footprints instead of 1206, and the crystal family didn't actually support 8MHz. fixed those and some of the part numbers. also changed the 3.3V regulator to the exposed-pad version because the little SOT-23 package would get too hot at the planned load

changed the hardware comparators too. the old ones didnt have a good enough guaranteed low output for the logic gates after them. the reset outputs now connect through 0 ohm links instead of diodes, so they don't lose voltage margin there either

the bridge now checks that the brake chopper is ready before it can turn on. that matters if USB keeps the mcu alive but the bus-powered 5V supply stops working. added dump current telemetry and isolated the hardware fault signals from the mcu pins too. found an annoying STM32 detail where the USB dead-battery pull-down can affect the pin used for the driver fault signal, so that needs to be disabled in firmware

the chopper has its own more accurate reference now. the calculated turn-on range is about 30.7-31.8V, with the nominal point around 31.3V. thats still just the emergency clamp, not a safe charging limit for a 6S battery

added buffers and low-leakage clamps for the external analog and temperature inputs. the NTC conversion also needs to account for the 1k series resistor, otherwise it can read the temperature wrong

using PCBWay for the fab checks. changed the corner shape on the USB connector ground pads to get enough clearance around its locating holes. the buck's 0.2mm thermal vias are okay with the selected rules too. still need the actual 2oz/1oz stackup before working out the USB routing dimensions

split the bigger pages again so everything fits on A3 or A4. there's 16 subsheets now. cleaned up the added buffers, protection circuits and labels, and fixed a project-rule setting that was hiding the wires in exports

ERC is still at 0 errors and 0 warnings. checked the exported connections, a separate set of 425 pin connections, and 4096 combinations of the shutdown logic. the pcb has 444 footprints in the staging grid, with no placement or routing done

stopping here for a review checkpoint. the reference supply headroom still needs a closer look, and the final BOM and connector fit checks aren't finished. the current ratings, regen behavior and fault timing all still need real hardware tests

### Devlog 04: reference supply and BOM

Date: Sep 28, 2026

Time spent: 3 hours
Lapse: no lapse

finished checking the reference supply and went through the part numbers and connectors

found a pretty bad mistake with the XT60. the footprint has pad 1 as negative and pad 2 as positive, but the nets were the other way around. fixed that in the schematic and pcb, and added a check against the actual footprint markings. nothing has been built yet. the devlog 03 files should not be used to make a board

the 3V reference didnt have enough guaranteed supply headroom. changed it to 2.5V, with 1.25V for the current sensing. also changed the regulator to an adjustable one set to about 3.36V and used a better supervisor on the analog rail. adjusted the current and voltage thresholds and the throttle dividers to match. the main current amplifiers still use gain 20, but the drivers diagnostic ones need gain 10

checked 112 different part numbers. fixed the missing characters in two TI part numbers and the chassis capacitor's order code. the sub polyfuse was actually an 0805 part, not 1206. the SWD connector now has the proper longer pads and pin 7 missing for the key

ERC has 0 errors and 0 warnings. the connection checks, 426 separate pin checks and 4096 shutdown logic cases pass too. there's 449 footprints on the pcb now. the existing positions stayed where they were and there's still no routing or outline

some images of the schematics: ![img1](image.png) ![img2](image-1.png) ![img3](image-2.png) ![img4](image-3.png) ![img5](image-4.png) ![img6](image-5.png) ![img7](image-6.png) ![img8](image-7.png) ![img9](image-8.png) ![img10](image-9.png) ![img11](image-10.png) ![img12](image-11.png) ![img13](image-12.png) ![img14](image-13.png) ![img15](image-14.png) ![img16](image-15.png) ![img17](image-16.png)

### Devlog 05: placement

Date: Sep 29, 2026

Time spent: 4 hours
Lapse:

the first placement is done. its 116 x 112 mm right now, with all 449 parts on the top side.

started with the bridge, shunts and local capacitors, then put the gate driver and current amplifiers around them. the amplifiers face the little Kelvin pads on the shunts. moved the driver again after checking the longer gate connections

the capacitor bank is on the left, the motor connections are at the top, and the smaller control connectors go around the bottom and right. the buck is away from the reference and analog inputs. also checked which way the USB and brake connectors face

found a problem before placement: the PCB update had 61 wrong pad assignments. the schematic export was correct, so the pcb was synchronized again before continuing. the old saved board is backed up, and the temporary ground pour is removed

went through the placement renders and DRC a few times. moved the snubbers and voltage pickup resistors closer to their own phases, kept space for the power connections, and cleaned up the reference labels. some of the crowded labels are on the back, but the components are all still on top

there are no courtyard overlaps or copper-clearance errors, and the schematic and PCB match. two bits of the XT60 silkscreen stick over the edge. those still need trimming before making production files

image: ![pcb placemnettn](image-17.png)