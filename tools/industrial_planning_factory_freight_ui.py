"""Freight settings and native resource icons within the existing right panel."""
from industrial_planning_catalog import STOCKS, NAMES, FREIGHT_BATCH_PER_LEVEL, FREIGHT_FEE
from industrial_planning_factory import P, REGIONS, cv


def localise(L,defined):
    L('freight_page','跨区运输','Freight')
    L('freight_page_active','§Y跨区运输§!','§YFreight§!')
    L('freight_page_tab','[GetRUSIPFreightMenu]','[GetRUSIPFreightMenu]')
    defined('GetRUSIPFreightMenu',[(cv('build_page','=',2),P+'freight_page_active'),('',P+'freight_page')])
    L('freight_title','[GetRUSIPRegion] · 自动运输线路','[GetRUSIPRegion] · Automatic freight')
    L('freight_destination_label','目的地区：[GetRUSIPFreightDestination]','Destination: [GetRUSIPFreightDestination]')
    L('freight_goods_label','发运货物：[GetRUSIPFreightGoods]','Cargo: [GetRUSIPFreightGoods]')
    L('freight_reserve_button','保留 [?RUS_ip_freight_reserve|0]','Keep [?RUS_ip_freight_reserve|0]')
    L('freight_on','§G自动发运：开§!','§GDispatch: ON§!');L('freight_off','自动发运：关','Dispatch: OFF')
    L('freight_toggle_button','[GetRUSIPFreightEnabled]','[GetRUSIPFreightEnabled]')
    defined('GetRUSIPFreightEnabled',[(cv('freight_enabled','=',1),P+'freight_on'),('',P+'freight_off')])
    L('freight_rules_tt',f'§Y跨区运输§!\n两区各建一座运输站并接通当地调度站。\n每区一条自动外运线路，可接收多个地区来货。\n单批上限：两端较低有效等级 × §Y{FREIGHT_BATCH_PER_LEVEL}§!\n每单位运费：§R-{FREIGHT_FEE:.2f}§! 投资。最低发运量：§Y1§!。\n工厂先用料，日末从超过保留量的库存发货。\n按地区距离计时；两端每共同提高一级，行程减少1天，最低1天。\n这是沙盘运输，不检查原版地图铁路。电力和已交付成品不运输。',
      f'§YFreight§!\nBuild and connect a station at both ends. Each region has one outbound route and may receive from multiple regions.\nBatch limit: lower effective station level × §Y{FREIGHT_BATCH_PER_LEVEL}§!. Fee: §R-{FREIGHT_FEE:.2f}§! investment per unit; minimum batch §Y1§!.\nPlants consume inputs first, then remaining stock above the reserve is shipped. Distance sets travel time; each shared level above one saves a day. Minimum one day. Native map railways are not queried. Power and delivered products cannot be shipped.')
    L('freight_select_tt','选择下一批货物的目的地区；已在途货物仍运往原目的地。','Choose the next destination. Cargo already in transit keeps its original destination.')
    L('freight_reserve_tt','本地最低保留库存：§Y0 → 3 → 6 → 12§!，点击循环。\n只运出高于保留量的部分；工厂仍可以消耗保留的材料。','Cycle the export reserve: §Y0 → 3 → 6 → 12§!. Export only stock above this level; local plants may consume the reserve.')
    L('freight_toggle_tt','开启后持续自动发运；上一批卸货后自动安排下一批，无需重复点击。\n库存、运费不足或运输站断线时暂停，条件恢复后自动继续。\n关闭只停止新发货，已在途货物继续运输。关闭窗口不停止物流。','Keep shipping automatically: once a batch is unloaded, the next is dispatched without another click.\nWaits for sufficient stock, funds and connected stations, then resumes automatically.\nDisabling stops new shipments; existing cargo continues. Closing the GUI does not stop freight.')
    L('freight_preview','批量上限：§Y[?RUS_ip_freight_limit|0]§!   本区有效站级：§Y[?RUS_ip_transport_capacity|0]§!\n当前可发：§G[?RUS_ip_freight_preview_amount|1]§!   运费：§R-[?RUS_ip_freight_preview_fee|2]§!   行程：§Y[?RUS_ip_freight_preview_days|0]§! 天\n[GetRUSIPFreightStatus]',
      'Batch limit: §Y[?RUS_ip_freight_limit|0]§!  Effective station: §Y[?RUS_ip_transport_capacity|0]§!\nAvailable now: §G[?RUS_ip_freight_preview_amount|1]§!  Fee: §R-[?RUS_ip_freight_preview_fee|2]§!  Days: §Y[?RUS_ip_freight_preview_days|0]§!\n[GetRUSIPFreightStatus]')
    L('freight_preview_tt','按当前库存与投资预估，尚未扣款。实际日末先供应生产，再按剩余库存和投资发运。多个地区共用建设投资。','Current stock/funds estimate, not a charge. Dispatch follows production and uses the remaining stock and shared investment.')
    L('freight_empty','当前没有外运货物','No outbound shipment')
    L('freight_shipment','[GetRUSIPFreightCargo] §Y[?RUS_ip_freight_amount|1]§! → [GetRUSIPFreightTo]\n剩余 §Y[?RUS_ip_freight_days|0]§! 天；到期需目的站接通、开机方可卸货。',
      '[GetRUSIPFreightCargo] §Y[?RUS_ip_freight_amount|1]§! → [GetRUSIPFreightTo]\n§Y[?RUS_ip_freight_days|0]§! days; unloading needs an active connected destination.')
    L('freight_outbound','[GetRUSIPFreightShipment]','[GetRUSIPFreightShipment]')
    L('freight_outbound_tt','货物离库后独立计时，修改配置或拆掉出发站不改变已发货物。\n目的站断线则等待卸货。期满未到货退回出发区，并退还该批运费。','Dispatched cargo is independent of settings and the source station. A disconnected destination holds unloading. At plan expiry, unfinished shipments and their fees return to their sources.')
    L('freight_incoming','本区来货：§Y[?RUS_ip_freight_incoming_count|0]§! 批／§Y[?RUS_ip_freight_incoming_amount|1]§! 单位\n累计到货：§G+[?RUS_ip_freight_received|1]§!   全国净运费：§R-[?RUS_ip_freight_spent|1]§!',
      'Incoming: §Y[?RUS_ip_freight_incoming_count|0]§! batches / §Y[?RUS_ip_freight_incoming_amount|1]§! units\nReceived: §G+[?RUS_ip_freight_received|1]§!  Total freight costs: §R-[?RUS_ip_freight_spent|1]§!')
    L('freight_incoming_tt','§Y发往本区的货物§!\n'+'\n'.join(f'[GetRUSIPFreightInbound{i}]' for i in range(6)),
      '§YInbound shipments§!\n'+'\n'.join(f'[GetRUSIPFreightInbound{i}]' for i in range(6)))
    statuses=[('§G可在日末发运§!','§GReady for end-of-day dispatch§!'),('§Y自动发运已关闭§!','§YAutomatic dispatch disabled§!'),('§R本区运输站未接通或已停机§!','§RLocal station offline or stopped§!'),('§R目的区运输站未接通或已停机§!','§RDestination station offline or stopped§!'),('§Y超出保留量的货物不足1单位§!','§YLess than one unit above reserve§!'),('§R建设投资不足以支付运费§!','§RInsufficient investment for freight§!'),('§Y上一批货物运输中§!','§YCargo in transit§!'),('§Y已抵达，等待目的站卸货§!','§YArrived; waiting to unload§!'),('§Y本期已结束；未到货物已退回§!','§YPlan ended; unfinished cargo returned§!'),('§Y尚未开始生产，配置已保存§!','§YStart production to activate this route§!'),('§R请选择其他地区§!','§RChoose another region§!')]
    for index,(zh,en) in enumerate(statuses):L(f'freight_status_{index}',zh,en)
    defined('GetRUSIPFreightStatus',[(cv('freight_status','=',i),P+f'freight_status_{i}') for i in range(len(statuses))])
    for name,key in [('GetRUSIPFreightDestination','freight_destination'),('GetRUSIPFreightTo','freight_to')]:defined(name,[(cv(key,'=',r['id']),P+f'region_{r["id"]}') for r in REGIONS])
    for index,key in enumerate(STOCKS):
        zh,en=NAMES[key];L(f'freight_goods_{index}',zh,en);L(f'freight_goods_{index}_active','§Y'+zh+'§!','§Y'+en+'§!')
        L(f'freight_goods_{index}_tab',f'[GetRUSIPFreightGoodsTab{index}]',f'[GetRUSIPFreightGoodsTab{index}]')
        L(f'freight_goods_{index}_tt',f'发运货物：§Y{zh}§!\n本区库存：§Y[?RUS_ip_{key}|1]§!\n只改变下一批货物；已在途货物保持原样。',f'Cargo: §Y{en}§!\nLocal stock: §Y[?RUS_ip_{key}|1]§!\nChanges the next batch only.')
        defined(f'GetRUSIPFreightGoodsTab{index}',[(cv('freight_resource','=',index),P+f'freight_goods_{index}_active'),('',P+f'freight_goods_{index}')])
    for name,key in [('GetRUSIPFreightGoods','freight_resource'),('GetRUSIPFreightCargo','freight_cargo')]:defined(name,[(cv(key,'=',i),P+f'freight_goods_{i}') for i in range(len(STOCKS))])
    defined('GetRUSIPFreightShipment',[(cv('freight_amount','>',0),P+'freight_shipment'),('',P+'freight_empty')])
    L('freight_blank','','')
    for source in REGIONS:
        rid=source['id']
        defined(f'GetRUSIPFreightIncomingGoods{rid}',[(cv(f'r{rid}_freight_cargo','=',i),P+f'freight_goods_{i}') for i in range(len(STOCKS))])
        L(f'freight_inbound_{rid}',f'{source["zh"]}：[GetRUSIPFreightIncomingGoods{rid}] §Y[?RUS_ip_r{rid}_freight_amount|1]§!，剩余 [?RUS_ip_r{rid}_freight_days|0] 天',f'{source["en"]}: [GetRUSIPFreightIncomingGoods{rid}] §Y[?RUS_ip_r{rid}_freight_amount|1]§!, [?RUS_ip_r{rid}_freight_days|0] days')
        defined(f'GetRUSIPFreightInbound{rid}',[(cv(f'r{rid}_freight_amount','>',0)+cv(f'r{rid}_freight_to','=',P+'region'),P+f'freight_inbound_{rid}'),('',P+'freight_blank')])
        L(f'freight_dest_{rid}',f'[GetRUSIPFreightDestTab{rid}]',f'[GetRUSIPFreightDestTab{rid}]')
        defined(f'GetRUSIPFreightDestTab{rid}',[(cv('freight_destination','=',rid),P+f'region_{rid}_active'),('',P+f'region_{rid}')])


