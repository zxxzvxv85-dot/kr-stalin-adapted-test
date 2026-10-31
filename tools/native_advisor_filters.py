"""Restore KR profession categories and badges; retain requested faction identities.

The retired UI hook blocks are stripped without changing their surrounding logic.
No runtime trait reordering, synthetic marker or ledger remains.
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
    result={}
    for sub in ('common/characters','common/scripted_effects','events'):
        for p in (root/sub).glob('*.txt'):
            if p.name in ('RUS_advisor_ui_refresh.txt','RUS_advisor_ui_refresh_effects.txt','RUS_native_advisor_filter_effects.txt'):continue
            original=p.read_text(encoding='utf-8-sig')
            s=correct_identities(strip_hooks(original),g)
            s=re.sub(r'^[ \t]*'+g.GUARD+r'_RUS_\w+\s*=\s*yes[^\n]*\n?', '', s, flags=re.M)
            if s!=original:result[p.relative_to(root).as_posix()]=s
    history_path='history/countries/RUS - Russia.txt'
    history=(root/history_path).read_bytes().decode('utf-8-sig')
    for line in ('# UI-only native advisor category ledger seed; no gameplay reward.',
                 'set_country_flag = RUS_ui_nf_new_game','RUS_ui_nf_sync_all = yes'):
        history=re.sub(r'(?m)^'+re.escape(line)+r'\r?\n?', '', history)
    # The old generator appended one separator newline before its three-line block.
    # Keep the pre-existing mixed CRLF/LF history bytes; remove only that separator.
    if history.endswith('\n\n') and 'RUS_ui_nf_new_game' in (root/history_path).read_bytes().decode('utf-8-sig'):
        history=history[:-1]
    result[history_path]=history
    result['common/scripted_effects/RUS_native_advisor_filter_effects.txt']='# Retired: original profession trait order drives native categories and badges.\n'
    result['common/country_leader/RUS_native_advisor_filter_traits.txt']='# Retired empty category markers; original advisor traits are unchanged.\nleader_traits = { }\n'
    result['interface/command_character_view.gui']='# KR profession categories and original card badges.\n'+(g.KR/'interface/command_character_view.gui').read_text(encoding='utf-8-sig')
    result['interface/zz_RUS_advisor_categories.gfx']='# Restore the original KR profession strip, shared by filters and card badges.\nspriteTypes = {\n SpriteType = { name = "GFX_idea_traits_strip" texturefile = "gfx/interface/ideas/idea_traits_strip.dds" noOfFrames = 18 }\n}\n'
    result['common/scripted_guis/RUS_advisor_faction_bar.txt']='# Retired faction overlay; native profession buttons own filtering.\nscripted_gui = { }\n'
    result['interface/RUS_advisor_faction_bar.gui']='# Retired scripted overlay.\nguiTypes = { }\n'
    result['common/characters/RUS_advisor_ui_refresh.txt']='characters = { RUS_ui_advisor_refresh_anchor = { name = RUS_ui_advisor_refresh_anchor } }\n'
    result['common/scripted_effects/RUS_advisor_ui_refresh_effects.txt']='# Retired ineffective refresh experiment.\n'
    result['common/ideas/RUS_advisor_ui_refresh.txt']='# No refresh ideas.\n'
    result['common/scripted_triggers/RUS_advisor_faction_filter_triggers.txt']='# Retired: no faction filter conditions or gameplay gates.\n'
    for language in ('simp_chinese','english','russian'):
        result['localisation/replace/RUS_advisor_faction_filter_l_'+language+'.yml']='l_'+language+':\n RUS_ui_advisor_refresh_anchor: ""\n'
    return result,0
