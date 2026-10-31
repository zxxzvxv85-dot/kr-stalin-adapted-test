"""Presentation compatibility contracts; does not simulate the native filter engine."""
import re
import unittest
from PIL import Image
from generate_advisor_categories import ROOT, KR, TRAITS, ATLAS, CATEGORIES, child_blocks, outputs, assets


class AdvisorCategories(unittest.TestCase):
    def test_faction_overrides_preserve_all_effects(self):
        files = {}
        for root in (KR, ROOT):
            for p in sorted((root/'common/country_leader').glob('*.txt')):
                if p.name != TRAITS.split('/')[-1]:
                    files[p.name] = p
        original = {}
        for _, p in sorted(files.items()):
            original.update(child_blocks(p.read_text(encoding='utf-8-sig')))
        def tokens(block):
            block = re.sub(r'\bsprite\s*=\s*\d+', '', block)
            return re.findall(r'"(?:\\.|[^"\\])*"|[{}=]|[^\s{}=]+', re.sub(r'#[^\n]*', '', block))
        seen = set()
        for key, block in child_blocks((ROOT/TRAITS).read_text(encoding='utf-8')):
            self.assertNotIn(key, seen);seen.add(key)
            self.assertEqual(tokens(original[key]), tokens(block), key)
            frame = int(re.search(r'\bsprite\s*=\s*(\d+)', block)[1])
            self.assertTrue(key.startswith(CATEGORIES[frame-19][4]), key)

    def test_native_art_and_geometry(self):
        with Image.open(KR/'gfx/interface/ideas/idea_traits_strip.dds') as old, Image.open(ROOT/ATLAS) as new:
            self.assertEqual(new.size, (1242,46))
            self.assertEqual(old.convert('RGBA').tobytes(),new.crop((0,0,828,46)).tobytes())
        base=(KR/'interface/command_character_view.gui').read_text(encoding='utf-8-sig')
        current=(ROOT/'interface/command_character_view.gui').read_text(encoding='utf-8').split('\n',1)[1]
        current=current.replace('position = { x = 0 y = 143 }','position = { x = 0 y = 98 }').replace('size = { width=100% height=95 }','size = { width=100% height=50 }').replace('max_slots_horizontal = 10','max_slots_horizontal = 8')
        self.assertEqual(current,base)
        self.assertLessEqual(12+10*45,500*.97)
        self.assertLessEqual(4+2*45,95)

    def test_outputs_and_translations_current(self):
        data,_=outputs()
        for name,text in data.items():
            p=ROOT/name
            self.assertEqual(p.read_text(encoding='utf-8-sig'),text,name)
            if name.endswith('.yml'):
                self.assertTrue(p.read_bytes().startswith(b'\xef\xbb\xbf'))
                keys=re.findall(r'^ (ADVISOR_CATEGORY_\d+):',text,re.M)
                self.assertEqual(len(keys),9);self.assertEqual(len(set(keys)),9)
        assets(False)


if __name__ == '__main__':
    unittest.main()
