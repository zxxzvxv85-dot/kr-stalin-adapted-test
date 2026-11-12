"""Russia-only conscription laws. Read-only unless --write.

Native references: KR 00 Laws / 00_laws_scripted_effects; KR militia subunit;
native unit_modifiers, effects_documentation, and ideas.gfx (64px law icons).
"""
import json
from pathlib import Path
from hoi4_politics_blocks import parse, load
from generation_io import cli

ROOT = Path(__file__).resolve().parents[1]
KR = ROOT.parent / '1521695605'
PREFIX = 'RUS_sc_'
KEYS = ('volunteers','territorial','universal','wartime','extended','emergency')
NAMES = ('工农志愿兵役制','常备军与地域兵役制','普遍义务兵役制','战时扩大征召','扩大役龄征召','全民紧急征召')
CHINESE_DESCRIPTIONS = {
 'volunteers': '“工农红军由劳动阶级中觉悟最高、最有组织性的人员组成。凡年满十八岁的社会主义共和国公民，均可申请加入红军。”',
 'territorial': '“现役兵役可在工农红军部队的常备编制或地域部队的轮换编制中履行，也可在部队以外履行。……地域部队轮换人员的现役期由集训和集训之间的休假组成。整个现役期内，集训总时长因兵种而异，上限为八至十二个月。”',
 'universal': '“普遍兵役义务由法律规定。在工农红军服役是共和国公民的光荣义务。……一切共和国男性公民，无论种族、民族、宗教信仰、教育程度、社会出身和地位，均须在共和国武装力量中服兵役。”',
 'wartime': '“为了保卫我们伟大的祖国和无产阶级革命的火种，凡出生于1905年至1918年（含首尾两年）的负有兵役义务人员，均须应召。”',
 'extended': '“动员1890年至1904年出生的负有兵役义务人员，并征召1922年至1923年出生的应征人员。征召范围为斯摩棱斯克州、图拉州、库尔斯克州，以及奥廖尔州柳季诺沃—布良斯克—谢夫斯克一线以西地区。”',
 'emergency': '“本市的工人、职员和学生按区动员参加人民民兵，并按区组建二十五个师。……民兵师从十七至五十五岁的劳动者中动员组建。”',
}
FOCI = ('RUS_fr_post_revolutionary_armed_forces','RUS_fr_general_staff_experimental_formations','RUS_future_foreign_062')
VANILLA = ('disarmed_nation','volunteer_only','limited_conscription','extensive_conscription','service_by_requirement','all_adults_serve','scraping_the_barrel')
STATS = (
 {'conscription':.03,'modifier_army_sub_unit_militia_attack_factor':.1,'modifier_army_sub_unit_militia_defence_factor':.1,'modifier_army_sub_unit_militia_max_org_factor':.1,'training_time_factor':-.1,'army_org_factor':-.15,'army_strength_factor':-.15,'mobilization_speed':-.5},
 {'conscription':.025,'training_time_factor':-.2,'modifier_army_sub_unit_militia_defence_factor':.1,'army_strength_factor':-.1,'modifier_army_sub_unit_militia_max_org_factor':-.1,'mobilization_speed':-.3},
 {'conscription':.05,'army_org_factor':.05,'army_org_regain':-.15,'training_time_factor':.1,'mobilization_speed':-.1},
 {'conscription':.07,'mobilization_speed':.3,'reinforce_rate':.02,'army_org_factor':-.05,'training_time_factor':.2,'industrial_capacity_factory':-.1,'industrial_capacity_dockyard':-.1,'production_speed_buildings_factor':-.1,'war_stability_factor':-.2},
 {'conscription':.15,'mobilization_speed':.4,'reinforce_rate':.03,'army_strength_factor':-.05,'army_org_factor':-.1,'training_time_factor':.3,'industrial_capacity_factory':-.3,'industrial_capacity_dockyard':-.3,'production_speed_buildings_factor':-.3,'war_stability_factor':-.5},
 {'conscription':.25,'mobilization_speed':.5,'reinforce_rate':.04,'army_strength_factor':-.1,'army_org_factor':-.2,'training_time_factor':.5,'industrial_capacity_factory':-.4,'industrial_capacity_dockyard':-.4,'production_speed_buildings_factor':-.4,'war_stability_factor':-.8},
)
IDEAS='common/ideas/RUS_socialist_conscription_laws.txt'
FX='common/scripted_effects/RUS_socialist_conscription_effects.txt'
TR='common/scripted_triggers/RUS_socialist_conscription_triggers.txt'
TECH='common/technologies/RUS_socialist_conscription_technologies.txt'

