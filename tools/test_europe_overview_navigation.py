"""Check fixed navigation ownership and actual country-filter callbacks."""
import argparse
import sys
import unittest
from pathlib import Path
from hoi4_politics_blocks import load
from doudizhu_script_model import ScriptModel, load_effects
from repair_europe_overview_navigation import ROOT,GUI,SCRIPT,BUTTON,render

TARGET = ROOT


class NavigationTests(unittest.TestCase):
    def nodes(self):
        windows = {n.value('name').strip('"'): n for n in load(TARGET/GUI)[0].v}
        modules = {n.k: n for n in load(TARGET/SCRIPT)[0].v}
        return windows, modules

    def test_overview_stays_inside_fixed_header_outside_map_scroll(self):
        windows, modules = self.nodes()
        header = windows['RUS_europe_intervention_header_window']
        button = next(n for n in header.children('buttonType') if n.value('name').strip('"')==BUTTON)
        position, size = button.one('position'), header.one('size')
        self.assertGreaterEqual(int(position.value('x')),0)
        self.assertGreaterEqual(int(position.value('y')),0)
        self.assertLessEqual(int(position.value('x'))+88,int(size.value('width')))
        self.assertLessEqual(int(position.value('y'))+32,int(size.value('height')))
        title=next(n for n in header.children('instantTextBoxType') if n.value('name').strip('"').endswith('header_title'))
        self.assertLessEqual(int(title.one('position').value('x'))+int(title.value('maxWidth')),int(position.value('x')))
        self.assertFalse(any(n.value('name','').strip('"')==BUTTON for n in windows['RUS_europe_intervention_window'].v))
        fixed = modules['RUS_europe_intervention_header_gui']
        self.assertEqual(fixed.value('window_name').strip('"'),'RUS_europe_intervention_header_window')
        self.assertIsNotNone(fixed.one('triggers').one(BUTTON+'_click_enabled'))
        self.assertIsNotNone(fixed.one('effects').one(BUTTON+'_click'))
        scroll = modules['RUS_europe_intervention_gui']
        self.assertIsNone(scroll.one('effects').one(BUTTON+'_click'))

    def test_every_country_selection_returns_to_overview_and_preserves_other_flags(self):
        _, modules = self.nodes()
        effects = load_effects((TARGET/'common/scripted_effects/RUS_europe_intervention_effects.txt').read_text(encoding='utf8'))
        m = ScriptModel(effects)
        preserved = {'RUS_europe_intervention_molotov_selected','RUS_europe_intervention_gui_unlocked','unrelated_route_flag'}
        m.flags.update(preserved)
        header = modules['RUS_europe_intervention_header_gui']
        enabled = header.one('triggers').one(BUTTON+'_click_enabled')
        reset = header.one('effects').one(BUTTON+'_click')
        callbacks = modules['RUS_europe_intervention_gui'].one('effects').v
        self.assertGreater(len(callbacks),50)
        for callback in callbacks:
            m.run(callback.v)
            self.assertTrue(m.check(enabled),callback.k)
            m.run(reset.v)
            self.assertEqual(m.flags,preserved,callback.k)
            self.assertFalse(m.check(enabled))
            m.run(reset.v)
            self.assertEqual(m.flags,preserved)

    def test_navigation_transform_matches_files_and_is_idempotent(self):
        outputs=render(TARGET)
        for path,text in outputs.items():
            self.assertEqual((TARGET/path).read_text(encoding='utf8'),text,path)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=ROOT)
    args, remaining=parser.parse_known_args()
    TARGET=args.root
    unittest.main(argv=[sys.argv[0],*remaining],verbosity=2)
