"""Exercise new production chains through the actual generated game effects."""
from __future__ import annotations
import copy
import math
import random
from collections import Counter
from industrial_planning_catalog import PLANTS, STOCKS, PRODUCTS, STORED, PRICES, TERRAINS, DEPOSITS, allowed, region_plants, specialty
from test_factory_planning import (REGIONS, CELLS, HUBS, P, TR, opened, starter, sites, builds,
    select, call, put, v, check, gui_click, production_snapshot, geology_snapshot, path_to, invariants)


def close(a,b):assert math.isclose(a,b,abs_tol=1e-7),(a,b)


def complete_chain(rid,seed=73):
    """Funded fixture, not a claim that an advanced chain fits starting funds.

    Every placement uses the generated cost, terrain, route and region guards.
    No stocks or production yields are injected.
    """
    s=opened(seed);put(s,'budget',10000);call(s,f'select_region_{rid}')
    selected=[]
    for kind in region_plants(rid):
        p=PLANTS[kind]
        count=3 if kind==1 else 4 if kind==3 else 2 if kind==4 else 1
        for _ in range(count):
            options=[i for i in REGIONS[rid]['cells'] if v(s,f'n{i}_terrain')==p['terrain'] and v(s,f'n{i}_type')==0]
            assert options,(rid,kind)
            i=min(options,key=lambda i:len(path_to(s,i)))
            for j in path_to(s,i):
                while v(s,f'n{j}_rail')<3:builds(s,j,'rail')
            builds(s,i,kind,3);assert v(s,f'n{i}_type')==kind
            selected.append(i)
    return s,selected


def test_deposit_quotas_and_gates():
    count=0
    for seed in range(12):
        s=opened(seed)
        for r in REGIONS:
            rid=r['id'];counts=Counter(v(s,f'n{i}_terrain') for i in r['cells'])
            for terrain,key in TERRAINS.items():
                expected=r[key] if key in ('coal','iron') else DEPOSITS[rid].get(key,0)
                assert counts[terrain]==expected,(rid,key,counts,expected)
                if key not in ('coal','iron') and expected:
                    assert r['kr_resources']['aluminium' if key=='bauxite' else key]>0
            assert counts[0]>=9,'The guaranteed starter factory must still fit'
            for i in r['cells']:
                if v(s,f'n{i}_terrain')!=3:assert i==r['hub'] or path_to(s,i)
            count+=1
    s=opened();put(s,'budget',1000)
    for rid,r in enumerate(REGIONS):
        call(s,f'select_region_{rid}')
        plain=next(i for i in r['cells'] if v(s,f'n{i}_terrain')==0)
        for kind in PLANTS:
            if allowed(kind,rid):continue
            before=production_snapshot(s);builds(s,plain,kind)
            assert production_snapshot(s)==before
        for kind in region_plants(rid):
            if not PLANTS[kind]['terrain'] or kind<6:continue
            site=next(i for i in r['cells'] if v(s,f'n{i}_terrain')==PLANTS[kind]['terrain'])
            before=production_snapshot(s);builds(s,plain,kind)
            assert production_snapshot(s)==before
            builds(s,site,kind);assert v(s,f'n{site}_type')==kind
            select(s,site);cost=v(s,f'n{site}_paid');budget=v(s,'budget')
            call(s,'remove');call(s,'remove');close(v(s,'budget'),budget+cost)
        # A regional manufacturing button cannot execute through the other menu.
        select(s,plain);before=production_snapshot(s)
        gui_click(s,f'ip_r{rid}_build_{15+rid}');assert production_snapshot(s)==before
        gui_click(s,'ip_special_page');gui_click(s,f'ip_r{rid}_build_{15+rid}')
        assert v(s,f'n{plain}_type')==15+rid
        before=production_snapshot(s);call(s,'toggle_help')
        gui_click(s,f'ip_r{rid}_build_{15+rid}');gui_click(s,'ip_special_page')
        assert production_snapshot(s)==before
        call(s,'toggle_help');call(s,'build_page_0');count+=1
    return count


