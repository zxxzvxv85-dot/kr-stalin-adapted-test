"""Execute unlock/settlement scripts; game UI still needs a restart test."""
import copy,subprocess,unittest
from PIL import Image
from doudizhu_script_model import ScriptModel,load_effects
from hoi4_politics_blocks import parse,load
from generate_easter_egg_advisors import ROOT,ADVISORS,token,render_outputs
from generate_tesla_minesweeper import PREFIX,render_outputs as mines_outputs

FX=load_effects((ROOT/'common/scripted_effects/RUS_easter_egg_advisor_effects.txt').read_text(),
               (ROOT/'common/scripted_effects/RUS_tesla_minesweeper.txt').read_text())

class Model(ScriptModel):
    def __init__(self,hired=False,eligible=10):
        super().__init__(copy.deepcopy(FX));self.ideas={'RUS_egg_larruping_advisor'} if hired else set()
        self.characters=set();self.recruits=0;self.events=[];self.states=[dict(energy_infrastructure=0,industrial_infrastructure=0,slots=0) for _ in range(eligible)]
        self.state=None;self.country=self.vars
    def check(self,nodes):
        if hasattr(nodes,'v'):nodes=nodes.v
        for n in nodes:
            if n.k=='has_idea':ok=n.v in self.ideas
            elif n.k=='has_character':ok=n.v in self.characters
            elif n.k=='any_owned_state':ok=any(s['energy_infrastructure']<1 and s['industrial_infrastructure']<1 for s in self.states)
            elif n.k=='owner':
                old=self.vars;self.vars=self.country;ok=self.check(n.v);self.vars=old
            else:ok=super().check([n])
            if not ok:return False
        return True
    def run(self,nodes):
        handled={'clamp_variable','recruit_character','country_event','while_loop_effect','random_owned_controlled_state',
                 'add_extra_state_shared_building_slots','add_building_construction',
                 'RUS_tesla_minesweeper_refresh_gui','RUS_tesla_refresh_power_grid_bonuses'}
        pending=[]
        for n in nodes:
            if n.k not in handled:pending.append(n);continue
            if pending:super().run(pending);pending=[]
            if n.k=='clamp_variable':
                key=n.value('var');self.vars[key]=max(self.number(n.value('min')),min(self.number(n.value('max')),self.number(key)))
            elif n.k=='recruit_character':self.characters.add(n.v);self.recruits+=1
            elif n.k=='country_event':self.events.append((n.value('id'),int(n.value('days'))))
            elif n.k=='while_loop_effect':
                count=0
                while self.check(n.one('limit')):
                    self.run([x for x in n.v if x.k!='limit']);count+=1
                    assert count<100,'settlement loop did not terminate'
            elif n.k=='random_owned_controlled_state':
                state=next(s for s in self.states if s['energy_infrastructure']<1 and s['industrial_infrastructure']<1)
                before,self.state,self.vars=self.vars,state,state
                self.run([x for x in n.v if x.k!='limit']);self.vars=before;self.state=None
            elif n.k=='add_extra_state_shared_building_slots':self.state['slots']+=int(n.v)
            elif n.k=='add_building_construction':self.state[n.value('type')]+=int(n.value('level'))
        if pending:super().run(pending)

