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
FX={k:v for k,_,v in parse((R/'common/scripted_effects/RUS_tesla_doctrine_effects.txt').read_text())}
tracks=['armor','combat_support','operations']
mios=['RUS_tstz_organisation','RUS_obukhov_organisation','RUS_amo_organisation']
def world(level=1,xp='1',funds='2.56',lines=1):
 w=dict(vars={},xp=D(xp),flags={f'RUS_tesla_doctrine_{t}_{l}' for t in tracks for l in range(1,level+1)},selected=set(tracks),completed=set(),gain={})
 w['mios']={m:dict(vars={'funds':D('100')+D(funds),'RUS_tesla_previous_funds':D('100'),'RUS_tesla_manufacturers':D(lines)},flags={'RUS_tesla_funds_sampled'},active=f'RUS_tesla_doctrine_{t}_policy',available=True) for m,t in zip(mios,tracks)}
 return w
def val(v,c,prev):
 try:return D(v)
 except Exception:
  if v.startswith('PREV.'):return val(v[5:],prev,c)
  if v=='army_experience':return c['xp']
  return c['vars'].get(v,D(0))
def check(ns,c,w,prev=None):
 def one(k,op,v):
  if k=='NOT':return not check(v,c,w,prev)
  if k.startswith('mio:'):return check(v,w['mios'][k[4:]],w,c)
  if k in ['has_country_flag','has_mio_flag']:return v in c['flags']
  if k=='has_army_experience':return c['xp']<D(v)
  if k=='has_subdoctrine_in_track':return v in c['selected']
  if k=='has_completed_track':return v in c['completed']
  if k=='has_mio_policy_active':return c['active']==v
  if k=='is_mio_available':return c['available']==(v=='yes')
  if k=='check_variable':
   a,o,b=v[0];a=val(a,c,prev);b=val(b,c,prev)
   return a<b if o=='<' else a>b if o=='>' else a==b
  raise AssertionError(k)
 return all(one(*n) for n in ns)
def run(ns,c,w,prev=None):
 matched=False
 for k,op,v in ns:
  if k in ['if','else_if','else']:
   if k=='if':matched=False
   if not matched and (k=='else' or check(get(v,'limit'),c,w,prev)):
    run([n for n in v if n[0]!='limit'],c,w,prev);matched=True
  elif k.startswith('mio:'):run(v,w['mios'][k[4:]],w,c)
  elif k=='PREV':run(v,prev,w,c)
  elif k in FX:run(FX[k],c,w,prev)
  elif k=='army_experience':c['xp']+=val(v,c,prev)
  elif k=='set_mio_flag':c['flags'].add(v)
  elif k=='add_mastery':
   t=get(v,'track');c['gain'][t]=c['gain'].get(t,D(0))+D(get(v,'amount'))
  elif k in ['set_variable','set_temp_variable','add_to_variable','subtract_from_variable','multiply_temp_variable']:
   a,_,b=v[0];n=val(b,c,prev);old=c['vars'].get(a,D(0))
   c['vars'][a]=old+n if k=='add_to_variable' else old-n if k=='subtract_from_variable' else old*n if k=='multiply_temp_variable' else n
  elif k=='clamp_variable':
   a=get(v,'var');c['vars'][a]=max(c['vars'].get(a,D(0)),D(get(v,'min')))
  else:raise AssertionError(k)
def tick(w):run(FX['RUS_tesla_doctrine_daily_tick'],w,w)
for level,gain in [(1,'.50'),(2,'.75'),(3,'1.00')]:
 w=world(level);tick(w);assert w['xp']==D('.7') and all(w['gain'][t]==D(gain) for t in tracks)
 assert all(w['vars'][f'RUS_tesla_doctrine_{t}_total']==D(gain) for t in tracks)
for funds,expected in [('0',False),('2.55',False),('2.56',True),('155.6',True)]:
 w=world(funds=funds);tick(w);assert bool(w['gain'])==expected and w['xp']==D('.7')
for lines,expected in [(0,False),(1,True),(12,True)]:
 w=world(lines=lines);tick(w);assert bool(w['gain'])==expected and w['xp']==D('.7')
 if expected:assert w['gain']['armor']==D('.5')
for field in ['selected','completed','available']:
 w=world()
 if field=='selected':w['selected']=set()
 elif field=='completed':w['completed']=set(tracks)
 else:
  for m in w['mios'].values():m['available']=False
 tick(w);assert not w['gain'] and w['xp']==D('.7')
w=world();
for m in w['mios'].values():m['active']=None
tick(w);assert w['xp']==1 and not w['gain']
for xp in ['0','.05','.1','.2']:
 w=world(xp=xp);tick(w);assert w['xp']==0 and len(w['gain'])==3
w=world(funds='100000')
for m in w['mios'].values():m['flags']=set()
tick(w);assert not w['gain'] # no historical-funds windfall on first sample
w=world(3,'9')
for i in range(30):
 if i:
  for m in w['mios'].values():m['vars']['funds']+=D('2.56')
 tick(w)
assert w['xp']==0 and all(v==30 for v in w['gain'].values())
loc=(R/'localisation/simp_chinese/RUS_tesla_doctrine_l_simp_chinese.yml').read_bytes()
assert loc.startswith(b'\xef\xbb\xbf')
keys=re.findall(r'^\s+(\w+):',loc.decode('utf-8-sig'),re.M);assert len(keys)==len(set(keys))
assert '2.56' in loc.decode('utf-8-sig')
print('PASS: funding threshold 2.55/2.56, independent upkeep, all tiers, production requirement, no line stacking, sample baseline, removal, zero-XP clamp and 30-day totals. Not an engine test.')
