# schematic review

Historical devlog 03 checkpoint. The current design changes and limits are in [review_m04.md](review_m04.md). In particular, the old J101 input polarity was wrong and must not be manufactured. The reference, logic regulator and supervisor have also changed.

Sep 28, 2026. This is the schematic review checkpoint, not a fabrication release. No hardware measurements yet. The current ratings are still targets.

## changes from devlog 02

| Circuit | Change | Reason |
| --- | --- | --- |
| Main enable and arm | `BRK_ARMED` qualifies both paths | USB power must not leave the bridge usable after the bus-powered chopper loses power or trips |
| Reset | R701/R703 are zero-ohm links; D701/D702 removed | Both supervisor outputs are open-drain. Combining them without diode drops gives a better guaranteed logic LOW |
| Hardware comparators | TLV9024PWR replaces TLV1704IPWR | 175 mV maximum LOW at 4 mA over temperature, against 800 mV maximum LOW-input threshold for the following LVC gates |
| Fault monitoring | Series resistors between hardware decision nodes and MCU inputs | A GPIO configuration mistake must not drive the actual fault or enable node |
| Chopper reference | REF2025 VBIAS replaces the comparator's internal reference | Tighter clamp thresholds; still powered from 5V_BUS, independently of the MCU |
| Chopper current | Added PA6 / ADC2_IN3 telemetry | Allows current and resistor-continuity checks before enabling meaningful regen |
| Analog ports | Added TLV9062 buffers, port TVSs and BAV199 clamps | Isolate high-impedance dividers from ADC sampling and reduce clamp leakage |
| Sensor pull-ups | Use the switched Hall/encoder rails | Avoid pulling external 5 V signals directly into the 3.3 V rail through the pull-up resistors |
| 3.3 V regulator | TLV75533PDRVR, WSON with exposed pad | The old SOT-23 package had poor thermal margin at the planned logic load |
| D301 | STPS5H100AF / SOD-128 | The previous STPS5H100B was a DPAK part assigned to an SMC footprint |
| C401/C402 | 1210 footprints | Matches the selected TDK part, which is not 1206 |
| Y501 | ABM3-8.000MHZ-D2Y-T / 5032 two-pad | The previous ABM8G family does not cover 8 MHz |
| C201, C404/C405, L401 | Corrected part numbers | Avoid obsolete or unsupported ordering codes |
| Drawings | Temperature, brake supervision and reset supervision separated | Keep the circuit pages on A3/A4 and the new circuitry readable |

## thresholds and timing

`electrical_checks.py` reproduces the numeric results in `electrical_checks.csv`. These are circuit calculations, not measured trip points.

| Item | Result | Qualification |
| --- | --- | --- |
| Main external current window | nominal +/-49.96 A | Board protection only; not the motor's working current limit |
| Main bus window | nominal 10.52-33 V | The commanded operating range remains 12-30 V |
| Chopper on / off | nominal 31.28 / 30.65 V | Includes 6 mV typical internal hysteresis |
| Chopper turn-on corner range | 30.73-31.81 V | Reference, comparator offset/CMRR/PSRR, hysteresis and resistor corners |
| Chopper hysteresis | 0.488-0.728 V | Correlated errors for the same assembled circuit |
| Chopper overcurrent | nominal 20.83 A; screening range 19.91-21.80 A | Includes INA180 offset/gain and shunt drift assumptions |
| Main POR delay | 57.64 ms typical | 10 nF timing capacitor; not 12 ms |
| Chopper POR delay | 6.21 ms typical | 1 nF timing capacitor; check reference settling and latch timing at startup |
| External watchdog | 200 ms nominal | Service jumper disables the watchdog and independently prevents bridge operation |

TLV9024 has no internal hysteresis. A current-window crossing clears a latch, so comparator chatter cannot automatically re-arm the bridge. A bus threshold crossing also clears the latch. Test slow bus ramps for gate-driver enable chatter; do not operate on the UV/OV boundary.

The 31 V clamp does **not** protect a full 6S battery from overcharge. Battery regen limits must come from the actual pack and BMS. The 28.5 V soft limit is only a starting point for the 26 V bench profile.

## startup and fault behavior

