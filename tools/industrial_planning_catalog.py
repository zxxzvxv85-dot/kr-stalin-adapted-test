"""Factory recipes and regional specialisations, independent of UI and scripts.

Amounts are sandbox units. Rates and input ratios describe one effective level.
The six regions keep their existing coal/iron guarantees; additional deposits
follow resources recorded in their installed KR state catchments.
"""
DECISIONS = 'gfx/interface/decisions/'
STOCKS = ('coal', 'iron', 'steel', 'bauxite', 'chromium', 'tungsten', 'oil', 'aluminium', 'alloy', 'fuel')
PRICES = dict(machines=1, machine_tools=2, aircraft_parts=3, tractors=1.5,
              rail_equipment=2.5, generators=3, precision_tools=4)
PRODUCTS = tuple(PRICES)
STORED = (*STOCKS, *PRODUCTS, 'value')
TARGET = 500
FREIGHT_KIND = 21
FREIGHT_BATCH_PER_LEVEL = 6
FREIGHT_FEE = .1
FREIGHT_RESERVES = (0,3,6,12)
# Abstract travel times between the six regional hubs, in game days.
# They are gameplay distances, not queries of the native railway network.
FREIGHT_DAYS = (
    (0,3,4,7,10,14), (3,0,6,9,12,16), (4,6,0,6,10,14),
    (7,9,6,0,5,10), (10,12,10,5,0,6), (14,16,14,10,6,0),
)
TERRAINS = {1:'coal', 2:'iron', 5:'bauxite', 6:'chromium', 7:'tungsten', 8:'oil'}
DEPOSITS = (
    {}, {'bauxite':10}, {'chromium':8, 'tungsten':4, 'oil':10},
    {'bauxite':6, 'chromium':8, 'oil':4},
    {'bauxite':16, 'chromium':8},
    {'bauxite':2, 'chromium':6, 'tungsten':6, 'oil':4},
)
NAMES = {
    'coal':('煤炭','Coal'), 'iron':('铁矿','Iron ore'), 'steel':('钢材','Steel'),
    'bauxite':('铝土矿','Bauxite'), 'chromium':('铬矿','Chromium'), 'tungsten':('钨矿','Tungsten'),
    'oil':('原油','Crude oil'), 'aluminium':('铝材','Aluminium'), 'alloy':('特种合金','Special alloy'),
    'fuel':('工业燃料','Industrial fuel'), 'machines':('工业机械','Machinery'),
    'machine_tools':('机床','Machine tools'), 'aircraft_parts':('航空部件','Aircraft parts'),
    'tractors':('拖拉机','Tractors'), 'rail_equipment':('铁路装备','Rail equipment'),
    'generators':('发电设备','Generating equipment'), 'precision_tools':('精密工具','Precision tools'),
}

def plant(zh,en,icon,cost,key,rate,inputs=None,power=0,terrain=0,region=None,output=None):
    return dict(zh=zh,en=en,icon=DECISIONS+icon,cost=cost,key=key,rate=rate,
                inputs=inputs or {},power=power,terrain=terrain,region=region,output=output or key)

