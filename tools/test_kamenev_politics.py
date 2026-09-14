"""Regression checks against the installed KR baseline; no game launch."""
from hoi4_politics_blocks import *
from dataclasses import replace
ROUTE='RUS_uses_kamenev_politics'
def norm(ns):return tuple(n.norm() for n in ns)
def body(n):return n.v if n else []
def stock_trigger(ns):
 # Project the explicit route gate while retaining original KR predicates verbatim.
 if len(ns)==1 and ns[0].k=='OR':
  arms=ns[0].children('AND')
  if len(arms)==2 and all(a.one(ROUTE) for a in arms):
   return [x for x in next(a for a in arms if a.value(ROUTE)=='no').v if x.k!=ROUTE]
 return ns

def stock_effect(ns):
 if ns and ns[0].k=='if' and norm(body(ns[0].one('limit')))==norm(parse(ROUTE+' = yes')):
  assert len(ns)==2 and ns[1].k=='else'
  return ns[1].v
 return ns

mr=roles(data(R/'common/characters/RUS characters.txt','characters'));br=roles(data(KR/'common/characters/RUS characters.txt','characters'))
count=0
for key,(char,a) in mr.items():
 if a.value('slot') not in ['political_advisor','second_in_command']:continue
 if key not in br:
  assert a.one('visible').value(ROUTE)=='yes',key;continue
 b=br[key][1]
 for field in ['available','visible']:
  assert norm(stock_trigger(body(a.one(field))))==norm(body(b.one(field))),(key,field)
 for field in ['on_add','on_remove']:
  assert norm(stock_effect(body(a.one(field))))==norm(body(b.one(field))),(key,field)
 for field in ['traits','allowed']:
  assert norm(body(a.one(field)))==norm(body(b.one(field))),(key,field)
 count+=1
print('PASS: stock requirements, traits and hiring callbacks for',count,'shared adviser roles.')
base=data(KR/'common/national_focus/RUS focus (Russia).txt','focus_tree');mod=data(R/'common/national_focus/RUS focus (Russia).txt','focus_tree');mf={n.value('id'):n for n in mod.children('focus')}
lo=base.s.index('### Socialist Tree');hi=base.s.index('### SocRus foreign policy');count=0
for b in base.children('focus'):
 if not lo<b.a<hi or b.value('id')=='RUS_syndicalists':continue
 a=mf[b.value('id')]
 for field in ['completion_reward','select_effect']:
  assert norm(stock_effect(body(a.one(field))))==norm(body(b.one(field))),(b.value('id'),field)
 assert a.value('cost')==b.value('cost'),b.value('id')
 st=stock_trigger(body(a.one('available')));bt=body(b.one('available'))
 if norm(a.children('prerequisite'))!=norm(b.children('prerequisite')):
  expected=parse('\n'.join('OR = { '+' '.join('has_completed_focus = '+x.v for x in p.v if x.k=='focus')+' }' for p in b.children('prerequisite')))
  assert norm(st)==norm(bt+expected),b.value('id')
 else:assert norm(st)==norm(bt),b.value('id')
 count+=1
print('PASS: original effects, durations and requirements for',count,'shared socialist focuses.')
be={n.value('id'):n for n in load(KR/'events/RUS events (Russia).txt') if n.k=='country_event' and n.value('id').startswith('russia_socialist_events.')};count=0
for a in load(R/'events/RUS events (Russia).txt'):
 if a.k!='country_event' or a.value('id') not in be:continue
 b=be[a.value('id')]
 for field in ['immediate','after']:assert norm(stock_effect(body(a.one(field))))==norm(body(b.one(field))),(a.value('id'),field)
 assert norm(stock_trigger(body(a.one('trigger'))))==norm(body(b.one('trigger'))),a.value('id')
 opts=[]
 for o in a.children('option'):
  t=o.one('trigger')
  if t and t.one(ROUTE):
   if t.value(ROUTE)=='yes':continue
   remaining=[x for x in t.v if x.k!=ROUTE]
   old=b.children('option')[len(opts)].one('trigger')
   vals=[replace(x,v=remaining) if x.k=='trigger' else x for x in o.v if x.k!='trigger' or old is not None]
   o=replace(o,v=vals)
  opts.append(o)
 assert norm(opts)==norm(b.children('option')),a.value('id');count+=1
