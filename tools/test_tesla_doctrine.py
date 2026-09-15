"""Execute daily-effect script branches in a small interpreter, not the game engine."""
from pathlib import Path
from decimal import Decimal as D
import re,copy
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
assert '>=' not in (R/'common/scripted_effects/RUS_tesla_doctrine_effects.txt').read_text(), 'HOI4 rejects >= in this trigger'
fx=get(parse((R/'common/scripted_effects/RUS_tesla_doctrine_effects.txt').read_text()),'RUS_tesla_doctrine_daily_tick')
tracks=['armor','combat_support','operations']
mios=['RUS_tstz_organisation','RUS_obukhov_organisation','RUS_amo_organisation']
def world(level=1,xp='1'):
 return dict(xp=D(xp),flags={f'RUS_tesla_doctrine_{t}_{l}' for t in tracks for l in range(1,level+1)},selected=set(tracks),completed=set(),active={f'RUS_tesla_doctrine_{t}_policy' for t in tracks},available=set(mios),gain={},total={})
def check(ns,w,mio=None):
 def one(k,op,v):
  if k=='NOT':return not check(v,w,mio)
  if k.startswith('mio:'):return check(v,w,k[4:])
  if k=='has_country_flag':return v in w['flags']
  if k=='has_army_experience':return w['xp']>=D(v) if op=='>=' else w['xp']<D(v)
  if k=='has_subdoctrine_in_track':return v in w['selected']
  if k=='has_completed_track':return v in w['completed']
  if k=='is_mio_available':return (mio in w['available'])==(v=='yes')
  if k=='has_mio_policy_active':return v in w['active']
  raise AssertionError(k)
 return all(one(*n) for n in ns)
def run(ns,w):
 matched=False
 for k,op,v in ns:
  if k in ('if','else_if','else'):
   if k=='if':matched=False
   if not matched and (k=='else' or check(get(v,'limit'),w)):
    run([n for n in v if n[0]!='limit'],w);matched=True
  elif k=='army_experience':w['xp']+=D(v)
  elif k=='add_mastery':
   t=get(v,'track');w['gain'][t]=w['gain'].get(t,D(0))+D(get(v,'amount'))
  elif k=='add_to_variable':
   t,_,amount=v[0];w['total'][t]=w['total'].get(t,D(0))+D(amount)
  else:raise AssertionError(k)
for level,gain in [(1,'0.6'),(2,'1'),(3,'1.5')]:
 w=world(level);run(fx,w)
 assert w['xp']==D('.7') and all(w['gain'][t]==D(gain) for t in tracks)
 assert all(v==D(gain) for v in w['total'].values())
for field in ['flags','selected','active','available']:
 w=world();w[field]=set();run(fx,w);assert w['xp']==1 and not w['gain'],field
w=world();w['completed']=set(tracks);run(fx,w);assert w['xp']==1 and not w['gain']
for xp,count in [('0',0),('.09',0),('.1',1),('.2',2),('.3',3)]:
 w=world(xp=xp);run(fx,w);assert len(w['gain'])==count and w['xp']>=0
w=world(3,'9')
for _ in range(30):run(fx,w)
assert w['xp']==0 and all(v==45 for v in w['gain'].values())
w=world(1);run(fx,w);w['flags'].update(f'RUS_tesla_doctrine_{t}_3' for t in tracks);run(fx,w)
assert all(v==D('2.1') for v in w['gain'].values())
w['active']=set();before=copy.deepcopy(w);run(fx,w);assert w==before
org=(R/'common/military_industrial_organization/organizations/RUS_tesla_organization.txt').read_text()
assert len(re.findall(r'token = RUS_tesla_doctrine_\w+_[123]\b',org))==9
for t in tracks:
 for l in (1,2,3):assert f'token = RUS_tesla_doctrine_{t}_{l}' in org
loc=(R/'localisation/simp_chinese/RUS_tesla_doctrine_l_simp_chinese.yml').read_bytes()
assert loc.startswith(b'\xef\xbb\xbf')
keys=re.findall(r'^\s+(\w+):',loc.decode('utf-8-sig'),re.M)
assert len(keys)==len(set(keys))
print('PASS: 9 traits; tier rewards; all pause gates; exact/insufficient XP; 30-day totals; live upgrade/removal; BOM and unique localisation keys. Not an engine test.')
