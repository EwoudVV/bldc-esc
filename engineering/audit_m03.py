import csv
import itertools
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from kicad_sexpr import child, parse

ROOT = Path(__file__).resolve().parent.parent
xml = ET.parse(ROOT / 'work/qa/bldc-esc.xml').getroot()
nets = {(p.get('ref'), p.get('pin')): n.get('name').split('/')[-1]
        for n in xml.findall('./nets/net') for p in n.findall('node')}
bom = {r['reference']: r for r in csv.DictReader((ROOT / 'engineering/schematic_bom.csv').open())}
errors = []
checked_pins = 0


def check(ok, name, *details):
    if not ok:
        errors.append([name, *details])


def pincheck(ref, expected):
    global checked_pins
    for pin, net in expected.items():
        actual = nets.get((ref, str(pin)))
        check(actual == net, 'PIN_NET', ref, pin, net, actual)
        checked_pins += 1


# These pin contracts are independent of circuits.py and its generated matrix.
# Sources and package drawings are indexed in sources.csv and review_m03.md.
contracts = {
    'U201': {1:'DRV_CPL',2:'DRV_CPH',3:'DRV_VM',4:'VBUS',5:'DRV_VCP',6:'GHA_DRV',7:'PHASE_A',
             8:'GLA_DRV',9:'SOURCE_A',10:'KS_A_N',11:'KS_B_N',12:'SOURCE_B',13:'GLB_DRV',14:'PHASE_B',
             15:'GHB_DRV',16:'GHC_DRV',17:'PHASE_C',18:'GLC_DRV',19:'SOURCE_C',20:'KS_C_N',
             21:'SO_C_DRV',22:'SO_B_DRV',23:'SO_A_DRV',24:'3V3_A',25:'GND',26:'DRV_nFAULT',
             27:'DRV_SDO',28:'DRV_SDI',29:'DRV_SCK',30:'DRV_nCS',31:'DRV_ENABLE',32:'IN_AH',
             33:'IN_AL',34:'IN_BH',35:'IN_BL',36:'IN_CH',37:'IN_CL',38:'DRV_DVDD',39:'GND',40:'DRV_VGLS',41:'GND'},
    'U301': {1:'nDUMP_REQUEST',2:'GND',3:'DUMP_HYST',4:'DUMP_VSENSE',6:'5V_BUS'},
    'U302': {1:'5V_BUS',2:'DUMP_GH',3:'DUMP_GL',4:'DUMP_SOURCE',5:'nDUMP_REQUEST',6:'BRK_ARMED'},
    'U303': {1:'DUMP_CURRENT',2:'GND',3:'DUMP_SOURCE',4:'GND',5:'5V_BUS'},
    'U304': {1:'BRK_OC_OK',2:'GND',3:'DUMP_REF',4:'DUMP_CURRENT',5:'5V_BUS'},
    'U305': {1:'BRK_POR',2:'GND',3:'5V_BUS',4:'BRK_CT',5:'5V_BUS',6:'5V_BUS'},
    'U306': {2:'BRK_CLK_RC',3:'GND',4:'BRK_CLK',5:'5V_BUS'},
    'U307': {1:'BRK_CLK',2:'5V_BUS',3:'nBRK_ARMED',4:'GND',5:'BRK_ARMED',6:'BRK_CLEAR',7:'5V_BUS',8:'5V_BUS'},
    'U308': {1:'DUMP_REF',2:'GND',3:'5V_BUS',4:'5V_BUS',5:'DUMP_REF_2V5'},
    'U401': {1:'GND',2:'VBUS',3:'BUCK_EN',4:'BUCK_RON',5:'BUCK_FB',6:'BUS_5V_GOOD',7:'BUCK_BST',8:'BUCK_SW',9:'GND'},
    'U402': {1:'GND',2:'5V_SYS',3:'5V_BUS',4:'MUX_PR1',5:'5V_BUS',6:'USB_5V',7:'5V_SYS',8:'PWR_BUS_SELECTED'},
    'U403': {1:'3V3',3:'GND',4:'5V_SYS',6:'5V_SYS',7:'GND'},
    'U404': {1:'USB_DP_PORT',2:'GND',3:'USB_DM_PORT',4:'USB_DM_ESD',5:'USB_VBUS_RAW',6:'USB_DP_ESD'},
    'U502': {1:'VBIAS_1V5',2:'GND',3:'3V3_A',4:'3V3_A',5:'VREF_3V0'},
    'U503': {1:'GND',2:'GND',3:'GND',4:'GND',5:'I2C_SDA',6:'I2C_SCL',7:'EEPROM_WP',8:'3V3'},
    'U701': {1:'POWER_OK',2:'GND',3:'3V3',4:'POR_CT',5:'3V3',6:'3V3'},
    'U702': {1:'3V3',2:'WD_CWD',3:'3V3',4:'GND',5:'WD_RUN',6:'WD_HEARTBEAT',7:'WD_OK',9:'GND'},
    'U703': {1:'NRST',2:'GND',3:'BUS_OK',4:'SYSTEM_GOOD_PRE',5:'3V3',6:'HW_ENABLE_OK'},
    'U704': {1:'SYSTEM_GOOD',2:'GND',3:'nOC_HW',4:'SAFETY_GOOD',5:'3V3',6:'DRV_nFAULT'},
    'U705': {1:'BRIDGE_ARM_REQ',2:'3V3',3:'nPWM_ENABLE',4:'GND',5:'nFAULT_LATCH',6:'SAFETY_GOOD',7:'3V3',8:'3V3'},
    'U706': {1:'nPWM_ENABLE',19:'nPWM_ENABLE',10:'GND',20:'3V3',2:'PWM_AH',18:'IN_AH',
             4:'PWM_AL',16:'IN_AL',6:'PWM_BH',14:'IN_BH',8:'PWM_BL',12:'IN_BL',11:'PWM_CH',9:'IN_CH',13:'PWM_CL',7:'IN_CL',15:'GND',17:'GND'},
    'U707': {1:'DRV_WAKE_REQ',2:'GND',3:'NRST',4:'DRV_ENABLE_PRE',5:'3V3',6:'BUS_OK'},
    'U708': {1:'DUMP_PWM',2:'GND',3:'NRST',4:'DUMP_PWM_SAFE',5:'3V3',6:'nFAULT_LATCH'},
    'U709': {1:'CAN_TX',2:'GND',3:'3V3',4:'CAN_RX',5:'3V3',6:'CAN_L',7:'CAN_H',8:'CAN_STB'},
    'U710': {2:'nHW_ENABLE_FILT',3:'GND',4:'HW_ENABLE_OK',5:'3V3'},
    'U711': {1:'SYSTEM_GOOD_PRE',2:'GND',3:'WD_RUN',4:'SYSTEM_GOOD',5:'3V3',6:'BRK_ARMED'},
    'U712': {1:'DRV_ENABLE_PRE',2:'GND',3:'WD_RUN',4:'DRV_ENABLE',5:'3V3',6:'BRK_ARMED'},
    'D301': {1:'VBUS',2:'DUMP_SW'}, 'Y501': {1:'HSE_IN',2:'HSE_XOUT'},
    'C203': {1:'DRV_CPH',2:'DRV_CPL'}, 'C204': {1:'DRV_VCP',2:'VBUS'},
    'C403': {1:'BUCK_BST',2:'BUCK_SW'},
    'J101': {1:'VBUS',2:'GND'}, 'J102': {1:'PHASE_A',2:'PHASE_B',3:'PHASE_C'},
    'J301': {1:'VBUS',2:'DUMP_SW'}, 'J701': {1:'GND',2:'CAN_H',3:'CAN_L'},
    'J702': {1:'GND',2:'UART_TX',3:'UART_RX',4:'3V3'},
    'J501': {1:'3V3',2:'SWDIO',3:'GND',4:'SWCLK',5:'GND',6:'SWO',9:'GND',10:'NRST'},
    'JP704': {1:'3V3',2:'WD_RUN',3:'GND'},
    'R701': {1:'NRST',2:'POWER_OK'}, 'R703': {1:'NRST',2:'WD_OK'},
    'U601': {1:'5V_SYS',2:'GND',3:'SENSOR_5V_EN',4:'SENSOR_nFAULT',5:'5V_HALL_ILIM',6:'5V_HALL'},
    'U602': {1:'5V_SYS',2:'GND',3:'ENCODER_5V_EN',4:'ENCODER_nFAULT',5:'5V_ENCODER_ILIM',6:'5V_ENCODER'},
    'U603': {1:'HALL_1_FILT',3:'HALL_2_FILT',6:'HALL_3_FILT',7:'HALL_1',5:'HALL_2',2:'HALL_3',8:'3V3',4:'GND'},
    'U604': {1:'ENC_A_FILT',3:'ENC_B_FILT',6:'ENC_Z_FILT',7:'ENC_A',5:'ENC_B',2:'ENC_Z',8:'3V3',4:'GND'},
    'U802': {1:'RC_PWM_RAW_FILT',3:'nBRAKE_RAW_FILT',6:'nDIR_RAW_FILT',7:'RC_PWM_IN',5:'nBRAKE_IN',2:'nDIR_IN',8:'3V3',4:'GND'},
    'U801': {1:'V_BUS_ADC_BUF',2:'V_BUS_ADC_BUF',3:'V_BUS_ADC_DIV',4:'3V3_A',5:'V_PHASE_A_DIV',6:'V_PHASE_A_BUF',7:'V_PHASE_A_BUF',
             8:'V_PHASE_B_BUF',9:'V_PHASE_B_BUF',10:'V_PHASE_B_DIV',11:'GND',12:'V_PHASE_C_DIV',13:'V_PHASE_C_BUF',14:'V_PHASE_C_BUF'},
}
for ref, pins in contracts.items():
    pincheck(ref, pins)
