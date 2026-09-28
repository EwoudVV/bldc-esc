import csv
import math
import sys

rows = []


def emit(identifier, value, unit, basis, state="calculated"):
    rows.append((identifier, format(value, ".9g"), unit, basis, state))


torque_nm = 6.68 * 0.112984829
output_power = torque_nm * 125 * 2 * math.pi / 60
emit("MOTOR_TORQUE", torque_nm, "Nm", "6.68in_lb")
emit("MOTOR_OUTPUT_POWER", output_power, "W", "125rpm")
emit("MOTOR_SPEED_INPUT", 125 * 20, "rpm", "20to1_nominal")
emit("MOTOR_VI_PRODUCT", 26 * 0.75, "W", "current_definition_unspecified", "conditional")
emit("MOTOR_EFFICIENCY_RATIO", output_power / (26 * 0.75), "ratio", "only_if_DC_input_current", "conditional")

r_shunt = 0.001
gain = 20
adc_ref = 2.5
bias = adc_ref / 2
emit("ADC_CURRENT_STEP", adc_ref / 4096 / (r_shunt * gain), "A_per_LSB", "12bit_raw")
emit("ADC_COUNTS_AT_0A5", 0.5 * r_shunt * gain * 4096 / adc_ref, "counts", "no_oversampling")
emit("ADC_COUNTS_AT_0A75", 0.75 * r_shunt * gain * 4096 / adc_ref, "counts", "no_oversampling")
emit("INA241A2_OFFSET_EQUIV", 15e-6 / r_shunt, "A", "25C_max_datasheet_test_conditions")
emit("INA241A2_DRIFT_60C_EQUIV", 150e-9 * 60 / r_shunt, "A", "max_offset_drift")
emit("DRV8353_OFFSET_EQUIV", 3e-3 / r_shunt, "A", "pre_external_offset_subtraction")
emit("DRV8353_SENSE_OC_MIN_EQUIV", 0.25 / r_shunt, "A", "SEN_LVL_00_nominal")
for current in (0.5, 0.75, 15, 20, 40, 50):
    key = str(current).replace(".", "p")
    emit("CSA_LOW_" + key, bias - current * r_shunt * gain, "V", "INA241_REF1_REF2_1V25")
    emit("CSA_HIGH_" + key, bias + current * r_shunt * gain, "V", "INA241_REF1_REF2_1V25")

r_on_25 = 1.15e-3
r_on_hot = r_on_25 * 2
emit("FET_RDS_HOT_MODEL", r_on_hot, "ohm", "2x_25C_max", "model_assumption")
for current in (15, 20, 40):
    emit("BRIDGE_CONDUCTION_" + str(current), 3 * current**2 * r_on_hot, "W", "3_Iphase_rms_squared_Rds_hot", "screening")
    emit("SHUNTS_TOTAL_UPPER_" + str(current), 3 * current**2 * r_shunt, "W", "continuous_all_3_upper_bound", "screening")
    emit("SHUNT_EACH_UPPER_" + str(current), current**2 * r_shunt, "W", "continuous_upper_bound", "screening")
for total_transition_ns in (100, 200):
    mean_abs = 2 * math.sqrt(2) / math.pi * 20
    emit("SWITCHING_20ARMS_" + str(total_transition_ns), 3 * 0.5 * 30 * mean_abs * total_transition_ns * 1e-9 * 20000, "W", "sinusoidal_three_legs_no_Coss_Qrr", "screening")

emit("GATE_CHARGE_CURRENT_TOTAL_MAX", 6 * 170e-9 * 20000, "A", "Qg_max_10V_all_six")
emit("GATE_CHARGE_CURRENT_PER_RAIL_MAX", 3 * 170e-9 * 20000, "A", "Qg_max_10V_three_FETs")
emit("GATE_DRIVE_POWER_MAX_10V", 6 * 170e-9 * 20000 * 10, "W", "Qg_max_10V")
emit("DRV_LINEAR_LOSS_SCREEN", (30 - 10) * 6 * 170e-9 * 20000, "W", "charge_pump_topology_and_Iq_omitted", "screening")
emit("BUS_POWER_AT_26V_20A", 26 * 20, "W", "DC_input_ceiling_not_motor_rating")
emit("TVS_60V_HEADROOM_AT_TEST", 60 - 48.4, "V", "25C_31A_10_1000us_only")
emit("DIVIDER_AT_30V", 30 / 21, "V", "200k_top_10k_bottom")
emit("DIVIDER_AT_50V", 50 / 21, "V", "200k_top_10k_bottom")
emit("DIVIDER_AT_60V", 60 / 21, "V", "200k_top_10k_bottom")
emit("DIVIDER_ADC_BUS_STEP", adc_ref / 4096 * 21, "V_per_LSB", "12bit_raw")

for label, cap in (("LEGACY", 792e-6), ("CURRENT", 1000e-6)):
    emit("DC_LINK_C_" + label, cap, "F", "nominal")
    emit("DC_LINK_DV_20A_" + label, 20 / (cap * 20000), "V", "constant_current_full_period_upper_screen", "screening")
    energy = 0.5 * cap * (31**2 - 26**2)
    emit("REGEN_ENERGY_26_TO_31_" + label, energy, "J", "capacitor_only")
    emit("REGEN_TIME_100W_" + label, energy / 100, "s", "capacitor_only")
emit("DC_LINK_CURRENT_MIN_C", 1000e-6 * 0.8, "F", "minus20pct_tolerance")
emit("HYBRID_BANK_IRMS_135C_100KHZ_SUM", 10 * 3.3, "A_rms", "nameplate_sum_not_sharing_qualification", "screening")
emit("HYBRID_BANK_IRMS_125C_10KHZ_SUM", 10 * 4.6 * 0.75, "A_rms", "10kHz_coefficient_not_sharing_qualification", "screening")
emit("CAP_PWM_SQUARE_WAVE_SCREEN_20ARMS", math.sqrt(2) * 20 / 2, "A_rms", "Iphase_peak_over2_50pct_pulse", "screening")

for resistance in (2, 5, 10, 25):
    emit("DUMP_CURRENT_" + str(resistance) + "R", 31 / resistance, "A", "31V")
    emit("DUMP_POWER_" + str(resistance) + "R", 31**2 / resistance, "W", "31V_external_thermal_rating_required")
emit("DUMP_10R_CURRENT_50V_TRANSIENT", 50 / 10, "A", "fault_transient_only", "screening")
emit("DUMP_10R_POWER_50V_TRANSIENT", 50**2 / 10, "W", "pulse_rating_required", "screening")
emit("HALL_1K_DROP_AT_10MA", 1000 * 0.01, "V", "1k_not_valid_functional_supply")
emit("COPPER_OUTER_RESISTANCE_30MM_10MM", 1.724e-8 * 0.03 / (0.01 * 70e-6), "ohm", "20C_single_layer_ignores_vias", "screening")

writer = csv.writer(sys.stdout, lineterminator="\n")
writer.writerow(("id", "value", "unit", "basis", "status"))
writer.writerows(rows)
