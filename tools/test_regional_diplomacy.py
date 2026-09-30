"""Regression scenarios; helper imports do not execute other tests."""
from test_support.regional_diplomacy import *

actions=[k for k,v in D.items() if get(v,'complete_effect')]
assert len(actions)==19 and len(D)==25
for id in actions:
    t=id.split('_')[2];resource=f'RUS_rd_{t}_stock';cap=3 if t in TAGS[:4] else 100
    for discounted in [False,True]:
        w=world();ready(id,w);c=w['RUS'];d=D[id]
        if discounted:c['flags']['RUS_diplomacy_pp_discount']=None
        source=FX[id+'_start'];pay=next(int(k.rsplit('_',1)[1]) for k,_,_ in source if k.startswith('RUS_diplomacy_pay_'))*(.8 if discounted else 1)
        c['pp']=pay-.01;assert not check(get(d,'custom_cost_trigger'),c,w)
        c['pp']=pay;assert check(get(d,'custom_cost_trigger'),c,w)
        before=c['vars'][resource];start(id,w)
        assert abs(c['pp'])<1e-8 and c['balance']==.005
        assert c['vars'][resource]<=before and not w[t]['ideas']
        # A running decision cannot be taken twice - the engine blocks it, not
        # the busy flag, now that several actions may run side by side.
        assert id in c['decisions']
        tick(w,int(get(d,'days_remove'))-1)
        assert id in c['decisions'] and not w[t]['ideas']
        tick(w);assert id not in c['decisions'] and 0<=c['vars'][resource]<=cap
        assert c['balance']==.005 and c['vars'][f'RUS_rd_{t}_remaining']==0
        saved=snap(w);run(get(d,'remove_effect'),c,w);assert w==saved,'double settlement '+id
    # Cancellation and a later engine remove callback cannot grant a reward/refund.
    for invalid in ['cap','socialist','exists','faction']+(['peace'] if get(D[id],'days_remove') and 'has_war_with' in str(D[id]) else []):
        w=world();ready(id,w);c=w['RUS'];start(id,w)
        if invalid=='peace':c['war'].clear()
        else:w[t][invalid]={'cap':True,'socialist':True,'exists':False,'faction':'OTHER'}[invalid]
        pp=c['pp'];stock=c['vars'][resource];equipment=copy.deepcopy(c['equipment']);tick(w)
        assert id not in c['decisions'] and not w[t]['ideas'] and not c.get('units')
        assert c['pp']==pp and c['equipment']==equipment and c['vars'][resource]==stock
        assert c['balance']==.005 and all(not p['damage'] for p in w['_provinces'])
    # Force the exposure branch for actions with risk.
    if 'random_list' in str(FX[id+'_finish']):
        w=world();ready(id,w);c=w['RUS'];start(id,w);stock=c['vars'][resource]
        tick(w,int(get(D[id],'days_remove')),choice=1)
        assert c['flags'][f'RUS_rd_{t}_lock']==30 and not w[t]['ideas'] and not c.get('units')
        assert c['vars'][resource]==max(0,stock-(1 if cap==3 else 10))
        assert all(not p['damage'] for p in w['_provinces'])
        tick(w,30);assert f'RUS_rd_{t}_lock' not in c['flags'] and c['vars'][f'RUS_rd_{t}_lock_days']==0

# Country isolation, stock generation/caps and idempotent initialization.
w=world();c=w['RUS']
for id in ['RUS_rd_BAT_press','RUS_rd_LIT_press','RUS_rd_GEO_stations','RUS_rd_AZR_stations','RUS_rd_BLR_supplies','RUS_rd_POL_contact']:start(id,w)
tick(w,21)
assert [c['vars'][f'RUS_rd_{t}_stock'] for t in TAGS]==[1,1,1,1,25,35]
assert abs(c['balance']-.03)<1e-9
for t in TAGS:
    stock=c['vars'][f'RUS_rd_{t}_stock'];run(FX[f'RUS_rd_{t}_init'],c,w);assert c['vars'][f'RUS_rd_{t}_stock']==stock
for id in ['RUS_rd_BAT_press','RUS_rd_BLR_supplies','RUS_rd_POL_training']:
    w=world();c=w['RUS'];t=id.split('_')[2];cap=3 if t=='BAT' else 100
    c['vars'][f'RUS_rd_{t}_stock']=cap-1;start(id,w);tick(w,30)
    assert c['vars'][f'RUS_rd_{t}_stock']==cap

