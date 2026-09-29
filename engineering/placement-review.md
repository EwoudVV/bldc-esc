# placement review

Sep 29, 2026. The main PCB contains the placement candidate. It is not routed or ready to manufacture.

## board and regions

The working outline is 116 x 112 mm. All 449 components are on the top side. Their courtyards total about 7,070 mm2, before extra routing space. The four corners have reserved space, but mounting holes and motor-cable strain relief are not finalized.

| Region | Placement | Routing priority |
| --- | --- | --- |
| Input and DC link | XT60 and TVS on the left, ten hybrids in two columns | Wide positive and return distribution; fuse remains external |
| Bridge | Three repeated half-bridge/shunt cells along the top | Local commutation loops first, then phase outputs |
| Current sensing | Amplifiers face the shunts' Kelvin pads | Short, coupled sense pairs, separate from power and gate returns |
| Gate driver | Below the bridge cells | GH/SH and GL/SP pairs, charge-pump and supply bypass loops |
| Brake power | Left edge near its resistor connector | Connector, diode, MOSFET and shunt loop; Kelvin driver return |
| Buck and rails | Lower left | Input bypass, SW/inductor, output return, then feedback |
| MCU and reference | Centre/right | ADC and reference connections, crystal, supply bypasses |
| Interfaces | Bottom and right edges | Port protection first; quiet signal routing inward |

The USB and brake connector orientations were checked for outward cable access. The phase snubbers and the first voltage-divider resistors are near their own bridge cells. The bleeder stays in the input-power region.

## measured placement geometry

These are straight-line pad-centre distances, not routed lengths or inductance measurements:

- Each shunt-to-amplifier Kelvin leg is about 2.53 mm, with equal positive and negative distances.
- High-side gate resistor to gate is about 1.87 mm. Low-side is about 2.28 mm.
- The longest driver-to-gate-resistor distance is about 33.1 mm after shifting the driver block. Allow for routing detours and keep the outgoing and return conductors closely coupled.
- All power MOSFETs, shunts, gate driver and local bridge ceramics remain on the same side.

Do not let a generic ground pour replace the Kelvin routes. SHx goes to the corresponding high-side source/switch-node pickup; SPx goes directly to the low-side source. The current-amplifier inputs go to the shunt's dedicated sense pads. VDRAIN needs its own pickup from the high-side drain distribution. Avoid sharing those sense/return traces with power current.

## four-layer routing intent

Keep the local high-di/dt commutation paths on F.Cu with their ceramics. Use broad outer-layer copper and sufficient vias for DC distribution and thermal spreading. Do not funnel phase current through the inner signal layers or through the driver's ground connection.

L2 remains the signal ground reference, with deliberate switch-node keepouts where needed. L3 provides quiet rails and signal routing. Paired gate/source connections may use an internal routing layer where that avoids the crowded surface, with adjacent outgoing/return vias and an intact reference. Do not route sensing traces parallel to gate or phase conductors. The bottom side is component-free for copper and heat spreading.

The manufacturer's actual 2 oz outer / 1 oz inner stack is still needed for USB geometry. The saved generic width/gap is not a controlled-impedance result. Check gate-return continuity, shunt pickup, current distribution, via loading and temperature after routing.

## saved checks

`placement-checks.json` records the canonical board's pad/net comparison, positions, file hashes and KiCad DRC result. There are no courtyard overlaps, copper-to-copper clearance errors or schematic-parity issues. The only geometric DRC findings are two existing XT60 body-outline silkscreen segments crossing the board edge. Trim those printed segments before production. No rule was disabled to hide them.

The reported 499 unconnected items are expected for this unrouted board. There are zero tracks, vias or zones. The approved provisional four-layer GND zone was removed. The before-placement board is backed up under `work/placement-20260928/`; it contains the earlier bad pad assignments and is for recovery, not fabrication.

The first PCB read during this pass had 61 mismatched pad assignments, including VBUS pads on GND and unconnected protection-diode pads. A fresh export of the saved schematic matched the design matrix and passed ERC. The board was resynchronized from that export. The cause of the earlier editor update has not been proven. The Mac was locked during the live-editor check, so close/reopen the saved project before another F8 update and review the proposed changes. The saved-file KiCad parity check passes.

All components remain on top. Printable 0.8 mm references that would collide on the front are on the back silkscreen. Functional control-port labels are on the front. Recheck all silkscreen after routing and via placement. Some custom/Infineon footprints have no available 3D model; use the 2D footprints and manufacturer drawings for their geometry.

## continuing the project

The KiCad PCB is the source of truth for further placement and routing. `placement.json` records this candidate. The placement scripts are construction/checking tools, not something to rerun over manual routing. The writer refuses to replace a canonical board whose saved hash no longer matches the checked placement.

Next: review this placement, finalize mounting/cable access and the fabrication stack, then route the bridge and brake power loops. Review those routes before filling the rest of the board. Current ratings, transient limits, reference sequencing and fault timing still require hardware tests.

For this unrouted stage, use `python3 engineering/check_project.py --placement` and `python3 engineering/placement_checks.py` after fresh KiCad exports. The latter expects the XML netlist at `work/qa/bldc-esc.xml` and the parity-enabled DRC report at `work/qa/drc-placement.json`. The older `verification.json` remains the historical schematic checkpoint.

References used for placement: [TI motor-driver layout guide](https://www.ti.com/lit/an/slva959b/slva959b.pdf), [DRV8353 layout guidance](https://www.ti.com/lit/ds/symlink/drv8353.pdf), [INA241 Kelvin layout](https://www.ti.com/lit/ds/symlink/ina241a.pdf), and [USB4105 mechanical drawing](https://gct.co/files/drawings/usb4105.pdf).
