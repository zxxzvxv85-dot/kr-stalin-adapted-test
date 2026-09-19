"""Check the actual reorganisation options and focus gates."""
from hoi4_politics_blocks import R, load

event = next(n for n in load(R / 'events/RUS events (Russia).txt')
             if n.k == 'country_event' and n.value('id') == 'russia_events.578')
focuses = {n.value('id'): n for n in load(R / 'common/national_focus/00_RUS_future_foreign_policy_skeleton.txt')
           if n.k == 'shared_focus'}
for suffix, number, flag in [('a', '023', 'RUS_central_asia_separate_republics'),
                             ('b', '024', 'RUS_central_asia_federation')]:
    option = next(n for n in event.children('option') if n.value('name') == 'russia_events.578.' + suffix)
    focus_id = 'RUS_future_foreign_' + number
    assert option.value('set_country_flag') == flag
    assert [n.v for n in option.children('complete_national_focus')] == [focus_id]
    focus = focuses[focus_id]
    assert focus.one('prerequisite').value('focus') == 'RUS_future_foreign_009'
    gate = focus.one('available').one('custom_trigger_tooltip')
    assert gate.value('has_country_flag') == flag
    other = 'RUS_future_foreign_' + ('024' if number == '023' else '023')
    assert focus.one('mutually_exclusive').value('focus') == other
    for lang in ['simp_chinese', 'english', 'russian']:
        path = R / f'localisation/{lang}/RUS_central_asia_choices_l_{lang}.yml'
        assert path.read_bytes().startswith(b'\xef\xbb\xbf')
        assert path.read_text(encoding='utf-8-sig').count(gate.value('tooltip') + ':') == 1
print('PASS: both event choices complete only the matching focus; choice gates, prerequisite links, mutual exclusion and 3 language tooltips match.')
