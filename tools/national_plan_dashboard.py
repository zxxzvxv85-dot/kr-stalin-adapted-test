"""Constructivist national-plan panel. Presentation only; no new polling/rewards.

Native animation reference: vanilla nationalfocusview.gfx and sprite_animation.fxh.
Decision-category controls reference: RUS_education_dashboard.
"""
import json
from hoi4_politics_blocks import parse
from national_plan_catalog import ROOT, PROJECTS, REGIONS
from national_plan import CAT, DEC, FX, b, sv, add, iff, ck
from dashboard_sector_motion import MOTIONS, FRAMES

P = 'RUS_np_ui_'
ART = 'gfx/interface/RUS_national_plan_dashboard'
SECTORS = {1: ('电气建设', {'energy'}), 2: ('工业与资源', {'industry', 'resource'}),
           3: ('交通与城市', {'rail', 'road', 'city'}), 4: ('农业配套', {'agriculture'})}
REGION_NAMES = ['莫斯科', '列宁格勒', '察里津', '乌拉尔', '西伯利亚·远东', '高加索·中亚']
SECTOR_POS = [(25, 246, 134), (345, 246, 134), (25, 479, 148), (329, 479, 150)]
# Native-size source for both GUI and layout proof. Text never baked into art.
LABELS = [
 ('title', 42, 9, 420, 18, 'hoi_16mbs', P+'title'),
 ('resources', 43, 36, 132, 18, 'hoi_16mbs', P+'resources'),
 ('frozen', 188, 36, 132, 18, 'hoi_16mbs', P+'frozen'),
 ('income', 330, 36, 132, 18, 'hoi_16mbs', P+'income'),
 ('slots', 43, 68, 132, 18, 'hoi_16mbs', P+'slots'),
 ('trains', 188, 68, 132, 18, 'hoi_16mbs', P+'trains'),
 ('rail', 330, 68, 132, 18, 'hoi_16mbs', P+'rail'),
 ('score_label', 205, 287, 86, 18, 'Main_14', P+'score_label'),
 ('score', 205, 309, 86, 25, 'hoi_24header', P+'score'),
 ('stage', 205, 343, 86, 18, 'Main_14', P+'stage'),
 ('status', 78, 534, 348, 18, 'Main_14', P+'status')]
for i,(x,y,w) in enumerate(SECTOR_POS,1):
    # Separate words and values: changing the numeric font must not enlarge
    # Chinese captions. Give two-character labels genuine wrapping slack;
    # native layout wraps at an exact 28px fit even when glyph advances fit.
    # Sector names live in the existing clickable-area tooltip, not this plaque.
    left=x+12+(w-14-120)//2
    for suffix,dx,width,font,key,dy in [
        ('active_label',0,40,'Main_14',P+'active_label',7),
        ('active_value',40,20,'hoi_16mbs',P+f'active_value_{i}',6),
        ('done_label',60,40,'Main_14',P+'done_label',7),
        ('done_value',100,20,'hoi_16mbs',P+f'done_value_{i}',6)]:
        LABELS.append((f'sector_{i}_{suffix}',left+dx,y+dy,width,18,font,key))
