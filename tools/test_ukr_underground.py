"""Regression scenarios; helper imports do not execute other tests."""
from test_support.ukr_underground import *

count=0
def ok():
    global count;count+=1
# Upfront debit, completion boundary, non-stacking, once-only, cooldown after cancellation.
w=world();start('mine',w);assert w['RUS']['pp']==965 and consumer_burden(w)==.03
tick(w,44);assert 'RUS_ukr_mine_network' not in w['RUS']['flags']
tick(w);assert w['RUS']['vars']['RUS_ukr_strength']==15 and not allowed('mine',w)
assert consumer_burden(w)==0;ok()
# Two operations of the same country may run side by side: each keeps its own
# timer, modifier burden and result, and both settle independently.
w=world();start('mine',w);assert allowed('families',w);start('families',w)
assert w['RUS']['pp']==940 and consumer_burden(w)==.05
tick(w,29);assert 'RUS_ukr_mine_network' not in w['RUS']['flags'] and w['RUS']['vars']['RUS_ukr_strength']==0
tick(w);assert w['RUS']['vars']['RUS_ukr_strength']==15 and consumer_burden(w)==.03
tick(w,15);assert w['RUS']['vars']['RUS_ukr_strength']==30 and consumer_burden(w)==0
assert not allowed('mine',w) and not allowed('families',w);ok()
for target,change in [('UKR',lambda c:c.update(exists=False)),('UKR',lambda c:c.update(cap=True)),('UKR',lambda c:c.update(socialist=True)),('UKR',lambda c:c.update(faction='RUS')),('RUS',lambda c:c.update(socialist=False)),('RUS',lambda c:c.update(subject=True))]:
    w=world();start('families',w);tick(w,29);change(w[target]);tick(w)
    assert w['RUS']['vars']['RUS_ukr_strength']==0 and w['RUS']['pp']==975
    assert not w['RUS']['ideas'] and 'RUS_ukr_families_cooldown' in w['RUS']['flags'];ok()
w=world();start('rural',w);war(w);tick(w)
assert w['RUS']['equipment']==9500 and 'RUS_ukr_rural_done' not in w['RUS']['flags'];ok()
# Every alert/land surcharge combination, at exact affordability boundaries.
for a in [49,50,79]:
    for reform in [69,70]:
        w=world();nets(w,'rural');alert(w,a);strength(w,15)
        w['UKR']['vars']['UKR_land_reform_score']=reform
        cost=25+10*(a>=50)+10*(reform>=70);w['RUS']['pp']=cost-.01
        assert not allowed('land',w);w['RUS']['pp']=cost;assert allowed('land',w)
        start('land',w);assert w['RUS']['pp']==0
        assert w['RUS']['vars']['RUS_ukr_strength']==15-10-5*(reform>=70);ok()
w=world();alert(w,79);w['RUS']['pp']=20;start('relocate',w);tick(w,30)
assert w['RUS']['pp']==0 and w['RUS']['vars']['RUS_ukr_alert']==59;ok()
# No equipment overdraft.
w=world();w['RUS']['equipment']=499;assert not allowed('rural',w);w['RUS']['equipment']=500;start('rural',w);assert w['RUS']['equipment']==0;ok()
# Calm needs 30 uninterrupted idle days; relocation cooldown ends after completion+60.
w=world();alert(w,50);tick(w,29);assert w['RUS']['vars']['RUS_ukr_alert']==50
tick(w);assert w['RUS']['vars']['RUS_ukr_alert']==45
start('relocate',w);tick(w,30);assert not allowed('relocate',w);tick(w,59);assert not allowed('relocate',w);tick(w);alert(w,20);assert allowed('relocate',w);ok()
# Raid at >=80 exactly once; no action while pending; clamped strength and valid random networks.
for choice in range(3):
    w=world();nets(w,'mine','rural','rail');strength(w,20);alert(w,65)
    start('strike',w);tick(w,30);assert len(w['RUS']['events'])==1 and not allowed('relocate',w)
    tick(w,40);assert len(w['RUS']['events'])==1 and w['RUS']['vars']['RUS_ukr_alert']==80
    run(FX['RUS_ukr_raid_abandon'],w['RUS'],w,choice)
    disabled=[k for k in w['RUS']['flags'] if k.endswith('_disabled')]
    assert len(disabled)==1 and w['RUS']['vars']['RUS_ukr_strength']==0
    tick(w,89);assert disabled[0] in w['RUS']['flags'];tick(w);assert disabled[0] not in w['RUS']['flags'];ok()
