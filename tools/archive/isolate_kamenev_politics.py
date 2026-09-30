"""Archived route-isolation experiment; historical reference only.

The original implementation below executes transformations at module level.
Its broad restoration of KR advisor defaults was subsequently superseded.
Do not import or run it against the current custom advisor/Frunze records.
"""
raise RuntimeError("Archived one-shot migration; read for reference, do not execute")

from hoi4_politics_blocks import *
import subprocess,sys
BACK=R/'tmp/politics_before';INDEX=R/'tmp/politics_index';manifest=[]
ROUTE='RUS_uses_kamenev_politics'
def cond(mod,base):return f'OR = {{ AND = {{ {ROUTE} = yes {mod} }} AND = {{ {ROUTE} = no {base} }} }}'
def effect(mod,base=''):return f'if = {{ limit = {{ {ROUTE} = yes }} {mod} }}\nelse = {{ {base} }}'
def edits(s,changes):
 for a,b,v in sorted(changes,reverse=True):s=s[:a]+v+s[b:]
 return s
def fields(n,changes):
 s=n.raw();es=[]
 for k,v in changes.items():
  old=n.children(k)
  if old:
   es.append((old[0].a-n.a,old[0].b-n.a,v))
   for x in old[1:]:es.append((x.a-n.a,x.b-n.a,''))
  elif v:es.append((len(s)-1,len(s)-1,'\n'+v+'\n'))
 return edits(s,es)
def change(path,fn):
 p=R/path;before=p.read_bytes();backup=BACK/path
 assert not backup.exists(),f'Already migrated: {path}'
 backup.parent.mkdir(parents=True,exist_ok=True);backup.write_bytes(before)
 after=fn(before.decode('utf-8-sig'));p.write_text(after,encoding='utf-8')
 # Transform the committed version independently; unrelated working changes stay unstaged.
 head=subprocess.run(['git','show','HEAD:'+path],cwd=R,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if head.returncode==0:
  indexed=fn(head.stdout.decode('utf-8-sig'));out=INDEX/path;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(indexed,encoding='utf-8')
 manifest.append(path)
def new(path,s,bom=False):
 p=R/path;assert not p.exists(),path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s.strip()+'\n',encoding='utf-8-sig' if bom else 'utf-8');manifest.append(path)
BASECHARS=data(KR/'common/characters/RUS characters.txt','characters');BR=roles(BASECHARS)
original_mod=data(R/'common/characters/RUS characters.txt','characters');MR=roles(original_mod)
trait_pairs=[]
def chars(s):
 root=next(x for x in parse(s) if x.k=='characters');es=[]
 for key,(c,a) in roles(root).items():
  if a.value('slot') not in ['political_advisor','second_in_command']:continue
  if key not in BR:
   v=a.one('visible');old=v.inner() if v else ''
   es.append((a.a,a.b,fields(a,{'visible':f'visible = {{ {ROUTE} = yes {old} }}'})));continue
  b=BR[key][1];repl={}
  for k in ['available','visible']:
   am=a.one(k);ab=b.one(k)
   if (am.norm() if am else None)!=(ab.norm() if ab else None):repl[k]=f'{k} = {{ '+cond(am.inner() if am else '',ab.inner() if ab else '')+' }'
  # allowed is evaluated when roles are loaded, so do not put route flags there.
  if [x.norm() for x in a.children('allowed')]!=[x.norm() for x in b.children('allowed')]:
   repl['allowed']=b.one('allowed').raw() if b.one('allowed') else ''
   am=a.one('allowed')
   if am:repl['available']=f'available = {{ '+cond((a.one('available').inner() if a.one('available') else '')+am.inner(),b.one('available').inner() if b.one('available') else '')+' }'
  for k in ['on_add','on_remove']:
   am=a.one(k);ab=b.one(k)
   if (am.norm() if am else None)!=(ab.norm() if ab else None):repl[k]=f'{k} = {{ '+effect(am.inner() if am else '',ab.inner() if ab else '')+' }'
  if tokens(a.one('traits'))!=tokens(b.one('traits')):repl['traits']=b.one('traits').raw() if b.one('traits') else 'traits = { }'
  if a.value('desc')!=b.value('desc'):repl['desc']=b.one('desc').raw() if b.one('desc') else ''
  if repl:es.append((a.a,a.b,fields(a,repl)))
 return edits(s,es)
