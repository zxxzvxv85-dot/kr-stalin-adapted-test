"""Eligibility, single native cost, original conversion and readonly previews."""
import unittest
from itertools import product
from hoi4_politics_blocks import load
from generate_reconstruction_republic_decisions import ROOT,TAGS,DECISION,TARGET,ELIGIBLE,DEC,TR,FX,NATIVE,FOCUS
TRIGGERS={n.k:n for n in load(ROOT/TR)}
DECISION_NODE=load(ROOT/DEC)[0].one(DECISION)
def check(nodes,c,root,target):
    if hasattr(nodes,'v'):nodes=nodes.v
    def one(n):
        if n.k in TRIGGERS:return check(TRIGGERS[n.k].v,c,root,target)
        if n.k in ('AND','hidden_trigger'):return check(n.v,c,root,target)
        if n.k=='OR':return any(one(x) for x in n.v)
        if n.k=='NOT':return not any(one(x) for x in n.v)
        if n.k=='FROM':return check(n.v,target,root,target)
        if n.k=='tag':return c['tag']==n.v
        if n.k=='original_tag':return c['tag']==n.v
        if n.k=='exists':return c['exists']==(n.v=='yes')
        if n.k=='has_completed_focus':return n.v in c.get('focuses',set())
        if n.k=='has_country_flag':return n.v in c.get('flags',set())
        if n.k=='is_subject_of':return c['overlord']==root['tag']
        if n.k=='has_autonomy_state':return c['autonomy']==n.v
        if n.k=='has_government':return c['gov']==n.v
        if n.k=='has_socialist_government':return (c['gov'] in ('totalist','syndicalist','radical_socialist'))==(n.v=='yes')
        if n.k=='RUS_diplomacy_can_pay_20':return root['pp']>=root['cost']
        if n.k=='RUS_europe_intervention_target_selected_or_overview':return root.get('selected') in (None,target['tag'])
        raise AssertionError(n.k)
    return all(one(n) for n in nodes)
def actor():return dict(tag='RUS',gov='communist',focuses={'RUS_future_foreign_014'},flags=set(),pp=20,cost=20)
def target(tag):return dict(tag=tag,gov='radical_socialist',exists=True,overlord='RUS',autonomy='autonomous_puppet')
def all_decisions():return {n.k:n for c in load(ROOT/NATIVE) if isinstance(c.v,list) for n in c.v}

class Tests(unittest.TestCase):
    def test_exact_requested_tags_and_936_eligibility_combinations(self):
        self.assertEqual(set(TAGS),{'BAT','EST','LAT','LIT','BLR','UKR','GEO','AZR','ARM','KAZ','TRK','KHI','BUK'})
        self.assertEqual(set(n.k for n in DECISION_NODE.one('targets').v),set(TAGS))
        self.assertIsNone(DECISION_NODE.one('target_array'))
        for tag,exists,gov,overlord,member,focus in product(TAGS,(False,True),('social_democrat','radical_socialist','communist'),(None,'GER','RUS'),(False,True),(False,True)):
            r=actor();t=target(tag);t.update(exists=exists,gov=gov,overlord=overlord,autonomy='soviet_socialist_republic' if member else 'autonomous_puppet')
            if not focus:r['focuses'].clear()
            eligible=exists and gov!='social_democrat' and overlord=='RUS' and not member and focus
            actual=check(DECISION_NODE.one('target_root_trigger'),r,r,t) and check(DECISION_NODE.one('target_trigger'),r,r,t)
            self.assertEqual(actual,eligible,(tag,exists,gov,overlord,member,focus))

    def test_cost_paid_once_and_already_members_do_not_offer_conversion(self):
        self.assertEqual(DECISION_NODE.value('cost'),'RUS_diplomacy_pp_cost_20?20')
        self.assertEqual(DECISION_NODE.value('fire_only_once'),'yes')
        self.assertNotIn('RUS_diplomacy_can_pay',DECISION_NODE.one('complete_effect').raw())
        for cost in (20,16):
            r=actor();r['cost']=cost;t=target('KAZ')
            r['pp']=cost-.01;self.assertFalse(check(DECISION_NODE.one('available'),r,r,t))
            r['pp']=cost;self.assertTrue(check(DECISION_NODE.one('available'),r,r,t))
            # Engine has already charged the declared cost before this guard.
            r['pp']=0
            self.assertTrue(check(DECISION_NODE.one('complete_effect').one('if').one('limit'),r,r,t))
            t['autonomy']='soviet_socialist_republic'
            self.assertFalse(check(DECISION_NODE.one('target_trigger'),r,r,t))
            self.assertFalse(check(DECISION_NODE.one('visible'),r,r,t))

    def test_original_conversion_effects_and_generic_costs_preserved(self):
        decisions=all_decisions();old=decisions['RUS_add_to_soviet_republic']
        helper=load(ROOT/FX)[0]
        self.assertEqual([n.norm() for n in old.one('complete_effect').v if n.k!='log'],[n.norm() for n in helper.v[:-1]])
        register=helper.v[-1].one('if')
        self.assertIn('is_in_array',register.one('limit').raw())
        self.assertEqual(register.one('add_to_array').value('value'),'FROM')
        self.assertEqual(decisions['RUS_add_to_soviet_republic_new'].value('cost'),'1000')
        self.assertIn(TARGET,old.one('target_trigger').raw())
        self.assertNotIn('RUS_add_soviet_union_integration_strain',helper.raw())
        self.assertEqual(helper.one('set_autonomy').value('autonomy_state'),'soviet_socialist_republic')
        self.assertIn('RUS_stalin_set_subject_radical_socialist_if_communist_path',helper.raw())

    def test_focus_has_13_readonly_unlock_previews(self):
        focus=next(n for n in load(ROOT/FOCUS) if n.value('id')=='RUS_future_foreign_014')
        previews=[n for n in focus.one('completion_reward').children('effect_tooltip') if DECISION in n.raw()]
        self.assertEqual(len(previews),1)
        self.assertEqual({n.value('target') for n in previews[0].children('activate_targeted_decision')},set(TAGS))
        for tag in TAGS:
            r=actor();t=target(tag);r['selected']='LIT'
            self.assertEqual(check(DECISION_NODE.one('target_trigger'),r,r,t),tag=='LIT')

if __name__=='__main__':unittest.main(verbosity=2)
