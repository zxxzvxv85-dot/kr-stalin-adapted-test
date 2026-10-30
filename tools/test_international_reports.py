"""Execute report guards and chains; this is not an HOI4 UI test."""
import copy,json,re,unittest
from itertools import product
from pathlib import Path
from hoi4_politics_blocks import load,parse
from generate_international_reports import ROOT,SPEC,NS,P,speech_parts,outputs

TR={n.k:n.v for n in load(ROOT/'common/scripted_triggers/RUS_international_reports_triggers.txt')}
FX={n.k:n.v for n in load(ROOT/'common/scripted_effects/RUS_international_reports_effects.txt')}
HOOK=load(ROOT/'common/on_actions/RUS_international_reports_on_actions.txt')[0]
EVENTS={n.value('id'):n for n in load(ROOT/'events/RUS_international_reports_events.txt') if n.k=='country_event'}

def country(tag,red=True):return dict(tag=tag,red=red,flags=set(),states=set(),exists=True,war=True,events=[])
def world():return {k:country(k) for k in ['RUS','SRI','SWF','FOP','CHL','ARG','GER']}

def check(nodes,c,w,root,source):
    def one(n):
        k,v=n.k,n.v
        if k in TR:return check(TR[k],c,w,root,source)==(v=='yes')
        if k in ('AND','hidden_trigger'):return check(v,c,w,root,source)
        if k=='OR':return any(one(x) for x in v)
        if k=='NOT':return not any(one(x) for x in v)
        if k=='has_country_flag':return v in c['flags']
        if k=='has_global_flag':return v in w.get('global',set())
        if k=='tag':return c['tag']==v
        if k=='has_socialist_government':return c['red']==(v=='yes')
        if k=='has_government':return c.get('government','')==v
        if k=='exists':return c['exists']==(v=='yes')
        if k=='has_war':return c['war']==(v=='yes')
        if k=='owns_state':return int(v) in c['states']
        if k=='country_exists':return w.get(v,dict(exists=False))['exists']
        if k in ('ROOT','FROM'):return check(v,root if k=='ROOT' else source,w,root,source)
        if k in w:return w[k]['exists'] and check(v,w[k],w,root,source)
        raise AssertionError(k)
    return all(one(n) for n in nodes)

def run(nodes,c,w,root=None,source=None):
    root=root or c
    for n in nodes:
        if n.k=='if':
            if check(n.one('limit').v,c,w,root,source):run([x for x in n.v if x.k!='limit'],c,w,root,source)
        elif n.k in FX:run(FX[n.k],c,w,root,source)
        elif n.k in ('hidden_effect',):run(n.v,c,w,root,source)
        elif n.k=='set_country_flag':c['flags'].add(n.v)
        elif n.k=='country_event':c['events'].append((n.value('id'),n.value('days','0')))
        elif n.k=='ROOT':run(n.v,root,w,root,source)
        elif n.k in ('name',):pass
        else:raise AssertionError(n.k)