class Tests(unittest.TestCase):
    def test_mia_completion_permanently_adds_to_education_spirit(self):
        from test_education_reform import initialized,unlock_all
        from education_reform_content import ACTIVITIES,CONTROLS
        from generate_education_reform import active,bv
        bonus='RUS_edu_mia_permanent_research'
        for a in ACTIVITIES+CONTROLS:
            m=unlock_all(initialized());m.vars['RUS_basic_education_level']=100
            m.ideas.add('RUS_egg_mia_advisor');m.call('RUS_education_begin_'+a['id'])
            self.assertIn(active(a),m.flags,a['id'])
            self.assertEqual(m.vars.get(bonus,0),0,'opening must not reward')
            m.call('RUS_education_finish_'+a['id'])
            self.assertAlmostEqual(m.vars[bonus],.05)
            m.call('RUS_education_finish_'+a['id'])
            self.assertAlmostEqual(m.vars[bonus],.05,'same completion cannot reward twice')
            m.ideas.discard('RUS_egg_mia_advisor');m.call('RUS_education_refresh')
            total=m.vars[bv('research_speed_factor')]
            m.vars[bonus]=0;m.call('RUS_education_refresh')
            self.assertAlmostEqual(total-m.vars[bv('research_speed_factor')],.05)
            self.assertFalse(any('mia' in d for d in m.dynamic),'no separate Mia spirit')
        m=initialized();m.ideas.add('RUS_egg_mia_advisor')
        m.call('RUS_education_begin_literacy');m.call('RUS_education_cancel_literacy')
        m.call('RUS_education_finish_literacy');self.assertEqual(m.vars.get(bonus,0),0)
        m=initialized();m.call('RUS_education_begin_literacy')
        m.call('RUS_education_finish_literacy');self.assertEqual(m.vars.get(bonus,0),0)
        m=initialized();m.ideas.add('RUS_egg_mia_advisor')
        for a in ('literacy','schools'):
            m.call('RUS_education_begin_'+a);m.call('RUS_education_finish_'+a)
        self.assertAlmostEqual(m.vars[bonus],.1)
        m.call('RUS_education_refresh');self.assertAlmostEqual(m.vars[bonus],.1)

    def test_mia_monthly_credits_existing_agriculture_account(self):
        ag=load_effects((ROOT/'common/scripted_effects/RUS_agri_development_effects.txt').read_text())
        ag.update(load_effects('RUS_maximalist_land_reform_update_stage_idea = {}'))
        class CreditModel(Model):
            def call(self,name):
                if name=='RUS_maximalist_land_reform_update_stage_idea':
                    self.call('RUS_agri_refresh_score_account');return
                super().call(name)
        for hired,enabled,success,failure in [(False,True,False,False),(True,False,False,False),
                (True,True,False,False),(True,True,True,False),(True,True,False,True)]:
            m=CreditModel();m.effects.update(ag)
            if hired:m.ideas.add('RUS_egg_mia_advisor')
            if enabled:m.flags.update({'RUS_agri_management_unlocked','RUS_maximalist_land_reform_in_progress'})
            if failure:m.flags.add('RUS_maximalist_land_reform_failure')
            if success:m.flags.add('RUS_maximalist_land_reform_success')
            m.vars['RUS_maximalist_land_reform_score']=100 if success else 10
            m.call('RUS_egg_mia_monthly')
            if hired and enabled and not failure:
                if success:self.assertEqual(m.vars['RUS_agri_spendable_score'],100)
                else:self.assertEqual(m.vars['RUS_maximalist_land_reform_score'],110)
            else:self.assertEqual(m.vars['RUS_maximalist_land_reform_score'],10)

    def test_unlock_is_opt_in_and_idempotent(self):
        for key in ADVISORS:
            m=Model();self.assertNotIn(token(key),m.characters)
            m.call(token(key)+'_unlock');m.call(token(key)+'_unlock')
            self.assertEqual(m.characters,{token(key)});self.assertEqual(m.recruits,1)
            self.assertFalse(m.ideas,'unlocking must not appoint the adviser')

    def test_traits_and_portrait_bindings(self):
        traits=load(ROOT/'common/country_leader/RUS_easter_egg_advisor_traits.txt')[0]
        xin=traits.one(token('xin')+'_trait')
        self.assertEqual(float(xin.value('org_loss_at_low_org_factor')),-1)
        self.assertFalse(xin.one('custom_modifier_tooltip'),'native modifier must display its real value')
        su=traits.one(token('su_beichen')+'_trait')
        expected=dict(army_attack_factor=.2,combat_width_factor=-.2,supply_consumption_factor=-.2,army_org_factor=.2)
        self.assertEqual({k:float(su.value(k)) for k in expected},expected)
        chars=load(ROOT/'common/characters/RUS_easter_egg_advisors.txt')[0]
        gfx=load(ROOT/'interface/RUS_easter_egg_advisors.gfx')[0]
        sprites={n.value('name').strip('"'):n.value('texturefile').strip('"') for n in gfx.v}
        for key in ADVISORS:
            role=chars.one(token(key)).one('advisor')
            self.assertEqual(role.value('slot'),'political_advisor');self.assertEqual(role.value('cost'),'0')
            portrait=chars.one(token(key)).one('portraits').one('civilian').value('small')
            im=Image.open(ROOT/sprites[portrait]);self.assertEqual(im.size,(65,67));self.assertEqual(im.mode,'RGBA')
            self.assertEqual(im.getchannel('A').getextrema(),(0,255))

    def test_hired_loss_is_victory_once_with_original_streak_reward(self):
        for result in ('finish_victory','finish_defeat'):
            m=Model(hired=True);m.flags.add(PREFIX+'_active');m.vars[PREFIX+'_win_streak']=2
            m.call(PREFIX+'_'+result)
            self.assertIn(PREFIX+'_won',m.flags);self.assertNotIn(PREFIX+'_lost',m.flags)
            self.assertEqual(m.vars[PREFIX+'_win_streak'],3);self.assertEqual(m.vars[PREFIX+'_reward_grids'],3)
            self.assertEqual(sum(s['energy_infrastructure'] for s in m.states),3)
            self.assertEqual(m.events,[(PREFIX+'.1',60)])
            m.call(PREFIX+'_finish_defeat');m.call(PREFIX+'_finish_victory')
            self.assertEqual(m.vars[PREFIX+'_win_streak'],3);self.assertEqual(len(m.events),1)

    def test_unlocked_but_not_hired_keeps_normal_loss(self):
        m=Model();m.call(token('larruping')+'_unlock');m.flags.add(PREFIX+'_active');m.vars[PREFIX+'_win_streak']=4
        m.call(PREFIX+'_finish_defeat')
        self.assertIn(PREFIX+'_lost',m.flags);self.assertNotIn(PREFIX+'_won',m.flags)
        self.assertEqual(m.vars[PREFIX+'_win_streak'],0);self.assertFalse(any(s['energy_infrastructure'] for s in m.states))

    def test_mine_click_routes_to_success_and_closed_window_is_not_a_result(self):
        m=Model(hired=True);m.flags.update({PREFIX+'_active',PREFIX+'_initialised',PREFIX+'_mine_00'})
        m.call(PREFIX+'_reveal_00');self.assertIn(PREFIX+'_won',m.flags)
        m=Model(hired=True);m.flags.add(PREFIX+'_active');m.call(PREFIX+'_close')
        self.assertIn(PREFIX+'_active',m.flags);self.assertFalse(m.events)

    def test_no_reward_states_still_win_and_dismissal_restores_loss(self):
        m=Model(hired=True,eligible=0);m.flags.add(PREFIX+'_active');m.call(PREFIX+'_finish_defeat')
        self.assertIn(PREFIX+'_won',m.flags);self.assertIn(PREFIX+'_no_reward',m.flags)
        m.ideas.clear();m.call(PREFIX+'_start');m.call(PREFIX+'_finish_defeat')
        self.assertIn(PREFIX+'_lost',m.flags);self.assertNotIn(PREFIX+'_won',m.flags)

    def test_original_settlement_bodies_and_other_gameplay_are_preserved(self):
        # Fixed, reviewed pre-feature baseline; the check must also pass after
        # this feature is committed and HEAD already contains the wrappers.
        before={n.k:n for n in parse(subprocess.check_output(['git','-C',str(ROOT),'show','fcb5531:common/scripted_effects/RUS_tesla_minesweeper.txt']).decode('utf8'))}
        after={n.k:n for n in load(ROOT/'common/scripted_effects/RUS_tesla_minesweeper.txt')}
        for key,n in before.items():
            if key==PREFIX+'_finish_victory':
                body=[x.norm() for x in after[key].one('if').v if x.k not in ('limit','clr_country_flag') or x.v!=PREFIX+'_lost']
                self.assertEqual(body,[x.norm() for x in parse('limit = { has_country_flag = '+PREFIX+'_active }')]+[x.norm() for x in n.v])
            elif key==PREFIX+'_finish_defeat':
                body=after[key].one('if').one('else')
                self.assertEqual([x.norm() for x in body.v],[x.norm() for x in n.v])
            else:self.assertEqual(after[key].norm(),n.norm(),key)
        for render in (render_outputs,mines_outputs):
            for path,text in render().items():self.assertEqual((ROOT/path).read_text(encoding='utf-8-sig'),text,path)

if __name__=='__main__':unittest.main(verbosity=2)
