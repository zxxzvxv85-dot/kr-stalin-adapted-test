"""Dynamic read-only industrial scene and project ledger. Used by the maintained generator."""
import re
from hoi4_politics_blocks import parse

def augment(out,groups,g):
    text=out[g.DECISIONS]
    text=re.sub(r'(?ms)^[ \t]*# RUS_RECOVERY_LEDGER_BEGIN\n.*?^[ \t]*# RUS_RECOVERY_LEDGER_END[ \t]*\n','',text)
    cat=next(n for n in parse(text) if n.k==g.CATEGORY)
    projects=[n for n in cat.v if isinstance(n.v,list) and n.one('days_remove') and n.one('remove_effect')]
    edits=[]
    for n in projects:
        end=n.one('remove_effect')
        line_start=text.rfind('\n',0,end.ib)+1
        at=line_start if not text[line_start:end.ib].strip() else end.ib
        prefix='' if at==line_start else '\n'
        edits.append((at,prefix+' # RUS_RECOVERY_LEDGER_BEGIN\n hidden_effect = { set_country_flag = RUS_rc_finished_'+n.k+' }\n # RUS_RECOVERY_LEDGER_END\n'))
    for at,s in sorted(edits,reverse=True):text=text[:at]+s+text[at:]
    out[g.DECISIONS]=text
    art=g.ART+'/dynamic'
    gui=['guiTypes = {','containerWindowType = { name = "RUS_rc_window" position = { x = 0 y = 0 } size = { width = 504 height = 574 }',
         'iconType = { name = "plate" position = { x = 6 y = 0 } spriteType = "GFX_RUS_rc_dynamic_plate" alwaystransparent = yes }']
    gfx=['spriteTypes = {',f'spriteType = {{ name = "GFX_RUS_rc_dynamic_plate" texturefile = "{art}/scene.png" noOfFrames = 3 }}',
         f'corneredTileSpriteType = {{ name = "GFX_RUS_rc_ledger_frame" texturefile = "{art}/frame.png" size = {{ x = 492 y = 166 }} borderSize = {{ x = 6 y = 6 }} }}',
         f'spriteType = {{ name = "GFX_RUS_rc_ledger_texture" texturefile = "{art}/ledger.png" }}',
         f'frameAnimatedSpriteType = {{ name = "GFX_RUS_rc_working" texturefile = "{art}/gear_spin.png" noOfFrames = 12 animation_rate_fps = 6 looping = yes play_on_show = yes alwaystransparent = yes }}',
         f'frameAnimatedSpriteType = {{ name = "GFX_RUS_rc_dust" texturefile = "{art}/dust.png" noOfFrames = 12 animation_rate_fps = 4 looping = yes play_on_show = yes alwaystransparent = yes }}']
    gfx.append(f'spriteType = {{ name = "GFX_RUS_rc_reset" texturefile = "{art}/reset.png" effectFile = "gfx/FX/buttonstate.lua" }}')
    props=['plate = { frame = RUS_rc_scene_frame }'];eff=[];vis=[]
    def label(name,x,y,w,h,font,text,align='left'):
        gui.append(f'instantTextBoxType = {{ name = "{name}" position = {{ x = {x} y = {y} }} font = "{font}" text = "{text}" maxWidth = {w} maxHeight = {h} format = {align} alwaystransparent = yes }}')
    def icon(name,x,y,sprite):gui.append(f'iconType = {{ name = "{name}" position = {{ x = {x} y = {y} }} spriteType = "{sprite}" alwaystransparent = yes }}')
    label('title',28,24,450,22,'hoi_18mbs','RUS_rc_title')
    label('status',30,354,445,18,'hoi_16mbs','RUS_rc_status')
    icon('recovery',30,381,'GFX_RUS_rc_recovery')
    gfx.append(f'spriteType = {{ name = "GFX_RUS_rc_recovery" texturefile = "{art}/recovery.png" noOfFrames = 7 }}')
    props.append('recovery = { frame = RUS_rc_recovery_frame }')
    for key,index,x,y,w,h in g.ZONES:
        gui.append(f'buttonType = {{ name = "{key}" position = {{ x = {x+6} y = {y} }} quadTextureSprite = "GFX_RUS_rc_dynamic_{key}" clicksound = click_default pdx_tooltip = RUS_rc_{key}_tt }}')
        gfx.append(f'spriteType = {{ name = "GFX_RUS_rc_dynamic_{key}" texturefile = "{art}/{key}.png" noOfFrames = 3 transparencecheck = yes effectFile = "gfx/FX/buttonstate.lua" }}')
        gfx.append(f'spriteType = {{ name = "GFX_RUS_rc_selected_{key}" texturefile = "{art}/{key}_selected.png" }}')
        icon('selected_'+key,x+6,y,'GFX_RUS_rc_selected_'+key)
        vis.append(f'selected_{key}_visible = {{ NOT = {{ has_country_flag = RUS_rc_blueprint_view }} check_variable = {{ RUS_rc_filter = {index} }} }}')
        vis.append(f'{key}_visible = {{ NOT = {{ has_country_flag = RUS_rc_blueprint_view }} }}')
        props.append(f'{key} = {{ frame = RUS_rc_scene_frame }}')
        eff.append(f'{key}_click = {{ hidden_effect = {{ if = {{ limit = {{ RUS_rc_provisional_phase = yes }} set_variable = {{ RUS_rc_filter = {index} }} }} }} }}')
    vis.append('plate_visible = { NOT = { has_country_flag = RUS_rc_blueprint_view } }')
    # An alternate engineering diagram assembled from the inspected library assets.
    gui.insert(3,'iconType = { name = "blueprint_plate" position = { x = 6 y = 0 } spriteType = "GFX_RUS_rc_blueprint_plate" alwaystransparent = yes }')
    gfx.append(f'spriteType = {{ name = "GFX_RUS_rc_blueprint_plate" texturefile = "{art}/blueprint_scene.png" noOfFrames = 3 }}')
    props.append('blueprint_plate = { frame = RUS_rc_scene_frame }')
    vis.append('blueprint_plate_visible = { has_country_flag = RUS_rc_blueprint_view }')
    for key,index,x,y,w,h in [('relief',1,42,165,100,90),('factory',2,190,128,110,100),('rail',3,105,260,110,80),('road',4,346,249,110,90)]:
        gui.append(f'buttonType = {{ name = "bp_{key}" position = {{ x = {x+6} y = {y} }} quadTextureSprite = "GFX_RUS_rc_bp_{key}" clicksound = click_default pdx_tooltip = RUS_rc_{key}_tt }}')
        gfx.append(f'spriteType = {{ name = "GFX_RUS_rc_bp_{key}" texturefile = "{art}/bp_{key}.png" noOfFrames = 3 transparencecheck = yes effectFile = "gfx/FX/buttonstate.lua" }}')
        props.append(f'bp_{key} = {{ frame = RUS_rc_scene_frame }}')
        vis.append(f'bp_{key}_visible = {{ has_country_flag = RUS_rc_blueprint_view }}')
        eff.append(f'bp_{key}_click = {{ hidden_effect = {{ if = {{ limit = {{ RUS_rc_provisional_phase = yes }} set_variable = {{ RUS_rc_filter = {index} }} }} }} }}')
        label('bp_label_'+key,x+6,y+h-18,w,18,'hoi_16mbs','RUS_rc_'+key,'center')
        vis.append(f'bp_label_{key}_visible = {{ has_country_flag = RUS_rc_blueprint_view }}')
    toggle_gui=('buttonType = { name = "view_toggle" position = { x = 350 y = 409 } quadTextureSprite = "GFX_RUS_rc_view_toggle" buttonText = "RUS_rc_view_toggle" buttonFont = "hoi_16mbs" clicksound = click_default pdx_tooltip = RUS_rc_view_toggle_tt }')
    gfx.append(f'spriteType = {{ name = "GFX_RUS_rc_view_toggle" texturefile = "{art}/view_toggle.png" effectFile = "gfx/FX/buttonstate.lua" }}')
    eff.append('view_toggle_click = { hidden_effect = { if = { limit = { RUS_rc_provisional_phase = yes } if = { limit = { has_country_flag = RUS_rc_blueprint_view } clr_country_flag = RUS_rc_blueprint_view } else = { set_country_flag = RUS_rc_blueprint_view } } } }')
    icon('dust',355,294,'GFX_RUS_rc_dust');vis.append('dust_visible = { NOT = { has_country_flag = RUS_rc_blueprint_view } check_variable = { RUS_rc_active_road > 0 } }')
    icon('ledger_texture',6,404,'GFX_RUS_rc_ledger_texture');icon('ledger_frame',6,404,'GFX_RUS_rc_ledger_frame')
    gui.append(toggle_gui)
    label('selection',22,413,320,20,'hoi_18mbs','RUS_rc_selection')
    gui.append('buttonType = { name = "reset" position = { x = 448 y = 409 } quadTextureSprite = "GFX_RUS_rc_reset" buttonText = "RUS_rc_reset" buttonFont = "hoi_16mbs" clicksound = click_default pdx_tooltip = RUS_rc_reset_tt }')
    eff.append('reset_click = { hidden_effect = { if = { limit = { RUS_rc_provisional_phase = yes } set_variable = { RUS_rc_filter = 0 } } } }')
    # Four connected work orders; same clicks as scene silhouettes, no extra project rewards.
    for j,(key,index,*_) in enumerate(g.ZONES):
        x=20+(j%2)*242;y=443+(j//2)*52
        gui.append(f'buttonType = {{ name = "order_{key}" position = {{ x = {x} y = {y} }} quadTextureSprite = "GFX_RUS_rc_order" clicksound = click_default pdx_tooltip = RUS_rc_{key}_tt }}')
        icon('order_icon_'+key,x+8,y+6,'GFX_RUS_rc_order_'+key)
        label('order_title_'+key,x+43,y+4,169,18,'hoi_16mbs','RUS_rc_'+key)
        label('order_stats_'+key,x+43,y+23,175,17,'hoi_14','RUS_rc_order_stats_'+key)
        icon('working_'+key,x+204,y+4,'GFX_RUS_rc_working');vis.append(f'working_{key}_visible = {{ check_variable = {{ RUS_rc_active_{key} > 0 }} }}')
        eff.append(f'order_{key}_click = {{ hidden_effect = {{ if = {{ limit = {{ RUS_rc_provisional_phase = yes }} set_variable = {{ RUS_rc_filter = {index} }} }} }} }}')
    gfx += [f'spriteType = {{ name = "GFX_RUS_rc_order" texturefile = "{art}/order.png" effectFile = "gfx/FX/buttonstate.lua" }}']
    for key,asset in [('relief','coins'),('factory','factory'),('rail','blueprint'),('road','tools')]:
        gfx.append(f'spriteType = {{ name = "GFX_RUS_rc_order_{key}" texturefile = "{art}/{asset}_icon.png" }}')
    # Temporary display values are rebuilt from engine timers and completion flags.
    calc=['set_temp_variable = { RUS_rc_active = 0 }','set_temp_variable = { RUS_rc_done = 0 }','set_temp_variable = { RUS_rc_next_days = 0 }','set_temp_variable = { RUS_rc_scene_frame = 1 }']
    for key,*_ in g.ZONES:
        calc += [f'set_temp_variable = {{ RUS_rc_active_{key} = 0 }}',f'set_temp_variable = {{ RUS_rc_done_{key} = 0 }}']
    for n in projects:
        keys=[k for k,i,*_ in g.ZONES if i in groups[n.k]]
        calc.append(f'set_temp_variable = {{ RUS_rc_left = days_decision_timeout@{n.k} }}')
        active=['add_to_temp_variable = { RUS_rc_active = 1 }']+[f'add_to_temp_variable = {{ RUS_rc_active_{k} = 1 }}' for k in keys]
        active.append('if = { limit = { OR = { check_variable = { RUS_rc_next_days = 0 } check_variable = { RUS_rc_left < RUS_rc_next_days } } } set_temp_variable = { RUS_rc_next_days = RUS_rc_left } }')
        calc.append('if = { limit = { check_variable = { RUS_rc_left > 0 } } '+' '.join(active)+' }')
        calc.append(f'if = {{ limit = {{ has_country_flag = RUS_rc_finished_{n.k} }} add_to_temp_variable = {{ RUS_rc_done = 1 }} '+' '.join(f'add_to_temp_variable = {{ RUS_rc_done_{k} = 1 }}' for k in keys)+' }')
    calc += ['set_temp_variable = { RUS_rc_recovery_frame = 7 }']
    for level in range(1,7):
        calc.append(f'if = {{ limit = {{ has_idea = RUS_black_monday_{level} }} set_temp_variable = {{ RUS_rc_recovery_frame = {7-level} }} }}')
    calc += ['if = { limit = { NOT = { OR = { has_idea = RUS_black_monday_6 has_idea = RUS_black_monday_5 } } } set_temp_variable = { RUS_rc_scene_frame = 2 } }',
             'if = { limit = { NOT = { OR = { has_idea = RUS_black_monday_6 has_idea = RUS_black_monday_5 has_idea = RUS_black_monday_4 has_idea = RUS_black_monday_3 } } } set_temp_variable = { RUS_rc_scene_frame = 3 } }',
             'if = { limit = { check_variable = { RUS_rc_active > 0 } } set_temp_variable = { RUS_rc_scene_frame = 2 } }']
    icon('project_clock',438,66,'GFX_RUS_rc_clock')
    gfx.insert(-1,f'spriteType = {{ name = "GFX_RUS_rc_clock" texturefile = "{art}/clock_icon.png" }}')
    vis.append('project_clock_visible = { check_variable = { RUS_rc_active > 0 } }')
    label('summary',30,57,402,40,'hoi_16mbs','RUS_rc_summary')
    gui+=['}','}'];gfx+=['}']
    out['interface/RUS_provisional_industry.gui']='\n'.join(gui)+'\n'
    out['interface/RUS_provisional_industry.gfx']='\n'.join(gfx)+'\n'
    out['common/scripted_guis/RUS_provisional_industry_gui.txt']='scripted_gui = { RUS_rc_dashboard = { context_type = decision_category window_name = "RUS_rc_window" visible = { RUS_rc_provisional_phase = yes }\ntriggers = { _ = {\n'+'\n'.join(calc)+'\n}\n'+'\n'.join(vis)+'\n}\nproperties = {\n'+'\n'.join(props)+'\n}\neffects = {\n'+'\n'.join(eff)+'\n}\n} }\n'
    for lang in ('simp_chinese','english','russian'):
        p=f'localisation/{lang}/RUS_provisional_industry_l_{lang}.yml'
        extra={'RUS_rc_summary':'在建工程：§Y[?RUS_rc_active|0]§!    竣工项目：§G[?RUS_rc_done|0]§!\\n[RUSRecoveryNextCompletion]',
               'RUS_rc_no_work':'暂无在建工程','RUS_rc_next_work':'最近竣工：§Y[?RUS_rc_next_days|0]§! 天','RUS_rc_view_toggle':'施工图','RUS_rc_view_toggle_tt':'切换厂区与施工图视图','RUS_rc_reset':'×','RUS_rc_reset_tt':'显示全部工程'}
        for key,*_ in g.ZONES:extra['RUS_rc_order_stats_'+key]=f'在建 §Y[?RUS_rc_active_{key}|0]§!   竣工 §G[?RUS_rc_done_{key}|0]§!'
        if lang!='simp_chinese':
            extra['RUS_rc_summary']='Active: §Y[?RUS_rc_active|0]§!    Completed: §G[?RUS_rc_done|0]§!\\n[RUSRecoveryNextCompletion]'
            extra['RUS_rc_reset_tt']='Show all projects'
            extra['RUS_rc_no_work']='No projects in progress'
            extra['RUS_rc_next_work']='Next completion: §Y[?RUS_rc_next_days|0]§! days'
            for key,*_ in g.ZONES:extra['RUS_rc_order_stats_'+key]=f'Active §Y[?RUS_rc_active_{key}|0]§!  Done §G[?RUS_rc_done_{key}|0]§!'
        if lang=='english':
            extra['RUS_rc_view_toggle']='Diagram'
            extra['RUS_rc_view_toggle_tt']='Switch site and engineering diagram views'
        if lang=='russian':
            extra['RUS_rc_summary']='В работе: §Y[?RUS_rc_active|0]§!    Завершено: §G[?RUS_rc_done|0]§!\\n[RUSRecoveryNextCompletion]'
            extra['RUS_rc_no_work']='Нет действующих проектов'
            extra['RUS_rc_next_work']='Ближайшее завершение: §Y[?RUS_rc_next_days|0]§! дн.'
            extra['RUS_rc_reset_tt']='Показать все проекты'
            extra['RUS_rc_view_toggle']='Схема'
            extra['RUS_rc_view_toggle_tt']='Переключить вид площадки и инженерную схему'
            for key,*_ in g.ZONES:extra['RUS_rc_order_stats_'+key]=f'В работе §Y[?RUS_rc_active_{key}|0]§!  Готово §G[?RUS_rc_done_{key}|0]§!'
        out[p]+=''.join(f' {k}:0 "{v}"\n' for k,v in extra.items())
    out['common/scripted_localisation/RUS_provisional_industry_loc.txt'] += 'defined_text = { name = RUSRecoveryNextCompletion text = { trigger = { check_variable = { RUS_rc_active > 0 } } localization_key = RUS_rc_next_work } text = { localization_key = RUS_rc_no_work } }\n'
    return out