for ref in ['R701','R703']:
    check(bom[ref]['value']=='0','RESET_ZERO_OHM_LINK',ref)
check('D701' not in bom and 'D702' not in bom,'RESET_DIODE_DROP_REMOVED')

for i, phase in enumerate('ABC'):
    for ref, drain, source, gate in [('Q'+str(201+2*i),'VBUS','PHASE_'+phase,'G'+phase+'H'),
                                     ('Q'+str(202+2*i),'PHASE_'+phase,'SOURCE_'+phase,'G'+phase+'L')]:
        pincheck(ref, {1:source,2:source,3:source,4:gate,5:drain})
    pincheck('R'+str(214+20*i), {1:'SOURCE_'+phase,2:'KS_'+phase+'_P',3:'KS_'+phase+'_N',4:'GND'})
    pincheck('U'+str(202+i), {1:'KS_'+phase+'_N',2:'GND',3:'VBIAS_1V5',4:'GND',
                            5:'I_'+phase+'_RAW',6:'3V3_A',7:'VBIAS_1V5',8:'KS_'+phase+'_P'})
for ref, channels in [('U101', [('I_PHASE_A','OC_HI','nOC_HW'),('OC_LO','I_PHASE_A','nOC_HW'),
                               ('I_PHASE_B','OC_HI','nOC_HW'),('OC_LO','I_PHASE_B','nOC_HW')]),
                      ('U102', [('I_PHASE_C','OC_HI','nOC_HW'),('OC_LO','I_PHASE_C','nOC_HW'),
                               ('V_BUS_ADC','BUS_OV_REF','BUS_OK'),('OC_LO','V_BUS_ADC','BUS_OK')])]:
    pincheck(ref, {3:'3V3_A',12:'GND'})
    for (minus, plus, out), (m,p,o) in zip(channels,[(4,5,2),(6,7,1),(8,9,14),(10,11,13)]):
        pincheck(ref, {m:minus,p:plus,o:out})
    check(bom[ref]['MPN']=='TLV9024PWR', 'COMPARATOR_VOL_GUARANTEE', ref)
