"""Exercise Suyi's daily draw, hire/remove timing and country isolation."""
import copy,subprocess,unittest
from hoi4_politics_blocks import load,parse
from test_easter_egg_advisors import Model,ROOT

ROLE=load(ROOT/'common/characters/RUS_easter_egg_advisors.txt')[0].one('RUS_egg_suyi').one('advisor')

class SuyiModel(Model):
    def __init__(self,draws=()):
        super().__init__();self.dynamic=set();self.draws=iter(draws);self.draw_count=0;self.tag='RUS';self.ai=False
        self.vars['global.num_days']=100
    def check(self,nodes):
        if hasattr(nodes,'v'):nodes=nodes.v
        for n in nodes:
            if n.k=='has_dynamic_modifier':ok=n.v in self.dynamic
            elif n.k=='original_tag':ok=n.v==self.tag
            elif n.k=='is_ai':ok=self.ai==(n.v=='yes')
            else:ok=super().check([n])
            if not ok:return False
        return True
    def run(self,nodes):
        pending=[]
        for n in nodes:
            if n.k not in ('randomize_variable','add_dynamic_modifier','remove_dynamic_modifier','force_update_dynamic_modifier'):
                pending.append(n);continue
            if pending:super().run(pending);pending=[]
            if n.k=='randomize_variable':
                self.draw_count+=1
                self.vars[n.value('var')]=next(self.draws,self.rng.uniform(float(n.value('min')),float(n.value('max'))))
            elif n.k=='add_dynamic_modifier':self.dynamic.add(n.value('modifier'))
            elif n.k=='remove_dynamic_modifier':self.dynamic.discard(n.value('modifier'))
        if pending:super().run(pending)
    def hire(self):
        # on_add can run before the new idea becomes observable.
        self.run(ROLE.one('on_add').v);self.ideas.add('RUS_egg_suyi_advisor')
    def fire(self):
        self.ideas.discard('RUS_egg_suyi_advisor');self.run(ROLE.one('on_remove').v)

class Tests(unittest.TestCase):
    def test_unlock_does_not_draw_then_first_appointment_draws_once(self):
        m=SuyiModel([12.348,-17.236]);m.call('RUS_egg_suyi_unlock')
        m.call('RUS_egg_suyi_daily');self.assertEqual(m.draw_count,0)
        m.hire();self.assertEqual(m.draw_count,1);self.assertAlmostEqual(m.vars['RUS_egg_suyi_pp'],12.35)
        self.assertIn('RUS_egg_suyi_active',m.flags);self.assertEqual(m.dynamic,{'RUS_egg_suyi_daily_pp'})
        for _ in range(4):m.call('RUS_egg_suyi_daily')
        m.fire();self.assertFalse(m.dynamic);self.assertNotIn('RUS_egg_suyi_active',m.flags)
        m.hire();self.assertEqual(m.draw_count,1);self.assertEqual(m.vars['RUS_egg_suyi_pp'],12.35)
        m.vars['global.num_days']+=1;m.call('RUS_egg_suyi_daily')
        self.assertEqual(m.draw_count,2);self.assertAlmostEqual(m.vars['RUS_egg_suyi_pp'],-17.24)
        self.assertEqual(len(m.dynamic),1)

    def test_range_zero_negative_positive_and_no_daily_stacking(self):
        for value in (-30,-29.999,-.004,0,.004,29.999,30):
            m=SuyiModel([value]);m.call('RUS_egg_suyi_unlock');m.hire()
            self.assertGreaterEqual(m.vars['RUS_egg_suyi_pp'],-30);self.assertLessEqual(m.vars['RUS_egg_suyi_pp'],30)
            self.assertAlmostEqual(m.vars['RUS_egg_suyi_pp'],round(value,2))
        m=SuyiModel();m.call('RUS_egg_suyi_unlock');m.hire()
        for day in range(101,201):
            m.vars['global.num_days']=day;m.call('RUS_egg_suyi_daily');m.call('RUS_egg_suyi_daily')
            self.assertTrue(-30<=m.vars['RUS_egg_suyi_pp']<=30)
            self.assertEqual(len(m.dynamic),1)
        self.assertEqual(m.draw_count,101)

    def test_unhired_days_and_saved_draw_and_cleanup(self):
        m=SuyiModel([5,9]);m.call('RUS_egg_suyi_unlock');m.hire();m.fire()
        m.vars['global.num_days']=110;m.call('RUS_egg_suyi_daily');self.assertEqual(m.draw_count,1)
        # Persisted flags/variables are sufficient to reuse a saved day's result.
        m.hire();self.assertEqual(m.draw_count,2);self.assertEqual(m.vars['RUS_egg_suyi_pp'],9)
        saved=SuyiModel();saved.vars=copy.deepcopy(m.vars);saved.flags=set(m.flags);saved.ideas=set(m.ideas)
        saved.call('RUS_egg_suyi_daily');self.assertEqual(saved.draw_count,0)
        self.assertEqual(saved.vars['RUS_egg_suyi_pp'],9)
        saved.ideas.clear();saved.call('RUS_egg_suyi_daily');self.assertFalse(saved.dynamic)

    def test_foreign_and_ai_do_not_receive_bonus(self):
        for tag,ai in [('GER',False),('RUS',True)]:
            m=SuyiModel();m.tag=tag;m.ai=ai;m.flags.add('RUS_egg_suyi_unlocked');m.ideas.add('RUS_egg_suyi_advisor')
            m.call('RUS_egg_suyi_appoint');m.call('RUS_egg_suyi_daily')
            self.assertEqual(m.draw_count,0);self.assertFalse(m.dynamic)

    def test_native_effect_is_flat_pp_and_prior_advisers_unchanged(self):
        dm=load(ROOT/'common/dynamic_modifiers/RUS_easter_egg_modifiers.txt')
        bonus=next(n for n in dm if n.k=='RUS_egg_suyi_daily_pp')
        self.assertEqual(bonus.value('political_power_gain'),'RUS_egg_suyi_pp')
        self.assertIsNone(bonus.one('political_power_factor'))
        self.assertIsNone(bonus.one('icon'))
        for path in ('common/characters/RUS_easter_egg_advisors.txt','common/country_leader/RUS_easter_egg_advisor_traits.txt'):
            before=parse(subprocess.check_output(['git','show','e7d2e3a:'+path]).decode('utf-8-sig'))[0]
            after=load(ROOT/path)[0]
            self.assertEqual([n.norm() for n in before.v],[n.norm() for n in after.v if 'suyi' not in n.k])
        self.assertIn('RUS_egg_suyi_daily = yes',(ROOT/'common/on_actions/RUS_easter_egg_on_actions.txt').read_text())

if __name__=='__main__':unittest.main(verbosity=2)
