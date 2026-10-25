"""Execute the delayed football report while preserving the preview focus boundary."""
import copy
import hashlib
import re
import subprocess
from PIL import Image
from hoi4_politics_blocks import load, parse
from hoi4_bitmap_fonts import font_data, measure
import football_event_content as build

ROOT = build.ROOT
EVENTS = {n.value('id'): n for n in load(ROOT/build.EVENT) if n.k == 'country_event'}


class World:
    def __init__(self, tag='RUS'):
        self.tag = tag
        self.flags = set()
        self.focuses = {'RUS_future_domestic_151'}
        self.day = 0
        self.queue = []
        self.popups = []
        self.fired = set()

    def condition(self, nodes):
        def one(n):
            if n.k == 'tag': return self.tag == n.v
            if n.k == 'has_country_flag': return n.v in self.flags
            if n.k == 'has_completed_focus': return n.v in self.focuses
            if n.k == 'NOT': return not any(one(x) for x in n.v)
            raise AssertionError(n.k)
        return all(one(n) for n in nodes)

    def run(self, nodes):
        for n in nodes:
            if n.k == 'hidden_effect': self.run(n.v)
            elif n.k == 'if':
                if self.condition(n.one('limit').v):
                    self.run([x for x in n.v if x.k != 'limit'])
            elif n.k == 'set_country_flag': self.flags.add(n.v)
            elif n.k == 'country_event': self.queue.append((self.day+int(n.value('days') or 0), n.value('id')))
            elif n.k != 'name': raise AssertionError(n.k)

    def advance(self, days):
        self.day += days
        while any(d <= self.day for d,k in self.queue):
            index = next(i for i,(d,k) in enumerate(self.queue) if d <= self.day)
            _, key = self.queue.pop(index)
            if key in self.fired: continue
            self.fired.add(key)
            event = EVENTS[key]
            # Explicit delivery deliberately ignores event.trigger in this model.
            if event.value('hidden') == 'yes': self.run(event.one('immediate').v)
            else: self.popups.append(key)

    def confirm(self):
        self.run(EVENTS[self.popups.pop(0)].one('option').v)
        self.advance(0)


def main():
    for p,data in build.outputs().items(): assert (ROOT/p).read_bytes() == data,p
    focuses = {n.value('id'): n for n in load(ROOT/'common/national_focus/00_RUS_future_domestic_skeleton.txt')}
    focus = focuses['RUS_future_domestic_151']
    baseline = subprocess.check_output(['git','show','65a62fb:common/national_focus/00_RUS_future_domestic_skeleton.txt'],cwd=ROOT).decode()
    original = next(n for n in parse(baseline) if n.value('id') == 'RUS_future_domestic_151')
    assert [n.norm() for n in focus.v if n.k != 'completion_reward'] == [n.norm() for n in original.v if n.k != 'completion_reward']
    reward = focus.one('completion_reward').v
    w = World(); w.run(reward); w.run(reward)
    assert w.queue == [(7,'RUS_football.0')]
    w.advance(6); assert not w.popups
    w.advance(1); assert w.popups == ['RUS_football.1']
    for index in (2,3):
        w.confirm(); assert w.popups == [f'RUS_football.{index}']
    w.confirm(); assert not w.popups and 'RUS_football_done' in w.flags
    state = copy.deepcopy(w.__dict__)
    w.run(EVENTS['RUS_football.3'].one('option').v); w.run(reward)
    assert w.__dict__ == state
    w = World('FER'); w.run(reward); assert not w.queue
    w = World(); w.run(reward); w.focuses.clear(); w.advance(7); assert not w.popups
    w = World(); w.run(EVENTS['RUS_football.2'].one('option').v); assert not w.queue and not w.flags
    spec = build.content()
    assert len(EVENTS) == 4 and len(spec['pages']) == 3
    assert ''.join(spec['pages']).replace('\n','') == ''.join(spec['paragraphs'])
    line_height = max(f['height'] for f in font_data('hoi4_typewriter16'))
    for index,page in enumerate(spec['pages'],1):
        lines = 0
        for paragraph in page.split('\n'):
            width = 0; lines += 1
            for c in paragraph:
                advance = measure('hoi4_typewriter16',c)
                if width+advance > 512: lines += 1; width = 0
                width += advance
        assert lines*line_height <= 230
        assert measure('hoi4_typewriter22',spec['title']+f'（{index}/3）') <= 551
    assert measure('hoi4_typewriter16',spec['option']) <= 512
    for lang in ('simp_chinese','english','russian'):
        p = ROOT/f'localisation/{lang}/RUS_football_l_{lang}.yml'
        assert p.read_bytes().startswith(b'\xef\xbb\xbf')
        text = p.read_text(encoding='utf-8-sig')
        keys = re.findall(r'^ (\w+[.\w]*):0 ',text,re.M)
        assert len(keys) == len(set(keys)) == 9
    picture = ROOT/spec['picture_path']
    assert hashlib.sha256(picture.read_bytes()).hexdigest() == spec['picture_sha256']
    image = Image.open(picture)
    assert image.size == (210,176) and image.mode == 'RGBA'
    assert image.getchannel('A').getextrema() == (0,255)
    assert any(n.value('name').strip('"') == spec['picture'] for n in load(ROOT/build.GFX)[0].v)
    print('PASS: day 6/7, one schedule, three pages, guards/repeat completion, preserved preview focus, exact prose, font bounds and photograph.')


if __name__ == '__main__':
    main()
