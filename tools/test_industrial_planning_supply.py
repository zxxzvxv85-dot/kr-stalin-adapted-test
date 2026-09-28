"""Execute finance and finite freight through the generated HOI4 effects.

Injected stocks are explicitly credited to the conservation ledger. This is a
script interpreter regression, not proof of engine resource/UI behaviour.
"""
import copy
import math
from industrial_planning_supply import routes, PRICES
from test_industrial_planning import DATA, fixture, started, call, v, put, select, invariant


def stock(s,i,r,amount):
    put(s,'produced_'+r,v(s,'produced_'+r)+amount-v(s,f'n{i}_stock_{r}'))
    put(s,f'n{i}_stock_{r}',amount)


def quiet():
    s=started(False);s['steel']=s['coal']=0
    for state in s['states'].values():
        state.update(coal=0,steel=0,industrial_complex=0,arms_factory=0,infrastructure=4,rail_way=3)
    call(s,'capture_capacity');call(s,'refresh');return s


def ledger(s):
    names=('funds','funds_spent','funds_refunded','funds_settled','budget_day','budget_net','days_left',
           'produced_steel','produced_coal','consumed_steel','consumed_coal','lost_steel','lost_coal')
    names+=tuple(f'n{c["id"]}_{key}' for c in DATA['cells'] for key in ('work','stock_steel','stock_coal','in_steel','in_coal','out_steel','out_coal','in_work_steel','in_work_coal','out_work_steel','out_work_coal'))
    return tuple(v(s,k) for k in names)


