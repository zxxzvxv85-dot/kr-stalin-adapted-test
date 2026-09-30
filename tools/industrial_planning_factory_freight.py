"""Six automatic regional freight routes; forecasts never move cargo or money."""
from industrial_planning_catalog import STOCKS, FREIGHT_BATCH_PER_LEVEL, FREIGHT_FEE, FREIGHT_RESERVES, FREIGHT_DAYS
from industrial_planning_factory import P, REGIONS, block, fx, cv, ge, iff, setv, add, sub, mul, div, minimum, clamp

PERSISTENT = ('freight_enabled','freight_destination','freight_resource','freight_reserve_setting',
              'freight_amount','freight_days','freight_cargo','freight_to','freight_fee',
              'freight_sent','freight_received','freight_returned')
DISPLAY = (*PERSISTENT,'transport_capacity','transport_sites','freight_reserve','freight_limit',
           'freight_stock','freight_preview_amount','freight_preview_fee','freight_preview_days',
           'freight_status','freight_incoming_count','freight_incoming_amount')


def initialise():
    result=setv('freight_spent',0)
    for r in REGIONS:
        rid=r['id']
        for key in PERSISTENT:
            number=(rid+1)%6 if key=='freight_destination' else 2 if key=='freight_reserve_setting' else 0
            result+=setv(f'r{rid}_'+key,number)
    return result