w=world();nets(w,'rail');w['RUS']['flags']['RUS_ukr_raid_pending']=None
run(FX['RUS_ukr_raid_abandon'],w['RUS'],w,2);assert 'RUS_ukr_rail_disabled' in w['RUS']['flags'];ok()
w=world();w['RUS']['flags']['RUS_ukr_raid_pending']=None;run(FX['RUS_ukr_raid_abandon'],w['RUS'],w);assert not any(k.endswith('_disabled') for k in w['RUS']['flags']);ok()
w=world();nets(w,'rail');w['RUS']['flags']['RUS_ukr_raid_pending']=None;strength(w,20)
run(FX['RUS_ukr_raid_evacuate'],w['RUS'],w);assert w['RUS']['vars']['RUS_ukr_strength']==10
start('mine',w);assert abs(consumer_burden(w)-.07)<1e-8
tick(w,30);assert 'RUS_ukr_emergency_burden' not in w['RUS']['ideas'];ok()
# A stale event after war starts cannot debit or damage anything.
w=world();w['RUS']['flags']['RUS_ukr_raid_pending']=None;war(w);tick(w);snapshot=copy.deepcopy(w)
run(FX['RUS_ukr_raid_abandon'],w['RUS'],w);run(FX['RUS_ukr_raid_evacuate'],w['RUS'],w);assert w==snapshot;ok()
# Stability loss capped at nine percentage points, even with repeated strikes.
w=world();nets(w,'mine')
for _ in range(4):
    strength(w,100);alert(w,0);start('strike',w);tick(w,30);tick(w,120)
assert abs(w['UKR']['stability']-.71)<1e-8 and w['RUS']['vars']['RUS_ukr_strikes']==3;ok()
# All strength-tier edges, frozen network contribution, exact durations and war cleanup.
for power,tier,duration in [(40,'low',30),(59,'low',30),(60,'medium',45),(79,'medium',45),(80,'high',60),(100,'high',60)]:
    w=world();war(w);nets(w,'mine','rural','rail');strength(w,power)
    w['UKR']['ideas']['RUS_ukr_mine_strike']=90
    start('night',w);assert w['RUS']['vars']['RUS_ukr_strength']==0
    tick(w,6);assert 'RUS_ukr_war_'+tier not in w['UKR']['ideas'];tick(w)
    assert w['UKR']['ideas']=={'RUS_ukr_war_'+tier:duration,'RUS_ukr_war_mine':duration,'RUS_ukr_war_rural':duration}
    assert w['RUS']['ideas']['RUS_ukr_war_attack']==duration and not allowed('night',w)
    assert not w['RUS']['events'];tick(w,89);assert w['RUS']['vars']['RUS_ukr_alert']==100
    tick(w);assert w['RUS']['vars']['RUS_ukr_alert']==40;ok()
w=world();war(w);nets(w,'mine','rural');strength(w,60);start('night',w);tick(w,6);peace(w);tick(w)
assert w['RUS']['vars']['RUS_ukr_strength']==60 and w['RUS']['equipment']==9000 and w['RUS']['pp']==950
assert 'RUS_ukr_night_done' not in w['RUS']['flags'] and not w['UKR']['ideas'];ok()
w=world();war(w);nets(w,'rural','rail');strength(w,80);start('night',w);tick(w,7)
assert 'RUS_ukr_war_mine' not in w['UKR']['ideas'];peace(w);tick(w)
assert not w['UKR']['ideas'] and not w['RUS']['ideas'];ok()
# Structural guardrails, localization key parity, intentional blank event text, resolved scripts.
newfiles=list(ROOT.glob('common/**/RUS_ukr_*.txt'))+list(ROOT.glob('events/RUS_ukr_*.txt'))
for f in newfiles:
    source=f.read_text(encoding='utf-8-sig');parse(source)
    assert not re.search(r'\b(add_to_faction|remove_from_faction|set_politics|start_civil_war|add_stability = -0.1)\b',source)
    for call in re.findall(r'\b(RUS_ukr_\w+) = (?:yes|no)\b',source):assert call in FX or call in TR,call
languages=[]
for lang in ['simp_chinese','english','russian']:
    p=ROOT/f'localisation/{lang}/RUS_ukr_underground_l_{lang}.yml';assert p.read_bytes().startswith(b'\xef\xbb\xbf')
    rows=re.findall(r'^ ([^:]+):0 "(.*)"$',p.read_text(encoding='utf-8-sig'),re.M)
    keys=dict(rows);assert len(keys)==len(rows)
    for suffix in ['t','d','a','b']:assert keys['RUS_ukr_underground.1.'+suffix]==''
    for name,d in D.items():
        cost=get(d,'custom_cost_text')
        if cost:
            assert cost in keys and cost+'_blocked' in keys,(lang,cost)
        if name!='RUS_ukr_status':
            assert int(get(d,'days_remove',0))>0 and get(d,'remove_effect') and get(d,'cancel_effect'),name
            assert 'requirements_tt' not in str(get(d,'available'))
            assert 'result_tt' not in str(get(d,'complete_effect'))
    languages.append(set(keys))
