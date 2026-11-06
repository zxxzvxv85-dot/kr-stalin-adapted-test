"""Execute generated plan effects; native engine timing still needs HOI4 QA."""
import copy,hashlib,json,math,re,unittest
from pathlib import Path
from doudizhu_script_model import ScriptModel,load_effects
from hoi4_politics_blocks import parse,load
from national_plan_catalog import ROOT,DATA,PROJECTS,CORRIDORS,MIO_TARGETS,MIO_REWARDS,CONSORTIUM_MIOS,FACTORY_GOALS
from national_plan import FX,DM,DEC,CAT,P,var,native_base,goals,restore,mio_preview
from generate_provisional_industry_gui import render

EFFECTS=load_effects((ROOT/FX).read_text(encoding='utf8'))
TR={n.k:n.v for n in load(ROOT/'common/scripted_triggers/RUS_national_plan_triggers.txt')}
NODES={n.k:n for n in next(n for n in load(ROOT/DEC) if n.k==CAT).v}

def walk(nodes):
    for n in nodes:
        yield n
        if isinstance(n.v,list):yield from walk(n.v)

class Model(ScriptModel):
    def __init__(self):
        super().__init__(copy.deepcopy(EFFECTS));self.context=True;self.stock=10000;self.scope=None;self.mio_scope=None;self.aat=True;self.events=[];self.offsite={};self.focuses=set();self.preview_mios=[]
        self.mios={token:{'size':0,'available':True,'assigned':False} for token in set(CONSORTIUM_MIOS)|{row[i] for row in MIO_TARGETS.values() for i in (0,2) if row[i]}}
        self.trigger_root='RUS';self.ai=False
        self.country=self.vars;self.country.update({'global.num_days':100,'year':1936,'num_of_available_civilian_factories':50,
            'RUS_basic_education_level':50,'RUS_higher_education_level':50,'RUS_education_enthusiasm':50,
            'RUS_nat_machine_stock':1000,'RUS_nat_target':1000,'RUS_nat_installed':0,'RUS_first_five_year_plan_stage':3})
        self.flags.update({'RUS_education_system_active','RUS_nat_enabled','RUS_agri_management_unlocked'})
        self.states={s:{'owned':True,'infrastructure':1,'industrial_complex':1,'state_population':100000,'resource@steel':0} for p in PROJECTS for s in p['states']}
        self.states.update({s:{'owned':True,'infrastructure':1,'industrial_complex':1} for c in CORRIDORS for s in c['states'] if s not in self.states})
        self.dynamic=set();self.state_mods={s:set() for s in self.states};self.state_flags={s:set() for s in self.states};self.timers={};self.rail=True;self.legacy_rewards={}
        # Legacy reward execution is structurally checked in full below. Here
        # replace that exact contiguous subtree with a counter, leaving all new
        # guards, settlement, goals, refunds and generated rewards executable.
        for p in PROJECTS:
            if not p['legacy']:continue
            signature=[n.norm() for n in parse(native_base(p))]
            for n in walk([self.effects[var(p,'finish')]]):
                if not isinstance(n.v,list):continue
                for i in range(len(n.v)-len(signature)+1):
                    if [x.norm() for x in n.v[i:i+len(signature)]]==signature:
                        n.v[i:i+len(signature)]=parse('model_legacy_reward = '+p['key']);break
    def number(self,v):
        if isinstance(v,str) and v.startswith(('PREV.','ROOT.')):return self.country.get(v.split('.',1)[1],0)
        if isinstance(v,str) and re.match(r'^\d+\.building_level@',v):
            state,kind=v.split('.building_level@');return self.states[int(state)].get(kind,0)
        if isinstance(v,str) and v.startswith('building_level@'):return self.vars.get(v.split('@')[1],0)
        if isinstance(v,str) and v.startswith('days_decision_timeout@'):return self.timers.get(v.split('@')[1],0)
        if v in ('global.num_days','year'):return self.country[v]
        return super().number(v)
    def check(self,nodes):
        if hasattr(nodes,'v'):nodes=nodes.v
        for n in nodes:
            if n.k in TR:ok=self.check(TR[n.k])==(n.v=='yes')
            elif n.k=='has_dlc_aat':ok=self.aat==(n.v=='yes')
            elif n.k=='has_completed_focus':ok=n.v in self.focuses
            elif n.k=='has_military_industrial_organization':ok=n.v in self.mios
            elif n.k.startswith('mio:'):
                before=self.mio_scope;self.mio_scope=n.k.split(':')[1]
                ok=self.mio_scope in self.mios and self.check(n.v);self.mio_scope=before
            elif n.k in ('is_mio_available','is_mio_assigned_to_task'):
                ok=self.mios[self.mio_scope]['available' if n.k=='is_mio_available' else 'assigned']==(n.v=='yes')
            elif n.k in ('RUS_rc_stalin_phase','has_socialist_government'):ok=self.context==(n.v=='yes')
            elif n.k=='custom_trigger_tooltip':ok=self.check([x for x in n.v if x.k!='tooltip'])
            elif n.k=='has_equipment':ok=all(self.compare(self.stock,self.number(x.v),x.op) for x in n.v)
            elif n.k=='num_of_civilian_factories_available_for_projects':ok=self.compare(50,self.number(n.v),n.op)
            elif n.k.isdigit():
                oldscope,oldvars=self.scope,self.vars;self.scope=int(n.k);self.vars=self.states[self.scope]
                ok=self.check(n.v);self.scope,self.vars=oldscope,oldvars
            elif n.k=='is_ai':ok=self.ai==(n.v=='yes')
            elif n.k=='is_owned_and_controlled_by_ROOT_or_subject':ok=self.states[self.scope]['owned'] and self.states[self.scope].get('controlled',True)
            elif n.k=='is_owned_and_controlled_by':
                target=self.trigger_root if n.v=='ROOT' else n.v
                ok=target=='RUS' and self.states[self.scope]['owned'] and self.states[self.scope].get('controlled',True)
            elif n.k=='is_core_of':
                target=self.trigger_root if n.v=='ROOT' else n.v
                ok=target=='RUS' and self.states[self.scope].get('core',True)
            elif n.k=='state':ok=self.scope==int(n.v)
            elif n.k=='has_state_category':ok=self.vars.get('category')==n.v
            elif n.k=='has_state_flag':ok=n.v in self.state_flags.get(self.scope,set())
            elif n.k=='has_dynamic_modifier':ok=n.value('modifier') in (self.state_mods[self.scope] if self.scope is not None else self.dynamic)
            elif n.k=='has_railway_connection':ok=self.rail
            elif n.k in ('infrastructure','industrial_complex','arms_factory','energy_infrastructure','industrial_infrastructure'):
                ok=self.compare(self.vars.get(n.k,0),self.number(n.v),n.op)
            else:ok=super().check([n])
            if not ok:return False
        return True
    def run(self,nodes):
        pending=[]
        native={'add_equipment_to_stockpile','add_dynamic_modifier','remove_dynamic_modifier','add_days_remove','remove_decision','remove_targeted_decision',
            'effect_tooltip','custom_effect_tooltip','force_update_dynamic_modifier','add_extra_state_shared_building_slots','add_building_construction',
            'add_manpower','add_resource','build_railway','model_legacy_reward','RUS_education_refresh','RUS_agri_credit_score','RUS_nat_refresh','every_owned_state','set_state_flag','clr_state_flag','add_mio_size','country_event','add_offsite_building'}
        for n in nodes:
            if n.k not in native and not n.k.isdigit() and not n.k.startswith('mio:'):pending.append(n);continue
            if pending:super().run(pending);pending=[]
            if n.k.startswith('mio:'):
                before=self.mio_scope;self.mio_scope=n.k.split(':')[1];self.run(n.v);self.mio_scope=before
            elif n.k=='add_mio_size':self.mios[self.mio_scope]['size']+=int(n.v)
            elif n.k=='effect_tooltip':self.preview_mios.extend(x.k.split(':',1)[1] for x in walk(n.v) if x.k.startswith('mio:'))
            elif n.k=='country_event':self.events.append(n.v if isinstance(n.v,str) else n.value('id'))
            elif n.k=='add_offsite_building':
                assert self.scope is None,'offsite factories belong to the country'
                kind=n.value('type');self.offsite[kind]=self.offsite.get(kind,0)+int(n.value('level'))
            elif n.k=='every_owned_state':
                for sid,data in self.states.items():
                    if not data['owned']:continue
                    oldscope,oldvars=self.scope,self.vars;self.scope=sid;self.vars=data
                    if self.check(n.one('limit')):self.run([x for x in n.v if x.k!='limit'])
                    self.scope,self.vars=oldscope,oldvars
            elif n.k=='set_state_flag':self.state_flags.setdefault(self.scope,set()).add(n.v)
            elif n.k=='clr_state_flag':self.state_flags.setdefault(self.scope,set()).discard(n.v)
            elif n.k.isdigit():
                oldscope,oldvars=self.scope,self.vars;self.scope=int(n.k);self.vars=self.states[self.scope]
                self.run(n.v);self.scope,self.vars=oldscope,oldvars
            elif n.k=='add_equipment_to_stockpile':self.stock+=self.number(n.value('amount'))
            elif n.k in ('add_dynamic_modifier','remove_dynamic_modifier'):
                target=self.dynamic if self.scope is None else self.state_mods[self.scope]
                target.add(n.value('modifier')) if n.k.startswith('add_') else target.discard(n.value('modifier'))
            elif n.k=='add_days_remove':
                # The real effect parses integer literals, not variable names.
                assert re.fullmatch(r'-?\d+',n.value('days')),n.raw()
                self.timers[n.value('decision')]=self.timers.get(n.value('decision'),0)+int(n.value('days'))
            elif n.k=='remove_decision':self.timers.pop(n.v,None)
            elif n.k=='remove_targeted_decision':self.timers.pop(n.value('decision'),None)
            elif n.k=='model_legacy_reward':self.legacy_rewards[n.v]=self.legacy_rewards.get(n.v,0)+1
            elif n.k=='add_extra_state_shared_building_slots':self.vars['slots']=self.vars.get('slots',0)+int(n.v)
            elif n.k=='add_building_construction':
                t=n.value('type');self.vars[t]=self.vars.get(t,0)+int(n.value('level'))
            elif n.k=='add_manpower':self.vars['state_population']=self.vars.get('state_population',0)+int(n.v)
            elif n.k=='add_resource':
                t='resource@'+n.value('type');self.vars[t]=self.vars.get(t,0)+int(n.value('amount'))
            elif n.k=='RUS_agri_credit_score':self.vars['land_awarded']=self.vars.get('land_awarded',0)+self.vars['RUS_agri_score_award']
            elif n.k in ('RUS_education_refresh','RUS_nat_refresh','build_railway'):pass
            # Tooltip-only effects never execute their nested reward previews.
        if pending:super().run(pending)
    def initialize(self):self.call('RUS_np_initialize');return self
    def start(self,p):
        self.timers[p['id']]=self.vars.get(var(p,'initial_days'),p['fallback']);self.call(var(p,'begin'))
    def advance(self,p,order='before'):
        self.country['global.num_days']+=1
        if order=='before':self.engine()
        self.call('RUS_np_daily')
        if order=='after':self.engine()
        else:self.engine(decay=False)
    def engine(self,decay=True):
        for key in list(self.timers):
            if decay:self.timers[key]-=1
            if self.timers[key]<=0:
                self.timers.pop(key,None)
                p=next(p for p in PROJECTS if p['id']==key)
                self.call(var(p,'finish'))

