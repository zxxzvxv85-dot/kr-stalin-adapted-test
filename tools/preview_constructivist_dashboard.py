"""Native-font layout proof + clickable browser demonstration (sample data).

This is not an in-game screenshot. Runtime bindings live in the generated GUI.
"""
import json,re,html,base64
from functools import lru_cache
from pathlib import Path
from PIL import Image,ImageDraw
from national_plan_catalog import ROOT
from national_plan_dashboard import ART,P,LABELS,SECTOR_POS,REGION_NAMES
from hoi4_bitmap_fonts import render,measure
from build_constructivist_dashboard import indicator, foreground, WHEEL_XY, PREVIEW_FRAMES
from dashboard_sector_motion import MOTIONS,FRAMES

OUT=ROOT/'output/constructivist_dashboard_20261112'
COLOURS={'C':'#77c9db','Y':'#f0cb75','G':'#91ba80','R':'#ed543d','!':'#e3dfcf'}
VARS={'RUS_np_available':1248.50,'RUS_np_frozen':240,'RUS_np_income':1.28,'RUS_np_active':4,'RUS_np_slots':7,'RUS_np_trains':45,'RUS_np_rail_display':1.67,'RUS_first_five_year_plan_score':78.5,'RUS_first_five_year_plan_stage':3,'RUS_np_pending_plan_score':0,'RUS_np_spent':560,'RUS_np_initial_grant':1200,'RUS_np_grant':1200,'RUS_np_efficiency':.96,'RUS_np_free_slots':3}
for i in range(1,5):VARS.update({P+f'active_{i}':1,P+f'done_{i}':i+1})
LOC={k:json.loads(v) for k,v in re.findall(r'^ ([\w.]+):0 (".*")$',(ROOT/'localisation/simp_chinese/RUS_national_plan_dashboard_l_simp_chinese.yml').read_text(encoding='utf-8-sig'),re.M)}
HELPERS={'RUSNPScoreCaption':'一五计划分数','RUSNPScoreValue':'78.5','RUSNPStageCaption':'阶段 3','RUSNPRegionName':'全部地区','RUSNPSectorName':'全部工程'}

@lru_cache(None)
def atlas(name):
    return Image.open(ROOT/ART/('sector_'+name+'.png')).convert('RGBA')

def resolved(s):
    for k,v in HELPERS.items():s=s.replace('['+k+']',v)
    return re.sub(r'\[\?([\w]+)\|(%?)(\d+)\]',lambda m:f'{VARS.get(m[1],0)*(100 if m[2] else 1):.{m[3]}f}'+('%' if m[2] else ''),s)

def rich(im,x,y,text,font,w):
    x+=(w-measure(font,text))/2;colour=COLOURS['!']
    for part in re.split(r'(§.)',text):
        if part.startswith('§'):colour=COLOURS.get(part[1],COLOURS['!'])
        elif part:
            render(im,x,y,part,font,colour);x+=measure(font,part)

def proof(frame=0,plan_active=True):
    im=Image.new('RGBA',(504,620),(19,20,18,255))
    im.alpha_composite(Image.open(ROOT/ART/'background.png').convert('RGBA'),(6,0))
    for name,(x,y,w,h,fps) in MOTIONS.items():
        index=int(frame*fps/8)%FRAMES
        im.alpha_composite(atlas(name).crop((index*w,0,(index+1)*w,h)),(x,y))
    im.alpha_composite(indicator('rotor',frame),WHEEL_XY)
    im.alpha_composite(foreground())
    d=ImageDraw.Draw(im)
    for i in range(3 if plan_active else 0):d.rectangle((216+i*11,365,221+i*11,368),fill='#e1cb9d')
    for name,x,y,w,h,font,key in LABELS:
        if not plan_active and name in ('score_label','score','stage'):continue
        text=resolved(LOC[key]);assert measure(font,text)<=w,(name,text,measure(font,text),w)
        rich(im,x,y,text,font,w)
    return im.convert('RGB')

def span(s):
    text='';colour='';opened=False
    for p in re.split(r'(§.)',s):
        if p.startswith('§'):
            if opened:text+='</span>'
            text+='<span style="color:'+COLOURS.get(p[1],COLOURS['!'])+'">';opened=True
        else:text+=html.escape(p)
    return text+('</span>' if opened else '')

