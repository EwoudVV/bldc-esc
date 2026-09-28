# reference and BOM review

Sep 28, 2026. Schematic freeze candidate for review and placement. This is not a fabrication release or a measured current rating. No hardware has been powered.

## input polarity correction

J101 was reversed in `dcad1e4` (devlog 03): the assigned XT60PW-M footprint marks pad 1 negative and pad 2 positive, but the schematic had them the other way around. The current schematic and PCB now connect **pad 1 to GND and pad 2 to VBUS**. Do not manufacture the old snapshot or use its export for wiring.

The old pin-contract check repeated the same incorrect assumption. `audit_connectors.py` now compares the net assignments to the polarity marks in the actual footprint, separately from the schematic pin list. Check the purchased connector and assembled harness with a meter before applying power. Keying still provides no protection against a miswired harness.

D101 is now drawn as a unidirectional TVS, matching SMCJ30A. Its cathode remains on VBUS and its anode on GND.

## reference and reset changes

REF2030 could not claim its full load-regulation specification from the old 3.3 V rail. The REF20 family specifies that condition with at least 0.6 V input headroom. U502 is now REF2025, giving 2.5 V for the ADC and 1.25 V for the three primary current amplifiers. U308 remains the separate bus-powered reference for the brake chopper.

The main supply is now TLV75801PDRVR with 51.1k/10k feedback, nominally 3.3605 V. The net names remain `3V3` and `3V3_A`. FB501 is the lower-resistance BLM18KG601SN1D. U701 is TPS389033DSER and monitors the filtered analog rail, with 47 nF on CT. Its WSON-6 package has no exposed pad.

`reference_checks.py` reads the assembled values from the BOM and reproduces `reference_checks.json`.

| Check | Result | Basis |
| --- | --- | --- |
| Logic rail budget | 3.258-3.464 V | IC accuracy, resistor tolerance and drift, FB current, line regulation, 20 mV load allowance |
| Analog rail minimum budget | 3.235 V | 100 mA analog load and 0.231 ohm hot-bead model |
| Reference loaded-supply requirement | 3.1044 V | Maximum reference output plus 0.6 V headroom |
| Reset assertion minimum | 3.1383 V | 3.17 V threshold minus 1% |
| Reset release maximum | 3.2209 V | 3.189 V threshold plus 1% |
| Normal reference headroom margin | 130.6 mV | Analog minimum minus loaded-supply requirement |
| Static reset/reference margin | 33.9 mV | Minimum reset threshold minus loaded-supply requirement |
| Startup rail/reset margin | 14.2 mV | Analog minimum minus maximum reset-release threshold |
| Reset delay | 50.3 ms typical, 85.2 ms upper screen | CT tolerance and temperature allowance included in upper screen |
| Boot time before minimum watchdog interval | about 84.8 ms | 170 ms minimum watchdog interval minus reset-delay screen |

The 20 mV load allowance, 100 mA analog load and hot-bead multiplier are design budgets, not guaranteed measured behavior. The extreme startup margin is small. Check cold/hot startup and supply transients before enabling the bridge. Start a real firmware-health heartbeat early in boot. A free-running timer feeding the watchdog defeats its purpose.

The reference's fixed-load screen is 3.70 mA, including shorted NTC inputs, with another 10 mA reserved for ADC reference loading. Verify real load and settling. The clamp diode and roughly 3.45 uJ stored on the reference output are not proof of safe behavior during every abrupt rail short.

Required bench captures: slow and fast bus ramps, USB-only startup, both-source switchover, USB removal, bus buck collapse with USB present, and a controlled analog-rail brownout. Observe `3V3_A`, `VREF_2V5`, `POWER_OK`, `NRST` and gate-driver enable. Confirm bridge permission disappears before valid sensing is lost. Datasheet-typical reset propagation is not a guaranteed fast-collapse shutdown time.

## changed signal scales

| Signal | Current value |
| --- | --- |
| Primary phase current | 1.25 V zero, 20 mV/A, about 30.5 mA per raw 12-bit count |
| +/-40 A primary signal | 0.45-2.05 V |
| Nominal external current trip | +/-50.11 A |
| Bus window | 10.46-32.98 V nominal |
| Bus/phase ADC full scale | 52.5 V nominal, with the existing 21:1 dividers |
| Throttle and auxiliary divider | 10k / (12.1k + 10k), about 0.45249 |
| 5 V throttle at ADC | 2.262 V nominal |
| Driver diagnostic amplifiers | Configure gain 10 V/V and VREF_DIV = 1; midpoint follows actual `3V3_A / 2` |

