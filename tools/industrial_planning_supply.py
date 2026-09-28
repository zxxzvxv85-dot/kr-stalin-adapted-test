"""Budget and finite materials for the independent construction programme.

Production alone books native coal/steel flow. Moving or using those packets
never charges native resources again. UI refresh only projects the next daily
step; production, arrivals, consumption and cash settlement are daily effects.
"""
import heapq
import math
from industrial_planning_economy import P, PROJECTS, setv, add, sub, mul, div, cv, ge, iff, fx, clamp, block

RESOURCES = ('steel', 'coal')
PRICES = {1:80, 2:80, 3:130, 4:180, 5:220, 6:90, 7:100, 8:70}
SUPPLY_METRICS = ('stock_steel','stock_coal','need_steel','need_coal','in_steel','in_coal',
                  'out_steel','out_coal','arrival','cover','warehouse_cap','income_month',
                  'upkeep_month','net_month','material_factor','members','pop_k','infra',
                  'paid','refund','delivery_load','route_days','route_live','mining_month',
                  'base_steel','base_coal','project_steel','project_coal','operating_factor',
                  'view_in_steel','view_in_coal','view_out_steel','view_out_coal')


def routes(data):
    """Shortest fixed planning paths by KR geometry, with a sea-link surcharge."""
    cells=data['cells'];hub=data['hub'];sea={tuple(e) for e in data['sea_edges']}
    terminals={b:a for a,b in sea}
    dist={hub:0};paths={hub:[hub]};queue=[(0,hub)]
    while queue:
        distance,a=heapq.heappop(queue)
        if distance!=dist[a]:continue
        for b in sorted(cells[a]['neighbors']):
            if a in terminals and b!=terminals[a]:continue
            if b in terminals and a!=terminals[b]:continue
            cost=math.hypot(cells[a]['geo_x']-cells[b]['geo_x'],cells[a]['geo_y']-cells[b]['geo_y'])/70+2
            if tuple(sorted((a,b))) in sea:cost+=5
            if distance+cost<dist.get(b,float('inf')):
                dist[b]=distance+cost;paths[b]=paths[a]+[b];heapq.heappush(queue,(dist[b],b))
    assert len(paths)==len(cells),'Disconnected planning geography'
    return {i:(paths[i],round(2+dist[i],2)) for i in paths}


def aggregate(cells):
    out='# Sum only owned AND controlled members; population/industry-weighted infrastructure.\n'
    for c in cells:
        n=f'n{c["id"]}_'
        for k in ('members','pop_k','civs','mil','coal','steel','grid','infra','infra_weight'):out+=setv(n+k,0)
        for state in c['states']:
            part=add(n+'members',1)
            for k,native in [('pop_k','state_population_k'),('civs','industrial_complex_level'),('mil','building_level@arms_factory'),
                             ('coal','resource@coal'),('steel','resource@steel'),('grid','building_level@energy_infrastructure')]:
                part+=add(n+k,f'{state}.{native}')
            part+=setv('survey_weight',f'{state}.industrial_complex_level')+add('survey_weight',f'{state}.building_level@arms_factory')+mul('survey_weight',100)
            part+=add('survey_weight',f'{state}.state_population_k')+add('survey_weight',1)+add(n+'infra_weight',P+'survey_weight')
            part+=mul('survey_weight',f'{state}.infrastructure_level')+add(n+'infra',P+'survey_weight')
            out+=iff(f'owns_state = {state}\ncontrols_state = {state}',part)
        out+=iff(cv(n+'infra_weight','>',0),div(n+'infra',P+n+'infra_weight'))
    return out


def seed_supply(cells):
    out=setv('funds',1000)+setv('budget_day',0)+setv('budget_net',0)+setv('last_budget',0)+setv('last_support',0)+setv('priority',-1)
    out+=setv('funds_spent',0)+setv('funds_refunded',0)+setv('funds_settled',0)
    for r in RESOURCES:
        for k in ('booked','produced','consumed','lost'):out+=setv(k+'_'+r,0)
    for c in cells:
        n=f'n{c["id"]}_'
        out+=setv(n+'paid',0)
        for r in RESOURCES:
            for k in ('stock','in','out','in_work','out_work','produced_today'):out+=setv(n+k+'_'+r,0)
    return out


