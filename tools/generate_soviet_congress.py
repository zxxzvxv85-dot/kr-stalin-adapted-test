"""Decision-category prototype. Default is read-only; --write updates owned files.

References: KR common/scripted_guis/_documentation.md, PHI scripted_gui
(Philippines).txt (array-indexed sprite frames), RUS_russian_congress (council
icon), 00_mobilisation_effects.txt (native while_loop_effect), and local
RUS_doudizhu_decisions/categories (free human-only launcher).
Seat dots and panel are geometric UI primitives. The complete hall illustration
is a built-in image_gen source, exported whole at its original aspect ratio.
"""
from pathlib import Path
from io import BytesIO
import argparse
import json
import math
import random
import re

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'RUS_congress'
TOTAL = 800
WIDTH, HEIGHT = 500, 1360
MAIN_HEIGHT = 824
# countrydecisionview.gui decision_grid has a 502px slot, not the outer 550px.
CONTENT_RIGHT = 468
HALL_SIZE = (476, 238)
VERTICAL_SHIFT = 158
TABLE_COLUMNS = [('name',48,244),('count',300,62),('share',380,88)]
HALL_SOURCE = Path('tools/design/soviet_congress_hall_20261023/source-symmetric.png')
PARTIES = [
    ('bolsheviks', '俄罗斯共产党（布尔什维克）', '473', 240, '#d65b60'),
    ('unions', '工会联盟', '275', 160, '#d7b45d'),
    ('labour', '全俄罗斯劳工联盟', '253', 120, '#de915e'),
    ('sr', '社会革命党', '269', 200, '#70b38c'),
    ('democrats', '社会主义民主联盟', '273', 80, '#72a8d3'),
]
CHILDREN = {
    'labour': [
        ('workers_opposition', '全俄劳联 · 工人反对派', '', 40, '#eaa678'),
        ('new_theory', '全俄劳联 · 新理论派', '262', 40, '#dc864e'),
        ('new_society', '全俄劳联 · 新社会派', '265', 40, '#b9643e'),
    ],
    'workers_opposition': [
        ('new_youth', '工人反对派 · 新青年派', '257', 10, '#f0b58a'),
        ('literary_union', '工人反对派 · 文艺联合会', '', 10, '#e9a070'),
        ('moderates', '工人反对派 · 温和派', '', 10, '#d88c63'),
        ('left_syndicalists', '工人反对派 · 左翼工团主义者', '', 10, '#c67b53'),
    ],
    'new_theory': [
        ('young_guard', '新理论派 · 少壮派', '', 10, '#e39a57'),
        ('anarcho_syndicalists', '新理论派 · 无政府工团主义者', '', 10, '#ce8041'),
        ('old_guard', '新理论派 · 元老派', '', 10, '#ba723a'),
        ('right_syndicalists', '新理论派 · 右翼工团主义者', '', 10, '#aa6331'),
    ],
    'sr': [
        ('sr_maximalists', '社革党 · 最高纲领派', '364', 100, '#46966c'),
        ('sr_populists', '社革党 · 民粹派', '290', 50, '#a0d7b1'),
        ('sr_democrats', '社革党 · 民主派', '', 50, '#7fcba6'),
    ],
}
SHARED = ('sr_citizens','社革党 · 公民派','',50,'#5ba899')
ALL_PARTIES = PARTIES + [row for rows in CHILDREN.values() for row in rows]+[SHARED]
BY_KEY={row[0]:row for row in ALL_PARTIES}
PARENTS={row[0]:[key] for key,rows in CHILDREN.items() for row in rows}
PARENTS['sr_citizens']=['sr_populists','sr_democrats']
# Contribution amounts are included in each parent's subtotal, not extra seats.
CIVIC_SOURCES={'sr_populists':'RUS_congress_citizens_from_populists','sr_democrats':'RUS_congress_citizens_from_democrats'}
PORTRAIT_LINE_GAP=5  # Default tooltip 16px lines: 80px >= 67px adviser art.
FRAMES = {row[0]:i for i,row in enumerate(ALL_PARTIES,1)}
LEADERS = {
    'bolsheviks': ['RUS_yakov_sverdlov'],
    'unions': ['RUS_mikhail_tomsky'],
    'labour': ['RUS_grigory_zinovyev','RUS_lev_kamenev','RUS_daniil_sulimov','RUS_vladimir_levitsky','RUS_fyodor_dan'],
    'sr': ['RUS_aleksey_ustinov','RUS_maria_spiridonova','RUS_vladimir_rikhter','RUS_pitirim_sorokin'],
    'democrats': ['RUS_gergard_zeller'],
    'new_youth': ['RUS_grigory_zinovyev'],
    'workers_opposition': ['RUS_grigory_zinovyev','RUS_lev_kamenev'],
    'literary_union': ['RUS_grigory_zinovyev'],
    'moderates': ['RUS_lev_kamenev'],
    'left_syndicalists': ['RUS_lev_kamenev'],
    'new_theory': ['RUS_daniil_sulimov','RUS_vladimir_levitsky'],
    'new_society': ['RUS_fyodor_dan'],
    'young_guard': ['RUS_daniil_sulimov'],
    'anarcho_syndicalists': ['RUS_vladimir_levitsky'],
    'old_guard': ['RUS_vladimir_levitsky'],
    'right_syndicalists': ['RUS_vladimir_levitsky'],
    'sr_populists': ['RUS_maria_spiridonova','RUS_pitirim_sorokin'],
    'sr_maximalists': ['RUS_aleksey_ustinov'],
    'sr_democrats': ['RUS_vladimir_rikhter','RUS_pitirim_sorokin'],
    'sr_citizens': ['RUS_pitirim_sorokin'],
}