for i in range(1,7):
    LABELS.append((f'region_{i}_label',42+(i-1)%3*144,557+(i-1)//3*29,132,18,'Main_14',P+f'region_{i}'))

def sector(p):
    return next(i for i,(_,kinds) in SECTORS.items() if p['kind'] in kinds)

def augment(out):
    from generate_provisional_industry_gui import CATEGORIES
    cattext = out[CATEGORIES]
    cat = next(n for n in parse(cattext) if n.k == CAT)
    out[CATEGORIES] = cattext[:cat.ib].rstrip()+'\n scripted_gui = RUS_np_dashboard\n'+cattext[cat.ib:]
    loc = {
      P+'title':'国家建设委员会',
      P+'resources':'资源 §C[?RUS_np_available|2]§!',
      P+'frozen':'冻结 §Y[?RUS_np_frozen|2]§!',
      P+'income':'日增 §G+[?RUS_np_income|2]§!',
      P+'slots':'在建 §Y[?RUS_np_active|0]§! / [?RUS_np_slots|0]',
      P+'trains':'列车 §Y[?RUS_np_trains|0]§!',
      P+'rail':'干线 §Y[?RUS_np_rail_display|2]§!',
      P+'score_label':'[RUSNPScoreCaption]',
      P+'score':'§Y[RUSNPScoreValue]§!',
      P+'score_active':'一五计划分数', P+'score_pending':'预备建设分数',
      P+'score_active_value':'[?RUS_first_five_year_plan_score|1]',
      P+'score_pending_value':'[?RUS_np_pending_plan_score|1]',
      P+'stage':'[RUSNPStageCaption]', P+'stage_active':'阶段 [?RUS_first_five_year_plan_stage|0]',
      P+'stage_pending':'计划未启动',
      P+'status':'[RUSNPRegionName] · [RUSNPSectorName]',
      P+'sector_0':'全部工程', P+'blank':'',
      P+'active_label':'在建', P+'done_label':'竣工',
      P+'ledger_tt':'§Y国家建设账本§!\n点击展开或收起详细账目。',
      P+'all_tt':'显示全部地区、全部类型的已解锁工程。',
      P+'resources_tt':'§C国家建设资源§!\n可用：[?RUS_np_available|2]\n冻结：[?RUS_np_frozen|2]\n已消耗：[?RUS_np_spent|2]',
      P+'frozen_tt':'施工中冻结的国家建设资源。工程结算时扣除已用部分，返还余款。',
      P+'income_tt':'每日收入：§G+[?RUS_np_income|2]§!\n初始拨款：[?RUS_np_initial_grant|2]\n年度拨款：[?RUS_np_grant|2]\n组织效率：[?RUS_np_efficiency|%1]',
      P+'slots_tt':'在建工程：[?RUS_np_active|0]\n工程名额：[?RUS_np_slots|0]\n空闲名额：§G[?RUS_np_free_slots|0]§!',
      P+'trains_tt':'工程征用与持续运输调度占用的普通列车总数。',
      P+'rail_tt':'当前地区的计划干线平均等级；显示全部地区时使用全计划平均值。',
      P+'ledger_title':'国家建设账本',
      P+'ledger_body':'可用建设资源：§C[?RUS_np_available|2]§!\n冻结额度：§Y[?RUS_np_frozen|2]§!\n累计消耗：[?RUS_np_spent|2]\n\n初始拨款：[?RUS_np_initial_grant|2]\n年度拨款：[?RUS_np_grant|2]\n每日收入：§G+[?RUS_np_income|2]§!\n组织效率：[?RUS_np_efficiency|%1]\n\n在建 / 总名额：[?RUS_np_active|0] / [?RUS_np_slots|0]\n空闲工程名额：§G[?RUS_np_free_slots|0]§!\n征用列车：[?RUS_np_trains|0]\n计划干线平均等级：[?RUS_np_rail_display|2]\n\n一五计划分数：§Y[?RUS_first_five_year_plan_score|1]§!\n待计入分数：§Y[?RUS_np_pending_plan_score|1]§!',
      P+'ledger_close':'收起账本'}
    loc[P+'open_ledger']='查阅国家建设账本'
    loc[P+'open_ledger_desc']='查阅建设资源、工程占用和计划成果。'
    gfx = ['spriteTypes = {']
    def sprite(name,file,frames=1,animated=False,fps=8):
        kind = 'frameAnimatedSpriteType' if animated else 'spriteType'
        gfx.append(f'{kind} = {{ name = "GFX_{P}{name}" texturefile = "{ART}/{file}.png" noOfFrames = {frames}'+(f' animation_rate_fps = {fps} looping = yes play_on_show = yes pause_on_loop = 0.0' if animated else '')+' }')
    for name in ('background','ledger','selected_sector','selected_region','stage_pip'):
        sprite(name,name)
    for name in ('header','sector','area','region','score','close'):
        sprite('hit_'+name,'hit_'+name,3)
    sprite('wheel_static','wheel')
    sprite('foreground','foreground')
    for name,(_,_,_,_,fps) in MOTIONS.items():
        sprite('sector_'+name,'sector_'+name,FRAMES,True,fps)
        sprite('sector_'+name+'_idle','sector_'+name+'_idle')
    # Continuous native UV rotation; retain original score face above it.
    # References: vanilla nationalfocusview.gfx, frontendmainview.gfx and
    # gfx/FX/sprite_animation.fxh (normal alpha blending).
    gfx.append('spriteType = { name = "GFX_'+P+'wheel_moving" texturefile = "'+ART+'/wheel_empty.png" effectFile = "gfx/FX/buttonstate_onlydisable.lua" '+
      'animation = { animationmaskfile = "'+ART+'/wheel_mask.png" animationtexturefile = "'+ART+'/wheel.png" '+
      'animationrotation = -90.0 animationlooping = yes animationtime = 24.0 animationdelay = 0.0 animationblendmode = "normal" animationtype = "rotating" '+
      'animationrotationoffset = { x = 0.0 y = 0.0 } animationtexturescale = { x = 1.0 y = 1.0 } } legacy_lazy_load = no }')
    gfx.append('}')
    gui=['guiTypes = { containerWindowType = { name = "RUS_np_dashboard_window" position = { x = 0 y = 0 } size = { width = 504 height = 620 }']
    triggers=[]; effects=[]
    def icon(name,x,y,sprite,transparent=True):
        gui.append(f'iconType = {{ name = "{name}" position = {{ x = {x} y = {y} }} spriteType = "GFX_{P}{sprite}"'+(' alwaystransparent = yes' if transparent else '')+' }')
    def button(name,x,y,texture,tooltip,code):
        gui.append(f'buttonType = {{ name = "{name}" position = {{ x = {x} y = {y} }} quadTextureSprite = "GFX_{P}hit_{texture}" pdx_tooltip = {tooltip} clicksound = click_default }}')
        effects.append(f'{name}_click = {{ hidden_effect = {{ if = {{ limit = {{ RUS_np_context = yes }} {code} }} }} }}')
    def label(row,tooltip=None):
        name,x,y,w,h,font,key=row
        gui.append(f'instantTextBoxType = {{ name = "{name}" position = {{ x = {x} y = {y} }} font = "{font}" text = "{key}" maxWidth = {w} maxHeight = {h} format = center '+('pdx_tooltip = '+tooltip if tooltip else 'alwaystransparent = yes')+' }')
    icon('background',6,0,'background')
    for i,(name,(x,y,_,_,_)) in enumerate(MOTIONS.items(),1):
        icon(name+'_active',x,y,'sector_'+name)
        icon(name+'_idle',x,y,'sector_'+name+'_idle')
        triggers += [name+'_active_visible = { check_variable = { '+P+'active_'+str(i)+' > 0 } }',
                     name+'_idle_visible = { NOT = { check_variable = { '+P+'active_'+str(i)+' > 0 } } }']
    icon('wheel_idle',136,202,'wheel_static')
    icon('wheel_active',136,202,'wheel_moving')
    triggers += ['wheel_active_visible = { check_variable = { RUS_np_active > 0 } }',
                 'wheel_idle_visible = { NOT = { check_variable = { RUS_np_active > 0 } } }']
    for name in ('score_label','score','stage'):
        triggers.append(name+'_visible = { RUS_completed_focus_4_year_plan = yes }')
    icon('stationary_faces',0,0,'foreground')
    for i in range(1,7):
        icon(f'stage_{i}',216+(i-1)*11,365,'stage_pip')
        triggers.append(f'stage_{i}_visible = {{ RUS_completed_focus_4_year_plan = yes check_variable = {{ RUS_first_five_year_plan_stage > {i-1} }} }}')
    toggle = 'if = { limit = { has_country_flag = '+P+'ledger_open } clr_country_flag = '+P+'ledger_open } else = { set_country_flag = '+P+'ledger_open }'
    button('ledger_toggle',38,7,'header',P+'ledger_tt',toggle)
    button('all',202,270,'score',P+'all_tt','set_variable = { RUS_np_filter = 0 } set_variable = { '+P+'sector = 0 } RUS_np_refresh = yes')
    triggers.append(f'all_visible = {{ NOT = {{ has_country_flag = {P}ledger_open }} }}')
    for i,(x,y,w) in enumerate(SECTOR_POS,1):
        ax,ay=[(18,110),(328,110),(18,378),(328,378)][i-1]
        button(f'sector_{i}',ax,ay,'area',P+f'sector_{i}_tt',f'if = {{ limit = {{ check_variable = {{ {P}sector = {i} }} }} set_variable = {{ {P}sector = 0 }} }} else = {{ set_variable = {{ {P}sector = {i} }} }} RUS_np_refresh = yes')
        triggers.append(f'sector_{i}_visible = {{ NOT = {{ has_country_flag = {P}ledger_open }} }}')
        icon(f'sector_{i}_selected',x+13,y+29,'selected_sector')
        triggers.append(f'sector_{i}_selected_visible = {{ check_variable = {{ {P}sector = {i} }} }}')
        loc[P+f'sector_{i}']=SECTORS[i][0]
        loc[P+f'counts_{i}']=f'在建 §Y[?{P}active_{i}|0]§!  竣工 §G[?{P}done_{i}|0]§!'
        loc[P+f'active_value_{i}']=f'§Y[?{P}active_{i}|0]§!'
        loc[P+f'done_value_{i}']=f'§G[?{P}done_{i}|0]§!'
        loc[P+f'sector_{i}_tt']=SECTORS[i][0]+'\n点击筛选；再次点击取消此类型筛选。\n统计范围随当前地区变化。'
    for i in range(1,7):
        x=41+(i-1)%3*144;y=554+(i-1)//3*29
        button(f'region_{i}',x,y,'region',P+f'region_{i}_tt',f'if = {{ limit = {{ check_variable = {{ RUS_np_filter = {i} }} }} set_variable = {{ RUS_np_filter = 0 }} }} else = {{ set_variable = {{ RUS_np_filter = {i} }} }} RUS_np_refresh = yes')
        icon(f'region_{i}_selected',x+6,y+21,'selected_region')
        triggers.append(f'region_{i}_selected_visible = {{ check_variable = {{ RUS_np_filter = {i} }} }}')
        loc[P+f'region_{i}']=REGION_NAMES[i-1]
        loc[P+f'region_{i}_tt']=REGIONS[i]+'\n点击筛选；再次点击显示全部地区。'
    for row in LABELS:label(row,P+row[0]+'_tt' if row[0] in ('resources','frozen','income','slots','trains','rail') else None)
    # Draw the expanded ledger last; its panel catches clicks over the machine.
    icon('ledger_panel',36,105,'ledger',False)
    label(('ledger_title',55,119,394,20,'hoi_16mbs',P+'ledger_title'))
    gui.append(f'instantTextBoxType = {{ name = "ledger_body" position = {{ x = 63 y = 154 }} font = "hoi_16mbs" text = "{P}ledger_body" maxWidth = 375 maxHeight = 350 format = left alwaystransparent = yes }}')
    button('ledger_close',184,497,'close',P+'ledger_close',f'clr_country_flag = {P}ledger_open')
    label(('ledger_close_label',184,499,136,18,'Main_14',P+'ledger_close'))
    for name in ('ledger_panel','ledger_title','ledger_body','ledger_close','ledger_close_label'):
        triggers.append(f'{name}_visible = {{ has_country_flag = {P}ledger_open }}')
    gui.append('} }')
    out['interface/RUS_national_plan_dashboard.gui']='\n'.join(gui)+'\n'
    out['interface/RUS_national_plan_dashboard.gfx']='\n'.join(gfx)+'\n'
    out['common/scripted_guis/RUS_national_plan_dashboard.txt']='\n'.join([
      'scripted_gui = { RUS_np_dashboard = { context_type = decision_category window_name = "RUS_np_dashboard_window"',
      'visible = { RUS_np_context = yes } ai_enabled = { always = no }',
      'triggers = {',*triggers,'} effects = {',*effects,'} } }',''])
    # Reuse the existing daily/settlement refresh. No frame-by-frame scripts.
    text=out[FX];node=next(n for n in parse(text) if n.k=='RUS_np_refresh')
    rows=[]
    for i in SECTORS:
        rows += [sv(P+'active_'+str(i),0),sv(P+'done_'+str(i),0)]
    for p in PROJECTS:
        r=p['region'];i=sector(p)
        rows.append(iff(f'OR = {{ {ck("RUS_np_filter","=",0)} {ck("RUS_np_filter","=",r)} }}',[
          iff('has_country_flag = RUS_np_'+p['key']+'_running',[add(P+'active_'+str(i),1)]),
          iff('has_country_flag = RUS_np_'+p['key']+'_completed',[add(P+'done_'+str(i),1)])]))
    out[FX]=text[:node.ib]+'\n'+'\n'.join(rows)+'\n'+text[node.ib:]
    text=out[DEC];cat=next(n for n in parse(text) if n.k==CAT);edits=[]
    byid={p['id']:p for p in PROJECTS};byid.update({'RUS_np_'+p['key']+'_terminate':p for p in PROJECTS})
    for n in cat.v:
        if n.k in ['RUS_np_filter_'+str(i) for i in range(7)]:edits.append((n.a,n.b,''))
        if n.k in byid:
            v=n.one('visible');i=sector(byid[n.k])
            at=v.ib
            while at>v.a and text[at-1] in ' \t':at-=1
            edits.append((at,v.ib,'\n OR = { '+ck(P+'sector','=',0)+' '+ck(P+'sector','=',i)+' }\n'))
    for a,z,replacement in sorted(edits,reverse=True):text=text[:a]+replacement+text[z:]
    # An unfiltered management entry keeps visible_when_empty=no from removing
    # the whole category when a region/type intersection has no projects.
    anchor=b(P+'open_ledger',[
      'allowed = { original_tag = RUS }',
      'visible = { RUS_np_context = yes has_country_flag = RUS_np_initialized }',
      'on_map_mode = decision_view_only','cost = 0','ai_will_do = { base = 0 }',
      'complete_effect = { hidden_effect = { set_country_flag = '+P+'ledger_open } }'])
    out[DEC]=text.replace('# RUS_NP_MANAGEMENT_END',anchor+'# RUS_NP_MANAGEMENT_END')
    sl=[]
    for name,a,c in [('RUSNPScoreCaption','score_active','score_pending'),('RUSNPScoreValue','score_active_value','score_pending_value'),('RUSNPStageCaption','stage_active','stage_pending')]:
        sl.append(b('defined_text',['name = '+name,'text = { trigger = { RUS_completed_focus_4_year_plan = yes } localization_key = '+P+a+' }','text = { localization_key = '+P+c+' }']))
    sl.append(b('defined_text',['name = RUSNPSectorName',*[f'text = {{ trigger = {{ check_variable = {{ {P}sector = {i} }} }} localization_key = {P}sector_{i} }}' for i in SECTORS],f'text = {{ localization_key = {P}sector_0 }}']))
    out['common/scripted_localisation/RUS_national_plan_dashboard.txt']=''.join(sl)
    # Keep the original ledger definition for reference/tooltip but remove its
    # duplicated paragraph above this panel only in the new plan context.
    path='common/scripted_localisation/RUS_stalin_five_year_plan_scripted_loc.txt'
    out[path]=out[path].replace('trigger = { RUS_np_context = yes } localization_key = RUS_np_header','trigger = { RUS_np_context = yes } localization_key = '+P+'blank')
    for lang in ('simp_chinese','english','russian'):
        out[f'localisation/{lang}/RUS_national_plan_dashboard_l_{lang}.yml']='l_'+lang+':\n'+''.join(' '+k+':0 '+json.dumps(v,ensure_ascii=False)+'\n' for k,v in loc.items())
    return out
