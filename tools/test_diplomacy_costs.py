"""Execute actual diplomatic cost helpers and decision costs; does not launch HOI4."""
import copy,re
import test_ukr_underground as t
from hoi4_politics_blocks import load
R=t.ROOT;cases=0
for a in [10,15,20,24,25,30,35,40,45,50,60,75,200]:
 for reduced in [False,True]:
  w=t.world();c=w['RUS']
  if reduced:c['focus'].add('RUS_future_foreign_008')
  expected=a*(.8 if reduced else 1)
  for money,allowed in [(expected-.01,False),(expected,True),(expected+.01,True)]:
   c['pp']=money;assert t.check(t.TR[f'RUS_diplomacy_can_pay_{a}'],c,w)==allowed
  c['pp']=1000;t.run(t.FX[f'RUS_diplomacy_pay_{a}'],c,w);assert abs(c['pp']-(1000-expected))<1e-8
  t.run(t.FX['RUS_diplomacy_refresh_pp_costs'],c,w);assert abs(c['vars'][f'RUS_diplomacy_pp_cost_{a}']-expected)<1e-8
  cases+=1
# Check the complete Ukraine invoice, including high-alert and land-reform surcharges.
for action in ['families','mine','rural','rail','relocate','declaration','strike','land','slowdown','night']:
 for warning in [0,50]:
  for landscore in [0,70]:
   before=t.world();t.strength(before,100);t.alert(before,warning);before['UKR']['vars']['UKR_land_reform_score']=landscore
   normal=copy.deepcopy(before);cheap=copy.deepcopy(before);cheap['RUS']['focus'].add('RUS_future_foreign_008')
   for w in [normal,cheap]:t.run(t.FX['RUS_ukr_start_'+action],w['RUS'],w)
   fee=1000-normal['RUS']['pp'];assert abs((1000-cheap['RUS']['pp'])-fee*.8)<1e-8
   assert cheap['RUS']['equipment']==normal['RUS']['equipment']
   assert cheap['RUS']['vars']['RUS_ukr_strength']==normal['RUS']['vars']['RUS_ukr_strength']
   before['RUS']['focus'].add('RUS_future_foreign_008');before['RUS']['pp']=fee*.8
   assert t.check(t.TR['RUS_ukr_can_pay_'+action],before['RUS'],before)
   before['RUS']['pp']-=.01;assert not t.check(t.TR['RUS_ukr_can_pay_'+action],before['RUS'],before)
   cases+=1
# Existing aid discounts are resolved first; the global factor then applies once.
for kind,rel,key in [('fx','common/scripted_effects/RUS_future_foreign_cooperation_effects.txt','RUS_future_foreign_pay_aid_pp'),('tr','common/scripted_triggers/RUS_future_foreign_cooperation_triggers.txt','RUS_future_foreign_can_pay_aid_pp')]:
 n=next(n for n in load(R/rel) if n.k==key);(t.FX if kind=='fx' else t.TR)[key]=t.parse(n.inner())
has_balkan_branch=any(k=='if' and 'RUS_future_foreign_has_balkan_aid_discount' in str(v) for k,_,v in t.FX['RUS_future_foreign_pay_aid_pp'])
for balkan,focus056,base in [(True,False,15),(True,True,15),(False,True,24),(False,False,30)]:
 if balkan and not has_balkan_branch:base=24 if focus056 else 30
 t.TR['RUS_future_foreign_has_balkan_aid_discount']=t.parse('always = '+('yes' if balkan else 'no'))
 for discounted in [False,True]:
  w=t.world();c=w['RUS']
  if focus056:c['focus'].add('RUS_future_foreign_056')
  if discounted:c['focus'].add('RUS_future_foreign_008')
  cost=base*(.8 if discounted else 1);c['pp']=cost
  assert t.check(t.TR['RUS_future_foreign_can_pay_aid_pp'],c,w)
  c['pp']-=.01;assert not t.check(t.TR['RUS_future_foreign_can_pay_aid_pp'],c,w)
  c['pp']=100;t.run(t.FX['RUS_future_foreign_pay_aid_pp'],c,w);assert abs(c['pp']-(100-cost))<1e-8;cases+=1
# Native decision coverage, initial fallback, immediate focus reward and saved-game refresh.
count=0
for p in (R/'common/decisions').glob('*.txt'):
 for cat in load(p):
  if cat.k!='RUS_Spreading_the_Revolution_decisions':continue
  for d in cat.v:
   if not isinstance(d.v,list):continue
   cost=d.value('cost')
   if cost and cost!='0':
    m=re.fullmatch(r'RUS_diplomacy_pp_cost_(\d+)\?(\d+)',cost);assert m,d.k;assert m[1]==m[2];count+=1
assert count>20
focus=next(n for n in load(R/'common/national_focus/00_RUS_future_foreign_policy_skeleton.txt') if n.value('id')=='RUS_future_foreign_008')
w=t.world();t.run(t.parse(focus.one('completion_reward').inner()),w['RUS'],w)
assert w['RUS']['vars']['RUS_diplomacy_pp_cost_200']==160
for lang in ['simp_chinese','english','russian']:
 p=R/f'localisation/{lang}/RUS_diplomacy_cost_l_{lang}.yml';assert p.read_bytes().startswith(b'\xef\xbb\xbf')
 keys=re.findall(r'^ ([^:]+):',p.read_text(encoding='utf-8-sig'),re.M);assert len(keys)==len(set(keys))
print(f'PASS: {cases} cost cases; {count} native diplomatic decision costs; focus reward and localization. Runtime QA required.')
