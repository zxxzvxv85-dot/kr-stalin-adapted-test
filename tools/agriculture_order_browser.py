"""Loaded by the card builder with its rendering helpers in scope."""
save('order_row',plate(452,72,'paper'),True)
save('order_tab',plate(234,30,'wood'),True)
save('order_toggle',plate(84,42,'green'),True)
save('order_scroll',plate(482,156))
im=Image.new('RGBA',(234,30));ImageDraw.Draw(im).rounded_rectangle((2,2,231,27),radius=3,outline='#edcf83',width=2);save('order_tab_selected',im)
browser_actions=[];browser_windows=[]
for i,(part,names) in enumerate([('domestic',['国内订单','Domestic','Внутренние']),('foreign',['国外订单','Foreign','Внешние'])]):
 name='card_orders_'+part
 button(name,'order_tab',10+248*i,367,label('orders_'+part,names),p=3)
 browser_actions.append(f'{name}_click = {{ set_variable = {{ RUS_nat_order_category = {i} }} RUS_nat_refresh = yes }}')
 test='check_variable = { RUS_nat_order_category < 1 }' if i==0 else 'check_variable = { RUS_nat_order_category = 1 }'
 img(name+'_selected','order_tab_selected',10+248*i,367,3,test)
 main_g=g;g=[]
 g.append(f'containerWindowType = {{ name = "{name}_scroll" position = {{ x = 10 y = 403 }} size = {{ width = 482 height = 156 }} clipping = yes verticalScrollbar = "right_vertical_slider" smooth_scrolling = yes background = {{ spriteType = "GFX_RUS_card_order_scroll" }}')
 if i==0:
  tip=label('domestic_order_tip',['国内基本需求优先满足，不能取消。这里显示本季实际需求与预计供给；农机行显示在役数量和目标。','Domestic essentials have priority and cannot be cancelled. Seasonal needs and estimated delivery are shown; machinery shows installed units and target.','Внутренние нужды обязательны. Показаны спрос и прогноз снабжения; техника — в строю и целевое количество.'])
  for j,(group,crop,names) in enumerate([('food','wheat',['粮食供给','Food supply','Продовольствие']),('beet','beet',['制糖原料','Sugar processing','Сырьё для сахара']),('textile','cotton',['纺织原料','Textile materials','Текстильное сырьё']),('machine',None,['国内农机需求','Domestic machinery','Техника для страны'])]):
   y=4+j*76;img('card_domestic_'+group,'order_row',4,y,tip=tip)
   if crop:g.append(f'iconType = {{ name = "card_domestic_icon_{group}" position = {{ x = 12 y = {y+8} }} spriteType = "GFX_RUS_agri_crop_{crop}" scale = 0.75 alwaystransparent = yes }}')
   txt('card_domestic_title_'+group,label('domestic_'+group,names),66,y+7,284,20,center=False)
   value=f'§Y[?RUS_nat_{group}_delivered|1]§! / §Y[?RUS_nat_{group}_need|1]§!' if crop else '§Y[?RUS_nat_installed|0]§! / §Y[?RUS_nat_target|0]§!'
   txt('card_domestic_supply_'+group,label('domestic_supply_'+group,value),66,y+35,280,25,center=False)
   txt('card_domestic_required_'+group,label('domestic_required',['必需','Required','Обязат.']),362,y+27,84,22)
 else:
  g.append('gridboxType = { name = "card_foreign_orders_grid" position = { x = 4 y = 4 } size = { width = 456 height = 100%% } slotsize = { width = 456 height = 1 } max_slots_horizontal = 1 add_horizontal = no }')
  txt('card_no_foreign_orders',label('no_foreign_orders',['本季暂无国外订单','No foreign orders this quarter','Нет внешних заказов в этом квартале']),18,50,430,40)
  tr.append('card_no_foreign_orders_visible = { check_variable = { RUS_nat_foreign_order_count = 0 } }')
 g.append('}');browser_windows.append('\n'.join(g));g=main_g

# One 76px entry for each numeric row id, supplied by the quarter's order cache.
main_g=g;g=[]
g.append('containerWindowType = { name = "RUS_agriculture_foreign_order_entry" size = { width = 456 height = 76 } clipping = yes')
rows=[('generic',None,False),('fra','FRA',False),('eng','ENG',False),('fra','FRA',True),('eng','ENG',True)]+[(tag.lower(),tag,False) for tag in ['SER','ROM','GRE','ALB','BUL']]
browser_aliases=[]
for i,(buyer,tag,machine) in enumerate(rows):
 row_start=len(g);trigger_start=len(tr)
 source=f'nat_{"maccept" if machine else "accept"}_{buyer}'
 tip=label('order_entry_tip_'+str(i),['左键卡片或右侧开关：接单／取消。本订单独立交付与结算。','Left-click the row or switch to accept/cancel. This order is delivered and settled independently.','ЛКМ по строке или переключателю: принять/отменить. Заказ поставляется и оплачивается отдельно.'])
 for suffix,sprite,x,y in [('card','order_row',0,0),('switch','order_toggle',362,15)]:
  n=f'card_order_{i}_{suffix}';button(n,sprite,x,y,tip=tip);browser_aliases.append((n,source))
 if machine:
  g.append('iconType = { name = "card_order_machine_icon_'+str(i)+'" position = { x = 10 y = 10 } spriteType = "GFX_RUS_card_combine" scale = 0.28 alwaystransparent = yes }')
 else:
  for j,crop in enumerate(C):
   n=f'card_order_{i}_crop_{crop}';g.append(f'iconType = {{ name = "{n}" position = {{ x = 8 y = 10 }} spriteType = "GFX_RUS_agri_crop_{crop}" scale = 0.75 alwaystransparent = yes }}');tr.append(f'{n}_visible = {{ check_variable = {{ RUS_nat_{buyer}_crop = {j+1} }} }}')
 title=[f'[{tag}.GetName]']*3 if tag else ['一般采购','General procurement','Общие закупки']
 txt(f'card_order_{i}_title',label('order_entry_title_'+str(i),title),64,6,286,22,center=False)
 quantity= f'[?RUS_nat_{buyer}_machine_quantity|0]' if machine else f'[?RUS_nat_{"generic_base_quantity" if i==0 else buyer+"_quantity"}|0]'
 details=[f'{"农机" if machine else "农产品"} × {quantity}',f'{"Machinery" if machine else "Crops"} × {quantity}',f'{"Техника" if machine else "Урожай"} × {quantity}']

 if not machine:details=[v+q for v,q in zip(details,[f' · 优先 [?RUS_nat_{buyer}_priority|0]',f' · Priority [?RUS_nat_{buyer}_priority|0]',f' · Приор. [?RUS_nat_{buyer}_priority|0]'])]
 txt(f'card_order_{i}_detail',label('order_entry_detail_'+str(i),details),64,31,290,35,center=False)
 txt(f'card_order_{i}_state',label('order_entry_state_'+str(i),f'[GetRUSNat{"MachineAccept" if machine else "Accept"}{buyer}]'),364,27,80,22)
 # Scripted GUI conditions must be attached to actual leaf widgets, not nested containers.
 for line in g[row_start:]:
  name=re.search(r'name = "([^"]+)"',line).group(1)
  prior=next((j for j in range(trigger_start,len(tr)) if tr[j].startswith(name+'_visible =')),None)
  guard=f'check_variable = {{ RUS_nat_order_row = {i} }}'
  if prior is None:tr.append(name+'_visible = { '+guard+' }')
  else:tr[prior]=tr[prior].replace('_visible = {','_visible = { '+guard,1)
g.append('}')
browser_entry='\n'.join(g);g=main_g