def leader_portraits():
    from hoi4_politics_blocks import load
    chars={n.k:n for top in load(ROOT/'common/characters/RUS characters.txt') for n in top.v}
    result={}
    for char in {char for row in LEADERS.values() for char in row}:
        result[char]=chars[char].one('portraits').one('civilian').value('small')
        assert result[char].startswith('GFX_')
    return result


def leader_textures():
    """Resolve the existing adviser artwork; text icons need non-lazy aliases."""
    from hoi4_politics_blocks import load
    portraits=leader_portraits(); wanted=set(portraits.values()); textures={}
    for root in [ROOT.parent/'1521695605',ROOT]:
        for path in sorted((root/'interface').rglob('*.gfx')):
            for block in load(path):
                if not isinstance(block.v,list): continue
                for node in block.v:
                    name=node.value('name').strip('"')
                    if name in wanted:
                        texture=next((n.v.strip('"') for n in node.v if n.k.lower()=='texturefile'),None)
                        if texture: textures[name]=texture
    if wanted-set(textures): raise ValueError('Missing installed adviser sprites: '+str(sorted(wanted-set(textures))))
    return {char:textures[sprite] for char,sprite in sorted(portraits.items())}


def portrait_texticon(char):
    return 'RUS_congress_face_'+char.removeprefix('RUS_')


def display_parties(expanded=False):
    """Expanded chart uses disjoint leaves; the shared civic pool appears once."""
    if not expanded: return PARTIES
    def leaves(row):
        if row[0] in CHILDREN:
            return [leaf for child in CHILDREN[row[0]] for leaf in leaves(child)]+([SHARED] if row[0]=='sr' else [])
        if row[0] in CIVIC_SOURCES:
            return [(row[0],row[1],row[2],row[3]-25,row[4])]
        return [row]
    return [row for parent in PARTIES for row in leaves(parent)]


def table_rows(expanded=False):
    """One copy per parent. Expanded children are indented below their parent."""
    result=[]; y=470+VERTICAL_SHIFT
    def visit(row,depth):
        nonlocal y
        result.append((row,depth,y)); y+=36 if depth==0 else 32
        if expanded and row[0] in CHILDREN:
            for child in CHILDREN[row[0]]: visit(child,depth+1)
            if row[0]=='sr': visit(SHARED,2)
            y+=10
    for parent in PARTIES: visit(parent,0)
    return result


def row_elements(row,depth,y):
    child=depth>0
    key=row[0]; font='hoi_16mbs' if child else 'hoi_18mbs'
    name_x=48 if not child else 54+18*depth
    return [
        {'kind':'icon','name':'RUS_congress_key_'+key,'x':name_x-18 if child else 27,'y':y+5,'w':9 if child else 12,'h':9 if child else 12,'child':child,'key':key},
        {'kind':'text','name':'RUS_congress_name_'+key,'x':name_x,'y':y,'w':292-name_x,'h':26,'font':font,'loc':('RUS_congress_childname_' if child else 'RUS_congress_name_')+key,'align':'left','child':child,'key':key},
        {'kind':'text','name':'RUS_congress_count_'+key,'x':300,'y':y,'w':62,'h':26,'font':font,'loc':'RUS_congress_count_'+key,'align':'right','child':child,'key':key},
        {'kind':'text','name':'RUS_congress_share_'+key,'x':380,'y':y,'w':88,'h':26,'font':font,'loc':'RUS_congress_share_'+key,'align':'right','child':child,'key':key},
    ]


