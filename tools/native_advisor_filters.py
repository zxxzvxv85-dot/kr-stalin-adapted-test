"""Native first-trait categories. Role trait ledgers preserve role-specific membership.

No gameplay trait is renamed or assigned a new modifier. Marked hooks must be
regenerated after other character/effect generators. New games are the baseline.
"""
from pathlib import Path
from collections import defaultdict
import re

BEGIN = '# RUS_NATIVE_FILTER_BEGIN'
END = '# RUS_NATIVE_FILTER_END'
MARKER = 'RUS_ui_native_category_'

def strip_hooks(text):
    return re.sub(r'\n?[ \t]*'+BEGIN+r'.*?'+END+r'[^\n]*\n?', '', text, flags=re.S)

def correct_identities(text,g):
    wanted={'RUS_lev_kamenev':'KR_vst_left_kamenev','RUS_sergey_kirov':'KR_bolshevik_kirov','RUS_grigory_zinovyev':'KR_vst_left_zinovyev'}
    prefixes=tuple(p for row in g.CATEGORIES for p in row[4])
    edits=[]
    def walk(nodes,owner=None):
        for n in nodes:
            if not isinstance(n.v,list):continue
            who=owner
            if n.k.startswith('RUS_') and any(c.k in ('portraits','advisor','add_trait','remove_trait','add_advisor_role') for c in n.v):who=n.k
            if n.k=='add_advisor_role':who=n.value('character',who)
            if n.k=='advisor' and who in wanted:
                traits=n.one('traits')
                if traits:
                    keep=[t.k for t in traits.v if not t.k.startswith(prefixes)]
                    edits.append((traits.a,traits.b,'traits = { '+' '.join(keep+[wanted[who]])+' }'))
            if n.k in ('add_trait','remove_trait'):
                char=n.value('character',who);t=n.one('trait')
                if char in wanted and n.value('slot') in ('political_advisor','second_in_command') and t and t.v.startswith(prefixes):
                    if n.k=='add_trait':edits.append((t.a,t.b,'trait = '+wanted[char]))
                    elif t.v==wanted[char]:edits.append((n.a,n.b,'# Fixed adviser faction identity is retained.\n'))
            walk(n.v,who)
    walk(g.parse(text))
    for a,b,v in sorted(edits,reverse=True):text=text[:a]+v+text[b:]
    return text