# Several actions of the same country may run in parallel: each keeps its own
# timer, cooldown and result, and the shared resource settles per action.
w=world();c=w['RUS'];c['vars']['RUS_rd_BAT_stock']=2
start('RUS_rd_BAT_press',w);start('RUS_rd_BAT_unions',w)
assert set(c['decisions'])=={'RUS_rd_BAT_press','RUS_rd_BAT_unions'}
assert c['vars']['RUS_rd_BAT_stock']==1
tick(w,14)
assert 'RUS_rd_BAT_press' not in c['decisions'] and 'RUS_rd_BAT_unions' in c['decisions']
assert c['vars']['RUS_rd_BAT_stock']==2 and c['flags']['RUS_rd_BAT_press_cooldown']==60
tick(w,7)
assert not c['decisions'] and w['BAT']['ideas'].get('RUS_rd_transport_resistance')==45
assert c['flags']['RUS_rd_BAT_unions_cooldown']==90 and c['vars']['RUS_rd_BAT_stock']==2

# Both raid variants hit every Belarus-controlled province, preserve foreign forts
# and leave non-fort infrastructure unchanged. Courier advantage is consumed once.
for id in ['RUS_rd_BLR_raids','RUS_rd_BLR_raids_fast']:
    w=world();ready(id,w);c=w['RUS'];start(id,w)
    assert 'RUS_rd_BLR_couriers_ready' not in c['flags']
    assert check(get(D[id],'visible'),c,w)
    tick(w,int(get(D[id],'days_remove')))
    for p in w['_provinces']:
        if p['controller']=='BLR':assert p['damage']=={k:p['buildings'][k] for k in ['bunker','coastal_bunker']}
        else:assert not p['damage']
        assert p['buildings']['rail_way']==4
    assert c['flags']['RUS_rd_BLR_raids_cooldown']==90

# Militia only appear on eligible Russian border states; cap is lifetime and
# separate per target. No common border cannot consume a spawn allowance.
for t,a in [('GEO','militias'),('AZR','militias'),('BLR','supplies'),('POL','training')]:
    id=f'RUS_rd_{t}_{a}';w=world();ready(id,w);c=w['RUS'];start(id,w);tick(w,int(get(D[id],'days_remove')))
    run(FX['RUS_rd_deploy_reserved_militias'],c,w)
    assert c['units']==[t+'_enemy'] and c['vars'][f'RUS_rd_{t}_militia_raised']==1
    fx=FX[f'RUS_rd_{t}_form_militia']
    run(fx,c,w);run(fx,c,w);assert c['units']==[t+'_enemy',t+'_enemy']
    assert c['vars'][f'RUS_rd_{t}_militia_raised']==2
    template=next(iter(c['templates'].values()))
    assert len(get(template,'regiments'))==4 and all(k=='militia' for k,_,_ in get(template,'regiments'))
    for mode in ['no_border','enemy_controlled','impassable']:
        w=world();c=w['RUS'];c['war'].clear()
        for s in c['states']:
            if mode=='no_border':s['neighbors']=[]
            elif mode=='enemy_controlled':s['controller']='GER'
            else:s['impassable']=True
        run(fx,c,w);assert not c.get('units') and c['vars'].get(f'RUS_rd_{t}_militia_raised',0)==0
    w=world();c=w['RUS'];c['war'].clear();run(fx,c,w);assert c['units']==[t]
    w=world();c=w['RUS'];w[t]['states'][0]['neighbors']=[];run(fx,c,w);assert not c.get('units')

# Integration: ten existing Ukraine actions get the same start reward, never
# status entries. Focus rewards are separate from idempotent resource setup.
ukr=(ROOT/'common/decisions/RUS_ukr_underground_decisions.txt').read_text(encoding='utf-8-sig')
assert len(re.findall(r'\bcomplete_effect\s*=\s*{',ukr))==ukr.count('RUS_rd_action_readiness = yes')==10
focus=(ROOT/'common/national_focus/00_RUS_future_foreign_policy_skeleton.txt').read_text(encoding='utf-8-sig')
for n in ['020','021','022','036']:
    body=focus.split('id = RUS_future_foreign_'+n,1)[1].split('\n\tfocus =',1)[0]
    assert 'add_political_power = 50' in body and 'RUS_rd_' in body
loc=(ROOT/'localisation/simp_chinese/RUS_regional_diplomacy_l_simp_chinese.yml').read_bytes()
assert loc.startswith(b'\xef\xbb\xbf')
keys=re.findall(r'^ ([A-Za-z0-9_]+):',loc.decode('utf-8-sig'),re.M)
assert len(keys)==len(set(keys))
for id in D:assert id in keys and id+'_desc' in keys
print('PASS: 19 action variants; transactions/discounts, readiness, cancellation, risk, timers, caps, parallel actions per country, country isolation, both fort-damage variants, border militia and integrations. Not a game-engine test.')
