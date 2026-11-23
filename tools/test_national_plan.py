"""Execute generated plan effects; native engine timing still needs HOI4 QA."""
import copy,hashlib,json,math,re,unittest
from pathlib import Path
from doudizhu_script_model import ScriptModel,load_effects
from hoi4_politics_blocks import parse,load
from national_plan_catalog import ROOT,DATA,PROJECTS,CORRIDORS,MIO_TARGETS,MIO_REWARDS,CONSORTIUM_MIOS,FACTORY_GOALS
from national_plan import FX,DM,DEC,CAT,P,var,native_base,managed_base,project_score,goals,restore,mio_preview,SCORE_FILE,SCORE_HOOK,score_hook,base_pp,pp_price
import disordered_industry as industry
from national_plan_focuses import PROJECT_FOCUS,FOCUS_PROJECTS,FIVE_YEAR_PLAN_PROJECTS
from generate_provisional_industry_gui import render

EFFECTS=load_effects((ROOT/FX).read_text(encoding='utf8'))
EFFECTS.update(load_effects((ROOT/'common/scripted_effects/RUS_disordered_industry.txt').read_text(encoding='utf8')))
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
        self.trigger_root='RUS';self.ai=False;self.stalin_phase=True
        self.focuses.update(PROJECT_FOCUS.values());self.plan_active=False
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
            signature=[n.norm() for n in parse(managed_base(p))]
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
            elif n.k=='RUS_completed_focus_4_year_plan':ok=self.plan_active==(n.v=='yes')
            elif n.k=='has_dlc_aat':ok=self.aat==(n.v=='yes')
            elif n.k=='has_completed_focus':ok=n.v in self.focuses
            elif n.k=='has_military_industrial_organization':ok=n.v in self.mios
            elif n.k.startswith('mio:'):
                before=self.mio_scope;self.mio_scope=n.k.split(':')[1]
                ok=self.mio_scope in self.mios and self.check(n.v);self.mio_scope=before
            elif n.k in ('is_mio_available','is_mio_assigned_to_task'):
                ok=self.mios[self.mio_scope]['available' if n.k=='is_mio_available' else 'assigned']==(n.v=='yes')
            elif n.k=='RUS_rc_stalin_phase':ok=self.stalin_phase==(n.v=='yes')
            elif n.k=='has_socialist_government':ok=self.context==(n.v=='yes')
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
            'effect_tooltip','custom_effect_tooltip','force_update_dynamic_modifier','add_extra_state_shared_building_slots','add_building_construction','remove_ideas',
            'add_manpower','add_resource','build_railway','model_legacy_reward','RUS_education_refresh','RUS_agri_credit_score','RUS_nat_refresh','every_owned_state','set_state_flag','clr_state_flag','add_mio_size','country_event','add_offsite_building','add_ideas'}
        for n in nodes:
            if n.k not in native and not n.k.isdigit() and not n.k.startswith('mio:'):pending.append(n);continue
            if pending:super().run(pending);pending=[]
            if n.k.startswith('mio:'):
                before=self.mio_scope;self.mio_scope=n.k.split(':')[1];self.run(n.v);self.mio_scope=before
            elif n.k=='add_ideas':self.ideas.add(n.v)
            elif n.k=='remove_ideas':self.ideas.difference_update(x.k for x in n.v)
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
    def test_first_policy_locks_route_and_tenth_focus_sets_spirit(self):
        prefix = 'RUS_future_domestic_'
        focuses = {n.value('id'): n for n in load(ROOT/'common/national_focus/00_RUS_future_domestic_skeleton.txt')}
        first_choices = {'422': '169', '421': '166', '486': '166', '377': '163', '487': '163'}
        for first, winner in first_choices.items():
            m = Model()
            m.focuses.clear()
            m.ideas = {industry.OLD}
            m.context = False
            m.call(industry.REFRESH)
            self.assertEqual(m.ideas, {industry.OLD})
            m.context = True
            m.call(industry.REFRESH)
            self.assertEqual(m.ideas, {industry.PREFIX+'_0'})
            policies = [first] + [s for s in first_choices if s != first]
            for progress, suffix in enumerate(['424', '621', '420', '160', *policies], 1):
                key = prefix+suffix
                m.focuses.add(key)
                m.run([n for n in focuses[key].one('completion_reward').v if industry.CHOICE in n.raw()])
                m.call(industry.REFRESH)
                self.assertEqual(m.ideas, {f'{industry.PREFIX}_{progress}'})
                for route in industry.ROUTES:
                    node = focuses[prefix+route]
                    route_check = next(n for n in node.one('available').children('custom_trigger_tooltip')
                                       if n.one('check_variable'))
                    prerequisites = all(p.value('focus') in m.focuses for p in node.children('prerequisite'))
                    self.assertEqual(prerequisites and m.check([route_check]), progress == 9 and route == winner)
            m.focuses.add(prefix+winner)
            m.call(industry.REFRESH)
            m.call(industry.REFRESH)
            self.assertEqual(m.ideas, {f'{industry.PREFIX}_{industry.ROUTES[winner]}'})

    def test_federal_spirit_uses_focus_icon_as_soon_as_route_is_completed(self):
        m = Model()
        m.focuses = {'RUS_future_domestic_'+s for s in ('424', '621', '420', '421', '422', '486', '377', '487')}
        m.ideas = {industry.OLD}
        m.call(industry.REFRESH)
        self.assertEqual(m.ideas, {industry.PREFIX+'_8'})
        m.focuses.add(industry.FEDERAL_FOCUS)
        m.call(industry.REFRESH)
        intermediate = industry.DISCOUNT_IDEA+'_9'
        self.assertEqual(m.ideas, {intermediate})
        m.call(industry.REFRESH)
        self.assertEqual(m.ideas, {intermediate})
        m.focuses.add('RUS_future_domestic_160')
        m.call(industry.REFRESH)
        self.assertEqual(m.ideas, {industry.DISCOUNT_IDEA})

        spirits = load(ROOT/'common/ideas/RUS_disordered_industry.txt')[0].one('country').v
        by_name = {node.k: node for node in spirits}
        for tier in range(10):
            original = by_name[f'{industry.PREFIX}_{tier}']
            federal = by_name[f'{industry.DISCOUNT_IDEA}_{tier}']
            self.assertEqual(original.one('modifier').norm(), federal.one('modifier').norm())
            self.assertEqual(federal.value('picture'), industry.FEDERAL_PICTURE)
        self.assertEqual(by_name[industry.DISCOUNT_IDEA].value('picture'), industry.FEDERAL_PICTURE)
        sprite = load(ROOT/'interface/RUS_disordered_industry.gfx')[0].one('spriteType')
        self.assertEqual(sprite.value('texturefile').strip('"'), industry.FEDERAL_TEXTURE)
        self.assertTrue((ROOT/industry.FEDERAL_TEXTURE).is_file())

    def test_cooperative_spirit_keeps_route_icon_and_merges_producers_plan(self):
        m = Model()
        m.focuses = {'RUS_future_domestic_'+s for s in ('424', '621', '420', '421', '422', '486', '377', '487')}
        m.ideas = {industry.OLD}
        m.focuses.add(industry.COOPERATIVE_FOCUS)
        m.call(industry.REFRESH)
        intermediate = industry.COOPERATIVE_IDEA+'_9'
        self.assertEqual(m.ideas, {intermediate})
        m.focuses.add('RUS_future_domestic_160')
        m.call(industry.REFRESH)
        self.assertEqual(m.ideas, {industry.COOPERATIVE_IDEA})
        m.focuses.add(industry.PRODUCERS_PLAN_FOCUS)
        m.ideas.add(industry.PRODUCERS_PLAN_IDEA)
        for _ in range(2):
            m.call(industry.REFRESH)
            self.assertEqual(m.ideas, {industry.COOPERATIVE_PLAN_IDEA})
        m.flags.add('RUS_education_system_active')
        m.call(industry.MONTHLY_EDUCATION)
        self.assertEqual(m.vars['RUS_basic_education_level'], 50.5)
        self.assertEqual(m.vars['RUS_higher_education_level'], 50.5)

        ideas = load(ROOT/'common/ideas/RUS_disordered_industry.txt')[0].one('country')
        for key in (intermediate, industry.COOPERATIVE_IDEA, industry.COOPERATIVE_PLAN_IDEA):
            self.assertEqual(ideas.one(key).value('picture'), industry.COOPERATIVE_IDEA)
        modifiers = ideas.one(industry.COOPERATIVE_PLAN_IDEA).one('modifier')
        self.assertEqual(float(ideas.one(industry.COOPERATIVE_IDEA).one('modifier').value('consumer_goods_expected_value')), .05)
        self.assertEqual(float(modifiers.value('consumer_goods_expected_value')), .05)
        self.assertEqual(float(modifiers.value('stability_weekly')), .0025)
        self.assertEqual(float(modifiers.value('political_power_factor')), .05)
        self.assertEqual(modifiers.value('custom_modifier_tooltip'), industry.COOPERATIVE_PLAN_IDEA+'_effects_tt')
        scripted_loc = load(ROOT/'common/scripted_localisation/RUS_disordered_industry_loc.txt')
        for focus, policy in industry.COOPERATIVE_EFFECTS.items():
            loc = next(node for node in scripted_loc if node.value('name') == 'RUSIndustrialPolicy_'+policy)
            self.assertEqual(loc.one('text').one('trigger').value('has_completed_focus'), focus)
            self.assertEqual(loc.one('text').value('localization_key'), f'{industry.PREFIX}_{policy}_row_tt')
        localisation = (ROOT/'localisation/simp_chinese/RUS_disordered_industry_l_simp_chinese.yml').read_text(encoding='utf-8-sig')
        group = next(line for line in localisation.splitlines() if f'{industry.PREFIX}_reform_group_tt:0' in line)
        self.assertEqual(group.count('土改启用后'), 1)
        self.assertEqual(group.count('[RUSIndustrialPolicy_'), 3)
        self.assertNotIn(r'\n\n', localisation)
        sprites = load(ROOT/'interface/RUS_disordered_industry.gfx')[0].children('spriteType')
        sprite = next(s for s in sprites if s.value('name').strip('"') == 'GFX_idea_'+industry.COOPERATIVE_IDEA)
        self.assertEqual(sprite.value('texturefile').strip('"'), industry.COOPERATIVE_TEXTURE)
        self.assertTrue((ROOT/industry.COOPERATIVE_TEXTURE).is_file())

    def test_democratic_efficiency_requires_more_than_100_reform_points(self):
        focuses = load(ROOT/'common/national_focus/00_RUS_future_domestic_skeleton.txt')
        focus = next(n for n in focuses if n.value('id') == industry.DEMOCRATIC_EFFICIENCY_FOCUS)
        gate = next(n for n in focus.one('available').children('custom_trigger_tooltip')
                    if n.one('check_variable'))
        m = Model()
        for score, available in ((99, False), (100, False), (100.01, True)):
            m.vars['RUS_agri_display_score'] = score
            self.assertEqual(m.check([gate]), available)

    def test_federal_discount_changes_pp_and_reserves_discounted_budget(self):
        m = Model().initialize()
        p = next(p for p in PROJECTS if base_pp(p) == 'RUS_ic_cost_low')
        price, _ = pp_price(base_pp(p))
        m.vars['RUS_ic_cost_low'] = 25
        m.call('RUS_np_refresh_prices')
        self.assertEqual(m.vars[price], 25)
        m.vars[P+'available'] = p['budget'] * .8
        ready = TR['RUS_np_ready_'+p['key']]
        self.assertFalse(m.check(ready))
        m.ideas.add(industry.DISCOUNT_IDEA)
        m.call('RUS_np_refresh_prices')
        self.assertEqual(m.vars[price], 20)
        self.assertTrue(m.check(ready))
        m.call(var(p,'begin'))
        self.assertAlmostEqual(m.vars[var(p,'paid')], p['budget'] * .8)
        self.assertAlmostEqual(m.vars[P+'available'], 0)
        self.assertAlmostEqual(m.vars[P+'frozen'], p['budget'] * .8)
        m.ideas.clear()
        m.call(var(p,'cancel'))
        self.assertEqual(m.vars[P+'frozen'], 0)

    def test_research_discounts_running_time_and_only_future_project_fees(self):
        m = Model()
        m.focuses.remove(industry.RESEARCH_FOCUS)
        m.vars['num_researched_technologies'] = 80
        m.initialize()
        self.assertEqual(m.vars[industry.RESEARCH_FACTOR], 1)
        m.focuses.add(industry.RESEARCH_FOCUS)
        m.call('RUS_np_refresh')
        self.assertAlmostEqual(m.vars[industry.RESEARCH_FACTOR], .84)

        project = next(p for p in PROJECTS if base_pp(p) == 'RUS_ic_cost_low')
        days = m.vars[var(project, 'initial_days')]
        m.start(project)
        paid = m.vars[var(project, 'paid')]
        m.vars['num_researched_technologies'] = 100
        m.ideas.add(industry.DISCOUNT_IDEA)
        m.call('RUS_np_refresh')
        self.assertAlmostEqual(m.vars[industry.RESEARCH_FACTOR], .8)
        self.assertGreater(m.vars[P+'speed'], 1)
        self.assertLess(m.vars[var(project, 'initial_days')], days)
        self.assertEqual(m.vars[var(project, 'paid')], paid)
        self.assertAlmostEqual(m.vars[var(project, 'budget_current')], project['budget'] * .8 * .8)
        remaining = m.vars[var(project, 'left')]
        m.vars['global.num_days'] += 1
        m.call(var(project, 'tick'))
        self.assertAlmostEqual(remaining - m.vars[var(project, 'left')], 1 / .8)
        m.call(var(project, 'cancel'))
        m.start(project)
        self.assertAlmostEqual(m.vars[var(project, 'paid')], project['budget'] * .8 * .8)

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
        for path,digest in DATA['preserved'].items():
            raw=(ROOT/path).read_bytes()
            if path==SCORE_FILE:
                # Exactly one owned initialization call; all original values,
                # mission logic and original scoring helpers stay byte-identical.
                raw=raw.replace(SCORE_HOOK.encode(),b'')
            self.assertEqual(hashlib.sha256(raw).hexdigest(),digest)
        # Non-scoring native rewards, including easy-mode branches, remain a
        # contiguous subtree. Deferred scoring is exercised separately below.
        for p in PROJECTS:
            if not p['legacy']:continue
            expected=[n.norm() for n in parse(managed_base(p))]
            self.assertTrue(any(isinstance(n.v,list) and any([x.norm() for x in n.v[i:i+len(expected)]]==expected for i in range(len(n.v)-len(expected)+1)) for n in walk([EFFECTS[var(p,'finish')]])),p['id'])
            price, fallback = pp_price(base_pp(p))
            self.assertEqual(NODES[p['id']].value('cost'), f'{price}?{fallback}')
            self.assertFalse(any(n.k=='add_political_power' for n in walk(NODES[p['id']].one('cancel_effect').v)))
    def test_foundation_opens_account_independently_of_stalin(self):
        m = Model()
        focus = 'RUS_future_domestic_424'
        account = NODES['RUS_np_open_account']
        m.focuses.remove(focus)
        self.assertFalse(m.check(account.one('visible')))
        m.run(account.one('complete_effect').v)
        self.assertNotIn('RUS_np_initialized', m.flags)
        m.stalin_phase = False
        m.focuses.add(focus)
        self.assertTrue(m.check(account.one('visible')))
        m.run(account.one('complete_effect').v)
        self.assertIn('RUS_np_initialized', m.flags)
        self.assertFalse(m.check(account.one('visible')))

    def test_all_62_focus_unlocked_and_classified(self):
        m=Model().initialize()
        for p in PROJECTS:
            n=NODES[p['id']];self.assertTrue(m.check(n.one('allowed')),p['id'])
            self.assertEqual([x.k for x in n.one('allowed').v],['original_tag'],'allowed is cached at game start')
            m.focuses.remove(PROJECT_FOCUS[p['key']])
            self.assertFalse(m.check(n.one('visible')),p['id'])
            self.assertFalse(m.check(TR['RUS_np_ready_'+p['key']]),p['id'])
            m.call(var(p,'begin'));self.assertNotIn(var(p,'running'),m.flags)
            m.focuses.add(PROJECT_FOCUS[p['key']])
            self.assertTrue(m.check(n.one('visible')),p['id'])
            m.vars[P+'filter']=p['region'];self.assertTrue(m.check(n.one('visible')))
            m.vars[P+'filter']=p['region']%6+1;self.assertFalse(m.check(n.one('visible')))
            m.vars[P+'filter']=0

    def test_focus_previews_match_all_unlocks_without_old_project_activations(self):
        focus_files = ('00_RUS_future_domestic_skeleton.txt', '00_RUS_future_five_year_plan_skeleton.txt')
        focuses = {n.value('id'): n for path in focus_files
                   for n in load(ROOT/'common/national_focus'/path) if n.k=='shared_focus'}
        project_ids = {p['key']: p['id'] for p in PROJECTS}
        expected = set(project_ids.values())
        seen = []
        for suffix,keys in FOCUS_PROJECTS.items():
            node=focuses['RUS_future_domestic_'+suffix]
            unlocks = [n.v for n in node.one('completion_reward').v if n.k == 'unlock_decision_tooltip']
            if suffix == '424':
                self.assertEqual(unlocks.pop(0), 'RUS_np_open_account')
            self.assertEqual(unlocks, [project_ids[key] for key in keys], node.value('id'))
            seen.extend(unlocks)
            self.assertIsNotNone(node.one('available').one('custom_trigger_tooltip').one('always'))
            self.assertEqual(node.one('ai_will_do').value('factor'),'0')
            self.assertFalse(any(n.k=='activate_targeted_decision' for n in walk(node.one('completion_reward').v)))
        self.assertEqual(set(seen),expected);self.assertEqual(len(seen),62)
        self.assertIsNone(focuses['RUS_future_domestic_422'].one('completion_reward').one('unlock_decision_tooltip'))
        self.assertIsNone(focuses['RUS_future_domestic_455'].one('completion_reward').one('unlock_decision_tooltip'))

    def test_project_distribution_is_small_and_electricity_spans_later_focuses(self):
        self.assertEqual(sum(map(len, FIVE_YEAR_PLAN_PROJECTS.values())), 28)
        self.assertEqual(FOCUS_PROJECTS['160'], ('renovate_and_expand_moscow', 'renovate_and_expand_tsaritsyn',
                                                'renovate_and_expand_saint_petersburg', 'metro'))
        self.assertNotIn('420', FOCUS_PROJECTS)
        land={'187','189','197','199','202','203','207','407','408','409','411','455','457'}
        self.assertEqual(sum(len(keys) for suffix,keys in FOCUS_PROJECTS.items() if suffix in land),2)
        self.assertEqual(FOCUS_PROJECTS['486'], ('moscow_rural',))
        electric=[p for p in PROJECTS if p['kind']=='energy']
        self.assertEqual(len(electric),8)
        self.assertEqual(FOCUS_PROJECTS['804'], ('kamenev_all_russian_electrification', 'kashira', 'moscow_grid'))
        self.assertEqual(set(FOCUS_PROJECTS['804']) & set(FIVE_YEAR_PLAN_PROJECTS['723']), set())
        domestic = [n for n in load(ROOT/'common/national_focus/00_RUS_future_domestic_skeleton.txt') if n.k=='shared_focus']
        descendants = { 'RUS_future_domestic_160' }
        for _ in range(len(domestic)):
            expanded = descendants | {n.value('id') for n in domestic if any(
                p.v in descendants for group in n.children('prerequisite') for p in group.children('focus'))}
            if expanded == descendants:
                break
            descendants = expanded
        self.assertTrue(all(len(FOCUS_PROJECTS.get(key.rsplit('_',1)[-1], ())) <= 1
                            for key in descendants - {'RUS_future_domestic_160'}))
        # Each selected economic approach unlocks its own distinct projects.
        for branch in ({'169','176','625','626','182'}, {'166','629','179','631','177'}, {'163','181','634','636','183'}):
            keys={key for suffix in branch for key in FOCUS_PROJECTS[suffix]}
            self.assertEqual(len(keys),5)
            for key in keys:self.assertIn(PROJECT_FOCUS[key].split('_')[-1],branch)

    def test_electrification_focus_awards_one_tesla_size_even_if_unlocked_later(self):
        mio_id = 'RUS_tesla_electrical_organisation'
        focus = next(n for n in load(ROOT/'common/national_focus/00_RUS_future_domestic_skeleton.txt')
                     if n.value('id') == 'RUS_future_domestic_804')
        award = next(n for n in focus.one('completion_reward').v if n.k=='if')
        effect = 'RUS_tesla_apply_electrification_focus_reward'
        m = Model()
        m.effects[effect] = next(n for n in load(ROOT/'common/scripted_effects/RUS_tesla_effects.txt') if n.k==effect)
        m.mios[mio_id] = {'size': 0}
        m.aat = False
        m.run([award])
        self.assertFalse(m.flags & {'RUS_tesla_electrification_focus_reward_pending'})
        m.aat = True
        m.run([award])
        self.assertEqual(m.preview_mios, [mio_id])
        self.assertEqual(m.mios[mio_id]['size'], 0)
        m.flags.add('RUS_tesla_mio_unlocked')
        m.call(effect)
        m.call(effect)
        m.run([award])
        self.assertEqual(m.mios[mio_id]['size'], 1)
        self.assertNotIn('RUS_tesla_electrification_focus_reward_pending', m.flags)

    def score_model(self):
        m=Model().initialize()
        m.vars[P+'available']=100000
        m.effects.update(load_effects((ROOT/SCORE_FILE).read_text(encoding='utf8')))
        m.flags.add('RUS_first_five_year_plan_mission_started')
        return m

    def test_pre_plan_scores_transfer_on_initialization_once_and_refresh_original_spirit(self):
        m=self.score_model()
        for p in PROJECTS:
            m.start(p);m.call(var(p,'finish'))
        total=sum(project_score(p)+industry.LONG_RANGE_SCORE for p in PROJECTS)
        self.assertAlmostEqual(m.vars[P+'pending_plan_score'],total)
        self.assertNotIn('RUS_first_five_year_plan_score',m.vars)
        self.assertNotIn('RUS_first_five_year_plan',m.dynamic)
        m.flags.add('RUS_auto_kamenev_vst_left_path');m.plan_active=True
        m.call('RUS_stalin_ensure_first_five_year_plan')
        self.assertAlmostEqual(m.vars['RUS_first_five_year_plan_score'],total)
        self.assertEqual(m.vars[P+'pending_plan_score'],0)
        self.assertEqual(m.vars['RUS_first_five_year_plan_stage'],6)
        self.assertAlmostEqual(m.vars['RUS_first_five_year_plan_construction_speed'],.225)
        for _ in range(3):m.call('RUS_stalin_ensure_first_five_year_plan');m.call('RUS_np_flush_plan_score')
        self.assertAlmostEqual(m.vars['RUS_first_five_year_plan_score'],total)

    def test_active_plan_credit_and_repeat_electrification_count_exactly_once_per_completion(self):
        m=self.score_model();m.flags.add('RUS_auto_kamenev_vst_left_path');m.plan_active=True
        m.call('RUS_stalin_ensure_first_five_year_plan')
        for p in PROJECTS:
            before=m.vars['RUS_first_five_year_plan_score']
            m.start(p);m.call(var(p,'finish'));m.call(var(p,'finish'));m.call(var(p,'cancel'))
            self.assertAlmostEqual(m.vars['RUS_first_five_year_plan_score']-before,
                                   project_score(p)+industry.LONG_RANGE_SCORE)
        p=PROJECTS[0];before=m.vars['RUS_first_five_year_plan_score']
        m.start(p);m.call(var(p,'finish'))
        self.assertEqual(m.vars['RUS_first_five_year_plan_score']-before,1+industry.LONG_RANGE_SCORE)
        self.assertEqual(m.vars[P+'pending_plan_score'],0)

    def test_federal_accounting_requires_both_goals_and_normal_completion(self):
        p=next(p for p in PROJECTS if p['key']=='bearing')
        for policy, both, cancel, consumed in (
            (False,True,False,.8), (True,False,False,.8),
            (True,True,False,.5), (True,True,True,.8),
        ):
            m=Model().initialize()
            if not policy:
                m.focuses.remove(industry.ACCOUNTING_FOCUS)
            m.start(p)
            paid=m.vars[var(p,'paid')]
            m.flags.add(var(p,'goal_1'))
            if both:
                m.flags.add(var(p,'goal_2'))
            m.vars[var(p,'left')]=0
            m.call(var(p,'cancel' if cancel else 'finish'))
            self.assertAlmostEqual(m.vars[P+'spent'],paid*consumed)
            self.assertEqual(m.vars[P+'frozen'],0)

    def test_federal_coordination_only_speeds_local_industry_once(self):
        local=next(p for p in PROJECTS if p['key']=='lipetsk_metallurgical_plant')
        remote=next(p for p in PROJECTS if p['key']=='bodaybo_gold_mines')
        energy=next(p for p in PROJECTS if p['key']=='kashira')
        road=next(p for p in PROJECTS if p['key']=='improve_roads_in_central_russia')
        hub=next(p for p in PROJECTS if p['key']=='moscow_logistics')
        m=Model().initialize()
        base={p['key']:m.vars[var(p,'initial_days')] for p in (local,remote,energy)}
        m.start(local)
        m.flags.add(var(road,'completed'))
        m.flags.add(var(hub,'completed'))
        m.call('RUS_np_refresh')
        self.assertEqual(m.vars[P+'transport_duration_1'],.9)
        self.assertLess(m.vars[var(local,'initial_days')],base[local['key']])
        for p in (remote,energy):
            self.assertEqual(m.vars[var(p,'initial_days')],base[p['key']])
        remaining=m.vars[var(local,'left')]
        m.vars['global.num_days']+=1
        m.call(var(local,'tick'))
        self.assertAlmostEqual(remaining-m.vars[var(local,'left')],m.vars[P+'speed']/.9)
        m.focuses.remove(industry.COORDINATION_FOCUS)
        m.call('RUS_np_refresh')
        self.assertEqual(m.vars[P+'transport_duration_1'],1)

    def test_long_range_requires_distinct_finished_projects_and_only_boosts_future_score(self):
        m=self.score_model()
        m.focuses.remove(industry.LONG_RANGE_FOCUS)
        repeat=next(p for p in PROJECTS if p['key']=='kamenev_all_russian_electrification')
        for _ in range(2):
            m.start(repeat)
            m.call(var(repeat,'finish'))
        self.assertEqual(m.vars[P+'completed_projects'],1)
        self.assertEqual(m.vars[P+'pending_plan_score'],2*project_score(repeat))
        others=[p for p in PROJECTS if p!=repeat]
        m.flags.update(var(p,'completed') for p in others[:28])
        m.call('RUS_np_refresh')
        self.assertEqual(m.vars[P+'completed_projects'],29)
        self.assertFalse(m.check(TR['RUS_np_long_range_ready']))
        m.flags.add(var(others[28],'completed'))
        m.call('RUS_np_refresh')
        self.assertTrue(m.check(TR['RUS_np_long_range_ready']))
        m.focuses.add(industry.LONG_RANGE_FOCUS)
        before=m.vars[P+'pending_plan_score']
        m.start(repeat)
        m.call(var(repeat,'finish'))
        m.call(var(repeat,'finish'))
        self.assertEqual(m.vars[P+'pending_plan_score']-before,
                         project_score(repeat)+industry.LONG_RANGE_SCORE)
        self.assertEqual(m.vars[P+'completed_projects'],30)

    def test_cancel_and_enemy_termination_never_credit_pre_plan_score(self):
        for p in PROJECTS:
            for lost in (False,True):
                m=self.score_model();m.start(p)
                if lost:
                    m.states[p['states'][0]]['owned']=False;m.call(var(p,'finish'))
                else:m.call(var(p,'cancel'))
                self.assertEqual(m.vars.get(P+'pending_plan_score',0),0)
                self.assertNotIn('RUS_first_five_year_plan_score',m.vars)

    def test_score_hook_is_single_and_idempotent(self):
        text=(ROOT/SCORE_FILE).read_text(encoding='utf8')
        self.assertEqual(text.count(SCORE_HOOK),1)
        self.assertEqual(score_hook(text),text)
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
        self.assertEqual(first.value('localization_key'),'RUS_np_ui_blank')
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

    def test_unavailable_native_timeout_cannot_accumulate_thousands_of_days(self):
        # The supplied save has total=120, left=0 and still-running rural jobs.
        # Reproduce the failure with a zero timeout read: the old controller
        # leaves 7381 native days at day 120 instead of finishing the project.
        class ZeroTimeout(Model):
            def number(self,value):
                if isinstance(value,str) and value.startswith('days_decision_timeout@'):
                    return 0
                return super().number(value)
        rural=[p for p in PROJECTS if p['key'] in
               ('moscow_rural','leningrad_rural','tsaritsyn_rural')]
        for order in ('before','after'):
            m=ZeroTimeout().initialize()
            for p in rural:m.start(p)
            for day in range(122):
                m.advance(rural[0],order)
                for p in rural:
                    self.assertLessEqual(m.timers.get(p['id'],0),121)
            for p in rural:
                self.assertIn(var(p,'completed'),m.flags)
                self.assertNotIn(var(p,'running'),m.flags)
                self.assertEqual(m.vars[var(p,'paid')],0)
            self.assertEqual(m.vars[P+'frozen'],0)

    def test_timer_deadline_is_idempotent_with_continuously_changing_heat(self):
        p=next(p for p in PROJECTS if p['key']=='moscow_rural')
        for order in ('before','after'):
            m=Model().initialize();m.start(p)
            for day in range(245):
                m.vars['RUS_education_enthusiasm']=(day*17)%101
                m.advance(p,order)
                if var(p,'completed') in m.flags:break
                remaining=m.timers[p['id']]
                # Refreshing a tooltip/filter or re-entering the same controller
                # on this date cannot append a second copy of the correction.
                m.call(var(p,'timer'));m.call(var(p,'timer'))
                self.assertEqual(m.timers[p['id']],remaining)
                expected=m.vars[var(p,'left')]/m.vars[P+'speed']
                self.assertLessEqual(abs(remaining-expected),3)
            self.assertIn(var(p,'completed'),m.flags)

    def test_missing_deadline_does_not_add_the_absolute_calendar_date(self):
        p=next(p for p in PROJECTS if p['key']=='moscow_rural')
        m=Model().initialize();m.start(p)
        m.vars.pop(var(p,'deadline'))
        m.vars['global.num_days']=709145
        before=m.timers[p['id']]
        m.call(var(p,'timer'))
        self.assertEqual(m.timers[p['id']],before)
        self.assertNotIn('days_decision_timeout@',(ROOT/FX).read_text(encoding='utf8'))
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
    def test_labor_oversight_credits_agricultural_completion_once(self):
        p = next(p for p in PROJECTS if p['key']=='bobrik')
        for result, expected in (('finish', 2), ('cancel', 0)):
            m = Model().initialize()
            m.flags.add('RUS_maximalist_land_reform_in_progress')
            m.start(p)
            m.call(var(p,result))
            m.call(var(p,'finish'))
            self.assertEqual(m.vars.get('land_awarded',0), expected)

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
