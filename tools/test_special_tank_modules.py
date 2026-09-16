from pathlib import Path
import re
R=Path(__file__).resolve().parents[1]
def parse(text):
 ts=re.findall(r'#[^\n]*|[{}]|>=|<=|[=<>]|[^\s{}=<>#]+',text)
 ts=[t for t in ts if not t.startswith('#')];i=0
 def block():
  nonlocal i
  nodes=[]
  while i<len(ts) and ts[i]!='}':
   k,op,v=ts[i:i+3];i+=3
   if v=='{':v=block();assert ts[i]=='}';i+=1
   nodes.append((k,op,v))
  return nodes
 out=block();assert i==len(ts);return out
def get(ns,key):return next(v for k,op,v in ns if k==key)

fx=get(parse((R/'common/scripted_effects/RUS_special_tank_modules.txt').read_text()),'RUS_refresh_special_tank_modules')
def check(nodes,tag,techs):
 for k,op,v in nodes:
  if k=='tag':ok=tag==v
  elif k=='has_tech':ok=v in techs
  elif k=='is_in_array':
   assert get(v,'array')=='researched_techs'
   ok=get(v,'value').removeprefix('token:') in techs
  elif k=='NOT':ok=not check(v,tag,techs)
  else:raise AssertionError(k)
  if not ok:return False
 return True
def run(nodes,tag,techs):
 for k,op,v in nodes:
  if k=='if':
   if check(get(v,'limit'),tag,techs):run([n for n in v if n[0]!='limit'],tag,techs)
  elif k=='set_technology':
   for tech,_,level in v:
    if tech!='popup':
     assert level=='1'; assert get(v,'popup')=='yes'
     POPUPS.append(tech);techs.add(tech)
  else:raise AssertionError(k)
pre=['RUS_fr_unlock_stabilizer','sp_advance_sabot_shells']
rewards=['RUS_unlock_special_stabilizer','RUS_unlock_special_auto_loader']
for tag in ['RUS','GER','FRA','SOV']:
 for mask in range(4):
  initial={pre[i] for i in range(2) if mask & (1<<i)}
  for legacy in [False,True]:
   POPUPS=[]
   techs=initial|({'RUS_auto_loader_old_save_compat'} if legacy else set());expected=techs|({rewards[i] for i in range(2) if mask & (1<<i)} if tag=='RUS' else set())
   run(fx,tag,techs);assert techs==expected,(tag,mask,legacy)
   expected_popups=[rewards[i] for i in range(2) if tag=='RUS' and mask & (1<<i)]
   assert POPUPS==expected_popups
   run(fx,tag,techs);assert techs==expected;assert POPUPS==expected_popups
for p in (R/'common/units/equipment/modules').glob('*.txt'):
 assert not re.search(r'^\s*(stabilizer|auto_loader)\s*=\s*{',p.read_text(),re.M)
p=R/'common/technologies/zzz_RUS_advanced_sabot_shells.txt'
assert not re.search(r'^\s*sp_advance_sabot_shells\s*=',p.read_text(),re.M)
print('32 country/prerequisite/legacy combinations and repeat checks passed; no shared module or sabot technology overrides remain in these files.')

POPUPS=[];techs=set(rewards)
run(fx,'RUS',techs);assert not POPUPS
run(fx,'RUS',techs);assert not POPUPS
assert not (R/'events/RUS_special_tank_modules.txt').exists()
print('Native research popups: once on new unlock; no repeat for already unlocked saves; no narrative events.')

# The local artillery file masks KR's file: verify the project-unlocked node still exists locally.
artillery=(R.parent/'1521695605/common/technologies/artillery.txt').read_text(encoding='utf-8-sig')
assert not (R/'common/technologies/artillery.txt').exists(), 'Do not mask the upstream artillery tree'
assert len(re.findall(r'^\s*sp_advance_sabot_shells\s*=\s*{',artillery,re.M))==1
assert 'leads_to_tech = sp_advance_sabot_shells' in artillery
assert 'is_special_project_completed = sp:sp_land_large_caliber_kinetic_energy_sabot' in artillery
print('Special-project research node and incoming technology path are present in the upstream artillery file; no local tree override remains.')

focus=(R/"common/national_focus/RUS focus (Russia).txt").read_text(encoding="utf-8-sig")
assert re.search(r"set_technology = \{ RUS_fr_unlock_stabilizer = 1 popup = no \}\s*hidden_effect = \{ RUS_refresh_special_tank_modules = yes \}",focus)
print("Stabilizer refresh executes directly after its focus prerequisite is granted.")
