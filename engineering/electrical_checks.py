import csv
import math
import sys
from itertools import product

rows=[]


def add(name,value,unit,basis):
    rows.append([name,format(value,'.9g'),unit,basis])


add('I_HW_TRIP_POS',(3*49900/59900-1.5)/0.02,'A','nominal_1mohm_gain20')
add('I_HW_TRIP_NEG',(1.5-3*10000/59900)/0.02,'A','nominal_1mohm_gain20')
add('BUS_UV',3*10000/59900*21,'V','nominal')
add('BUS_OV',3*11000/21000*21,'V','nominal')
add('DUMP_OC',1.25/(0.003*20),'A','REF2025_VBIAS')
scale=(200000+8450)/8450
high=(1.25/10000+5/2490000)/(1/10000+1/2490000)
low=(1.25/10000+0.1/2490000)/(1/10000+1/2490000)
add('DUMP_ON',(high+.003)*scale,'V','1V25_reference_6mV_internal_hysteresis')
add('DUMP_OFF',(low-.003)*scale,'V','output0V1_6mV_internal_hysteresis')
ref_error=.0005+8e-6*100+35e-6*.5+20e-6*.15
offset_bound=.009+1.27/10**(54/20)+.001*3.5
limits=[];off_limits=[];hysteresis=[]
for vref,offset,rt,rb,rr,rf,vo,hys,vol in product([1.25*(1-ref_error),1.25*(1+ref_error)],[-offset_bound,offset_bound],
    [200000*.999,200000*1.001],[8450*.999,8450*1.001],
    [10000*.999,10000*1.001],[2490000*.99,2490000*1.01],[4.7,5.3],[.002,.008],[0,.2]):
    on=((vref/rr+vo/rf)/(1/rr+1/rf)+offset+hys/2)*(rt+rb)/rb
    off=((vref/rr+vol/rf)/(1/rr+1/rf)+offset-hys/2)*(rt+rb)/rb
    limits.append(on);off_limits.append(off);hysteresis.append(on-off)
add('DUMP_REFERENCE_FRACTIONAL_BOUND',ref_error,'ratio','0p05pct_8ppm_per_C_100C_line_and_load')
add('DUMP_COMPARATOR_OFFSET_BOUND',offset_bound,'V','9mV_plus_54dB_CMRR_plus_1mV_per_V_PSRR_full_span')
add('DUMP_ON_CORNER_MIN',min(limits),'V','static_extreme_corners_not_dynamic_validation')
add('DUMP_ON_CORNER_MAX',max(limits),'V','static_extreme_corners_not_dynamic_validation')
add('DUMP_OFF_CORNER_MIN',min(off_limits),'V','same_parts_correlated_reference_offset')
add('DUMP_OFF_CORNER_MAX',max(off_limits),'V','same_parts_correlated_reference_offset')
add('DUMP_HYSTERESIS_MIN',min(hysteresis),'V','correlated_not_subtracted_independent_extremes')
add('DUMP_HYSTERESIS_MAX',max(hysteresis),'V','correlated_not_subtracted_independent_extremes')
trip=[((1.25*(1+s*ref_error)+vcomp)/20/(1+gain)-vos)/(.003*(1+shunt))
      for s,vcomp,gain,vos,shunt in product([-1,1],[-.006,.006],[-.012,.012],[-.0006,.0006],[-.0175,.0175])]
add('DUMP_OCP_SCREEN_MIN',min(trip),'A','reference_comparator6mV_INA600uV_gain1p2pct_shunt1p75pct')
add('DUMP_OCP_SCREEN_MAX',max(trip),'A','static_screen_thermal_drift_included')
vout=1.2*(1+324000/100000)
freq=vout*2500/42.2*1000
add('BUCK_SETPOINT',vout,'V','before_ripple_injection_offset')
add('BUCK_FREQUENCY',freq,'Hz','RON42k2')
for vin in (12,26,30,50):
    delta=vout/(freq*68e-6)*(1-vout/vin)
    add('BUCK_IL_RIPPLE_'+str(vin),delta,'A_pp','68uH_nominal_CCM')
    add('BUCK_FB_RIPPLE_'+str(vin),vout/(vin*freq)*(vin-vout)/(301000*2.2e-9),'V_pp','type3_screening')
    add('BUCK_OUTPUT_RIPPLE_CEFF22U_'+str(vin),delta/(8*freq*22e-6),'V_pp','assumes_total_Ceff22uF_verify_DC_bias_and_temperature')
    add('BUCK_RIPPLE_RATIO_'+str(vin),8*freq*68e-6*22e-6/(301000*2.2e-9),'ratio','in_phase_to_capacitive_ripple_SNVA874_screen')