def price_forecasts(n):
    out=''
    for kind,price in PRICES.items():
        out+=setv(f'forecast_{kind}_cost',P+n+'development')+mul(f'forecast_{kind}_cost',-.005)+add(f'forecast_{kind}_cost',1.5)+mul(f'forecast_{kind}_cost',price)
    return out


def render_supply(data):
    cells=data['cells'];hub=data['hub'];route_map=routes(data);effects=[]
    loads='';route_flags=''
    for c in cells:loads+=setv(f'n{c["id"]}_delivery_load',0)
    for i,(path,days) in sorted(route_map.items()):
        n=f'n{i}_';condition=f'RUS_ip_owned_{i} = yes\nRUS_ip_owned_{hub} = yes\n'
        for a,b in zip(path,path[1:]):condition+=cv(f'edge_{min(a,b)}_{max(a,b)}_live','=',1)
        route_flags+=setv(n+'route_live',0)+setv(n+'route_days',days)+iff(condition,setv(n+'route_live',1))
        if i==hub:continue
        loads+=setv('cargo_load',0)
        for r in RESOURCES:
            for direction in ('in','out'):loads+=add('cargo_load',P+n+direction+'_'+r)
        loads+=div('cargo_load',14)
        for j in path:loads+=add(f'n{j}_delivery_load',P+'cargo_load')
    effects.append(fx('cargo_loads',loads))
    effects.append(fx('cargo_routes',route_flags))

    # These read-only values are shared by live work, finance and GUI tooltips.
    prepare=''
    for c in cells:
        i=c['id'];n=f'n{i}_'
        prepare+=setv(n+'warehouse_cap',P+n+'development')+mul(n+'warehouse_cap',.5)+add(n+'warehouse_cap',20)
        for key,factor in [('infra',10),('urban',10)]:
            prepare+=setv('cargo_part',P+n+key)+mul('cargo_part',factor)+add(n+'warehouse_cap',P+'cargo_part')
        if i==hub:prepare+=add(n+'warehouse_cap',200)
        for r in RESOURCES:
            prepare+=setv(n+'base_'+r,P+n+'civs')+mul(n+'base_'+r,.05 if r=='steel' else .08)
            prepare+=setv('cargo_part',P+n+'mil')+mul('cargo_part',.1 if r=='steel' else .06)+add(n+'base_'+r,P+'cargo_part')
            prepare+=setv(n+'project_'+r,0)
        for kind,spec in PROJECTS.items():
            prepare+=iff(cv(n+'running','=',1)+cv(n+'project','=',kind),''.join(setv(n+'project_'+r,spec[r]*.1) for r in RESOURCES))
        for r in RESOURCES:prepare+=setv(n+'need_'+r,P+n+'base_'+r)+add(n+'need_'+r,P+n+'project_'+r)
        # Refund is only projected here; cancellation consumes paid once.
        prepare+=setv(n+'refund',0)
        prepare+=iff(cv(n+'required','>',0),setv(n+'refund',1)+setv('cargo_part',P+n+'work')+div('cargo_part',P+n+'required')+sub(n+'refund',P+'cargo_part')+clamp(n+'refund',0,1)+mul(n+'refund',P+n+'paid')+mul(n+'refund',.75))
        prepare+=setv(n+'cover',999)+setv(n+'arrival',0)
        for r in RESOURCES:
            prepare+=iff(cv(n+'need_'+r,'>',0),setv('cargo_part',P+n+'stock_'+r)+div('cargo_part',P+n+'need_'+r)+clamp(n+'cover',0,P+'cargo_part'))
            prepare+=iff(cv(n+'in_'+r,'>',0),iff(cv(n+'arrival','=',0),setv(n+'arrival',P+n+'in_work_'+r))+block('else',clamp(n+'arrival',0,P+n+'in_work_'+r)))
        prepare+=setv(n+'arrival_factor',1)
        for j in route_map[i][0]:
            prepare+=iff(cv(f'n{j}_freight_used','>',0),setv('cargo_part',P+f'n{j}_freight')+div('cargo_part',P+f'n{j}_freight_used')+clamp(n+'arrival_factor',0,P+'cargo_part'))
        prepare+=clamp(n+'arrival_factor',.05,1)+div(n+'arrival',P+n+'arrival_factor')
        for r in RESOURCES:
            prepare+=setv(n+'view_in_'+r,P+n+'in_'+r)+setv(n+'view_out_'+r,P+n+'out_'+r)
    # Hub display aggregates regional batch slots without duplicating physical
    # inventory in its own in/out fields (those must remain zero for the ledger).
    h=f'n{hub}_'
    for r in RESOURCES:
        for c in cells:
            if c['id']==hub:continue
            n=f'n{c["id"]}_'
            prepare+=add(h+'view_in_'+r,P+n+'out_'+r)+add(h+'view_out_'+r,P+n+'in_'+r)
            candidate=setv('cargo_part',P+n+'out_work_'+r)+div('cargo_part',P+n+'arrival_factor')
            candidate+=iff(cv(h+'arrival','=',0),setv(h+'arrival',P+'cargo_part'))+block('else',clamp(h+'arrival',0,P+'cargo_part'))
            prepare+=iff(cv(n+'out_'+r,'>',0)+cv(n+'route_live','=',1),candidate)
    effects.append(fx('cargo_prepare',prepare))

    projection=''
    for c in cells:
        i=c['id'];n=f'n{i}_'
        projection+=''.join(setv('material_left_'+r,P+n+'stock_'+r)+setv(n+'used_'+r,0) for r in RESOURCES)
        # Construction receives priority at war; peacetime gives local industry
        # first use. No automatic building orders or cancellation during war.
        def portion(part,factor):
            body=setv(n+factor,1)
            for r in RESOURCES:
                body+=iff(cv(n+part+'_'+r,'>',0),setv('cargo_part',P+'material_left_'+r)+div('cargo_part',P+n+part+'_'+r)+clamp(n+factor,0,P+'cargo_part'))
            body+=clamp(n+factor,0,1)
            for r in RESOURCES:
                body+=setv('cargo_part',P+n+part+'_'+r)+mul('cargo_part',P+n+factor)+sub('material_left_'+r,P+'cargo_part')+add(n+'used_'+r,P+'cargo_part')
            return body
        normal=portion('base','operating_factor')+portion('project','material_factor')
        wartime=portion('project','material_factor')+portion('base','operating_factor')
        projection+=iff('has_war = yes',wartime)+block('else',normal)
        # Existing native factories are not debuffed: this is their contribution
        # to the programme's separate operating account.
        for resource,need in [('workers','base_workers_need'),('power','base_power_need')]:
            projection+=iff(cv(n+need,'>',0),setv('cargo_part',P+n+resource)+div('cargo_part',P+n+need)+clamp(n+'operating_factor',0,P+'cargo_part'))
        projection+=setv(n+'income_month',P+n+'civs')+mul(n+'income_month',3.6)
        projection+=setv('cargo_part',P+n+'development')+mul('cargo_part',.01)+add('cargo_part',.5)+mul(n+'income_month',P+'cargo_part')+mul(n+'income_month',P+n+'operating_factor')
        projection+=setv(n+'upkeep_month',P+n+'mil')+mul(n+'upkeep_month',2.1)
        projection+=setv('cargo_part',40)+sub('cargo_part',P+n+'development')+clamp('cargo_part',0,40)+mul('cargo_part',.15)+add('cargo_part',3)+add(n+'upkeep_month',P+'cargo_part')
        for key,factor in [('urban',1.2),('grid',1.05),('rail',.45)]:
            projection+=setv('cargo_part',P+n+key)+mul('cargo_part',factor)+add(n+'upkeep_month',P+'cargo_part')
        projection+=setv(n+'mining_month',P+n+'produced_today_steel')+add(n+'mining_month',P+n+'produced_today_coal')+mul(n+'mining_month',4.5)
        projection+=setv(n+'net_month',P+n+'income_month')+add(n+'net_month',P+n+'mining_month')+sub(n+'net_month',P+n+'upkeep_month')
    effects.append(fx('cargo_projection',projection))

    produce=''
    for r in RESOURCES:
        produce+=setv('booked_'+r,0)+setv('material_quota_'+r,P+'capacity_'+r)+mul('material_quota_'+r,.5)
        produce+=setv('material_requested_'+r,0)
        produce+=setv('hub_incoming_'+r,0)
        for c in cells:produce+=add('hub_incoming_'+r,P+f'n{c["id"]}_out_'+r)
    for c in cells:
        i=c['id'];n=f'n{i}_';body=''
        for r in RESOURCES:
            produce+=setv(n+'produced_today_'+r,0)
            produce+=setv(n+'requested_'+r,0)
            part=setv('cargo_amount',P+n+'warehouse_cap')+sub('cargo_amount',P+n+'stock_'+r)+sub('cargo_amount',P+n+'in_'+r)
            if i==hub:part+=sub('cargo_amount',P+'hub_incoming_'+r)
            part+=clamp('cargo_amount',0,99999)
            part+=div('cargo_amount',.25)+clamp('cargo_amount',0,P+n+r)
            part+=setv(n+'requested_'+r,P+'cargo_amount')+add('material_requested_'+r,P+'cargo_amount')
            body+=part
        produce+=iff(f'RUS_ip_owned_{i} = yes',body)
    # Fairly share the national quota across productive regions. A low district
    # number must not permanently monopolise the available native resource flow.
    for r in RESOURCES:
        produce+=setv('material_ratio_'+r,1)
        produce+=iff(cv('material_requested_'+r,'>',0),setv('material_ratio_'+r,P+'material_quota_'+r)+div('material_ratio_'+r,P+'material_requested_'+r)+clamp('material_ratio_'+r,0,1))
        for c in cells:
            n=f'n{c["id"]}_'
            produce+=setv('cargo_amount',P+n+'requested_'+r)+mul('cargo_amount',P+'material_ratio_'+r)+add('booked_'+r,P+'cargo_amount')+mul('cargo_amount',.25)
            produce+=add(n+'stock_'+r,P+'cargo_amount')+add('produced_'+r,P+'cargo_amount')+setv(n+'produced_today_'+r,P+'cargo_amount')
    effects.append(fx('cargo_produce',produce))

    movement=''
    for i,(path,days) in sorted(route_map.items()):
        if i==hub:continue
        n=f'n{i}_'
        for r in RESOURCES:
            for direction,target in [('in',i),('out',hub)]:
                amount=n+direction+'_'+r;work=n+direction+'_work_'+r;dest=f'n{target}_'
                step=sub(work,P+n+'arrival_factor')+clamp(work,0,99999)
                arrival=setv('cargo_amount',P+dest+'warehouse_cap')+sub('cargo_amount',P+dest+'stock_'+r)+clamp('cargo_amount',0,P+amount)
                arrival+=add(dest+'stock_'+r,P+'cargo_amount')+sub(amount,P+'cargo_amount')
                step+=iff(cv(work,'=',0),arrival)
                movement+=iff(cv(amount,'>',0)+cv(n+'route_live','=',1),step)
    effects.append(fx('cargo_move',movement))

    dispatch=''
    for i,(path,days) in sorted(route_map.items()):
        if i==hub:continue
        n=f'n{i}_';body=''
        for r in RESOURCES:
            for direction,source,target in [('out',i,hub),('in',hub,i)]:
                src,dst=f'n{source}_',f'n{target}_';amount=n+direction+'_'+r;work=n+direction+'_work_'+r
                # A 21-day export reserve exceeds the 14-day import target:
                # the dispatcher must not endlessly return yesterday's import.
                part=setv('cargo_amount',P+src+'stock_'+r)+setv('cargo_part',P+src+'need_'+r)+mul('cargo_part',21 if direction=='out' else 7)+sub('cargo_amount',P+'cargo_part')+clamp('cargo_amount',0,99999)
                # The hub retains a large supply reserve for distribution; a
                # destination requests only two weeks of its current use.
                part+=setv('cargo_limit',P+dst+'warehouse_cap' if direction=='out' else P+dst+'need_'+r)
                if direction=='in':part+=mul('cargo_limit',14)
                part+=sub('cargo_limit',P+dst+'stock_'+r)
                if direction=='out':part+=sub('cargo_limit',P+'hub_incoming_'+r)
                part+=clamp('cargo_limit',0,99999)+clamp('cargo_amount',0,P+'cargo_limit')
                for j in path:
                    # A small emergency dispatch allowance prevents an already
                    # overloaded industrial region from permanently blocking
                    # the materials needed to improve its own transport.
                    part+=setv('cargo_floor',P+f'n{j}_freight')+mul('cargo_floor',.1)
                    part+=setv('cargo_limit',P+f'n{j}_freight')+sub('cargo_limit',P+f'n{j}_freight_used')+clamp('cargo_limit',P+'cargo_floor',99999)+mul('cargo_limit',14)+clamp('cargo_amount',0,P+'cargo_limit')
                send=sub(src+'stock_'+r,P+'cargo_amount')+setv(amount,P+'cargo_amount')+setv(work,days)
                if direction=='out':send+=add('hub_incoming_'+r,P+'cargo_amount')
                send+=div('cargo_amount',14)
                for j in path:send+=add(f'n{j}_freight_used',P+'cargo_amount')
                part+=iff(cv('cargo_amount','>',.1),send)
                body+=iff(cv(amount,'=',0),part)
        # Priority district first; wartime next prioritises unfinished work.
        effects.append(fx(f'cargo_dispatch_{i}',iff(cv(n+'route_live','=',1),body)))
    for r in RESOURCES:
        dispatch+=setv('hub_incoming_'+r,0)
        for c in cells:dispatch+=add('hub_incoming_'+r,P+f'n{c["id"]}_out_'+r)
    for i in sorted(route_map):
        if i!=hub:dispatch+=iff(cv('priority','=',i),f'RUS_ip_cargo_dispatch_{i} = yes\n')
    # A dispatched slot cannot send again; the second pass is safe and leaves
    # any unused bandwidth available to districts later in the stable order.
    for i in sorted(route_map):
        if i!=hub:dispatch+=iff('has_war = yes\n'+cv(f'n{i}_project','>',0),f'RUS_ip_cargo_dispatch_{i} = yes\n')
    for i in sorted(route_map):
        if i!=hub:dispatch+=f'RUS_ip_cargo_dispatch_{i} = yes\n'
    effects.append(fx('cargo_dispatch',dispatch))

    consume=''
    for c in cells:
        i=c['id'];n=f'n{i}_';body=''
        for r in RESOURCES:body+=sub(n+'stock_'+r,P+n+'used_'+r)+clamp(n+'stock_'+r,0,99999)+add('consumed_'+r,P+n+'used_'+r)
        body+=setv('cargo_part',P+n+'net_month')+div('cargo_part',30)+add('budget_net',P+'cargo_part')
        consume+=iff(f'RUS_ip_owned_{i} = yes',body)
    effects.append(fx('cargo_consume',consume))
    settlement=add('budget_day',1)
    cycle=setv('last_budget',P+'budget_net')+add('last_budget',100)+setv('last_support',25)+sub('last_support',P+'last_budget')+clamp('last_support',0,99999)
    cycle+=add('last_budget',P+'last_support')+add('funds',P+'last_budget')+add('funds_settled',P+'last_budget')+setv('budget_net',0)+setv('budget_day',0)
    settlement+=iff(ge('budget_day',30),cycle)
    effects.append(fx('budget_daily',settlement))
    loss=''
    for c in cells:
        i=c['id'];n=f'n{i}_';body=''
        for r in RESOURCES:
            body+=add('lost_'+r,P+n+'stock_'+r)+setv(n+'stock_'+r,0)
            body+=add('lost_'+r,P+n+'in_'+r)+setv(n+'in_'+r,0)+setv(n+'in_work_'+r,0)
            if i!=hub:
                loss+=iff(f'NOT = {{ RUS_ip_owned_{hub} = yes }}',add('lost_'+r,P+n+'out_'+r)+setv(n+'out_'+r,0)+setv(n+'out_work_'+r,0))
        loss+=iff(f'NOT = {{ RUS_ip_owned_{i} = yes }}',body)
    effects.append(fx('cargo_losses',loss))
    totals=setv('budget_next',30)+sub('budget_next',P+'budget_day')+setv('projected_net',100)
    for r in RESOURCES:
        totals+=setv('total_stock_'+r,0)+setv('total_transit_'+r,0)
        for c in cells:
            n=f'n{c["id"]}_';totals+=add('total_stock_'+r,P+n+'stock_'+r)+add('total_transit_'+r,P+n+'in_'+r)+add('total_transit_'+r,P+n+'out_'+r)
    for c in cells:totals+=iff(f'RUS_ip_owned_{c["id"]} = yes',add('projected_net',P+f'n{c["id"]}_net_month'))
    effects.append(fx('cargo_totals',totals))
    return effects
