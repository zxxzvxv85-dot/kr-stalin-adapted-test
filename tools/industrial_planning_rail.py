"""Manual two-click rail planning, paid in the GUI queue, built on completion.

Native SOV_scripted_effects.txt uses var:ROOT.* state endpoints in build_railway.
There is no invented native construction-queue parameter. The end district owns
the paid queue; each order copies its endpoints and target level at acceptance.
"""
from industrial_planning_economy import P, PROJECTS, block, setv, add, sub, mul, div, cv, ge, iff, fx, clamp, rail_spec


def specification(start, end):
    return rail_spec('var:ROOT.'+P+start, 'var:ROOT.'+P+end)


def native_reward(start, end, level):
    return ''.join(iff(cv(level,'=',k),block('build_railway',f'level = {k}\n'+specification(start,end))) for k in range(1,6))


def seed_rail(cells):
    out=setv('rail_from',-1)+setv('rail_to',-1)+setv('rail_pick',0)+setv('rail_level',2)
    for key in ('from_state','to_state','from_x','from_y','to_x','to_y'):out+=setv('rail_'+key,0)
    for c in cells:
        for key in ('rail_from_state','rail_to_state','rail_level'):out+=setv(f'n{c["id"]}_'+key,0)
    return out


def map_pick(c):
    # Read the mode only once. Two independent ifs would make one click set
    # both endpoints. Clicking the start again keeps waiting for a destination.
    def point(which):
        out=setv('rail_'+which,c['id'])+setv('rail_'+which+'_state',c['state'])
        for axis in ('x','y'):out+=setv('rail_'+which+'_'+axis,round(c['geo_'+axis],3))
        return out
    return iff(cv('rail_pick','=',1),point('from')+setv('rail_pick',2))+block('else_if',
        block('limit',cv('rail_pick','=',2)+block('NOT',cv('rail_from','=',c['id'])))+point('to')+setv('rail_pick',0))


def queued_site(n):
    return (cv(n+'rail_from_state','>',0)+ge(n+'rail_level',1)+block('NOT',cv(n+'rail_level','>',5))+
        f'owns_state = var:ROOT.{P}{n}rail_from_state\ncontrols_state = var:ROOT.{P}{n}rail_from_state\n'+
        block('can_build_railway',specification(n+'rail_from_state',n+'rail_to_state')))


def render_rail(data):
    cells=data['cells'];effects=[];triggers=[]
    valid=ge('rail_from',0)+ge('rail_to',0)+block('NOT',cv('rail_from','=',P+'rail_to'))
    valid+=ge('rail_level',1)+block('NOT',cv('rail_level','>',5))
    valid+=('owns_state = var:ROOT.RUS_ip_rail_from_state\ncontrols_state = var:ROOT.RUS_ip_rail_from_state\n'
            'owns_state = var:ROOT.RUS_ip_rail_to_state\ncontrols_state = var:ROOT.RUS_ip_rail_to_state\n')
    valid+=block('can_build_railway',specification('rail_from_state','rail_to_state'))
    triggers.append(fx('rail_path_valid',valid))
    duplicate=''
    for c in cells:
        i=c['id'];n=f'n{i}_'
        forward=cv('rail_to','=',i)+cv(n+'rail_from_state','=',P+'rail_from_state')
        reverse=cv('rail_from','=',i)+cv(n+'rail_from_state','=',P+'rail_to_state')
        duplicate+=block('AND',cv(n+'project','=',10)+block('OR',block('AND',forward)+block('AND',reverse)))
    can='RUS_ip_editing = yes\nRUS_ip_rail_path_valid = yes\n'+ge('free_civs',PROJECTS[10]['civs'])+ge('funds',P+'rail_cost')
    can+=block('NOT',block('OR',duplicate))
    can+=block('OR',''.join(block('AND',cv('rail_to','=',c['id'])+cv(f'n{c["id"]}_project','=',0)) for c in cells))
    triggers.append(fx('can_build_10',can))
    reset=setv('rail_from',-1)+setv('rail_to',-1)+setv('rail_pick',0)
    reset+=setv('rail_from_state',0)+setv('rail_to_state',0)
    effects.append(fx('rail_choose',iff('RUS_ip_available = yes\nhas_country_flag = RUS_ip_open',reset+setv('rail_pick',1)+add('dirty',1))))
    effects.append(fx('rail_clear',reset+'RUS_ip_refresh = yes\n'))
    effects.append(fx('rail_cycle_level',add('rail_level',1)+iff(cv('rail_level','>',5),setv('rail_level',1))+'RUS_ip_refresh = yes\n'))
    # A transparent geographical estimate, not a claim to know the engine's
    # actual provincial route. Longer/higher-level projects cost and take more.
    forecast=''.join(setv('rail_'+key,0) for key in ('cost','days','gain','bottleneck','work'))
    calc=setv('rail_factor',P+'rail_to_x')+sub('rail_factor',P+'rail_from_x')
    calc+=iff(cv('rail_factor','<',0),mul('rail_factor',-1))
    calc+=setv('rail_span_y',P+'rail_to_y')+sub('rail_span_y',P+'rail_from_y')
    calc+=iff(cv('rail_span_y','<',0),mul('rail_span_y',-1))
    calc+=add('rail_factor',P+'rail_span_y')+div('rail_factor',200)+add('rail_factor',1)+mul('rail_factor',P+'rail_level')
    # Reuse the exact destination forecast including its neighbour power, then
    # restore the normal selection and all regular project forecasts.
    calc+=setv('rail_saved_selection',P+'selected')+setv('selected',P+'rail_to')+'RUS_ip_regional_forecasts = yes\n'
    for key in ('cost','days','gain','bottleneck'):calc+=setv('rail_'+key,P+'forecast_10_'+key)
    for key in ('cost','days'):calc+=mul('rail_'+key,P+'rail_factor')
    calc+=setv('rail_work',PROJECTS[10]['days'])+mul('rail_work',P+'rail_factor')
    calc+=setv('selected',P+'rail_saved_selection')+'RUS_ip_regional_forecasts = yes\n'
    forecast+=iff(ge('rail_from',0)+ge('rail_to',0),calc)
    effects.append(fx('rail_forecast',forecast))
    queue=''
    for c in cells:
        n=f'n{c["id"]}_'
        order=setv(n+'project',10)+setv(n+'work',0)+setv(n+'required',P+'rail_work')+setv(n+'paused',0)
        for key in ('from_state','to_state','level'):order+=setv(n+'rail_'+key,P+'rail_'+key)
        order+=setv(n+'paid',P+'rail_cost')+sub('funds',P+n+'paid')+add('funds_spent',P+n+'paid')
        queue+=iff(cv('rail_to','=',c['id']),order)
    queue+=setv('selected',P+'rail_to')+'clr_country_flag = RUS_ip_cancel_armed\nRUS_ip_refresh = yes\n'
    effects.append(fx('build_10','RUS_ip_refresh = yes\n'+iff('RUS_ip_can_build_10 = yes',queue)))
    return triggers,effects