def seats():
    """800 non-overlapping points, ordered by angle for contiguous party sectors."""
    radii = [110 + 11.5*i for i in range(12)]
    raw = [TOTAL*r/sum(radii) for r in radii]
    counts = [math.floor(n) for n in raw]
    for i in sorted(range(12), key=lambda i: raw[i]-counts[i], reverse=True)[:TOTAL-sum(counts)]:
        counts[i] += 1
    points = []
    for row, (r, count) in enumerate(zip(radii, counts)):
        for j in range(count):
            angle = math.pi*(j+0.5)/count
            points.append((angle, row, round(WIDTH/2-r*(WIDTH-56)/480*math.cos(angle)-3), round(218+VERTICAL_SHIFT+0.82*r*math.sin(angle)-3)))
    return [(x,y) for _,_,x,y in sorted(points)]


def png(im):
    out = BytesIO(); im.save(out, format='PNG'); return out.getvalue()


def assets():
    atlas = Image.new('RGBA', (6*len(ALL_PARTIES),6))
    draw = ImageDraw.Draw(atlas)
    for i, (_,_,_,_,colour) in enumerate(ALL_PARTIES):
        draw.rounded_rectangle((i*6,0,i*6+4,4), radius=1, fill=colour)
        draw.line((i*6+1,0,i*6+3,0), fill='#ecdabb')
    panel = Image.new('RGBA',(WIDTH,HEIGHT),'#202625')
    d = ImageDraw.Draw(panel); rng=random.Random(800)
    for y in range(HEIGHT):
        shade=rng.choice([31,32,33,34]); d.line((1,y,WIDTH-2,y),fill=(shade,shade+5,shade+4))
    d.rectangle((1,1,WIDTH-2,HEIGHT-2),outline='#a99564')
    d.rectangle((5,5,WIDTH-6,HEIGHT-6),outline='#444b43')
    d.rectangle((11,11,WIDTH-12,251),outline='#a99564')
    d.line((22,292,WIDTH-23,292), fill='#807452')
    d.rectangle((22,296,WIDTH-23,348),fill='#191f1e',outline='#5f6555')
    d.rectangle((22,582,WIDTH-23,617),fill='#30362f',outline='#756b50')
    main_panel=panel.crop((0,0,WIDTH,MAIN_HEIGHT))
    md=ImageDraw.Draw(main_panel)
    md.line((1,MAIN_HEIGHT-2,WIDTH-2,MAIN_HEIGHT-2),fill='#a99564')
    md.line((5,MAIN_HEIGHT-6,WIDTH-6,MAIN_HEIGHT-6),fill='#444b43')
    return {'gfx/interface/RUS_soviet_congress/panel.png': png(panel),
            'gfx/interface/RUS_soviet_congress/panel_main.png':png(main_panel),
            'gfx/interface/RUS_soviet_congress/seats.png': png(atlas),
            'gfx/interface/RUS_soviet_congress/congress_hall.png':png(Image.open(ROOT/HALL_SOURCE).convert('RGBA').resize(HALL_SIZE,Image.Resampling.LANCZOS))}


def text(name, x,y, key, width=456, height=24, font='hoi_16mbs', align='center', tooltip=None):
    hover=f'pdx_tooltip = "{tooltip}" alwaystransparent = no' if tooltip else 'alwaystransparent = yes'
    return f'\t\tinstantTextBoxType = {{ name = "{name}" position = {{ x = {x} y = {y} }} text = "{key}" font = "{font}" maxWidth = {width} maxHeight = {height} format = {align} fixedsize = yes {hover} }}'


def icon(name,x,y,sprite,extra=''):
    return f'\t\ticonType = {{ name = "{name}" position = {{ x = {x} y = {y} }} spriteType = "{sprite}" {extra} alwaystransparent = yes }}'