def build(g):
    root=g.ROOT
    families={}
    for source in (g.KR,root):
        for p in (source/'common/country_leader').glob('*.txt'):
            for n in g.load(p):
                if n.k=='leader_traits':
                    for t in n.v:
                        for row in g.CATEGORIES:
                            if t.k.startswith(row[4]) and {x.k for x in t.v} <= {'sprite','random','custom_modifier_tooltip'}:
                                families[t.k]=row[0]
    texts={}
    for sub in ('common/characters','common/scripted_effects','events'):
        for p in (root/sub).glob('*.txt'):
            if p.name in ('RUS_advisor_ui_refresh.txt','RUS_advisor_ui_refresh_effects.txt','RUS_native_advisor_filter_effects.txt'):continue
            s=correct_identities(strip_hooks(p.read_text(encoding='utf-8-sig')),g)
            # Remove the previous list-visibility workaround, preserving the real requirements.
            s=re.sub(r'^[ \t]*'+g.GUARD+r'_RUS_\w+\s*=\s*yes[^\n]*\n?', '', s, flags=re.M)
            texts[p.relative_to(root).as_posix()]=s
    candidates=defaultdict(list); defaults={}; operations=defaultdict(list); tails=defaultdict(list)
    def remember(pair,traits):
        for t in traits:
            if t not in candidates[pair]:candidates[pair].append(t)
    def scan(nodes,owner=None,path='',declaration=False,depth=0):
        for n in nodes:
            if not isinstance(n.v,list):continue
            who=owner
            if depth==0 and path.startswith('common/scripted_effects/') and n.k in ('RUS_add_faction_traits','RUS_sync_political_advisor_route'):tails[path].append(n.ib)
            if n.k.startswith('RUS_') and any(c.k in ('portraits','advisor','add_trait','remove_trait','add_advisor_role') for c in n.v):who=n.k
            if n.k=='add_advisor_role':who=n.value('character',who)
            if n.k=='advisor' and who and who.startswith('RUS_'):
                slot=n.value('slot');t=n.one('traits')
                if slot in ('political_advisor','second_in_command') and t:
                    traits=[c.k for c in t.v];pair=(who,slot);remember(pair,traits)
                    if declaration:defaults[pair]=traits
            if n.k in ('add_trait','remove_trait'):
                char=n.value('character',who);slot=n.value('slot');trait=n.value('trait')
                if char and char.startswith('RUS_') and slot in ('political_advisor','second_in_command') and trait:
                    pair=(char,slot);remember(pair,[trait]);operations[path].append((n,pair,'add' if n.k=='add_trait' else 'remove',trait))
            if n.k=='add_advisor_role' and who and who.startswith('RUS_'):
                a=n.one('advisor')
                if a and a.value('slot') in ('political_advisor','second_in_command'):
                    pair=(who,a.value('slot'));operations[path].append((n,pair,'role',[c.k for c in a.one('traits').v] if a.one('traits') else []))
            scan(n.v,who,path,declaration,depth+1)
    for path,s in texts.items():scan(g.parse(s),path=path,declaration=path.startswith('common/characters/'))
    # Only roles which can acquire a faction identity need a category ledger.
    active={p for p,ts in candidates.items() if any(t in families for t in ts)}
    def ident(pair):return pair[0]+'_'+pair[1]
    def tf(slot,t):return 'RUS_ui_nf_'+slot+'_'+t
    def mf(slot,k):return 'RUS_ui_nf_marker_'+slot+'_'+k
    def hook(pair,kind,value):
        who,slot=pair;name=ident(pair)
        lines=[BEGIN, 'ROOT = {',who+' = {','RUS_ui_nf_init_'+name+' = yes']
        if kind=='role':
            lines += ['clr_character_flag = '+tf(slot,t) for t in candidates[pair]]
            lines += ['set_character_flag = '+tf(slot,t) for t in value]
        else:lines += [('set' if kind=='add' else 'clr')+'_character_flag = '+tf(slot,value)]
        lines += ['}', 'if = { limit = { RUS_ui_use_faction_advisor_filters = yes } '+who+' = { RUS_ui_nf_order_'+name+' = yes } }','}',END]
        return '\n'+'\n'.join(lines)+'\n'
    result={}
    history_path='history/countries/RUS - Russia.txt'
    history=(root/history_path).read_bytes().decode('utf-8-sig')
    if 'RUS_ui_nf_new_game' not in history: history += '\n# UI-only native advisor category ledger seed; no gameplay reward.\nset_country_flag = RUS_ui_nf_new_game\n'
    if 'RUS_ui_nf_sync_all = yes' not in history: history += 'RUS_ui_nf_sync_all = yes\n'
    result[history_path]=history
    for path,s in texts.items():
        inserts=[(at,'\n'+BEGIN+'\nRUS_ui_nf_sync_all = yes\n'+END+'\n') for at in tails[path]]
        for n,pair,kind,value in operations[path]:
            if pair in active:inserts.append((n.b,hook(pair,kind,value)))
        for at,value in sorted(inserts,reverse=True):s=s[:at]+value+s[at:]
        original=(root/path).read_text(encoding='utf-8-sig')
        if s!=original or inserts:result[path]=s
    lines=['# Generated native filter state; flags record actual script writes separately for each role.']
    for pair in sorted(active):
        who,slot=pair;name=ident(pair);ts=candidates[pair]
        init='RUS_ui_nf_initialized_'+slot
        lines += ['RUS_ui_nf_init_'+name+' = {',' if = { limit = { NOT = { has_character_flag = '+init+' } }',' set_character_flag = '+init]
        lines += [' set_character_flag = '+tf(slot,t) for t in defaults.get(pair,[])]
        lines += [' }','}']
        lines += ['RUS_ui_nf_order_'+name+' = {',' if = { limit = { has_advisor_role = '+slot+' }',' set_temp_variable = { RUS_ui_nf_target = 0 }']
        for index,row in enumerate(g.CATEGORIES,19):
            members=[t for t in ts if families.get(t)==row[0]]
            if not members:continue
            checks=' '.join('has_character_flag = '+tf(slot,t) for t in members)
            lines += [' if = { limit = { check_variable = { RUS_ui_nf_target = 0 } OR = { '+checks+' } } set_temp_variable = { RUS_ui_nf_target = '+str(index)+' } }']
        # Rebuild only when the category changes. Snapshot flags already identify
        # exact slot membership; has_trait alone would mix Sic and political roles.
        same=' '.join('AND = { check_variable = { RUS_ui_nf_target = '+str(i)+' } has_character_flag = '+mf(slot,r[0])+' }' for i,r in enumerate(g.CATEGORIES,19))
        none='AND = { check_variable = { RUS_ui_nf_target = 0 } NOT = { OR = { '+' '.join('has_character_flag = '+mf(slot,r[0]) for r in g.CATEGORIES)+' } } }'
        lines += [' if = { limit = { NOT = { OR = { '+same+' '+none+' } } }']
        for t in ts:lines += [' if = { limit = { has_character_flag = '+tf(slot,t)+' } remove_trait = { slot = '+slot+' trait = '+t+' } }']
        for r in g.CATEGORIES:
            lines += [' if = { limit = { has_character_flag = '+mf(slot,r[0])+' } remove_trait = { slot = '+slot+' trait = '+MARKER+r[0]+' } }',' clr_character_flag = '+mf(slot,r[0])]
        for index,r in enumerate(g.CATEGORIES,19):
            lines += [' if = { limit = { check_variable = { RUS_ui_nf_target = '+str(index)+' } } add_trait = { slot = '+slot+' trait = '+MARKER+r[0]+' } set_character_flag = '+mf(slot,r[0])+' }']
        for t in ts:lines += [' if = { limit = { has_character_flag = '+tf(slot,t)+' } add_trait = { slot = '+slot+' trait = '+t+' } }']
        lines += [' }',' }','}']
    lines += ['RUS_ui_nf_sync_all = {']
    for who,slot in sorted(active):
        name=ident((who,slot))
        lines += [' if = { limit = { has_character = '+who+' } '+who+' = { if = { limit = { has_advisor_role = '+slot+' } RUS_ui_nf_init_'+name+' = yes } } }']
    lines += [' if = { limit = { RUS_ui_use_faction_advisor_filters = yes }']
    for who,slot in sorted(active):
        lines += [' if = { limit = { has_character = '+who+' } '+who+' = { RUS_ui_nf_order_'+ident((who,slot))+' = yes } }']
    lines += [' }','}']
    result['common/scripted_effects/RUS_native_advisor_filter_effects.txt']='\n'.join(lines)+'\n'
    result['common/country_leader/RUS_native_advisor_filter_traits.txt']='leader_traits = {\n'+'\n'.join(' '+MARKER+r[0]+' = { sprite = '+str(i)+' random = no }' for i,r in enumerate(g.CATEGORIES,19))+'\n}\n'
    # Native buttons own both the category state and the list rebuild.
    gui=(g.KR/'interface/command_character_view.gui').read_text(encoding='utf-8-sig').replace('max_slots_horizontal = 8','max_slots_horizontal = 10')
    result['interface/command_character_view.gui']='# Native category buttons; no scripted overlay.\n'+gui
    result['interface/zz_RUS_advisor_categories.gfx']='spriteTypes = {\n SpriteType = { name = "GFX_idea_traits_strip" texturefile = "'+g.ATLAS+'" noOfFrames = 27 }\n}\n'
    result['common/scripted_guis/RUS_advisor_faction_bar.txt']='# Retired: engine-native category buttons now handle filtering.\nscripted_gui = { }\n'
    result['interface/RUS_advisor_faction_bar.gui']='# Retired scripted overlay.\nguiTypes = { }\n'
    result['common/characters/RUS_advisor_ui_refresh.txt']='characters = { RUS_ui_advisor_refresh_anchor = { name = RUS_ui_advisor_refresh_anchor } }\n'
    result['common/scripted_effects/RUS_advisor_ui_refresh_effects.txt']='# Retired ineffective refresh experiment.\n'
    result['common/ideas/RUS_advisor_ui_refresh.txt']='# No refresh ideas.\n'
    result['common/scripted_triggers/RUS_advisor_faction_filter_triggers.txt']='RUS_ui_use_faction_advisor_filters = { original_tag = RUS is_ai = no has_country_flag = RUS_ui_nf_new_game OR = { has_government = totalist has_government = communist has_government = syndicalist has_government = radical_socialist } }\n'
    for language,col in [('simp_chinese',1),('english',2),('russian',3)]:
        loc=['l_'+language+':',' RUS_ui_advisor_refresh_anchor: ""']
        for i,r in enumerate(g.CATEGORIES,19):loc += [' ADVISOR_CATEGORY_'+str(i)+': "'+r[col]+'"',' '+MARKER+r[0]+': ""',' '+MARKER+r[0]+'_desc: ""']
        result['localisation/replace/RUS_advisor_faction_filter_l_'+language+'.yml']='\n'.join(loc)+'\n'
    return result,len(active)
