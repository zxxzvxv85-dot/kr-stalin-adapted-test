"""Execute generated freight scripts: conservation, delivery timing and controls."""
import copy
import math
from industrial_planning_catalog import STOCKS, FREIGHT_KIND, FREIGHT_DAYS
from industrial_planning_factory_freight import PERSISTENT
from test_factory_planning import opened, builds, call, gui_click, select, put, v, REGIONS, path_to, production_snapshot


def eq(a,b):assert math.isclose(a,b,abs_tol=1e-7),(a,b)


def station(s,rid,grade=1):
    # Explicitly funded construction fixture; never presented as a 40-budget start.
    site=next(i for i in REGIONS[rid]['starter'][1:-2] if v(s,f'n{i}_type')==0)
    for i in path_to(s,site):
        while v(s,f'n{i}_rail')<grade:builds(s,i,'rail')
    builds(s,site,FREIGHT_KIND,grade)
    assert v(s,f'n{site}_type')==FREIGHT_KIND
    return site


def pair(source=0,target=1,grade=1):
    s=opened();put(s,'budget',1000)
    return s,station(s,source,grade),station(s,target,grade)


def route(s,source,target,goods='coal',reserve=0,enabled=True):
    call(s,f'select_region_{source}');gui_click(s,'ip_freight_page')
    gui_click(s,f'ip_freight_r{source}_dest_{target}')
    gui_click(s,f'ip_freight_r{source}_goods_{STOCKS.index(goods)}')
    for _ in range(4):
        if v(s,f'r{source}_freight_reserve')==reserve:break
        gui_click(s,f'ip_freight_r{source}_reserve')
    assert v(s,f'r{source}_freight_reserve')==reserve
    if bool(v(s,f'r{source}_freight_enabled'))!=enabled:gui_click(s,f'ip_freight_r{source}_toggle')


def snapshot(s):
    return (production_snapshot(s),v(s,'freight_spent'),tuple(v(s,f'r{r}_{k}') for r in range(6) for k in PERSISTENT))


def cargo_total(s,key):
    return sum(v(s,f'r{r}_{key}') for r in range(6))+sum(v(s,f'r{r}_freight_amount') for r in range(6) if v(s,f'r{r}_freight_cargo')==STOCKS.index(key))


def test_building_and_controls():
    s,origin,dest=pair();count=0
    call(s,'select_region_0');other=next(i for i in REGIONS[0]['starter'][1:-2] if i!=origin)
    budget=v(s,'budget');builds(s,other,21);eq(v(s,'budget'),budget);assert v(s,f'n{other}_type')==0;count+=1
    builds(s,origin,21,3);assert v(s,f'n{origin}_level')==3 and v(s,'r0_transport_capacity')==1
    for i in path_to(s,origin):builds(s,i,'rail',2)
    assert v(s,'r0_transport_capacity')==3;count+=1
    route(s,0,1,reserve=3);before=snapshot(s)
    for _ in range(4):call(s,'refresh');call(s,'freight_preview')
    assert snapshot(s)==before
    for action in ['ip_freight_r1_toggle','ip_freight_r1_dest_0','ip_freight_r1_goods_3','ip_freight_r1_reserve']:
        gui_click(s,action);assert snapshot(s)==before
    call(s,'toggle_help');gui_click(s,'ip_freight_r0_toggle');assert snapshot(s)==before
    call(s,'toggle_help');call(s,'build_page_0');gui_click(s,'ip_freight_r0_toggle');assert snapshot(s)==before
    call(s,'close_effect');call(s,'r0_freight_target_2');assert snapshot(s)==before;count+=1
    call(s,'open_effect');call(s,'start');put(s,'r0_coal',20);route(s,0,1,reserve=3)
    # The weaker receiving endpoint limits both volume and time.
    eq(v(s,'freight_limit'),6);eq(v(s,'freight_preview_days'),3)
    builds(s,dest,21);builds(s,dest,'rail');route(s,0,1,reserve=3)
    eq(v(s,'freight_limit'),12);eq(v(s,'freight_preview_days'),2);count+=1
    select(s,origin);call(s,'remove');builds(s,other,21)
    assert v(s,'r0_transport_sites')==1 and v(s,f'n{other}_type')==21;count+=1
    return count


