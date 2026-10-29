"""Native red route guards and postwar release exemptions; no engine claim."""
from pathlib import Path
from itertools import product
import unittest
from hoi4_politics_blocks import load,parse
from generate_ostwall_route_locks import ROOT,BLOCKED,TAGS,INPUTS
from kr_generation_baseline import kr_root

TR={n.k:n for n in load(ROOT/'common/scripted_triggers/RUS_ostwall_native_routes_triggers.txt')}
FX=load(ROOT/'common/scripted_effects/RUS_ostwall_native_routes_effects.txt')[0]
def red(c):return c and c['gov'] in ('radical_socialist','syndicalist','totalist','communist')
def check(nodes,c):
    if c is None:return False
    def one(n):
        if n.k in TR:return check(TR[n.k].v,c)
        if n.k in ('AND','hidden_trigger'):return check(n.v,c)
        if n.k=='OR':return any(one(x) for x in n.v)
        if n.k=='NOT':return not any(one(x) for x in n.v)
        if n.k=='original_tag':return c['tag']==n.v
        if n.k=='has_government':return c['gov']==n.v
        if n.k=='has_socialist_government':return (c['gov'] in ('radical_socialist','syndicalist','totalist'))==(n.v=='yes')
        if n.k=='is_subject':return bool(c['overlord'])==(n.v=='yes')
        if n.k=='is_in_faction':return bool(c['faction_leader'])==(n.v=='yes')
        if n.k=='overlord':return check(n.v,c['overlord'])
        if n.k=='faction_leader':return check(n.v,c['faction_leader'])
        if n.k=='has_idea':return n.v in c['ideas']
        raise AssertionError(n.k)
    return all(one(n) for n in nodes)
def run(nodes,c):
    for n in nodes:
        if n.k=='if':
            if check(n.one('limit').v,c):run([x for x in n.v if x.k!='limit'],c)
        elif n.k=='clr_country_flag':c['flags'].discard(n.v)
        elif n.k=='country_event':
            assert n.v=='united_baltic_duchy_events.41'
            c['events'].append(n.v)
            # This native event's immediate block removes the Forest Brothers.
            c['ideas'].discard('BAT_forest_brothers')
        elif n.k=='leave_faction':c['faction_leader']=None
        else:raise AssertionError('Unexpected policy mutation: '+n.k)

def country(tag,gov='authoritarian_democrat'):
    return dict(tag=tag,gov=gov,overlord=None,faction_leader=None,ideas=set(),flags=set(),events=[])

class Tests(unittest.TestCase):
    def test_native_entry_guards_and_unchanged_other_country_content(self):
        expected={'events/BAT events (Baltic Duchy).txt':{'united_baltic_duchy_events.31'},
                  'events/LIT events (Lithuania).txt':{'lithuania_events.210'},
                  'events/BLR events (White Ruthenia).txt':{'belarus_political_events.42','belarus_political_events.53'},
                  'common/decisions/LIT decisions (Lithuania).txt':{'LIT_start_the_revolution'}}
        for path in INPUTS:
            before=load(kr_root(ROOT)/path);after=load(ROOT/path)
            if path.startswith('events/'):
                old={n.value('id'):n for n in before if n.k=='country_event'};new={n.value('id'):n for n in after if n.k=='country_event'}
            else:
                old={n.k:n for c in before for n in c.v};new={n.k:n for c in after for n in c.v}
            self.assertEqual(old.keys(),new.keys())
            self.assertEqual({k for k in old if old[k].norm()!=new[k].norm()},expected[path])
            for key in expected[path]:self.assertIn(BLOCKED,new[key].raw())
        event=next(n for n in load(kr_root(ROOT)/'events/BAT events (Baltic Duchy).txt') if n.value('id')=='united_baltic_duchy_events.41')
        self.assertIn('BAT_forest_brothers',event.one('immediate').raw())

    def test_five_tags_only_and_postwar_government_exemptions(self):
        red_parent=country('RUS','communist');white_parent=country('GER')
        for tag,gov,parent,leader in product((*TAGS,'UKR','ARM','EST','LAT','FRA'),('authoritarian_democrat','radical_socialist','communist'),(None,white_parent,red_parent),(None,white_parent,red_parent)):
            c=country(tag,gov);c.update(overlord=parent,faction_leader=leader)
            c['ideas'].add('BAT_forest_brothers');c['flags'].add('BAT_AI_collapse')
            blocked=tag in TAGS and not red(c) and not red(parent)
            self.assertEqual(check(TR[BLOCKED].v,c),blocked,(tag,gov,parent))
            run(FX.v,c)
            self.assertEqual(c['gov'],gov,'No force-blue government watchdog')
            self.assertIs(c['overlord'],parent)
            self.assertIs(c['faction_leader'],None if blocked and red(leader) else leader)
            self.assertEqual(c['events'],['united_baltic_duchy_events.41'] if tag=='BAT' and blocked else [])
            before=len(c['events']);run(FX.v,c);self.assertEqual(len(c['events']),before)

    def test_on_actions_use_correct_invited_country_scope_and_ukraine_is_untouched(self):
        hooks=load(ROOT/'common/on_actions/RUS_ostwall_native_routes_on_actions.txt')[0]
        offer=hooks.one('on_offer_join_faction').one('effect').one('FROM')
        self.assertEqual(offer.value('RUS_ostwall_preserve_native_alignment'),'yes')
        self.assertIn('on_daily',hooks.raw())
        ukr=(ROOT/'common/on_actions/RUS_ostwall_alignment_on_actions.txt').read_text(encoding='utf-8-sig')
        self.assertIn('UKR_hetman_side_ai',ukr)
        self.assertNotIn('UKR',TR[BLOCKED].raw())

if __name__=='__main__':unittest.main(verbosity=2)