def widgets(text,icon,button,x):
    condition=cv('build_page','=',2)
    icon('ip_freight_icon','GFX_RUS_ip_facility_21',x,394,1,condition=condition,tip=P+'freight_rules_tt')
    text('ip_freight_title',P+'freight_title',x+42,398,460,26,'hoi_20b',condition=condition,tip=P+'freight_rules_tt')
    text('ip_freight_destination_label',P+'freight_destination_label',x,435,510,24,condition=condition)
    text('ip_freight_goods_label',P+'freight_goods_label',x,539,510,24,condition=condition)
    for r in REGIONS:
        rid=r['id'];local=condition+cv('region','=',rid)
        for index,target in enumerate(t for t in range(6) if t!=rid):
            button(f'ip_freight_r{rid}_dest_{target}',P+f'freight_dest_{target}',x+(index%3)*172,463+(index//3)*37,P+'freight_select_tt',f'RUS_ip_r{rid}_freight_target_{target} = yes\n','RUS_ip_freight_controls = yes',condition=local,scale=1.17)
        for index,key in enumerate(STOCKS):
            xx,yy=x+(index%5)*103,571+(index//5)*38
            name=f'ip_freight_r{rid}_goods_{index}';tip=P+f'freight_goods_{index}_tt'
            button(name,'',xx,yy,tip,f'RUS_ip_r{rid}_freight_goods_{index} = yes\n','RUS_ip_freight_controls = yes',condition=local,scale=.80)
            icon(name+'_icon','GFX_RUS_ip_resource_'+key,xx+3,yy+4,.55,condition=local)
            text(name+'_text',P+f'freight_goods_{index}_tab',xx+23,yy+5,77,23,condition=local,center=True)
        button(f'ip_freight_r{rid}_reserve',P+'freight_reserve_button',x,662,P+'freight_reserve_tt',f'RUS_ip_r{rid}_freight_reserve = yes\n','RUS_ip_freight_controls = yes',condition=local)
        button(f'ip_freight_r{rid}_toggle',P+'freight_toggle_button',x+166,662,P+'freight_toggle_tt',f'RUS_ip_r{rid}_freight_toggle = yes\n','RUS_ip_freight_controls = yes',condition=local,scale=1.3)
    text('ip_freight_preview',P+'freight_preview',x,713,510,65,condition=condition,tip=P+'freight_preview_tt')
    text('ip_freight_outbound',P+'freight_outbound',x,797,510,54,condition=condition,tip=P+'freight_outbound_tt')
    text('ip_freight_incoming',P+'freight_incoming',x,873,510,55,condition=condition,tip=P+'freight_incoming_tt')
