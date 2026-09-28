import csv


def build(c):
    p,R,C,D,TP,CON=c.part,c.R,c.C,c.D,c.TP,c.CON
    sot5='Package_TO_SOT_SMD:SOT-23-5'
    sot6='Package_TO_SOT_SMD:SOT-23-6'
    vssop8='Package_SO:VSSOP-8_2.3x2mm_P0.5mm'
    fetfp='Package_SON:Infineon_PG-TDSON-8_6.15x5.15mm'
    gh=lambda n:'Connector_JST:JST_GH_BM%02dB-GHS-TBT_1x%02d-1MP_P1.25mm_Vertical'%(n,n)

    s='01_dc_link'
    CON(s,'J101','XT60PW-M',65,70,['GND','VBUS'],'Connector_AMASS:AMASS_XT60PW-M_1x02_P7.20mm_Horizontal','XT60PW-M')
    D(s,'D101','SMCJ30A',125,70,'GND','VBUS','Diode_SMD:D_SMC','Device:D_Zener')
    for i in range(6):
        p(s,'C'+str(101+i),'Device:C_Polarized','100u 63V',200+55*i,70,{1:'VBUS',2:'GND'},
          'Capacitor_SMD:CP_Elec_10x12.5','GXC1J101MCW1GS','Nichicon')
    for i in range(2):
        p(s,'C'+str(107+i),'Device:C_Polarized','100u 63V',65+60*i,150,{1:'VBUS',2:'GND'},
          'Capacitor_SMD:CP_Elec_10x12.5','GXC1J101MCW1GS','Nichicon')
        p(s,'C'+str(115+i),'Device:C_Polarized','100u 63V',65+60*i,230,{1:'VBUS',2:'GND'},
          'Capacitor_SMD:CP_Elec_10x12.5','GXC1J101MCW1GS','Nichicon')
    R(s,'R101','10k',220,150,'VBUS','GND','1206')
    CON(s,'J102','MT60 / 12AWG pigtail',340,150,['PHASE_A','PHASE_B','PHASE_C'],'bldc-esc:MT60_Pigtail_12AWG','MT60-M')
    CON(s,'J103','CHASSIS',490,150,['CHASSIS','GND'],'Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical','M20-9990245')
    R(s,'R102','1M',420,230,'CHASSIS','GND')
    C(s,'C109','4.7n 1kV',480,230,'CHASSIS','GND','1206','C1206C472KDRACTU')
    R(s,'R103','0',540,230,'CHASSIS','GND',dnp=True)
    for i,(net,x) in enumerate([('VBUS',65),('GND',125),('PHASE_A',220),('PHASE_B',285),('PHASE_C',350)],1):
        TP(s,'TP'+str(100+i),net,x,305)
    for i,net in enumerate(['VBUS','GND'],1):p(s,'#FLG'+str(100+i),'power:PWR_FLAG','PWR_FLAG',65+60*i,345,{1:net})
    c.notes[s]+=[(25,38,'12-30V / external DC fuse at source'),(25,190,'10 x 100uF hybrids; 4.6Arms each @ 125C / 100kHz. Thermal checks still needed.'),
        (25,370,'MT60 cable: 1=A / 2=B / 3=C. Add cable strain relief during placement.')]

    s='02_bridge'
    p(s,'U201','bldc-esc:DRV8353S','DRV8353SRTAT',90,110,{
        1:'DRV_CPL',2:'DRV_CPH',3:'DRV_VM',4:'VBUS',5:'DRV_VCP',6:'GHA_DRV',7:'PHASE_A',8:'GLA_DRV',9:'SOURCE_A',10:'KS_A_N',
        11:'KS_B_N',12:'SOURCE_B',13:'GLB_DRV',14:'PHASE_B',15:'GHB_DRV',16:'GHC_DRV',17:'PHASE_C',18:'GLC_DRV',19:'SOURCE_C',20:'KS_C_N',
        21:'SO_C_DRV',22:'SO_B_DRV',23:'SO_A_DRV',24:'3V3_A',25:'GND',26:'DRV_nFAULT',27:'DRV_SDO',28:'DRV_SDI',29:'DRV_SCK',30:'DRV_nCS',
        31:'DRV_ENABLE',32:'IN_AH',33:'IN_AL',34:'IN_BH',35:'IN_BL',36:'IN_CH',37:'IN_CL',38:'DRV_DVDD',39:'GND',40:'DRV_VGLS',41:'GND'},
        'bldc-esc:DRV8353_RTA0040B','DRV8353SRTAT','Texas Instruments')
    R(s,'R201','2.2',45,205,'VBUS','DRV_VM','0805')
    p(s,'C201','Device:C_Polarized','22u 63V',90,205,{1:'DRV_VM',2:'GND'},'Capacitor_THT:CP_Radial_D6.3mm_P2.50mm','EEUFC1J220','Panasonic')
    C(s,'C202','100n 100V',135,205,'DRV_VM','GND','0603','C0603C104K1RACTU')
    C(s,'C203','47n 100V',45,260,'DRV_CPH','DRV_CPL','0805','C0805C473K1RACTU')
    C(s,'C204','1u 50V',90,260,'DRV_VCP','VBUS','1206','C3216X7R1H105K160AB')
    C(s,'C205','1u 25V',135,260,'DRV_VGLS','GND','0805','C0805C105K3RACTU')
    C(s,'C206','1u 16V',45,315,'DRV_DVDD','GND','0603','C0603C105K4RACTU')
    C(s,'C207','100n 50V',90,315,'3V3_A')
    R(s,'R202','4.7k',135,315,'3V3','DRV_SDO')
    R(s,'R203','10k',45,365,'3V3','DRV_nFAULT')
    R(s,'R204','100k',90,365,'DRV_ENABLE','GND')
    R(s,'R205','10k',135,365,'3V3','DRV_nCS')
    for i,phase in enumerate('ABC'):
        x=250+145*i; b=210+20*i
        p(s,'Q'+str(201+2*i),'bldc-esc:ISC011N06LM5','ISC011N06LM5',x,70,{1:'PHASE_'+phase,2:'PHASE_'+phase,3:'PHASE_'+phase,4:'G'+phase+'H',5:'VBUS'},fetfp,'ISC011N06LM5ATMA1','Infineon')
        p(s,'Q'+str(202+2*i),'bldc-esc:ISC011N06LM5','ISC011N06LM5',x,140,{1:'SOURCE_'+phase,2:'SOURCE_'+phase,3:'SOURCE_'+phase,4:'G'+phase+'L',5:'PHASE_'+phase},fetfp,'ISC011N06LM5ATMA1','Infineon')
        R(s,'R'+str(b),'3.3',x-55,70,'GH'+phase+'_DRV','G'+phase+'H',angle=90)
        R(s,'R'+str(b+1),'47k',x+40,70,'G'+phase+'H','PHASE_'+phase)
        R(s,'R'+str(b+2),'3.3',x-55,140,'GL'+phase+'_DRV','G'+phase+'L',angle=90)
        R(s,'R'+str(b+3),'47k',x+40,140,'G'+phase+'L','SOURCE_'+phase)
        p(s,'R'+str(b+4),'Device:R_Shunt','1m 1% 8W',x,200,{1:'SOURCE_'+phase,2:'KS_'+phase+'_P',3:'KS_'+phase+'_N',4:'GND'},'bldc-esc:CSS4J_4026','CSS4J-4026R-1L00F','Bourns')
        C(s,'C'+str(b),'1u 100V',x-50,200,'VBUS','GND','1206','C3216X7R2A105K160AA')
        C(s,'C'+str(b+1),'1u 100V',x+45,200,'VBUS','GND','1206','C3216X7R2A105K160AA')
        p(s,'U'+str(202+i),'Amplifier_Current:INA241A2xDGK','INA241A2IDGKR',x,275,{1:'KS_'+phase+'_N',2:'GND',3:'VBIAS_1V25',4:'GND',5:'I_'+phase+'_RAW',6:'3V3_A',7:'VBIAS_1V25',8:'KS_'+phase+'_P'},
          'Package_SO:VSSOP-8_3x3mm_P0.65mm','INA241A2IDGKR','Texas Instruments')
        C(s,'C'+str(b+2),'100n 50V',x-50,275,'3V3_A')
        R(s,'R'+str(b+5),'100',x-50,330,'I_'+phase+'_RAW','I_PHASE_'+phase,angle=90)
        C(s,'C'+str(b+3),'1n 50V',x,330,'I_PHASE_'+phase,'GND','0603','C0603C102J5GACTU')
        TP(s,'TP'+str(210+i),'I_PHASE_'+phase,x+50,330)
        R(s,'R'+str(b+6),'1k',x-50,380,'SO_'+phase+'_DRV','I_DRV_'+phase,angle=90)
        C(s,'C'+str(b+4),'1n 50V',x,380,'I_DRV_'+phase,'GND','0603','C0603C102J5GACTU')
        R(s,'R'+str(b+7),'10',x+35,25,'PHASE_'+phase,'SNUB_'+phase,'0805',dnp=True)
        C(s,'C'+str(b+5),'1n 100V',x+70,25,'SNUB_'+phase,'GND','0805','C0805C102J1GACTU',dnp=True)
    c.notes[s]+=[(180,240,'Kelvin pads: 1=I+ / 2=V+ / 3=V- / 4=I-'),(180,400,'CSA: 1.25V zero / 20mV per A. SPx gate return stays direct to low-side source.')]

    s='04_power_usb'
    p(s,'U401','Regulator_Switching:LM5164DDA','LM5164DDAR',90,75,{1:'GND',2:'VBUS',3:'BUCK_EN',4:'BUCK_RON',5:'BUCK_FB',6:'BUS_5V_GOOD',7:'BUCK_BST',8:'BUCK_SW',9:'GND'},mpn='LM5164DDAR',manufacturer='Texas Instruments')
    R(s,'R401','300k',30,140,'VBUS','BUCK_EN')
    R(s,'R402','100k',70,140,'BUCK_EN','GND')
    R(s,'R403','42.2k',110,140,'BUCK_RON','GND')
    C(s,'C401','2.2u 100V',30,195,'VBUS','GND','1210','CGA6N3X7R2A225K230AB')
    C(s,'C402','2.2u 100V',70,195,'VBUS','GND','1210','CGA6N3X7R2A225K230AB')
    C(s,'C403','2.2n 50V',150,75,'BUCK_BST','BUCK_SW','0603','C0603C222J5GACTU')
    p(s,'L401','Device:L','68uH / Isat>=2.3A',215,75,{1:'BUCK_SW',2:'5V_BUS'},'Inductor_SMD:L_Coilcraft_MSS1246T-XXX','MSS1246T-683MLC','Coilcraft',90)
    C(s,'C404','22u 25V',260,75,'5V_BUS','GND','1210','MSAST32MSB7226KPNB25')
    C(s,'C405','22u 25V',305,75,'5V_BUS','GND','1210','MSAST32MSB7226KPNB25')
    R(s,'R404','324k',170,140,'5V_BUS','BUCK_FB',precision=True)
    R(s,'R405','100k',215,140,'BUCK_FB','GND',precision=True)
    R(s,'R406','301k',260,140,'BUCK_SW','BUCK_RIPPLE')
    C(s,'C406','2.2n 50V',305,140,'BUCK_RIPPLE','5V_BUS','0603','C0603C222J5GACTU')
    C(s,'C407','82p 50V',260,195,'BUCK_RIPPLE','BUCK_FB','0603','C0603C820J5GACTU')
    R(s,'R407','10k',305,195,'3V3','BUS_5V_GOOD')
    p(s,'U402','Power_Management:TPS2116DRL','TPS2116DRLR',415,75,{1:'GND',2:'5V_SYS',3:'5V_BUS',4:'MUX_PR1',5:'5V_BUS',6:'USB_5V',7:'5V_SYS',8:'PWR_BUS_SELECTED'},mpn='TPS2116DRLR',manufacturer='Texas Instruments')
    R(s,'R408','300k',370,145,'5V_BUS','MUX_PR1')
    R(s,'R409','100k',415,145,'MUX_PR1','GND')
    R(s,'R410','10k',460,145,'3V3','PWR_BUS_SELECTED')
    C(s,'C408','1u 16V',370,195,'5V_BUS','GND','0603','C0603C105K4RACTU')
    C(s,'C409','1u 16V',415,195,'USB_5V','GND','0603','C0603C105K4RACTU')
    C(s,'C410','4.7u 25V',460,195,'5V_SYS','GND','0805','C0805C475K3RACTU')
    p(s,'U403','Regulator_Linear:TLV75801PDRV','TLV75801PDRVR',520,75,{1:'3V3',2:'VDD_FB',3:'GND',4:'5V_SYS',5:None,6:'5V_SYS',7:'GND'},mpn='TLV75801PDRVR',manufacturer='Texas Instruments')
    R(s,'R417','51.1k',560,170,'3V3','VDD_FB',precision=True)
    R(s,'R418','10k',560,210,'VDD_FB','GND',precision=True)
    C(s,'C411','1u 16V',520,145,'5V_SYS','GND','0603','C0603C105K4RACTU')
    C(s,'C412','4.7u 25V',560,145,'3V3','GND','0805','C0805C475K3RACTU')
    c.box_symbol('USB_C_16P',[("A4",'VBUS','passive'),('A9','VBUS','passive'),('B4','VBUS','passive'),('B9','VBUS','passive'),('A5','CC1','passive'),('B5','CC2','passive'),('A8','SBU1','passive'),('B8','SBU2','passive')],
        [('A6','D+','passive'),('B6','D+','passive'),('A7','D-','passive'),('B7','D-','passive'),('A1','GND','passive'),('A12','GND','passive'),('B1','GND','passive'),('B12','GND','passive'),('SH','SHIELD','passive')],25.4)
    p(s,'J401','bldc-esc:USB_C_16P','USB4105-GF-A',75,295,{'A4':'USB_VBUS_RAW','A9':'USB_VBUS_RAW','B4':'USB_VBUS_RAW','B9':'USB_VBUS_RAW',
        'A5':'CC1','B5':'CC2','A8':None,'B8':None,'A6':'USB_DP_PORT','B6':'USB_DP_PORT','A7':'USB_DM_PORT','B7':'USB_DM_PORT',
        'A1':'GND','A12':'GND','B1':'GND','B12':'GND','SH':'CHASSIS'},'bldc-esc:USB4105_PCBWay','USB4105-GF-A','GCT')
    R(s,'R411','5.1k',155,260,'CC1','GND')
    R(s,'R412','5.1k',205,260,'CC2','GND')
    p(s,'F401','Device:Polyfuse','0.5A / 6V',160,325,{1:'USB_VBUS_RAW',2:'USB_5V'},'bldc-esc:MF_PSMF0805','MF-PSMF050X-2','Bourns',90)
    C(s,'C413','100n 50V',205,325,'USB_VBUS_RAW')
    p(s,'U404','Power_Protection:USBLC6-2SC6','USBLC6-2SC6',305,285,{1:'USB_DP_PORT',2:'GND',3:'USB_DM_PORT',4:'USB_DM_ESD',5:'USB_VBUS_RAW',6:'USB_DP_ESD'},mpn='USBLC6-2SC6',manufacturer='STMicroelectronics')
    R(s,'R413','22',390,270,'USB_DP_ESD','USB_DP',angle=90)
    R(s,'R414','22',390,315,'USB_DM_ESD','USB_DM',angle=90)
    R(s,'R415','10k',465,270,'USB_VBUS_RAW','USB_VBUS_SENSE')
    R(s,'R416','15k',510,270,'USB_VBUS_SENSE','GND')
    for i,(net,x) in enumerate([('5V_BUS',260),('5V_SYS',330),('3V3',400),('GND',470)],1):TP(s,'TP'+str(400+i),net,x,375)
    for i,net in enumerate(['5V_BUS','USB_VBUS_RAW','USB_5V'],1):p(s,'#FLG'+str(400+i),'power:PWR_FLAG','PWR_FLAG',40+60*i,380,{1:net})
    c.notes[s]+=[(25,38,'LM5164: about 5V / 300kHz / type-3 ripple injection'),(355,235,'USB-only: sensors off at boot; bridge stays disarmed')]

    s='05_mcu'
    pinmap=list(csv.DictReader((c.ROOT/'engineering/pinmap.csv').open()))
    pin_nets={int(r['pin']):None if r['net']=='NC' else r['net'] for r in pinmap}
    p(s,'U501','MCU_ST_STM32G4:STM32G474VETx','STM32G474VET6',135,160,pin_nets,mpn='STM32G474VET6',manufacturer='STMicroelectronics')
    for i in range(5):C(s,'C'+str(501+i),'100n 50V',45+40*i,300,'3V3')
    C(s,'C506','4.7u 25V',245,300,'3V3','GND','0805','C0805C475K3RACTU')
    p(s,'FB501','Device:FerriteBead','600R @ 100MHz',295,75,{1:'3V3',2:'3V3_A'},'Inductor_SMD:L_0603_1608Metric','BLM18KG601SN1D','Murata',90)
    C(s,'C507','4.7u 25V',350,75,'3V3_A','GND','0805','C0805C475K3RACTU')
    C(s,'C508','100n 50V',395,75,'3V3_A')
    p(s,'U502','Reference_Voltage:REF2025','REF2025AIDDCR',310,155,{1:'VBIAS_1V25',2:'GND',3:'3V3_A',4:'3V3_A',5:'VREF_2V5'},mpn='REF2025AIDDCR',manufacturer='Texas Instruments')
    C(s,'C509','100n 50V',250,155,'3V3_A')
    C(s,'C510','1u 16V',375,145,'VREF_2V5','GND','0603','C0603C105K4RACTU')
    C(s,'C511','100n 50V',420,145,'VREF_2V5')
    C(s,'C512','100n 50V',375,205,'VBIAS_1V25')
    R(s,'R501','1k',420,205,'VREF_2V5','GND')
    D(s,'D501','PMEG2010ER',465,145,'VREF_2V5','3V3_A','Diode_SMD:Nexperia_CFP3_SOD-123W')
    p(s,'Y501','Device:Crystal','8MHz / CL18p',310,240,{1:'HSE_IN',2:'HSE_XOUT'},'Crystal:Crystal_SMD_Abracon_ABM3-2Pin_5.0x3.2mm','ABM3-8.000MHZ-D2Y-T','Abracon')
    R(s,'R502','0',245,240,'HSE_OUT','HSE_XOUT',angle=90)
    C(s,'C513','27p 50V',375,260,'HSE_IN','GND','0603','C0603C270J5GACTU')
    C(s,'C514','27p 50V',420,260,'HSE_XOUT','GND','0603','C0603C270J5GACTU')
    R(s,'R503','100k',470,260,'BOOT0','GND')
    CON(s,'JP501','BOOT0',525,260,['BOOT0','3V3'],'Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical','M20-9990245')
    p(s,'SW501','Switch:SW_Push','RESET',310,330,{1:'NRST',2:'GND'},'Button_Switch_SMD:SW_SPST_TL3342','TL3342F160QG','E-Switch')
    C(s,'C515','100n 50V',375,330,'NRST')
    R(s,'R504','10k',420,330,'3V3','NRST')
    p(s,'SW502','Switch:SW_Push','USER',470,330,{1:'BUTTON_USER',2:'GND'},'Button_Switch_SMD:SW_SPST_TL3342','TL3342F160QG','E-Switch')
    R(s,'R505','10k',525,330,'3V3','BUTTON_USER')
    p(s,'J501','bldc-esc:SWD10_Keyed','SWD / KEY 7',500,75,{1:'3V3',2:'SWDIO',3:'GND',4:'SWCLK',5:'GND',6:'SWO',8:None,9:'GND',10:'NRST'},
      'bldc-esc:FTSH_105_DV_007_K','FTSH-105-01-L-DV-007-K','Samtec')
    for i,(net,x) in enumerate([('VREF_2V5',45),('VBIAS_1V25',105),('3V3_A',165),('ADC_TRIG_SCOPE',245),('DAC1_CH1_TP',335),('DAC1_CH2_TP',425)],1):TP(s,'TP'+str(500+i),net,x,380)
    p(s,'#FLG501','power:PWR_FLAG','PWR_FLAG',530,200,{1:'3V3_A'})
    c.notes[s]+=[(230,38,'PB8=BOOT0 / PA15=I2C1_SCL / PG10=NRST'),(230,110,'VREF=2.5V below VDDA; reference supply follows 3V3_A')]

    build_regen(c)
    build_sensors(c)
    build_io(c)
    p('02_bridge','#FLG201','power:PWR_FLAG','PWR_FLAG',40,180,{1:'DRV_VM'})
    p('03_regen','#FLG301','power:PWR_FLAG','PWR_FLAG',540,235,{1:'DUMP_SOURCE'})
    reorganize(c)
    build_m03(c)