def render_freight():
    triggers=[fx('freight_controls','RUS_ip_editing = yes\nNOT = { has_country_flag = RUS_ip_help_open }\n'+cv('build_page','=',2))]
    effects=[];preview='';arrivals='';dispatch='';finish=''
    for r in REGIONS:
        rid=r['id'];rp=f'r{rid}_'
        def val(key):return P+rp+key
        plan=setv(rp+'freight_reserve',0)+setv(rp+'freight_stock',0)+setv(rp+'freight_limit',0)+setv(rp+'freight_preview_days',0)
        for index,reserve in enumerate(FREIGHT_RESERVES):plan+=iff(cv(rp+'freight_reserve_setting','=',index),setv(rp+'freight_reserve',reserve))
        for index,key in enumerate(STOCKS):plan+=iff(cv(rp+'freight_resource','=',index),setv(rp+'freight_stock',val(key)))
        plan+=setv(rp+'freight_status',0)
        for target in range(6):
            if target==rid:continue
            route=setv(rp+'freight_limit',val('transport_capacity'))+minimum(rp+'freight_limit',P+f'r{target}_transport_capacity')
            route+=setv(rp+'freight_preview_days',FREIGHT_DAYS[rid][target]+1)+sub(rp+'freight_preview_days',val('freight_limit'))+clamp(rp+'freight_preview_days',1,30)
            route+=mul(rp+'freight_limit',FREIGHT_BATCH_PER_LEVEL)
            route+=iff(cv(f'r{target}_transport_capacity','<',1),setv(rp+'freight_status',3))
            plan+=iff(cv(rp+'freight_destination','=',target),route)
        plan+=setv(rp+'freight_preview_amount',val('freight_stock'))+sub(rp+'freight_preview_amount',val('freight_reserve'))+clamp(rp+'freight_preview_amount',0,1000000)
        plan+=minimum(rp+'freight_preview_amount',val('freight_limit'))
        plan+=setv(rp+'freight_affordable',P+'budget')+div(rp+'freight_affordable',FREIGHT_FEE)+minimum(rp+'freight_preview_amount',val('freight_affordable'))
        plan+=iff(cv(rp+'freight_preview_amount','<',1),setv(rp+'freight_preview_amount',0))
        plan+=setv(rp+'freight_preview_fee',val('freight_preview_amount'))+mul(rp+'freight_preview_fee',FREIGHT_FEE)
        # Status precedence: physical route, availability, then lifecycle.
        plan+=iff(cv(rp+'freight_status','=',0)+cv(rp+'freight_preview_amount','<',1),setv(rp+'freight_status',4))
        plan+=iff(cv('budget','<',FREIGHT_FEE),setv(rp+'freight_status',5))
        plan+=iff(cv(rp+'transport_capacity','<',1),setv(rp+'freight_status',2))
        plan+=iff(cv(rp+'freight_destination','=',rid),setv(rp+'freight_status',10))
        plan+=iff(cv(rp+'freight_enabled','=',0),setv(rp+'freight_status',1))
        plan+=iff(cv(rp+'freight_amount','>',0),setv(rp+'freight_status',6)+iff(cv(rp+'freight_days','=',0),setv(rp+'freight_status',7)))
        plan+=iff('NOT = { has_country_flag = RUS_ip_started }\n',setv(rp+'freight_status',9))
        plan+=iff('has_country_flag = RUS_ip_finished\n',setv(rp+'freight_status',8))
        effects.append(fx(f'r{rid}_freight_plan',plan));preview+=f'RUS_ip_r{rid}_freight_plan = yes\n'

        # Freight settings are independent of the selected tile. In-flight
        # cargo has its own resource/destination snapshot, never retargeted.
        guard='RUS_ip_freight_controls = yes\n'+cv('region','=',rid)
        for target in range(6):
            if target!=rid:effects.append(fx(f'r{rid}_freight_target_{target}',iff(guard,setv(rp+'freight_destination',target)+'RUS_ip_refresh = yes\n')))
        for index,key in enumerate(STOCKS):effects.append(fx(f'r{rid}_freight_goods_{index}',iff(guard,setv(rp+'freight_resource',index)+'RUS_ip_refresh = yes\n')))
        effects.append(fx(f'r{rid}_freight_toggle',iff(guard,iff(cv(rp+'freight_enabled','=',0),setv(rp+'freight_enabled',1))+block('else',setv(rp+'freight_enabled',0))+'RUS_ip_refresh = yes\n')))
        effects.append(fx(f'r{rid}_freight_reserve',iff(guard,add(rp+'freight_reserve_setting',1)+iff(cv(rp+'freight_reserve_setting','>',3),setv(rp+'freight_reserve_setting',0))+'RUS_ip_refresh = yes\n')))

        clear=''.join(setv(rp+key,0) for key in ('freight_amount','freight_days','freight_fee','freight_cargo','freight_to'))
        arrival=''
        for target in range(6):
            if target==rid:continue
            unload=''.join(iff(cv(rp+'freight_cargo','=',index),add(f'r{target}_'+key,val('freight_amount'))) for index,key in enumerate(STOCKS))
            unload+=add(f'r{target}_freight_received',val('freight_amount'))+clear
            arrival+=iff(cv(rp+'freight_amount','>',0)+cv(rp+'freight_to','=',target)+cv(f'r{target}_transport_capacity','>',0),unload)
        # Countdown never advances through GUI refresh; a disconnected target
        # holds arrived cargo rather than destroying or teleporting it.
        arrival=iff(cv(rp+'freight_days','>',0),sub(rp+'freight_days',1))+iff(cv(rp+'freight_days','=',0),arrival)
        arrivals+=iff(cv(rp+'freight_amount','>',0),arrival)
        send=''.join(iff(cv(rp+'freight_resource','=',index),sub(rp+key,val('freight_preview_amount'))) for index,key in enumerate(STOCKS))
        send+=setv(rp+'freight_amount',val('freight_preview_amount'))+setv(rp+'freight_days',val('freight_preview_days'))
        send+=setv(rp+'freight_cargo',val('freight_resource'))+setv(rp+'freight_to',val('freight_destination'))+setv(rp+'freight_fee',val('freight_preview_fee'))
        send+=sub('budget',val('freight_fee'))+add('freight_spent',val('freight_fee'))+add(rp+'freight_sent',val('freight_amount'))
        dispatch+=f'RUS_ip_r{rid}_freight_plan = yes\n'+iff(cv(rp+'freight_status','=',0),send)
        returned=''.join(iff(cv(rp+'freight_cargo','=',index),add(rp+key,val('freight_amount'))) for index,key in enumerate(STOCKS))
        returned+=add(rp+'freight_returned',val('freight_amount'))+add('budget',val('freight_fee'))+sub('freight_spent',val('freight_fee'))+clamp('freight_spent',0,1000000)+clear
        finish+=iff(cv(rp+'freight_amount','>',0),returned)
    for target in range(6):
        preview+=setv(f'r{target}_freight_incoming_count',0)+setv(f'r{target}_freight_incoming_amount',0)
        for source in range(6):
            if source==target:continue
            preview+=iff(cv(f'r{source}_freight_amount','>',0)+cv(f'r{source}_freight_to','=',target),add(f'r{target}_freight_incoming_count',1)+add(f'r{target}_freight_incoming_amount',P+f'r{source}_freight_amount'))
    for name,body in [('freight_preview',preview),('freight_arrivals',arrivals),('freight_dispatch',dispatch),('freight_finish',finish)]:effects.append(fx(name,body))
    return triggers,effects