for key,(c,a) in MR.items():
 if key in BR and a.value('slot') in ['political_advisor','second_in_command']:
  b=BR[key][1];old=tokens(b.one('traits'));custom=tokens(a.one('traits'))
  if old!=custom:trait_pairs.append((key[0],a.value('slot'),old,custom))
new('common/scripted_triggers/RUS_kamenev_politics_triggers.txt',f'''# A VST party score alone is not entry into this route.
{ROUTE} = {{ RUS = {{ OR = {{
 has_country_flag = RUS_auto_kamenev_vst_left_path
 AND = {{ has_country_flag = RUS_kamenev_politics_entered has_country_flag = RUS_stalin_communist_path }}
}} }} }}''')
change('common/characters/RUS characters.txt',chars)
fx='''RUS_sync_political_advisor_route = {
 if = { limit = { RUS_uses_kamenev_politics = yes }
  set_country_flag = RUS_kamenev_politics_entered
 }
'''
for char,slot,base,custom in trait_pairs:
 flag=f'RUS_route_traits_{char}_{slot}';stock=flag+'_kr'
 fx+=f' if = {{ limit = {{ has_character = {char} }}\n'
 for idx,(route,done,clear,remove,add) in enumerate([(True,flag,stock,set(base)-set(custom),set(custom)-set(base)),(False,stock,flag,set(custom)-set(base),set(base)-set(custom))]):
  fx+=f'  {"if" if idx==0 else "else_if"} = {{ limit = {{ {ROUTE} = {"yes" if route else "no"} NOT = {{ has_country_flag = {done} }} }}\n'
  for t in sorted(remove):fx+=f'   remove_trait = {{ character = {char} slot = {slot} trait = {t} }}\n'
  for t in sorted(add):fx+=f'   add_trait = {{ character = {char} slot = {slot} trait = {t} }}\n'
  fx+=f'   set_country_flag = {done}\n   clr_country_flag = {clear}\n  }}\n'
 fx+=' }\n'
fx+=''' if = { limit = { RUS_uses_kamenev_politics = no NOT = { has_country_flag = RUS_kr_advisor_cleanup_done } }
  RUS_stalin_clear_rkp_advisor_trait_tiers = yes
  RUS_stalin_clear_psr_advisor_trait_tiers = yes
  RUS_stalin_clear_max_advisor_trait_tiers = yes
  clr_country_flag = RUS_relationship_advisor_traits_initialised
  set_country_flag = RUS_kr_advisor_cleanup_done
 }
 if = { limit = { RUS_uses_kamenev_politics = yes } clr_country_flag = RUS_kr_advisor_cleanup_done }
}
'''
new('common/scripted_effects/RUS_kamenev_politics_effects.txt',fx)
new('common/on_actions/RUS_kamenev_politics_on_actions.txt','''on_actions = {
 on_startup = { effect = { RUS = { RUS_sync_political_advisor_route = yes } } }
 on_daily = { effect = { if = { limit = { original_tag = RUS } RUS_sync_political_advisor_route = yes } } }
}''')
def wrap(s,ids,pre='',after=''):
 es=[]
 for n in parse(s):
  if n.k in ids:es.append((n.a,n.b,n.k+' = {\n'+pre+'\n'+effect(n.inner(),after)+'\n}\n'))
 return edits(s,es)