def build_m03(c):
    p,R,C,D,TP=c.part,c.R,c.C,c.D,c.TP
    for item in c.parts:
        if item['ref']!='U501':
            item['nets']={pin:('nHW_ENABLE_FILT' if net=='nHW_ENABLE_SENSE' else net) for pin,net in item['nets'].items()}
    for ref,value,raw,sense in [('R707','100k','nOC_HW','nOC_HW_SENSE'),
        ('R708','100k','BUS_OK','BUS_OK_SENSE'),('R709','1k','nFAULT_LATCH','nFAULT_LATCH_SENSE'),
        ('R723','10k','WD_RUN','WD_RUN_SENSE'),('R724','100k','nHW_ENABLE_FILT','nHW_ENABLE_SENSE'),
        ('R725','100k','DRV_nFAULT','DRV_nFAULT_SENSE')]:
        R('09_safety',ref,value,20,20,raw,sense,angle=90)
    c.box_symbol('TLV9062',[(8,'V+','power_in'),(3,'IN1+','input'),(2,'IN1-','input'),
        (5,'IN2+','input'),(6,'IN2-','input')],[(1,'OUT1','output'),(7,'OUT2','output'),(4,'V-','power_in')])
    pairs=[('U803',['THROTTLE_ADC','AUX_ANALOG_ADC'],[852,857],'C847'),
           ('U804',['NTC_MOTOR','NTC_DUMP'],[888,891],'C848')]
    for ref,signals,numbers,decap in pairs:
        nets={4:'GND',8:'3V3_A'}
        for i,(net,num) in enumerate(zip(signals,numbers)):
            for item in c.parts:
                if item['ref']=='U501':continue
                item['nets']={pin:(net+'_DIV' if value==net else value) for pin,value in item['nets'].items()}
                if item['value']=='BAT54S' and item['nets'].get('3')==net+'_DIV':
                    item['lib_id']='Device:D_Dual_Series_AKC'
                    item['node']=c.symbol(item['lib_id'])
                    item['value']='BAV199';item['mpn']='BAV199,215'
                    item['datasheet']='https://assets.nexperia.com/documents/data-sheet/BAV199.pdf'
            plus,minus,out=[(3,2,1),(5,6,7)][i]
            nets[plus]=net+'_DIV';nets[minus]=net+'_BUF';nets[out]=net+'_BUF'
            R('08_analog_inputs','R'+str(num),'100',20,20,net+'_BUF',net,angle=90)
            C('08_analog_inputs','C'+str(num),'1n 50V',30,30,net,'GND','0603','C0603C102J5GACTU')
            D('08_analog_inputs','D'+str(num),'PESD5V0S1BA',40,40,'GND',net+'_IN','Diode_SMD:D_SOD-323','Device:D_TVS')
        p('08_analog_inputs',ref,'bldc-esc:TLV9062','TLV9062IDR',50,50,nets,
            'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm','TLV9062IDR','Texas Instruments')
        C('08_analog_inputs',decap,'100n 50V',60,60,'3V3_A')
    C('07_io_can','C706','1u 16V',70,70,'3V3','GND','0603','C0603C105K4RACTU')
    for i,phase in enumerate('ABC'):
        for offset,net in enumerate(['G'+phase+'H','G'+phase+'L','SOURCE_'+phase]):
            TP('02_bridge','TP'+str(220+20*i+offset),net,10,10)