# Keep the original five IDs and recipes stable. Regional manufacturers use
# distinct IDs so their saved identity and hovered recipe cannot change on tabs.
PLANTS = {
    1:plant('煤矿','Coal mine','decision_coal.dds',3,'coal',.3,terrain=1),
    2:plant('铁矿','Iron mine','decision_steel.dds',3,'iron',.3,terrain=2),
    3:plant('燃煤电站','Coal power','decision_generic_electricity.dds',5,'power',.6,{'coal':1/6},output='power'),
    4:plant('钢铁厂','Steelworks','decision_generic_factory.dds',6,'steel',.2,{'coal':1,'iron':1},2),
    5:plant('机械厂','Machine works','decision_generic_industry.dds',8,'machine',.2,{'steel':2},1,output='machines'),
    6:plant('铝土矿场','Bauxite mine','decision_aluminium.dds',4,'bauxite',.3,terrain=5),
    7:plant('铬矿场','Chromium mine','decision_chromium.dds',4,'chromium',.2,terrain=6),
    8:plant('钨矿场','Tungsten mine','decision_tungsten.dds',5,'tungsten',.15,terrain=7),
    9:plant('油井','Oil well','decision_oil.dds',5,'oil',.3,terrain=8),
    10:plant('铝冶炼厂','Aluminium works','decision_aluminium.dds',9,'aluminium',.2,{'bauxite':1.5},3),
    11:plant('铬合金厂','Chromium alloys','decision_chromium.dds',9,'chrome_alloy',.2,{'steel':1,'chromium':.5},2,output='alloy'),
    12:plant('钨合金厂','Tungsten alloys','decision_tungsten.dds',10,'tungsten_alloy',.12,{'steel':1,'tungsten':.5},2.5,output='alloy'),
    13:plant('炼油厂','Oil refinery','decision_oil.dds',8,'fuel',.3,{'oil':1}),
    14:plant('燃油电站','Fuel power','decision_generic_electricity.dds',8,'fuel_power',.9,{'fuel':.1},output='power'),
    15:plant('机床厂','Machine tool works','decision_generic_research.dds',12,'machine_tools',.16,{'steel':2},2,region=0),
    16:plant('航空部件厂','Aircraft parts works','decision_generic_air.dds',16,'aircraft_parts',.14,{'steel':1,'aluminium':2},3,region=1),
    17:plant('拖拉机厂','Tractor works','decision_generic_motorized.dds',10,'tractors',.2,{'steel':2},1.2,region=2),
    18:plant('铁路装备厂','Rail equipment works','decision_generic_train.dds',14,'rail_equipment',.16,{'steel':1.5,'alloy':1},2.5,region=3),
    19:plant('动力设备厂','Power equipment works','decision_generic_electricity.dds',15,'generators',.14,{'steel':1,'aluminium':2},3,region=4),
    20:plant('精密工具厂','Precision tool works','decision_generic_army_support.dds',18,'precision_tools',.12,{'alloy':2,'tungsten':.5},3,region=5),
    21:plant('跨区运输站','Freight station','decision_generic_train.dds',10,'transport',0,output='transport'),
}
PLANTS[13]['icon']='gfx/interface/military_industrial_organization/trait_icons/generic/refinery_icon.png'
PLANTS[14]['icon']='gfx/interface/military_industrial_organization/trait_icons/generic/fuel_drum.png'
PLANTS[15]['icon']='gfx/interface/technologies/advanced_machine_tools.dds'
PLANTS[20]['icon']='gfx/interface/technologies/basic_machine_tools.dds'
PLANTS[21]['icon']='gfx/interface/military_industrial_organization/trait_icons/generic/railway_icon.png'
RESOURCE_ICONS = {key:PLANTS[k]['icon'] for key,k in dict(coal=1,iron=2,steel=4,bauxite=6,chromium=7,tungsten=8,oil=9,aluminium=10,alloy=11,fuel=14).items()}
PRODUCT_ICONS = {p['output']:p['icon'] for p in PLANTS.values() if p['output'] in PRODUCTS}
PROCESS_ORDER = (1,2,6,7,8,9,13,3,14,4,10,11,12,15,16,17,18,19,20,5)
# Refineries use their own auxiliary power; fuel can therefore bootstrap power.
# Regional manufacturers receive materials before generic machinery. Stopping
# a regional plant makes those materials available to generic production.

def allowed(kind,rid):
    p=PLANTS[kind]
    if p['region'] is not None:return p['region']==rid
    if kind<=5 or kind>=10:return True
    required={6:'bauxite',7:'chromium',8:'tungsten',9:'oil'}[kind]
    return DEPOSITS[rid].get(required,0)>0

def region_plants(rid):return tuple(k for k in PLANTS if allowed(k,rid))
def specialty(rid):return PLANTS[15+rid]
def extra_stocks(rid):
    # Imported raw materials and intermediates must remain visible even when
    # the receiving region has no local deposits of that mineral.
    return STOCKS[3:]
