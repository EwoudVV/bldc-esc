import csv
import itertools
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
bom = {r['reference']: r for r in csv.DictReader((ROOT/'engineering/schematic_bom.csv').open())}


def value(ref):
    s = bom[ref]['value'].split()[0]
    suffix = s[-1]
    return float(s[:-1]) * {'p':1e-12,'n':1e-9,'u':1e-6,'m':1e-3,'k':1e3,'M':1e6}[suffix] if suffix.isalpha() else float(s)


def calculate():
    assert bom['U502']['MPN'] == 'REF2025AIDDCR'
    assert bom['U403']['MPN'] == 'TLV75801PDRVR'
    assert bom['U701']['MPN'] == 'TPS389033DSER'
    assert bom['FB501']['MPN'] == 'BLM18KG601SN1D'
    vref=2.5; bias=1.25; scale=.001*20
    vnom=.55*(1+value('R417')/value('R418'))
    # Full-temperature resistor budget: 0.1% initial plus 25ppm/C over 100C.
    rerr=.001+25e-6*100
    ifb_error=100e-9*value('R417')*(1+rerr)
    # Load allowance is a design budget, not a guaranteed regulator specification.
    load_allowance=.020
    line_max=.0075
    vlo=.55*.985*(1+value('R417')*(1-rerr)/(value('R418')*(1+rerr)))-ifb_error-line_max-load_allowance
    vhi=.55*1.015*(1+value('R417')*(1+rerr)/(value('R418')*(1-rerr)))+ifb_error+line_max+load_allowance
    analog_budget=.100
    bead_hot_model=.165*1.4
    analog_min=vlo-analog_budget*bead_hot_model
    ref_error=.0005+8e-6*100+35e-6*(5-3.1)+20e-6*20
    ref_max=vref*(1+ref_error)
    ref_min=vref*(1-ref_error)
    minimum_ref_supply=ref_max+.600
    reset_fall_min=3.17*.99
    reset_rise_max=3.189*1.01
    cct=value('C702')
    delay_typ=cct*1e6*1.07+25e-6
    delay_max_screen=cct*1.10*1.15*1.29/.90e-6+25e-6
    # VREF load budgets include NTC short circuits and all three trip dividers.
    fixed_ref_load=ref_max/value('R501')+sum(ref_max/value(r) for r in ['R880','R883','R886','R889'])
    for a,b in [('R110','R111'),('R112','R113'),('R114','R115'),('R118','R119')]:
        fixed_ref_load+=ref_max/(value(a)+value(b))
    adc_ref_budget=.010
    i_hi=(vref*value('R111')/(value('R110')+value('R111'))-bias)/scale
    i_lo=(bias-vref*value('R113')/(value('R112')+value('R113')))/scale
    bus_ratio=(value('R801')+value('R802')+value('R803'))/value('R803')
    uv=vref*value('R119')/(value('R118')+value('R119'))*bus_ratio
    ov=vref*value('R115')/(value('R114')+value('R115'))*bus_ratio
    throttle_max=5.3*value('R851')*1.01/(value('R850')*.99+value('R851')*1.01)+.002
    usb_min=4.4*value('R416')*.99/(value('R415')*1.01+value('R416')*.99)
    usb_min-=4.5e-6*(value('R415')*1.01*value('R416')*.99/(value('R415')*1.01+value('R416')*.99))
    checks={
        'reference_headroom_normal_budget':analog_min>minimum_ref_supply,
        'reference_headroom_at_static_reset_threshold':reset_fall_min>minimum_ref_supply,
        'reset_release_below_normal_rail_budget':analog_min>reset_rise_max,
        'logic_rail_below_3V6':vhi<3.6,
        'primary_40A_inside_ADC':bias-40*scale>.2 and bias+40*scale<ref_min-.2,
        'external_trip_approximately_50A':49<i_hi<51 and 49<i_lo<51,
        'bus_thresholds_retained':10.3<uv<10.7 and 32.8<ov<33.2,
        'throttle_at_5V3_with_tolerances':throttle_max<ref_min,
        'bus_at_50V_with_tolerances':50/(1+200000*.999/(10000*1.001))+.002<ref_min,
        'DRV_diagnostic_gain10_at_50A':vhi/2+.5+.030<ref_min,
        'USB_sense_logic_high_at_4V4':usb_min>.7*vhi,
        'reference_output_load_budget':fixed_ref_load+adc_ref_budget<.020,
        'POR_delay_leaves_healthy_boot_time':.170-delay_max_screen>.050,
    }
    return {'passed':all(checks.values()),'scope':'static_datasheet_corners_and_explicit_load_budgets_not_transient_validation',
        'checks':checks,'results':{
            'logic_nominal_V':vnom,'logic_budget_min_V':vlo,'logic_budget_max_V':vhi,
            'analog_load_budget_A':analog_budget,'bead_hot_resistance_model_ohm':bead_hot_model,
            'analog_supply_budget_min_V':analog_min,'reference_output_max_V':ref_max,
            'reference_guaranteed_loaded_supply_min_V':minimum_ref_supply,
            'reference_normal_headroom_margin_V':analog_min-minimum_ref_supply,
            'reset_assert_min_V':reset_fall_min,'reset_release_max_V':reset_rise_max,
            'reset_static_reference_margin_V':reset_fall_min-minimum_ref_supply,
            'reset_startup_budget_margin_V':analog_min-reset_rise_max,
            'reset_delay_typ_s':delay_typ,'reset_delay_high_screen_s':delay_max_screen,
            'watchdog_minimum_remaining_boot_s':.170-delay_max_screen,
            'reference_fixed_load_max_A':fixed_ref_load,'ADC_reference_load_budget_A':adc_ref_budget,
            'current_mA_per_LSB':vref/4096/scale*1000,'positive_trip_A':i_hi,'negative_trip_magnitude_A':i_lo,
            'bus_UV_V':uv,'bus_OV_V':ov,'phase_voltage_ADC_fullscale_V':vref*bus_ratio,
            'throttle_nominal_divider_gain':value('R851')/(value('R850')+value('R851')),
            'throttle_max_ADC_V':throttle_max,'USB_sense_high_margin_V':usb_min-.7*vhi,
            'reference_capacitor_energy_J':.5*(value('C510')+value('C511'))*ref_max**2}}


if __name__=='__main__':
    result=calculate()
    print(json.dumps(result,indent=2))
    raise SystemExit(not result['passed'])