change('common/scripted_effects/RUS_stalin_advisor_relationship_effects.txt',lambda s:wrap(s,{'RUS_stalin_refresh_advisor_relationship_effects','RUS_stalin_freeze_advisor_relationship_effects','RUS_stalin_remove_obsolete_kirov_vst_right_traits'},'RUS_sync_political_advisor_route = yes'))
change('common/scripted_effects/RUS_stalin_kamenev_bop_effects.txt',lambda s:wrap(s,{'RUS_stalin_enforce_kamenev_advisor_locks','RUS_stalin_sverdlov_refresh_sic_trait','RUS_stalin_kamenev_balance_refresh','RUS_stalin_kamenev_bop_refresh_runtime_effects'}))
# Preserve vanilla dynamic modifiers; custom VST effects are an explicit route-only add-on.
dynbase={x.k:x for x in load(KR/'common/dynamic_modifiers/RUS dynamic_modifiers (Russia).txt')}
def dynamic(s):return edits(s,[(n.a,n.b,dynbase[n.k].raw()) for n in parse(s) if n.k in ['RUS_vst_party_unity_modifier','RUS_vst_party_factionalism_modifier']])
change('common/dynamic_modifiers/RUS stalin dynamic_modifiers.txt',dynamic)
new('common/dynamic_modifiers/RUS_kamenev_politics_modifiers.txt','''RUS_kamenev_vst_relationship_addon = {
 enable = { RUS_uses_kamenev_politics = yes }
 political_power_gain = RUS_vst_factionalism_pp_delta
 stability_weekly = RUS_vst_factionalism_weekly_stability
 global_building_slots_factor = RUS_vst_factionalism_building_slots_factor
 production_cost_arms_factory_factor = RUS_vst_factionalism_arms_factory_cost_factor
}''')
def vst(s):
 ns=parse(s);es=[]
 for n in ns:
  body=n.inner()
  if n.k in ['RUS_stalin_refresh_vst_factionalism_dynamic_modifier','RUS_stalin_freeze_vst_factionalism_relationship_effects']:
   body+='''\nset_variable = { RUS_vst_factionalism_pp_delta = RUS_vst_factionalism_total_pp_gain }
subtract_from_variable = { RUS_vst_factionalism_pp_delta = vst_popularity_var }
if = { limit = { OR = { has_idea = RUS_vst_party_unity_idea has_idea = RUS_vst_party_streamlined_idea has_idea = RUS_vst_party_factionalism_idea } }
 add_dynamic_modifier = { modifier = RUS_kamenev_vst_relationship_addon }
}
'''
  fallback='''if = { limit = { has_dynamic_modifier = { modifier = RUS_kamenev_vst_relationship_addon } } remove_dynamic_modifier = { modifier = RUS_kamenev_vst_relationship_addon } }
if = { limit = { has_idea = RUS_vst_party_streamlined_idea } remove_dynamic_modifier = { modifier = RUS_vst_party_unity_modifier } }
'''
  es.append((n.a,n.b,n.k+' = {\n'+effect(body,fallback if n.k=='RUS_stalin_refresh_vst_factionalism_dynamic_modifier' else '')+'\n}'))
 return edits(s,es)
change('common/scripted_effects/RUS_stalin_vst_factionalism_effects.txt',vst)
def ideas(s):
 root=next(n for n in parse(s) if n.k=='ideas').one('country');base=data(KR/'common/ideas/RUS ideas (Russia).txt','ideas').one('country');es=[]
 for a in root.v:
  if a.k not in ['RUS_vst_party_unity_idea','RUS_vst_party_factionalism_idea','RUS_vst_party_streamlined_idea']:continue
  b=base.one(a.k);repl={}
  for k in ['on_add','on_remove']:
   ma=a.one(k);ba=b.one(k);repl[k]=f'{k} = {{ '+effect(ma.inner() if ma else '',ba.inner() if ba else '')+' }'
  if a.k=='RUS_vst_party_streamlined_idea':repl['modifier']=b.one('modifier').raw()
  es.append((a.a,a.b,fields(a,repl)))
 return edits(s,es)