| State | Required behavior / limitation |
| --- | --- |
| USB only | MCU can run; BUS_OK and BRK_ARMED prevent bridge enable |
| Bus only | Buck, chopper reference and chopper latch start first; bridge still needs healthy supervision, driver wake and a fresh arm edge |
| Both sources | TPS2116 gives bus-derived power priority; check switching and reverse current on the bench |
| Bus buck fails while USB remains | BRK_ARMED falls; driver enable and bridge latch both lose permission |
| MCU unprogrammed | Wake and arm pulldowns keep the bridge off; sensor supplies default off |
| MCU stalls | Watchdog pulls NRST low; latch clears and driver enable drops |
| Hardware enable removed | Latch clears. Restoring the connector does not re-arm it |
| Driver fault / current trip / bus window fault | Latch clears; PWM outputs are disabled and gate-driver input pulldowns act |
| Chopper short / overcurrent | Chopper latch clears until a bus-power cycle; main bridge permission is removed too |
| Chopper resistor unplugged | Not independently detected by the hardware latch; validate current response before allowing regen |
| Motor backdriven with bridge off | Body diodes can still charge the bus. Turning off the gates is not an energy sink |
| Controller unpowered while backdriven | Chopper startup is not an instantaneous protection guarantee; exclude this condition until tested with a suitable external energy path |

The logic audit covers 4,096 combinations and the explicit fault/re-arm sequence. It does not simulate analog delays, contact bounce, propagation skew, metastability, every component failure, or single-fault safety compliance.

STM32 detail: PA10 is CAN_STB. Its reset pull-up can activate the UCPD dead-battery pull-down on PB4. R725 isolates that pin from the real DRV_nFAULT node. Firmware must set `PWR_CR3.UCPD1_DBDIS` before trusting PB4. PA9's higher leakage also required lowering the USB sense-divider impedance to 10k/15k.

## sampling and current limits

- The INA241 polarity gives a higher ADC voltage when current flows from the motor into the low-side bridge return. With positive phase current defined from bridge to motor, use `I_phase = (V_zero - V_adc) / 0.020`. Verify this with a known injected current before commutation.
- One raw ADC count is about 36.6 mA. At 0.5 A there are only about 14 counts of signal. Calibrate offsets and measure noise; oversampling does not fix a bad sampling window.
- ADC1/2/3 use the same TIM1 trigger and clock, with equal injected sampling times. Initial screen: 42.5 MHz ADC clock, 24.5 sample cycles, 12.5 conversion cycles, about 0.871 us total.
- The 100 ohm / 1 nF filter gives about 47 uV residual after a worst-case 3 V sampling step in the simplified 5 pF ADC-capacitor model. Amplifier settling, switching blanking and board parasitics are additional constraints. Keep an initial valid low-side window of at least 3 us.
- Three low-side shunts do not provide three valid measurements at every duty cycle. Track sample validity and reconstruct the missing phase. Start with duty limited to 85%.
- Driver diagnostic ADCs, temperature channels and dump-current telemetry use slower regular conversions. The dump-current scale is 36 mV/A after its divider.
- Subtract the external NTC's 1k series resistor before converting resistance to temperature. Use the actual sensor R/T curve; B25/50 alone is not a precision high-temperature model.
- First motor operation: 0.5 A phase-peak software limit. The nameplate's 0.75 A definition is still unknown; do not equate it with a phase RMS rating or use the board's 50 A trip as motor protection.

## power and thermal checks

At 20 kHz, three 170 nC gates plus gate pulldowns require about 10.84 mA from each driver rail. The 12 V gate-supply capability is 20 mA per rail. At 40 kHz the same screening load is 21.04 mA, so 40 kHz is not approved by this design review. The DRV8353 uses a charge pump; its capacitor is connected from VCP to VDRAIN, not to ground. No ordinary bootstrap duty-cycle limit is being assumed for the main bridge.

The 3.3 V LDO dissipates about 0.39 W at 200 mA with 5.2 V in and 3.25 V out. TI's JEDEC thermal figures give about 90 C rise for the old DBV package versus 39 C for the selected DRV package. These are package comparisons, not board-temperature predictions. Solder and spread heat from the exposed pad.

