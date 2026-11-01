"""Dynamic read-only industrial scene and project ledger. Used by the maintained generator."""
import re
from hoi4_politics_blocks import parse

def augment(out,groups,g):
    text=out[g.DECISIONS]
    text=re.sub(r'(?ms)^[ \t]*# RUS_RECOVERY_LEDGER_BEGIN\n.*?^[ \t]*# RUS_RECOVERY_LEDGER_END[ \t]*\n','',text)
    cat=next(n for n in parse(text) if n.k==g.CATEGORY)
    projects=[n for n in cat.v if isinstance(n.v,list) and n.one('days_remove') and n.one('remove_effect')]
    edits=[]
    def observe(n,field,code):
        effect=n.one(field)
        if effect:
            at=effect.ib;line=text.rfind('\n',0,at)+1
            if not text[line:at].strip():at=line;prefix=''
            else:prefix='\n'
            body='hidden_effect = { '+code+' }'
        else:
            at=n.ib;line=text.rfind('\n',0,at)+1
            if not text[line:at].strip():at=line;prefix=''
            else:prefix='\n'
            body=field+' = { hidden_effect = { '+code+' } }'
        edits.append((at,prefix+' # RUS_RECOVERY_LEDGER_BEGIN\n '+body+'\n # RUS_RECOVERY_LEDGER_END\n'))
    for n in projects:
        observe(n,'complete_effect','set_country_flag = RUS_rc_running_'+n.k+' clr_country_flag = RUS_rc_settled_'+n.k+' RUS_rc_refresh = yes')
        observe(n,'remove_effect','set_country_flag = RUS_rc_finished_'+n.k+' set_country_flag = RUS_rc_settled_'+n.k+' clr_country_flag = RUS_rc_running_'+n.k+' RUS_rc_refresh = yes')
        observe(n,'cancel_effect','set_country_flag = RUS_rc_settled_'+n.k+' clr_country_flag = RUS_rc_running_'+n.k+' RUS_rc_refresh = yes')
    for at,s in sorted(edits,reverse=True):text=text[:at]+s+text[at:]
    overview=next(n for n in parse(text) if n.k==g.CATEGORY).one('RUS_rc_overview')
    hook=overview.one('complete_effect').one('hidden_effect')
    if 'RUS_rc_refresh' not in hook.raw():text=text[:hook.ib]+' RUS_rc_refresh = yes '+text[hook.ib:]
    out[g.DECISIONS]=text
    art=g.ART+'/dynamic'
    gui=['guiTypes = {','containerWindowType = { name = "RUS_rc_window" position = { x = 0 y = 0 } size = { width = 504 height = 574 }',
         'iconType = { name = "plate" position = { x = 6 y = 0 } spriteType = "GFX_RUS_rc_dynamic_plate" alwaystransparent = yes }']
    gfx=['spriteTypes = {',f'spriteType = {{ name = "GFX_RUS_rc_dynamic_plate" texturefile = "{art}/scene.png" noOfFrames = 3 }}',
         f'corneredTileSpriteType = {{ name = "GFX_RUS_rc_ledger_frame" texturefile = "{art}/frame.png" size = {{ x = 492 y = 166 }} borderSize = {{ x = 6 y = 6 }} }}',
         f'spriteType = {{ name = "GFX_RUS_rc_ledger_texture" texturefile = "{art}/ledger.png" }}',
         f'frameAnimatedSpriteType = {{ name = "GFX_RUS_rc_working" texturefile = "{art}/gear_spin.png" noOfFrames = 12 animation_rate_fps = 6 looping = yes play_on_show = yes alwaystransparent = yes }}',
         f'frameAnimatedSpriteType = {{ name = "GFX_RUS_rc_dust" texturefile = "{art}/dust.png" noOfFrames = 12 animation_rate_fps = 4 looping = yes play_on_show = yes alwaystransparent = yes }}']
    props=['plate = { frame = RUS_rc_scene_frame }'];eff=[];vis=[]
    def label(name,x,y,w,h,font,text,align='left'):
        gui.append(f'instantTextBoxType = {{ name = "{name}" position = {{ x = {x} y = {y} }} font = "{font}" text = "{text}" maxWidth = {w} maxHeight = {h} format = {align} alwaystransparent = yes }}')
    def icon(name,x,y,sprite):gui.append(f'iconType = {{ name = "{name}" position = {{ x = {x} y = {y} }} spriteType = "{sprite}" alwaystransparent = yes }}')
    label('title',28,24,450,22,'hoi_18mbs','RUS_rc_title')
    icon('recovery',30,381,'GFX_RUS_rc_recovery')
    gfx.append(f'spriteType = {{ name = "GFX_RUS_rc_recovery" texturefile = "{art}/recovery.png" noOfFrames = 7 }}')
    props.append('recovery = { frame = RUS_rc_recovery_frame }')
    for key,index,x,y,w,h in g.ZONES:
        gui.append(f'buttonType = {{ name = "{key}" position = {{ x = {x+6} y = {y} }} quadTextureSprite = "GFX_RUS_rc_dynamic_{key}" clicksound = click_default pdx_tooltip = RUS_rc_{key}_tt }}')
        gfx.append(f'spriteType = {{ name = "GFX_RUS_rc_dynamic_{key}" texturefile = "{art}/{key}.png" noOfFrames = 3 transparencecheck = yes effectFile = "gfx/FX/buttonstate.lua" }}')
        props.append(f'{key} = {{ frame = RUS_rc_frame_{key} }}')
        eff.append(f'{key}_click = {{ hidden_effect = {{ if = {{ limit = {{ RUS_rc_provisional_phase = yes }} set_variable = {{ RUS_rc_filter = {index} }} RUS_rc_refresh = yes }} }} }}')
    icon('dust',355,294,'GFX_RUS_rc_dust');vis.append('dust_visible = { check_variable = { RUS_rc_active_road > 0 } }')
    icon('rail_steam',145,230,'GFX_RUS_rc_dust');vis.append('rail_steam_visible = { check_variable = { RUS_rc_active_rail > 0 } }')
    icon('ledger_texture',6,404,'GFX_RUS_rc_ledger_texture');icon('ledger_frame',6,404,'GFX_RUS_rc_ledger_frame')
    label('selection',22,413,450,20,'hoi_18mbs','RUS_rc_selection')
    # Four connected work orders; same clicks as scene silhouettes, no extra project rewards.
    for j,(key,index,*_) in enumerate(g.ZONES):
        x=20+(j%2)*242;y=443+(j//2)*52
        gui.append(f'buttonType = {{ name = "order_{key}" position = {{ x = {x} y = {y} }} quadTextureSprite = "GFX_RUS_rc_order" clicksound = click_default pdx_tooltip = RUS_rc_{key}_tt }}')
        icon('order_icon_'+key,x+8,y+6,'GFX_RUS_rc_order_'+key)
        label('order_title_'+key,x+43,y+4,169,18,'hoi_16mbs','RUS_rc_'+key)
        label('order_stats_'+key,x+43,y+23,175,18,'hoi_16mbs','RUS_rc_order_stats_'+key)
        icon('working_'+key,x+204,y+4,'GFX_RUS_rc_working');vis.append(f'working_{key}_visible = {{ check_variable = {{ RUS_rc_active_{key} > 0 }} }}')
        eff.append(f'order_{key}_click = {{ hidden_effect = {{ if = {{ limit = {{ RUS_rc_provisional_phase = yes }} set_variable = {{ RUS_rc_filter = {index} }} RUS_rc_refresh = yes }} }} }}')
    gfx += [f'spriteType = {{ name = "GFX_RUS_rc_order" texturefile = "{art}/order.png" effectFile = "gfx/FX/buttonstate.lua" }}']
    for key,asset in [('relief','coins'),('factory','factory'),('rail','train'),('road','tools')]:
        gfx.append(f'spriteType = {{ name = "GFX_RUS_rc_order_{key}" texturefile = "{art}/{asset}_icon.png" }}')
    # Temporary display values are rebuilt from engine timers and completion flags.
    calc=['set_variable = { RUS_rc_active = 0 }','set_variable = { RUS_rc_done = 0 }','set_variable = { RUS_rc_next_days = 0 }','set_variable = { RUS_rc_scene_frame = 1 }']
    for key,*_ in g.ZONES:
        calc += [f'set_variable = {{ RUS_rc_active_{key} = 0 }}',f'set_variable = {{ RUS_rc_done_{key} = 0 }}']
    for n in projects:
        keys=[k for k,i,*_ in g.ZONES if i in groups[n.k]]
        calc.append(f'set_variable = {{ RUS_rc_left = days_decision_timeout@{n.k} }}')
        active=['add_to_variable = { RUS_rc_active = 1 }']+[f'add_to_variable = {{ RUS_rc_active_{k} = 1 }}' for k in keys]
        active.append('if = { limit = { check_variable = { RUS_rc_left > 0 } OR = { check_variable = { RUS_rc_next_days = 0 } check_variable = { RUS_rc_left < RUS_rc_next_days } } } set_variable = { RUS_rc_next_days = RUS_rc_left } }')
        calc.append('if = { limit = { NOT = { has_country_flag = RUS_rc_settled_'+n.k+' } OR = { check_variable = { RUS_rc_left > 0 } has_country_flag = RUS_rc_running_'+n.k+' } } '+' '.join(active)+' }')
        calc.append(f'if = {{ limit = {{ has_country_flag = RUS_rc_finished_{n.k} }} add_to_variable = {{ RUS_rc_done = 1 }} '+' '.join(f'add_to_variable = {{ RUS_rc_done_{k} = 1 }}' for k in keys)+' }')
    calc += ['set_variable = { RUS_rc_recovery_frame = 7 }']
    for level in range(1,7):
        calc.append(f'if = {{ limit = {{ has_idea = RUS_black_monday_{level} }} set_variable = {{ RUS_rc_recovery_frame = {7-level} }} }}')
    calc += ['if = { limit = { NOT = { OR = { has_idea = RUS_black_monday_6 has_idea = RUS_black_monday_5 } } } set_variable = { RUS_rc_scene_frame = 2 } }',
             'if = { limit = { NOT = { OR = { has_idea = RUS_black_monday_6 has_idea = RUS_black_monday_5 has_idea = RUS_black_monday_4 has_idea = RUS_black_monday_3 } } } set_variable = { RUS_rc_scene_frame = 3 } }',
             ]
    for key,*_ in g.ZONES:
        calc += [f'set_variable = {{ RUS_rc_frame_{key} = RUS_rc_scene_frame }}',f'if = {{ limit = {{ check_variable = {{ RUS_rc_done_{key} > 0 }} }} set_variable = {{ RUS_rc_frame_{key} = 3 }} }}',f'if = {{ limit = {{ check_variable = {{ RUS_rc_active_{key} > 0 }} }} set_variable = {{ RUS_rc_frame_{key} = 2 }} }}']
    icon('project_clock',438,66,'GFX_RUS_rc_clock')
    gfx.insert(-1,f'spriteType = {{ name = "GFX_RUS_rc_clock" texturefile = "{art}/clock_icon.png" }}')
    vis.append('project_clock_visible = { check_variable = { RUS_rc_active > 0 } }')
    label('summary',30,57,402,40,'hoi_16mbs','RUS_rc_summary')
    gui+=['}','}'];gfx+=['}']
    out['interface/RUS_provisional_industry.gui']='\n'.join(gui)+'\n'
    out['interface/RUS_provisional_industry.gfx']='\n'.join(gfx)+'\n'
    out['common/scripted_guis/RUS_provisional_industry_gui.txt']='scripted_gui = { RUS_rc_dashboard = { context_type = decision_category window_name = "RUS_rc_window" visible = { RUS_rc_provisional_phase = yes }\ntriggers = {\n'+'\n'.join(vis)+'\n}\nproperties = {\n'+'\n'.join(props)+'\n}\neffects = {\n'+'\n'.join(eff)+'\n}\n} }\n'
    out['common/scripted_effects/RUS_provisional_industry_effects.txt']='RUS_rc_refresh = { if = { limit = { RUS_rc_provisional_phase = yes }\n'+'\n'.join(calc)+'\n} }\n'
    out['common/on_actions/RUS_provisional_industry_on_actions.txt']='on_actions = { on_daily = { effect = { if = { limit = { RUS_rc_provisional_phase = yes } RUS_rc_refresh = yes } } } }\n'
    for lang in ('simp_chinese','english','russian'):
        p=f'localisation/{lang}/RUS_provisional_industry_l_{lang}.yml'
        extra={'RUS_rc_summary':'在建工程：§Y[?RUS_rc_active|0]§!    竣工项目：§G[?RUS_rc_done|0]§!\\n[RUSRecoveryNextCompletion]',
               'RUS_rc_starting':'工程启动中','RUS_rc_no_work':'暂无在建工程','RUS_rc_next_work':'最近竣工：§Y[?RUS_rc_next_days|0]§! 天'}
        for key,*_ in g.ZONES:extra['RUS_rc_order_stats_'+key]=f'在建 §Y[?RUS_rc_active_{key}|0]§!   竣工 §G[?RUS_rc_done_{key}|0]§!'
        if lang!='simp_chinese':
            extra['RUS_rc_summary']='Active: §Y[?RUS_rc_active|0]§!    Completed: §G[?RUS_rc_done|0]§!\\n[RUSRecoveryNextCompletion]'
            extra['RUS_rc_starting']='Projects starting'
            extra['RUS_rc_no_work']='No projects in progress'
            extra['RUS_rc_next_work']='Next completion: §Y[?RUS_rc_next_days|0]§! days'
            for key,*_ in g.ZONES:extra['RUS_rc_order_stats_'+key]=f'Active §Y[?RUS_rc_active_{key}|0]§!  Done §G[?RUS_rc_done_{key}|0]§!'
        if lang=='russian':
            extra['RUS_rc_summary']='В работе: §Y[?RUS_rc_active|0]§!    Завершено: §G[?RUS_rc_done|0]§!\\n[RUSRecoveryNextCompletion]'
            extra['RUS_rc_starting']='Запуск проектов'
            extra['RUS_rc_no_work']='Нет действующих проектов'
            extra['RUS_rc_next_work']='Ближайшее завершение: §Y[?RUS_rc_next_days|0]§! дн.'
            for key,*_ in g.ZONES:extra['RUS_rc_order_stats_'+key]=f'В работе §Y[?RUS_rc_active_{key}|0]§!  Готово §G[?RUS_rc_done_{key}|0]§!'
        out[p]+=''.join(f' {k}:0 "{v}"\n' for k,v in extra.items())
    out['common/scripted_localisation/RUS_provisional_industry_loc.txt'] += 'defined_text = { name = RUSRecoveryNextCompletion text = { trigger = { check_variable = { RUS_rc_active > 0 } check_variable = { RUS_rc_next_days > 0 } } localization_key = RUS_rc_next_work } text = { trigger = { check_variable = { RUS_rc_active > 0 } } localization_key = RUS_rc_starting } text = { localization_key = RUS_rc_no_work } }\n'
    return out