change('common/ideas/RUS ideas (Russia).txt',ideas)
# Vanilla socialist focus effects and requirements outside the custom route.
basefocus=data(KR/'common/national_focus/RUS focus (Russia).txt','focus_tree');lo=basefocus.s.index('### Socialist Tree');hi=basefocus.s.index('### SocRus foreign policy')
BF={b.value('id'):b for b in basefocus.children('focus') if lo<b.a<hi}
def prerequisites(nodes):return '\n'.join('OR = { '+' '.join('has_completed_focus = '+n.v for n in pre.v if n.k=='focus')+' }' for pre in nodes)
def focuses(s):
 root=next(n for n in parse(s) if n.k=='focus_tree');es=[]
 for a in root.children('focus'):
  id=a.value('id');b=BF.get(id)
  if not b or id=='RUS_syndicalists':continue # route is chosen at this one entry point
  repl={}
  for k in ['completion_reward','select_effect']:
   ma=a.one(k);ba=b.one(k)
   if (ma.norm() if ma else None)!=(ba.norm() if ba else None):repl[k]=f'{k} = {{ '+effect(ma.inner() if ma else '',ba.inner() if ba else '')+' }'
  for k in ['available']:
   ma=a.one(k);ba=b.one(k)
   if (ma.norm() if ma else None)!=(ba.norm() if ba else None):repl[k]=f'{k} = {{ '+cond(ma.inner() if ma else '',ba.inner() if ba else '')+' }'
  if a.value('cost')!=b.value('cost'):repl['cost']=b.one('cost').raw()
  aps=a.children('prerequisite');bps=b.children('prerequisite')
  if [x.norm() for x in aps]!=[x.norm() for x in bps]:
   union=sorted({n.v for pre in aps+bps for n in pre.v if n.k=='focus'})
   repl['prerequisite']='prerequisite = { '+' '.join('focus = '+x for x in union)+' }'
   am=a.one('available');ba=b.one('available')
   repl['available']='available = { '+cond((am.inner() if am else '')+prerequisites(aps),(ba.inner() if ba else '')+prerequisites(bps))+' }'
  if repl:es.append((a.a,a.b,fields(a,repl)))
 return edits(s,es)
change('common/national_focus/RUS focus (Russia).txt',focuses)
# Restore stock choices/effects in shared socialist events outside the custom route.
BE={n.value('id'):n for n in load(KR/'events/RUS events (Russia).txt') if n.k=='country_event' and n.value('id').startswith('russia_socialist_events.')}
def events(s):
 es=[]
 for a in parse(s):
  if a.k!='country_event' or a.value('id') not in BE:continue
  b=BE[a.value('id')];repl={}
  for k in ['immediate','after']:
   ma=a.one(k);ba=b.one(k)
   if (ma.norm() if ma else None)!=(ba.norm() if ba else None):repl[k]=f'{k} = {{ '+effect(ma.inner() if ma else '',ba.inner() if ba else '')+' }'
  ma=a.one('trigger');ba=b.one('trigger')
  if (ma.norm() if ma else None)!=(ba.norm() if ba else None):repl['trigger']='trigger = { '+cond(ma.inner() if ma else '',ba.inner() if ba else '')+' }'
  if [n.norm() for n in a.children('option')]!=[n.norm() for n in b.children('option')]:
   opts=[]
   for src,route in [(a,'yes'),(b,'no')]:
    for option in src.children('option'):
     old=option.one('trigger');opts.append(fields(option,{'trigger':f'trigger = {{ {ROUTE} = {route} '+(old.inner() if old else '')+' }'}))
   repl['option']='\n'.join(opts)
  if repl:es.append((a.a,a.b,fields(a,repl)))
 return edits(s,es)
change('events/RUS events (Russia).txt',events)
for lang,name in [('simp_chinese','全俄劳联：路线关系修正'),('english','VST: Faction Relations'),('russian','ВСТ: отношения фракций')]:
 new(f'localisation/{lang}/RUS_kamenev_politics_l_{lang}.yml',f'l_{lang}:\n RUS_kamenev_vst_relationship_addon:0 "{name}"',True)
(R/'tmp/politics_manifest.json').write_text(json.dumps({'files':manifest,'trait_pairs':trait_pairs},ensure_ascii=False,indent=2),encoding='utf-8')
print('Migrated',len(manifest),'files;',len(trait_pairs),'advisor roles restored to KR defaults.')
