"""Opening-stage graph, event restrictions and actual-script lifecycle checks."""
from pathlib import Path
from collections import Counter
import copy,json,math,re,random,subprocess
from hoi4_politics_blocks import load,parse
import rework_savinkov_opening as build

ROOT=Path(__file__).resolve().parents[1]
FROOT=load(ROOT/build.NEW)
FOCI={n.value('id'):n for n in FROOT if n.k=='shared_focus'}
EFFECTS={n.k:n for n in load(ROOT/'common/scripted_effects/RUS_savinkov_opening_effects.txt')}
EFFECTS.update({n.k:n for n in load(ROOT/'common/scripted_effects/RUS effects (Russia).txt') if n.k in build.SPEC['anger_effects']})
EVENTS={n.value('id'):n for p in ['events/RUS events (Russia).txt','events/RUS_savinkov_opening_events.txt','events/KHI events (Khiva).txt'] for n in load(ROOT/p) if n.k.endswith('_event')}
MISSIONS={n.k:n for c in load(ROOT/'common/decisions/RUS_savinkov_opening_decisions.txt') for n in c.v}
ON=load(ROOT/'common/on_actions/RUS_savinkov_opening_on_actions.txt')[0]
COUNTRY_HISTORY=(ROOT/'history/countries/RUS - Russia.txt').read_text(encoding='utf-8-sig')
INITIAL_PROJECTS=parse(COUNTRY_HISTORY.split(build.HISTORY_BEGIN)[1].split(build.HISTORY_END)[0])