def test_multi_resource_conservation():
    s=opened();rng=random.Random(884);count=0
    for case in range(35):
        for r in REGIONS:
            prefix=f'r{r["id"]}_'
            for key in STOCKS:put(s,prefix+key,rng.random()*2)
            for kind,p in PLANTS.items():put(s,prefix+p['key']+'_capacity',rng.randrange(10) if allowed(kind,r['id']) else 0)
        before=production_snapshot(s);draws=s['draws'];call(s,'forecast')
        assert production_snapshot(s)==before and s['draws']==draws
        total_value=0
        for r in REGIONS:
            rid=r['id'];get=lambda key:v(s,f'r{rid}_'+key)
            outputs={k:get(p['key']+'_output') for k,p in PLANTS.items()}
            # Inventory and power conservation, independently summed over all
            # reported plant outputs (not copied from the sequential algorithm).
            for key in STOCKS:
                expected=get(key)+sum(outputs[k] for k,p in PLANTS.items() if p['output']==key)
                expected-=sum(outputs[k]*p['inputs'].get(key,0) for k,p in PLANTS.items())
                close(get('next_'+key),expected);assert get('next_'+key)>=0
            generated=sum(outputs[k] for k,p in PLANTS.items() if p['output']=='power')
            used=sum(outputs[k]*p['power'] for k,p in PLANTS.items())
            close(get('power_total'),generated);close(get('power_left'),generated-used)
            income=0
            for product in PRODUCTS:
                delivered=sum(outputs[k] for k,p in PLANTS.items() if p['output']==product)
                close(get('next_'+product)-get(product),delivered)
                income+=delivered*PRICES[product]
            close(get('investment_output'),income);close(get('next_value')-get('value'),income)
            for kind,p in PLANTS.items():
                assert outputs[kind]<=get(p['key']+'_capacity')*p['rate']+1e-9
                if not allowed(kind,rid):assert outputs[kind]==0
            total_value+=income
        close(v(s,'investment_output'),total_value);count+=1
    # Explicit small examples give an external numerical check of prices and
    # material priority, independently of the catalogue-driven conservation.
    s=opened();put(s,'r2_steel',.5);put(s,'r2_coal',1)
    put(s,'r2_power_capacity',1);put(s,'r2_tractors_capacity',1);put(s,'r2_machine_capacity',1)
    call(s,'forecast')
    close(v(s,'r2_tractors_output'),.2);close(v(s,'r2_machine_output'),.05)
    close(v(s,'r2_investment_output'),.35);count+=1
    # Fuel-only bootstrap: an oil well and refinery supply a fuel power plant
    # despite having no coal stock, mine or coal-fired power station.
    s=opened();put(s,'r5_coal',0)
    for key in ('oil','fuel','fuel_power'):put(s,'r5_'+key+'_capacity',1)
    call(s,'forecast');close(v(s,'r5_power_total'),.9)
    close(v(s,'r5_next_oil'),0);close(v(s,'r5_next_fuel'),.21);count+=1
    return count


def test_regional_chains_and_lifecycle():
    count=0
    for rid in range(6):
        s,placed=complete_chain(rid);product=specialty(rid)['output']
        before=production_snapshot(s);geology=geology_snapshot(s)
        call(s,'forecast');call(s,'refresh');assert production_snapshot(s)==before
        initial_budget=v(s,'budget');call(s,'start');call(s,'close_effect')
        for _ in range(8):call(s,'daily')
        assert v(s,product)>0,(rid,product)
        assert all(v(s,p)==0 for p in PRODUCTS if p not in ('machines',product))
        close(v(s,'value'),sum(v(s,p)*PRICES[p] for p in PRODUCTS))
        close(v(s,'budget')-initial_budget,v(s,'value'))
        assert all(v(s,f'r{r["id"]}_value')==0 for r in REGIONS if r['id']!=rid)
        # Switching and repeated forecasts do not produce; serialised state
        # retains all newly added stocks and deliveries.
        call(s,'open_effect');before=production_snapshot(s)
        for other in range(6):call(s,f'select_region_{other}');call(s,'forecast')
        assert production_snapshot(s)==before and geology_snapshot(s)==geology
        clone=copy.deepcopy(s);call(s,'daily');call(clone,'refresh');call(clone,'daily')
        assert production_snapshot(s)==production_snapshot(clone)
        call(s,f'select_region_{rid}')
        special_site=next(i for i in placed if v(s,f'n{i}_type')==15+rid)
        select(s,special_site);call(s,'switch');assert v(s,f'r{rid}_specialty_output')==0
        call(s,'switch');assert v(s,f'r{rid}_specialty_output')>0
        # Removing the final line must disable the advanced facility as well.
        call(s,'remove_rail')
        assert v(s,f'n{special_site}_effective')==0
        call(s,'arm_restart');call(s,'confirm_restart')
        assert all(v(s,p)==0 for p in PRODUCTS) and v(s,'value')==0
        assert all(v(s,f'r{r["id"]}_{k}')==0 for r in REGIONS for k in STORED if k not in ('coal','iron','steel'))
        invariants(s);count+=1
    return count


def test_affordable_specialty_start():
    # A genuine 40-investment start can specialise immediately in Tsaritsyn.
    # The original 36-cost chain refunds its 8-cost generic factory, then buys
    # a 10-cost tractor plant on the same connected tile: 38 spent, 2 left.
    s=starter(rid=2);site=sites(s,2)['machine'];select(s,site)
    call(s,'remove');builds(s,site,17);close(v(s,'budget'),2)
    assert v(s,f'n{site}_type')==17
    call(s,'start')
    for _ in range(100):call(s,'daily')
    invariants(s);assert v(s,'tractors')>=10
    close(v(s,'value'),v(s,'tractors')*1.5)
    close(v(s,'budget'),2+v(s,'value'))
    assert v(s,'machines')==0 and v(s,'elapsed')==100
    return 1


def main():
    total=sum(test() for test in (test_deposit_quotas_and_gates,test_multi_resource_conservation,test_regional_chains_and_lifecycle,test_affordable_specialty_start))
    print(f'{total} regional-industry scenarios passed: deposits, build gates, 10-stock conservation, fixed-price income and six working chains.')


if __name__=='__main__':main()