def build_regen(c):
    p,R,C,D,TP,CON=c.part,c.R,c.C,c.D,c.TP,c.CON
    s='03_regen';sot6='Package_TO_SOT_SMD:SOT-23-6';vssop8='Package_SO:VSSOP-8_2.3x2mm_P0.5mm'
    p(s,'U301','bldc-esc:TLV3011B','TLV3011BIDBVR',80,75,{1:'nDUMP_REQUEST',2:'GND',3:'DUMP_HYST',4:'DUMP_VSENSE',5:None,6:'5V_BUS'},sot6,'TLV3011BIDBVR','Texas Instruments')
    R(s,'R301','100k',30,145,'VBUS','DUMP_DIV_MID',precision=True)
    R(s,'R302','100k',75,145,'DUMP_DIV_MID','DUMP_VSENSE',precision=True)
    R(s,'R303','8.45k',120,145,'DUMP_VSENSE','GND',precision=True)
    R(s,'R304','10k',30,205,'DUMP_REF','DUMP_HYST',precision=True)
    R(s,'R305','2.49M',90,205,'nDUMP_REQUEST','DUMP_HYST')
    R(s,'R306','4.7k',155,205,'5V_BUS','nDUMP_REQUEST')
    C(s,'C301','1n 50V',165,145,'DUMP_VSENSE','GND','0603','C0603C102J5GACTU')
    C(s,'C302','100n 50V',165,75,'5V_BUS')
    C(s,'C303','100n 50V',30,260,'DUMP_REF')
    p(s,'U308','Reference_Voltage:REF2025','REF2025AIDDCR',70,260,{1:'DUMP_REF',2:'GND',3:'5V_BUS',4:'5V_BUS',5:'DUMP_REF_2V5'},mpn='REF2025AIDDCR',manufacturer='Texas Instruments')
    C(s,'C313','100n 50V',95,260,'5V_BUS')
    C(s,'C314','1u 16V',125,260,'DUMP_REF_2V5','GND','0603','C0603C105K4RACTU')
    p(s,'U302','Driver_FET:UCC27511ADBV','UCC27511ADBVR',275,75,{1:'5V_BUS',2:'DUMP_GH',3:'DUMP_GL',4:'DUMP_SOURCE',5:'nDUMP_REQUEST',6:'BRK_ARMED'},mpn='UCC27511ADBVR',manufacturer='Texas Instruments')
    R(s,'R307','2.2',355,55,'DUMP_GH','DUMP_GATE',angle=90)
    R(s,'R308','1',355,105,'DUMP_GL','DUMP_GATE',angle=90)
    p(s,'Q301','bldc-esc:ISC011N06LM5','ISC011N06LM5',430,75,{1:'DUMP_SOURCE',2:'DUMP_SOURCE',3:'DUMP_SOURCE',4:'DUMP_GATE',5:'DUMP_SW'},
       'Package_SON:Infineon_PG-TDSON-8_6.15x5.15mm','ISC011N06LM5ATMA1','Infineon')
    R(s,'R309','47k',490,75,'DUMP_GATE','DUMP_SOURCE')
    p(s,'R310','Device:R','3m / 3W',430,150,{1:'DUMP_SOURCE',2:'GND'},'Resistor_SMD:R_2512_6332Metric','WSLP2512R0030FEA','Vishay')
    C(s,'C304','100n 50V',230,145,'5V_BUS','DUMP_SOURCE')
    C(s,'C305','1u 16V',280,145,'5V_BUS','DUMP_SOURCE','0603','C0603C105K4RACTU')
    CON(s,'J301','DUMP RESISTOR',535,160,['VBUS','DUMP_SW'],
        'TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-3-2-5.08_1x02_P5.08mm_Horizontal','1711725')
    D(s,'D301','STPS5H100AF',490,220,'DUMP_SW','VBUS','Diode_SMD:D_SOD-128','Device:D_Schottky')
    p(s,'U303','Amplifier_Current:INA180A1','INA180A1IDBVR',385,245,{1:'DUMP_CURRENT',2:'GND',3:'DUMP_SOURCE',4:'GND',5:'5V_BUS'},mpn='INA180A1IDBVR',manufacturer='Texas Instruments')
    C(s,'C306','100n 50V',305,245,'5V_BUS')
    p(s,'U304','bldc-esc:TLV3201','TLV3201AIDBVR',200,310,{1:'BRK_OC_OK',2:'GND',3:'DUMP_REF',4:'DUMP_CURRENT',5:'5V_BUS'},sot5(),'TLV3201AIDBVR','Texas Instruments')
    C(s,'C307','100n 50V',135,315,'5V_BUS')
    R(s,'R311','10k',135,365,'5V_BUS','BRK_CLEAR')
    p(s,'U305','bldc-esc:TPS3808Gxx','TPS3808G50DBVR',60,335,{1:'BRK_POR',2:'GND',3:'5V_BUS',4:'BRK_CT',5:'5V_BUS',6:'5V_BUS'},sot6,'TPS3808G50DBVR','Texas Instruments')
    C(s,'C308','1n 50V',30,390,'BRK_CT','GND','0603','C0603C102J5GACTU')
    C(s,'C309','100n 50V',85,390,'5V_BUS')
    R(s,'R312','10k',30,260,'5V_BUS','BRK_POR')
    D(s,'D302','BAT54H',260,365,'BRK_CLEAR','BRK_POR','Diode_SMD:D_SOD-123F')
    D(s,'D303','BAT54H',260,315,'BRK_CLEAR','BRK_OC_OK','Diode_SMD:D_SOD-123F')
    R(s,'R313','10k',310,365,'BRK_POR','BRK_CLK_RC')
    C(s,'C310','10n 50V',360,365,'BRK_CLK_RC','GND','0603','C0603C103K5RACTU')
    p(s,'U306','74xGxx:74LVC1G17','SN74LVC1G17DBVR',445,335,{1:None,2:'BRK_CLK_RC',3:'GND',4:'BRK_CLK',5:'5V_BUS'},sot5(),'SN74LVC1G17DBVR','Texas Instruments')
    p(s,'U307','bldc-esc:SN74LVC1G74','SN74LVC1G74DCUR',545,305,{1:'BRK_CLK',2:'5V_BUS',3:'nBRK_ARMED',4:'GND',5:'BRK_ARMED',6:'BRK_CLEAR',7:'5V_BUS',8:'5V_BUS'},vssop8,'SN74LVC1G74DCUR','Texas Instruments')
    R(s,'R314','100k',490,380,'BRK_ARMED','GND')
    C(s,'C311','100n 50V',540,380,'5V_BUS')
    R(s,'R315','100k',220,200,'nDUMP_REQUEST','DUMP_ACTIVE_SENSE')
    R(s,'R316','150k',275,200,'DUMP_ACTIVE_SENSE','GND')
    R(s,'R317','100k',385,195,'nBRK_ARMED','BRK_FAULT_SENSE')
    R(s,'R318','150k',430,195,'BRK_FAULT_SENSE','GND')
    p(s,'Q302','Transistor_FET:2N7002','2N7002',95,260,{1:'DUMP_PWM_SAFE',2:'GND',3:'nDUMP_REQUEST'},mpn='2N7002P,215',manufacturer='Nexperia')
    R(s,'R319','100k',155,260,'DUMP_PWM_SAFE','GND')
    TP(s,'TP301','DUMP_CURRENT',345,195)
    R(s,'R320','10k',590,210,'DUMP_CURRENT','DUMP_I_ADC',precision=True,angle=90)
    R(s,'R321','15k',635,245,'DUMP_I_ADC','GND',precision=True)
    C(s,'C312','100p 50V',670,245,'DUMP_I_ADC','GND','0603','C0603C101J5GACTU')
    c.notes[s]+=[(25,38,'About 31V on / 30.5V off. Chopper OCP about 20.7A; power-cycle reset.'),
        (250,395,'Q301 source and U302 GND use Kelvin return to R310 high pad.'),
        (25,285,'External resistor: 2-25ohm; pulse and thermal ratings still need checking.')]