def outputs():
    out = assets()
    gui=['# Generated by tools/generate_soviet_congress.py --write', 'guiTypes = {', '\tcontainerWindowType = {',
         '\t\tname = "RUS_congress_window"', '\t\tposition = { x = 0 y = 0 }',
         f'\t\tsize = {{ width = 100% height = {HEIGHT} }}', '\t\tclipping = no',
         icon('RUS_congress_panel',0,0,'GFX_RUS_congress_panel'),
         icon('RUS_congress_hall',12,12,'GFX_RUS_congress_hall'),
         text('RUS_congress_title',12,260,'RUS_congress_title',476,30,'hoi_24header'),
         text('RUS_congress_bill',22,302,'RUS_congress_bill'),
         text('RUS_congress_threshold',22,325,'RUS_congress_threshold'),
         text('RUS_congress_total',150,391,'RUS_congress_total',200,34,'hoi_24header'),
         text('RUS_congress_total_caption',150,428,'RUS_congress_total_caption',200)]
    gui += [text('RUS_congress_column_'+key,x,588,'RUS_congress_column_'+key,w,26,'hoi_18mbs','left' if key=='name' else 'right') for key,x,w in TABLE_COLUMNS]
    for i,(x,y) in enumerate(seats()):
        gui.append(icon(f'RUS_congress_seat_{i}',x,y,'GFX_RUS_congress_seats'))
    body=[e for row,child,y in table_rows(True) for e in row_elements(row,child,y)]
    for e in body:
        if e['kind']=='icon':
            gui.append(icon(e['name'],e['x'],e['y'],'GFX_RUS_congress_seats',f'frame = {FRAMES[e["key"]]} scale = '+('1.5' if e['child'] else '2')))
        else:
            tip='RUS_congress_leaders_'+e['key']+'_tt' if e['name'].startswith(('RUS_congress_count_','RUS_congress_share_')) else None
            gui.append(text(e['name'],e['x'],e['y'],e['loc'],e['w'],e['h'],e['font'],e['align'],tip))
    gui += ['\t\tbuttonType = { name = "RUS_congress_toggle" position = { x = 176 y = 356 } quadTextureSprite = "GFX_button_148x34" buttonText = "RUS_congress_toggle" buttonFont = "hoi_16mbs" clicksound = click_default }', '\t}', '}']
    # Native properties expose x/y/frame, not category layout height. Use two
    # mutually exclusive decision categories with real short/long root windows.
    # Both are emitted from the same controls; no oversized hidden root remains.
    child_names={e['name'] for e in body if e['child']}
    main_positions={e['name']:e['y'] for row,depth,y in table_rows(False) for e in row_elements(row,depth,y)}
    main_gui=[]
    for line in gui[2:-1]:
        if any(f'name = "{name}"' in line for name in child_names): continue
        line=line.replace('"RUS_congress_window"','"RUS_congress_window_main"').replace(f'height = {HEIGHT}',f'height = {MAIN_HEIGHT}').replace('"GFX_RUS_congress_panel"','"GFX_RUS_congress_panel_main"')
        name=re.search(r'name = "([^"]+)"',line)
        if name and name[1] in main_positions:
            line=re.sub(r'(position = \{ x = \d+ y = )\d+',lambda m:m[1]+str(main_positions[name[1]]),line,count=1)
        main_gui.append(line)
    full_gui=[line.replace('"RUS_congress_window"','"RUS_congress_window_children"') for line in gui[2:-1]]
    out['interface/RUS_soviet_congress.gui']='\n'.join(gui[:2]+main_gui+full_gui+['}'])+'\n'
    gfx='''spriteTypes = {
    spriteType = { name = "GFX_RUS_congress_panel" texturefile = "gfx/interface/RUS_soviet_congress/panel.png" noOfFrames = 1 }
    spriteType = { name = "GFX_RUS_congress_panel_main" texturefile = "gfx/interface/RUS_soviet_congress/panel_main.png" noOfFrames = 1 }
    spriteType = { name = "GFX_RUS_congress_seats" texturefile = "gfx/interface/RUS_soviet_congress/seats.png" noOfFrames = FRAME_COUNT }
    spriteType = { name = "GFX_RUS_congress_hall" texturefile = "gfx/interface/RUS_soviet_congress/congress_hall.png" noOfFrames = 1 }
'''.replace('FRAME_COUNT',str(len(ALL_PARTIES)))
    for char,texture in leader_textures().items():
        gfx+=f'    spriteType = {{ name = "GFX_{portrait_texticon(char)}" texturefile = "{texture}" noOfFrames = 1 legacy_lazy_load = no }}\n'
    out['interface/RUS_soviet_congress.gfx']=gfx+'}\n'
    scripted=['scripted_gui = {', '\tRUS_congress_gui = {', '\t\tcontext_type = decision_category',
              '\t\twindow_name = "RUS_congress_window"', '\t\tdirty = RUS.RUS_congress_revision',
              '\t\tai_enabled = { always = no }',
              '\t\tvisible = { original_tag = RUS has_country_flag = RUS_congress_demo_initialized }',
              '\t\ttriggers = {']
    scripted += [f'\t\t\t{e["name"]}_visible = {{ RUS = {{ has_country_flag = RUS_congress_show_children }} }}' for e in body if e['child']]
    scripted += ['\t\t}',
              '\t\teffects = {',
              '\t\t\tRUS_congress_toggle_click = { hidden_effect = { RUS = {',
              '\t\t\t\tif = { limit = { has_country_flag = RUS_congress_show_children } clr_country_flag = RUS_congress_show_children }',
              '\t\t\t\telse = { set_country_flag = RUS_congress_show_children }',
              '\t\t\t\tRUS_congress_refresh_display = yes',
              '\t\t\t\tlog = "[GetLogRoot]: Congress view toggled; revision=[?RUS_congress_revision]"',
              '\t\t\t} } }',
              '\t\t}',
              '\t\tproperties = {']
    scripted += [f'\t\t\tRUS_congress_seat_{i} = {{ frame = RUS.RUS_congress_seats^{i} }}' for i in range(TOTAL)]
    scripted += ['\t\t}', '\t}', '}']
    main_scripted=[];full_scripted=[]
    for line in scripted[1:-1]:
        full_scripted.append(line.replace('RUS_congress_gui =','RUS_congress_gui_children =').replace('"RUS_congress_window"','"RUS_congress_window_children"').replace('visible = { original_tag = RUS has_country_flag = RUS_congress_demo_initialized }','visible = { original_tag = RUS has_country_flag = RUS_congress_demo_initialized has_country_flag = RUS_congress_show_children }'))
        if any(re.match(r'\s*'+name+r'(?:_visible)?\s*=',line) for name in child_names): continue
        main_scripted.append(line.replace('RUS_congress_gui =','RUS_congress_gui_main =').replace('"RUS_congress_window"','"RUS_congress_window_main"').replace('visible = { original_tag = RUS has_country_flag = RUS_congress_demo_initialized }','visible = { original_tag = RUS has_country_flag = RUS_congress_demo_initialized NOT = { has_country_flag = RUS_congress_show_children } }'))
    out['common/scripted_guis/RUS_soviet_congress.txt']='\n'.join(['scripted_gui = {']+main_scripted+full_scripted+['}'])+'\n'
    effects=['# Display state only. Call refresh after changing integer seat counts; their sum must remain 800.',
             'RUS_congress_refresh_display = {', '\tset_temp_variable = { RUS_congress_sum = 0 }']
    for key,_,_,_,_ in PARTIES:
        effects.append(f'\tadd_to_temp_variable = {{ RUS_congress_sum = RUS_congress_{key}_seats }}')
    for parent,children in CHILDREN.items():
        effects += [f'\tset_temp_variable = {{ RUS_congress_{parent}_sum = 0 }}']
        effects += [f'\tadd_to_temp_variable = {{ RUS_congress_{parent}_sum = RUS_congress_{row[0]}_seats }}' for row in children]
    effects += ['\tset_temp_variable = { RUS_congress_civic_sum = 0 }']
    effects += [f'\tadd_to_temp_variable = {{ RUS_congress_civic_sum = {var} }}' for var in CIVIC_SOURCES.values()]
    effects += ['\tif = {', '\t\tlimit = {', '\t\t\tcheck_variable = { RUS_congress_sum = 800 }']
    for parent in CHILDREN:
        effects += [f'\t\t\tcheck_variable = {{ RUS_congress_{parent}_sum = RUS_congress_{parent}_seats }}']
    effects += ['\t\t\tcheck_variable = { RUS_congress_civic_sum = RUS_congress_sr_citizens_seats }']
    for parent,var in CIVIC_SOURCES.items():
        effects += [f'\t\t\tcheck_variable = {{ {var} > -1 }}',
                    f'\t\t\tcheck_variable = {{ {var} <= RUS_congress_{parent}_seats }}']
    for key,_,_,_,_ in ALL_PARTIES:
        effects += [f'\t\t\tcheck_variable = {{ RUS_congress_{key}_seats > -1 }}',f'\t\t\tcheck_variable = {{ RUS_congress_{key}_seats < 801 }}']
    effects += ['\t\t}', '\t\tclear_array = RUS_congress_seats']
    for key,_,_,_,_ in ALL_PARTIES:
        effects += [f'\t\tset_variable = {{ RUS_congress_{key}_percent = RUS_congress_{key}_seats }}',
                    f'\t\tdivide_variable = {{ RUS_congress_{key}_percent = 8 }}']
    def append_seats(row,indent,count_var=None):
        key=row[0]; t='\t'*indent
        return [t+'set_temp_variable = { RUS_congress_i = 0 }',t+'while_loop_effect = {',
                t+f'\tlimit = {{ check_variable = {{ RUS_congress_i < {count_var or "RUS_congress_"+key+"_seats"} }} }}',
                t+f'\tadd_to_array = {{ RUS_congress_seats = {FRAMES[key]} }}',
                t+'\tadd_to_temp_variable = { RUS_congress_i = 1 }',t+'}']
    def append_leaves(row,indent):
        key=row[0]; t='\t'*indent
        if key in CHILDREN:
            result=[line for child in CHILDREN[key] for line in append_leaves(child,indent)]
            if key=='sr': result+=append_seats(SHARED,indent)
            return result
        if key in CIVIC_SOURCES:
            remainder='RUS_congress_'+key+'_remainder'
            return [t+f'set_temp_variable = {{ {remainder} = RUS_congress_{key}_seats }}',
                    t+f'subtract_from_temp_variable = {{ {remainder} = {CIVIC_SOURCES[key]} }}']+append_seats(row,indent,remainder)
        return append_seats(row,indent)
    for row in PARTIES:
        if row[0] in CHILDREN:
            effects += ['\t\tif = {', '\t\t\tlimit = { NOT = { has_country_flag = RUS_congress_show_children } }']
            effects += append_seats(row,3)+['\t\t}']
            effects += ['\t\tif = {', '\t\t\tlimit = { has_country_flag = RUS_congress_show_children }']
            effects += append_leaves(row,3)
            effects += ['\t\t}']
        else: effects += append_seats(row,2)
    effects += ['\t\tadd_to_variable = { RUS_congress_revision = 1 }', '\t}', '}', '',
                'RUS_congress_prepare_demo = {', '\tif = {',
                '\t\tlimit = { NOT = { has_country_flag = RUS_congress_demo_initialized } }']
    effects += [f'\t\tset_variable = {{ RUS_congress_{key}_seats = {count} }}' for key,_,_,count,_ in ALL_PARTIES]
    effects += [f'\t\tset_variable = {{ {var} = 25 }}' for var in CIVIC_SOURCES.values()]
    effects += ['\t\tRUS_congress_refresh_display = yes', '\t\tset_country_flag = RUS_congress_demo_initialized', '\t}', '}']
    out['common/scripted_effects/RUS_soviet_congress.txt']='\n'.join(effects)+'\n'
    out['common/decisions/categories/RUS_soviet_congress.txt']='''# Prototype access follows the existing development GUI launcher.
RUS_congress_category = {
    icon = GFX_decision_category_generic_political_actions
    priority = 110
    allowed = { original_tag = RUS }
    visible = { is_ai = no has_country_flag = RUS_congress_demo_initialized NOT = { has_country_flag = RUS_congress_show_children } }
    visible_when_empty = yes
    scripted_gui = RUS_congress_gui_main
}
RUS_congress_children_category = {
    icon = GFX_decision_category_generic_political_actions
    priority = 110
    allowed = { original_tag = RUS }
    visible = { is_ai = no has_country_flag = RUS_congress_demo_initialized has_country_flag = RUS_congress_show_children }
    visible_when_empty = yes
    scripted_gui = RUS_congress_gui_children
}
RUS_congress_entry_category = {
    icon = GFX_decision_category_generic_political_actions
    priority = 110
    allowed = { original_tag = RUS }
    visible = { is_ai = no NOT = { has_country_flag = RUS_congress_demo_initialized } }
    visible_when_empty = no
}
'''
    out['common/decisions/RUS_soviet_congress.txt']='''RUS_congress_entry_category = {
    RUS_congress_view = {
        icon = GFX_decision_generic_political_discourse
        cost = 0
        visible = { NOT = { has_country_flag = RUS_congress_demo_initialized } }
        available = { hidden_trigger = { original_tag = RUS is_ai = no } }
        complete_effect = {
            custom_effect_tooltip = RUS_congress_view_tt
            hidden_effect = {
                RUS_congress_prepare_demo = yes
                log = "[GetLogRoot]: Congress demo opened; seats=[?RUS_congress_bolsheviks_seats]/[?RUS_congress_unions_seats]/[?RUS_congress_labour_seats]/[?RUS_congress_sr_seats]/[?RUS_congress_democrats_seats]; revision=[?RUS_congress_revision]"
            }
        }
        ai_will_do = { base = 0 }
    }
}
'''
    loc={
        'RUS_congress_category':'苏维埃与工会代表大会',
        'RUS_congress_children_category':'苏维埃与工会代表大会',
        'RUS_congress_children_category_desc':'来自各地苏维埃、工会与社会主义政党的代表齐聚一堂，共商共和国的前途。',
        'RUS_congress_entry_category':'苏维埃与工会代表大会',
        'RUS_congress_entry_category_desc':'召集各派代表，查看大会的席位构成。',
        'RUS_congress_category_desc':'来自各地苏维埃、工会与社会主义政党的代表齐聚一堂，共商共和国的前途。',
        'RUS_congress_view':'查看代表大会（测试）',
        'RUS_congress_view_desc':'查看各派代表的席位分布及大会的议案通过门槛。',
        'RUS_congress_view_tt':'展示苏维埃与工会代表大会的§Y800个席位§!。',
        'RUS_congress_title':'苏维埃与工会代表大会',
        'RUS_congress_bill':'下一项议案：§g尚未提出§!',
        'RUS_congress_threshold':'通过门槛：§Y超过50%§! · §Y401 / 800席§!',
        'RUS_congress_total':'§Y800§!',
        'RUS_congress_total_caption':'代表席位',
        'RUS_congress_toggle':'显示/收起子派系',
        'RUS_congress_column_name':'派系',
        'RUS_congress_column_count':'席位',
        'RUS_congress_column_share':'占比',
    }
    for key,name,_,_,_ in ALL_PARTIES:
        loc['RUS_congress_name_'+key]=name
        loc['RUS_congress_value_'+key]=f'§Y[?RUS.RUS_congress_{key}_seats|0]§!席  /  [?RUS.RUS_congress_{key}_percent|1]%'
        loc['RUS_congress_count_'+key]=f'§Y[?RUS.RUS_congress_{key}_seats|0]§!'
        loc['RUS_congress_share_'+key]=f'[?RUS.RUS_congress_{key}_percent|1]%'
    for parent,rows in CHILDREN.items():
        for key,name,_,_,_ in rows: loc['RUS_congress_childname_'+key]=name.split(' · ')[1]
    loc['RUS_congress_childname_sr_citizens']='公民派'
    portraits=leader_portraits()
    for key,name,_,_,_ in ALL_PARTIES:
        parents=PARENTS.get(key,[])
        lines=['§Y'+('子派系：' if parents else '主派系：')+name+'§!']
        if parents:
            root=parents[0]
            while root in PARENTS: root=PARENTS[root][0]
            lines += ['所属主派系：§Y'+BY_KEY[root][1]+'§!']
            if parents!=[root]: lines += ['所属子派系：§Y'+'、'.join(BY_KEY[p][1].split(' · ')[-1] for p in parents)+'§!']
        if key=='sr_citizens':
            lines += [f'民粹派：[?RUS.{CIVIC_SOURCES["sr_populists"]}|0]席',
                      f'民主派：[?RUS.{CIVIC_SOURCES["sr_democrats"]}|0]席']
        lines += [loc['RUS_congress_value_'+key],'','§Y派系领导人§!']
        for char in LEADERS[key]:
            # Character.GetName is the same native lookup used by the card GUI.
            lines += ['']*(PORTRAIT_LINE_GAP-1)+['£'+portrait_texticon(char)+'  §Y['+char+'.GetName]§!']
        loc['RUS_congress_leaders_'+key+'_tt']='\n'.join(lines).rstrip()
    # The mod's current Chinese-only political preview retains Chinese titles in other UIs.
    for lang in ['simp_chinese','english','russian']:
        out[f'localisation/{lang}/RUS_soviet_congress_l_{lang}.yml']=('\n'.join(['l_'+lang+':']+[' '+k+':0 '+json.dumps(v,ensure_ascii=False) for k,v in loc.items()])+'\n').encode('utf-8-sig')
    return {Path(p):(v.encode('utf-8') if isinstance(v,str) else v) for p,v in out.items()}


