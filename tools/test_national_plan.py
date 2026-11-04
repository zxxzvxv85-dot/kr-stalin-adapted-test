"""Execute generated plan effects; native engine timing still needs HOI4 QA."""
import copy,hashlib,json,math,re,unittest
from pathlib import Path
from doudizhu_script_model import ScriptModel,load_effects
from hoi4_politics_blocks import parse,load
from national_plan_catalog import ROOT,DATA,PROJECTS,CORRIDORS
from national_plan import FX,DM,DEC,CAT,P,var,native_base,goals,restore
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
        super().__init__(copy.deepcopy(EFFECTS));self.context=True;self.stock=10000;self.scope=None
        self.country=self.vars;self.country.update({'global.num_days':100,'year':1936,'num_of_available_civilian_factories':50,
            'RUS_basic_education_level':50,'RUS_higher_education_level':50,'RUS_education_enthusiasm':50,
            'RUS_nat_machine_stock':1000,'RUS_nat_target':1000,'RUS_nat_installed':0,'RUS_first_five_year_plan_stage':3})
        self.flags.update({'RUS_education_system_active','RUS_nat_enabled','RUS_agri_management_unlocked'})
        self.states={s:{'owned':True,'infrastructure':1,'industrial_complex':1,'state_population':100000,'resource@steel':0} for p in PROJECTS for s in p['states']}
        self.states.update({s:{'owned':True,'infrastructure':1,'industrial_complex':1} for c in CORRIDORS for s in c['states'] if s not in self.states})
        self.dynamic=set();self.state_mods={s:set() for s in self.states};self.timers={};self.rail=True;self.legacy_rewards={}
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
        if isinstance(v,str) and v.startswith('days_decision_timeout@'):return self.timers.get(v.split('@')[1],0)
        if v in ('global.num_days','year'):return self.country[v]
        return super().number(v)
    def check(self,nodes):
        if hasattr(nodes,'v'):nodes=nodes.v
        for n in nodes:
            if n.k in TR:ok=self.check(TR[n.k])==(n.v=='yes')
            elif n.k in ('RUS_rc_stalin_phase','has_socialist_government'):ok=self.context==(n.v=='yes')
            elif n.k=='custom_trigger_tooltip':ok=self.check([x for x in n.v if x.k!='tooltip'])
            elif n.k=='has_equipment':ok=all(self.compare(self.stock,self.number(x.v),x.op) for x in n.v)
            elif n.k=='num_of_civilian_factories_available_for_projects':ok=self.compare(50,self.number(n.v),n.op)
            elif n.k.isdigit():
                oldscope,oldvars=self.scope,self.vars;self.scope=int(n.k);self.vars=self.states[self.scope]
                ok=self.check(n.v);self.scope,self.vars=oldscope,oldvars
            elif n.k in ('is_owned_and_controlled_by_ROOT_or_subject','is_owned_and_controlled_by'):ok=self.states[self.scope]['owned']
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
            'add_manpower','add_resource','build_railway','model_legacy_reward','RUS_education_refresh','RUS_agri_credit_score','RUS_nat_refresh'}
        for n in nodes:
            if n.k not in native and not n.k.isdigit():pending.append(n);continue
            if pending:super().run(pending);pending=[]
            if n.k.isdigit():
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
    def test_only_two_education_and_two_land_score_rewards(self):
        edu=[p['key'] for p in PROJECTS if any('RUS_np_award_education = yes' in x[2] for x in goals(p))]
        land=[p['key'] for p in PROJECTS if any('RUS_np_award_land_score = yes' in x[2] for x in goals(p))]
        self.assertEqual(edu,['bearing','uvz']);self.assertEqual(set(land),{'rostselmash','tsaritsyn_rural'})
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