With positive phase current defined from bridge to motor, use `I_phase = (V_zero - V_adc) / 0.020`. Calibrate the offset and verify the sign by injecting a known current. The 0.5 A first-motor limit is only about 16 raw counts. Sampling-window and noise checks remain essential.

R118/R119/C117 provide a separate bus-undervoltage reference, preserving the bus window after the current-reference change. R111/R112 and R115 were adjusted for the new reference. Primary INA241 gain stays 20. Do not reuse the old 3 V ADC scaling or set the driver's diagnostic gain to 20 without rechecking clipping. Disable the MCU's internal VREF buffer when using the external reference.

The emergency brake thresholds, source-specific regen restrictions and 20 kHz gate-charge budget from the previous review still apply. The 31 V chopper is not a 6S battery charge limiter.

## parts and connectors

The part audit covers 112 distinct order codes. `bom_audit.csv` records each source, fitted/optional quantity and footprint. Cached exact resistor/capacitor PDFs are checked against the values and package sizes in the BOM. IC ordering tables and manufacturer connector drawings supplement those checks. This is not a stock reservation, production qualification or physical-fit test.

- INA241A2IDR and TLV3011BIDBVR now include their required temperature-code character.
- C109 is C1206C472KDRACTU, a verified 4.7 nF / 1 kV part. Several general MLCCs now use exact KEMET part specifications. The 4.7 uF 0805 parts are rated 25 V.
- J501 is FTSH-105-01-L-DV-007-K. Pin 7 is physically absent. The local land pattern uses the manufacturer's 2.794 x 0.7366 mm pads instead of the shorter generic lands.
- F401 is MF-PSMF050X-2 in its actual 0805 package, with the manufacturer's land pattern. It holds 0.5 A at room temperature but only about 0.23 A at 85 C. USB current budgeting must account for that derating and its resistance. It does not enforce the 100 mA pre-enumeration limit.
- The ten GH connector footprints were checked against the manufacturer drawing. Pin numbering depends on viewing side; do not copy a cable-end view directly onto the PCB view. Confirm the purchased housings and crimp contacts before assembly.
- JST-GH and the selected M24C64 temperature grade are limited to 85 C. Keep them away from the bridge hot spot. The provisional 95 C bridge-NTC shutdown point is not permission for the entire board to reach 95 C.
- The dump connector remains Phoenix 1711725, 5.08 mm pitch and 24 A nominal. Wire size, connection quality and actual temperature still determine usable current.

The TLV758 package screen gives about 0.408 W at 200 mA with 5.3 V in and 3.258 V out. Its 80.3 C/W JEDEC figure gives about 32.8 C rise under those test-board conditions. The real board needs thermal spreading and measurement.

## handoff

The updated design has 449 footprints, still in the staging grid. Existing component positions are preserved. There is no outline, routing or copper fill. ERC, netlist, independent pin checks, connector checks and static logic checks must be rerun after any schematic edit. `verification.json` is the saved result for this checkpoint.

Next is a user review and rough placement. Review the bridge/DC-link/shunt loops, gate returns, chopper loop and quiet analog region before routing. PCBWay is selected, but the actual 2 oz outer / 1 oz inner dielectric stack is still needed before calculating USB geometry. Purchase stock, physical connector fit, motor leadout, firmware safe defaults, fault timing, waveforms, regen and thermal ratings remain separate checks.

The exact source links are in `sources.csv` and `bom_evidence.json`. `review_m03.md` is historical; its old reference, current scales and main reset timing no longer apply.

For this checkpoint, `checkpoint.py --baseline dcad1e4` reruns the project, netlist, pin, reference and connector checks and compares existing PCB positions against that commit. Run KiCad ERC, netlist export and PCB DRC first. BOM PDF checks use the ignored `work/datasheets/` cache and the primary links in `bom_evidence.json`; `fetch_passive_specs.py` can restore the exact passive-part specifications. Re-run `bom_audit.py` after a BOM change. Only use `--visual-reviewed` after inspecting the current PDF renders. The scripts do not stage or commit files.