def b(key, lines):
 return key+' = {\n'+''.join('\t'+line+'\n' for item in lines for line in item.splitlines())+'}\n'
def cond(c,lines,kind='if'):
 return b(kind,['limit = { '+c+' }',*lines]).rstrip()
def law(i):return PREFIX+KEYS[i-1]
def patch_focus(text, fid, stage):
 focus=next(n for t in parse(text) for n in ([t] if t.k=='shared_focus' else t.children('focus')) if n.value('id')==fid)
 reward=focus.one('completion_reward'); call=PREFIX+'focus_'+str(stage)
 inner=reward.inner()
 old=reward.one(call)
 if old:inner=inner[:old.a-reward.ia]+inner[old.b-reward.ia:]
 indent=text[text.rfind('\n',0,reward.a)+1:reward.a]
 inner=inner.rstrip()+'\n'+indent+'\t'+call+' = yes\n'+indent
 return text[:reward.ia]+inner+text[reward.ib:]

def native_laws():
 """Only guard the seven shared choices; all other KR fields remain verbatim."""
 text=(KR/'common/ideas/00 Laws.txt').read_text(encoding='utf-8-sig')
 group=parse(text)[0].one('mobilization_laws')
 for n in sorted((n for n in group.v if n.k in VANILLA),key=lambda n:n.ia,reverse=True):
  assert n.one('visible') is None, 'Review updated KR law visibility before composing'
  text=text[:n.ia]+'\n\t\t\tvisible = { NOT = { RUS_sc_context = yes } }'+text[n.ia:]
 return text