def sot5():
    return 'Package_TO_SOT_SMD:SOT-23-5'


def build_sensors(c):
    p,R,C,D,TP,CON=c.part,c.R,c.C,c.D,c.TP,c.CON
    s='06_sensors';sot6='Package_TO_SOT_SMD:SOT-23-6';vssop8='Package_SO:VSSOP-8_2.3x2mm_P0.5mm'
    for k,(rail,en,fault,ref,x) in enumerate([('5V_HALL','SENSOR_5V_EN','SENSOR_nFAULT',601,70),('5V_ENCODER','ENCODER_5V_EN','ENCODER_nFAULT',602,340)]):
        p(s,'U'+str(ref),'bldc-esc:TPS2553_1','TPS2553DBVR-1',x,75,{1:'5V_SYS',2:'GND',3:en,4:fault,5:rail+'_ILIM',6:rail},sot6,'TPS2553DBVR-1','Texas Instruments')
        R(s,'R'+str(601+4*k),'200k',x-40,145,rail+'_ILIM','GND')
        R(s,'R'+str(602+4*k),'100k',x+10,145,en,'GND')
        R(s,'R'+str(603+4*k),'10k',x+60,145,'3V3',fault)
        C(s,'C'+str(601+2*k),'100n 50V',x+60,75,'5V_SYS')
        C(s,'C'+str(602+2*k),'1u 16V',x+115,75,rail,'GND','0603','C0603C105K4RACTU')
    CON(s,'J601','HALL',80,225,['5V_HALL','GND','HALL_1_IN','HALL_2_IN','HALL_3_IN'])
    CON(s,'J602','ENCODER',350,225,['5V_ENCODER','GND','ENC_A_IN','ENC_B_IN','ENC_Z_IN'])
    for k,(channels,x) in enumerate([(['HALL_1','HALL_2','HALL_3'],180),(['ENC_A','ENC_B','ENC_Z'],465)]):
        nets={8:'3V3',4:'GND'}
        for j,net in enumerate(channels):
            b=620+k*12+j*3
            R(s,'R'+str(b),'1k',x-75+j*55,305,net+'_IN',net+'_FILT',angle=90)
            R(s,'R'+str(b+1),'10k',x-75+j*55,355,'5V_HALL' if k==0 else '5V_ENCODER',net+'_IN')
            C(s,'C'+str(610+k*3+j),'100p 50V',x-75+j*55,395,net+'_FILT','GND','0603','C0603C101J5GACTU')
            D(s,'D'+str(610+k*3+j),'PESD5V0S1BA',x-75+j*55,265,'GND',net+'_IN','Diode_SMD:D_SOD-323','Device:D_TVS')
            nets[[1,3,6][j]]=net+'_FILT';nets[[7,5,2][j]]=net
        p(s,'U'+str(603+k),'bldc-esc:SN74LVC3G17','SN74LVC3G17DCUR',x,220,nets,vssop8,'SN74LVC3G17DCUR','Texas Instruments')
        C(s,'C'+str(605+k),'100n 50V',x+65,210,'3V3')
    c.notes[s]+=[(25,38,'5V sensor outputs default off / about 0.13A current limit each'),
        (25,180,'Hall pin order is the controller connector order. Verify OEM motor wires first.'),
        (305,180,'Single-ended encoder A/B/Z, 3.3V or 5V. Not an RS-422 receiver.')]