class Model:
    def __init__(self,reward_on_complete=True):
        self.flags=set();self.ideas=set();self.v={};self.temp={};self.pop={p:68/9 for p in build.PARTIES}|{'national_populist':32}
        self.gov='national_populist';self.tag='RUS';self.leader=True;self.manpower=1000000;self.pp=0;self.scope='country'
        self.completed=set();self.native_rewards=reward_on_complete;self.popups=[];self.loads=[];self.events=[];self.missions={};self.finished=set();self.day=0;self.buildings=[];self.slots=[];self.resources=[];self.external=Counter();self.state=None

    def number(self,value):
        if isinstance(value,list):
            result=0
            for n in value:
                if n.k=='value':result=self.number(n.v)
                elif n.k=='add':result+=self.number(n.v)
                elif n.k=='subtract':result-=self.number(n.v)
                elif n.k=='multiply':result*=self.number(n.v)
                elif n.k=='divide':result/=self.number(n.v)
                elif n.k=='clamp':result=max(self.number(n.value('min')),min(self.number(n.value('max')),result))
                else:raise AssertionError(('unhandled numeric operator',n.k))
            return result
        if value.startswith('party_popularity_100@'):return self.pop[value.split('@')[1]]
        try:return float(value)
        except ValueError:return self.temp.get(value,self.v.get(value,0))

    def cond(self,ns):
        if hasattr(ns,'v'):ns=ns.v
        results=[]
        for n in ns:
            if n.k in ['AND','hidden_trigger']:value=self.cond(n.v)
            elif n.k=='OR':value=any(self.cond([x]) for x in n.v)
            elif n.k=='NOT':value=not self.cond(n.v)
            elif n.k=='always':value=n.v=='yes'
            elif n.k in ['tag','original_tag']:value=self.tag==n.v
            elif n.k=='has_country_flag':value=n.v in self.flags
            elif n.k=='has_idea':value=n.v in self.ideas
            elif n.k=='has_government':value=self.gov==n.v
            elif n.k=='is_subject':value=n.v=='no'
            elif n.k=='RUS_boris_savinkov':value=self.leader
            elif n.k=='has_variable':value=n.v in self.v
            elif n.k=='has_completed_focus':value=n.v in self.completed
            elif n.k=='check_variable':
                c=n.v[0];left=self.temp.get(c.k,self.v.get(c.k,0));right=self.number(c.v)
                value={'=':lambda:math.isclose(left,right,abs_tol=1e-8),'>':lambda:left>right,'<':lambda:left<right,'>=':lambda:left>=right,'<=':lambda:left<=right}[c.op]()
            elif n.k=='has_war_with':value=False
            elif n.k=='surrender_progress':value=False
            else:raise AssertionError(('unhandled condition',n.k))
            results.append(value)
        return all(results)

    def run(self,nodes):
        if hasattr(nodes,'v'):nodes=nodes.v
        taken=None
        for n in nodes:
            if n.k=='if':
                taken=self.cond(n.one('limit'));self.run([x for x in n.v if x.k!='limit']) if taken else None;continue
            if n.k=='else_if':
                if not taken and self.cond(n.one('limit')):self.run([x for x in n.v if x.k!='limit']);taken=True
                continue
            if n.k=='else':
                if not taken:self.run(n.v)
                taken=None;continue
            taken=None
            if n.k in ['log','effect_tooltip','custom_effect_tooltip','search_filters']:continue
            if n.k=='hidden_effect':self.run(n.v)
            elif n.k=='RUS':
                previous=self.scope;self.scope='country';self.run(n.v);self.scope=previous
            elif n.k in ['set_variable','set_temp_variable','add_to_variable','add_to_temp_variable','subtract_from_variable']:
                c=n.v[0];target=self.temp if 'temp' in n.k else self.v;value=self.number(c.v)
                target[c.k]=value if n.k.startswith('set_') else target.get(c.k,0)+(-value if n.k.startswith('subtract') else value)
            elif n.k=='set_popularities':self.pop={x.k:self.number(x.v) for x in n.v}
            elif n.k=='set_country_flag':self.flags.add(n.v)
            elif n.k=='clr_country_flag':self.flags.discard(n.v)
            elif n.k=='add_ideas':self.ideas.add(n.v)
            elif n.k=='add_manpower':self.manpower+=self.number(n.v)
            elif n.k=='add_political_power':self.pp+=self.number(n.v)
            elif n.k=='complete_national_focus':
                if n.v not in self.completed:
                    self.popups.append(n.v)
                    self.completed.add(n.v)
                    if self.native_rewards:self.run(FOCI[n.v].one('completion_reward'))
            elif n.k=='unlock_national_focus':self.completed.add(n.v)
            elif n.k=='load_focus_tree':self.loads.append(n.value('tree') if isinstance(n.v,list) else n.v)
            elif n.k=='country_event':
                assert self.scope=='country',('country event sent from',self.scope)
                self.events.append((n.value('id'),self.day+int(n.value('days','0'))) if isinstance(n.v,list) else (n.v,self.day))
            elif n.k=='activate_mission':
                if n.v not in self.missions and n.v not in self.finished:self.missions[n.v]=self.day+int(MISSIONS[n.v].value('days_mission_timeout'))
            elif n.k.isdigit():
                old=self.state;self.state=int(n.k);self.run(n.v);self.state=old
            elif n.k=='add_building_construction':self.buildings.append((self.state,n.value('type'),int(n.value('level')),n.value('instant_build')))
            elif n.k=='add_extra_state_shared_building_slots':self.slots.append((self.state,int(n.v)))
            elif n.k=='add_resource':self.resources.append((int(n.value('state')),n.value('type'),int(n.value('amount'))))
            elif n.k in EFFECTS:self.run(EFFECTS[n.k])
            elif n.k in ['set_global_flag','set_victory_points','activate_targeted_decision','mark_focus_tree_layout_dirty']:continue
            elif n.k in ['RUS_select_AEG_nationalisation_states','rename_state_effect']:self.external[n.k]+=1
            else:raise AssertionError(('unhandled effect',n.k))

    def tick(self):
        self.day+=1;self.run(ON.one('on_daily_RUS').one('effect'))
        for key,expiry in list(self.missions.items()):
            m=MISSIONS[key]
            if self.cond(m.one('cancel_trigger')):del self.missions[key];self.finished.add(key)
            # Native missions complete as soon as available passes. Omitting
            # available is an unconditional success, not a timeout-only timer.
            elif m.one('available') is None or self.cond(m.one('available')):
                del self.missions[key];self.finished.add(key)
                if m.one('complete_effect'):self.run(m.one('complete_effect'))
            elif self.day>=expiry:
                del self.missions[key];self.finished.add(key);self.run(m.one('timeout_effect'))