add('BUCK_SETPOINT_OFFSET_26V',vout+(.5*float(next(r[1] for r in rows if r[0]=='BUCK_FB_RIPPLE_26')))*(1+324/100),'V','type3_DC_offset_first_order')
add('USB_SENSE_AT_4V4',4.4*.6,'V','Rtop10k_Rbottom15k')
add('USB_SENSE_AT_5V25',5.25*.6,'V','Rtop10k_Rbottom15k')
usb_min=4.4*14850/(10100+14850)-4.5e-6*(10100*14850/(10100+14850))
add('USB_SENSE_MIN_WITH_LEAKAGE',usb_min,'V','1pct_resistors_4p5uA_PA9_leakage')
add('USB_SENSE_VIH_MARGIN',usb_min-.7*3.35,'V','STM32_CMOS_0p7VDD_not_TTL_assumption')
add('TLV9024_LOGIC_LOW_MARGIN',.8-.175,'V','LVC_VILmax_minus_comparator_VOLmax_4mA_full_temp')
add('DRV_GATE_CURRENT_PER_RAIL_20KHZ',3*170e-9*20000+3*10/47000,'A','max_Qg_plus_worst_pulldown_load')
add('DRV_GATE_RAIL_HEADROOM_12V',.020-(3*170e-9*20000+3*10/47000),'A','datasheet_20mA_12V_rail')
add('DRV_GATE_CURRENT_PER_RAIL_40KHZ',3*170e-9*40000+3*10/47000,'A','exceeds_12V_budget_not_approved')
for current in (.1,.2,.25):
    heat=current*(5.2-3.25)
    add('LDO_LOSS_'+str(current),heat,'W','worst_rail_screen')
    add('LDO_DBV_RISE_'+str(current),heat*231.1,'degC','old_SOT23_JEDEC_not_board_prediction')
    add('LDO_DRV_RISE_'+str(current),heat*100.2,'degC','WSON_EP_JEDEC_layout_dependent')
for name,c in [('MAIN',10e-9),('CHOPPER',1e-9)]:
    add('POR_'+name+'_DELAY',.0005+c*1e9/175,'s','TPS3808_typical_CT_equation')
add('ADC_CURRENT_LSB',3/4096/.02,'A','12bit_3V_reference')
add('ADC_CURRENT_ACQUISITION',24.5/42.5e6,'s','all_three_injected_ADCs_equal')
add('ADC_CURRENT_CONVERSION',37/42.5e6,'s','24p5_sample_plus12p5_conversion')
add('ADC_RC_RESIDUAL_FULLSTEP',3*5e-12/(1e-9+5e-12)*math.exp(-(24.5/42.5e6)/(100*1e-9)),'V','charge_sharing_5pF_ADC_100R_1nF_excludes_amplifier_settling')
add('ADC_HALF_LSB',3/8192,'V','12bit')
add('DUMP_ADC_SCALE',.003*20*.6,'V_per_A','10k_15k_divider')
add('CRYSTAL_GM_CRITICAL',4*140*(2*math.pi*8e6)**2*(7e-12+18e-12)**2,'S','ABM3_max_ESR_C0_AN2867_screen')
add('CRYSTAL_DRIVE_CURRENT_MAX',math.sqrt(100e-6/140),'A_rms','100uW_max_ESR140_requires_measurement')
add('HALL_ILIM_NOM',23950/(200**.977)/1000,'A','TI_typical_equation_200k')
add('HALL_ILIM_MIN',25230/(202**1.016)/1000,'A','200k_1pct_TI_min_equation')
add('HALL_ILIM_MAX',22980/(198**.94)/1000,'A','200k_1pct_TI_max_equation')
add('DC_LINK_C',1000e-6,'F','10_matching_hybrids')
add('DC_LINK_C_MIN',800e-6,'F','minus20pct')
add('DC_LINK_IRMS_NAMEPLATE',10*4.6*.75,'A_rms','125C_10kHz_factor_screening')
add('DC_LINK_I_EACH_AT16A',1.6,'A_rms','equal_sharing_screening')
add('DC_LINK_LOSS_AT16A',10*1.6**2*.017,'W','100kHz_ESR_proxy_requires_measurement')
add('DC_LINK_ENERGY_26_31',.5*.001*(31**2-26**2),'J','nominal_capacitance')
zh=(.017-1j/(2*math.pi*20000*100e-6))/6
ze=(.085-1j/(2*math.pi*20000*330e-6))/2
v=16*abs(1/(1/zh+1/ze))
add('REJECTED_MIXED_BANK_EACH_ELECTROLYTIC',v/(2*abs(ze)),'A_rms','20kHz_16A_max_ESR_proxy')
add('PRECHARGE_ENERGY_30V',.5*.001*30**2,'J','source_harness_precharge_required')
add('PRECHARGE_100R_INITIAL_30V',30/100,'A','external_precharge_resistor')
add('PRECHARGE_100R_5TAU',5*100*.001,'s','ignores_controller_load')
add('PRECHARGE_100R_MAX_LOAD_12V',12**2/(4*100),'W','constant_power_load_screen_startup_can_stall')
add('PRECHARGE_22R_MAX_LOAD_12V',12**2/(4*22),'W','still_measure_bus_before_bypass')
for lead_uH in (1,10,100):
    add('DUMP_LEAD_ENERGY_'+str(lead_uH)+'UH',.5*lead_uH*1e-6*16**2,'J','flyback_diode_pulse_and_average_loss_check')
w=csv.writer(sys.stdout,lineterminator='\n');w.writerow(['id','value','unit','basis']);w.writerows(rows)
