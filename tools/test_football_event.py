"""Execute the delayed football report while preserving the preview focus boundary."""
import copy
import hashlib
import re
import subprocess
from PIL import Image
from hoi4_politics_blocks import load, parse
from hoi4_bitmap_fonts import measure
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
        self.stability = 0.5
        self.political_power = 100

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
            elif n.k == 'add_stability': self.stability += float(n.v)
            elif n.k == 'add_political_power': self.political_power += float(n.v)
            elif n.k == 'effect_tooltip': pass  # Display only; never execute rewards twice.
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
    assert w.stability == 0.5 and w.political_power == 100
    w.confirm(); assert not w.popups and 'RUS_football_done' in w.flags
    assert w.stability == 0.52 and w.political_power == 105
    state = copy.deepcopy(w.__dict__)
    w.run(EVENTS['RUS_football.1'].one('option').v); w.run(reward)
    assert w.__dict__ == state
    w = World('FER'); w.run(reward); assert not w.queue
    w = World(); w.run(reward); w.focuses.clear(); w.advance(7); assert not w.popups
    # Console preview can award the requested effects without scheduling flags.
    option = EVENTS['RUS_football.1'].one('option')
    w = World(); w.focuses.clear(); w.run(option.v)
    assert not w.queue and 'RUS_football_done' in w.flags
    assert w.stability == 0.52 and w.political_power == 105
    w = World('FER'); w.run(option.v)
    assert not w.flags and w.stability == 0.5 and w.political_power == 100
    preview = option.one('effect_tooltip')
    assert preview.value('add_stability') == '0.02' and preview.value('add_political_power') == '5'
    assert len(preview.v) == 2
    spec = build.content()
    assert set(EVENTS) == {'RUS_football.0','RUS_football.1'}
    import json
    text = (ROOT/'localisation/simp_chinese/RUS_football_l_simp_chinese.yml').read_text(encoding='utf-8-sig')
    loc = {k:json.loads(v) for k,v in re.findall(r'^ ([\w.]+):0 (.+)$',text,re.M)}
    assert loc['RUS_football.1.d'] == '\n\n'.join(spec['paragraphs'])
    assert loc['RUS_football.1.t'] == spec['title']
    assert loc['RUS_football.1.a'] == spec['option']
    assert '继续阅读' not in text and 'RUS_football.2' not in text and 'RUS_football.3' not in text
    assert measure('hoi4_typewriter22',spec['title']) <= 551
    assert measure('hoi4_typewriter16',spec['option']) <= 512
    for lang in ('simp_chinese','english','russian'):
        p = ROOT/f'localisation/{lang}/RUS_football_l_{lang}.yml'
        assert p.read_bytes().startswith(b'\xef\xbb\xbf')
        text = p.read_text(encoding='utf-8-sig')
        keys = re.findall(r'^ (\w+[.\w]*):0 ',text,re.M)
        assert len(keys) == len(set(keys)) == 3
    picture = ROOT/spec['picture_path']
    assert hashlib.sha256(picture.read_bytes()).hexdigest() == spec['picture_sha256']
    image = Image.open(picture)
    assert image.size == (210,176) and image.mode == 'RGBA'
    assert image.getchannel('A').getextrema() == (0,255)
    assert any(n.value('name').strip('"') == spec['picture'] for n in load(ROOT/build.GFX)[0].v)
    print('PASS: day 6/7, one window/option, native +2% stability/+5 PP preview and single reward, console/foreign guards, preserved preview focus, prose and photograph.')


if __name__ == '__main__':
    main()