The buck is about 301 kHz, with a 5.088 V ideal setpoint and about 5.13 V after the first-order ripple-injection offset. The nominal feedback ripple is 14.7 mV at 12 V input and 20.5 mV at 26 V. TI recommends 20 mV nominal and at least 12 mV at minimum input. With 22 uF **effective total** output capacitance, the in-phase/capacitive ripple ratio is about 5.45. Confirm effective capacitance, load steps and low-input operation; timing and MLCC bias are not fully bounded by this nominal model.

REF2030 is powered from 3V3_A for shutdown tracking. Its 20 mA load-regulation specification requires 0.6 V headroom, which this circuit does not have. The actual load is much smaller, but low-headroom regulation and VREF-versus-VDDA startup/shutdown need measurement. Do not claim the full reference accuracy specification under these conditions. Keep this as a review gate before freezing the analog design.

USB-only firmware must stay under 100 mA before enumeration, with sensors off and a low-power clock configuration. The polyfuse does not enforce the USB enumeration budget. Measure pre-enumeration current and inrush before connecting to an ordinary host port.

At 20 A phase RMS, the hot-RDS screening model gives 2.76 W bridge conduction loss and up to 1.2 W across all shunts. The switching estimate adds about 1.62-3.24 W for 100-200 ns combined transitions, before Coss and reverse-recovery losses. Driver heating, connectors and copper must also be included. The 15/20 A continuous and 40 A peak ratings remain unpublished targets.

## regen and source wiring

The 1000 uF bank stores only 0.1425 J between 26 and 31 V. A 100 W regenerative event crosses that energy interval in about 1.4 ms. The TVS is for residual pulses, not continuous braking.

A 10 ohm resistor dissipates about 96 W at 31 V. It is a reasonable first-motor test load with suitable heatsinking, not a full-controller braking load. A 2 ohm load is about 480 W at the clamp voltage. Limit firmware regen power to the resistor, cooling and source acceptance. Measure flyback current and temperature at D301, especially with long resistor leads.

Use a verified regen-capable supply or reverse-blocking source connection when bench testing. A normal bench supply may not sink current even though the chopper limits the bus later. Do not connect a fully charged battery for initial regen testing.

A 100 ohm precharge resistor can stall regulator startup: at 12 V its maximum transferable power into a constant-power load is only 0.36 W. Start with a controlled, current-limited bench ramp. For a battery harness, calculate the precharge load and pulse rating and verify bus voltage before bypassing; do not use an unqualified fixed delay. The external DC fuse remains mandatory. XT60 keying is not protection against a miswired harness.

## PCBWay and layout handoff

- Starting rules: 0.20 mm copper and NPTH clearance, 0.20 mm minimum finished drill, 0.15 mm via annulus. The LM5164 footprint's 0.20 mm holes / 0.50 mm pads meet those nominal rules.
- J401 uses the local USB4105 footprint. Only the four ground-pad corner radii change, from 0.15 to 0.30 mm. Pad extents and holes remain in place. Calculated locator-hole clearance rises from 0.194 to about 0.233 mm. Keep this footprint rather than substituting the stock one on update.
- Four layers, 2 oz outer / 1 oz inner remains the requested stack. PCBWay's default stack is not a confirmed quote for this copper combination. Obtain the actual dielectric stack before setting USB differential geometry. The saved 0.20 mm width/gap is a placeholder, not a 90 ohm claim.
- Keep the DC-link ceramics, bridge and shunts on the same side. Kelvin sense traces go to the shunt sense pads. DRV SPx and gate-source returns go directly to the power-device source, not through a sense-input filter.
- L2 should be continuous ground for signal returns, with deliberate switch-node keepouts. Do not use L3 as a long high-di/dt switching-current detour. Keep the analog return quiet by current-path placement, not a split ground plane under ADC/SPI signals.
- Review placement before routing: commutation loops, gate loops, chopper loop, analog sampling paths, thermal spreading and connectors. No component placement, outline, zones or routes have been designed here.

## still open

Before schematic freeze: low-headroom reference analysis, final orderable BOM pass, connector drawing/physical fit checks and any resulting corrections. Before production: user placement/routing, actual stackup, layout review, DRC and a fresh schematic/PCB comparison. Before powered motor use: motor pinout and measurements, firmware safe defaults, gate waveforms and fault-injection tests. None of these is replaced by clean ERC.

Datasheet locators and PCBWay links are in `sources.csv`. Pending checks are tracked in `open_items.csv` and `review_gates.csv`.