assert languages[0]==languages[1]==languages[2];ok()
# Native action stays visible in the engine's active-decision registry until completion.
w=world();start('families',w);assert w['RUS']['decisions'];tick(w,29);assert w['RUS']['decisions'];tick(w);assert not w['RUS']['decisions'];ok()
# Both Ukraine focuses enumerate their actual unlocks with native focus tooltips.
from hoi4_politics_blocks import load as load_focus
focuses=load_focus(ROOT/'common/national_focus/00_RUS_future_foreign_policy_skeleton.txt')
flat=[n for root in focuses for n in (root.v if isinstance(root.v,list) else [])]+focuses
for fid,expected in [('RUS_future_foreign_037',set(D)-{'RUS_ukr_status','RUS_ukr_night'}),('RUS_future_foreign_059',{'RUS_ukr_night'})]:
    f=next(n for n in flat if n.value('id')==fid)
    assert {n.v for n in f.one('completion_reward').children('unlock_decision_tooltip')}==expected
ok()
# Sabotage selects five distinct railway states and three distinct infrastructure states.
def target_state(i,owner='UKR',controller='UKR',rail=1,infra=2):
    return dict(id=i,owner=owner,controller=controller,flags={},buildings={'rail_way':rail,'infrastructure':infra},damage={})
for choice in range(7):
    w=world();states=[target_state(i) for i in range(10)]+[target_state(10,owner='GER'),target_state(11,controller='GER'),target_state(12,rail=0,infra=0)]
    w['UKR']['states']=states
    run(FX['RUS_ukr_damage_transport'],w['UKR'],w,choice)
    assert sum(st['damage'].get('rail_way',0) for st in states)==5
    assert sum(st['damage'].get('infrastructure',0) for st in states)==3
    assert all(d==1 for st in states for d in st['damage'].values())
    assert all(not st['flags'] for st in states) and all(not st['damage'] for st in states[10:])
ok()
w=world();w['UKR']['states']=[target_state(0),target_state(1,rail=0),target_state(2,controller='GER')]
run(FX['RUS_ukr_damage_transport'],w['UKR'],w)
assert [st['damage'] for st in w['UKR']['states']]==[{'rail_way':1,'infrastructure':1},{'infrastructure':1},{}];ok()
# Native action waits until day 21, grants building damage once and no old timed penalty.
w=world();nets(w,'rail');strength(w,100);w['UKR']['states']=[target_state(i) for i in range(8)]
start('slowdown',w);tick(w,20);assert not any(st['damage'] for st in w['UKR']['states'])
tick(w);assert sum(st['damage'].get('rail_way',0) for st in w['UKR']['states'])==5
assert 'RUS_ukr_rail_slowdown' not in w['UKR']['ideas']
snapshot=copy.deepcopy(w['UKR']['states']);tick(w);assert w['UKR']['states']==snapshot;ok()
w=world();nets(w,'rail');strength(w,100);w['UKR']['states']=[target_state(i) for i in range(8)]
start('slowdown',w);tick(w,20);war(w);tick(w);assert not any(st['damage'] for st in w['UKR']['states']);ok()
# Reform damage: active KR missions, independent three-hit caps, zero floor and cancellation.
for action,variable,mission,amount,network in [('land','UKR_land_reform_score','UKR_landreform_mission',5,'rural'),('strike','UKR_industrial_score','UKR_industrialisation_mission',3,'mine')]:
    counter='RUS_ukr_'+action+'_score_hits'
    for initial,active,expected in [(50,True,50-amount),(2,True,0),(0,True,0),(50,False,50)]:
        w=world();w['UKR']['vars'][variable]=initial;w['UKR']['missions']={mission} if active else set()
        run(FX['RUS_ukr_reduce_'+action+'_score'],w['RUS'],w)
        assert w['UKR']['vars'][variable]==expected
        assert w['RUS']['vars'].get(counter,0)==int(expected<initial)
    ok()
    w=world();nets(w,network);w['UKR']['missions']={mission};w['UKR']['vars'][variable]=50
    for i in range(4):
        strength(w,100);alert(w,0);start(action,w);tick(w,29)
        assert w['UKR']['vars'][variable]==50-min(i,3)*amount
        tick(w);assert w['UKR']['vars'][variable]==50-min(i+1,3)*amount
        tick(w,120)
    assert w['RUS']['vars'][counter]==3
    other='strike' if action=='land' else 'land';assert w['RUS']['vars'].get('RUS_ukr_'+other+'_score_hits',0)==0
    ok()
    for cancel in [True,False]:
        w=world();nets(w,network);strength(w,100);w['UKR']['missions']={mission};w['UKR']['vars'][variable]=50
        start(action,w);tick(w,29)
        if cancel:war(w)
        else:w['UKR']['missions'].clear()
        tick(w);assert w['UKR']['vars'][variable]==50 and w['RUS']['vars'].get(counter,0)==0
    ok()
print(f'PASS: {count} scenario groups; executed actual decision/trigger/effect scripts. Game-engine and GUI QA still required.')
