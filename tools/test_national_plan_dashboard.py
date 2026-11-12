"""Exercise real generated filter callbacks, read-only observers and asset contracts."""
import unittest,re,json
from PIL import Image
from national_plan_dashboard import ROOT,P,ART,SECTORS,sector,LABELS
from national_plan_catalog import PROJECTS
from generate_provisional_industry_gui import render
from hoi4_politics_blocks import parse
from test_national_plan import Model,NODES

class DashboardTests(unittest.TestCase):
    def test_all_62_projects_partitioned_and_no_extra_scheduler(self):
        self.assertEqual(len(PROJECTS),62)
        self.assertTrue(all(sector(p) in SECTORS for p in PROJECTS))
        out=render()
        self.assertNotIn('common/on_actions/RUS_national_plan_dashboard.txt',out)
        anchor=NODES[P+'open_ledger']
        self.assertNotIn('RUS_np_filter',anchor.one('visible').raw())
        self.assertNotIn(P+'sector',anchor.one('visible').raw())
        for p in PROJECTS:
            visible=NODES[p['id']].one('visible').raw()
            self.assertIn(f'{P}sector = {sector(p)}',visible)
            self.assertIn('RUS_np_filter = '+str(p['region']),visible)

    def test_actual_callbacks_toggle_region_sector_and_reset_without_spending(self):
        out=render();node=parse(out['common/scripted_guis/RUS_national_plan_dashboard.txt'])[0].v[0]
        m=Model();m.initialize()
        callbacks={n.k:n for n in node.one('effects').v}
        m.effects.update(callbacks)
        values={k:v for k,v in m.vars.items() if not k.startswith(P) and k!='RUS_np_filter'}
        for i in range(1,7):
            m.call(f'region_{i}_click');self.assertEqual(m.vars['RUS_np_filter'],i)
            m.call(f'region_{i}_click');self.assertEqual(m.vars['RUS_np_filter'],0)
        for i in range(1,5):
            m.call(f'sector_{i}_click');self.assertEqual(m.vars[P+'sector'],i)
            m.call(f'sector_{i}_click');self.assertEqual(m.vars[P+'sector'],0)
        m.call('sector_2_click');m.call('region_4_click');m.call('all_click')
        self.assertEqual(m.vars[P+'sector'],0);self.assertEqual(m.vars['RUS_np_filter'],0)
        self.assertEqual(values,{k:v for k,v in m.vars.items() if not k.startswith(P) and k!='RUS_np_filter'})
        m.call('ledger_toggle_click');self.assertIn(P+'ledger_open',m.flags)
        m.call('ledger_close_click');self.assertNotIn(P+'ledger_open',m.flags)

    def test_observer_counts_follow_region_and_completion_without_mutating_projects(self):
        m=Model();m.initialize()
        for p in PROJECTS:
            m.flags.add('RUS_np_'+p['key']+'_running')
            m.flags.add('RUS_np_'+p['key']+'_completed')
        before=m.flags.copy()
        for region in range(7):
            m.vars['RUS_np_filter']=region;m.call('RUS_np_refresh')
            for i in SECTORS:
                expected=sum(sector(p)==i and (region==0 or p['region']==region) for p in PROJECTS)
                self.assertEqual(m.vars[P+'active_'+str(i)],expected)
                self.assertEqual(m.vars[P+'done_'+str(i)],expected)
        self.assertEqual(m.flags,before)

    def test_native_animation_sheets_and_localisation_bindings(self):
        out=render();gfx=parse(out['interface/RUS_national_plan_dashboard.gfx'])[0]
        for n in gfx.v:
            path=n.value('texturefile').strip('"');im=Image.open(ROOT/path)
            frames=int(n.value('noOfFrames'))
            self.assertEqual(im.width%frames,0,path)
            if n.k=='frameAnimatedSpriteType':
                self.assertEqual(frames,24);self.assertEqual(n.value('looping'),'yes')
                self.assertGreater(im.getchannel('A').getextrema()[1],0)
            im.close()
        loc=out['localisation/simp_chinese/RUS_national_plan_dashboard_l_simp_chinese.yml']
        for row in LABELS:self.assertIn(' '+row[6]+':0 ',loc)
        self.assertIn('RUS_first_five_year_plan_score|1',loc)
        self.assertIn('RUS_np_pending_plan_score|1',loc)
        self.assertEqual(out,render())

if __name__=='__main__':unittest.main(verbosity=2)