class PlanTests(unittest.TestCase):
    def test_managed_projects_cannot_expand_to_world_targets(self):
        targeted={'state_target','state_trigger','targets','target_array','target_trigger','target_root_trigger'}
        for p in PROJECTS:
            n=NODES[p['id']]
            self.assertFalse(targeted & {x.k for x in n.v},p['id'])
            self.assertNotEqual(n.value('cancel_if_not_visible'),'yes',p['id'])
            self.assertEqual(n.value('on_map_mode'),'decision_view_only')
        for key,n in NODES.items():
            if key.startswith(P):self.assertEqual(n.value('on_map_mode'),'decision_view_only',key)
        # Original native target semantics outside the managed layer stay intact.
        for p in PROJECTS:
            if p['legacy']:
                self.assertEqual(NODES[p['original_id']].value('state_target'),parse(p['original'])[0].value('state_target'))

    def test_timer_effects_use_native_integer_literals_and_synced_tokens(self):
        for n in walk(list(EFFECTS.values())):
            if n.k=='add_days_remove':self.assertRegex(n.value('days'),r'^-?\d+$')
        tokens=(ROOT/'common/synchronized_dynamic_tokens/RUS_national_plan_tokens.txt').read_text().split()
        self.assertEqual(set(tokens),{p['id'] for p in PROJECTS})
        m=Model();p=PROJECTS[0]
        for delta in (-7301,-4096,-1025,-1,0,1,1025,4096,7301):
            m.timers[p['id']]=7500;m.vars[P+'adjust']=delta
            m.call(var(p,'apply_timer_delta'))
            self.assertEqual(m.timers[p['id']],7500+delta)
            self.assertEqual(m.vars[P+'adjust'],0)

    def test_rail_highlights_match_exact_construction_provinces(self):
        for c in CORRIDORS:
            p=next(p for p in PROJECTS if c['project']==p.get('original_id',p['id']))
            for key in (p['id'],P+'upgrade_'+c['key']):
                h=NODES[key].one('highlight_states')
                self.assertEqual([int(n.k) for n in h.one('highlight_provinces').v],c['path'],key)
                self.assertEqual(h.value('highlight_only_provinces'),'yes')
                self.assertIsNone(h.one('highlight_state_targets'))

    def test_rural_modifier_is_continuous_bounded_and_does_not_stack(self):
        m=Model();s=next(s for s in m.states if s not in (219,195,217))
        m.states[s].update(category='two',core=True,infrastructure=1,industrial_complex=0,arms_factory=0)
        m.initialize();self.assertIn('RUS_np_rural_area',m.state_flags[s])
        last=-1
        for score in (-50,0,47.39,75,119.9,120,149.9,150,200):
            m.vars['RUS_first_five_year_plan_score']=score;m.call('RUS_np_refresh')
            expected=-.2+min(150,max(0,score))/150*.25
            self.assertAlmostEqual(m.states[s][P+'rural_build_speed'],expected)
            self.assertAlmostEqual(m.states[s][P+'rural_slots'],-.15+min(150,max(0,score))/150*.175)
            self.assertGreaterEqual(expected,last);last=expected
            mods=m.state_mods[s]&{'RUS_np_rural_infrastructure','RUS_np_rural_infrastructure_improved'}
            self.assertEqual(len(mods),1)
        # Building up a registered rural state cannot erase the modifier.
        m.states[s]['infrastructure']=5;m.states[s]['industrial_complex']=10
        m.vars['RUS_first_five_year_plan_score']=50;m.call('RUS_np_refresh')
        self.assertAlmostEqual(m.states[s][P+'rural_build_speed'],-.2+50/150*.25+.1)
        # Same score/date does not scan the state list again.
        m.states[s][P+'rural_build_speed']=99;m.call('RUS_np_refresh_rural')
        self.assertEqual(m.states[s][P+'rural_build_speed'],99)
        m.vars['global.num_days']+=30;m.call('RUS_np_refresh_rural')
        self.assertNotEqual(m.states[s][P+'rural_build_speed'],99)

    def test_rural_penalty_exists_on_startup_without_opening_plan_account(self):
        m=Model();m.context=False;s=next(s for s in m.states if s not in (219,195,217))
        m.states[s].update(category='two',infrastructure=1,industrial_complex=0,arms_factory=0)
        m.call('RUS_np_initialize_rural')
        self.assertAlmostEqual(m.states[s][P+'rural_build_speed'],-.2)
        self.assertAlmostEqual(m.states[s][P+'rural_slots'],-.15)
        self.assertIn('RUS_np_rural_infrastructure',m.state_mods[s])
        self.assertNotIn(P+'initialized',m.flags);self.assertNotIn(P+'available',m.vars)
        m.vars['RUS_first_five_year_plan_score']=150;m.call('RUS_np_refresh_rural')
        self.assertAlmostEqual(m.states[s][P+'rural_build_speed'],.05)
        self.assertAlmostEqual(m.states[s][P+'rural_slots'],.025)
        self.assertNotIn(P+'initialized',m.flags)
        hooks=load(ROOT/'common/on_actions/RUS_national_plan_on_actions.txt')[0]
        self.assertIn('RUS_np_initialize_rural',hooks.one('on_startup').raw())

    def test_rural_startup_explicit_russia_and_real_screenshot_states(self):
        import subprocess
        before=parse(subprocess.check_output(['git','show','338eb16:common/scripted_triggers/RUS_national_plan_triggers.txt']).decode('utf8'))
        old=next(n for n in before if n.k=='RUS_np_rural_candidate')
        m=Model();m.context=False;m.trigger_root='GER';m.ai=True
        for sid,filename in ((213,'213 - Murmansk.txt'),(237,'237 - Elista.txt')):
            state=load(ROOT.parent/'1521695605/history/states'/filename)[0];h=state.one('history');buildings=h.one('buildings')
            self.assertEqual(h.value('owner'),'RUS')
            m.states[sid]=dict(owned=True,controlled=True,core=True,category=state.value('state_category'),
                infrastructure=int(buildings.value('infrastructure','0')),
                industrial_complex=int(buildings.value('industrial_complex','0')),arms_factory=int(buildings.value('arms_factory','0')))
            m.state_flags[sid]=set();m.state_mods[sid]=set()
            scope,variables=m.scope,m.vars;m.scope=sid;m.vars=m.states[sid]
            self.assertFalse(m.check(old),'old relative ROOT must expose the scope dependency')
            self.assertTrue(m.check(TR['RUS_np_rural_candidate']))
            m.scope,m.vars=scope,variables
        m.call('RUS_np_initialize_rural')
        for sid in (213,237):
            self.assertAlmostEqual(m.states[sid][P+'rural_build_speed'],-.2)
            self.assertAlmostEqual(m.states[sid][P+'rural_slots'],-.15)
            self.assertIn('RUS_np_rural_infrastructure',m.state_mods[sid])
        self.assertNotIn(P+'initialized',m.flags)
        dm=load(ROOT/DM);rural=next(n for n in dm if n.k=='RUS_np_rural_infrastructure')
        owner=rural.one('enable').one('owner');self.assertTrue(m.check(owner))
        m.ai=False;self.assertTrue(m.check(owner))

    def test_level_five_infrastructure_adds_ten_points_and_never_stacks(self):
        m=Model();m.context=False;s=next(s for s in m.states if s not in (219,195,217))
        m.states[s].update(category='two',infrastructure=1,industrial_complex=0,arms_factory=0)
        m.call('RUS_np_initialize_rural')
        m.states[s]['infrastructure']=5;m.vars['global.num_days']+=1;m.call('RUS_np_rural_daily')
        self.assertAlmostEqual(m.states[s][P+'rural_build_speed'],-.1)
        self.assertAlmostEqual(m.states[s][P+'rural_slots'],-.15)
        for _ in range(3):m.call('RUS_np_rural_daily')
        self.assertAlmostEqual(m.states[s][P+'rural_build_speed'],-.1)
        m.states[s]['infrastructure']=4;m.vars['global.num_days']+=1;m.call('RUS_np_rural_daily')
        self.assertAlmostEqual(m.states[s][P+'rural_build_speed'],-.2)
        m.states[s]['infrastructure']=5;m.vars['global.num_days']+=1;m.call('RUS_np_rural_daily')
        m.vars['RUS_first_five_year_plan_score']=150;m.call('RUS_np_refresh_rural')
        self.assertAlmostEqual(m.states[s][P+'rural_build_speed'],.15)
        self.assertAlmostEqual(m.states[s][P+'rural_slots'],.025)

    def test_rural_eligibility_excludes_cities_industry_noncores_and_enemy_land(self):
        m=Model();s=next(s for s in m.states if s not in (219,195,217))
        cases=[({},True),({'category':'six'},False),({'core':False},False),({'controlled':False},False),
               ({'industrial_complex':3},False),({'arms_factory':3},False),({'infrastructure':3},False)]
        for change,expected in cases:
            m.states[s].update(owned=True,controlled=True,core=True,category='two',infrastructure=1,industrial_complex=0,arms_factory=0)
            m.states[s].update(change);m.scope=s;m.vars=m.states[s]
            self.assertEqual(m.check(TR['RUS_np_rural_candidate']),expected,change)
        for sid in (219,195,217):
            m.scope=sid;m.vars=m.states[sid];m.vars.update(owned=True,core=True,category='two',infrastructure=1,industrial_complex=0,arms_factory=0)
            self.assertFalse(m.check(TR['RUS_np_rural_candidate']))
    def test_catalogue_and_preserved_spirit_score(self):
        self.assertEqual(len(PROJECTS),62);self.assertEqual(sum(p['legacy'] for p in PROJECTS),46)
        for path,digest in DATA['preserved'].items():self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),digest)
        # Every old native reward, including easy-mode branches and scoring,
        # occurs contiguously and unchanged in its managed completion handler.
        for p in PROJECTS:
            if not p['legacy']:continue
            expected=[n.norm() for n in parse(native_base(p))]
            self.assertTrue(any(isinstance(n.v,list) and any([x.norm() for x in n.v[i:i+len(expected)]]==expected for i in range(len(n.v)-len(expected)+1)) for n in walk([EFFECTS[var(p,'finish')]])),p['id'])
            self.assertEqual(NODES[p['id']].value('cost'),parse(p['original'])[0].value('cost'))
            self.assertFalse(any(n.k=='add_political_power' for n in walk(NODES[p['id']].one('cancel_effect').v)))
    def test_all_62_directly_visible_without_focus_and_classified(self):
        m=Model().initialize()
        for p in PROJECTS:
            n=NODES[p['id']];self.assertTrue(m.check(n.one('allowed')),p['id'])
            self.assertEqual([x.k for x in n.one('allowed').v],['original_tag'],'allowed is cached at game start')
            self.assertTrue(m.check(n.one('visible')),p['id'])
            m.vars[P+'filter']=p['region'];self.assertTrue(m.check(n.one('visible')))
            m.vars[P+'filter']=p['region']%6+1;self.assertFalse(m.check(n.one('visible')))
            m.vars[P+'filter']=0
    def test_one_time_projects_and_repeat_electrification_keep_original_scoring(self):
        p=next(p for p in PROJECTS if p['key']=='renovate_and_expand_moscow')
        m=Model().initialize();m.start(p);m.vars[var(p,'left')]=0;m.call(var(p,'finish'))
        self.assertFalse(m.check(TR['RUS_np_ready_'+p['key']]))
        self.assertFalse(m.check(NODES[p['id']].one('visible')))
        p=PROJECTS[0];m=Model().initialize();m.vars['RUS_np_rail_region_'+str(p['region'])]=2;m.start(p)
        m.vars[var(p,'left')]=0;m.call(var(p,'finish'));first=m.states[p['states'][0]].get('industrial_infrastructure',0)
        m.start(p);m.vars[var(p,'left')]=0;m.call(var(p,'finish'))
        self.assertEqual(m.legacy_rewards[p['key']],2)
        self.assertEqual(m.states[p['states'][0]].get('industrial_infrastructure',0),first)
    def test_population_and_local_development_never_inflate_national_manpower(self):
        p=next(p for p in PROJECTS if p['key']=='metro');m=Model().initialize();before=m.states[219]['state_population']
        m.start(p);m.vars[var(p,'left')]=0;m.call(var(p,'finish'))
        self.assertGreater(m.states[219]['state_population'],before);self.assertNotIn('state_population',m.country)
        m.scope=219;m.vars=m.states[219]
        from national_plan import develop
        for _ in range(10):m.run(parse(develop(219)))
        self.assertEqual(m.states[219]['RUS_np_development'],3)
        self.assertEqual(m.state_mods[219],{'RUS_np_region_3'})
    def test_every_project_settles_once_and_refunds_exactly(self):
        for p in PROJECTS:
            m=Model().initialize();before=m.vars[P+'available'];stock=m.stock;m.start(p)
            self.assertIn(var(p,'running'),m.flags,p['id'])
            self.assertEqual(m.stock,stock-p['trains']);self.assertEqual(m.vars[P+'frozen'],p['budget'])
            m.vars[var(p,'left')]=0;m.call(var(p,'finish'))
            self.assertAlmostEqual(m.vars[P+'available'],before-p['budget']*.8)
            self.assertAlmostEqual(m.vars[P+'spent'],p['budget']*.8);self.assertEqual(m.stock,stock+(10 if p.get('reward')=='wagons' else 0))
            self.assertEqual(m.vars[P+'frozen'],0);self.assertNotIn(var(p,'cost'),m.dynamic)
            snapshot=(m.vars[P+'available'],m.vars[P+'spent'],m.stock,dict(m.legacy_rewards))
            m.call(var(p,'finish'));m.call(var(p,'cancel'));self.assertEqual(snapshot,(m.vars[P+'available'],m.vars[P+'spent'],m.stock,m.legacy_rewards))
    def test_cancel_and_enemy_losses_conserve_budget_and_trains(self):
        p=PROJECTS[4]
        for progress in (0,.25,.8,1):
            for lost in (False,True):
                m=Model().initialize();before=m.vars[P+'available'];stock=m.stock;m.start(p)
                m.vars[var(p,'left')]=p['fallback']*(1-progress)
                if lost:m.states[p['states'][0]]['owned']=False
                if lost:m.call(var(p,'cancel'))
                else:
                    n=NODES[var(p,'terminate')]
                    self.assertTrue(m.check(n.one('visible')))
                    m.run(n.one('complete_effect').v)
                    self.assertNotIn(p['id'],m.timers)
                self.assertAlmostEqual(m.vars[P+'available']+m.vars[P+'spent'],before)
                self.assertEqual(m.vars[P+'frozen'],0)
                self.assertEqual(m.stock,stock-(math.ceil(p['trains']*.25) if lost else 0))
                self.assertFalse(m.legacy_rewards)
    def test_account_opens_on_click_with_full_current_year_grant(self):
        m=Model()
        m.call('RUS_np_daily')
        self.assertNotIn('RUS_np_initialized',m.flags)
        self.assertNotIn(P+'available',m.vars)
        # Open late in a year: grant is still the full annual 10*C*E.
        m.vars['global.num_days']=364
        m.run(NODES['RUS_np_open_account'].one('complete_effect').v)
        self.assertIn('RUS_np_initialized',m.flags)
        self.assertEqual(m.vars[P+'year'],1936)
        self.assertAlmostEqual(m.vars[P+'initial_grant'],500)
        self.assertAlmostEqual(m.vars[P+'available'],500)
        self.assertAlmostEqual(m.vars[P+'income'],1)
        self.assertEqual(m.vars[P+'free_slots'],7)
        m.call('RUS_np_initialize');m.call('RUS_np_daily')
        self.assertEqual(m.vars[P+'available'],500)
        m.vars['global.num_days']+=1;m.call('RUS_np_daily')
        self.assertEqual(m.vars[P+'available'],501)
        m.call('RUS_np_daily');self.assertEqual(m.vars[P+'available'],501)
        m.vars['year']=1937;m.vars['global.num_days']+=1;m.call('RUS_np_daily')
        self.assertEqual(m.vars[P+'available'],1002)
        m.call('RUS_np_initialize');m.call('RUS_np_daily')
        self.assertEqual(m.vars[P+'available'],1002)

    def test_seven_slots_and_original_resource_formula(self):
        for civ,basic,higher in ((0,0,0),(20,32,7),(50,50,50),(200,100,100)):
            m=Model();m.vars.update({'num_of_available_civilian_factories':civ,
                'RUS_basic_education_level':basic,'RUS_higher_education_level':higher})
            m.initialize();eff=.75+.005*(.6*basic+.4*higher)
            self.assertAlmostEqual(m.vars[P+'available'],10*civ*eff)
            self.assertAlmostEqual(m.vars[P+'income'],.02*civ*eff)
            self.assertEqual(m.vars[P+'slots'],7)
            self.assertEqual(m.vars[P+'free_slots'],7)
            # Recount active records; a capacity refresh never stops an existing job.
            for p in PROJECTS[:7]:m.flags.add(var(p,'running'))
            m.call('RUS_np_refresh')
            self.assertEqual(m.vars[P+'active'],7)
            self.assertEqual(m.vars[P+'free_slots'],0)
            self.assertFalse(m.check(TR['RUS_np_ready_'+PROJECTS[8]['key']]))
            m.flags.add(var(PROJECTS[7],'running'));m.call('RUS_np_refresh')
            self.assertEqual(m.vars[P+'active'],8)
            self.assertEqual(m.vars[P+'free_slots'],0)

    def test_category_dispatch_has_one_owner_and_live_resource_header(self):
        outputs=render()
        path='common/scripted_localisation/RUS_stalin_five_year_plan_scripted_loc.txt'
        desc=next(n for n in parse(outputs[path]) if n.value('name')=='RUSGetFirstFiveYearPlanIndustrialProjectsDesc')
        first=desc.children('text')[0]
        self.assertEqual(first.value('localization_key'),'RUS_np_header')
        self.assertIn('RUS_np_context = yes',first.raw())
        key='RUS_first_five_year_plan_industrial_projects_desc'
        for lang in ('simp_chinese','english','russian'):
            loc=outputs[f'localisation/replace/RUS_stalin_five_year_plan_replace_l_{lang}.yml']
            self.assertIn(key+': "[ROOT.RUSGetFirstFiveYearPlanIndustrialProjectsDesc]"',loc)
            self.assertIn(key+'_normal: ""',loc)
        self.assertNotIn(key+':',outputs['localisation/replace/RUS_national_plan_category_l_simp_chinese.yml'])
        loc=outputs['localisation/simp_chinese/RUS_national_plan_l_simp_chinese.yml']
        header=next(line for line in loc.splitlines() if 'RUS_np_header:0' in line)
        for suffix in ('available','frozen','spent','initial_grant','grant','income','active','free_slots','trains','rail_display'):
            self.assertIn('[?RUS_np_'+suffix+'|',header)

    def test_income_and_annual_grant_only_once_and_capacity_reduction_no_pause(self):
        m=Model().initialize();m.call('RUS_np_daily');before=m.vars[P+'available'];m.call('RUS_np_daily');self.assertEqual(m.vars[P+'available'],before)
        m.vars['year']=1937;m.vars['global.num_days']+=1;m.call('RUS_np_daily')
        self.assertAlmostEqual(m.vars[P+'available']-before,m.vars[P+'grant']+m.vars[P+'income'])
        p=PROJECTS[4];m.start(p);left=m.vars[var(p,'left')]
        m.vars['num_of_available_civilian_factories']=0;m.vars[P+'available']=0;m.advance(p)
        self.assertLess(m.vars[var(p,'left')],left);self.assertIn(var(p,'running'),m.flags)
    def test_variable_heat_native_timer_and_both_engine_orders(self):
        p=next(p for p in PROJECTS if p['key']=='bearing')
        for order in ('before','after'):
            m=Model().initialize();m.vars['RUS_education_enthusiasm']=0;m.call('RUS_np_refresh');m.start(p)
            m.advance(p,order);cold=m.timers[p['id']]
            m.vars['RUS_education_enthusiasm']=100;m.advance(p,order)
            self.assertLess(m.timers[p['id']],cold)
            hot=m.timers[p['id']]
            m.vars['RUS_education_enthusiasm']=0;m.advance(p,order);self.assertGreater(m.timers[p['id']],hot)
            for _ in range(p['fallback']*2+4):
                m.advance(p,order)
                if var(p,'completed') in m.flags:break
            self.assertIn(var(p,'completed'),m.flags);self.assertNotIn(var(p,'running'),m.flags)
    def test_last_day_goal_latches_and_previews_never_award(self):
        p=next(p for p in PROJECTS if p['key']=='bearing');m=Model().initialize();m.start(p)
        self.assertNotIn(var(p,'goal_1'),m.flags)
        m.states[219]['infrastructure']=3;m.call(var(p,'goals'));self.assertIn(var(p,'goal_1'),m.flags)
        m.states[219]['infrastructure']=1;basic=m.vars['RUS_basic_education_level'];m.vars[var(p,'left')]=0
        m.run(NODES[p['id']].one('remove_effect').v)
        self.assertEqual(m.vars['RUS_basic_education_level'],basic+1)
        m.run(NODES[p['id']].one('remove_effect').v);self.assertEqual(m.vars['RUS_basic_education_level'],basic+1)
        # A goal first reached on the final callback is also credited.
        m=Model().initialize();m.start(p);m.states[219]['infrastructure']=3;m.vars[var(p,'left')]=0;m.call(var(p,'finish'))
        self.assertEqual(m.vars['RUS_basic_education_level'],51)
    def test_five_education_and_two_land_score_rewards(self):
        edu=[p['key'] for p in PROJECTS if any('RUS_np_award_education = yes' in x[2] for x in goals(p))]
        land=[p['key'] for p in PROJECTS if any('RUS_np_award_land_score = yes' in x[2] for x in goals(p))]
        self.assertEqual(set(edu),{'bearing','uvz','modernisation_of_AMO','uralmash','moscow_rural'});self.assertEqual(set(land),{'rostselmash','tsaritsyn_rural'})

    def test_extra_construction_resource_goals_settle_once_only_on_completion(self):
        for key in ('moscow_logistics','leningrad_logistics','tsaritsyn_logistics'):
            p=next(p for p in PROJECTS if p['key']==key)
            for cancel in (False,True):
                m=Model().initialize();m.start(p);s=p['states'][0]
                m.call(var(p,'goals'));self.assertNotIn(var(p,'goal_3'),m.flags)
                m.states[s]['infrastructure']=3;m.vars[P+'rail_region_'+str(p['region'])]=2
                m.call(var(p,'goals'));self.assertIn(var(p,'goal_3'),m.flags)
                m.vars[var(p,'left')]=0
                if cancel:m.call(var(p,'cancel'))
                m.call(var(p,'finish'));m.call(var(p,'finish'))
                self.assertEqual(m.vars.get(P+'bonus_resources',0),0 if cancel else 15)

    def test_extra_strategic_resources_match_existing_deposit_and_settle_once(self):
        from national_plan_catalog import EXTRA_STRATEGIC_PROJECTS
        for key,(resource,amount,_) in EXTRA_STRATEGIC_PROJECTS.items():
            p=next(p for p in PROJECTS if p['key']==key)
            self.assertRegex(p['original'],r'type\s*=\s*'+resource+r'\b')
            for cancel in (False,True):
                m=Model().initialize();s=p['states'][0];field='resource@'+resource
                m.states[s][field]=8;m.start(p)
                m.call(var(p,'goals'));self.assertNotIn(var(p,'goal_3'),m.flags)
                m.states[s]['infrastructure']=3;m.call(var(p,'goals'))
                self.assertIn(var(p,'goal_3'),m.flags)
                m.vars[var(p,'left')]=0
                if cancel:m.call(var(p,'cancel'))
                m.call(var(p,'finish'));m.call(var(p,'finish'))
                self.assertEqual(m.states[s][field],8 if cancel else 8+4+amount)

    def test_mio_size_rewards_once_deferred_and_transferred_to_merged_bureau(self):
        definitions={n.k for path in (ROOT/'common/military_industrial_organization/organizations').glob('RUS*.txt') for n in load(path)}
        for row in MIO_TARGETS.values():
            self.assertIn(row[0],definitions)
            if row[2]:self.assertIn(row[2],definitions)
        self.assertTrue(set(CONSORTIUM_MIOS)<=definitions)
        for project,(key,index) in MIO_REWARDS.items():
            if key=='consortium':continue
            p=next(p for p in PROJECTS if p['key']==project)
            primary,merged,successor,_=MIO_TARGETS[key]
            m=Model().initialize();m.states[p['states'][0]]['infrastructure']=3;m.start(p)
            m.vars[var(p,'left')]=0;m.call(var(p,'finish'))
            self.assertEqual(m.mios[primary]['size'],1)
            m.call(var(p,'finish'));m.call(P+'claim_mio_'+key)
            self.assertEqual(m.mios[primary]['size'],1)
            # An unavailable MIO retains one credit instead of losing rewards.
            m=Model().initialize();m.mios[primary]['available']=False
            m.call(P+'award_mio_'+key);self.assertEqual(m.vars[P+'mio_'+key+'_credit'],1)
            if merged:m.flags.add(merged);m.focuses.add('RUS_future_foreign_030');target=successor
            else:m.mios[primary]['available']=True;target=primary
            m.run(NODES[P+'redeem_mio_'+key].one('complete_effect').v)
            self.assertEqual(m.mios[target]['size'],1);self.assertEqual(m.vars[P+'mio_'+key+'_credit'],0)
            m.call(P+'claim_mio_'+key);self.assertEqual(m.mios[target]['size'],1)
        m=Model();m.aat=False;m.call(P+'award_mio_amo')
        self.assertEqual(m.mios[MIO_TARGETS['amo'][0]]['size'],0)
        self.assertEqual(m.vars.get(P+'mio_amo_credit',0),0)

    def test_postwar_bureaus_never_preview_or_receive_rewards_before_unlock(self):
        for key,(primary,merged,successor,_) in MIO_TARGETS.items():
            if not merged:continue
            preview=parse('\n'.join(mio_preview(key)));m=Model()
            m.run(preview);self.assertEqual(m.preview_mios,[primary])
            # A merge flag or an instantiated future MIO alone is insufficient.
            m.flags.add(merged);m.preview_mios=[];m.run(preview)
            self.assertEqual(m.preview_mios,[primary])
            m.mios[primary]['available']=False;m.call(P+'award_mio_'+key)
            self.assertEqual(m.mios[successor]['size'],0);self.assertEqual(m.vars[P+'mio_'+key+'_credit'],1)
            m.call(P+'claim_mio_'+key);self.assertEqual(m.mios[successor]['size'],0)
            m.focuses.add('RUS_future_foreign_030');m.mios[successor]['available']=False
            m.preview_mios=[];m.run(preview);self.assertEqual(m.preview_mios,[primary])
            m.call(P+'claim_mio_'+key);self.assertEqual(m.mios[successor]['size'],0)
            m.mios[successor]['available']=True;m.preview_mios=[];m.run(preview)
            self.assertEqual(m.preview_mios,[successor])
            m.call(P+'claim_mio_'+key);m.call(P+'claim_mio_'+key)
            self.assertEqual(m.mios[successor]['size'],1);self.assertEqual(m.vars[P+'mio_'+key+'_credit'],0)
        for project,(key,_) in MIO_REWARDS.items():
            if key=='consortium':continue
            p=next(p for p in PROJECTS if p['key']==project)
            for n in walk(NODES[p['id']].v):
                if n.k=='effect_tooltip':
                    self.assertFalse(any(x.k.startswith('RUS_np_award_mio_') for x in walk(n.v)),'MIO preview dispatch must not be forced inside effect_tooltip')
        for file in ('RUS_armour_design_bureau.txt','RUS_ordnance_design_bureau.txt'):
            n=load(ROOT/'common/military_industrial_organization/organizations'/file)[0]
            for field in ('visible','available'):self.assertIn('has_completed_focus = RUS_future_foreign_030',n.one(field).raw())

    def test_consortium_choice_waits_for_active_mio_and_opens_native_event_once(self):
        p=next(p for p in PROJECTS if p['key']=='volkhov');m=Model().initialize();m.start(p)
        m.vars[P+'rail_region_'+str(p['region'])]=2;m.call(var(p,'goals'))
        m.vars[var(p,'left')]=0;m.call(var(p,'finish'))
        self.assertEqual(m.vars[P+'mio_consortium_credit'],1);self.assertFalse(m.events)
        n=NODES[P+'redeem_mio_consortium'];self.assertFalse(m.check(n.one('available')))
        m.mios[CONSORTIUM_MIOS[0]]['assigned']=True;self.assertTrue(m.check(n.one('available')))
        m.run(n.one('complete_effect').v);m.run(n.one('complete_effect').v)
        self.assertEqual(m.events,['russia_events.440']);self.assertEqual(m.vars[P+'mio_consortium_credit'],0)
        event=next(n for n in load(ROOT/'events/RUS events (Russia).txt') if n.value('id')=='russia_events.440')
        self.assertEqual(len(event.children('option')),6)
        for option in event.children('option'):
            self.assertIn('is_mio_assigned_to_task = yes',option.raw())
            self.assertIn('add_mio_funds_gain_factor = 0.25',option.raw())

    def test_factory_goals_count_net_new_completed_buildings_and_offsite_only_once(self):
        for key,(index,kind,_,amount,offsite) in FACTORY_GOALS.items():
            p=next(p for p in PROJECTS if p['key']==key);s=p['states'][0]
            m=Model().initialize();m.states[s][kind]=5;m.start(p)
            self.assertEqual(m.vars[var(p,'factory_target')],5+amount)
            self.assertNotIn(var(p,'goal_'+str(index+1)),m.flags)
            m.vars[var(p,'left')]=0;m.call(var(p,'finish'))
            self.assertNotIn(var(p,'goal_'+str(index+1)),m.flags,'base factory rewards cannot satisfy their own goal')
            self.assertFalse(m.offsite)
            m=Model().initialize();m.states[s][kind]=5;m.start(p);m.states[s][kind]+=amount;m.call(var(p,'goals'))
            self.assertIn(var(p,'goal_'+str(index+1)),m.flags)
            m.states[s][kind]=5;m.vars[var(p,'left')]=0;m.call(var(p,'finish'));m.call(var(p,'finish'))
            self.assertEqual(m.offsite,{offsite:1} if offsite else {})
            m=Model().initialize();m.start(p);m.states[s][kind]=m.states[s].get(kind,0)+amount;m.call(var(p,'goals'));m.call(var(p,'cancel'));m.call(var(p,'finish'))
            self.assertFalse(m.offsite)
    def test_registered_rail_average_has_fixed_weight_and_connection_guard(self):
        m=Model().initialize();den=sum(c['weight'] for c in CORRIDORS)
        c=CORRIDORS[0];m.vars[P+'rail_'+c['key']]=2;m.call('RUS_np_refresh')
        self.assertAlmostEqual(m.vars[P+'rail_average'],2*c['weight']/den)
        m.rail=False;m.call('RUS_np_refresh');self.assertEqual(m.vars[P+'rail_average'],0)
    def test_agri_delivery_has_capacity_and_no_duplicate_daily_credit(self):
        m=Model().initialize();m.vars[P+'farm_rate']=6;m.vars[P+'farm_credit']=100
        m.call('RUS_np_agri_delivery');self.assertEqual(m.vars['RUS_nat_machine_stock'],1106)
        m.call('RUS_np_agri_delivery');self.assertEqual(m.vars['RUS_nat_machine_stock'],1106)
        m.vars['global.num_days']+=1;m.vars['RUS_nat_machine_stock']=6000;m.vars[P+'farm_credit']=100
        m.call('RUS_np_agri_delivery');self.assertEqual(m.vars['RUS_nat_machine_stock'],6000);self.assertEqual(m.vars[P+'farm_credit'],100)
    def test_composition_localisation_and_no_progress_ui(self):
        outputs=render();self.assertEqual(outputs,render())
        for rel,text in outputs.items():self.assertEqual((ROOT/rel).read_text(encoding='utf-8-sig'),text,rel)
        loc=outputs['localisation/simp_chinese/RUS_national_plan_l_simp_chinese.yml']
        self.assertNotIn('施工进度',loc);self.assertNotIn('预计剩余',loc);self.assertNotIn('暂停',loc)
        for p in PROJECTS:self.assertIn(var(p,'description')+':0',loc)
        self.assertEqual(len([p for p in PROJECTS if p['legacy']]),len([n for n in next(n for n in parse(restore(outputs[DEC])) if n.k==CAT).v if n.one('days_remove') and n.one('remove_effect')]))

if __name__=='__main__':unittest.main(verbosity=2)
