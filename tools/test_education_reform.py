"""Execute generated education scripts. Engine rendering/timing still needs HOI4."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import unittest
from itertools import product
from doudizhu_script_model import ScriptModel,load_effects
from hoi4_politics_blocks import load,parse
from education_reform_content import ACTIVITIES,CONTROLS,BODY,POOL_CAPS,education_focuses,HEAT_ECONOMIC_MODIFIERS,EDUCATION_GAIN_CAPS
from generate_education_reform import ROOT,FX,DEC,DM,GUI,SGUI,GFX,VARS,pv,bv,active,remain,render_outputs,DESIGN,ART

EFFECTS=load_effects((ROOT/FX).read_text(encoding='utf-8-sig'))
DECISIONS={n.k:n for root in load(ROOT/DEC) for n in root.v}

class EducationModel(ScriptModel):
    def __init__(self):
        super().__init__(EFFECTS);self.ideas=set();self.dynamic=set();self.done=set();self.expiry={};self.day=0
        self.at_war=False;self.state_scope=None
        self.idea_expiry={}
        self.states={i:dict(owned=True,controlled=True,modifiers={}) for i in (195,219,202)}
    def check(self,nodes):
        if hasattr(nodes,'v'): nodes=nodes.v
        for n in nodes:
            if n.k=='has_idea': ok=n.v in self.ideas
            elif n.k=='has_completed_focus':ok=n.v in self.done
            elif n.k=='has_socialist_government':ok=n.v=='yes'
            elif n.k=='has_war':ok=self.at_war==(n.v=='yes')
            elif n.k in ('owns_state','controls_state'):
                ok=self.states.get(int(n.v),{}).get('owned' if n.k=='owns_state' else 'controlled',False)
            elif n.k=='has_dynamic_modifier':ok=n.value('modifier') in (self.states[self.state_scope]['modifiers'] if self.state_scope else self.dynamic)
            elif n.k in ('custom_trigger_tooltip','custom_override_tooltip'):ok=self.check([x for x in n.v if x.k!='tooltip'])
            else:ok=super().check([n])
            if not ok:return False
        return True
    def run(self,nodes):
        pending=[]
        native={'remove_ideas','add_ideas','add_dynamic_modifier','remove_dynamic_modifier','force_update_dynamic_modifier','effect_tooltip','custom_effect_tooltip','set_country_flag','add_timed_idea','RUS_nat_refresh'}
        for n in nodes:
            if n.k not in native and not n.k.isdigit():pending.append(n);continue
            if pending:super().run(pending);pending=[]
            if n.k=='RUS_nat_refresh':self.call(n.k)
            elif n.k.isdigit():
                before=self.state_scope;self.state_scope=int(n.k);self.run(n.v);self.state_scope=before
            elif n.k=='set_country_flag':
                if isinstance(n.v,str):self.flags.add(n.v)
                else:self.flags.add(n.value('flag'));self.expiry[n.value('flag')]=self.day+int(n.value('days'))
            elif n.k in ('remove_ideas','add_ideas'):
                self.ideas.discard(n.v) if n.k=='remove_ideas' else self.ideas.add(n.v)
            elif n.k=='add_dynamic_modifier':
                if self.state_scope:self.states[self.state_scope]['modifiers'][n.value('modifier')]=int(n.value('days'))
                else:self.dynamic.add(n.value('modifier'))
            elif n.k=='remove_dynamic_modifier':self.dynamic.discard(n.value('modifier'))
            elif n.k=='add_timed_idea':
                self.ideas.add(n.value('idea'));self.idea_expiry[n.value('idea')]=self.day+int(n.value('days'))
            # Tooltip blocks are display only; never execute their effects.
        if pending:super().run(pending)
    def call(self,name):
        if name=='RUS_nat_refresh':
            # Agriculture's own generator/tests validate recalculation. Here
            # record the handoff after checking the real stock/support writes.
            self.calls[name]=self.calls.get(name,0)+1;return
        super().call(name)
    def start(self,aid):
        d=DECISIONS['RUS_education_'+aid]
        if not self.check(d.one('visible')) or not self.check(d.one('available')):return False
        self.run(d.one('complete_effect').v);return True
    def end(self,aid,cancel=False):self.run(DECISIONS['RUS_education_'+aid].one('cancel_effect' if cancel else 'remove_effect').v)
    def advance(self,days,auto_finish=True):
        for _ in range(days):
            self.day+=1
            for idea,day in list(self.idea_expiry.items()):
                if day<=self.day:self.ideas.discard(idea);del self.idea_expiry[idea]
            for f,day in list(self.expiry.items()):
                if day<=self.day:self.flags.discard(f);del self.expiry[f]
            self.call('RUS_education_daily')
            if auto_finish:
                for a in ACTIVITIES+CONTROLS:
                    if active(a) in self.flags:
                        if self.check(DECISIONS['RUS_education_'+a['id']].one('cancel_trigger')):self.end(a['id'],True)
                        elif self.vars[remain(a)]<=0:self.end(a['id'])

def initialized():
    m=EducationModel();m.call('RUS_education_initialize');return m

def unlock_all(m):
    m.flags.update({'RUS_edu_culture_open','RUS_edu_technical_open','RUS_fr_basic_reform_completed'})
    m.done.update({'RUS_future_foreign_062','RUS_future_foreign_005'});m.at_war=True
    return m

class EducationTests(unittest.TestCase):
    def test_distinct_temporary_benefits_and_costs_keep_original_permanent_rewards(self):
        modifiers={k for a in ACTIVITIES for k in a['modifiers']}
        self.assertGreaterEqual(len(modifiers),30)
        lower_better={'political_power_cost','consumer_goods_factor','political_advisor_cost_factor',
            'resistance_growth_on_our_occupied_states','conversion_cost_civ_to_mil_factor','conversion_cost_mil_to_civ_factor',
            'production_lack_of_resource_penalty_factor','supply_consumption_factor','experience_loss_factor','training_time_army_factor'}
        for a in ACTIVITIES:
            values=[-v if k in lower_better else v for k,v in a['modifiers'].items()]
            self.assertTrue(any(v>0 for v in values),a['id']);self.assertTrue(any(v<0 for v in values),a['id'])
            actual={n.k:float(n.v) for n in DECISIONS['RUS_education_'+a['id']].one('modifier').v}
            self.assertEqual(actual,a['modifiers'])
            for cancel in (False,True):
                m=unlock_all(initialized());m.vars.update({VARS['basic']:40,'RUS_edu_category':a['category']})
                for mod,cap in POOL_CAPS.items():m.vars[pv(mod)]=cap/2
                before={mod:m.vars[pv(mod)] for mod in POOL_CAPS}
                self.assertTrue(m.start(a['id']))
                m.end(a['id'],cancel)
                expected=dict(before)
                if not cancel:
                    for mod,award in a['permanent_modifiers'].items():
                        cap=POOL_CAPS[mod];expected[mod]=min(max(before[mod]+award,min(0,cap)),max(0,cap))
                self.assertEqual(expected,{mod:m.vars[pv(mod)] for mod in POOL_CAPS})
                self.assertNotIn(active(a),m.flags)
                finish=DECISIONS['RUS_education_'+a['id']].one('remove_effect').raw()
                self.assertEqual('RUS_edu_result_' in finish,bool(a['permanent_modifiers']))
                self.assertNotIn('add_tech_bonus',finish)
            for mod,award in a['permanent_modifiers'].items():
                self.assertGreater(award*POOL_CAPS[mod],0)
        by_id={a['id']:a for a in ACTIVITIES}
        self.assertEqual(by_id['teachers']['permanent_modifiers'],{'political_power_cost':-.01})
        self.assertEqual(by_id['construction']['permanent_modifiers'],{'industrial_capacity_factory':.01})
        self.assertEqual(by_id['university']['permanent_modifiers'],{'research_speed_factor':.005})
        # Compare native decision values with the unscaled authoring snapshot:
        # each benefit is 2.5--5x, and every cost keeps its previous amount.
        for a in ACTIVITIES+CONTROLS:
            actual={n.k:float(n.v) for n in DECISIONS['RUS_education_'+a['id']].one('modifier').v}
            for mod,base in a['base_temporary_modifiers'].items():
                if (-base if mod in lower_better else base)>0:
                    self.assertGreaterEqual(actual[mod]/base,2.5-1e-10)
                    self.assertLessEqual(actual[mod]/base,5+1e-10)
                else:self.assertEqual(actual[mod],base)
        self.assertEqual(by_id['literacy']['modifiers'],{'research_speed_factor':.05,'production_speed_buildings_factor':-.05})
        for a in ACTIVITIES:
            construction=a['modifiers'].get('production_speed_buildings_factor',0)
            if construction<0:self.assertEqual(construction,-.075 if a['id']=='teachers' else -.05)
        for aid in ('pedagogy','ten_days','soviet_elections','harvest_battle'):
            self.assertEqual(by_id[aid]['modifiers']['industrial_capacity_factory'],-.05)
        for aid in ('schools','university','construction','advanced_theory','grain_delivery',
                    'socialist_industry','volunteer_enlistment','women_frontline'):
            self.assertEqual(by_id[aid]['modifiers']['consumer_goods_factor'],.05)
        for aid in ('cultural_enemies','protect_children','lenin_banner','public_property'):
            self.assertEqual(by_id[aid]['modifiers']['stability_factor'],-.05)
        for aid,mod in [('teachers','production_speed_buildings_factor'),
                        ('night_school','production_factory_efficiency_gain_factor'),
                        ('defend_leningrad','industrial_capacity_factory'),
                        ('defend_moscow','industrial_capacity_factory'),
                        ('complete_collectivisation','stability_factor')]:
            self.assertEqual(by_id[aid]['modifiers'][mod],-.075)
        self.assertEqual(by_id['agriculture']['modifiers']['consumer_goods_factor'],.005)
        self.assertEqual(by_id['literacy']['permanent_modifiers'],{'research_speed_factor':.002})
    def test_per_campaign_education_limits_include_route_advisor_and_heat_multipliers(self):
        for a in ACTIVITIES:
            for kind,cap in EDUCATION_GAIN_CAPS.items():self.assertLessEqual(a[kind],cap)
            for route in ('theory','practice'):
                m=unlock_all(initialized());m.flags.update({'RUS_edu_'+route,'RUS_edu_amateur','RUS_edu_future'})
                m.ideas.add('RUS_mikhail_kalinin_advisor')
                m.vars.update({VARS['basic']:40,VARS['higher']:7,VARS['heat']:55,'RUS_edu_category':a['category']})
                self.assertTrue(m.start(a['id']));before={k:m.vars[VARS[k]] for k in EDUCATION_GAIN_CAPS}
                for _ in range(a['days']):m.call('RUS_education_tick_'+a['id'])
                m.end(a['id'])
                for kind,cap in EDUCATION_GAIN_CAPS.items():
                    self.assertLessEqual(m.vars[VARS[kind]]-before[kind],cap+1e-9)
                saved={k:m.vars[VARS[k]] for k in EDUCATION_GAIN_CAPS};m.end(a['id'])
                self.assertEqual(saved,{k:m.vars[VARS[k]] for k in EDUCATION_GAIN_CAPS})
        # Smaller rewards still benefit from multipliers below the hard limit.
        m=unlock_all(initialized());m.flags.add('RUS_edu_practice')
        m.vars.update({VARS['heat']:55,'RUS_edu_category':2});self.assertTrue(m.start('construction'))
        m.end('construction',True)
        m.vars['RUS_edu_category']=3;self.assertTrue(m.start('mentoring'))
        before=m.vars[VARS['basic']];m.call('RUS_education_tick_mentoring')
        self.assertAlmostEqual(m.vars[VARS['basic']]-before,1.2/90)
    def test_dnieper_targeted_core_attack_is_30_days_and_not_a_state_reward(self):
        a=next(a for a in ACTIVITIES if a['id']=='dnieper_water');idea='RUS_edu_dnieper_offensive'
        self.assertNotIn('state_reward',a)
        definition=load(ROOT/'common/ideas/RUS stalin education reform ideas.txt')[0].one('country').one(idea)
        target=definition.one('targeted_modifier')
        self.assertEqual(target.value('tag'),'UKR');self.assertEqual(float(target.value('attack_bonus_against_cores')),.05)
        self.assertIsNone(definition.one('modifier'))
        m=unlock_all(initialized());m.vars['RUS_edu_category']=1
        m.states[202].update(owned=False,controlled=False)
        self.assertTrue(m.start(a['id']));self.assertNotIn(idea,m.ideas)
        m.end(a['id']);self.assertIn(idea,m.ideas);self.assertEqual(m.idea_expiry[idea],30)
        self.assertFalse(m.states[202]['modifiers'])
        m.advance(29);self.assertIn(idea,m.ideas)
        m.end(a['id']);self.assertEqual(m.idea_expiry[idea],30)
        m.advance(1);self.assertNotIn(idea,m.ideas)
        m.end(a['id']);self.assertNotIn(idea,m.ideas)
        m=unlock_all(initialized());m.vars['RUS_edu_category']=1
        self.assertTrue(m.start(a['id']));m.end(a['id'],True);self.assertNotIn(idea,m.ideas)
    def test_new_unlocks_direct_begin_guards_and_war_end_cancellation(self):
        m=initialized();m.vars['RUS_edu_category']=1
        self.assertFalse(m.start('motherland_calls'));m.call('RUS_education_begin_motherland_calls')
        self.assertEqual(m.vars['RUS_edu_active_count'],0)
        m.flags.add('RUS_fr_basic_reform_completed');self.assertTrue(m.start('motherland_calls'));m.end('motherland_calls',True)
        self.assertFalse(m.start('defend_leningrad'))
        m.done.add('RUS_future_foreign_062');self.assertFalse(m.start('defend_leningrad'))
        m.call('RUS_education_begin_defend_leningrad');self.assertEqual(m.vars['RUS_edu_active_count'],0)
        m.at_war=True;self.assertTrue(m.start('defend_leningrad'));m.at_war=False;m.advance(1)
        self.assertEqual(m.vars['RUS_edu_active_count'],0);self.assertEqual(m.vars['RUS_education_completed_activities'],0)
        self.assertFalse(m.states[195]['modifiers'])
        m.flags.add('RUS_edu_culture_open');m.vars['RUS_edu_category']=6
        self.assertFalse(m.start('long_live_peace'));m.done.add('RUS_future_foreign_005')
        self.assertTrue(m.start('long_live_peace'))
    def test_state_rewards_only_on_completion_with_current_ownership(self):
        for a in [a for a in ACTIVITIES if a.get('state_reward')]:
            for cancel,lost in ((False,False),(True,False),(False,True)):
                m=unlock_all(initialized());m.vars['RUS_edu_category']=a['category']
                self.assertTrue(m.start(a['id']));reward=a['state_reward'];state=reward['state']
                self.assertFalse(m.states[state]['modifiers'])
                if lost:m.states[state]['controlled']=False
                m.end(a['id'],cancel)
                expected={} if cancel or lost else {'RUS_edu_state_'+reward['preset']:reward['days']}
                self.assertEqual(m.states[state]['modifiers'],expected)
                m.end(a['id']);self.assertEqual(m.states[state]['modifiers'],expected)
                self.assertEqual(m.vars['RUS_education_completed_activities'],0 if cancel else 1)
        # Occupied or foreign territory never satisfies a city-targeted activity.
        m=unlock_all(initialized());m.vars['RUS_edu_category']=1;m.states[219]['owned']=False
        self.assertFalse(m.start('defend_moscow'));m.call('RUS_education_begin_defend_moscow')
        self.assertEqual(m.vars['RUS_edu_active_count'],0)
        from education_poster_expansion import STATE_REWARDS
        definitions={n.k:n for n in load(ROOT/DM)}
        for preset in STATE_REWARDS:
            enable=definitions['RUS_edu_state_'+preset].one('enable')
            self.assertEqual(enable.one('owner').value('original_tag'),'RUS')
            self.assertEqual(enable.one('controller').value('original_tag'),'RUS')
    def test_agricultural_handoffs_caps_shutdown_and_no_repeat_rewards(self):
        for enabled,closed,cancel in product((False,True),repeat=3):
            m=unlock_all(initialized());m.vars.update(RUS_edu_category=3,RUS_nat_wheat_stock=11)
            if enabled:m.flags.add('RUS_nat_enabled')
            if closed:m.flags.add('RUS_nat_system_closed')
            self.assertTrue(m.start('grain_delivery'));m.end('grain_delivery',cancel)
            granted=enabled and not closed and not cancel
            self.assertEqual(m.vars['RUS_nat_wheat_stock'],12 if granted else 11)
            self.assertEqual(m.calls.get('RUS_nat_refresh',0),int(granted))
            m.end('grain_delivery');self.assertEqual(m.calls.get('RUS_nat_refresh',0),int(granted))
        for aid,var,start,expected in [('harvest_battle','RUS_nat_rye_stock',10,12),
                ('agricultural_statistics','RUS_nat_technical_support',0,1),
                ('tractors_nurseries','RUS_nat_repair_support',0,.05),
                ('tractors_nurseries','RUS_nat_repair_support',.08,.08)]:
            m=unlock_all(initialized());m.flags.add('RUS_nat_enabled');m.vars.update(RUS_edu_category=2);m.vars[var]=start
            self.assertTrue(m.start(aid));m.end(aid);self.assertEqual(m.vars[var],expected)
    def test_decision_icons_match_topics_and_resolve_to_installed_sprites(self):
        game=ROOT.parents[3]/'common/Hearts of Iron IV'
        files=[game/'interface/decisions.gfx',ROOT.parent/'1521695605/interface/kaiserreich/decisions.gfx',ROOT/GFX]
        names={m for path in files for m in re.findall(r'name\s*=\s*"([^"]+)"',path.read_text(encoding='utf-8-sig'))}
        from generate_education_reform import decision_icon
        self.assertEqual(len(ACTIVITIES),51);self.assertEqual(len({a['id'] for a in ACTIVITIES}),51)
        for a in ACTIVITIES+CONTROLS:
            icon=DECISIONS['RUS_education_'+a['id']].value('icon')
            self.assertEqual(icon,decision_icon(a));self.assertIn(icon,names)
        self.assertGreaterEqual(len({decision_icon(a) for a in ACTIVITIES}),8)
    def test_selected_economic_bonuses_rise_with_heat_and_weekly_pressure_starts_above_75(self):
        for basic,higher in [(20,5),(46,7),(80,80),(100,100)]:
            m=initialized();m.vars.update({VARS['basic']:basic,VARS['higher']:higher})
            previous=None
            for heat in [0,10,32,55,70,75,75.01,80,90,100]:
                m.vars[VARS['heat']]=heat;m.call('RUS_education_refresh')
                values=[m.vars[bv(k)] for k in ['industrial_capacity_factory',*sorted(HEAT_ECONOMIC_MODIFIERS)]]
                if previous:
                    self.assertTrue(all(a>=b-1e-10 for a,b in zip(values,previous)))
                previous=values
                expected=-.01*(max(heat-75,0)/25)**2
                self.assertAlmostEqual(m.vars[bv('stability_weekly')],expected,places=10)
            if basic==100:
                self.assertAlmostEqual(m.vars[bv('production_factory_start_efficiency_factor')],.10)
                self.assertAlmostEqual(m.vars[bv('production_factory_efficiency_gain_factor')],.125)
                self.assertAlmostEqual(m.vars[bv('industrial_capacity_factory')],.05)
                # Research retains its separate heat penalty as industry rises.
                self.assertAlmostEqual(m.vars[bv('research_speed_factor')],-.05)
        primary=next(n for n in load(ROOT/DM) if n.k=='RUS_education_social_capacity')
        self.assertEqual(primary.value('stability_weekly'),bv('stability_weekly'))
        m.vars[VARS['heat']]=80;m.advance(1);self.assertEqual(m.vars['RUS_education_overheat_days'],1)
        m.vars[VARS['heat']]=75;m.advance(1);self.assertEqual(m.vars['RUS_education_overheat_days'],0)
    def test_category_filters_and_switching_preserve_running_activities(self):
        m=initialized();self.assertTrue(m.start('literacy'));m.advance(7)
        script=load(ROOT/SGUI)[0].v[0];clicks=script.one('effects');rules=script.one('triggers')
        before={k:v for k,v in m.vars.items() if not k.startswith('RUS_edu_catalog_') and k!='RUS_edu_category'}
        flags=set(m.flags)
        counts={c:sum(a['category']==c for a in ACTIVITIES) for c in range(1,7)}
        for category,count in counts.items():
            m.run(clicks.one(f'edu_category_{category}_click').v)
            self.assertEqual(m.vars['RUS_edu_catalog_count'],count)
            expected=[code for code,a in enumerate(ACTIVITIES,3) if a['category']==category and active(a) in m.flags]
            seen=[m.vars[f'RUS_edu_catalog_{i}_activity'] for i in range(1,4) if m.vars[f'RUS_edu_catalog_{i}_activity']]
            self.assertEqual(seen,expected)
            for a in ACTIVITIES:
                if m.check(DECISIONS['RUS_education_'+a['id']].one('visible')):
                    self.assertEqual(a['category'],category)
        m.run(clicks.one('edu_category_4_click').v)
        self.assertTrue(m.check(rules.one('activity_progress_1_visible')))
        self.assertEqual(m.vars['RUS_edu_catalog_1_days'],83)
        self.assertEqual(before,{k:m.vars[k] for k in before});self.assertEqual(flags,m.flags)
        m.run(clicks.one('edu_category_3_click').v)
        m.end('literacy');self.assertEqual(m.vars['RUS_edu_active_count'],0)
        self.assertTrue(all(m.vars[f'RUS_edu_slot_{i}']==0 for i in range(1,4)))
    def test_posters_require_started_campaign_and_clear_on_finish_or_cancel(self):
        clicks=load(ROOT/SGUI)[0].v[0].one('effects')
        for a in ACTIVITIES:
            for cancel in (False,True):
                m=unlock_all(initialized())
                m.vars[VARS['basic']]=60
                m.run(clicks.one(f'edu_category_{a["category"]}_click').v)
                self.assertTrue(all(m.vars[f'RUS_edu_catalog_{i}_frame']==2 for i in range(1,4)))
                self.assertTrue(m.start(a['id']))
                self.assertEqual(m.vars['RUS_edu_catalog_1_activity'],ACTIVITIES.index(a)+3)
                self.assertEqual(m.vars['RUS_edu_catalog_1_frame'],ACTIVITIES.index(a)+3)
                self.assertEqual(m.vars['RUS_edu_catalog_1_days'],a['days'])
                self.assertTrue(all(m.vars[f'RUS_edu_catalog_{i}_frame']==2 for i in (2,3)))
                m.end(a['id'],cancel)
                self.assertTrue(all(m.vars[f'RUS_edu_catalog_{i}_activity']==0 and m.vars[f'RUS_edu_catalog_{i}_frame']==2 for i in range(1,4)))
        # Two campaigns in the same category appear once each, even if another
        # running category occupies a gameplay slot between them.
        m=initialized();m.flags.update({'RUS_edu_culture_open','RUS_edu_technical_open'})
        m.vars[VARS['basic']]=60;m.call('RUS_education_refresh')
        for aid in ('literacy','mentoring','university'):
            a=next(a for a in ACTIVITIES if a['id']==aid)
            m.run(clicks.one(f'edu_category_{a["category"]}_click').v)
            self.assertTrue(m.start(aid))
        for category in (3,4,3,4):
            m.run(clicks.one(f'edu_category_{category}_click').v)
            displayed=[m.vars[f'RUS_edu_catalog_{i}_activity'] for i in range(1,4) if m.vars[f'RUS_edu_catalog_{i}_activity']]
            expected=[code for code,a in enumerate(ACTIVITIES,3) if a['category']==category and active(a) in m.flags]
            self.assertEqual(displayed,expected)
            self.assertEqual(m.vars['RUS_edu_active_count'],3)
    def test_exact_initial_and_optimal_maxima(self):
        m=initialized()
        self.assertEqual([m.vars[VARS[k]] for k in ('basic','higher','heat')],[46,7,32])
        # Lower curve endpoints remain independent of the new starting levels.
        m.vars.update({VARS['basic']:20,VARS['higher']:5,VARS['heat']:55});m.call('RUS_education_refresh')
        for mod,(lo,hi,w) in BODY.items():self.assertAlmostEqual(m.vars[bv(mod)],lo)
        m.vars.update({VARS['basic']:100,VARS['higher']:100,VARS['heat']:55});m.call('RUS_education_refresh')
        for mod,(lo,hi,w) in BODY.items():self.assertAlmostEqual(m.vars[bv(mod)],hi*.775 if mod in HEAT_ECONOMIC_MODIFIERS else (.05 if mod=='political_power_factor' else hi))
        for cap in POOL_CAPS:self.assertEqual(m.vars[pv(cap)],0)
        self.assertEqual(m.dynamic,{'RUS_education_social_capacity'})
    def test_one_education_spirit_includes_pooled_results_without_refresh_stacking(self):
        m=initialized();m.vars.update({VARS['basic']:100,VARS['higher']:100,VARS['heat']:55})
        for mod,cap in POOL_CAPS.items():m.vars[pv(mod)]=cap
        # Remove only the retired attachment, preserving all earned contributions.
        m.dynamic.add('RUS_education_permanent_results');m.call('RUS_education_refresh')
        expected={'research_speed_factor':.20,'industrial_capacity_factory':.1275,'stability_factor':.15,'political_power_factor':.15,'political_power_cost':-.20}
        for mod,value in expected.items():self.assertAlmostEqual(m.vars[bv(mod)],value)
        self.assertEqual(m.dynamic,{'RUS_education_social_capacity'})
        before={mod:m.vars[bv(mod)] for mod in expected}
        for _ in range(4):m.call('RUS_education_refresh')
        self.assertEqual(before,{mod:m.vars[bv(mod)] for mod in expected})
        primary=next(n for n in load(ROOT/DM) if n.k=='RUS_education_social_capacity')
        for mod in expected:self.assertEqual(primary.value(mod),bv(mod))
    def test_heat_curve_and_continuity(self):
        m=initialized()
        for t in [0,19.999,20,39.999,40,47.39,54.9999,55,55.0001,69.999,70,84.999,85,100]:
            m.vars[VARS['heat']]=t;m.call('RUS_education_refresh')
            d=(t-55)/(55 if t<=55 else 45);q=1/(1+4*d*d)
            self.assertAlmostEqual(m.vars['RUS_edu_quality'],q,places=10)
            self.assertAlmostEqual(m.vars[bv('stability_factor')],-.08*(1-q),places=10)
        for edge in (20,40,55,70,85):
            values=[]
            for t in (edge-.00001,edge+.00001):
                m.vars[VARS['heat']]=t;m.call('RUS_education_refresh');values.append(m.vars['RUS_edu_quality'])
            self.assertLess(abs(values[0]-values[1]),.000001)
        m.vars[VARS['heat']]=47.39;m.call('RUS_education_refresh')
        self.assertAlmostEqual(m.vars['RUS_edu_quality_percent'],92.886908,places=5)
        for t in (30,75):
            m.vars[VARS['heat']]=t;m.call('RUS_education_refresh')
            self.assertLess(m.vars['RUS_edu_quality'],.60)
            self.assertLess(m.vars[bv('stability_factor')],-.03)
    def test_daily_decay_no_education_decay(self):
        m=initialized();m.advance(30)
        self.assertAlmostEqual(m.vars[VARS['heat']],29)
        self.assertEqual(m.vars[VARS['basic']],46);self.assertEqual(m.vars[VARS['higher']],7)
    def test_entry_only_and_idempotence(self):
        m=EducationModel();m.call('RUS_education_reform_start');self.assertNotIn('RUS_education_system_active',m.flags)
        m.done.add('RUS_future_domestic_205');m.call('RUS_education_reform_start');m.advance(5)
        saved=m.vars.copy();m.call('RUS_education_initialize');self.assertEqual(saved,m.vars)
    def test_slots_kind_conflicts_and_unlocks(self):
        m=initialized();self.assertFalse(m.start('university'));self.assertFalse(m.start('technical'))
        self.assertTrue(m.start('literacy'));self.assertFalse(m.start('schools'))
        m.flags.update({'RUS_edu_culture_open','RUS_edu_technical_open'});m.call('RUS_education_refresh')
        self.assertTrue(m.start('reading'));self.assertTrue(m.start('technical'));self.assertFalse(m.start('science'))
        self.assertEqual(m.vars['RUS_edu_active_count'],3)
        m.end('reading',True);self.assertEqual(m.vars['RUS_edu_active_count'],2)
        self.assertFalse(m.start('reading'));self.assertEqual(m.vars['RUS_education_completed_activities'],0)
    def test_all_activity_lifecycles_and_original_permanent_rewards(self):
        for a in ACTIVITIES:
            with self.subTest(a=a['id']):
                m=unlock_all(initialized());m.vars.update({VARS['basic']:40,'RUS_edu_category':a['category']});m.call('RUS_education_refresh')
                self.assertTrue(m.start(a['id']));m.advance(a['days']);self.assertNotIn(active(a),m.flags)
                self.assertEqual(m.vars['RUS_education_completed_activities'],1);self.assertEqual(m.vars['RUS_edu_active_count'],0)
                self.assertTrue(all(m.vars[f'RUS_edu_slot_{i}']==0 for i in range(1,4)))
                for mod in POOL_CAPS:self.assertAlmostEqual(m.vars[pv(mod)],a['permanent_modifiers'].get(mod,0))
                saved={mod:m.vars[pv(mod)] for mod in POOL_CAPS};m.end(a['id']);self.assertEqual(saved,{mod:m.vars[pv(mod)] for mod in POOL_CAPS})
                self.assertEqual(m.vars['RUS_education_completed_activities'],1)
                self.assertFalse(any(x.startswith('RUS_edu_result_') for x in m.dynamic))
    def test_cancellation_and_final_daily_pulse(self):
        m=initialized();m.start('literacy');m.advance(45);self.assertGreater(m.vars[VARS['basic']],46)
        m.end('literacy',True);self.assertEqual(m.vars['RUS_education_completed_activities'],0);self.assertEqual(m.vars[pv('research_speed_factor')],0)
        m=initialized();m.start('literacy');m.advance(89);before=m.vars[VARS['basic']];m.end('literacy')
        self.assertGreater(m.vars[VARS['basic']],before);self.assertEqual(m.vars['RUS_education_completed_activities'],1)
    def test_controls_do_not_use_slots_or_count(self):
        for aid,start in [('listen',20),('restore_order',80)]:
            m=initialized();m.vars[VARS['heat']]=start;m.call('RUS_education_refresh');self.assertTrue(m.start(aid))
            self.assertEqual(m.vars['RUS_edu_active_count'],0);m.advance(30)
            self.assertEqual(m.vars['RUS_education_completed_activities'],0)
            self.assertAlmostEqual(m.vars[VARS['heat']],start-3+(10 if aid=='listen' else -12))
            self.assertAlmostEqual(m.vars[pv('political_power_cost')],-.005)
    def test_permanent_caps_and_all_decimal_inputs(self):
        m=initialized()
        for key in VARS.values():m.vars[key]=123.456
        for mod,cap in POOL_CAPS.items():m.vars[pv(mod)]=100 if cap>0 else -100
        m.call('RUS_education_refresh')
        for key in VARS.values():self.assertEqual(m.vars[key],100)
        for mod,cap in POOL_CAPS.items():self.assertEqual(m.vars[pv(mod)],cap)
        self.assertAlmostEqual(.15+m.vars[pv('research_speed_factor')],.20)
        for mod in POOL_CAPS:
            for a in ACTIVITIES+CONTROLS:
                name='RUS_edu_reward_'+a['id']+'_'+mod
                if name in m.vars:self.assertAlmostEqual(m.vars[name],0)
    def test_routes_multipliers_and_focus_gates(self):
        for theory,central,future in product([False,True],repeat=3):
            m=initialized();m.flags.update({'RUS_edu_theory' if theory else 'RUS_edu_practice','RUS_edu_central' if central else 'RUS_edu_amateur'})
            if future:m.flags.add('RUS_edu_future')
            m.call('RUS_education_refresh')
            self.assertAlmostEqual(m.vars['RUS_edu_basic_multiplier'],(1 if theory else 1.2)*(1 if central else 1.1))
            self.assertAlmostEqual(m.vars['RUS_edu_higher_multiplier'],(1.2 if theory else 1)*(1.2 if future else 1)*(1 if central else 1.1))
            self.assertAlmostEqual(m.vars['RUS_edu_cost_literacy'],20 if central else 25)
        for suffix,n,b,h in [('218',3,30,0),('224',6,45,15),('229',10,60,25)]:
            req=parse('\n'.join(education_focuses()[suffix]['available']))
            m=initialized();m.vars.update({'RUS_education_completed_activities':n,VARS['basic']:b,VARS['higher']:h})
            self.assertTrue(m.check(req))
            for key in ['RUS_education_completed_activities',VARS['basic']]+([VARS['higher']] if h else []):
                m.vars[key]-=.001;self.assertFalse(m.check(req));m.vars[key]+=.001
    def test_no_events_no_old_stacking(self):
        text=(ROOT/FX).read_text(encoding='utf-8-sig')+(ROOT/DEC).read_text(encoding='utf-8-sig')
        self.assertNotIn('country_event =',text);self.assertNotIn('repeat_limit',text)
        self.assertNotIn('RUS_education_recruitable_population_factor',text)
    def test_three_year_bounded_daily_campaign_schedule(self):
        m=initialized();m.flags.update({'RUS_edu_culture_open','RUS_edu_technical_open','RUS_edu_practice','RUS_edu_amateur','RUS_edu_future'});m.call('RUS_education_refresh')
        checkpoints=[]
        for day in range(1095):
            for a in ACTIVITIES:
                if a['id']=='construction' and m.vars[VARS['heat']]>60:continue
                if a['id'] in ('reading','outreach','library') and m.vars[VARS['heat']]<50:continue
                m.vars['RUS_edu_category']=a['category'];m.start(a['id'])
            if m.vars[VARS['heat']]<35:m.start('listen')
            if m.vars[VARS['heat']]>=70:m.start('restore_order')
            m.advance(1)
            self.assertLessEqual(m.vars['RUS_edu_active_count'],3)
            for v in VARS.values():self.assertGreaterEqual(m.vars[v],0);self.assertLessEqual(m.vars[v],100)
            if day in (364,729,1094):checkpoints.append((m.vars[VARS['basic']],m.vars[VARS['higher']],m.vars[bv('research_speed_factor')] ))
        self.assertLess(checkpoints[0][2],checkpoints[1][2]);self.assertLess(checkpoints[1][2],checkpoints[2][2])
        for kind in (0,1):
            self.assertLess(checkpoints[0][kind],checkpoints[1][kind]);self.assertLess(checkpoints[1][kind],checkpoints[2][kind])
        for mod,cap in POOL_CAPS.items():self.assertLessEqual(abs(m.vars[pv(mod)]),abs(cap)+.000001)
    def test_outputs_encoding_assets_and_gui_bounds(self):
        outputs=render_outputs()
        for p,b in outputs.items():self.assertEqual((ROOT/p).read_bytes(),b,str(p))
        for p in outputs:
            if p.suffix=='.yml':
                data=(ROOT/p).read_bytes();self.assertTrue(data.startswith(b'\xef\xbb\xbf'))
                keys=re.findall(r'^ ([\w.]+):',data.decode('utf-8-sig'),re.M);self.assertEqual(len(keys),len(set(keys)))
            else:parse((ROOT/p).read_text(encoding='utf-8-sig'))
        from PIL import Image
        for kind in ('basic','higher','heat','activity'):
            with Image.open(ROOT/ART/(kind+'_bar.dds')) as im:self.assertEqual(im.size,(11918,21))
        with Image.open(ROOT/ART/'posters.dds') as im:self.assertEqual(im.size,(160*(len(ACTIVITIES)+2),205))
        manifest=json.loads((ROOT/DESIGN/'poster_sources.json').read_text(encoding='utf-8'))
        self.assertEqual(len(manifest['sources']),len(ACTIVITIES))
        for a in manifest['sources']:self.assertEqual(hashlib.sha256((ROOT/a['path']).read_bytes()).hexdigest(),a['sha256'])
        catalogue=json.loads((ROOT/DESIGN/'poster_catalog.json').read_text(encoding='utf-8'))['posters']
        self.assertEqual(len(catalogue),271);self.assertEqual(len({p['code'] for p in catalogue}),271)
        self.assertEqual(sum(bool(p['activity']) for p in catalogue),len({a['poster'] for a in ACTIVITIES}))
        self.assertEqual({aid for p in catalogue for aid in p['activities']},{a['id'] for a in ACTIVITIES})
        by_code={p['code']:p for p in catalogue}
        for a in manifest['sources']:self.assertEqual(by_code[a['poster']]['sha256'],a['sha256'])
        from education_reform_content import POSTER_CATEGORIES
        for p in catalogue:
            self.assertIn(p['folder'],POSTER_CATEGORIES[p['category']][1]);self.assertRegex(p['title_zh'],r'[\u4e00-\u9fff]')
        for container in load(ROOT/GUI)[0].v:
            canvas_width=int(container.one('size').value('width'))
            for n in container.v:
                if n.k not in ('iconType','instantTextBoxType'):continue
                pos=n.one('position');x=int(pos.value('x'));y=int(pos.value('y'))
                if n.k=='iconType':
                    sprites={x.value('name').strip('"'):x for root in load(ROOT/GFX) for x in root.v}
                    sprite=sprites[n.value('spriteType').strip('"')];relative=sprite.value('texturefile').strip('"')
                    path=next(r/relative for r in (ROOT,ROOT.parents[3]/'common/Hearts of Iron IV') if (r/relative).is_file())
                    with Image.open(path) as im:w=im.width//int(sprite.value('noOfFrames','1'));h=im.height
                    self.assertLessEqual(y+h,601)
                else:w=int(n.value('maxWidth'))
                self.assertGreaterEqual(x,0);self.assertLessEqual(x+w,canvas_width);self.assertGreaterEqual(y,0);self.assertLess(y,601)
    def test_native_bar_art_noticeboard_and_empty_slot_visibility(self):
        from PIL import Image
        game=ROOT.parents[3]/'common/Hearts of Iron IV'
        for kind,source in [('basic','prod_progress_bar2.dds'),('higher','prod_progress_bar2_yellow.dds'),('heat','prod_progress_bar2_red.dds'),('activity','prod_progress_bar2.dds')]:
            with Image.open(ROOT/ART/(kind+'_bar.dds')) as image, Image.open(game/'gfx/interface/prod_progress_bar2_bg.dds') as bg, Image.open(game/'gfx/interface'/source) as fg:
                strip=image.convert('RGBA');base=bg.convert('RGBA');fill=fg.convert('RGBA').crop((0,21,118,42))
                for pct in (0,20,55,100):
                    expected=base.copy();right=round(118*pct/100)
                    if right:expected.alpha_composite(fill.crop((0,0,right,21)),(0,0))
                    self.assertEqual(strip.crop((pct*118,0,(pct+1)*118,21)).tobytes(),expected.tobytes())
                self.assertNotEqual(strip.getpixel((20*118+10,10)),base.getpixel((10,10)),'The native fill layer must be visibly nonempty')
        sprites={x.value('name').strip('"'):x for root in load(ROOT/GFX) for x in root.v}
        self.assertEqual(sprites['GFX_RUS_education_noticeboard'].value('texturefile').strip('"'),'gfx/interface/propaganda/propaganda_bg.dds')
        controls=load(ROOT/GUI)[0].v[0].v;names=[n.value('name').strip('"') for n in controls if n.value('name')]
        self.assertLess(names.index('education_noticeboard'),names.index('poster_1'))
        triggers=load(ROOT/SGUI)[0].v[0].one('triggers');m=initialized()
        for i in range(1,4):
            self.assertFalse(m.check(triggers.one(f'activity_progress_{i}_visible')))
            self.assertFalse(m.check(triggers.one(f'activity_days_{i}_visible')))
            self.assertEqual(m.vars[f'RUS_edu_catalog_{i}_frame'],1 if i==3 else 2)
            self.assertEqual(m.vars[f'RUS_edu_catalog_{i}_activity'],0)
        m.start('literacy');self.assertTrue(m.check(triggers.one('activity_progress_1_visible')))
        m.end('literacy',True);self.assertFalse(m.check(triggers.one('activity_progress_1_visible')))
        window=load(ROOT/GUI)[0].v[0]
        self.assertEqual(window.one('position').value('x'),'8')
        by_name={n.value('name').strip('"'):n for n in controls if n.value('name')}
        for kind in ('basic','higher','heat'):
            panel=by_name[kind+'_panel'];px=int(panel.one('position').value('x'));py=int(panel.one('position').value('y'))
            self.assertLess(names.index(kind+'_panel'),names.index(kind+'_label'))
            for suffix,w,h in [('name_panel',150,28),('value_panel',96,22),('label',150,24),('value',96,18),('bar',118,21)]:
                n=by_name[kind+'_'+suffix];x=int(n.one('position').value('x'));y=int(n.one('position').value('y'))
                self.assertGreaterEqual(x,px);self.assertGreaterEqual(y,py)
                self.assertLessEqual(x+w,px+160);self.assertLessEqual(y+h,py+82)
                self.assertEqual(x+w/2,px+80)
            for plate,label,w,h in [('name_panel','label',150,24),('value_panel','value',96,18)]:
                self.assertLess(names.index(kind+'_'+plate),names.index(kind+'_'+label))
                frame=by_name[kind+'_'+plate].one('position');text=by_name[kind+'_'+label].one('position')
                self.assertEqual(frame.value('x'),text.value('x'))
                self.assertGreaterEqual(int(text.value('y')),int(frame.value('y')))
                self.assertLessEqual(int(text.value('y'))+h,int(frame.value('y'))+(28 if plate=='name_panel' else 22))
    def test_education_texticons_transparent_distinct_cool_warm_palettes(self):
        from PIL import Image
        sprites={x.value('name').strip('"'):x for root in load(ROOT/GFX) for x in root.v}
        for kind in ('basic','higher'):
            with Image.open(ROOT/ART/(kind+'_texticon.dds')) as image:
                icon=image.convert('RGBA');self.assertEqual(icon.size,(24,24));self.assertEqual(icon.getchannel('A').getextrema(),(0,255))
                pixels=[icon.getpixel((x,y)) for y in range(24) for x in range(24)];total=sum(c[3] for c in pixels)
                means=[sum(c[i]*c[3] for c in pixels)/total for i in range(3)]
                self.assertGreater(means[2]-means[0] if kind=='basic' else means[0]-means[2],10)
                self.assertEqual(sprites[f'GFX_RUS_edu_{kind}_texticon'].value('texturefile').strip('"'),f'{ART.as_posix()}/{kind}_texticon.dds')

if __name__=='__main__':unittest.main(verbosity=2)
