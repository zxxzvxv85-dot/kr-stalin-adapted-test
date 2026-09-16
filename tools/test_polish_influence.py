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
        if not expected:assert c['flags']['RUS_rd_POL_lock']==60
        run(get(D[id],'remove_effect'),c,w);assert w['POL']['vars']['POL_soc_influence']==20+expected
    w=world();c=w['RUS'];c['vars']['RUS_rd_POL_stock']=50;w['POL']['vars']['POL_soc_influence']=20
    start(id,w);w['POL']['socialist']=True;tick(w);assert w['POL']['vars']['POL_soc_influence']==20 and c['pp']==1000-pp
    w=world();assert not check(get(D[id],'available'),w['RUS'],w)
    w['POL']['vars']['POL_soc_influence']=100;assert not check(get(D[id],'available'),w['RUS'],w)
print('PASS: 3 Polish influence decisions; costs, readiness, delays, success/exposure, cancellation, eligibility and idempotence. Native KR effect is mocked at its boundary.')
