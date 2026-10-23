"""Decision-category prototype. Default is read-only; --write updates owned files.

References: KR common/scripted_guis/_documentation.md, PHI scripted_gui
(Philippines).txt (array-indexed sprite frames), RUS_russian_congress (council
icon), 00_mobilisation_effects.txt (native while_loop_effect), and local
RUS_doudizhu_decisions/categories (free human-only launcher).
Seat dots and panel are geometric UI primitives, not generated illustration.
"""
from pathlib import Path
from io import BytesIO
import argparse
import json
import math
import random

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'RUS_congress'
TOTAL = 800
WIDTH, HEIGHT = 536, 620
PARTIES = [
    ('bolsheviks', '俄罗斯共产党（布尔什维克）', '473', 240, '#d65b60'),
    ('unions', '工会联盟', '275', 160, '#d7b45d'),
    ('labour', '全俄罗斯劳工联盟', '253', 120, '#de915e'),
    ('sr', '社会革命党', '269', 200, '#70b38c'),
    ('democrats', '社会主义民主联盟', '273', 80, '#72a8d3'),
]
CHILDREN = {
    'labour': [
        ('new_youth', '全俄劳联 · 新青年派', '257', 40, '#f0b58a'),
        ('new_theory', '全俄劳联 · 新理论派', '262', 40, '#dc864e'),
        ('new_society', '全俄劳联 · 新社会派', '265', 40, '#b9643e'),
    ],
    'sr': [
        ('sr_populists', '社革党 · 民粹派', '290', 100, '#a0d7b1'),
        ('sr_maximalists', '社革党 · 最高纲领派', '364', 100, '#46966c'),
    ],
}
ALL_PARTIES = PARTIES + [row for rows in CHILDREN.values() for row in rows]
FRAMES = {row[0]:i for i,row in enumerate(ALL_PARTIES,1)}
SHORT_NAMES = dict(zip([p[0] for p in PARTIES],['俄共（布）','工会联盟','全俄劳联','社会革命党','社民盟']))
LEADERS = {
    'bolsheviks': ['RUS_yakov_sverdlov'],
    'unions': ['RUS_mikhail_tomsky'],
    'labour': ['RUS_grigory_zinovyev','RUS_lev_kamenev','RUS_daniil_sulimov','RUS_vladimir_levitsky','RUS_fyodor_dan'],
    'sr': ['RUS_aleksey_ustinov','RUS_maria_spiridonova','RUS_vladimir_rikhter','RUS_pitirim_sorokin'],
    'democrats': ['RUS_gergard_zeller'],
    'new_youth': ['RUS_grigory_zinovyev'],
    'new_theory': ['RUS_daniil_sulimov','RUS_vladimir_levitsky'],
    'new_society': ['RUS_fyodor_dan'],
    'sr_populists': ['RUS_maria_spiridonova','RUS_pitirim_sorokin'],
    'sr_maximalists': ['RUS_aleksey_ustinov'],
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
    return [row for parent in PARTIES for row in (CHILDREN.get(parent[0],[parent]) if expanded else [parent])]


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
            points.append((angle, row, round(268-r*math.cos(angle)-3), round(218+0.82*r*math.sin(angle)-3)))
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
    d.rectangle((12,12,WIDTH-13,133),fill='#292c29',outline='#675e46')
    d.line((22,138,WIDTH-23,138), fill='#807452')
    d.rectangle((22,145,WIDTH-23,193),fill='#191f1e',outline='#5f6555')
    d.line((22,438,WIDTH-23,438),fill='#807452')
    return {'gfx/interface/RUS_soviet_congress/panel.png': png(panel),
            'gfx/interface/RUS_soviet_congress/seats.png': png(atlas)}


def text(name, x,y, key, width=492, height=24, font='hoi_16mbs', align='center', tooltip=None):
    hover=f'pdx_tooltip = "{tooltip}" alwaystransparent = no' if tooltip else 'alwaystransparent = yes'
    return f'\t\tinstantTextBoxType = {{ name = "{name}" position = {{ x = {x} y = {y} }} text = "{key}" font = "{font}" maxWidth = {width} maxHeight = {height} format = {align} fixedsize = yes {hover} }}'


def icon(name,x,y,sprite,extra=''):
    return f'\t\ticonType = {{ name = "{name}" position = {{ x = {x} y = {y} }} spriteType = "{sprite}" {extra} alwaystransparent = yes }}'


def outputs():
    out = assets()
    gui=['# Generated by tools/generate_soviet_congress.py --write', 'guiTypes = {', '\tcontainerWindowType = {',
         '\t\tname = "RUS_congress_window"', '\t\tposition = { x = 0 y = 0 }',
         '\t\tsize = { width = 100% height = 620 }', '\t\tclipping = no',
         icon('RUS_congress_panel',0,0,'GFX_RUS_congress_panel'),
         icon('RUS_congress_emblem',222,17,'GFX_focus_RUS_the_supreme_soviet','scale = 0.95'),
         text('RUS_congress_title',12,99,'RUS_congress_title',512,28,'hoi_20b'),
         text('RUS_congress_bill',22,150,'RUS_congress_bill'),
         text('RUS_congress_threshold',22,173,'RUS_congress_threshold'),
         text('RUS_congress_total',168,233,'RUS_congress_total',200,34,'hoi_24header'),
         text('RUS_congress_total_caption',168,270,'RUS_congress_total_caption',200),
         text('RUS_congress_legend_title',22,418,'RUS_congress_legend_title')]
    for i,(x,y) in enumerate(seats()):
        gui.append(icon(f'RUS_congress_seat_{i}',x,y,'GFX_RUS_congress_seats'))
    for mode,expanded in [('main',False),('children',True)]:
        gui += ['\t\tcontainerWindowType = {', f'\t\t\tname = "RUS_congress_legend_{mode}"',
                '\t\t\tposition = { x = 0 y = 0 }', '\t\t\tsize = { width = 536 height = 620 }']
        if expanded:
            gui += [text('RUS_congress_main_heading',22,418,'RUS_congress_main_heading',236),
                    text('RUS_congress_child_heading',280,418,'RUS_congress_child_heading',236)]
        for i,(key,_,_,_,_) in enumerate(PARTIES):
            y=451+26*i
            gui += [icon(f'RUS_congress_key_{mode}_{key}',25,y+4,'GFX_RUS_congress_seats',f'frame = {FRAMES[key]} scale = 2')]
            if expanded:
                gui += [text(f'RUS_congress_name_{mode}_{key}',43,y,'RUS_congress_short_'+key,112,18,font='Main_14',align='left'),
                        text(f'RUS_congress_value_{mode}_{key}',151,y,'RUS_congress_value_'+key,109,18,font='Main_14',align='right',tooltip='RUS_congress_leaders_'+key+'_tt')]
            else:
                gui += [text(f'RUS_congress_name_{mode}_{key}',47,y,'RUS_congress_name_'+key,332,18,align='left'),
                        text(f'RUS_congress_value_{mode}_{key}',377,y,'RUS_congress_value_'+key,135,18,align='right',tooltip='RUS_congress_leaders_'+key+'_tt')]
        if expanded:
            for parent,heading_y,first_y in [('labour',447,467),('sr',527,547)]:
                gui += [text('RUS_congress_group_'+parent,282,heading_y,'RUS_congress_group_'+parent,232,18,font='Main_14',align='left',tooltip='RUS_congress_leaders_'+parent+'_tt')]
                for i,(key,_,_,_,_) in enumerate(CHILDREN[parent]):
                    y=first_y+18*i
                    gui += [icon('RUS_congress_child_key_'+key,288,y+4,'GFX_RUS_congress_seats',f'frame = {FRAMES[key]} scale = 1.5'),
                            text('RUS_congress_child_name_'+key,302,y,'RUS_congress_childname_'+key,92,18,font='Main_14',align='left'),
                            text('RUS_congress_child_value_'+key,397,y,'RUS_congress_value_'+key,117,18,font='Main_14',align='right',tooltip='RUS_congress_leaders_'+key+'_tt')]
        gui += ['\t\t}']
    for action in ['expand','collapse']:
        gui += [f'\t\tbuttonType = {{ name = "RUS_congress_{action}" position = {{ x = 194 y = 198 }} quadTextureSprite = "GFX_button_148x34" buttonText = "RUS_congress_{action}" buttonFont = "hoi_16mbs" clicksound = click_default }}']
    gui += [text('RUS_congress_footer',22,596,'RUS_congress_footer',height=18), '\t}', '}']
    out['interface/RUS_soviet_congress.gui']='\n'.join(gui)+'\n'
    gfx='''spriteTypes = {
    spriteType = { name = "GFX_RUS_congress_panel" texturefile = "gfx/interface/RUS_soviet_congress/panel.png" noOfFrames = 1 }
    spriteType = { name = "GFX_RUS_congress_seats" texturefile = "gfx/interface/RUS_soviet_congress/seats.png" noOfFrames = 10 }
'''
    for char,texture in leader_textures().items():
        gfx+=f'    spriteType = {{ name = "GFX_{portrait_texticon(char)}" texturefile = "{texture}" noOfFrames = 1 legacy_lazy_load = no }}\n'
    out['interface/RUS_soviet_congress.gfx']=gfx+'}\n'
    scripted=['scripted_gui = {', '\tRUS_congress_gui = {', '\t\tcontext_type = decision_category',
              '\t\twindow_name = "RUS_congress_window"', '\t\tdirty = RUS.RUS_congress_revision',
              '\t\tai_enabled = { always = no }',
              '\t\tvisible = { original_tag = RUS has_country_flag = RUS_congress_demo_initialized }',
              '\t\ttriggers = {',
              '\t\t\tRUS_congress_expand_visible = { RUS = { NOT = { has_country_flag = RUS_congress_show_children } } }',
              '\t\t\tRUS_congress_legend_main_visible = { RUS = { NOT = { has_country_flag = RUS_congress_show_children } } }',
              '\t\t\tRUS_congress_legend_title_visible = { RUS = { NOT = { has_country_flag = RUS_congress_show_children } } }',
              '\t\t\tRUS_congress_collapse_visible = { RUS = { has_country_flag = RUS_congress_show_children } }',
              '\t\t\tRUS_congress_legend_children_visible = { RUS = { has_country_flag = RUS_congress_show_children } }',
              '\t\t}',
              '\t\teffects = {',
              '\t\t\tRUS_congress_expand_click = { hidden_effect = { RUS = { set_country_flag = RUS_congress_show_children RUS_congress_refresh_display = yes log = "[GetLogRoot]: Congress child view; revision=[?RUS_congress_revision]" } } }',
              '\t\t\tRUS_congress_collapse_click = { hidden_effect = { RUS = { clr_country_flag = RUS_congress_show_children RUS_congress_refresh_display = yes log = "[GetLogRoot]: Congress main view; revision=[?RUS_congress_revision]" } } }',
              '\t\t}',
              '\t\tproperties = {']
    scripted += [f'\t\t\tRUS_congress_seat_{i} = {{ frame = RUS.RUS_congress_seats^{i} }}' for i in range(TOTAL)]
    scripted += ['\t\t}', '\t}', '}']
    out['common/scripted_guis/RUS_soviet_congress.txt']='\n'.join(scripted)+'\n'
    effects=['# Display state only. Call refresh after changing integer seat counts; their sum must remain 800.',
             'RUS_congress_refresh_display = {', '\tset_temp_variable = { RUS_congress_sum = 0 }']
    for key,_,_,_,_ in PARTIES:
        effects.append(f'\tadd_to_temp_variable = {{ RUS_congress_sum = RUS_congress_{key}_seats }}')
    for parent,children in CHILDREN.items():
        effects += [f'\tset_temp_variable = {{ RUS_congress_{parent}_sum = 0 }}']
        effects += [f'\tadd_to_temp_variable = {{ RUS_congress_{parent}_sum = RUS_congress_{row[0]}_seats }}' for row in children]
    effects += ['\tif = {', '\t\tlimit = {', '\t\t\tcheck_variable = { RUS_congress_sum = 800 }']
    for parent in CHILDREN:
        effects += [f'\t\t\tcheck_variable = {{ RUS_congress_{parent}_sum = RUS_congress_{parent}_seats }}']
    for key,_,_,_,_ in ALL_PARTIES:
        effects += [f'\t\t\tcheck_variable = {{ RUS_congress_{key}_seats > -1 }}',f'\t\t\tcheck_variable = {{ RUS_congress_{key}_seats < 801 }}']
    effects += ['\t\t}', '\t\tclear_array = RUS_congress_seats']
    for key,_,_,_,_ in ALL_PARTIES:
        effects += [f'\t\tset_variable = {{ RUS_congress_{key}_percent = RUS_congress_{key}_seats }}',
                    f'\t\tdivide_variable = {{ RUS_congress_{key}_percent = 8 }}']
    def append_seats(row,indent):
        key=row[0]; t='\t'*indent
        return [t+'set_temp_variable = { RUS_congress_i = 0 }',t+'while_loop_effect = {',
                t+f'\tlimit = {{ check_variable = {{ RUS_congress_i < RUS_congress_{key}_seats }} }}',
                t+f'\tadd_to_array = {{ RUS_congress_seats = {FRAMES[key]} }}',
                t+'\tadd_to_temp_variable = { RUS_congress_i = 1 }',t+'}']
    for row in PARTIES:
        if row[0] in CHILDREN:
            effects += ['\t\tif = {', '\t\t\tlimit = { NOT = { has_country_flag = RUS_congress_show_children } }']
            effects += append_seats(row,3)+['\t\t}']
            effects += ['\t\tif = {', '\t\t\tlimit = { has_country_flag = RUS_congress_show_children }']
            for child in CHILDREN[row[0]]: effects += append_seats(child,3)
            effects += ['\t\t}']
        else: effects += append_seats(row,2)
    effects += ['\t\tadd_to_variable = { RUS_congress_revision = 1 }', '\t}', '}', '',
                'RUS_congress_prepare_demo = {', '\tif = {',
                '\t\tlimit = { NOT = { has_country_flag = RUS_congress_demo_initialized } }']
    effects += [f'\t\tset_variable = {{ RUS_congress_{key}_seats = {count} }}' for key,_,_,count,_ in ALL_PARTIES]
    effects += ['\t\tRUS_congress_refresh_display = yes', '\t\tset_country_flag = RUS_congress_demo_initialized', '\t}', '}']
    out['common/scripted_effects/RUS_soviet_congress.txt']='\n'.join(effects)+'\n'
    out['common/decisions/categories/RUS_soviet_congress.txt']='''# Prototype access follows the existing development GUI launcher.
RUS_congress_category = {
    icon = GFX_decision_category_generic_political_actions
    priority = 110
    allowed = { original_tag = RUS }
    visible = { is_ai = no has_country_flag = RUS_congress_demo_initialized }
    visible_when_empty = yes
    scripted_gui = RUS_congress_gui
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
        'RUS_congress_legend_title':'各派代表 · 席位与占比',
        'RUS_congress_footer':'§g每个色点代表1席 · 共800席§!',
        'RUS_congress_expand':'显示子派系',
        'RUS_congress_collapse':'仅显示大派系',
        'RUS_congress_main_heading':'主派系 · 总席位',
        'RUS_congress_child_heading':'子派系 · 已计入左侧',
    }
    for key,name,_,_,_ in ALL_PARTIES:
        loc['RUS_congress_name_'+key]=name
        loc['RUS_congress_value_'+key]=f'§Y[?RUS.RUS_congress_{key}_seats|0]§!席  /  [?RUS.RUS_congress_{key}_percent|1]%'
    for key,value in SHORT_NAMES.items(): loc['RUS_congress_short_'+key]=value
    for parent,rows in CHILDREN.items():
        loc['RUS_congress_group_'+parent]=f'§Y{SHORT_NAMES[parent]} · [?RUS.RUS_congress_{parent}_seats|0]席§!'
        for key,name,_,_,_ in rows: loc['RUS_congress_childname_'+key]=name.split(' · ')[1]
    portraits=leader_portraits()
    for key,name,_,_,_ in ALL_PARTIES:
        parent=next((parent for parent,children in CHILDREN.items() if any(row[0]==key for row in children)),None)
        lines=['§Y'+('子派系：' if parent else '主派系：')+name+'§!']
        if parent: lines += ['所属主派系：§Y'+next(row[1] for row in PARTIES if row[0]==parent)+'§!']
        lines += [loc['RUS_congress_value_'+key],'','§Y派系领导人§!']
        for char in LEADERS[key]:
            # Character.GetName is the same native lookup used by the card GUI.
            lines += ['£'+portrait_texticon(char)+'  §Y['+char+'.GetName]§!','']
        loc['RUS_congress_leaders_'+key+'_tt']='\n'.join(lines).rstrip()
    # The mod's current Chinese-only political preview retains Chinese titles in other UIs.
    for lang in ['simp_chinese','english','russian']:
        out[f'localisation/{lang}/RUS_soviet_congress_l_{lang}.yml']=('\n'.join(['l_'+lang+':']+[' '+k+':0 '+json.dumps(v,ensure_ascii=False) for k,v in loc.items()])+'\n').encode('utf-8-sig')
    return {Path(p):(v.encode('utf-8') if isinstance(v,str) else v) for p,v in out.items()}


def preview(expanded=False):
    """Layout proof from the exact runtime geometry; not an in-game screenshot."""
    from bisect import bisect_right
    scale=2
    im=Image.open(BytesIO(assets()['gfx/interface/RUS_soviet_congress/panel.png'])).convert('RGBA').resize((WIDTH*scale,HEIGHT*scale))
    emblem=Image.open(ROOT/'gfx/GFX_focus_RUS_the_supreme_soviet.png').convert('RGBA')
    emblem=emblem.resize((round(emblem.width*.95*scale),round(emblem.height*.95*scale)),Image.Resampling.LANCZOS)
    im.alpha_composite(emblem,(222*scale,17*scale))
    d=ImageDraw.Draw(im)
    def write(x,y,value,size=15,colour='#ded9c8',center=False):
        font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',size*scale)
        if center: x-=d.textlength(value,font=font)/scale/2
        d.text((x*scale,y*scale),value,font=font,fill=colour)
    write(268,99,'苏维埃与工会代表大会',20,'#f1e3b7',True)
    write(268,150,'下一项议案：尚未提出',14,center=True)
    write(268,173,'通过门槛：超过50% · 401 / 800席',14,'#d7b45d',True)
    write(268,233,'800',26,'#e4c46f',True); write(268,270,'代表席位',14,center=True)
    cuts=[]; n=0
    rows=display_parties(expanded)
    for _,_,_,count,_ in rows: n+=count; cuts.append(n)
    atlas=Image.open(BytesIO(assets()['gfx/interface/RUS_soviet_congress/seats.png']))
    for i,(x,y) in enumerate(seats()):
        frame=FRAMES[rows[bisect_right(cuts,i)][0]]-1
        tile=atlas.crop((frame*6,0,frame*6+6,6)).resize((12,12),Image.Resampling.NEAREST)
        im.alpha_composite(tile,(x*scale,y*scale))
    if expanded:
        write(140,418,'主派系 · 总席位',14,center=True)
        write(398,418,'子派系 · 已计入左侧',14,center=True)
    else: write(268,418,'各派代表 · 席位与占比',14,center=True)
    d.rounded_rectangle((194*scale,198*scale,342*scale,232*scale),radius=3*scale,fill='#343e35',outline='#a99564')
    write(268,204,'仅显示大派系' if expanded else '显示子派系',14,'#f0e0b9',True)
    for i,(key,name,_,count,colour) in enumerate(PARTIES):
        y=451+26*i
        d.rectangle((25*scale,(y+4)*scale,35*scale,(y+14)*scale),fill=colour)
        if expanded:
            write(43,y,SHORT_NAMES[key],13); write(155,y,f'{count}席 / {count/8:.1f}%',12,'#e1d5b3')
        else:
            write(47,y,name,14); write(379,y,f'{count}席 / {count/8:.1f}%',14,'#e1d5b3')
    if expanded:
        d.line((270*scale,447*scale,270*scale,581*scale), fill='#615c46')
        for parent,heading_y,first_y in [('labour',447,467),('sr',527,547)]:
            parent_count=next(r[3] for r in PARTIES if r[0]==parent)
            write(282,heading_y,f'{SHORT_NAMES[parent]} · {parent_count}席',13,'#d7b45d')
            for i,(_,name,_,count,colour) in enumerate(CHILDREN[parent]):
                y=first_y+18*i
                d.rectangle((288*scale,(y+4)*scale,296*scale,(y+12)*scale),fill=colour)
                write(302,y,name.split(' · ')[1],12); write(400,y,f'{count}席 / {count/8:.1f}%',12,'#e1d5b3')
    write(268,596,'每个色点代表1席 · 共800席',13,'#a6ad9f',True)
    path=ROOT/'output/soviet_congress'/('代表大会子派系预览.png' if expanded else '代表大会布局预览.png'); path.parent.mkdir(parents=True,exist_ok=True); im.save(path)
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