def browser():
    # This export deliberately uses separate art / text / animation layers.
    # JavaScript demonstrator changes displayed sample state; never a save edit.
    s=['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>国家建设委员会 · 动态成品预览</title><style>',
       'body{margin:0;background:#101211;color:#e3dfcf;font-family:"Microsoft YaHei",sans-serif}main{width:504px;margin:20px auto}header{font-size:12px;color:#aaa;margin-bottom:10px;display:flex;align-items:center;gap:9px}select{background:#242722;color:#e3dfcf;padding:5px;border:1px solid #665f4c}.panel{position:relative;width:504px;height:620px;background:#141412;box-shadow:0 8px 50px #0008}.back{position:absolute;left:6px;top:0;width:492px;height:615px}.text{position:absolute;text-align:center;line-height:18px;pointer-events:none;white-space:nowrap;text-shadow:1px 1px #000}.hit{position:absolute;border:0;background:transparent;color:inherit;cursor:pointer;z-index:3}.hit:hover,.hit:focus-visible{background:#e1cb9d18;outline:1px solid #e1cb9d88}[id^="s-"].hit:hover,[id^="s-"].hit:focus-visible{background:transparent;outline:none}[id^="r-"].hit.on{box-shadow:inset 0 -2px #df371d}.anim{position:absolute;pointer-events:none;animation:turn 24s linear infinite}.still{animation:none}#all:hover,#all:active,#all:focus-visible{background:transparent;outline:none;box-shadow:none}.pip{position:absolute;top:365px;width:6px;height:4px;background:#e1cb9d}@keyframes turn{to{transform:rotate(360deg)}}.ledger{position:absolute;z-index:10;left:36px;top:105px;width:432px;height:419px;box-sizing:border-box;background:#131412fc;border:2px solid #e1cb9d;padding:12px 25px;font-size:15px;line-height:21px}.ledger h3{font-size:16px;text-align:center;margin:0 0 13px;padding:0 0 12px;border-bottom:2px solid #df371d}.ledger button{display:block;width:136px;margin:10px auto 0;background:#282820;border:1px solid #e1cb9d;color:#e3dfcf;padding:3px;cursor:pointer}.ledger[hidden]{display:none}footer{font-size:12px;color:#b6ae9d;line-height:1.7;margin-top:10px}@media(max-width:530px){main{margin:10px auto;transform-origin:top left}}@media(prefers-reduced-motion:reduce){.anim{animation:none}}</style>',
       '<main><header>动态预览 · 演示数据 <label>状态 <select id="sample"><option value="1">建设进行中</option><option value="0">建设账本初建</option><option value="2">建设成果扩大</option></select></label></header><div class="panel" id="panel"><img class="back" src="../../gfx/interface/RUS_national_plan_dashboard/background.png" alt="构成主义国家建设界面">']
    s.append('<style>.sectoranim{position:absolute;pointer-events:none;animation:sectorframes var(--duration) steps(64) infinite}.sectoranim.still{animation:none;background-position:0 0}.sectoranim.power.still{opacity:0}@keyframes sectorframes{to{background-position:var(--distance) 0}}@media(prefers-reduced-motion:reduce){.sectoranim{animation:none}}</style>')
    for i,(name,(x,y,w,h,fps)) in enumerate(MOTIONS.items(),1):
        s.append(f'<div class="sectoranim {"power" if i==1 else ""}" id="anim-sector-{i}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;background-image:url(../../{ART}/sector_{name}.png);background-size:{w*FRAMES}px {h}px;--distance:-{w*FRAMES}px;--duration:{FRAMES/fps}s"></div>')
    s.append(f'<img class="anim" id="anim-rotor" src="../../{ART}/wheel.png" style="left:136px;top:202px;width:224px;height:224px" alt="旋转传动轮">')
    s.append(f'<img src="../../{ART}/foreground.png" style="position:absolute;left:0;top:0;width:504px;height:620px;pointer-events:none" alt="固定分数盘">')
    for i in range(6):s.append(f'<i class="pip" id="pip-{i}" style="left:{216+i*11}px"></i>')
    for name,x,y,w,h,font,key in LABELS:
        fs=24 if font=='hoi_24header' else 16 if font=='hoi_16mbs' else 13
        s.append(f'<div class="text" id="{name}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;font-size:{fs}px">{span(resolved(LOC[key]))}</div>')
    def button(id,x,y,w,h,title):s.append(f'<button class="hit" id="{id}" aria-label="{title}" title="{title}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px"></button>')
    button('ledger-toggle',38,7,428,20,'展开国家建设账本')
    button('all',202,270,92,100,'显示全部地区、全部工程')
    for i,(x,y) in enumerate([(18,110),(328,110),(18,378),(328,378)],1):button(f's-{i}',x,y,158,166,'筛选'+LOC[P+f'sector_{i}'])
    for i,name in enumerate(REGION_NAMES):button(f'r-{i+1}',41+i%3*144,554+i//3*29,136,24,'筛选'+name)
    s.append('<section class="ledger" id="ledger" hidden><h3>国家建设账本</h3><div id="ledger-content"></div><button id="close">收起账本</button></section></div><footer id="filter-note">点击四块产业图案或下方地区切换筛选；点击中央分数恢复全部。<br>点击标题展开账本。此页用于查看动效与排版，游戏内显示真实存档数值。</footer></main>')
    s.append('<script>const templates='+json.dumps({r[0]:LOC[r[6]] for r in LABELS},ensure_ascii=False)+';const ledgerTemplate='+json.dumps(LOC[P+'ledger_body'],ensure_ascii=False)+';const base='+json.dumps(VARS)+';const regions='+json.dumps(['全部地区']+REGION_NAMES,ensure_ascii=False)+';const sectors='+json.dumps(['全部工程']+[LOC[P+f'sector_{i}'] for i in range(1,5)],ensure_ascii=False)+';')
    s.append(r'''let region=0,sector=0,state=1;const el=id=>document.getElementById(id);function formatted(s,v){s=s.replace(/\[RUSNPScoreCaption\]/g,state?'一五计划分数':'预备建设分数').replace(/\[RUSNPScoreValue\]/g,(state?v.RUS_first_five_year_plan_score:0).toFixed(1)).replace(/\[RUSNPStageCaption\]/g,state?'阶段 '+v.RUS_first_five_year_plan_stage:'计划未启动').replace(/\[RUSNPRegionName\]/g,regions[region]).replace(/\[RUSNPSectorName\]/g,sectors[sector]);s=s.replace(/\[\?([\w]+)\|(%?)(\d+)\]/g,(_,k,p,n)=>((v[k]||0)*(p?100:1)).toFixed(+n)+(p?'%':''));return '<span>'+s.replace(/§([CYGR!])/g,(_,c)=>'</span><span style="color:'+({C:'#77c9db',Y:'#f0cb75',G:'#91ba80',R:'#ed543d','!':'#e3dfcf'}[c])+'">').replace(/\n/g,'<br>')+'</span>'}function update(){let v={...base};if(state===0)Object.assign(v,{RUS_np_available:1200,RUS_np_frozen:0,RUS_np_active:0,RUS_np_trains:0,RUS_np_rail_display:0,RUS_np_spent:0,RUS_np_free_slots:7,RUS_first_five_year_plan_score:0,RUS_first_five_year_plan_stage:0});if(state===2)Object.assign(v,{RUS_np_available:2634.75,RUS_np_frozen:420,RUS_np_active:6,RUS_np_trains:90,RUS_np_rail_display:2.5,RUS_np_spent:1480,RUS_np_free_slots:1,RUS_first_five_year_plan_score:136.5,RUS_first_five_year_plan_stage:5});for(let i=1;i<=4;i++){v['RUS_np_ui_active_'+i]=state?(region?(i===((region-1)%4+1)?1:0):(state===2&&i<3?2:1)):0;v['RUS_np_ui_done_'+i]=state?(region?i:i+1+(state===2?3:0)):0;el('s-'+i).classList.toggle('on',sector===i);el('s-'+i).setAttribute('aria-pressed',sector===i)}for(const [k,t] of Object.entries(templates))el(k).innerHTML=formatted(t,v);for(let i=1;i<=6;i++){el('r-'+i).classList.toggle('on',region===i);el('r-'+i).setAttribute('aria-pressed',region===i);el('pip-'+(i-1)).style.display=i<=v.RUS_first_five_year_plan_stage?'block':'none'}for(const id of ['score_label','score','stage'])el(id).style.display=state?'block':'none';el('anim-rotor').classList.toggle('still',!state);for(let i=1;i<=4;i++)el('anim-sector-'+i).classList.toggle('still',!v['RUS_np_ui_active_'+i]);el('ledger-content').innerHTML=formatted(ledgerTemplate,v)}el('ledger-toggle').onclick=()=>el('ledger').hidden=!el('ledger').hidden;el('close').onclick=()=>el('ledger').hidden=true;el('all').onclick=()=>{region=sector=0;update()};for(let i=1;i<=6;i++)el('r-'+i).onclick=()=>{region=region===i?0:i;update()};for(let i=1;i<=4;i++)el('s-'+i).onclick=()=>{sector=sector===i?0:i;update()};el('sample').onchange=e=>{state=+e.target.value;update()};update();</script></html>''')
    (OUT/'interactive.html').write_text('\n'.join(s),encoding='utf8')

if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    im=proof();im.save(OUT/'finished_native.png');im.resize((1008,1240),Image.Resampling.NEAREST).save(OUT/'finished_2x.png')
    proof(plan_active=False).save(OUT/'plan_not_started.png')
    frames=[proof(f/2) for f in range(PREVIEW_FRAMES*2)]
    palette=frames[0].quantize(colors=256)
    frames=[frame.quantize(palette=palette,dither=Image.Dither.NONE) for frame in frames]
    frames[0].save(OUT/'animated_preview.gif',save_all=True,append_images=frames[1:],duration=[60,60,60,70]*(len(frames)//4),loop=0,optimize=True)
    browser();print(OUT)
