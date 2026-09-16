"""Exercise our transactions; KR's influence redistribution is an external boundary."""
import runpy
from pathlib import Path
m=runpy.run_path(str(Path(__file__).with_name('test_regional_diplomacy.py')))
read,get,parse,run,check,world,start,tick=[m[k] for k in ['read','get','parse','run','check','world','start','tick']]
FX,D=m['FX'],m['D']
newfx={k:v for k,_,v in read('common/scripted_effects/RUS_polish_influence_effects.txt')}
FX.update(newfx)
# Model only the documented boundary input, not KR's competing-faction algorithm.
FX['POL_add_syndicalist_influence']=parse('add_to_variable = { POL_soc_influence = POL_influence_change }')
newdec={k:v for k,_,v in get(read('common/decisions/RUS_polish_influence_decisions.txt'),'RUS_Spreading_the_Revolution_decisions')};D.update(newdec)
assert len(newdec)==3
for key,pp,spend,days,gain in [('press',25,0,21,3),('unions',35,10,30,5),('workers_peasants',40,15,30,7)]:
    id='RUS_rd_POL_'+key
    for fail in [False,True]:
        w=world();c=w['RUS'];c['vars']['RUS_rd_POL_stock']=50;w['POL']['vars']['POL_soc_influence']=20
        start(id,w);assert c['pp']==1000-pp and c['vars']['RUS_rd_POL_stock']==50-spend and c['balance']==.005
        assert not check(get(D[id],'available'),c,w)
        tick(w,days-1);assert w['POL']['vars']['POL_soc_influence']==20
        tick(w,choice=int(fail));expected=0 if fail and key!='press' else gain
        assert w['POL']['vars']['POL_soc_influence']==20+expected
        if not expected:assert c['flags']['RUS_rd_POL_lock']==30
        run(get(D[id],'remove_effect'),c,w);assert w['POL']['vars']['POL_soc_influence']==20+expected
    w=world();c=w['RUS'];c['vars']['RUS_rd_POL_stock']=50;w['POL']['vars']['POL_soc_influence']=20
    start(id,w);w['POL']['socialist']=True;tick(w);assert w['POL']['vars']['POL_soc_influence']==20 and c['pp']==1000-pp
    w=world();assert not check(get(D[id],'available'),w['RUS'],w)
    w['POL']['vars']['POL_soc_influence']=100;assert not check(get(D[id],'available'),w['RUS'],w)
print('PASS: 3 Polish influence decisions; costs, readiness, delays, success/exposure, cancellation, eligibility and idempotence. Native KR effect is mocked at its boundary.')

# Failure alone halves cooldown, while success/cancellation retain normal timing.
cases={
 'BAT_unions':90,'BAT_boycott':120,'LIT_unions':90,'LIT_boycott':120,
 'GEO_militias':90,'GEO_fuel':120,'AZR_militias':90,'AZR_fuel':120,
 'BLR_raids':90,'BLR_raids_fast':90,'POL_training':90,'POL_cooperation':120,
 'POL_unions':120,'POL_workers_peasants':150,
}
for suffix,normal in cases.items():
    id='RUS_rd_'+suffix;tag=suffix.split('_')[0]
    cd=('RUS_rd_BLR_raids' if suffix=='BLR_raids_fast' else id)+'_cooldown'
    for outcome in ['success','failure','cancel']:
        w=world();c=w['RUS'];m['ready'](id,w);w['POL']['vars']['POL_soc_influence']=20
        start(id,w)
        if outcome=='cancel':w[tag]['cap']=True;tick(w)
        else:tick(w,int(get(D[id],'days_remove')),choice=int(outcome=='failure'))
        assert c['flags'][cd]==(normal//2 if outcome=='failure' else normal),(id,outcome,c['flags'])
        assert id+'_failed' not in c['flags']
        if outcome=='failure':
            half=normal//2
            tick(w,half-1);assert cd in c['flags']
            tick(w);assert cd not in c['flags'] and f'RUS_rd_{tag}_lock' not in c['flags']
            m['ready'](id,w);assert check(get(D[id],'available'),c,w)
print('PASS: all 14 risky actions halve only failure cooldown; actual reavailability, shared raid cooldown, success and cancellation checked.')