def build_io(c):
    p,R,C,D,TP,CON=c.part,c.R,c.C,c.D,c.TP,c.CON
    s='07_io_can';sot6='Package_TO_SOT_SMD:SOT-23-6';vssop8='Package_SO:VSSOP-8_2.3x2mm_P0.5mm'
    p(s,'U701','bldc-esc:TPS3890','TPS389033DSER',70,75,{1:'3V3_A',2:'GND',3:'3V3',4:'3V3',5:'POR_CT',6:'POWER_OK'},
      'Package_SON:WSON-6_1.5x1.5mm_P0.5mm','TPS389033DSER','Texas Instruments')
    R(s,'R701','0',30,135,'NRST','POWER_OK')
    C(s,'C701','100n 50V',80,135,'3V3')
    C(s,'C702','47n 50V',130,135,'POR_CT','GND','0603','C0603C473K5RACTU')
    p(s,'U702','bldc-esc:TPS3431','TPS3431SDRBR',220,75,{1:'3V3',2:'WD_CWD',3:'3V3',4:'GND',5:'WD_RUN',6:'WD_HEARTBEAT',7:'WD_OK',8:None,9:'GND'},
        'Package_SON:VSON-8-1EP_3x3mm_P0.65mm_EP1.65x2.4mm','TPS3431SDRBR','Texas Instruments')
    R(s,'R702','10k',180,135,'3V3','WD_CWD')
    R(s,'R703','0',230,135,'NRST','WD_OK')
    R(s,'R704','100k',280,135,'WD_HEARTBEAT','GND')
    C(s,'C703','100n 50V',285,70,'3V3')
    p(s,'U703','74xGxx:74LVC1G11','SN74LVC1G11DBVR',370,125,{1:'NRST',2:'GND',3:'BUS_OK',4:'SYSTEM_GOOD_PRE',5:'3V3',6:'HW_ENABLE_OK'},sot6,'SN74LVC1G11DBVR','Texas Instruments')
    p(s,'U704','74xGxx:74LVC1G11','SN74LVC1G11DBVR',505,125,{1:'SYSTEM_GOOD',2:'GND',3:'nOC_HW',4:'SAFETY_GOOD',5:'3V3',6:'DRV_nFAULT'},sot6,'SN74LVC1G11DBVR','Texas Instruments')
    p(s,'U705','bldc-esc:SN74LVC1G74','SN74LVC1G74DCUR',490,60,{1:'BRIDGE_ARM_REQ',2:'3V3',3:'nPWM_ENABLE',4:'GND',5:'nFAULT_LATCH',6:'SAFETY_GOOD',7:'3V3',8:'3V3'},vssop8,'SN74LVC1G74DCUR','Texas Instruments')
    R(s,'R705','100k',430,40,'BRIDGE_ARM_REQ','GND')
    R(s,'R706','10k',550,40,'3V3','nPWM_ENABLE')
    p(s,'U706','bldc-esc:SN74LVC244A','SN74LVC244APWR',500,225,{20:'3V3',10:'GND',1:'nPWM_ENABLE',19:'nPWM_ENABLE',
        2:'PWM_AH',18:'IN_AH',4:'PWM_AL',16:'IN_AL',6:'PWM_BH',14:'IN_BH',8:'PWM_BL',12:'IN_BL',
        11:'PWM_CH',9:'IN_CH',13:'PWM_CL',7:'IN_CL',15:'GND',5:None,17:'GND',3:None},
        'Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm','SN74LVC244APWR','Texas Instruments')
    for i,net in enumerate(['IN_AH','IN_AL','IN_BH','IN_BL','IN_CH','IN_CL']):R(s,'R'+str(710+i),'10k',330+43*i,305,net,'GND')
    p(s,'U707','74xGxx:74LVC1G11','SN74LVC1G11DBVR',365,205,{1:'DRV_WAKE_REQ',2:'GND',3:'NRST',4:'DRV_ENABLE_PRE',5:'3V3',6:'BUS_OK'},sot6,'SN74LVC1G11DBVR','Texas Instruments')
    R(s,'R716','100k',310,260,'DRV_WAKE_REQ','GND')
    p(s,'U708','74xGxx:74LVC1G11','SN74LVC1G11DBVR',380,365,{1:'DUMP_PWM',2:'GND',3:'NRST',4:'DUMP_PWM_SAFE',5:'3V3',6:'nFAULT_LATCH'},sot6,'SN74LVC1G11DBVR','Texas Instruments')
    for i,x in enumerate([30,80,130,180,230,280,330,380],1):C(s,'C'+str(710+i),'100n 50V',x,390,'3V3')
    p(s,'U709','bldc-esc:TCAN3403','TCAN3403DRQ1',70,215,{1:'CAN_TX',2:'GND',3:'3V3',4:'CAN_RX',5:'3V3',6:'CAN_L',7:'CAN_H',8:'CAN_STB'},
        'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm','TCAN3403DRQ1','Texas Instruments')
    R(s,'R717','10k',30,295,'3V3','CAN_STB')
    R(s,'R718','10k',75,295,'3V3','CAN_TX')
    C(s,'C704','100n 50V',140,215,'3V3')
    CON(s,'J701','CAN',225,205,['GND','CAN_H','CAN_L'])
    R(s,'R719','120',170,295,'CAN_H','CAN_TERM','0805')
    CON(s,'JP701','CAN TERM',230,295,['CAN_TERM','CAN_L'],'Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical','M20-9990245')
    p(s,'D703','bldc-esc:PESD2CANFD24V_T','PESD2CANFD24V-T',130,295,{1:'CAN_H',2:'CAN_L',3:'GND'},'Package_TO_SOT_SMD:SOT-23','PESD2CANFD24V-T,215','Nexperia')
    CON(s,'J702','UART / 3V3',70,350,['GND','UART_TX','UART_RX','3V3'])
    build_protection(c)
    build_analog_io(c)


