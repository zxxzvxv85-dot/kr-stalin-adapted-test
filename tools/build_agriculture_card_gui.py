"""Interactive agriculture tabletop: artwork is the click target, labels stay live."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps,ImageFilter,ImageEnhance
import re,math,json
R=Path(__file__).resolve().parents[1];L=R.parent/'新美工素材库';A=R/'gfx/interface/RUS_agriculture_cards';A.mkdir(parents=True,exist_ok=True)
C=['wheat','rye','beet','flax','cotton'];sprites={}
def save(name,im,button=False):
 im.save(A/(name+'.png'));sprites[name]=(im.width,im.height,button)
def paste(im,path,box):
 a=Image.open(path).convert('RGBA');bb=a.getbbox()
 if bb:a=a.crop(bb)
 a.thumbnail((box[2],box[3]),Image.Resampling.LANCZOS);im.alpha_composite(a,(box[0]+(box[2]-a.width)//2,box[1]+(box[3]-a.height)//2))
metal=Image.open(L/'底面/纹理金属.png').convert('L')
def plate(w,h,kind='green'):
 palettes={'green':('#142521','#48624b'),'paper':('#635037','#b19c6b'),'red':('#2d1516','#864734'),'wood':('#322b21','#7b6445')}
 lo,hi=palettes[kind];im=ImageOps.colorize(ImageOps.fit(metal,(w,h)),lo,hi).convert('RGBA');d=ImageDraw.Draw(im)
 d.rounded_rectangle((1,1,w-2,h-2),radius=6,outline='#1a1813',width=3);d.rounded_rectangle((4,4,w-5,h-5),radius=3,outline='#b09865');d.line((7,7,w-8,7),fill='#e1c88b')
 for x in [8,w-11]:
  for y in [11,h-13]:d.ellipse((x,y,x+3,y+3),fill='#b9ae8d');d.line((x,y+2,x+3,y+2),fill='#292d24')
 return im
def token(name,path,size=(100,58),kind='wood'):
 im=plate(*size,kind);paste(im,path,(6,4,size[0]-12,size[1]-20));save(name,im,True)
for i,c in enumerate(C):
 im=plate(92,190,'green');d=ImageDraw.Draw(im);d.ellipse((10,33,81,115),fill='#293d2c',outline='#8e8355',width=2)
 paste(im,R/f'gfx/interface/RUS_agri_crops/RUS_agri_{c}.png',(12,38,68,76));d.rectangle((18,127,73,153),fill='#17221c',outline='#88764e');d.line((10,164,81,164),fill='#9b8960');save('crop_'+c,im,True)
 im=plate(92,96,'wood');paste(im,R/f'gfx/interface/RUS_agri_crops/RUS_agri_{c}.png',(18,8,56,49));save('bin_'+c,im)
im=Image.new('RGBA',(32,26));d=ImageDraw.Draw(im);d.ellipse((4,1,27,24),fill='#642e25',outline='#c6b07a',width=2);d.line((10,13,21,13),fill='#e2d6b1',width=3);save('minus',im,True)
for name in ['factory_minus10','factory_minus1','factory_plus10']:save(name,plate(66,40,'wood'),True)
for name,path in [('auto',L/'物件/notebook small.png'),('clear',L/'经济技术/cog.png'),('confirm',L/'物件/Padlock.png'),('reopen',L/'物件/Padlock.png')]:token(name,path,(108,57),'red' if name=='confirm' else 'wood')
navpaths=[R/'gfx/interface/RUS_agri_crops/RUS_agri_wheat.png',L/'经济技术/Combine.png',L/'经济技术/Bag.png',L/'物件/notebook small.png']
for i,p in enumerate(navpaths):token('nav_'+str(i),p,(116,57))
for name,p in [('factory',L/'经济技术/Factories5.png'),('combine',L/'经济技术/Combine.png')]:
 im=plate(180,148);paste(im,p,(17,10,146,102));save(name,im,name=='factory')
for i in range(3):
 im=plate(100,62,'wood');paste(im,L/'经济技术/Bag.png',(4,6,42,44));save('reserve_'+str(i),im,True)
for name in ['generic','fra','eng']:
 im=plate(154,132,'paper');d=ImageDraw.Draw(im);d.rectangle((12,11,141,31),fill='#5c241d');d.line((15,97,138,97),fill='#5c523a');save('order_'+name,im,True)
for name in ['fra','eng']:
 im=plate(234,53,'paper');paste(im,L/'经济技术/Combine.png',(10,4,45,43));save('morder_'+name,im,True)
for name in ['priority','stop','max','ledger']:save(name,plate(110,35,'wood'),True)
bg=plate(502,625,'wood');pano=Image.open(R/'output/agri-gui/harvest-panorama.png').convert('RGBA');pano=ImageOps.fit(pano,(486,438));pano=ImageEnhance.Brightness(pano).enhance(.48);bg.alpha_composite(pano,(8,171));d=ImageDraw.Draw(bg)
bg.alpha_composite(plate(486,105),(8,65))
for x in [17,401]:d.ellipse((x,78,x+82,160),fill='#1b2922',outline='#c2a164',width=3)
for i in range(11):
 angle=math.radians(140+26*i)
 for x in [58,442]:
  d.line((x+34*math.cos(angle),119+34*math.sin(angle),x+38*math.cos(angle),119+38*math.sin(angle)),fill='#cbb779',width=2)
d.rectangle((10,595,491,621),fill='#1f2b24',outline='#827552');save('board',bg)
im=Image.new('RGBA',(116,57));ImageDraw.Draw(im).rounded_rectangle((2,2,113,54),radius=4,outline='#e2c47f',width=3);save('selected',im)
im=Image.new('RGBA',(100,62));ImageDraw.Draw(im).rounded_rectangle((2,2,97,59),radius=4,outline='#edcf83',width=3);save('reserve_selected',im)
for name,w,h,color in [('tick',6,5,'#d8bd70'),('bar',28,6,'#b9bc74'),('reform',20,3,'#d8bd70')]:save(name,Image.new('RGBA',(w,h),color))
im=Image.new('RGBA',(120,40));d=ImageDraw.Draw(im);d.polygon([(0,15),(89,15),(89,3),(117,20),(89,37),(89,25),(0,25)],fill='#cbb579',outline='#514c38');save('arrow',im)
save('supply_panel',plate(482,89))
save('ledger_column',plate(158,112))
save('report_panel',plate(482,371,'green'))
save('small_panel',plate(234,80))
save('footer',plate(482,26))
atlas=Image.open(R/'tools/assets/agriculture_weather_atlas.png').convert('RGBA')
for index,name in enumerate(['good','normal','bad']):
 cell=atlas.crop((index*atlas.width//3,0,(index+1)*atlas.width//3,atlas.height))
 cell=cell.crop(cell.getbbox());cell.thumbnail((38,32),Image.Resampling.LANCZOS)
 im=Image.new('RGBA',(42,34));im.alpha_composite(cell,((42-cell.width)//2,(34-cell.height)//2));save('weather_'+name,im)
g=['guiTypes = { containerWindowType = { name = "RUS_national_agriculture_window" position = { x = 0 y = 0 } size = { width = 100% height = 625 } clipping = yes']
tr=[];loc={};layout=[]
def condition(p):return 'check_variable = { RUS_nat_page < 2 }' if p==1 else f'check_variable = {{ RUS_nat_page = {p} }}'
def visible(n,p,extra=''):
 if p:tr.append(f'{n}_visible = {{ {condition(p)} {extra} }}')
def img(n,s,x,y,p=0,extra='',tip=''):
 g.append(f'iconType = {{ name = "{n}" position = {{ x = {x} y = {y} }} spriteType = "GFX_RUS_card_{s}" '+(f'pdx_tooltip = "{tip}" alwaystransparent = no' if tip else 'alwaystransparent = yes')+' }');visible(n,p,extra)
def button(n,s,x,y,text='',tip='',p=0):
 g.append(f'buttonType = {{ name = "{n}" position = {{ x = {x} y = {y} }} quadTextureSprite = "GFX_RUS_card_{s}" buttonText = "{text}" buttonFont = "hoi_16mbs" pdx_tooltip = "{tip}" clicksound = click_default }}');visible(n,p)
def txt(n,text,x,y,w,h=22,p=0,font='hoi_16mbs',center=True,extra=''):
 g.append(f'instantTextBoxType = {{ name = "{n}" position = {{ x = {x} y = {y} }} font = "{font}" text = "{text}" maxWidth = {w} maxHeight = {h} format = {"center" if center else "left"} fixedsize = yes alwaystransparent = yes }}');visible(n,p,extra)
def label(key,values):
 loc['RUS_card_'+key]=values if isinstance(values,list) else [values]*3
 return 'RUS_card_'+key
def ticks(n,var,x,y,count,dx,dy,unit,p,s='tick',extra=''):
 for i in range(count):
  name=f'card_{n}_{i}';img(name,s,x+dx*i,y+dy*i)
  tr.append(f'{name}_visible = {{ {condition(p) if p else ""} NOT = {{ check_variable = {{ {var} < {(i+1)*unit:g} }} }} {extra} }}')
img('card_board','board',0,0)
for i in range(4):
 button('nat_tab_'+str(i),'nav_'+str(i),8+i*123,5,tip='RUS_nat_tab_'+str(i)+'_tt')
 txt('card_nav_label_'+str(i),'RUS_nat_tab_'+str(i),10+i*123,42,112)
 img('card_nav_selected_'+str(i),'selected',8+i*123,5,i+1)
txt('card_season',label('season','[?RUS_nat_season|0]'),30,99,57,28,font='hoi_24header')
txt('card_season_label',label('season_label',['季度','Quarter','Квартал']),27,133,62)
txt('card_remaining',label('remaining','[?RUS_nat_remaining|0]'),412,99,59,28,font='hoi_24header')
txt('card_days',label('days',['剩余天数','Days left','Дней']),404,133,76)
txt('nat_title','RUS_nat_title',107,76,288)
txt('card_plan',label('plan',['配额 §Y[?RUS_nat_allocated|0]§! / 免费 §Y[?RUS_nat_budget|0]§!','Plan §Y[?RUS_nat_allocated|0]§! / Free §Y[?RUS_nat_budget|0]§!','План §Y[?RUS_nat_allocated|0]§! / Лимит §Y[?RUS_nat_budget|0]§!']),105,105,292)
for name,op in [('good','>'),('normal','='),('bad','<')]:
 n='card_weather_'+name;img(n,'weather_'+name,167,130,tip=label('weather_tip','$RUS_nat_weather$\\n\\n$RUS_nat_task_line$\\n$RUS_nat_next_line$'))
 tr.append(f'{n}_visible = {{ check_variable = {{ RUS_agri_weather_forecast {op} 0 }} }}')
txt('card_plan_state',label('plan_state','[GetRUSNatPlan]'),213,135,166)
img('card_footer','footer',10,595,tip=label('reform_tip','$RUS_nat_score_line$\\n$RUS_nat_decision_score_line$'))
txt('nat_score',label('reform_brief',['土改  §Y[?RUS_agri_display_score|1]§! / 200','Reform  §Y[?RUS_agri_display_score|1]§! / 200','Реформа  §Y[?RUS_agri_display_score|1]§! / 200']),14,600,474)
ticks('reform','RUS_agri_display_score',17,622,20,23.5,0,10,0,'reform')
for i,c in enumerate(C):
 x=10+i*97
 button('nat_'+c+'_plus','crop_'+c,x,183,tip=label(c+'_tip',[f'§Y$RUS_agri_{c}$§!\\n点击卡片：增加1点配额。下方减号：收回1点。\\n\\n$RUS_nat_{c}_info$\\n$RUS_nat_{c}_market_line$\\n$RUS_nat_{c}_soil$',f'§Y$RUS_agri_{c}$§!\\nClick card: +1. Minus token: -1.\\n\\n$RUS_nat_{c}_info$\\n$RUS_nat_{c}_market_line$\\n$RUS_nat_{c}_soil$',f'§Y$RUS_agri_{c}$§!\\nКарта: +1. Минус: -1.\\n\\n$RUS_nat_{c}_info$\\n$RUS_nat_{c}_market_line$\\n$RUS_nat_{c}_soil$']))
 txt('nat_'+c+'_name','RUS_agri_'+c,x+5,196,82)
 txt('nat_'+c+'_amount','RUS_nat_'+c+'_amount',x+18,313,56,29,font='hoi_24header')
 txt('card_yield_'+c,label(c+'_yield',[f'产 §Y[?RUS_nat_{c}_yield|1]§!',f'Yield §Y[?RUS_nat_{c}_yield|1]§!',f'Сбор §Y[?RUS_nat_{c}_yield|1]§!']),x+6,350,80,p=1)
 button('nat_'+c+'_minus','minus',x+30,381,tip=label(c+'_tip',loc['RUS_card_'+c+'_tip']))
 ticks('allocation_'+c,'RUS_agri_'+c+'_investment',x+8,375,10,8,0,1,1)
for i,(c,name) in enumerate([('food',['粮食','Food','Зерно']),('beet',['甜菜','Beet','Свёкла']),('textile',['纺织','Fibre','Ткани'])]):
 details=[]
 for lang in range(3):
  words=[['本季供需','现有库存','预计新增','内需供给','满足率','储备目标','已接订单','还需增产'],['Quarterly supply','Stock','Expected harvest','Domestic supply','Coverage','Reserve target','Accepted orders','Extra production needed'],['Снабжение квартала','Запас','Прогноз урожая','Внутреннее снабжение','Обеспечение','Целевой резерв','Принятые заказы','Нужно произвести']][lang]
  details.append(f'§Y{name[lang]} · {words[0]}§!\\n\\n{words[1]}: §Y[?RUS_nat_{c}_stock_now|1]§!\\n{words[2]}: §Y[?RUS_nat_{c}_new_yield|1]§!\\n{words[3]}: §Y[?RUS_nat_{c}_delivered|1]§! / §Y[?RUS_nat_{c}_need|1]§!\\n{words[4]}: §Y[?RUS_nat_{c}_preview|2]§!%\\n{words[5]}: §Y[?RUS_nat_{c}_reserve|1]§!\\n{words[6]}: §Y[?RUS_nat_{c}_order_need|1]§!\\n{words[7]}: §Y[?RUS_nat_{c}_all_gap|2]§!')
 img('card_ledger_'+c,'ledger_column',10+i*162,415,1,tip=label('ledger_'+c+'_tip',details))
 txt('card_supply_label_'+c,label('supply_'+c,[f'{n} §Y[?RUS_nat_{c}_preview|0]§!%' for n in name]),18+i*162,423,142,p=1)
 for row,(key,words,decimals) in enumerate([('stock_now',['库存','Stock','Запас'],1),('new_yield',['预计新增','Harvest','Урожай'],1),('all_gap',['还需增产','Shortfall','Дефицит'],2)]):
  txt('card_ledger_'+c+'_'+key,label('ledger_'+c+'_'+key,[f'{w} §Y[?RUS_nat_{c}_{key}|{decimals}]§!' for w in words]),18+i*162,447+22*row,142,p=1)
 ticks('need_'+c,'RUS_nat_'+c+'_preview',40+i*162,518,10,10,0,10,1)
for i,(n,s,key) in enumerate([('nat_auto','auto','RUS_nat_auto'),('nat_clear','clear','RUS_agri_clear'),('nat_confirm','confirm','RUS_agri_confirm'),('nat_reopen','reopen','RUS_agri_reopen')]):
 button(n,s,12+i*123,535,tip=key);txt('card_label_'+s,key,14+i*123,570,104,p=1)
# Production line: click the factory illustration to add one civilian factory.
button('nat_factory_2','factory',26,190,tip='RUS_nat_factory_2')
img('card_combine','combine',296,190,2);img('card_arrow','arrow',191,240,2)
txt('nat_machine_0',label('factory_num',['§Y[?RUS_nat_factories|0]§! 座民工','§Y[?RUS_nat_factories|0]§! factories','§Y[?RUS_nat_factories|0]§! фабрик']),37,308,158,26)
txt('nat_machine_1',label('daily',['日产 §Y[?RUS_nat_daily|2]§!','Daily §Y[?RUS_nat_daily|2]§!','В день §Y[?RUS_nat_daily|2]§!']),307,308,158,26)
for n,s,x,key,number in [('nat_factory_0','factory_minus10',26,'RUS_nat_factory_0','-10'),('nat_factory_1','factory_minus1',100,'RUS_nat_factory_1','-1'),('nat_factory_3','factory_plus10',174,'RUS_nat_factory_3','+10')]:button(n,s,x,349,label(s,number),key)
txt('card_available',label('available',['可增派 §Y[?RUS_nat_available|0]§!','Available §Y[?RUS_nat_available|0]§!','Доступно §Y[?RUS_nat_available|0]§!']),273,359,204,p=2)
img('card_machine_panel','supply_panel',10,403,2,tip=label('machine_tip','$RUS_nat_machine_0$\\n$RUS_nat_machine_1$\\n$RUS_nat_machine_2$\\n$RUS_nat_machine_3$\\n$RUS_nat_machine_4$\\n$RUS_nat_promise_state$'))
txt('nat_machine_2','RUS_dash_machine_2',23,417,456,24)
txt('nat_machine_coverage','RUS_nat_machine_coverage',23,454,456,22)
ticks('coverage','RUS_nat_coverage_display',34,480,18,25,0,100/18,2,'reform')
txt('nat_machine_3',label('produced',['累计自产 §Y[?RUS_nat_produced|0]§! / 4000','Produced §Y[?RUS_nat_produced|0]§! / 4000','Выпущено §Y[?RUS_nat_produced|0]§! / 4000']),16,506,470,24)
button('nat_stop','stop',26,548,'RUS_nat_stop','RUS_nat_stop');button('nat_max','max',365,548,'RUS_nat_max','RUS_nat_max')
# Storage and orders: the entire contract is the accept/cancel target.
for i,c in enumerate(C):
 x=10+i*97;group='food' if i<2 else 'beet' if i==2 else 'textile';img('card_bin_'+c,'bin_'+c,x,185,3,tip=label('bin_tip_'+c,f'$RUS_nat_stock_{c}$\\n$RUS_nat_supply_{group}$\\n$RUS_nat_reserve_line$'))
 txt('nat_stock_'+c,label('stock_'+c,f'§Y[?RUS_nat_{c}_stock|1]§!'),x+5,247,82,25)
 ticks('stock_'+c,'RUS_nat_'+c+'_stock',x+8,284,10,8,0,1.2 if i<2 else .6,3)
for i,key in enumerate(['RUS_nat_reserve_0','RUS_nat_reserve_1','RUS_nat_reserve_2']):
 button('nat_reserve_'+str(i),'reserve_'+str(i),92+i*104,299,tip=key+'_tt');txt('card_reserve_'+str(i),label('reserve_num_'+str(i),['0.5','1','2'][i]),137+i*104,319,53,40,3,'hoi_24header')
 img('card_reserve_selected_'+str(i),'reserve_selected',92+i*104,299,3,f'check_variable = {{ RUS_nat_reserve = {[.5,1,2][i]} }}')
txt('card_reserve_label',label('reserve',['保留\\n储备','Keep\\nreserve','Резерв']),15,312,70,42,3)
for i,o in enumerate(['generic','fra','eng']):
 x=10+i*164;button('nat_accept_'+o,'order_'+o,x,370,tip='RUS_nat_order_'+o)
 txt('card_order_title_'+o,label('buyer_'+o,{'generic':['一般订单','General','Общий'],'fra':['法兰西','France','Франция'],'eng':['不列颠','Britain','Британия']}[o]),x+8,383,138,p=3)
 for j,c in enumerate(C):
  n=f'card_order_{o}_{c}';g.append(f'iconType = {{ name = "{n}" position = {{ x = {x+48} y = 407 }} spriteType = "GFX_RUS_agri_crop_{c}" scale = 0.85 alwaystransparent = yes }}');visible(n,3,f'check_variable = {{ RUS_nat_{o}_crop = {j+1} }}')
 txt('nat_order_'+o,label('order_'+o,f'× §Y[?RUS_nat_{o}_quantity|0]§!'),x+7,459,140,23)
 txt('nat_order_rank_'+o,label('accepted_'+o,f'[GetRUSNatAccept{o}] · §Y[?RUS_nat_{o}_priority|0]§!'),x+7,481,140,21)
for i,o in enumerate(['fra','eng']):
 x=10+i*248;button('nat_maccept_'+o,'morder_'+o,x,512,tip='RUS_nat_morder_'+o)
 txt('nat_morder_'+o,label('machine_order_'+o,[f'{"法" if o=="fra" else "英"} · 农机 §Y[?RUS_nat_{o}_machine_quantity|0]§!\\n[GetRUSNatMachineAccept{o}]',f'{o.upper()} · §Y[?RUS_nat_{o}_machine_quantity|0]§! machines\\n[GetRUSNatMachineAccept{o}]',f'{o.upper()} · §Y[?RUS_nat_{o}_machine_quantity|0]§! машин\\n[GetRUSNatMachineAccept{o}]']),x+56,520,171,43)
button('nat_priority','priority',10,565,label('priority',['调整优先级','Priority','Приоритет']),'RUS_nat_priority')
button('nat_ledger','ledger',382,565,'RUS_nat_ledger','RUS_nat_ledger',3)
# Report: live crop chart, live income and reward counters.
img('card_report_panel','report_panel',10,185,4,tip=label('report_tip','$RUS_nat_report_weather$\\n$RUS_nat_report_shortage$\\n$RUS_nat_report_orders$'))
txt('nat_report_head','RUS_dash_report_head',22,198,458,26)
for i,c in enumerate(C):
 x=38+96*i
 ticks('harvest_'+c,'RUS_nat_'+c+'_last_yield',x,393,20,0,-8,1,4,'bar','has_country_flag = RUS_nat_has_report')
 n='card_report_crop_'+c;g.append(f'iconType = {{ name = "{n}" position = {{ x = {x-4} y = 408 }} spriteType = "GFX_RUS_agri_crop_{c}" scale = 0.6 pdx_tooltip = "RUS_nat_report_{c}" alwaystransparent = no }}');visible(n,4,'has_country_flag = RUS_nat_has_report')
 txt('nat_report_'+c,label('last_'+c,f'§Y[?RUS_nat_{c}_last_yield|1]§!'),x-17,452,63,29,font='hoi_24header')
txt('nat_report_supply','RUS_dash_report_supply',22,494,458,25)
txt('nat_report_pp','RUS_dash_report_pp',22,524,458,25)
txt('nat_empty_report','RUS_nat_empty_report',30,250,442,75)
g.append('} }')
(R/'interface/RUS_national_agriculture.gui').write_text('\n'.join(g)+'\n',encoding='utf-8')
# Drop the rejected dashboard's cosmetic trigger block, preserve all original actions.
p=R/'common/scripted_guis/RUS_national_agriculture.txt';s=p.read_text(encoding='utf-8-sig');s=re.sub(r'# (?:DASHBOARD|CARDS) BEGIN\n.*?# (?:DASHBOARD|CARDS) END\n','',s,flags=re.S)
s=re.sub(r'triggers = \{\s*','triggers = {\n',s,count=1)
# Reuse original visibility for original widgets; generated rules only define new names.
defined=set(re.findall(r'\b(\w+)_visible\s*=',s));tr=[t for t in tr if t.split('_visible')[0] not in defined]
s=s.replace('triggers = {','triggers = {\n# CARDS BEGIN\n'+'\n'.join(tr)+'\n# CARDS END\n',1);p.write_text(s,encoding='utf-8')
for i,lang in enumerate(['simp_chinese','english','russian']):
 # GUI tooltips do not reliably expand nested $localisation$ references.
 # Resolve them at build time, leaving live [?variables] and [Get...] intact.
 source={}
 files=sorted((R/f'localisation/{lang}').glob('*.yml'))+sorted((R/'localisation/replace').glob(f'*_l_{lang}.yml'))
 for file in files:
  if file.name.startswith('RUS_agriculture_expanded_'):continue
  source.update(re.findall(r'^\s*([\w.]+):(?:\d+)?\s*"(.*)"$',file.read_text(encoding='utf-8-sig'),re.M))
 source.update({k:v[i] for k,v in loc.items()})
 def expand(value,depth=0):
  assert depth<12, 'Localisation reference cycle'
  return re.sub(r'\$([\w.]+)\$',lambda m:expand(source[m[1]],depth+1),value)
 (R/f'localisation/{lang}/RUS_agriculture_cards_l_{lang}.yml').write_text(f'l_{lang}:\n'+''.join(f' {k}:0 "{expand(v[i])}"\n' for k,v in loc.items()),encoding='utf-8-sig')
 # Legacy stock/report tooltip keys are used directly by several widgets and
 # scripted-localisation branches. Flatten their nested crop-name references too.
 flattened={k:expand(v) for k,v in source.items() if k.startswith(('RUS_nat_','RUS_dash_')) and re.search(r'\$[\w.]+\$',v)}
 (R/f'localisation/replace/RUS_agriculture_expanded_l_{lang}.yml').write_text(f'l_{lang}:\n'+''.join(f' {k}:0 "{v}"\n' for k,v in flattened.items()),encoding='utf-8-sig')
gfx=['spriteTypes = {']
for name,(w,h,b) in sprites.items():gfx.append(f'spriteType = {{ name = "GFX_RUS_card_{name}" texturefile = "gfx/interface/RUS_agriculture_cards/{name}.png" noOfFrames = 1 '+('effectFile = "gfx/FX/buttonstate.lua" ' if b else '')+'}')
gfx.append('}');(R/'interface/RUS_agriculture_cards.gfx').write_text('\n'.join(gfx)+'\n',encoding='utf-8')
(R/'output/agri-gui/card-sprite-sizes.json').write_text(json.dumps(sprites),encoding='utf-8')
print('Four illustrated interactive pages generated; original click actions preserved.')
