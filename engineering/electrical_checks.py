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
add('DUMP_OC',1.242/(0.003*20),'A','nominal')
scale=(200000+8450)/8450
high=(1.242/10000+5/2490000)/(1/10000+1/2490000)
low=(1.242/10000+0.1/2490000)/(1/10000+1/2490000)
add('DUMP_ON',high*scale,'V','reference1V242_output5V')
add('DUMP_OFF',low*scale,'V','output0V1')
limits=[]
for vref,offset,rt,rb,rr,rf,vo in product([1.242*.99,1.242*1.01],[-.012,.012],
    [200000*.999,200000*1.001],[8450*.999,8450*1.001],
    [10000*.999,10000*1.001],[2490000*.99,2490000*1.01],[4.8,5.2]):
    threshold=(vref/rr+vo/rf)/(1/rr+1/rf)+offset
    limits.append(threshold*(rt+rb)/rb)
add('DUMP_ON_CORNER_MIN',min(limits),'V','1pct_ref_12mV_offset_0p1pct_divider_1pct_feedback')
add('DUMP_ON_CORNER_MAX',max(limits),'V','same_corner_model_not_dynamic_validation')
vout=1.2*(1+324000/100000)
freq=vout*2500/42.2*1000
add('BUCK_SETPOINT',vout,'V','before_ripple_injection_offset')
add('BUCK_FREQUENCY',freq,'Hz','RON42k2')
for vin in (12,26,30,50):
    delta=vout/(freq*68e-6)*(1-vout/vin)
    add('BUCK_IL_RIPPLE_'+str(vin),delta,'A_pp','68uH_nominal_CCM')
    add('BUCK_FB_RIPPLE_'+str(vin),vout/(vin*freq)*(vin-vout)/(301000*2.2e-9),'V_pp','type3_screening')
add('USB_SENSE_AT_4V4',4.4*150/250,'V','Rtop100k_Rbottom150k')
add('USB_SENSE_AT_5V25',5.25*150/250,'V','Rtop100k_Rbottom150k')
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
w=csv.writer(sys.stdout,lineterminator='\n');w.writerow(['id','value','unit','basis']);w.writerows(rows)