for ref, channels in [('U803',['THROTTLE_ADC','AUX_ANALOG_ADC']),('U804',['NTC_MOTOR','NTC_DUMP'])]:
    pincheck(ref, {4:'GND',8:'3V3_A'})
    for n, (out,minus,plus) in zip(channels, [(1,2,3),(7,6,5)]):
        pincheck(ref, {out:n+'_BUF',minus:n+'_BUF',plus:n+'_DIV'})

protected = {'nOC_HW','BUS_OK','DRV_nFAULT','nHW_ENABLE_FILT','WD_RUN','nFAULT_LATCH','BRK_ARMED'}
check(not protected.intersection(n for (r,p),n in nets.items() if r=='U501'), 'GPIO_ISOLATION')
for ref, raw, sense in [('R707','nOC_HW','nOC_HW_SENSE'),('R708','BUS_OK','BUS_OK_SENSE'),
                       ('R709','nFAULT_LATCH','nFAULT_LATCH_SENSE'),('R723','WD_RUN','WD_RUN_SENSE'),
                       ('R724','nHW_ENABLE_FILT','nHW_ENABLE_SENSE'),('R725','DRV_nFAULT','DRV_nFAULT_SENSE')]:
    pincheck(ref,{1:raw,2:sense})

gate_refs = ['U703','U711','U704','U707','U712','U708']
def gates(signals):
    result = dict(signals)
    for ref in gate_refs:
        if all(nets[(ref,str(p))] in result for p in (1,3,6)):
            result[nets[(ref,'4')]] = all(result[nets[(ref,str(p))]] for p in (1,3,6))
    return result