def build_protection(c):
    p,R,C,D,TP,CON=c.part,c.R,c.C,c.D,c.TP,c.CON
    s='01_dc_link'
    p(s,'U101','bldc-esc:TLV9024','TLV9024PWR',65,240,{3:'3V3_A',12:'GND',5:'OC_HI',4:'I_PHASE_A',2:'nOC_HW',7:'I_PHASE_A',6:'OC_LO',1:'nOC_HW',9:'OC_HI',8:'I_PHASE_B',14:'nOC_HW',11:'I_PHASE_B',10:'OC_LO',13:'nOC_HW'},
      'Package_SO:TSSOP-14_4.4x5mm_P0.65mm','TLV9024PWR','Texas Instruments')
    p(s,'U102','bldc-esc:TLV9024','TLV9024PWR',235,240,{3:'3V3_A',12:'GND',5:'OC_HI',4:'I_PHASE_C',2:'nOC_HW',7:'I_PHASE_C',6:'OC_LO',1:'nOC_HW',9:'BUS_OV_REF',8:'V_BUS_ADC',14:'BUS_OK',11:'V_BUS_ADC',10:'BUS_UV_REF',13:'BUS_OK'},
      'Package_SO:TSSOP-14_4.4x5mm_P0.65mm','TLV9024PWR','Texas Instruments')
    R(s,'R110','10k',340,65,'VREF_2V5','OC_HI',precision=True)
    R(s,'R111','90.9k',340,105,'OC_HI','GND',precision=True)
    R(s,'R112','90.9k',400,105,'VREF_2V5','OC_LO',precision=True)
    R(s,'R113','10k',460,105,'OC_LO','GND',precision=True)
    R(s,'R114','10k',400,160,'VREF_2V5','BUS_OV_REF',precision=True)
    R(s,'R115','16.9k',460,160,'BUS_OV_REF','GND',precision=True)
    R(s,'R118','40.2k',520,160,'VREF_2V5','BUS_UV_REF',precision=True)
    R(s,'R119','10k',570,160,'BUS_UV_REF','GND',precision=True)
    C(s,'C117','10n 50V',570,220,'BUS_UV_REF','GND','0603','C0603C103K5RACTU')
    C(s,'C110','10n 50V',335,235,'OC_HI','GND','0603','C0603C103K5RACTU')
    C(s,'C111','10n 50V',335,285,'OC_LO','GND','0603','C0603C103K5RACTU')
    C(s,'C112','10n 50V',395,285,'BUS_OV_REF','GND','0603','C0603C103K5RACTU')
    R(s,'R116','4.7k',460,285,'3V3','nOC_HW')
    R(s,'R117','10k',520,285,'3V3','BUS_OK')
    C(s,'C113','100n 50V',170,235,'3V3_A')
    C(s,'C114','100n 50V',285,290,'3V3_A')
    c.notes[s].append((365,340,'OCP: about +/-50A / bus window: 10.5-33V'))


