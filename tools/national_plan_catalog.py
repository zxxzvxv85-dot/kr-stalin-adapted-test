"""National plan catalogue; legacy source is reviewed and owned in catalog.json.

No import-time writes. The 46 legacy rewards and their scoring calls are retained.
"""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=ROOT/'tools/design/national_plan_20261104/catalog.json'
DATA=json.loads(SPEC.read_text(encoding='utf8'))
REGIONS={1:'莫斯科与中央工业区',2:'列宁格勒与西北工业区',3:'察里津与伏尔加工业区',4:'乌拉尔工业区',5:'西伯利亚与远东',6:'高加索与中亚'}
# Mod-owned reward metadata. Existing native rewards remain unmodified.
MIO_TARGETS={
 'amo':('RUS_amo_organisation','RUS_adb_merged_amo','RUS_adb_organisation','汽车工业'),
 'toz':('RUS_toz_organisation','RUS_odb_merged_toz','RUS_odb_organisation','图拉兵工'),
 'uztm':('RUS_uztm_organisation','RUS_adb_merged_uztm','RUS_adb_organisation','乌拉尔重型机械'),
 'av':('RUS_av_organisation',None,None,'海军部船坞'),
}
MIO_REWARDS={'modernisation_of_AMO':('amo',0),'tula_arms_factory':('toz',0),
             'uralmash':('uztm',0),'admiralty_dockyards':('av',0),'volkhov':('consortium',1)}
CONSORTIUM_MIOS=tuple('RUS_'+key+'_organisation' for key in ('osoavia','duks','tsagi','gamayun','skorost','sokol'))
FACTORY_GOALS={
 'gaz':(0,'industrial_complex','民用工厂',1,'industrial_complex'),
 'uvz':(1,'arms_factory','军用工厂',1,'arms_factory'),
 'krasnoyarskpromstroy':(0,'industrial_complex','民用工厂',1,None),
}
NEW_ROWS=[
 ('gaz','下诺夫哥罗德汽车厂',252,1,'industry',180,140,40,'factory','https://museum.gaz.ru/eng/gaz-history/'),
 ('bearing','莫斯科第一轴承厂',219,1,'industry',150,100,35,'factory','https://mr.moscow/na-sovetskih-podshipnikah/'),
 ('kashira','卡希拉电站扩建',219,1,'energy',180,140,40,'energy','https://www.mosenergo-museum.ru/History_of_Mosenergo/Historical_Review/21420/'),
 ('moscow_grid','莫斯科高压环网',219,1,'energy',120,80,25,'grid','https://www.mosenergo-museum.ru/Museum/News/21903/'),
 ('metro','莫斯科地铁第一期',219,1,'city',270,180,50,'metro','https://www.mosmetro.ru/about/history'),
 ('moscow_volga','莫斯科—伏尔加运河',247,1,'road',540,220,75,'canal','https://www.mosvodokanal.ru/about/history/'),
 ('svir','下斯维里水电站',216,2,'energy',365,220,60,'energy','https://www.so-ups.ru/memorial-day/history-event/news/9803/'),
 ('volkhov','沃尔霍夫铝厂',264,2,'industry',210,160,45,'aluminium','https://www.rusal.ru/about/facts/'),
 ('uvz','乌拉尔车辆厂',653,4,'industry',240,180,50,'wagons','https://www.rostec.ru/media/news/uralvagonzavod-pervyy-i-edinstvennyy/'),
 ('bobrik','博布里基化工联合体',223,1,'agriculture',210,160,45,'fertilizer','https://www.eurochem.ru/nak-azot/'),
]
for key,state,region,name in [('moscow',219,1,'莫斯科'),('leningrad',195,2,'列宁格勒'),('tsaritsyn',217,3,'察里津')]:
    NEW_ROWS += [(key+'_logistics',name+'工业区物流调度中心',state,region,'rail',120,80,25,'hub','mechanism adaptation'),
                 (key+'_rural',name+'工业区农机维修与服务网络',state,region,'agriculture',120,60,20,'rural','mechanism adaptation')]
PROJECTS=[dict(p) for p in DATA['legacy']]
for p in PROJECTS:
    p['original_id']=p['id']
    p['id']='RUS_np_project_'+p['key']
for key,name,state,region,kind,days,budget,cost,reward,source in NEW_ROWS:
    PROJECTS.append(dict(id='RUS_np_'+key,key=key,legacy=False,name=name,states=[state],region=region,kind=kind,
        base_days=str(days),fallback=days,budget=budget,cost=cost,trains=15 if kind=='rail' else 10 if kind in ('industry','energy') else 5,
        civ=2 if kind in ('industry','energy','city') else 1,reward=reward,source=source))
assert len(PROJECTS)==62 and len({p['id'] for p in PROJECTS})==62
for p in PROJECTS:
    # Different real commitments: urban/road works use builders, extraction
    # and long-distance railworks use rolling stock plus the native burden.
    p['consumer']=0
    if p['kind'] in ('rail','resource'):p['civ']=0
    if p['kind'] in ('city','road'):p['trains']=0
    if p.get('reward')=='rural':p['trains']=0
    if p['key']=='bearing':p['civ']=1;p['trains']=0
    if p['key']=='metro':p['civ']=3;p['consumer']=.01
    if p['key']=='moscow_volga':p['civ']=3;p['trains']=20
    if p['key']=='bobrik':p['civ']=0;p['consumer']=.02

# Fixed registered corridors. Weights are province segments, not arbitrary
# state maximum rail levels. Only completed plan railway works enter the ledger.
CORRIDORS=json.loads((SPEC.parent/'corridors.json').read_text(encoding='utf8'))['corridors']