def main():
    tree=next(n for n in FROOT if n.k=='focus_tree');assert tree.value('id')==build.TREE
    refs=[n.v for n in tree.children('shared_focus')];assert len(refs)==len(set(refs))==10 and set(refs)==set(build.LAYOUT)==set(FOCI)
    parents={key:[n.v for p in f.children('prerequisite') for n in p.children('focus')] for key,f in FOCI.items()}
    assert parents=={k:v[2] for k,v in build.LAYOUT.items()}
    assert len(FOCI['RUS_declare_russian_state'].children('prerequisite'))==1
    assert FOCI[build.VOZHD].value('cost')=='3' and FOCI[build.CRACK].value('cost')=='2'
    for key,f in FOCI.items():
        assert int(f.value('x'))==build.LAYOUT[key][0] and int(f.value('y'))==build.LAYOUT[key][1]
        for other,g in FOCI.items():
            if key!=other:assert abs(int(f.value('x'))-int(g.value('x')))*96>=174 or abs(int(f.value('y'))-int(g.value('y')))*130>=128
    definitions=Counter(n.value('id') for p in (ROOT/'common/national_focus').glob('*.txt') for n in load(p) if n.k=='shared_focus')
    definitions.update(f.value('id') for p in (ROOT/'common/national_focus').glob('*.txt') for t in load(p) if t.k=='focus_tree' for f in t.children('focus'))
    assert all(definitions[k]==1 for k in FOCI)
    for key,chosen in build.SPEC['event_choices'].items():assert [o.value('name') for o in EVENTS[key].children('option')]==[chosen]
    for key in build.SPEC['disabled_events']:assert EVENTS[key].one('trigger').value('always')=='no'
    assert not re.search(r'unit_leader_event\s*=\s*\{\s*id\s*=\s*russia_events\.(133|134)\b',EVENTS['russia_events.124'].raw())
    native_funeral=next(n for n in load(build.KR/build.EV) if n.value('id')=='russia_events.113')
    assert EVENTS['russia_events.113'].one('option').norm()==native_funeral.children('option')[1].norm()
    assert len(EVENTS['russia_events.924'].children('option'))==1
    for key in ['russia_events.922','russia_events.923']:assert 'NOT = { has_country_flag = RUS_opening_active }' in EVENTS[key].one('trigger').raw()
    assert EVENTS['russia_events.112'].raw().index('RUS_opening_request_army_minister')<EVENTS['russia_events.112'].raw().index('kill_character')
    funeral=EVENTS['russia_events.112'].children('option')[0]
    assert any(n.one('country_event') and n.one('country_event').value('id')=='russia_events.113' for n in funeral.children('RUS'))
    assert not ON.children('on_daily') and len(ON.children('on_daily_RUS'))==1
    assert ON.one('on_startup').one('effect').one('RUS').value('country_event')=='rus_opening.3'
    boot=EVENTS['rus_opening.3'];assert boot.value('hidden')==boot.value('is_triggered_only')==boot.value('fire_only_once')=='yes'
    assert boot.one('immediate').value('RUS_opening_initialise')=='yes'
    assert 'complete_national_focus' not in EFFECTS['RUS_opening_initialise'].raw()
    legacy=next(n for n in load(ROOT/build.F) if n.k=='focus_tree')
    assert not {n.value('id') for n in legacy.children('focus')}&set(build.SPEC['retired_focuses'])
    retired=load(ROOT/build.RETIRED_PATH)[0]
    assert retired.value('id')==build.RETIRED_TREE and retired.value('default')=='no' and retired.one('country').value('factor')=='0'
    assert {n.value('id') for n in retired.children('focus')}==set(build.SPEC['retired_focuses'])
    for focus in retired.children('focus'):
        assert focus.one('allow_branch').value('always')=='no' and focus.one('available').value('always')=='no'
    m=Model()
    for focus in legacy.children('focus'):
        gates=[n for n in focus.one('allow_branch').children('NOT') if n.value('has_government')=='national_populist']
        assert gates and not m.cond([gates[-1]]),focus.value('id')
    for focus in load(ROOT/'common/national_focus/00_RUS_future_domestic_skeleton.txt'):
        assert not m.cond(focus.one('allow_branch')),focus.value('id')
    # Validate native sprite registration as well as syntactic icon fields.
    game=ROOT.parents[3]/'common/Hearts of Iron IV'
    registered=set()
    for library in [game,build.KR,ROOT]:
        for p in (library/'interface').rglob('*.gfx'):
            registered.update(re.findall(r'\bname\s*=\s*"([^"]+)"',p.read_text(encoding='utf-8-sig')))
    for mission in MISSIONS.values():
        assert 'GFX_decision_'+mission.value('icon') in registered,mission.k
        assert not Model().cond(mission.one('available')) and mission.value('selectable_mission')=='no'
    for num in [1,2]:assert EVENTS[f'rus_opening.{num}'].value('picture') in registered
    for focus in FOCI.values():assert focus.value('icon') in registered,focus.value('id')
    for ideas in load(ROOT/'common/ideas/RUS_savinkov_opening_ideas.txt'):
        for category in ideas.v:
            for idea in category.v:assert 'GFX_idea_'+idea.value('picture') in registered,idea.k
    for native_completion_rewards in [False,True]:
        m=Model(native_completion_rewards);m.run(INITIAL_PROJECTS)
        # Rewards already exist at time zero, before any event or startup effect.
        assert len(m.buildings)==13 and not m.events and m.day==0 and not m.loads
        assert m.v['RUS_completed_voskhod_projects']==5 and m.v['RUS_voskhod_cap']==420000
        before=copy.deepcopy((m.buildings,m.slots,m.resources,m.v))
        m.run(EFFECTS['RUS_opening_initialise']);assert (m.buildings,m.slots,m.resources,m.v)==before
        snapshot=copy.deepcopy(m.__dict__)
        m.run(EFFECTS['RUS_opening_initialise']);assert m.__dict__==snapshot,'Startup replay changed rewards'
        assert m.completed=={'RUS_voskhod','RUS_artelizatsiya'} and m.loads==[build.TREE]
        assert m.v['RUS_voskhod_cap']==m.v['RUS_voskhod_remaining_mp']==420000 and m.v['RUS_voskhod_current_mp']==m.v['RUS_voskhod_total_mp']==0
        assert m.v['RUS_completed_voskhod_projects']==5 and m.manpower==1000000 and m.pp==0 and not m.events and not m.popups
        assert m.external['RUS_select_AEG_nationalisation_states']==1
        assert len(m.buildings)==13 and all(x[3]=='yes' for x in m.buildings)
        assert sum(x[2] for x in m.buildings if x[1]=='industrial_complex')==8
        assert sum(x[2] for x in m.buildings if x[1]=='infrastructure')==8 and sum(n for _,n in m.slots)==8
        expected=Counter((int(s.k),n.value('type'),int(n.value('level'))) for raw in build.SPEC['completed_projects'].values() for s in parse(raw)[0].v if s.k.isdigit() for n in s.children('add_building_construction'))
        assert Counter((s,t,n) for s,t,n,_ in m.buildings)==expected
        assert set(m.resources)=={(644,'steel',10),(397,'steel',12)}
        assert all('RUS_opening_prebuilt_'+p in m.flags for p in build.PROJECTS)
    initialiser=EFFECTS['RUS_opening_initialise'].raw()
    assert [n.v for n in parse(COUNTRY_HISTORY) if n.k=='add_ideas' and n.v=='tak']==['tak']
    assert 'add_ideas = tak' not in initialiser
    concern=next(n for root in load(ROOT/'common/ideas/RUS ideas (Russia).txt') for category in root.v if category.k=='industrial_concern' for n in category.v if n.k=='tak')
    assert concern.one('modifier').value('production_speed_industrial_complex_factor')=='0.1'
    assert concern.one('modifier').value('production_speed_arms_factory_factor')=='0.1'
    assert not any(word in initialiser for word in ['add_building_construction','add_extra_state_shared_building_slots','add_resource','RUS_opening_prebuilt_','RUS_completed_voskhod_projects','RUS_voskhod_cap'])
    rng=random.Random(20261018)
    for _ in range(60):
        m=Model();weights=[rng.random()**4 for _ in range(10)];total=sum(weights);m.pop=dict(zip(build.PARTIES+['national_populist'],[100*x/total for x in weights]));before=m.pop.copy();m.run(EFFECTS['RUS_opening_transfer_opposition_support'])
        for p in build.PARTIES:assert math.isclose(m.pop[p],max(0,before[p]-2),abs_tol=1e-7)
        assert math.isclose(sum(m.pop.values()),100,abs_tol=1e-7)
        assert math.isclose(m.pop['national_populist']-before['national_populist'],sum(min(2,before[p]) for p in build.PARTIES),abs_tol=1e-7)
    for level in [0,4,5,6,7,8,10]:
        for minister,num in [('wrangel',1),('denikin',2)]:
            m=Model();m.flags.add(build.ACTIVE);m.v['RUS_military_anger']=level;m.flags.add('RUS_opening_'+minister+'_minister')
            for _ in range(4):m.run(EFFECTS['RUS_opening_check_military_anger'])
            assert m.events==([(f'rus_opening.{num}',1)] if level>=5 else [])
    m=Model();m.flags.add(build.ACTIVE);m.v['RUS_military_anger']=5;m.run(EFFECTS['RUS_opening_check_military_anger']);assert not m.events
    m.v['RUS_military_anger']=1;m.flags.add('RUS_opening_denikin_minister');m.run(EFFECTS['RUS_opening_check_military_anger']);assert m.events==[('rus_opening.2',1)]
    # Kornilov's death is a unit-leader event: nested helpers must select a
    # country recipient, and a queued popup must not count as delivered yet.
    for minister,num in [('wrangel',1),('denikin',2)]:
        m=Model();m.scope='unit_leader';m.flags.add(build.ACTIVE)
        m.run(EFFECTS['RUS_opening_request_army_minister']);m.run(EFFECTS['RUS_opening_request_army_minister'])
        assert m.scope=='unit_leader' and m.events==[('russia_events.124',1)]
        m.events.clear();m.flags.add('RUS_opening_'+minister+'_minister');m.v['RUS_military_anger']=5
        m.run(EFFECTS['RUS_opening_check_military_anger']);m.run(EFFECTS['RUS_opening_check_military_anger'])
        assert m.events==[(f'rus_opening.{num}',1)] and m.scope=='unit_leader'
        assert 'RUS_opening_military_warning_queued' in m.flags and 'RUS_opening_military_warning_sent' not in m.flags
        m.scope='country';event=EVENTS[f'rus_opening.{num}'];assert m.cond(event.one('trigger'))
        m.run(event.one('immediate'));assert 'RUS_opening_military_warning_sent' in m.flags
        m.run(EFFECTS['RUS_opening_check_military_anger']);assert len(m.events)==1
        m.run([n for n in event.one('option').v if n.k!='name'])
        assert m.missions=={'RUS_opening_military_action':180} and 'RUS_opening_military_warning_queued' not in m.flags
        m.run(EFFECTS['RUS_opening_check_military_anger']);assert len(m.events)==1
    # A pre-emptive sent marker alone cannot suppress a warning without a queue
    # or countdown. No reward, phase, or anger value is reset to retry delivery.
    m=Model();m.flags.update([build.ACTIVE,'RUS_opening_denikin_minister','RUS_opening_military_threshold_reached','RUS_opening_military_warning_sent']);m.v['RUS_military_anger']=4
    m.tick();m.tick();assert m.events==[('rus_opening.2',2)] and m.v['RUS_military_anger']==4 and m.manpower==1000000
    for event in ['rus_opening.1','rus_opening.2']:
        m=Model();m.flags.add(build.ACTIVE);opt=EVENTS[event].children('option')[0];m.run([n for n in opt.v if n.k not in ['name']]);m.run([n for n in opt.v if n.k not in ['name']]);assert m.missions=={'RUS_opening_military_action':180}
        for _ in range(180):m.tick()
        assert not m.missions and not m.events and 'RUS_opening_military_countdown_finished' in m.flags
    for level in [7,8,9,10]:
        m=Model();m.flags.add(build.ACTIVE);m.v['RUS_popular_anger']=level
        for _ in range(5):m.run(EFFECTS['RUS_opening_check_popular_anger'])
        if level<8:assert not m.missions;continue
        assert m.missions=={'RUS_opening_resistance_wave':7}
        for _ in range(6):m.tick()
        assert m.missions=={'RUS_opening_resistance_wave':7} and not m.events
        m.tick();assert m.events==[('russia_events.924',7)] and 'RUS_opening_revolt_ready' in m.flags
        assert m.cond(EVENTS['russia_events.924'].one('trigger'))
        for _ in range(6):m.tick()
        assert len(m.events)==1
    m=Model();m.run(EFFECTS['RUS_opening_initialise']);m.v['RUS_popular_anger']=8;m.run(EFFECTS['RUS_opening_check_popular_anger']);m.gov='radical_socialist';cap=m.v.copy();m.run(EFFECTS['RUS_opening_finish_phase']);m.run(EFFECTS['RUS_opening_finish_phase']);m.tick();assert m.loads==[build.TREE,'Russia_Focus'] and not m.missions and m.v==cap
    # Daily manpower is a single country hook and continues only while its idea exists.
    m=Model();m.ideas.add('RUS_opening_disordered_industry');m.tick();assert m.manpower==999800;m.ideas.clear();m.tick();assert m.manpower==999800
    # Two modified native blocks. Two existing replacements retain sole ownership.
    native={n.k:n.norm() for n in load(build.KR/'common/scripted_effects/RUS effects (Russia).txt')};actual={n.k:n.norm() for n in load(ROOT/'common/scripted_effects/RUS effects (Russia).txt')}
    assert set(native)-set(actual)==set(build.DELEGATED_EFFECTS) and not set(actual)-set(native)
    assert {k for k in actual if native[k]!=actual[k]}==set(build.SPEC['anger_effects'])
    for key,owner in build.DELEGATED_EFFECTS.items():
        assert sum(n.k==key for p in (ROOT/'common/scripted_effects').glob('*.txt') for n in load(p))==1
        assert any(n.k==key for n in load(ROOT/owner))
    decision_roots=load(ROOT/build.DC);decisions={n.k:n for c in decision_roots for n in c.v if isinstance(c.v,list)}
    voskhod=next(c for c in decision_roots if c.k=='RUS_voskhod_decisions')
    assert 'RUS_decrease_black_monday' not in voskhod.raw() and 'RUS_black_monday' not in voskhod.raw()
    assert decisions['RUS_utilise_army'].value('fire_only_once')=='yes'
    assert decisions['RUS_RASOLKO'].one('visible').value('always')=='no'
    assert decisions['RUS_nationalise_AEG_electrical_facilities'].value('days_remove')=='RUS_tesla_industry_time_180?180'
    for p in build.PROJECTS:assert 'RUS_opening_prebuilt_'+p in decisions[p].one('visible').raw()
    for lang in ['simp_chinese','english','russian']:
        p=ROOT/f'localisation/{lang}/replace/RUS_savinkov_opening_l_{lang}.yml';raw=p.read_bytes();assert raw.startswith(b'\xef\xbb\xbf');keys=re.findall(r'^\s*(\w+):',raw.decode('utf-8-sig'),re.M);assert len(keys)==len(set(keys))
        daily=next(line for line in raw.decode('utf-8-sig').splitlines() if line.strip().startswith('RUS_opening_daily_manpower_tt:'))
        assert '£manpower_texticon£' in daily and '§R-200§!' in daily and '−200' not in daily and '—200' not in daily
        assert not {'RUS_anger_decisions_natpop','RUS_opening_anger_rules','RUS_opening_anger_rules_legacy'}&set(keys)
    assert not (ROOT/'common/scripted_localisation/RUS_savinkov_opening_loc.txt').exists()
    print('PASS: ten-focus isolated opening, zero-time country-history projects and accounting, no startup reward replay, restricted event outcomes, disabled minister flavour events, 60 popularity conservation cases, thresholds, minister deferral, 7/180-day lifecycles, stage handoff, single daily manpower hook, original effects preserved, and localisation BOM/keys.')

if __name__=='__main__':main()