def preview(expanded=False):
    """Proof using installed native bitmap font atlases and runtime geometry."""
    from bisect import bisect_right
    import re
    from hoi4_bitmap_fonts import render
    generated=outputs()
    values={k:json.loads(v) for k,v in re.findall(r'^\s+([^ :]+):0 (".*")$',generated[Path('localisation/simp_chinese/RUS_soviet_congress_l_simp_chinese.yml')].decode('utf-8-sig'),re.M)}
    variables={f'RUS.RUS_congress_{key}_seats':count for key,_,_,count,_ in ALL_PARTIES}
    variables.update({f'RUS.RUS_congress_{key}_percent':count/8 for key,_,_,count,_ in ALL_PARTIES})
    def resolved(key):
        return re.sub(r'\[\?([^|\]]+)\|(\d+)\]',lambda m:f'{variables[m[1]]:.{m[2]}f}',values[key])
    im=Image.open(BytesIO(generated[Path('gfx/interface/RUS_soviet_congress/'+('panel.png' if expanded else 'panel_main.png'))])).convert('RGBA')
    im.alpha_composite(Image.open(BytesIO(generated[Path('gfx/interface/RUS_soviet_congress/congress_hall.png')])),(12,12))
    def write(x,y,key,font='hoi_16mbs',width=456,align='center',colour='#ded9c8'):
        render(im,x,y,resolved(key),font,colour,align,width)
    write(12,260,'RUS_congress_title','hoi_24header',476,colour='#efdfb4')
    write(22,302,'RUS_congress_bill')
    write(22,325,'RUS_congress_threshold',colour='#d7b45d')
    write(150,391,'RUS_congress_total','hoi_24header',200,colour='#e4c46f')
    write(150,428,'RUS_congress_total_caption',width=200)
    rows=display_parties(expanded);cuts=[];n=0
    for _,_,_,count,_ in rows: n+=count;cuts.append(n)
    atlas=Image.open(BytesIO(generated[Path('gfx/interface/RUS_soviet_congress/seats.png')]))
    for i,(x,y) in enumerate(seats()):
        frame=FRAMES[rows[bisect_right(cuts,i)][0]]-1
        im.alpha_composite(atlas.crop((frame*6,0,frame*6+6,6)),(x,y))
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((176,356,324,390),radius=3,fill='#343e35',outline='#a99564')
    write(176,364,'RUS_congress_toggle',width=148,colour='#f0e0b9')
    for key,x,w in TABLE_COLUMNS:
        write(x,588,'RUS_congress_column_'+key,'hoi_18mbs',w,'left' if key=='name' else 'right')
    for row,child,y in table_rows(expanded):
        for e in row_elements(row,child,y):
            if e['kind']=='icon':
                frame=FRAMES[e['key']]-1
                tile=atlas.crop((frame*6,0,frame*6+6,6)).resize((e['w'],e['h']),Image.Resampling.NEAREST)
                im.alpha_composite(tile,(e['x'],e['y']))
            else:
                write(e['x'],e['y'],e['loc'],e['font'],e['w'],e['align'], '#e7e0c9' if not child else '#c1c9be')
    path=ROOT/'output/soviet_congress'/('代表大会子派系预览.png' if expanded else '代表大会布局预览.png')
    path.parent.mkdir(parents=True,exist_ok=True)
    im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST).save(path)
    im.save(path.with_stem(path.stem+'_原生尺寸'))
    return path


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--write',action='store_true'); parser.add_argument('--check',action='store_true'); parser.add_argument('--preview',action='store_true')
    args=parser.parse_args(); generated=outputs()
    if args.write:
        for path,data in generated.items():
            target=ROOT/path; target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(data)
        print(f'Wrote {len(generated)} congress files; 800 seats, five parties.')
    else:
        stale=[str(path) for path,data in generated.items() if not (ROOT/path).exists() or (ROOT/path).read_bytes()!=data]
        if stale: raise SystemExit('STALE: '+', '.join(stale))
        print('PASS: congress generated files current; 800 seats, five parties.')
    if args.preview:
        print(preview()); print(preview(True))


if __name__=='__main__':
    main()