def render_outputs():
 out={'common/ideas/00 Laws.txt':native_laws()}
 out[TR]=b('RUS_sc_context',['original_tag = RUS','has_socialist_government = yes'])
 # Manual selection is deliberately independent of the old war-support gates.
 laws=[]
 for i,key in enumerate(KEYS,1):
  stats=[f'{k} = {v:g}' for k,v in STATS[i-1].items()]
  if i==2:stats.append('custom_modifier_tooltip = RUS_sc_militia_supply_tt')
  laws.append(b(law(i),[
   'picture = RUS_sc_'+key,'cost = 150','level = '+str(7-i),'removal_cost = -1','cancel_if_invalid = no',
   'allowed = { original_tag = RUS }','visible = { RUS_sc_context = yes }',
   'available = { hidden_trigger = { RUS_sc_context = yes } '+('NOT = { country_exists = GER }' if i in (2,3,4) else 'custom_trigger_tooltip = { tooltip = RUS_sc_auto_'+str(i)+'_tt always = no }')+' }',
   'allowed_to_remove = { NOT = { country_exists = GER } }',
   b('on_add',['set_temp_variable = { law_level = '+str(7-i)+' }','mobilisation_laws_on_add_effect = yes',*(['unlock_subunit = militia'] if i in (1,2) else []),
    cond('RUS_sc_context = yes NOT = { has_tech = RUS_sc_territorial_supply }',['set_technology = { RUS_sc_territorial_supply = 1 popup = no }']) if i==2 else 'RUS_sc_remove_territorial = yes']).strip(),
   b('on_remove',['RUS_sc_remove_territorial = yes']).strip(),b('modifier',stats).strip(),
   'ai_will_do = { factor = '+('10' if i==3 else '0')+' }']).rstrip())
 out[IDEAS]=b('ideas',[b('mobilization_laws',laws).strip()])
 # Reversible, country-local militia supply bonus, not a global unit edit.
 out[TECH]=b('technologies',[b('RUS_sc_territorial_supply',[
  'allow = { always = no }','research_cost = 1','start_year = 1936','ai_will_do = { factor = 0 }',
  'militia = { supply_consumption = -0.15 }']).strip()])
 fx=[b('RUS_sc_remove_territorial',[
  cond('has_tech = RUS_sc_territorial_supply',['set_technology = { RUS_sc_territorial_supply = 0 popup = no }'])]),
  b('RUS_sc_sync_territorial',[
  cond('RUS_sc_context = yes has_idea = RUS_sc_territorial',[
   cond('NOT = { has_tech = RUS_sc_territorial_supply }',['set_technology = { RUS_sc_territorial_supply = 1 popup = no }'])]),
  b('else',['RUS_sc_remove_territorial = yes']).strip()])]
 for i in range(1,7):
  fx.append(b(PREFIX+'set_'+str(i),[cond('NOT = { has_idea = '+law(i)+' }',['add_ideas = '+law(i)])]))
 # Current crisis thresholds override focus progress; strict >, never >=.
 normal=[]
 for i,fid in reversed(tuple(enumerate(FOCI,2))):
  normal.append(cond('OR = { has_completed_focus = '+fid+' has_country_flag = RUS_sc_reached_'+str(i)+' }',[PREFIX+'set_'+str(i)+' = yes'], 'if' if i==4 else 'else_if'))
 normal.append(b('else',['RUS_sc_set_1 = yes']).strip())
 choices='OR = { '+' '.join('has_idea = '+law(i) for i in (2,3,4))+' }'
 fx.append(b('RUS_sc_refresh',[
  cond('RUS_sc_context = yes',[
   cond('NOT = { country_exists = GER }',[
    cond('NOT = { '+choices+' }',[
     cond('OR = { has_completed_focus = '+FOCI[2]+' has_country_flag = RUS_sc_reached_4 }',['RUS_sc_set_4 = yes']),
     cond('OR = { has_completed_focus = '+FOCI[1]+' has_country_flag = RUS_sc_reached_3 }',['RUS_sc_set_3 = yes'],'else_if'),
     b('else',['RUS_sc_set_2 = yes']).strip()])]),
   cond('surrender_progress > 0.5',['RUS_sc_set_6 = yes'],'else_if'),
   cond('surrender_progress > 0.2',['RUS_sc_set_5 = yes'],'else_if'),
   b('else',normal).strip(),'RUS_sc_sync_territorial = yes']),
  b('else',[
   # Restore an equivalent vanilla law if the country leaves the route.
   *[cond('has_idea = '+law(i),['add_ideas = '+VANILLA[i]]) for i in range(1,7)],
   'RUS_sc_remove_territorial = yes']).strip()]))
 for i in (2,3,4):
  higher=' '.join('NOT = { OR = { has_completed_focus = '+FOCI[j-2]+' has_country_flag = RUS_sc_reached_'+str(j)+' } }' for j in range(i+1,5))
  fx.append(b(PREFIX+'focus_'+str(i),[
   cond('hidden_trigger = { RUS_sc_context = yes country_exists = GER NOT = { surrender_progress > 0.2 } '+higher+' }',[
    'effect_tooltip = { add_ideas = '+law(i)+' }']),
   b('hidden_effect',['set_country_flag = RUS_sc_reached_'+str(i),'RUS_sc_refresh = yes']).strip()]))
 out[FX]='\n'.join(fx)
 out['common/on_actions/RUS_socialist_conscription_on_actions.txt']=b('on_actions',[
  b('on_startup',[b('effect',['RUS = { RUS_sc_refresh = yes }']).strip()]).strip(),
  *[b(hook,[b('effect',[cond('original_tag = RUS',['RUS_sc_refresh = yes'])]).strip()]).strip() for hook in ('on_daily_RUS','on_government_change')]])
 # Focus hooks compose with existing maintained rewards without replacing them.
 for path,rows in [('common/national_focus/RUS focus (Russia).txt',[(FOCI[0],2),(FOCI[1],3)]),('common/national_focus/00_RUS_future_foreign_policy_skeleton.txt',[(FOCI[2],4)])]:
  text=(ROOT/path).read_text(encoding='utf-8-sig')
  for fid,i in rows:text=patch_focus(text,fid,i)
  out[path]=text
 loc={PREFIX+k:n for k,n in zip(KEYS,NAMES)}
 loc.update({PREFIX+k+'_desc':'' for k in KEYS})
 loc['RUS_sc_territorial_supply']='地域兵役补给组织'
 loc['RUS_sc_territorial_supply_desc']=''
 loc['RUS_sc_militia_supply_tt']='民兵补给消耗：§G-15.0%§!'
 loc['RUS_sc_auto_1_tt']='进入社会主义俄罗斯后自动采用'
 loc['RUS_sc_auto_5_tt']='投降度高于§Y20%§!时自动采用'
 loc['RUS_sc_auto_6_tt']='投降度高于§Y50%§!时自动采用'
 for lang in ('simp_chinese','english','russian'):
  descriptions = {PREFIX+k+'_desc': v for k,v in CHINESE_DESCRIPTIONS.items()} if lang == 'simp_chinese' else {}
  out[f'localisation/{lang}/RUS_socialist_conscription_l_{lang}.yml']='l_'+lang+':\n'+''.join(' '+k+':0 '+json.dumps(v,ensure_ascii=False)+'\n' for k,v in (loc | descriptions).items())
 out['interface/RUS_socialist_conscription.gfx']=b('spriteTypes',[
  b('spriteType',['name = "GFX_idea_RUS_sc_'+key+'"','texturefile = "gfx/interface/ideas/RUS_sc_'+key+'.dds"']).strip() for key in KEYS])
 return out

if __name__=='__main__':cli(render_outputs,root=ROOT)
