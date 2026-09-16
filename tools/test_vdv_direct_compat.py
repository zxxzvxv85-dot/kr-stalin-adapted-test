from pathlib import Path
import re
R=Path(__file__).resolve().parents[1]
V=Path('D:/steam/steamapps/common/Hearts of Iron IV')
KR=R.parent/'1521695605';EXT=R.parent/'3105210203';EXT2=R.parent/'3555444820'
def effective(roots,folder):
 files={}
 for root in roots:
  for p in (root/folder).rglob('*.txt'):files[p.relative_to(root).as_posix()]=p
 return files
for title,roots in [('KR + test',[V,KR,R]),('KR + both technology extensions + test',[V,KR,EXT,EXT2,R])]:
 tech=effective(roots,'common/technologies');units=effective(roots,'common/units');mio=effective(roots,'common/military_industrial_organization/organizations')
 tree=tech['common/technologies/artillery.txt'].read_text(encoding='utf-8-sig')
 assert ('sp_advance_sabot_shells = {' in tree)==(len(roots)==3), 'Respect each upstream technology tree'
 assert tech['common/technologies/artillery.txt'].is_relative_to(KR if len(roots)==3 else EXT2)
 text='\n'.join(p.read_text(encoding='utf-8-sig',errors='replace') for p in units.values())
 assert len(re.findall(r'^\s*RUS_vdv\s*=\s*{',text,re.M))==0
 assert len(re.findall(r'^\s*air_assault_special_forces\s*=\s*{',text,re.M))==1
 assert re.search(r'^\s*helicopter_equipment\s*=\s*{',text,re.M)
 mt='\n'.join(p.read_text(encoding='utf-8-sig',errors='replace') for p in mio.values())
 assert len(re.findall(r'^RUS_vdv_kamov_organisation\s*=\s*{',mt,re.M))==1
 if len(roots)>3:
  assert len(re.findall(r'^RUS_kamov_helicopter_organisation\s*=\s*{',mt,re.M))==1
  assert len(re.findall(r'^\s*air_assault\s*=\s*{', (EXT2/'common/units/helicopters.txt').read_text(),re.M))==1
 print(title+': shared research, equipment, independent battalion and MIO definitions resolved')
assert not (R/'common/technologies/zzz_RUS_forest_marsh_mechanized.txt').exists()
for p in (R/'common/technologies').glob('*.txt'):
 assert not re.search(r'^\s*tech_(forest|marsh)_warfare\s*=',p.read_text(encoding='utf-8-sig'),re.M)
gfx=(R/'interface/RUS_stalin_air_assault.gfx').read_text()
for rel in re.findall(r'texture[Ff]ile\s*=\s*"([^"]+)"',gfx):assert (R/rel).exists(),rel
assert 'GFX_unit_RUS_vdv_icon_medium' in gfx
assert 'GFX_unit_air_assault_icon_medium"' not in gfx
print('VDV graphics resolve; shared terrain technology overrides are absent.')
