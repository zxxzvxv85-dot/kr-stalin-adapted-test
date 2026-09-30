"""Current advisor/route contracts after the approved 2026-09-15 rollback.

The former 'all shared content equals KR' assertion described the explicitly
reverted 09-14 design. These checks exercise the restored custom policy instead.
"""
from itertools import product
from hoi4_politics_blocks import R, data, load, roles, tokens
import re

locks={n.k:n for n in load(R/'common/scripted_triggers/RUS_stalin_advisor_lock_triggers.txt')}
def check(nodes,state):
 def one(n):
  if n.k=='tooltip':return True
  if n.k in {'AND','custom_override_tooltip','hidden_trigger'}:return check(n.v,state)
  if n.k=='OR':return any(one(x) for x in n.v)
  if n.k=='NOT':return not check(n.v,state)
  if n.k=='has_country_flag':return n.v in state['flags']
  if n.k=='has_completed_focus':return n.v in state['focuses']
  if n.k=='original_tag':return state['tag']==n.v
  if n.k=='RUS_is_maximalist':return state['maximalist']==(n.v=='yes')
  if n.k=='check_variable':
   return all((state['balance']<float(x.v) if x.op=='<' else state['balance']>float(x.v)) for x in n.v)
  if n.k in locks:return check(locks[n.k].v,state)==(n.v=='yes')
  raise AssertionError(('Unsupported advisor trigger',n.k))
 return all(one(n) for n in nodes)

cases=0
for collapse,active,deal,alliance,maximalist,mantle in product([False,True],repeat=6):
 for balance in [0,74,75,100]:
  flags={name for name,on in [('RUS_stalin_psr_balance_collapse_done',collapse),('RUS_kamenev_bop_active',active),('RUS_VST_MAX_deal',deal),('RUS_maximalist_bolshevik_alliance',alliance),('RUS_mantle_of_the_srs_advisor_lock',mantle)] if on}
  state=dict(flags=flags,focuses=set(),tag='RUS',maximalist=maximalist,balance=balance)
  psr=not collapse and not mantle and (not active or balance<75)
  assert check(locks['RUS_stalin_can_hire_psr_advisor'].v,state)==psr
  assert check(locks['RUS_stalin_can_hire_bolshevik_advisor'].v,state)==(not collapse)
  assert check(locks['RUS_stalin_can_hire_maximalist_advisor'].v,state)==(not collapse and (maximalist or deal or alliance or psr))
  cases+=1
for tag,unlocked in product(['RUS','FRA'],[False,True]):
 state=dict(flags={'RUS_kamenev_post_election_advisors_unlocked'} if unlocked else set(),focuses=set(),tag=tag,maximalist=False,balance=0)
 assert check(locks['RUS_kamenev_post_election_advisors_unlocked'].v,state)==(tag!='RUS' or unlocked)

characters=R/'common/characters/RUS characters.txt'
rolemap=roles(data(characters,'characters'))
for slug,character in [('sverdlov','yakov_sverdlov'),('ustinov','aleksey_ustinov'),('kolegayev','andrey_kolegayev'),('kakhovskaya','irina_kakhovskaya')]:
 _,advisor=rolemap[('RUS_'+character,'RUS_'+character+'_advisor')]
 assert 'RUS_relationship_display_'+slug in tokens(advisor.one('traits'))
 assert advisor.one('available').one('RUS_kamenev_post_election_advisors_unlocked').v=='yes'
 assert 'RUS_stalin_psr_balance_collapse_done' in advisor.one('available').raw()
assert rolemap['RUS_aleksey_ustinov','RUS_aleksey_ustinov_advisor'][1].value('cost')=='100'
# The withdrawn blanket route restriction must not return before the election.
for path in [characters,R/'events/RUS events (Russia).txt']:
 assert 'RUS_uses_kamenev_politics' not in path.read_text(encoding='utf-8-sig'),path

focuses=data(R/'common/national_focus/RUS focus (Russia).txt','focus_tree').children('focus')
entry=[n for n in focuses if 'set_country_flag = RUS_auto_kamenev_vst_left_path' in (n.one('completion_reward').raw() if n.one('completion_reward') else '')]
assert len(entry)==1
reward=entry[0].one('completion_reward').raw()
for marker in ['vst_left_var > 7','vst_centre_unity > 3','russia_socialist_events.442','RUS_auto_kamenev_vst_left_path']:
 assert marker in reward,marker
for path in (R/'common/on_actions').glob('RUS*.txt'):
 assert not re.search(r'set_country_flag\s*=\s*RUS_auto_kamenev_vst_left_path',path.read_text(encoding='utf-8-sig')),path
for language in ['simp_chinese','english','russian']:
 path=R/f'localisation/{language}/RUS_kamenev_politics_l_{language}.yml'
 assert path.read_bytes().startswith(b'\xef\xbb\xbf')
 keys=re.findall(r'^ ([^:]+):',path.read_text(encoding='utf-8-sig'),re.M)
 assert len(keys)==len(set(keys))
print(f'PASS: {cases} advisor lock boundaries, election unlock, restored custom advisor defaults, single focus route entry and localization; no HOI4 runtime claim.')