def test_all_materials_and_timing():
    count=0
    for key in STOCKS:
        s,_,_=pair();put(s,'r0_'+key,8);route(s,0,1,key,reserve=3)
        initial=cargo_total(s,key);target=v(s,'r1_'+key);cash=v(s,'budget')
        before=snapshot(s);call(s,'daily');assert snapshot(s)==before # no start, no transport
        call(s,'start');call(s,'daily')
        eq(v(s,'r0_'+key),3);eq(v(s,'r0_freight_amount'),5);eq(v(s,'r0_freight_days'),3)
        eq(v(s,'budget'),cash-.5);eq(cargo_total(s,key),initial);eq(v(s,'value'),0)
        route(s,0,1,key,reserve=3,enabled=False);call(s,'close_effect')
        for remaining in (2,1):
            call(s,'daily');eq(v(s,'r0_freight_days'),remaining);eq(v(s,'r1_'+key),target)
        call(s,'daily');eq(v(s,'r1_'+key),target+5);eq(v(s,'r0_freight_amount'),0)
        eq(cargo_total(s,key),initial);eq(v(s,'r1_freight_received'),5)
        call(s,'daily');eq(v(s,'r1_'+key),target+5);eq(v(s,'budget'),cash-.5);count+=1
    return count


def test_waiting_retarget_and_reload():
    s,origin,dest=pair();put(s,'r0_coal',10);route(s,0,1,reserve=0);call(s,'start');call(s,'daily')
    eq(v(s,'r0_freight_amount'),6);eq(v(s,'r0_freight_fee'),.6)
    # Settings can change for the next batch but cannot transform current cargo.
    route(s,0,2,'oil',reserve=0,enabled=False)
    assert v(s,'r0_freight_to')==1 and v(s,'r0_freight_cargo')==0
    select(s,origin);call(s,'remove');select(s,dest);call(s,'remove_rail')
    before=v(s,'r1_coal')
    for _ in range(5):call(s,'daily')
    eq(v(s,'r0_freight_days'),0);eq(v(s,'r0_freight_amount'),6);eq(v(s,'r1_coal'),before)
    assert v(s,'r0_freight_status')==7
    clone=copy.deepcopy(s);call(clone,'refresh');call(s,'daily');call(clone,'daily');assert snapshot(s)==snapshot(clone)
    builds(s,dest,'rail');call(s,'daily');eq(v(s,'r1_coal'),before+6);eq(v(s,'r0_freight_amount'),0)
    eq(v(s,'r2_oil'),0);eq(v(s,'freight_spent'),.6)
    # Pausing the target has the same hold/unload semantics as disconnecting.
    s,_,dest=pair();route(s,0,1,reserve=0);call(s,'start');call(s,'daily');select(s,dest);call(s,'switch')
    for _ in range(4):call(s,'daily')
    assert v(s,'r0_freight_amount')==6 and v(s,'r0_freight_days')==0
    call(s,'switch');call(s,'daily');assert v(s,'r0_freight_amount')==0
    return 4


def test_continuous_dispatch_and_recovery():
    # Enable once, close the GUI, then execute real daily hooks through three
    # consecutive batches. No freight button or internal dispatch call follows.
    s,_,_=pair();put(s,'r0_coal',23);route(s,0,1,'coal',3)
    total=cargo_total(s,'coal');cash=v(s,'budget');target=v(s,'r1_coal')
    call(s,'start');call(s,'close_effect')
    for day in range(1,11):
        call(s,'daily')
        if day==4:
            eq(v(s,'r1_coal'),target+6);eq(v(s,'r0_freight_sent'),12)
            eq(v(s,'r0_freight_days'),3)
        if day==7:eq(v(s,'r1_coal'),target+12);eq(v(s,'r0_freight_sent'),18)
    eq(v(s,'r1_coal'),target+18);eq(v(s,'r0_freight_amount'),2)
    for _ in range(3):call(s,'daily')
    eq(v(s,'r1_coal'),target+20);eq(v(s,'r0_coal'),3)
    eq(v(s,'r0_freight_amount'),0);eq(v(s,'budget'),cash-2)
    eq(cargo_total(s,'coal'),total);assert v(s,'r0_freight_enabled')==1
    # A stock shortage only suspends the route. Replenishment resumes it.
    put(s,'r0_coal',8);call(s,'daily')
    eq(v(s,'r0_freight_amount'),5);eq(v(s,'r0_coal'),3)
    # Likewise for cash or a broken station: do not toggle the route again.
    s,_,dest=pair();put(s,'r0_coal',20);route(s,0,1,'coal',3)
    call(s,'start');put(s,'budget',.09);call(s,'daily')
    assert v(s,'r0_freight_status')==5;eq(v(s,'r0_freight_amount'),0)
    put(s,'budget',20);select(s,dest);call(s,'remove_rail');call(s,'daily')
    assert v(s,'r0_freight_status')==3;eq(v(s,'r0_freight_amount'),0)
    builds(s,dest,'rail');call(s,'close_effect');call(s,'daily')
    eq(v(s,'r0_freight_amount'),6);assert v(s,'r0_freight_enabled')==1
    return 3