class Tests(unittest.TestCase):
    def test_full_speech_preserved_in_two_readable_parts(self):
        spec=json.loads((ROOT/SPEC).read_text(encoding='utf8'));parts=speech_parts(spec['speech']['paragraphs'])
        self.assertEqual(len(parts),2)
        self.assertEqual([p for page in parts for p in page],spec['speech']['paragraphs'])
        self.assertTrue(all(800<=len(''.join(p))<=1200 for p in parts))
        self.assertEqual(set(EVENTS),{NS+'.'+str(i) for i in [1,2,3,4,5,6,8]})

    def test_participation_scopes_and_nonparticipants(self):
        nodes=HOOK.one('on_send_volunteers').one('effect').v
        for sender_red,receiver_red,war,tag in product((False,True),(False,True),(False,True),['SRI','SWF','FOP','CHL','GER']):
            w=world();c=w['RUS'];t=w[tag];c['red']=sender_red;t['red']=receiver_red;t['war']=war
            run(nodes,c,w,c,t)
            kind={'SRI':'italy','SWF':'spain','FOP':'south','CHL':'south'}.get(tag)
            expected={P+kind+'_intervened'} if kind and sender_red and receiver_red and war else set()
            self.assertEqual(c['flags'],expected)
            self.assertFalse(t['flags'])
        for tag,flag in [('SRI','SRI_italy_unified_flag'),('SWF','SPA_aftermath_of_the_civil_war')]:
            w=world();w[tag]['flags'].add(flag);run(nodes,w['RUS'],w,w['RUS'],w[tag]);self.assertFalse(w['RUS']['flags'])
        w=world();w['RUS'].update(red=False,government='communist');w['SRI'].update(red=False,government='communist')
        run(nodes,w['RUS'],w,w['RUS'],w['SRI'])
        self.assertEqual(w['RUS']['flags'],{P+'italy_intervened'})

    def test_victory_requires_participation_and_full_native_outcome(self):
        for kind,tag,idx,state,flag in [('italy','SRI',1,None,'SRI_italy_unified_flag'),('spain','SWF',3,41,'SPA_aftermath_of_the_civil_war'),('south','FOP',8,278,None)]:
            for marked,won,red in product((False,True),repeat=3):
                w=world();c=w['RUS'];t=w[tag];t['red']=red
                if marked:c['flags'].add(P+kind+'_intervened')
                if won:
                    if state:t['states'].add(state)
                    if flag:t['flags'].add(flag)
                    if kind=='south':w['ARG']['exists']=False
                run(FX[P+'check'],c,w);run(FX[P+'check'],c,w)
                self.assertEqual(c['events'],[(NS+'.'+str(idx),'0')] if marked and won and red else [])
        for begun,over,red in product((False,True),repeat=3):
            w=world();c=w['RUS'];c['red']=red;w['global']=set()
            if begun:w['global'].add('USA_civil_war_begun_flag')
            if over:w['global'].add('USA_civil_war_over_flag')
            run(FX[P+'check'],c,w);run(FX[P+'check'],c,w)
            self.assertEqual(c['events'],[(NS+'.4','0')] if begun and not over and red else [])

    def test_visit_exact_delay_and_speech_is_second_option_only(self):
        w=world();c=w['RUS'];immediate=EVENTS[NS+'.1'].one('immediate').v
        run(immediate,c,w);run(immediate,c,w)
        self.assertEqual(c['events'],[(NS+'.2','7')])
        c['events'].clear();options=EVENTS[NS+'.4'].children('option')
        run(options[0].v,c,w);self.assertFalse(c['events'])
        run(options[1].v,c,w);run(options[1].v,c,w)
        self.assertEqual(c['events'],[(NS+'.5','0')])
        run(EVENTS[NS+'.5'].one('option').v,c,w)
        self.assertEqual(c['events'][-1],(NS+'.6','0'))
        before=copy.deepcopy(c);run(EVENTS[NS+'.6'].one('option').v,c,w);self.assertEqual(c,before)

    def test_generated_localisation_dynamic_city_and_asset_references(self):
        data=outputs();catalogs=[]
        for path,text in data.items():
            raw=(ROOT/path).read_bytes()
            self.assertEqual(raw.replace(b'\r\n',b'\n'),text.encode('utf-8-sig' if path.endswith('.yml') else 'utf8'))
            if path.endswith('.yml'):
                rows=re.findall(r'^ (\S+):0 (.*)$',text,re.M);catalogs.append(dict(rows));self.assertEqual(len(rows),len(dict(rows)))
        self.assertTrue(all(x==catalogs[0] for x in catalogs))
        visit=json.loads(catalogs[0][NS+'.2.d'])
        self.assertNotIn('斯大林格勒',visit);self.assertEqual(visit.count('[217.GetName]'),4)
        gfx=(ROOT.parent/'1521695605/interface/kaiserreich/event_pictures.gfx').read_text(encoding='utf-8-sig')
        for event in EVENTS.values():self.assertIn('"'+event.value('picture')+'"',gfx)

if __name__=='__main__':unittest.main(verbosity=2)
