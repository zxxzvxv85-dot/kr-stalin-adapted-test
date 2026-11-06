"""Protect native projects while retiring the provisional industrial panels."""
import re
import subprocess
import unittest
from generate_provisional_industry_gui import ROOT, CATEGORY, DECISIONS, CATEGORIES, render
from hoi4_politics_blocks import parse
from national_plan import FX

BASELINE = 'f68786f'


def old(path):
    return subprocess.check_output(['git', '-C', str(ROOT), 'show', BASELINE+':'+path]).decode('utf-8-sig')


def gameplay(text):
    # Only the retired overview/filter/refresh are exempt from native AST equality.
    text = re.sub(r'RUS_rc_refresh\s*=\s*yes', '', text)
    text = re.sub(r'RUS_rc_show_\w+\s*=\s*yes', '', text)
    text = re.sub(r'NOT\s*=\s*\{\s*RUS_np_context\s*=\s*yes\s*\}', 'RUS_np_context = no', text)
    nodes = parse(text)
    def clean(ns, depth=0):
        result = []
        for n in ns:
            if n.k == 'RUS_rc_overview' or (n.k == 'visible' and n.v == []):
                continue
            result.append((n.k, n.op, clean(n.v, depth+1) if isinstance(n.v, list) else n.v))
        # Decision field order has no meaning; effect statement order does.
        return sorted(result, key=repr) if depth == 2 else result
    return clean(nodes)


class Tests(unittest.TestCase):
    def test_native_gameplay_and_plan_rewards_preserved(self):
        outputs = render()
        self.assertEqual(gameplay(old(DECISIONS)), gameplay(outputs[DECISIONS]))
        # Account policy may evolve; only the retired panel's project rewards
        # belong to this regression. Account/refresh changes have their own tests.
        account = {'RUS_np_initialize', 'RUS_np_refresh', 'RUS_np_daily'}
        def effects(text):
            return '\n'.join(n.raw() for n in parse(text) if n.k not in account)
        self.assertEqual(gameplay(effects(old(FX))), gameplay(effects(outputs[FX])))
        # The original plan score and spirit scripts are outside generator ownership.
        self.assertNotIn('common/ideas/RUS stalin first five year plan ideas.txt', outputs)

    def test_no_attached_panels_or_reserved_space(self):
        outputs = render()
        category = next(n for n in parse(outputs[CATEGORIES]) if n.k == CATEGORY)
        self.assertIsNone(category.one('scripted_gui'))
        self.assertIsNone(category.one('picture'))
        for path in ('interface/RUS_provisional_industry.gui',
                     'interface/RUS_provisional_industry.gfx',
                     'common/scripted_guis/RUS_provisional_industry_gui.txt',
                     'common/on_actions/RUS_provisional_industry_on_actions.txt',
                     'common/scripted_effects/RUS_provisional_industry_effects.txt'):
            self.assertEqual(parse(outputs[path]), [], path)
        # Every other category is untouched.
        before = [n.norm() for n in parse(old(CATEGORIES)) if n.k != CATEGORY]
        after = [n.norm() for n in parse(outputs[CATEGORIES]) if n.k != CATEGORY]
        self.assertEqual(before, after)

    def test_no_stranded_filters_or_polling_and_keep_completion_credit(self):
        outputs = render()
        runtime = '\n'.join(v for k, v in outputs.items() if k.startswith(('common/', 'interface/')))
        for retired in ('RUS_rc_refresh', 'RUS_rc_filter', 'RUS_rc_show_', 'RUS_rc_dashboard', 'RUS_rc_overview'):
            self.assertNotIn(retired, runtime)
        category = next(n for n in parse(outputs[DECISIONS]) if n.k == CATEGORY)
        legacy = [n for n in category.v if n.k.startswith('RUS_') and not n.k.startswith('RUS_np_') and n.one('days_remove') and n.one('remove_effect')]
        self.assertEqual(len(legacy), 46)
        for n in legacy:
            self.assertIn('set_country_flag = RUS_rc_finished_'+n.k, n.one('remove_effect').raw())

    def test_blank_old_intro_and_preserved_national_plan_ledger(self):
        outputs = render()
        for lang in ('simp_chinese', 'english', 'russian'):
            loc = outputs[f'localisation/{lang}/RUS_national_plan_l_{lang}.yml']
            self.assertIn('RUS_np_header_old:0 ""', loc)
            header = next(line for line in loc.splitlines() if 'RUS_np_header:0' in line)
            self.assertIn('[?RUS_np_available|2]', header)
            self.assertIn('[?RUS_np_slots|0]', header)
        self.assertIn('RUS_rc_stalin_phase = {', outputs['common/scripted_triggers/RUS_provisional_industry_triggers.txt'])

    def test_generation_matches_and_is_idempotent(self):
        outputs = render()
        self.assertEqual(outputs, render())
        for path, text in outputs.items():
            self.assertEqual((ROOT/path).read_text(encoding='utf-8-sig'), text, path)


if __name__ == '__main__':
    unittest.main(verbosity=2)