cases = 0
names = ['NRST','BUS_OK','HW_ENABLE_OK','WD_RUN','BRK_ARMED','nOC_HW','DRV_nFAULT','DRV_WAKE_REQ']
for values in itertools.product((False,True), repeat=len(names)):
    inputs = dict(zip(names,values)); derived = gates(inputs)
    expected_safe = all(values[:7])
    check(derived['SAFETY_GOOD']==expected_safe,'GATE_TRUTH',inputs)
    check(derived['DRV_ENABLE']==all(inputs[k] for k in ['DRV_WAKE_REQ','NRST','BUS_OK','WD_RUN','BRK_ARMED']), 'DRIVER_TRUTH',inputs)
    for old_q, old_clk, clk in itertools.product((False,True), repeat=3):
        q = False if not derived['SAFETY_GOOD'] else (old_q or (clk and not old_clk))
        for pwm in (False, True):
            gate_output = pwm and q
            check(not gate_output or expected_safe,'FAULT_MUST_BLOCK_PWM',inputs)
            cases += 1

q=False; previous=False
for safe,clk,want in [(0,0,0),(1,0,0),(1,1,1),(0,1,0),(1,1,0),(1,0,0),(1,1,1)]:
    q=False if not safe else (q or (clk and not previous));previous=clk
    check(q==bool(want),'REARM_EDGE_REQUIRED',safe,clk)
project=json.loads((ROOT/'bldc-esc.kicad_pro').read_text())
cls=next(c for c in project['net_settings']['classes'] if c['name']=='Default')
check(cls.get('wire_width',0)>0 and cls.get('bus_width',0)>0,'VISIBLE_SCHEMATIC_NETCLASS')
check(project['board']['design_settings']['rules']['min_hole_clearance']>=.2,'PCBWAY_NPTH_RULE')
fp=parse((ROOT/'bldc-esc.pretty/USB4105_PCBWay.kicad_mod').read_text())
for pad in (n for n in fp if isinstance(n,list) and n and n[0]=='pad' and n[1] in ['A1','A12','B1','B12']):
    check(float(child(pad,'roundrect_rratio')[1])==.5,'USB_GROUND_PAD_RADIUS',pad[1])

print(json.dumps({'passed':not errors,'independent_pin_contracts':checked_pins,
                  'logic_cases':cases,'scope':'static_pin_logic_and_geometry_not_analog_timing_or_hardware',
                  'errors':errors},indent=2))
sys.exit(bool(errors))