def build_analog_io(c):
    p,R,C,D,TP,CON=c.part,c.R,c.C,c.D,c.TP,c.CON
    s='06_sensors'
    c.notes[s].append((25,415,'5V Hall/encoder signals: buffered, series-R, ESD. No 24V input rating.'))
    s='05_mcu'
    p(s,'U503','bldc-esc:M24C64_R','M24C64-RMN6TP',500,195,{1:'GND',2:'GND',3:'GND',4:'GND',5:'I2C_SDA',6:'I2C_SCL',7:'EEPROM_WP',8:'3V3'},
        'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm','M24C64-RMN6TP','STMicroelectronics')
    R(s,'R506','4.7k',445,90,'3V3','I2C_SCL')
    R(s,'R507','4.7k',555,90,'3V3','I2C_SDA')
    R(s,'R508','10k',555,205,'3V3','EEPROM_WP')
    C(s,'C516','100n 50V',555,155,'3V3')
    C(s,'C517','100n 50V',280,300,'3V3')
    for i,(net,x) in enumerate([('LED_STATUS',45),('LED_COMM',105),('3V3',165)],1):
        R(s,'R'+str(510+i),'1k',x,345,net,'LED_'+str(i))
        p(s,'D'+str(510+i),'Device:LED',['STATUS','COMM','POWER'][i-1],x,375,{1:'GND',2:'LED_'+str(i)},'LED_SMD:LED_0603_1608Metric','LTST-C190KGKT','Lite-On',90)
    s='07_io_can'
    p(s,'U710','74xGxx:74LVC1G14','SN74LVC1G14DBVR',240,355,{1:None,2:'nHW_ENABLE_SENSE',3:'GND',4:'HW_ENABLE_OK',5:'3V3'},sot5(),'SN74LVC1G14DBVR','Texas Instruments')
    CON(s,'J703','HW ENABLE',475,375,['nHW_ENABLE_IN','GND'],'Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical','M20-9990245')
    R(s,'R720','10k',540,355,'3V3','nHW_ENABLE_IN')
    R(s,'R721','1k',540,395,'nHW_ENABLE_IN','nHW_ENABLE_SENSE',angle=90)
    C(s,'C705','10n 50V',470,335,'nHW_ENABLE_SENSE','GND','0603','C0603C103K5RACTU')
    build_measurements(c)
    ss='09_safety'
    p(ss,'U711','74xGxx:74LVC1G11','SN74LVC1G11DBVR',70,475,{1:'SYSTEM_GOOD_PRE',2:'GND',3:'WD_RUN',4:'SYSTEM_GOOD',5:'3V3',6:'BRK_ARMED'},'Package_TO_SOT_SMD:SOT-23-6','SN74LVC1G11DBVR','Texas Instruments')
    p(ss,'U712','74xGxx:74LVC1G11','SN74LVC1G11DBVR',225,475,{1:'DRV_ENABLE_PRE',2:'GND',3:'WD_RUN',4:'DRV_ENABLE',5:'3V3',6:'BRK_ARMED'},'Package_TO_SOT_SMD:SOT-23-6','SN74LVC1G11DBVR','Texas Instruments')
    D(ss,'D704','PESD5V0S1BA',540,420,'GND','nHW_ENABLE_IN','Diode_SMD:D_SOD-323','Device:D_TVS')
    R(ss,'R722','10k',365,475,'3V3','WD_RUN')
    CON(ss,'JP704','RUN 1-2 / SERVICE 2-3',470,475,['3V3','WD_RUN','GND'],
        'Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical','M20-9990345')
    C(ss,'C719','100n 50V',70,530,'3V3')
    C(ss,'C720','100n 50V',225,530,'3V3')