def test_budget_expiry_and_reset():
    s,_,_=pair();put(s,'r0_coal',20);route(s,0,1,reserve=0);call(s,'start')
    put(s,'budget',.09);call(s,'daily');eq(v(s,'r0_freight_amount'),0)
    put(s,'budget',.25);call(s,'daily');eq(v(s,'r0_freight_amount'),2.5);eq(v(s,'budget'),0)
    assert v(s,'r0_coal')>=0
    original=cargo_total(s,'coal');put(s,'days_left',1);put(s,'elapsed',1799);call(s,'daily')
    eq(v(s,'r0_freight_amount'),0);eq(v(s,'budget'),.25);eq(v(s,'freight_spent'),0);eq(cargo_total(s,'coal'),original)
    before=snapshot(s);call(s,'daily');call(s,'freight_finish');assert snapshot(s)==before
    call(s,'arm_restart');call(s,'confirm_restart')
    eq(v(s,'budget'),40);eq(v(s,'freight_spent'),0)
    for rid in range(6):
        for key in ('freight_amount','freight_days','freight_fee','freight_sent','freight_received','freight_returned','freight_enabled'):eq(v(s,f'r{rid}_'+key),0)
    return 4


def test_concurrent_arrivals_and_import_processing():
    s=opened();put(s,'budget',1000)
    for rid in range(3):station(s,rid)
    for rid in (1,2):put(s,f'r{rid}_steel',10);route(s,rid,0,'steel',0)
    total=cargo_total(s,'steel');cash=v(s,'budget');call(s,'start');call(s,'daily')
    assert v(s,'r0_freight_incoming_count')==2;eq(v(s,'r0_freight_incoming_amount'),12)
    for rid in (1,2):route(s,rid,0,'steel',0,False)
    for _ in range(4):call(s,'daily')
    eq(v(s,'r0_steel'),14);eq(v(s,'r0_freight_received'),12);eq(cargo_total(s,'steel'),total);eq(v(s,'budget'),cash-1.2)
    # Moscow has no oil deposits, but imports can operate its refinery and
    # fuel power on the very day the shipment actually arrives.
    s,_,_=pair(2,0)
    for kind in (13,14):
        site=next(i for i in REGIONS[0]['starter'][1:-2] if v(s,f'n{i}_type')==0)
        for i in path_to(s,site):
            if v(s,f'n{i}_rail')==0:builds(s,i,'rail')
        builds(s,site,kind);assert v(s,f'n{site}_type')==kind
    put(s,'r2_oil',6);route(s,2,0,'oil',0);call(s,'start');call(s,'daily')
    route(s,2,0,'oil',0,False)
    for _ in range(FREIGHT_DAYS[2][0]-1):call(s,'daily');eq(v(s,'r0_fuel'),0)
    call(s,'daily');eq(v(s,'r0_oil'),5.7);eq(v(s,'r0_fuel'),.21)
    assert v(s,'r0_power_total')==.9
    return 2


def main():
    total=sum(t() for t in (test_building_and_controls,test_all_materials_and_timing,test_waiting_retarget_and_reload,test_continuous_dispatch_and_recovery,test_budget_expiry_and_reset,test_concurrent_arrivals_and_import_processing))
    print(f'{total} freight scenarios passed: station gates, 10 materials, continuous automatic dispatch, recovery, timing, accounting, blocked unloading, expiry and imported production.')


if __name__=='__main__':main()