print('PASS: stock option sets and event effects for',count,'socialist events.')
for key in ['RUS_vst_party_unity_modifier','RUS_vst_party_factionalism_modifier']:
 assert data(R/'common/dynamic_modifiers/RUS stalin dynamic_modifiers.txt',key).norm()==data(KR/'common/dynamic_modifiers/RUS dynamic_modifiers (Russia).txt',key).norm()
print('PASS: original VST dynamic modifiers.')
# All maintained runtime files parse; newly added localization has BOM and no duplicate keys.
for p in list(R.glob('common/**/RUS_kamenev_politics*.txt')):load(p)
for lang in ['simp_chinese','english','russian']:
 p=R/f'localisation/{lang}/RUS_kamenev_politics_l_{lang}.yml';assert p.read_bytes().startswith(b'\xef\xbb\xbf')
 keys=re.findall(r'^ ([^:]+):',p.read_text(encoding='utf-8-sig'),re.M);assert len(keys)==len(set(keys))
print('PASS: route definitions and localization integrity. Engine QA still required.')
# Exercise the shipped route switch, including repeated refreshes and inherited KR traits.
fx=data(R/'common/scripted_effects/RUS_kamenev_politics_effects.txt','RUS_sync_political_advisor_route')
chars={c.k:c for c,_ in mr.values()};traits={}
for key,(c,a) in mr.items():
 slot=a.value('slot')
 if slot in ['political_advisor','second_in_command']:traits[c.k,slot]=set(tokens(a.one('traits')))
initial={k:set(v) for k,v in traits.items()};flags=set();route=False

def check(ns,scope=None):
 vals=[]
 for n in ns:
  if n.k==ROUTE:v=route==(n.v=='yes')
  elif n.k=='has_character':v=n.v in chars
  elif n.k=='has_country_flag':v=n.v in flags
  elif n.k=='has_trait':v=any(n.v in ts for (ch,slot),ts in traits.items() if ch==scope)
  elif n.k=='NOT':v=not check(n.v,scope)
  elif n.k=='AND':v=check(n.v,scope)
  elif n.k in chars:v=check(n.v,n.k)
  else:raise AssertionError(('unhandled trigger',n.k))
  vals.append(v)
 return all(vals)

def execute(ns):
 selected=False
 for n in ns:
  if n.k in ['if','else_if','else']:
   if n.k=='if':selected=False
   yes=(n.k=='if' or not selected) and (n.k=='else' or check(body(n.one('limit'))))
   if yes:execute([x for x in n.v if x.k!='limit']);selected=True
  elif n.k in ['add_trait','remove_trait']:
   ts=traits[n.value('character'),n.value('slot')];t=n.value('trait')
   if n.k=='add_trait':assert t not in ts;ts.add(t)
   else:assert t in ts;ts.remove(t)
  elif n.k=='set_country_flag':flags.add(n.v)
  elif n.k=='clr_country_flag':flags.discard(n.v)
  elif n.k.startswith('RUS_stalin_clear_') and n.k.endswith('_advisor_trait_tiers'):pass
  else:raise AssertionError(('unhandled effect',n.k))
execute(fx.v);assert traits==initial
route=True;execute(fx.v)
assert 'RUS_relationship_display_sverdlov' in traits['RUS_yakov_sverdlov','political_advisor']
assert 'KR_red_eminence' not in traits['RUS_yakov_sverdlov','political_advisor']
inside={k:set(v) for k,v in traits.items()};execute(fx.v);assert traits==inside
route=False;execute(fx.v);assert traits==initial
traits['RUS_yakov_sverdlov','political_advisor'].discard('KR_red_eminence');execute(fx.v)
assert 'KR_red_eminence' not in traits['RUS_yakov_sverdlov','political_advisor']
print('PASS: route switching is reversible and idempotent; later KR trait changes remain intact.')