def build_measurements(c):
    p,R,C,D,TP,CON=c.part,c.R,c.C,c.D,c.TP,c.CON
    s='06_sensors'
    c.notes[s].append((305,38,'Hall/encoder supplies: 200k ILIM, latch-off on a short'))
    s='05_mcu'
    c.notes[s].append((25,265,'NRST and BOOT0 have dedicated pull states. ADC trigger is TIM1 TRGO.'))
    s='08_analog_inputs'
    nets={4:'3V3_A',11:'GND'}
    for i,(source,out) in enumerate([('VBUS','V_BUS_ADC'),('PHASE_A','V_PHASE_A'),('PHASE_B','V_PHASE_B'),('PHASE_C','V_PHASE_C')]):
        x=65+175*i; b=801+10*i
        R(s,'R'+str(b),'100k',x,65,source,out+'_MID',precision=True)
        R(s,'R'+str(b+1),'100k',x+50,65,out+'_MID',out+'_DIV',precision=True)
        R(s,'R'+str(b+2),'10k',x+105,65,out+'_DIV','GND',precision=True)
        C(s,'C'+str(b),'220p 50V',x,135,out+'_DIV','GND','0603','C0603C221J5GACTU')
        p(s,'D'+str(b),'Device:D_Dual_Series_AKC','BAV199',x+70,135,{1:'GND',2:'3V3_A',3:out+'_DIV'},'Package_TO_SOT_SMD:SOT-23','BAV199,215','Nexperia')
        R(s,'R'+str(b+3),'100',x,205,out+'_BUF',out,angle=90)
        C(s,'C'+str(b+1),'1n 50V',x+70,205,out,'GND','0603','C0603C102J5GACTU')
        pos,neg,output=[(3,2,1),(5,6,7),(10,9,8),(12,13,14)][i]
        nets[pos]=out+'_DIV';nets[neg]=out+'_BUF';nets[output]=out+'_BUF'
    p(s,'U801','bldc-esc:TLV9064','TLV9064IPWR',745,135,nets,'Package_SO:TSSOP-14_4.4x5mm_P0.65mm','TLV9064IPWR','Texas Instruments')
    C(s,'C840','100n 50V',745,215,'3V3_A')
    for i,(net,x) in enumerate([('THROTTLE_ADC',70),('AUX_ANALOG_ADC',245)]):
        n=850+5*i
        CON(s,'J'+str(801+i),net,x,285,['5V_HALL','GND',net+'_IN'])
        R(s,'R'+str(n),'12.1k',x-25,345,net+'_IN',net,angle=90)
        R(s,'R'+str(n+1),'10k',x+35,345,net,'GND')
        C(s,'C'+str(n),'10n 50V',x-25,400,net,'GND','0603','C0603C103K5RACTU')
        p(s,'D'+str(n),'Diode:BAT54S','BAT54S',x+45,400,{1:'GND',2:'3V3_A',3:net},mpn='BAT54S,215',manufacturer='Nexperia')
    CON(s,'J803','RC PWM',410,275,['GND','5V_HALL','RC_PWM_RAW'])
    CON(s,'J804','BRAKE / DIR',585,275,['GND','nBRAKE_RAW','nDIR_RAW'])
    logic={8:'3V3',4:'GND'}
    for i,(raw,out,x) in enumerate([('RC_PWM_RAW','RC_PWM_IN',390),('nBRAKE_RAW','nBRAKE_IN',505),('nDIR_RAW','nDIR_IN',620)]):
        n=865+3*i
        R(s,'R'+str(n),'1k',x,345,raw,raw+'_FILT',angle=90)
        R(s,'R'+str(n+1),'10k',x+50,345,'GND' if i==0 else '3V3',raw)
        C(s,'C'+str(n),'1n 50V',x,400,raw+'_FILT','GND','0603','C0603C102J5GACTU')
        D(s,'D'+str(n),'PESD5V0S1BA',x+50,400,'GND',raw,'Diode_SMD:D_SOD-323','Device:D_TVS')
        logic[[1,3,6][i]]=raw+'_FILT';logic[[7,5,2][i]]=out
    p(s,'U802','bldc-esc:SN74LVC3G17','SN74LVC3G17DCUR',750,335,logic,'Package_SO:VSSOP-8_2.3x2mm_P0.5mm','SN74LVC3G17DCUR','Texas Instruments')
    C(s,'C845','100n 50V',750,405,'3V3')
    for i,(net,x) in enumerate([('NTC_BRIDGE',70),('NTC_PCB',245),('NTC_MOTOR',420),('NTC_DUMP',595)]):
        n=880+3*i
        R(s,'R'+str(n),'10k',x,475,'VREF_2V5',net,precision=True)
        C(s,'C'+str(n),'10n 50V',x+55,475,net,'GND','0603','C0603C103K5RACTU')
        if i<2:
            p(s,'TH'+str(801+i),'Device:Thermistor_NTC','10k / B25-50=3380K',x,540,{1:net,2:'GND'},'Resistor_SMD:R_0603_1608Metric','NCP18XH103F03RB','Murata')
        else:
            CON(s,'J'+str(805+i-2),net,x,540,[net+'_IN','GND'])
            R(s,'R'+str(n+1),'1k',x+95,475,net+'_IN',net,angle=90)
            p(s,'D'+str(n),'Diode:BAT54S','BAT54S',x+95,540,{1:'GND',2:'3V3_A',3:net},mpn='BAT54S,215',manufacturer='Nexperia')
    R(s,'R898','10k',765,485,'3V3','V_3V3_ADC',precision=True)
    R(s,'R899','10k',765,535,'V_3V3_ADC','GND',precision=True)
    C(s,'C899','10n 50V',705,475,'V_3V3_ADC','GND','0603','C0603C103K5RACTU')
    c.notes[s]+=[(25,38,'Bus / phase dividers: 21:1. Buffer outputs drive ADC RC filters.'),(25,245,'Analog inputs: 0-5V. Connector 5V supplies are current-limited.')]


def reorganize(c):
    for part in c.parts:
        if part['mpn']=='INA241A2IDGKR':
            part['value']='INA241A2IDR';part['mpn']='INA241A2IDR'
            part['footprint']='Package_SO:SOIC-8_3.9x4.9mm_P1.27mm'
        elif part['mpn']=='SN74LVC3G17DCUR':
            part['value']='SN74LVC3G17DCTR';part['mpn']='SN74LVC3G17DCTR'
            part['footprint']='Package_SO:SSOP-8_2.95x2.8mm_P0.65mm'
        elif part['mpn']=='SN74LVC1G74DCUR':
            part['value']='SN74LVC1G74DCTR';part['mpn']='SN74LVC1G74DCTR'
            part['footprint']='Package_SO:SSOP-8_2.95x2.8mm_P0.65mm'
    for p in c.parts:
        if p['sheet']=='02_bridge' and p['ref'][0] in ('R','C') and int(p['ref'][1:])>=230:
            p['x']-=30 if int(p['ref'][1:])<250 else 60
        if p['sheet']=='02_bridge' and p['ref'] in ('Q203','Q204','U203','TP211'):p['x']-=30
        if p['sheet']=='02_bridge' and p['ref'] in ('Q205','Q206','U204','TP212'):p['x']-=60
        if p['ref']=='C254':p['x'],p['y']=465,365
        if p['ref']=='R312':p['x'],p['y']=215,255
        if p['ref']=='R314':p['x'],p['y']=530,345
        if p['ref']=='C311':p['x'],p['y']=550,260
        if p['sheet']=='06_sensors' and p['ref'] in ('R621','R624','R627','R633','R636','R639'):p['y']=330
        if p['sheet']=='06_sensors' and p['ref'] in ('C610','C611','C612','C613','C614','C615'):p['y']=350
        if p['ref']=='R899':p['y']=520
        if p['ref'] in ('R211','R231','R251'):p['y']=95
        if p['ref'] in ('R213','R233','R253'):p['y']=165
        if p['ref'] in ('TP210','TP211','TP212'):
            p['x']=280+115*(int(p['ref'][2:])-210);p['y']=300
        if p['ref'] in ('R511','R512','R513','D511','D512','D513'):
            p['sheet']='04_power_usb'
            p['x']=470+50*(int(p['ref'][1:])-511)
            p['y']=320 if p['ref'].startswith('R') else 350
    safety_refs={*['U'+str(n) for n in range(701,709)],'U710',
        *['R'+str(n) for n in range(701,717)],'R720','R721',
        'C701','C702','C703','C705',*['C'+str(n) for n in range(711,719)],'D701','D702','J703'}
    for p in c.parts:
        if p['ref'] in safety_refs:p['sheet']='09_safety'
    for p in c.parts:
        if p['sheet']=='07_io_can':p['y']-=170
    protection={*['R'+str(n) for n in range(110,118)],*['C'+str(n) for n in range(110,115)],'U101','U102'}
    placements={'U101':(675,85),'U102':(675,195),'R110':(605,285),'R111':(665,285),
        'R112':(725,285),'R113':(785,285),'R114':(605,345),'R115':(665,345),
        'R116':(725,345),'R117':(785,345),'C110':(605,405),'C111':(665,405),'C112':(725,405),'C113':(765,85),'C114':(765,195)}
    for p in c.parts:
        if p['ref'] in protection:
            p['sheet']='09_safety';p['x'],p['y']=placements[p['ref']]
    c.notes['09_safety']=[(25,38,'Main bridge: fault clears arm latch; a new arm edge is required.'),
        (590,38,'Fixed +/-50A current window / bus window about 10.5-33V'),
        (25,560,'JP704 SERVICE: watchdog off, gate driver and PWM held off.'),
        (25,575,'MCU comparator thresholds can be lower; external trips do not depend on firmware.')]
    c.notes['06_sensors']=[(x,380 if y==415 else y,t) for x,y,t in c.notes['06_sensors']]
