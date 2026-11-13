"""Exercise decree timing and single-award semantics with the shared event harness."""
import subprocess
from pathlib import Path
from PIL import Image
from hoi4_politics_blocks import load, parse
import red_army_decree_content as build
import test_football_event as harness

ROOT = Path(__file__).resolve().parents[1]


class World(harness.World):
    def condition(self, nodes):
        flattened = []
        for node in nodes:
            flattened.extend(node.v if node.k == 'hidden_trigger' else [node])
        return super().condition(flattened)


def main():
    for path, data in build.outputs().items():
        assert (ROOT/path).read_bytes() == data, path
    harness.EVENTS = {n.value('id'): n for n in load(ROOT/'events/RUS_red_army_decree.txt') if n.k == 'country_event'}
    event = harness.EVENTS[build.EVENT_ID]
    assert event.value('is_triggered_only') == event.value('fire_only_once') == 'yes'
    focus = next(n for n in load(ROOT/'common/national_focus/00_RUS_future_domestic_skeleton.txt') if n.value('id') == 'RUS_future_domestic_142')
    original = subprocess.check_output(['git','show','a589d1a:common/national_focus/00_RUS_future_domestic_skeleton.txt'], cwd=ROOT).decode('utf-8-sig')
    baseline = next(n for n in parse(original) if n.value('id') == 'RUS_future_domestic_142')
    assert [n.norm() for n in focus.v if n.k != 'completion_reward'] == [n.norm() for n in baseline.v if n.k != 'completion_reward']
    w = World()
    w.run(focus.one('completion_reward').v)
    assert w.political_power == 110 and w.stability == .5
    # Replaying the outgoing hook must not enqueue a duplicate decree.
    w.run(parse('\n'.join(build.focus_reward())))
    assert w.queue == [(3, build.EVENT_ID)]
    w.advance(2)
    assert not w.popups
    w.advance(1)
    assert w.popups == [build.EVENT_ID] and w.stability == .5
    w.confirm()
    assert w.stability == .55 and build.FLAG in w.flags
    w.run(event.one('option').v)
    assert w.stability == .55
    assert event.one('option').one('effect_tooltip').value('add_stability') == '0.05'
    assert build.TEXT.startswith('[?global.date.GetDateStringNoHourLong]')
    for lang in ('simp_chinese','english','russian'):
        assert (ROOT/f'localisation/{lang}/RUS_red_army_decree_l_{lang}.yml').read_bytes().startswith(b'\xef\xbb\xbf')
    with Image.open(ROOT/'gfx/event_pictures/RUS_red_army_decree.png') as im:
        assert im.size == (210,176) and im.mode == 'RGBA'
        assert im.getchannel('A').getextrema() == (0,255)
    print('PASS: story-only focus unchanged, day 2/3 boundary, one queue, native preview and one +5% reward, dynamic date, generated prose and KR sprite.')


if __name__ == '__main__':
    main()
