"""Execute the generated railway UI and paid queue, not a mirrored algorithm."""
import copy
import math
from test_industrial_planning import DATA, TR, started, call, gui_click, plan_rail, select, put, v, check, finish, invariant


def rail_tests():
    count=0
    q=started();cash=v(q,'funds');days=v(q,'days_left')
    gui_click(q,'ip_rail_choose');assert v(q,'rail_pick')==1
    gui_click(q,'ip_cell_3');assert v(q,'rail_from')==3 and v(q,'rail_to')==-1 and v(q,'rail_pick')==2
    call(q,'build_10');assert v(q,'queued')==0
    gui_click(q,'ip_cell_3');assert v(q,'rail_to')==-1 and v(q,'rail_pick')==2
    gui_click(q,'ip_cell_5');assert v(q,'rail_to')==5 and v(q,'rail_pick')==0
    gui_click(q,'ip_cell_8');assert v(q,'rail_from')==3 and v(q,'rail_to')==5
    assert v(q,'funds')==cash and v(q,'days_left')==days and not q['rewards'];count+=5
    costs=[];work=[]
    for level in range(1,6):
        q=started();plan_rail(q,3,5,level)
        assert check(TR['RUS_ip_can_build_10'],q)
        cash=v(q,'funds');cost=v(q,'rail_cost');required=v(q,'rail_work');eta=v(q,'rail_days')
        call(q,'build_10');assert v(q,'n5_project')==10 and v(q,'reserved_civs')==3
        assert math.isclose(cash-v(q,'funds'),cost) and v(q,'n5_required')==required
        assert math.isclose(v(q,'n5_eta'),eta) and not q['rewards']
        saved=(v(q,'n5_rail_from_state'),v(q,'n5_rail_to_state'),v(q,'n5_rail_level'))
        plan_rail(q,16,21,5);call(q,'close_effect');call(q,'open_effect')
        restored=copy.deepcopy(q);call(restored,'refresh');assert saved==(v(restored,'n5_rail_from_state'),v(restored,'n5_rail_to_state'),v(restored,'n5_rail_level'))
        finish(q,5);assert q['rail_orders']==[(DATA['cells'][3]['state'],219,level)]
        assert v(q,'reserved_civs')==0 and v(q,'consumed_steel')>0 and v(q,'consumed_coal')>0
        before=copy.deepcopy(q['rewards']);call(q,'complete_5_10');assert q['rewards']==before
        invariant(q);costs.append(cost);work.append(required);count+=1
    assert all(b>a for a,b in zip(costs,costs[1:])) and all(b>a for a,b in zip(work,work[1:]));count+=1
    # Reverse routes cannot duplicate an existing order. Another line to a busy
    # destination also cannot overwrite paid work.
    q=started();plan_rail(q,3,5);call(q,'build_10');cash=v(q,'funds')
    for a,b in ((3,5),(5,3),(8,5)):
        plan_rail(q,a,b);call(q,'build_10');assert v(q,'queued')==1 and v(q,'funds')==cash;count+=1
    # No shared-building-slot requirement, but domestic path and ownership are
    # required both at acceptance and each construction day.
    q=started();q['states'][219].update(slots=3,infrastructure=5,category='twelve');plan_rail(q,3,5)
    call(q,'build_10');assert v(q,'n5_project')==10;count+=1
    pair=tuple(sorted((DATA['cells'][3]['state'],219)))
    for reason in ('origin','destination','path'):
        q=started();plan_rail(q,3,5)
        if reason=='origin':q['controlled'].discard(pair[0])
        elif reason=='destination':q['owned'].discard(pair[1])
        else:q['blocked_paths']={pair}
        call(q,'build_10');assert v(q,'queued')==0;count+=1
    q=started();plan_rail(q,3,5);call(q,'build_10');paid=v(q,'n5_paid');q['blocked_paths']={pair}
    call(q,'daily');assert v(q,'n5_work')==0 and v(q,'reserved_civs')==0 and not q['rewards']
    select(q,5);q['flags'].add('RUS_ip_cancel_armed');call(q,'cancel')
    assert math.isclose(v(q,'funds_refunded'),paid*.75) and not q['rewards'];invariant(q);count+=1
    q=started(False);q['steel']=q['coal']=0;plan_rail(q,3,5);call(q,'build_10');call(q,'daily')
    assert v(q,'n5_project')==10 and v(q,'n5_work')==0 and not q['rewards'];count+=1
    q=started();plan_rail(q,3,5);call(q,'build_10');put(q,'days_left',1);call(q,'daily')
    assert v(q,'queued')==0 and not q['rewards'] and v(q,'reserved_civs')==0;invariant(q);count+=1
    q=started();plan_rail(q,3,5,5);gui_click(q,'ip_rail_level');assert v(q,'rail_level')==1
    gui_click(q,'ip_rail_clear');assert v(q,'rail_from')==v(q,'rail_to')==-1 and v(q,'rail_pick')==0
    assert not check(TR['RUS_ip_can_build_10'],q);count+=1
    return count


if __name__=='__main__':print(f'PASS: {rail_tests()} manual railway scenarios (model, not engine).')
