import csv
import json
import os
import sys
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

import wx

app = wx.App(False)
import pcbnew

ROOT = Path(__file__).resolve().parent.parent
FP_ROOT = Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints')
board = pcbnew.LoadBoard(str(ROOT / 'bldc-esc.kicad_pcb'))
tree = ET.parse(ROOT / 'work/qa/bldc-esc.xml').getroot()
metadata = {r['reference']:r for r in csv.DictReader((ROOT/'engineering/schematic_bom.csv').open())}
components = {c.attrib['ref']:c for c in tree.findall('./components/comp')}
existing = {f.GetReference():f for f in board.GetFootprints()}
placement_before = {ref:(fp.GetPosition().x,fp.GetPosition().y,fp.GetOrientationDegrees()) for ref,fp in existing.items()}
if set(existing)-set(components):
    raise RuntimeError('UNEXPECTED_EXISTING_FOOTPRINTS')
if len(board.GetTracks()) or len(board.Zones()):
    raise RuntimeError('PCB_HAS_LAYOUT')
net_by_pin = {}
net_map = {}
for net in tree.findall('./nets/net'):
    name = net.attrib['name']
    item = board.FindNet(name)
    if item is None or item.GetNetCode() < 0:
        item = pcbnew.NETINFO_ITEM(board,name)
        board.Add(item)
    net_map[name] = item
    for node in net.findall('node'):
        net_by_pin[(node.attrib['ref'],node.attrib['pin'])] = name

errors = []
all_pads = 0
connected_pads = 0
for index, (reference,component) in enumerate(sorted(components.items())):
    fp_id = component.findtext('footprint')
    library, name = fp_id.split(':',1)
    directory = ROOT/'bldc-esc.pretty' if library=='bldc-esc' else FP_ROOT/(library+'.pretty')
    footprint = existing.get(reference)
    saved_position=None
    saved_angle=None
    if footprint is not None and (str(footprint.GetFPID().GetLibNickname())!=library or str(footprint.GetFPID().GetLibItemName())!=name):
        saved_position=pcbnew.VECTOR2I(footprint.GetPosition())
        saved_angle=footprint.GetOrientation()
        board.Remove(footprint)
        footprint=None
    if footprint is None:
        footprint = pcbnew.FootprintLoad(str(directory),name)
        if footprint is None:
            errors.append([reference,'FOOTPRINT_LOAD',fp_id]);continue
        footprint.SetFPID(pcbnew.LIB_ID(library,name))
        footprint.SetPosition(saved_position if saved_position is not None else pcbnew.VECTOR2I(pcbnew.FromMM(30+(index%18)*32),pcbnew.FromMM(30+(index//18)*32)))
        if saved_angle is not None:footprint.SetOrientation(saved_angle)
        board.Add(footprint)
    footprint.SetReference(reference)
    footprint.SetValue(component.findtext('value') or '')
    if '--stage' in sys.argv:
        footprint.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(30+(index%18)*32),pcbnew.FromMM(30+(index//18)*32)))
    for key in ('MPN','Manufacturer'):
        footprint.SetField(key,metadata[reference][key.lower() if key=='Manufacturer' else key])
        footprint.GetField(key).SetVisible(False)
        footprint.GetField(key).SetLayer(pcbnew.F_Fab)
    for key in ('Datasheet','Description'):
        field=component.find("./fields/field[@name='"+key+"']")
        footprint.SetField(key,(field.text or '') if field is not None else '')
        footprint.GetField(key).SetVisible(False)
        footprint.GetField(key).SetLayer(pcbnew.F_Fab)
    sheet = component.find('sheetpath')
    path = pcbnew.KIID_PATH()
    unit_stamps=component.findtext('tstamps').split()
    primary_stamp=str(uuid.uuid5(uuid.UUID('10000000-0000-4000-8000-000000000000'),reference))
    if primary_stamp not in unit_stamps:
        raise RuntimeError(('MISSING_PRIMARY_UNIT_UUID',reference))
    path_string = sheet.attrib['tstamps'].strip('/')+'/'+primary_stamp
    for identifier in path_string.split('/'):
        if identifier:path.push_back(pcbnew.KIID(identifier))
    footprint.SetPath(path)
    footprint.SetSheetname(sheet.attrib['names'])
    footprint.SetSheetfile(next((p.get('value','') for p in component.findall('property') if p.get('name')=='Sheetfile'),''))
    attributes=footprint.GetAttributes() & ~(pcbnew.FP_DNP | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
    if metadata[reference]['DNP']=='true':attributes |= pcbnew.FP_DNP
    if reference.startswith('TP'):attributes |= pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES
    footprint.SetAttributes(attributes)
    numbers = {pad.GetNumber() for pad in footprint.Pads() if pad.GetNumber()}
    pins = {pin for (ref,pin) in net_by_pin if ref==reference}
    missing = pins - numbers
    if missing:errors.append([reference,'MISSING_PADS',sorted(missing),sorted(numbers)])
    for pad in footprint.Pads():
        if not pad.GetNumber():continue
        all_pads+=1
        net = net_by_pin.get((reference,pad.GetNumber()))
        if net:
            pad.SetNet(net_map[net]);connected_pads+=1
        else:pad.SetNetCode(0)

result={'footprints':len(board.GetFootprints()),'copper_layers':board.GetCopperLayerCount(),
        'numbered_pads':all_pads,'connected_pads':connected_pads,'errors':errors}
if errors:
    print(json.dumps(result,indent=2));sys.exit(1)
pcbnew.SaveBoard(str(ROOT/'bldc-esc.kicad_pcb'),board)
loaded=pcbnew.LoadBoard(str(ROOT/'bldc-esc.kicad_pcb'))
pad_errors=[]
for fp in loaded.GetFootprints():
    for pad in fp.Pads():
        expected=net_by_pin.get((fp.GetReference(),pad.GetNumber()),'')
        if pad.GetNumber() and pad.GetNetname()!=expected:
            pad_errors.append([fp.GetReference(),pad.GetNumber(),expected,pad.GetNetname()])
result.update({'reloaded_footprints':len(loaded.GetFootprints()),'tracks':len(loaded.GetTracks()),
               'zones':len(loaded.Zones()),'drawings':len(loaded.GetDrawings()),'pad_net_mismatches':pad_errors})
placement_errors=[]
if '--stage' not in sys.argv:
    for fp in loaded.GetFootprints():
        now=(fp.GetPosition().x,fp.GetPosition().y,fp.GetOrientationDegrees())
        before=placement_before.get(fp.GetReference())
        if before is not None and before!=now:placement_errors.append([fp.GetReference(),before,now])
result['placement_changes']=placement_errors
print(json.dumps(result,indent=2))
sys.exit(bool(pad_errors or placement_errors))