def supply_tests():
    count=0
    # Unlocking/starting does not manufacture a free inventory or reset money.
    s=fixture();call(s,'open_effect');before=ledger(s)
    for _ in range(3):call(s,'daily');call(s,'open_effect')
    assert ledger(s)==before and v(s,'funds')==1000 and not s['modifier'];count+=1
    call(s,'start');call(s,'start')
    assert v(s,'produced_steel')==0 and v(s,'produced_coal')==0
    call(s,'daily');assert 0<v(s,'booked_coal')<=v(s,'capacity_coal')*.5+1e-7
    assert math.isclose(v(s,'produced_coal'),v(s,'booked_coal')*.25)
    assert v(s,'reserved_civs')==0 and s['modifier'];invariant(s);count+=1

    # Aggregation excludes occupation-only and uncontrolled owned states. Raw
    # counts grow across the economic region, while development is seeded once.
    s=started(False);i=5;extra=205;dev=v(s,'n5_development');old_pop=v(s,'n5_pop_k')
    d=s['states'][extra];d.update(state_population_k=1200,industrial_complex=3,arms_factory=2,infrastructure=5,coal=10,steel=20,energy_infrastructure=1)
    s['owned'].add(extra);call(s,'refresh');assert v(s,'n5_members')==1
    s['controlled'].add(extra);call(s,'refresh')
    assert v(s,'n5_members')==2 and v(s,'n5_pop_k')==old_pop+1200
    assert v(s,'n5_civs')==5 and v(s,'n5_mil')==3 and v(s,'n5_grid')==1
    assert v(s,'n5_development')==dev
    expected=(2*(4800+100*3+1)+5*(1200+100*5+1))/((4800+100*3+1)+(1200+100*5+1))
    assert math.isclose(v(s,'n5_infra'),expected)
    s['owned'].discard(extra);call(s,'refresh');assert v(s,'n5_members')==1;count+=4

    # Regional production shares a scarce national quota proportionally, not by
    # node order. No resource or money is created by UI refresh / save reload.
    s=started(False);call(s,'daily')
    first,last=v(s,'n0_produced_today_coal'),v(s,'n35_produced_today_coal')
    assert first>0 and math.isclose(first,last)
    before=ledger(s)
    for _ in range(4):
        call(s,'refresh');call(s,'toggle_supply');call(s,'toggle_help');call(s,'open_effect')
    assert ledger(s)==before
    reloaded=copy.deepcopy(s);call(reloaded,'refresh');assert ledger(reloaded)==before
    invariant(s);count+=3

    # Upfront costs vary with development; re-clicking is free of side effects,
    # pause is not a refund, and cancellation consumes its refundable balance once.
    s=started(False);select(s,5);put(s,'n5_development',20);call(s,'refresh')
    low=v(s,'forecast_7_cost');put(s,'n5_development',80);call(s,'refresh')
    high=v(s,'forecast_7_cost');assert low>high==PRICES[7]*1.1
    call(s,'build_7');assert math.isclose(v(s,'funds'),1000-high)
    before=ledger(s);call(s,'build_7');assert ledger(s)==before
    call(s,'pause');assert v(s,'funds_refunded')==0
    put(s,'n5_work',40);call(s,'refresh');expected=high*.6*.75
    assert math.isclose(v(s,'sel_refund'),expected)
    s['flags'].add('RUS_ip_cancel_armed');call(s,'cancel');assert math.isclose(v(s,'funds_refunded'),expected)
    s['flags'].add('RUS_ip_cancel_armed');call(s,'cancel');assert math.isclose(v(s,'funds_refunded'),expected)
    invariant(s);count+=5
    # Rapidly opening sites cannot spend the same money twice.
    s=started(False)
    for i in (0,1,2,3):select(s,i);call(s,'build_5')
    assert v(s,'queued')==3 and v(s,'funds')>=0;invariant(s);count+=1

    # No native steel flow need not block starting: stock can be used, but empty
    # warehouses pause real progress and steel alone cannot satisfy coal demand.
    s=quiet();select(s,4);call(s,'build_7');call(s,'daily')
    assert v(s,'n4_project')==7 and v(s,'n4_work')==0 and v(s,'n4_status')==6
    stock(s,4,'steel',5);call(s,'daily');assert v(s,'n4_work')==0 and v(s,'consumed_steel')==0
    stock(s,4,'coal',5);call(s,'daily');assert v(s,'n4_work')>0
    invariant(s);count+=3

    # A real arrival is delayed. Source stock is deducted at dispatch and the
    # batch cannot be duplicated by reopening the page or selecting another site.
    s=quiet();select(s,4);call(s,'build_7')
    for r in ('steel','coal'):stock(s,5,r,30)
    call(s,'daily');assert v(s,'n4_in_steel')>0 and v(s,'n4_stock_steel')==0 and v(s,'n4_work')==0
    dispatched=v(s,'n4_in_steel');assert math.isclose(dispatched,1.4)
    before=ledger(s);call(s,'refresh');call(s,'toggle_supply');assert ledger(s)==before
    remaining=v(s,'n4_in_work_steel');call(s,'daily');assert 0<v(s,'n4_in_work_steel')<remaining
    for _ in range(5):call(s,'daily');invariant(s)
    assert v(s,'n4_work')>0 and v(s,'n4_stock_steel')>0;count+=8

    # Exports keep 21 days whereas imports stop at 14: the same batch must not
    # immediately be sent back to its supplier.
    call(s,'cargo_dispatch');assert v(s,'n4_out_steel')==0
    isolated=quiet();stock(isolated,4,'steel',20);call(isolated,'daily')
    assert v(isolated,'n4_out_steel')==20 and v(isolated,'n4_stock_steel')==0
    assert v(isolated,'n5_stock_steel')==0
    select(isolated,5);assert v(isolated,'sel_view_in_steel')==20 and v(isolated,'sel_arrival')>0
    for _ in range(6):call(isolated,'daily');invariant(isolated)
    assert v(isolated,'n5_stock_steel')==20;count+=3

    # A nearly full hub accepts part of a batch and leaves its physical
    # remainder in transit. Its aggregated display never adds a second copy.
    s=quiet();stock(s,4,'steel',10);call(s,'daily')
    put(s,'n4_out_work_steel',0);stock(s,5,'steel',v(s,'n5_warehouse_cap')-2)
    call(s,'cargo_move');assert v(s,'n4_out_steel')==8
    before=v(s,'n5_stock_steel');call(s,'cargo_move');assert v(s,'n5_stock_steel')==before and v(s,'n4_out_steel')==8
    call(s,'refresh');assert v(s,'n5_view_in_steel')==8 and v(s,'n5_in_steel')==0
    invariant(s);count+=2

    # Congestion at any intermediate region slows the same remaining trip.
    s=quiet();select(s,4);call(s,'build_7');stock(s,5,'steel',40);stock(s,5,'coal',40);call(s,'daily')
    light=v(s,'n4_arrival_factor');s['states'][219]['arms_factory']=80;call(s,'refresh')
    assert .05<=v(s,'n4_arrival_factor')<light
    before=v(s,'n4_in_work_steel');call(s,'daily')
    assert 0<before-v(s,'n4_in_work_steel')<1;invariant(s);count+=2
    # Broken mid-route: no advancement, then resume the same batch. Losing its
    # destination disposes of the stock and batch exactly once, with no refund.
    s=quiet();select(s,0);call(s,'build_7');stock(s,5,'steel',40);stock(s,5,'coal',40);call(s,'daily')
    path=routes(DATA)[0][0];mid=path[1];s['controlled'].discard(DATA['cells'][mid]['state'])
    before=v(s,'n0_in_work_steel');call(s,'daily');assert v(s,'n0_in_work_steel')==before and v(s,'n0_route_live')==0
    s['controlled'].add(DATA['cells'][mid]['state']);call(s,'daily');assert v(s,'n0_in_work_steel')<before
    s['controlled'].discard(DATA['cells'][0]['state']);call(s,'daily');assert v(s,'n0_in_steel')==0 and v(s,'lost_steel')>0
    lost=v(s,'lost_steel');call(s,'daily');assert v(s,'lost_steel')==lost
    invariant(s);count+=4

    # Completed-state storage cannot manufacture space. Production pauses at a
    # full warehouse and restarts only when room exists (no raw resource double-charge).
    s=started(False);call(s,'refresh');cap=v(s,'n5_warehouse_cap')
    for r in ('steel','coal'):stock(s,5,r,cap)
    call(s,'cargo_produce');assert v(s,'n5_produced_today_steel')==0
    assert all(v(s,f'n{c["id"]}_stock_steel')<=v(s,f'n{c["id"]}_warehouse_cap')+1e-7 for c in DATA['cells'])
    call(s,'refresh');invariant(s);count+=1

    # War actually changes material allocation, rather than merely changing a
    # label: scarce local stocks feed work ahead of established industry.
    peace=quiet();peace['states'][219]['industrial_complex']=8;select(peace,5);call(peace,'build_7')
    stock(peace,5,'steel',.1);stock(peace,5,'coal',.1);call(peace,'refresh')
    war=copy.deepcopy(peace);war['war']=True;call(war,'refresh')
    assert v(peace,'n5_material_factor')==0 and v(war,'n5_material_factor')==1
    assert v(peace,'n5_operating_factor')>v(war,'n5_operating_factor')
    call(war,'daily');assert v(war,'n5_work')>0
    invariant(war);count+=2
    # Explicit district priority controls both scarce civs and hub dispatch.
    s=quiet();select(s,3);call(s,'build_7');select(s,4);call(s,'build_7')
    put(s,'capacity_civs',2);call(s,'refresh');assert v(s,'n3_running')==1 and v(s,'n4_running')==0
    call(s,'prioritise');assert v(s,'n4_running')==1 and v(s,'n3_running')==0
    stock(s,5,'steel',1);stock(s,5,'coal',1);call(s,'cargo_dispatch')
    assert v(s,'n4_in_steel')==1 and v(s,'n3_in_steel')==0
    invariant(s);count+=2

    # Thirty real daily ticks are required to settle. Central aid prevents a
    # cash deadlock, but neither opening the page nor pausing generates funding.
    s=quiet();base=v(s,'funds')
    for _ in range(29):call(s,'daily');invariant(s)
    assert v(s,'funds')==base and v(s,'budget_day')==29
    call(s,'daily');assert v(s,'budget_day')==0 and v(s,'last_budget')==25 and v(s,'last_support')>0
    assert v(s,'funds')==base+25;invariant(s);count+=30
    # The nearest settlement includes past accruals; the 30-day figure is a run
    # rate. Neither forecast can credit funds or advance the simulation.
    for monthly,day,accrued in [(-270,0,0),(-75,0,0),(0,0,0),(150,0,0),(150,17,-120),(-270,17,300)]:
        q=started(False)
        for c in DATA['cells']:put(q,f'n{c["id"]}_net_month',0)
        put(q,'n5_net_month',monthly);put(q,'budget_day',day);put(q,'budget_net',accrued)
        before=ledger(q);call(q,'cargo_totals');call(q,'cargo_totals')
        assert ledger(q)==before
        assert math.isclose(v(q,'projected_operating'),monthly)
        assert math.isclose(v(q,'projected_settlement'),max(25,monthly+100))
        expected=accrued+monthly*(30-day)/30+100
        assert math.isclose(v(q,'next_support'),max(0,25-expected))
        assert math.isclose(v(q,'next_settlement'),max(25,expected))
        assert math.isclose(v(q,'next_balance'),v(q,'funds')+max(25,expected))
        put(q,'budget_net',expected-100);put(q,'budget_day',29);call(q,'budget_daily')
        assert math.isclose(v(q,'last_budget'),v(q,'next_settlement'))
        invariant(q);count+=1
    q=quiet();old=v(q,'projected_operating')
    q['states'][219].update(industrial_complex=4,energy_infrastructure=1)
    put(q,'n5_development',90);stock(q,5,'steel',20);stock(q,5,'coal',20)
    cash=v(q,'funds');call(q,'refresh')
    assert v(q,'projected_operating')!=old and v(q,'funds')==cash;count+=1
    # Mature civilian hubs can contribute a positive balance; empty frontier
    # districts need funds for public services rather than generating free cash.
    s=quiet();s['states'][219].update(industrial_complex=4,energy_infrastructure=1)
    put(s,'n5_development',90);stock(s,5,'steel',20);stock(s,5,'coal',20);call(s,'refresh')
    assert v(s,'n5_net_month')>0 and v(s,'n4_net_month')<0;count+=1
    # Final day honours completions, refunds only unfinished work and seals the
    # financial/cargo ledger. Repeated daily calls cannot create more income.
    s=started();select(s,5);call(s,'build_5');select(s,4);call(s,'build_7')
    put(s,'n5_work',299.99);put(s,'n4_work',30);put(s,'days_left',1);call(s,'daily')
    assert v(s,'completed')==1 and v(s,'funds_refunded')>0 and not s['modifier']
    assert v(s,'reserved_civs')==v(s,'reserved_steel')==v(s,'reserved_coal')==0
    before=ledger(s);call(s,'daily');call(s,'refresh');assert ledger(s)==before;invariant(s);count+=2
    return count


if __name__=='__main__':print(f'PASS: {supply_tests()} finance and freight scenarios (script model).')
