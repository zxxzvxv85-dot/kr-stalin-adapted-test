// Deterministic expansion of the five-crop national agriculture scripts and UI.
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const crops = ['wheat', 'rye', 'beet', 'flax', 'cotton'];
const n = x => 'RUS_nat_' + x;
const a = x => 'RUS_agri_' + x;
const v = (k, x) => `set_variable = { ${n(k)} = ${x} }\n`;
const op = (type, k, x) => `${type}_variable = { ${n(k)} = ${x} }\n`;
const add = (k, x) => op('add_to', k, x);
const sub = (k, x) => op('subtract_from', k, x);
const mul = (k, x) => op('multiply', k, x);
const div = (k, x) => op('divide', k, x);
const cl = (k, min, max) => `clamp_variable = { var = ${n(k)} min = ${min} max = ${max} }\n`;
const ck = (k, rel, x) => `check_variable = { ${n(k)} ${rel} ${x} }`;
const flag = x => `has_country_flag = ${x}`;
const iff = (test, yes, no = '') => `if = { limit = { ${test} }\n${yes}}\n${no ? `else = {\n${no}}\n` : ''}`;
const call = x => `${n(x)} = yes\n`;
const effects = [];
const effect = (id, body) => effects.push(`${n(id)} = {\n${body}}\n`);
const write = (file, text, bom = false) => { fs.mkdirSync(path.dirname(path.join(root, file)), { recursive: true }); fs.writeFileSync(path.join(root, file), (bom ? '\uFEFF' : '') + text); };
const mode = flag(n('enabled'));
const success = flag('RUS_maximalist_land_reform_success');
const failure = flag('RUS_maximalist_land_reform_failure');
const active = flag('RUS_maximalist_land_reform_in_progress');

// HOI4 has 365-day years; global.num_days is year * 365 on January 1.
effect('calendar', v('doy', 'global.num_days') + op('modulo', 'doy', 365) + v('season', 4) + v('season_length', 90) + v('remaining', 59) + sub('remaining', n('doy')) +
  iff(ck('doy', '>', 333), v('remaining', 424) + sub('remaining', n('doy'))) +
  [[59,151,1,92],[151,243,2,92],[243,334,3,91]].map(([start,end,season,len]) => iff(`${ck('doy','>',start-1)} ${ck('doy','<',end)}`, v('season',season)+v('season_length',len)+v('remaining',end)+sub('remaining',n('doy')))).join(''));
effect('enable', iff(`NOT = { ${mode} }`, `set_country_flag = ${n('enabled')}\nset_country_flag = RUS_agri_management_unlocked\n` +
 v('factories',0)+v('efficiency',3000)+v('installed',100)+v('machine_stock',0)+v('produced',0)+v('reserve',1)+v('page',1)+v('target',400)+v('last_day','global.num_days')+
 crops.map((c,i)=>v(c+'_stock',i<2?4:2)).join('')+call('start_quarter')+
 `add_dynamic_modifier = { modifier = RUS_nat_industry }\n`));
effect('parameters', v('score',0)+iff(flag('RUS_first_five_year_plan_mission_started'),v('score','RUS_first_five_year_plan_score'))+cl('score',0,150)+
 v('output','modifier@industrial_capacity_factory')+mul('output',.5)+add('output',1)+v('tmp',n('score'))+mul('tmp',.002)+add('output',n('tmp'))+cl('output',.5,2)+
 v('cap','modifier@production_factory_max_efficiency_factor')+mul('cap',5000)+add('cap',6500)+v('tmp',n('score'))+mul('tmp',10)+add('cap',n('tmp'))+cl('cap',4500,10000)+
 v('growth','modifier@production_factory_efficiency_gain_factor')+mul('growth',.5)+add('growth',1)+v('tmp',n('score'))+mul('tmp',.002)+add('growth',n('tmp'))+cl('growth',.25,2)+
 cl('efficiency',3000,n('cap'))+v('daily',n('factories'))+mul('daily',1.2)+mul('daily',n('efficiency'))+div('daily',10000)+mul('daily',n('output'))+
 v('room',n('target'))+sub('room',n('installed'))+add('room',4500)+sub('room',n('machine_stock'))+cl('room',0,1001000)+cl('daily',0,n('room'))+
 v('eff_display',n('efficiency'))+div('eff_display',100)+v('cap_display',n('cap'))+div('cap_display',100)+
 v('available','num_of_civilian_factories_available_for_projects')+cl('available',0,1000000));
// Query capacity with our own reservation released; the engine may floor free factories at zero.
effect('factory_capacity',v('held_factories',n('factories'))+v('factories',0)+`force_update_dynamic_modifier = yes\n`+
 v('capacity','num_of_civilian_factories_available_for_projects')+cl('capacity',0,1000000)+v('factories',n('held_factories'))+cl('factories',0,n('capacity'))+`force_update_dynamic_modifier = yes\n`);
effect('set_factories', call('factory_capacity')+call('parameters')+v('max_factories',n('capacity'))+cl('requested',0,n('max_factories'))+
 iff(ck('requested','>',n('factories')), v('tmp',n('requested'))+sub('tmp',n('factories'))+mul('tmp',3000)+mul('efficiency',n('factories'))+add('efficiency',n('tmp'))+div('efficiency',n('requested')))+
 v('factories',n('requested'))+`force_update_dynamic_modifier = yes\n`+call('parameters')+`RUS_agri_refresh_gui = yes\n`);
effect('install', v('needed',n('target'))+sub('needed',n('installed'))+cl('needed',0,n('machine_stock'))+sub('machine_stock',n('needed'))+add('installed',n('needed')));
effect('production_day', call('factory_capacity')+call('parameters')+
 v('room',n('target'))+sub('room',n('installed'))+add('room',4500)+sub('room',n('machine_stock'))+cl('room',0,1001000)+
 iff(`${ck('factories','>',0)} ${ck('room','>',0)}`,v('step',n('cap'))+sub('step',n('efficiency'))+mul('step',.004)+mul('step',n('growth'))+add('efficiency',n('step'))+call('parameters')+cl('daily',0,n('room'))+add('machine_stock',n('daily'))+add('produced',n('daily'))+call('install'),
 sub('efficiency',10)+cl('efficiency',3000,n('cap'))+v('daily',0))+
 v('coverage',n('installed'))+div('coverage',n('target'))+cl('coverage',0,1)+add('coverage_sum',n('coverage'))+add('elapsed',1)+
 iff(`${active} NOT = { ${failure} }`,add('eligible_days',1)));
effect('draw_orders', ['generic','fra','eng'].map((o)=>v(o+'_crop',0)+v(o+'_quantity',0)+v(o+'_shipped',0)+v(o+'_accept',1)+v(o+'_priority',o==='generic'?1:o==='fra'?2:3)).join('')+
 ['fra','eng'].map(o=>v(o+'_machine_quantity',0)+v(o+'_machine_shipped',0)+v(o+'_machine_accept',1)).join('')+
 [['generic','has_completed_focus = RUS_future_foreign_002'],['fra','has_completed_focus = RUS_future_foreign_017 country_exists = FRA'],['eng','has_completed_focus = RUS_future_foreign_017 country_exists = ENG']].map(([o,t])=>iff(t,
 `random_list = { ${crops.map((c,i)=>`1 = { ${v(o+'_crop',i+1)} }`).join(' ')} }\nrandom_list = { ${[2,3,4].map(x=>`1 = { ${v(o+'_quantity',x)} }`).join(' ')} }\n`+
 (o==='generic'?'':`random_list = { ${[60,80,100].map(x=>`1 = { ${v(o+'_machine_quantity',x)} }`).join(' ')} }\n`))).join(''));
effect('start_quarter', call('calendar')+v('quarter_end','global.num_days')+add('quarter_end',n('remaining'))+v('elapsed',0)+v('eligible_days',0)+v('coverage_sum',0)+v('target',400)+iff(success,v('target',500))+
 v('support_count',0)+v('technical_support',0)+v('repair_support',0)+v('emergency_purchase',0)+['food','processing','textiles','technical','repair','emergency'].map(k=>v('support_'+k,0)).join('')+
 v('budget',20)+iff(success,add('budget',2))+iff(flag('RUS_max_landreform_tractor_promise_kept'),add('budget',2))+
 v('food_demand',8)+v('beet_demand',2)+v('textile_demand',4)+iff('has_war = yes',add('food_demand',2)+add('textile_demand',1))+
 `set_country_flag = RUS_agri_quarter_active\nclr_country_flag = RUS_agri_allocation_locked\nRUS_agri_activate_next_investment = yes\nset_variable = { RUS_agri_season = ${n('season')} }\n`+
 crops.map(c=>`set_variable = { ${a(c+'_investment')} = 0 }\n`).join('')+
 `RUS_agri_set_base_rates = yes\nRUS_agri_draw_weather = yes\nRUS_agri_draw_market = yes\nRUS_agri_draw_business_conditions = yes\n`+
 `random_list = { 20 = { ${v('wear',.1)} } 40 = { ${v('wear',.15)} } 30 = { ${v('wear',.2)} } 10 = { ${v('wear',.25)} } }\n`+
 `random_list = { 1 = { ${v('task',1)} } 1 = { ${v('task',2)} } 1 = { ${v('task',3)} } }\n`+
 `random_list = { 1 = { ${v('machine_forecast',-1)} } 1 = { ${v('machine_forecast',0)} } 1 = { ${v('machine_forecast',1)} } }\n`+
 iff(ck('machine_forecast','=',0),`random_list = { 60 = { ${v('machine_market',0)} } 20 = { ${v('machine_market',.2)} } 20 = { ${v('machine_market',-.2)} } }\n`,
 `random_list = { 70 = { ${v('machine_market',.2)} } 20 = { ${v('machine_market',0)} } 10 = { ${v('machine_market',-.2)} } }\n`+mul('machine_market',n('machine_forecast')))+
 call('draw_orders')+call('refresh'));
effect('totals',v('allocated',0)+crops.map(c=>add('allocated',a(c+'_investment'))).join('')+v('unused',n('budget'))+sub('unused',n('allocated'))+
 crops.map(c=>`clr_country_flag = RUS_agri_saturation_${c}\n`+v('concentration',a(c+'_investment'))+mul('concentration',2)+iff(`${flag('RUS_agri_previous_dominant_'+c)} ${ck('allocated','>',0)} ${ck('concentration','>',n('allocated'))}`,`set_country_flag = RUS_agri_saturation_${c}\n`)).join('')+
 `set_variable = { RUS_agri_total_investment = ${n('allocated')} }\nset_variable = { RUS_agri_investment_limit = ${n('budget')} }\n`);
effect('yield', v('harvest',0)+v('mechanisation',n('coverage_sum'))+
 iff(ck('elapsed','>',0),div('mechanisation',n('elapsed')),v('mechanisation',n('installed'))+div('mechanisation',n('target')))+cl('mechanisation',0,1)+v('mean_coverage',n('mechanisation'))+mul('mechanisation',.2)+add('mechanisation',.9)+
 crops.map(c=>v(c+'_rate',a(c+'_base'))+v('tmp',a(c+'_fatigue'))+mul('tmp',.15)+sub(c+'_rate',n('tmp'))+
 iff(ck('actual','=',1),add(c+'_rate','RUS_agri_weather'))+cl(c+'_rate',.4,1.5)+
 iff(`${flag('RUS_agri_active_storage')} ${ck(c+'_rate','<',1)}`,add(c+'_rate',.15)+cl(c+'_rate',.4,1))+
 v(c+'_yield',a(c+'_investment'))+mul(c+'_yield',n(c+'_rate'))+mul(c+'_yield',n('mechanisation'))+mul(c+'_yield',n('fraction'))+
 iff('has_idea = RUS_andrey_kolegayev_advisor',mul(c+'_yield',1.05))+iff(ck('technical_support','=',1),mul(c+'_yield',1.05))+add('harvest',n(c+'_yield'))).join(''));
const groups = [['food',['wheat','rye']],['beet',['beet']],['textile',['flax','cotton']]];
effect('consume',groups.map(([g,cs])=>v(g+'_available',0)+cs.map(c=>add(g+'_available',n(c+'_work'))).join('')+v(g+'_need',n(g+'_demand'))+mul(g+'_need',n('fraction'))+
 v(g+'_delivered',n(g+'_available'))+cl(g+'_delivered',0,n(g+'_need'))+v(g+'_ratio',1)+iff(ck(g+'_need','>',0),v(g+'_ratio',n(g+'_delivered'))+div(g+'_ratio',n(g+'_need')))+
 iff(ck(g+'_available','>',0),cs.map(c=>v('tmp',n(c+'_work'))+div('tmp',n(g+'_available'))+mul('tmp',n(g+'_delivered'))+sub(c+'_work',n('tmp'))+cl(c+'_work',0,100000)).join(''))+
 v(g+'_reserve',n(g+'_demand'))+mul(g+'_reserve',n('reserve'))+v(g+'_left',n(g+'_available'))+sub(g+'_left',n(g+'_delivered'))).join(''));
effect('trade',v('income',0)+crops.map(c=>v(c+'_sold',0)).join('')+
  [1,2,3].map(rank=>['generic','fra','eng'].map(o=>iff(`${ck(o+'_priority','=',rank)} ${ck(o+'_accept','=',1)} ${ck(o+'_shipped','=',0)} ${ck(o+'_quantity','>',0)} ${groups.map(([g])=>ck(g+'_ratio','>',.9999)).join(' ')}`,
 crops.map((c,i)=>{const g=i<2?'food':i===2?'beet':'textile';return iff(ck(o+'_crop','=',i+1),v('free',n(g+'_left'))+sub('free',n(g+'_reserve'))+
 iff(`${ck('free','>',-0.0001)} NOT = { ${ck('free','<',n(o+'_quantity'))} } NOT = { ${ck(c+'_work','<',n(o+'_quantity'))} } ${ck(g+'_ratio','>',.9999)}`,
 v('price',1)+iff(ck('actual','=',1),add('price',a(c+'_market')))+iff(flag('RUS_agri_saturation_'+c),sub('price',.15))+ (o==='generic'?'':add('price',.1))+
 // Marginal pricing across all contracts, without discounting domestic consumption.
 v('order_cash',0)+v('units',n(o+'_quantity'))+`while_loop_effect = { limit = { ${ck('units','>',0)} }\n`+
 v('unit_price',n('price'))+iff(`NOT = { ${ck(c+'_sold','<',a(c+'_capacity'))} }`,sub('unit_price',.3))+
 v('tmp',a(c+'_capacity'))+add('tmp',2)+iff(`NOT = { ${ck(c+'_sold','<',n('tmp'))} }`,sub('unit_price',.4))+cl('unit_price',.4,1.5)+add('order_cash',n('unit_price'))+add(c+'_sold',1)+sub('units',1)+`}\n`+
 mul('order_cash',1000)+add('income',n('order_cash'))+sub(c+'_work',n(o+'_quantity'))+sub(g+'_left',n(o+'_quantity'))+
 iff(ck('actual','=',1),v(o+'_shipped',1))))}).join(''))).join('')).join('')+
 ['fra','eng'].map(o=>iff(`${ck(o+'_machine_accept','=',1)} ${ck(o+'_machine_shipped','=',0)} ${ck(o+'_machine_quantity','>',0)}`,
 v('free',n('machine_work'))+v('tmp',n('target'))+mul('tmp',.25)+sub('free',n('tmp'))+
 iff(`NOT = { ${ck('free','<',n(o+'_machine_quantity'))} } NOT = { ${ck('installed','<',n('target'))} }`,
 v('price',1.1)+iff(ck('actual','=',1),add('price',n('machine_market')))+cl('price',.4,1.5)+mul('price',150)+mul('price',n(o+'_machine_quantity'))+add('income',n('price'))+sub('machine_work',n(o+'_machine_quantity'))+iff(ck('actual','=',1),v(o+'_machine_shipped',1))))).join(''));
effect('refresh',v('remaining',n('quarter_end'))+sub('remaining','global.num_days')+cl('remaining',0,92)+`set_variable = { RUS_agri_days_remaining = ${n('remaining')} }\n`+call('totals')+call('parameters')+
 v('fraction',n('elapsed'))+add('fraction',n('remaining'))+div('fraction',n('season_length'))+v('actual',0)+call('yield')+
 crops.map(c=>v(c+'_work',n(c+'_stock'))+add(c+'_work',n(c+'_yield'))).join('')+call('consume')+v('machine_work',n('machine_stock'))+call('trade')+v('preview_income',n('income'))+
 groups.map(([g])=>v(g+'_preview',n(g+'_ratio'))+mul(g+'_preview',100)+v(g+'_gap',n(g+'_need'))+sub(g+'_gap',n(g+'_delivered'))+cl(g+'_gap',0,1000)).join('')+
 v('coverage_display',n('mean_coverage'))+mul('coverage_display',100)+
 `RUS_agri_refresh_gui = yes\n`);
// Public-information greedy allocator: prioritise food, processing, textiles, then reserves.
effect('auto_allocate',crops.map(c=>`set_variable = { ${a(c+'_investment')} = 0 }\n`).join('')+
 v('iterations',n('budget'))+`while_loop_effect = { limit = { ${ck('iterations','>',0)} }\n`+call('refresh')+v('chosen',0)+v('best',-1000)+
 crops.map((c,i)=>{const g=i<2?'food':i===2?'beet':'textile';return iff(`check_variable = { ${a(c+'_investment')} < 10 }`,v('utility',n(c+'_rate'))+v('tmp',a(c+'_fatigue'))+mul('tmp',.001)+sub('utility',n('tmp'))+
 iff(ck(g+'_ratio','<',.9999),add('utility',g==='food'?300:g==='beet'?200:100),iff(ck(g+'_left','<',n(g+'_reserve')),add('utility',30)))+
 iff(ck('utility','>',n('best')),v('chosen',i+1)+v('best',n('utility'))))}).join('')+
 crops.map((c,i)=>iff(ck('chosen','=',i+1),`add_to_variable = { ${a(c+'_investment')} = 1 }\n`)).join('')+sub('iterations',1)+`}\n`+call('refresh'));
effect('award',v('points',0)+iff(ck('food_ratio','>',.9999),add('points',2),iff(ck('food_ratio','>',.8999),add('points',1)))+
 iff(ck('beet_ratio','>',.9999),add('points',.5))+iff(ck('textile_ratio','>',.9999),add('points',.5))+
 v('domestic_raw',n('points'))+
 iff(`NOT = { ${ck('food_left','<',n('food_demand'))} }`,add('points',2))+iff(ck('mean_coverage','>',.8999),add('points',2))+
 v('diverse',0)+crops.map(c=>iff(`check_variable = { ${a(c+'_investment')} > 2 }`,add('diverse',1))).join('')+
 v('task_done',0)+iff(`${ck('task','=',1)} ${groups.map(([g])=>ck(g+'_ratio','>',.9999)).join(' ')}`,v('task_done',1))+
 iff(`${ck('task','=',2)} ${groups.map(([g])=>`NOT = { ${ck(g+'_left','<',n(g+'_demand'))} }`).join(' ')}`,v('task_done',1))+
 iff(`${ck('task','=',3)} ${ck('diverse','>',3)}`,v('task_done',1))+
 iff(ck('task_done','=',1),add('points',4)+iff('has_idea = RUS_aleksey_ustinov_advisor',add('points',1)))+
 v('score_fraction',n('fraction'))+iff(`NOT = { ${success} }`,v('score_fraction',n('eligible_days'))+div('score_fraction',n('season_length')))+mul('points',n('score_fraction'))+
 mul('domestic_raw',n('score_fraction'))+sub('points',n('domestic_raw'))+v('domestic_room',12)+sub('domestic_room',n('domestic_year'))+cl('domestic_raw',0,n('domestic_room'))+add('points',n('domestic_raw'))+
 `set_variable = { RUS_agri_score_award = ${n('points')} }\nRUS_agri_credit_score = yes\nset_variable = { RUS_agri_last_quarter_score = RUS_agri_score_award }\n`+
 iff(`NOT = { ${failure} } OR = { ${active} ${success} }`,add('domestic_year',n('domestic_raw')))+
 v('last_pp',0)+iff(groups.map(([g])=>ck(g+'_ratio','>',.9999)).join(' '),v('last_pp',50)+mul('last_pp',n('fraction'))+v('pp_room',200)+sub('pp_room',n('pp_year'))+cl('last_pp',0,n('pp_room'))+add('pp_year',n('last_pp'))+`add_political_power = ${n('last_pp')}\n`));
effect('penalties',iff(ck('food_ratio','<',.9),add('shortage',1),sub('shortage',1))+cl('shortage',0,3)+v('stability',n('shortage'))+mul('stability',-.02)+v('consumer',n('shortage'))+mul('consumer',.02)+cl('consumer',0,.05)+
 v('factory_penalty',0)+iff(ck('beet_ratio','<',.9999),sub('factory_penalty',.03))+iff(ck('textile_ratio','<',.9999),sub('factory_penalty',.03))+cl('factory_penalty',-.05,0)+`force_update_dynamic_modifier = yes\n`);
effect('annual',v('annual_average',n('year_supply'))+div('annual_average',n('year_weight'))+
 ['shortfall','surplus','bumper_surplus'].map(t=>`remove_ideas = RUS_agri_annual_${t}\n`).join('')+
 iff(ck('annual_average','<',.9),`add_timed_idea = { idea = RUS_agri_annual_shortfall days = 365 }\n`,
 iff(ck('annual_average','>',.9999),iff(groups.map(([g])=>`NOT = { ${ck(g+'_left','<',n(g+'_demand'))} }`).join(' '),`add_timed_idea = { idea = RUS_agri_annual_bumper_surplus days = 365 }\n`,`add_timed_idea = { idea = RUS_agri_annual_surplus days = 365 }\n`)))+
 v('last_annual',n('annual_average'))+mul('last_annual',100)+v('year_supply',0)+v('year_weight',0)+v('domestic_year',0)+v('pp_year',0)+`country_event = { id = RUS_national_agriculture.1 }\n`);
effect('settle',iff(ck('elapsed','>',0),
 iff(`NOT = { ${flag('RUS_agri_allocation_locked')} }`,call('auto_allocate')+`set_country_flag = RUS_agri_allocation_locked\n`)+
 v('fraction',n('elapsed'))+div('fraction',n('season_length'))+v('actual',1)+call('yield')+crops.map(c=>v(c+'_work',n(c+'_stock'))+add(c+'_work',n(c+'_yield'))+v(c+'_last_yield',n(c+'_yield'))+v(c+'_last_market',a(c+'_market'))).join('')+
 call('emergency_fill')+call('consume')+
 v('loss_rate',n('wear'))+iff('check_variable = { RUS_agri_weather < 0 }',add('loss_rate',.05))+sub('loss_rate',n('repair_support'))+cl('loss_rate',0,.3)+v('loss',n('installed'))+mul('loss',n('loss_rate'))+mul('loss',n('fraction'))+sub('installed',n('loss'))+call('install')+
 v('machine_work',n('machine_stock'))+call('trade')+`add_cic = ${n('income')}\n`+v('machine_stock',n('machine_work'))+v('last_income',n('income'))+v('last_loss',n('loss'))+v('last_weather','RUS_agri_weather')+v('last_machine_market',n('machine_market'))+v('last_season',n('season'))+
 v('last_crop_orders',0)+['generic','fra','eng'].map(o=>add('last_crop_orders',n(o+'_shipped'))).join('')+v('last_machine_orders',0)+['fra','eng'].map(o=>add('last_machine_orders',n(o+'_machine_shipped'))).join('')+
 v('retention',.95)+iff('has_idea = RUS_irina_kakhovskaya_advisor',v('retention',.98))+
 // Prorate losses, and do not let capped inventory manufacture additional goods.
 v('spoil',1)+sub('spoil',n('retention'))+mul('spoil',n('fraction'))+v('retention',1)+sub('retention',n('spoil'))+
 crops.map((c,i)=>v(c+'_stock',n(c+'_work'))+cl(c+'_stock',0,i<2?12:6)+mul(c+'_stock',n('retention'))).join('')+
 groups.map(([g,cs])=>v(g+'_left',0)+cs.map(c=>add(g+'_left',n(c+'_stock'))).join('')).join('')+call('award')+
 groups.map(([g])=>v(g+'_last_ratio',n(g+'_ratio'))+mul(g+'_last_ratio',100)).join('')+
 v('supply',0)+groups.map(([g])=>add('supply',n(g+'_ratio'))).join('')+div('supply',3)+mul('supply',n('fraction'))+add('year_supply',n('supply'))+add('year_weight',n('fraction'))+
 iff(ck('boundary','=',1),call('penalties')+`RUS_agri_update_rotation = yes\nRUS_agri_record_dominant_crop = yes\n`)+
 `set_country_flag = RUS_nat_has_report\n`+v('elapsed',0)+v('eligible_days',0)+v('coverage_sum',0)+
 iff(`${ck('boundary','=',1)} ${ck('season','=',4)}`,call('annual'))));
effect('daily',iff(`${mode} ${ck('last_day','<','global.num_days')}`,
 v('last_day','global.num_days')+call('production_day')+
 iff(`NOT = { ${ck('quarter_end','>','global.num_days')} }`,v('boundary',1)+call('settle')+call('start_quarter'),call('refresh'))));
effect('deadline',iff(mode,call('daily')+v('boundary',0)+call('settle')+call('refresh')));
effect('emergency_fill',iff(ck('emergency_purchase','=',1),v('emergency_need',n('food_demand'))+mul('emergency_need',n('fraction'))+mul('emergency_need',.9)+sub('emergency_need',n('wheat_work'))+sub('emergency_need',n('rye_work'))+cl('emergency_need',0,4)+add('wheat_work',n('emergency_need'))+v('emergency_purchase',0)));
write('common/scripted_effects/RUS_national_agriculture_effects.txt', '# Generated by tools/generate_national_agriculture.cjs\n'+effects.join('\n'));
write('common/dynamic_modifiers/RUS_national_agriculture_modifiers.txt',`RUS_nat_industry = { enable = { ${mode} } civilian_factory_use = RUS_nat_factories stability_factor = RUS_nat_stability consumer_goods_expected_value = RUS_nat_consumer industrial_capacity_factory = RUS_nat_factory_penalty }\n`);
write('common/scripted_triggers/RUS_national_agriculture_triggers.txt',`RUS_nat_reform_complete = { OR = { AND = { ${mode} NOT = { check_variable = { RUS_maximalist_land_reform_score < 150 } } } AND = { NOT = { ${mode} } NOT = { check_variable = { RUS_maximalist_land_reform_score < 100 } } } } }\nRUS_nat_reform_decision_closed = { OR = { RUS_nat_reform_complete = yes AND = { ${mode} NOT = { ${active} } } } }\nRUS_nat_tractor_complete = { check_variable = { RUS_max_landreform_tractor_promise_count > 2 } OR = { NOT = { ${mode} } NOT = { check_variable = { RUS_nat_produced < 3000 } } } }\nRUS_nat_promote_allowed = { OR = { RUS_nat_reform_decision_closed = no AND = { ${mode} NOT = { ${failure} } has_country_flag = RUS_max_landreform_tractor_promise_active check_variable = { RUS_max_landreform_tractor_promise_count < 3 } } } }\n`);

// UI and translations are emitted below; all UI changes route through country-scoped effects.
const loc = {};
function label(key, zh, en, ru) { loc[key] = [zh,en,ru]; return key; }
label(n('support_available'),'本季政治点支援少于2项，且本项尚未实施。','Fewer than two political support measures this quarter; this measure not yet used.','Менее двух мер поддержки за квартал; эта мера ещё не применялась.');
const support = [
 ['food',40,['跨区粮食调运','Interregional Grain Deliveries','Межрегиональные поставки зерна'],['增加4单位小麦库存','Add 4 units of wheat','Добавить 4 ед. пшеницы'],add('wheat_stock',4)+cl('wheat_stock',0,12)],
 ['processing',35,['补充加工原料','Processing Supplies','Сырьё для переработки'],['增加2单位甜菜库存','Add 2 units of beet','Добавить 2 ед. свёклы'],add('beet_stock',2)+cl('beet_stock',0,6)],
 ['textiles',40,['保障纺织原料','Textile Supplies','Сырьё для текстиля'],['亚麻、棉花库存各增加1.5单位','Add 1.5 units each of flax and cotton','Добавить по 1,5 ед. льна и хлопка'],add('flax_stock',1.5)+cl('flax_stock',0,6)+add('cotton_stock',1.5)+cl('cotton_stock',0,6)],
 ['technical',50,['派驻农业技术组','Agronomic Support','Агрономическая поддержка'],['本季作物产量+5%','Crop output +5% this quarter','Урожайность +5% в этом квартале'],v('technical_support',1)],
 ['repair',40,['农机集中检修','Machinery Overhaul','Ремонт сельхозтехники'],['本季农机损耗率降低5个百分点','Machinery wear -5 percentage points this quarter','Износ техники -5 п.п. в этом квартале'],v('repair_support',.05)],
 ['emergency',60,['启动应急粮食采购','Emergency Grain Procurement','Экстренная закупка зерна'],['结算时补粮至90%内需，最多补4单位；不产生可出口余粮','At settlement, cover up to 90% of food needs; maximum 4 units, no export surplus','При расчёте покрыть до 90% потребности в зерне: не более 4 ед., без экспортного излишка'],v('emergency_purchase',1)]
];
write('common/decisions/RUS_national_agriculture_decisions.txt',`RUS_agricultural_quarterly_management_category = {\n`+support.map(([id,cost,names,desc,body])=>{
 label(n('support_'+id),...names);label(n('support_'+id+'_desc'),...desc.map((t,i)=>t+['。每季限一次，政治点支援每季最多两项。','; once per quarter, at most two political support measures per quarter.','; один раз за квартал, максимум две меры поддержки за квартал.'][i]));
 label(n('support_'+id+'_effect'),...desc);
 return `${n('support_'+id)} = { icon = GFX_decision_generic_agriculture cost = ${cost} visible = { ${mode} } available = { custom_trigger_tooltip = { tooltip = ${n('support_available')} ${mode} ${ck('support_count','<',2)} ${ck('support_'+id,'=',0)} } } complete_effect = { custom_effect_tooltip = ${n('support_'+id+'_effect')} hidden_effect = { ${iff(`${mode} ${ck('support_count','<',2)} ${ck('support_'+id,'=',0)}`,v('support_'+id,1)+add('support_count',1)+body+call('refresh'))} } } ai_will_do = { base = 0 } }\n`;
}).join('')+`}\n`);
const ui = [], triggers = [], clicks = [];
const visible = (id,p) => { if(p) triggers.push(`${id}_visible = { check_variable = { RUS_nat_page = ${p} } }`); };
// The native decision grid is 502px wide; keep text inside its right padding.
function text(id,x,y,width,key,p=0,height=26) { width=Math.min(width,492-x); ui.push(`instantTextBoxType = { name = "${id}" position = { x = ${x} y = ${y} } font = "hoi_16mbs" text = "${key}" maxWidth = ${width} maxHeight = ${height} fixedsize = yes alwaystransparent = yes }`); visible(id,p); }
function button(id,x,y,key,body,p=0,enabled='always = yes',sprite='GFX_button_123x34') { const tooltip=id.startsWith('nat_tab_')?key+'_tt':key; ui.push(`buttonType = { name = "${id}" position = { x = ${x} y = ${y} } quadTextureSprite = "${sprite}" buttonText = "${key}" buttonFont = "hoi_16mbs" clicksound = click_default pdx_tooltip = "${tooltip}" }`); visible(id,p); triggers.push(`${id}_click_enabled = { ${enabled} }`); clicks.push(`${id}_click = { ${body} RUS_nat_refresh = yes }`); }
function icon(id,kind,x,y,p=0){ui.push(`iconType = { name = "${id}" position = { x = ${x} y = ${y} } spriteType = "GFX_RUS_nat_${kind}" scale = 0.75 alwaystransparent = yes }`);visible(id,p);}
const iconNames=['stock','reform','orders','machinery','food','export','income','factories'];
write('interface/RUS_national_agriculture.gfx','spriteTypes = {\n'+iconNames.map(k=>`spriteType = { name = "GFX_RUS_nat_${k}" texturefile = "gfx/interface/RUS_national_agriculture/${k}.png" noOfFrames = 1 }`).join('\n')+'\n}\n');
label('RUS_nat_title','国家农业委员会','National Agriculture Board','Государственный аграрный комитет');
text('nat_title',10,8,520,'RUS_nat_title');
['农业生产','农机生产','库存与贸易','季度报告'].forEach((zh,i)=>{let key=label(n('tab_'+i),zh,['Agriculture','Machinery','Stocks & Trade','Quarterly Report'][i],['Земледелие','Техника','Торговля','Отчёт'][i]); button('nat_tab_'+i,5+i*123,38,key,v('page',i+1));});
label(n('tab_0_tt'),
 '§Y农业生产§!\\n每季配置20点，每种作物最多10点；农机承诺成功、土改成功各永久+2点，总额最多24。\\n实物产量受季节、地力疲劳、实际天气、平均农机覆盖及农业产量修正影响。预估不计隐藏天气与行情，预测不保证准确。行情、市场饱和与销售容量只影响售价。\\n确认后锁定配置，季末前可重新调整；未确认时按内需与储备自动配置。首次及截止日的不足整季时段按实际天数结算。',
 '§YAgriculture§!\\nAllocate 20 points per quarter, at most 10 per crop. Fulfilling the machinery promise and completing reform each add 2 permanently, up to 24.\\nPhysical output depends on season, soil fatigue, actual weather, average machinery coverage and agricultural output modifiers. Estimates exclude hidden weather and markets; forecasts may be wrong. Markets, saturation and sales capacity affect prices only.\\nConfirmation locks the plan until reopened. Unconfirmed plans are allocated automatically for domestic needs and reserves. Partial quarters are prorated by actual days.',
 '§YЗемледелие§!\\n20 единиц плана за квартал, не более 10 на культуру. Выполнение обещания о технике и завершение реформы дают по 2 постоянные единицы, максимум 24.\\nУрожай зависит от сезона, истощения почвы, фактической погоды, средней обеспеченности техникой и модификаторов выпуска. Оценка не учитывает скрытые погоду и рынок; прогноз может ошибаться. Рынок, насыщение и ёмкость сбыта влияют только на цену.\\nУтверждённый план можно открыть для изменения до конца квартала. Без утверждения применяется автоплан внутренних нужд и резервов. Неполный квартал рассчитывается по фактическим дням.');
label(n('tab_1_tt'),
 '§Y农机生产§!\\n实际占用所分配的可用民用工厂，日产为每厂1.20×效率×产出系数。一五当前分数与国家工厂产出、效率上限、效率增长修正参与计算。\\n新厂以30%效率并入；停产时效率每日降低0.1个百分点，最低30%。失去工厂时自动减少占用；在役与仓库均满时停止生产，不增加累计产量。\\n农机优先补齐国内在役目标400，土改成功后下一季为500，仓库上限4500。每季在役损耗随机10%/15%/20%/25%，恶劣天气再+5个百分点，最多30%；库存不参与损耗。平均覆盖率使作物产量变为90%至110%。\\n承诺要求540天内推广拖拉机3次，且从农业系统启动起累计自产3000单位；出口不扣累计成绩。',
 '§YMachinery§!\\nAssigned available civilian factories are reserved. Daily output per factory is 1.20 x efficiency x output factor. Current five-year-plan score and national factory output, efficiency cap and efficiency growth modifiers apply.\\nNew factories enter at 30% efficiency. Stopped lines lose 0.1 percentage points daily, to a 30% floor. Factory losses reduce allocation. Full domestic service and storage stop production and cumulative credit.\\nDomestic target: 400, rising to 500 next quarter after reform; warehouse cap: 4500. Quarterly in-service wear is 10/15/20/25%, plus 5 percentage points in adverse weather, capped at 30%. Stored machines do not wear. Average coverage scales crops to 90-110%.\\nThe promise requires three tractor decisions within 540 days and 3000 self-produced units since system activation. Exports do not reduce cumulative production.',
 '§YТехника§!\\nВыделенные доступные гражданские заводы резервируются. Выпуск одного завода в сутки: 1,20 x эффективность x коэффициент выпуска. Учитываются текущие очки пятилетки и государственные модификаторы выпуска, предела и роста эффективности.\\nНовые заводы начинают с 30%. При остановке эффективность снижается на 0,1 процентного пункта в сутки до 30%. Потеря заводов сокращает назначение. Заполненные парк и склад останавливают производство и накопительный счётчик.\\nЦель парка: 400, со следующего квартала после реформы 500; склад: 4500. Квартальный износ парка 10/15/20/25%, при плохой погоде ещё 5 п.п., максимум 30%. Склад не изнашивается. Среднее покрытие меняет урожай до 90-110%.\\nОбещание: три решения о тракторах за 540 дней и 3000 единиц собственного производства с запуска системы. Экспорт не уменьшает накопленный выпуск.');
label(n('tab_2_tt'),
 '§Y库存与贸易§!\\n完整季度内需：小麦与黑麦共8、甜菜2、亚麻与棉花共4；开季处于战争时粮食+2、纺织+1。\\n先满足内需，再保留选定的半季/一季/两季储备，最后按优先级交付已接订单。仅交整单，同一库存不可重复交付。作物库存上限12/12/6/6/6，季末损耗5%，卡霍夫斯卡娅任职时为2%。\\n西方同志解锁普通作物订单；巴黎条约后，存在的英法各提供作物与农机订单，从下一季生效。作物每单位基价1000经济盈余，农机150；英法已交付订单售价倍率+0.10，最终售价倍率0.40至1.50。农机出口先补国内缺口并留下目标25%的备件。',
 '§YStocks and Trade§!\\nFull-quarter needs: wheat and rye combined 8, beet 2, flax and cotton combined 4. War at quarter start adds 2 food and 1 fibre.\\nDomestic needs come first, then selected half/one/two-quarter reserves, then accepted orders by priority. Whole orders only; stock cannot be reused. Crop caps are 12/12/6/6/6. End-quarter spoilage is 5%, or 2% with Kakhovskaya.\\nWestern Comrades unlocks an ordinary crop order. After the Paris treaty, existing Britain and France each supply crop and machinery orders from the next quarter. Base surplus per unit: crops 1000, machinery 150. Delivered British/French orders add 0.10 to price; final price multiplier 0.40-1.50. Machinery exports require domestic replenishment and spare reserves of 25% of target.',
 '§YЗапасы и торговля§!\\nПотребности полного квартала: пшеница и рожь вместе 8, свёкла 2, лён и хлопок вместе 4. Война на начало квартала добавляет 2 продовольствия и 1 волокна.\\nСначала внутренние нужды, затем выбранный резерв на половину/один/два квартала, затем принятые заказы по приоритету. Только полные заказы, без повторного расходования запасов. Пределы культур: 12/12/6/6/6. Потери запасов 5%, с Каховской 2%.\\nЗападные товарищи открывают обычный заказ. После Парижского договора существующие Британия и Франция дают заказы культур и техники со следующего квартала. Базовый экономический профицит за единицу: культуры 1000, техника 150. Выполненные англо-французские заказы дают +0,10 к цене; итоговый множитель 0,40-1,50. Перед экспортом техники восполняется парк и резервируется 25% целевого парка.');
label(n('tab_3_tt'),
 '§Y季度报告§!\\n内需积分：粮食全部满足+2，满足90%至不足100%时+1；甜菜、纺织全部满足各+0.5。此项每季最多3分，每农业年度最多12分。三类内需全部满足额外+50政治点，每年最多200。\\n另外：一季粮食储备+2分、平均农机覆盖至少90%+2分、季度任务+4分；乌斯季诺夫任职时完成任务再+1。仅正式土改进行中或成功后发分；不足整季按实际天数折算。\\n乌斯季诺夫路线目标150分、720天。成功后超额分数成为可消费余额，不降低改革阶段；失败后停止积分与兑换，农业继续运转。出口没有额外土改积分。\\n年度精神依据内需平均满足率与年末储备评定。粮食短缺导致逐级惩罚，恢复供给一季降低一级；甜菜或纺织短缺影响工厂产出。',
 '§YQuarterly Report§!\\nDomestic points: all food +2, or 90% to below 100% +1; all beet and all fibre +0.5 each. This component is capped at 3 per quarter and 12 per agricultural year. Meeting all three needs also grants 50 political power, capped at 200 per year.\\nAdditional points: one-quarter food reserves +2; average machinery coverage at least 90% +2; quarterly task +4, plus 1 with Ustinov. Points require ongoing or successful formal reform. Partial quarters are prorated.\\nUstinov reform: 150 points in 720 days. After success, excess points form a spendable balance without lowering stages. Failure stops points and exchanges, not farming. Exports grant no additional reform points.\\nAnnual spirits use average domestic supply and year-end reserves. Food shortages build penalties, recovering one level per supplied quarter. Beet or fibre shortages reduce factory output.',
 '§YКвартальный отчёт§!\\nОчки снабжения: всё продовольствие +2, при 90% и менее 100% +1; полная свёкла и волокно по +0,5. Только эта часть ограничена 3 очками за квартал и 12 за сельскохозяйственный год. Все три потребности дают ещё 50 политвласти, максимум 200 за год.\\nДополнительно: квартальный запас зерна +2; среднее покрытие техникой от 90% +2; задание +4 и ещё 1 с Устиновым. Очки выдаются только при действующей или успешной официальной реформе. Неполные кварталы пропорциональны дням.\\nРеформа Устинова: 150 очков за 720 дней. После успеха излишек становится расходуемым балансом без снижения этапа. Провал останавливает очки и обмен, но не производство. Экспорт не даёт очков реформы.\\nГодовые духи зависят от среднего снабжения и резервов на конец года. Нехватка продовольствия накапливает штрафы, полное снабжение снимает один уровень за квартал. Нехватка свёклы или волокна снижает выпуск заводов.');
text('nat_header',10,76,520,label(n('header'),'第[?RUS_nat_season|0]季  剩余[?RUS_nat_remaining|0]天  配置[?RUS_nat_allocated|0]/[?RUS_nat_budget|0]','Season [?RUS_nat_season|0]  [?RUS_nat_remaining|0] days  Allocation [?RUS_nat_allocated|0]/[?RUS_nat_budget|0]','Сезон [?RUS_nat_season|0]  Дней: [?RUS_nat_remaining|0]  План: [?RUS_nat_allocated|0]/[?RUS_nat_budget|0]'));
icon('nat_reform_icon','reform',8,100);
text('nat_score',38,102,492,label(n('score_line'),'土改：[?RUS_agri_display_score|1]/150  可用：[?RUS_agri_spendable_score|1]  上季：+[?RUS_agri_last_quarter_score|1]','Reform: [?RUS_agri_display_score|1]/150  Available: [?RUS_agri_spendable_score|1]  Last: +[?RUS_agri_last_quarter_score|1]','Реформа: [?RUS_agri_display_score|1]/150  Доступно: [?RUS_agri_spendable_score|1]  Прирост: +[?RUS_agri_last_quarter_score|1]'));
text('nat_weather',10,134,520,label(n('weather'),'天气预测：[GetRUSNatWeather]    [GetRUSNatPlan]','Weather outlook: [GetRUSNatWeather]    [GetRUSNatPlan]','Прогноз погоды: [GetRUSNatWeather]    [GetRUSNatPlan]'),1);
crops.forEach((c,i)=>{
 const y=173+i*50;
 ui.push(`iconType = { name = "nat_${c}_icon" position = { x = 10 y = ${y} } spriteType = "GFX_RUS_agri_crop_${c}" scale = 0.5 alwaystransparent = yes }`);visible('nat_'+c+'_icon',1);
 text('nat_'+c+'_name',50,y,80,a(c),1);
 button('nat_'+c+'_minus',136,y,'',`RUS_agri_decrease_${c} = yes`,1,`NOT = { has_country_flag = RUS_agri_allocation_locked } check_variable = { ${a(c+'_investment')} > 0 }`,'GFX_naval_decrease_amount');
 text('nat_'+c+'_amount',168,y,35,label(n(c+'_amount'),`[?${a(c+'_investment')}|0]`,`[?${a(c+'_investment')}|0]`,`[?${a(c+'_investment')}|0]`),1);
 button('nat_'+c+'_plus',201,y,'',`RUS_agri_increase_${c} = yes`,1,`NOT = { has_country_flag = RUS_agri_allocation_locked } check_variable = { ${a(c+'_investment')} < 10 } ${ck('allocated','<',n('budget'))}`,'GFX_naval_increase_amount');
 text('nat_'+c+'_info',239,y,290,label(n(c+'_info'),`预计产量 [?${n(c+'_yield')}|1]  [GetRUSNat${c}Market]`,`Yield [?${n(c+'_yield')}|1]  [GetRUSNat${c}Market]`,`Урожай [?${n(c+'_yield')}|1]  [GetRUSNat${c}Market]`),1,20);
 text('nat_'+c+'_soil',239,y+22,290,label(n(c+'_soil'),`地力疲劳 [?${a(c+'_fatigue')}|0]  容量 [?${a(c+'_capacity')}|0] [GetRUSNat${c}Saturation]`,`Fatigue [?${a(c+'_fatigue')}|0]  Capacity [?${a(c+'_capacity')}|0] [GetRUSNat${c}Saturation]`,`Истощ. [?${a(c+'_fatigue')}|0]  Сбыт [?${a(c+'_capacity')}|0] [GetRUSNat${c}Saturation]`),1,20);
});
icon('nat_food_icon','food',8,428,1);
text('nat_needs',38,430,492,label(n('needs'),'预计满足：粮食[?RUS_nat_food_preview|0]% 加工[?RUS_nat_beet_preview|0]% 纺织[?RUS_nat_textile_preview|0]%','Supply: Food [?RUS_nat_food_preview|0]% Processing [?RUS_nat_beet_preview|0]% Textiles [?RUS_nat_textile_preview|0]%','Снабжение: зерно [?RUS_nat_food_preview|0]% свёкла [?RUS_nat_beet_preview|0]% волокно [?RUS_nat_textile_preview|0]%'),1);
text('nat_task',10,459,520,label(n('task_line'),'季度任务：[GetRUSNatTask]','Quarterly task: [GetRUSNatTask]','Задание: [GetRUSNatTask]'),1);
text('nat_next',10,487,520,label(n('next_line'),'下季投入：[GetRUSNatNext]','Next quarter: [GetRUSNatNext]','Следующий квартал: [GetRUSNatNext]'),1);
button('nat_auto',5,526,label(n('auto'),'自动配置','Auto Allocate','Автоплан'),call('auto_allocate'),1,'NOT = { has_country_flag = RUS_agri_allocation_locked }');
button('nat_clear',128,526,'RUS_agri_clear','RUS_agri_clear_allocation = yes',1,'NOT = { has_country_flag = RUS_agri_allocation_locked }');
button('nat_confirm',251,526,'RUS_agri_confirm','RUS_agri_confirm_allocation = yes',1,'NOT = { has_country_flag = RUS_agri_allocation_locked }');
button('nat_reopen',374,526,'RUS_agri_reopen','RUS_agri_reopen_allocation = yes',1,'has_country_flag = RUS_agri_allocation_locked');
text('nat_gaps',10,574,520,label(n('gaps'),'本季缺口：粮食[?RUS_nat_food_gap|1] 加工[?RUS_nat_beet_gap|1] 纺织[?RUS_nat_textile_gap|1]','Deficit: Food [?RUS_nat_food_gap|1] Beet [?RUS_nat_beet_gap|1] Fibre [?RUS_nat_textile_gap|1]','Дефицит: зерно [?RUS_nat_food_gap|1] свёкла [?RUS_nat_beet_gap|1] волокно [?RUS_nat_textile_gap|1]'),1);
const machineRows=[
 ['分配民工：[?RUS_nat_factories|0]  可增派：[?RUS_nat_available|0]','Assigned factories: [?RUS_nat_factories|0]  Available: [?RUS_nat_available|0]','Заводов: [?RUS_nat_factories|0]  Доступно: [?RUS_nat_available|0]'],
 ['日产：[?RUS_nat_daily|2]  累计自产：[?RUS_nat_produced|1]','Daily output: [?RUS_nat_daily|2]  Total produced: [?RUS_nat_produced|1]','В сутки: [?RUS_nat_daily|2]  Произведено: [?RUS_nat_produced|1]'],
 ['效率：[?RUS_nat_eff_display|1]% / [?RUS_nat_cap_display|1]%','Efficiency: [?RUS_nat_eff_display|1]% / [?RUS_nat_cap_display|1]%','Эффективность: [?RUS_nat_eff_display|1]% / [?RUS_nat_cap_display|1]%'],
 ['产出系数：[?RUS_nat_output|2]  增长系数：[?RUS_nat_growth|2]','Output factor: [?RUS_nat_output|2]  Growth factor: [?RUS_nat_growth|2]','Выпуск: x[?RUS_nat_output|2]  Рост: x[?RUS_nat_growth|2]'],
 ['在役：[?RUS_nat_installed|1]/[?RUS_nat_target|0]  库存：[?RUS_nat_machine_stock|1]/4500','In service: [?RUS_nat_installed|1]/[?RUS_nat_target|0]  Stock: [?RUS_nat_machine_stock|1]/4500','В строю: [?RUS_nat_installed|1]/[?RUS_nat_target|0]  Склад: [?RUS_nat_machine_stock|1]/4500'],
 ['拖拉机承诺：推广[?RUS_max_landreform_tractor_promise_count|0]/3次；自产[?RUS_nat_produced|0]/3000','Promise: decisions [?RUS_max_landreform_tractor_promise_count|0]/3; output [?RUS_nat_produced|0]/3000','Обещание: решения [?RUS_max_landreform_tractor_promise_count|0]/3; выпуск [?RUS_nat_produced|0]/3000'],
 ['机械行情预测：[GetRUSNatMachineryMarket]','Machinery market: [GetRUSNatMachineryMarket]','Рынок техники: [GetRUSNatMachineryMarket]']
];
machineRows.forEach((l,i)=>{const kind={0:'factories',1:'machinery',4:'stock'}[i];if(kind)icon('nat_machine_icon_'+i,kind,8,143+i*46,2);text('nat_machine_'+i,kind?38:10,145+i*46,kind?492:520,label(n('machine_'+i),...l),2);});
text('nat_promise_state',10,397,520,label(n('promise_state'),'[GetRUSNatPromise]','[GetRUSNatPromise]','[GetRUSNatPromise]'),2,20);
text('nat_machine_coverage',10,452,520,label(n('machine_coverage'),'本季平均覆盖率：[?RUS_nat_coverage_display|1]%','Average machinery coverage: [?RUS_nat_coverage_display|1]%','Средняя обеспеченность техникой: [?RUS_nat_coverage_display|1]%'),2);
[-10,-1,1,10].forEach((delta,i)=>button('nat_factory_'+i,5+i*123,492,label(n('factory_'+i),`${delta>0?'+':''}${delta} 民工`,`${delta>0?'+':''}${delta} factories`,`${delta>0?'+':''}${delta} зав.`),v('requested',n('factories'))+add('requested',delta)+call('set_factories'),2,delta>0?ck('available','>',0):ck('factories','>',0)));
button('nat_stop',10,533,label(n('stop'),'停产','Stop','Остановить'),v('requested',0)+call('set_factories'),2);
button('nat_max',270,533,label(n('max'),'全部可用民工','All Available','Все доступные'),v('requested',n('factories'))+add('requested',n('available'))+call('set_factories'),2);
crops.forEach((c,i)=>text('nat_stock_'+c,10,141+i*26,190,label(n('stock_'+c),`$${a(c)}$：[?${n(c+'_stock')}|1]/${i<2?12:6}`,`$${a(c)}$: [?${n(c+'_stock')}|1]/${i<2?12:6}`,`$${a(c)}$: [?${n(c+'_stock')}|1]/${i<2?12:6}`),3));
groups.forEach(([g],i)=>text('nat_supply_'+g,208,141+i*38,320,label(n('supply_'+g),`${['粮食','加工','纺织'][i]}预计供给 [?${n(g+'_delivered')}|1]/[?${n(g+'_need')}|1]`,`${['Food','Beet','Fibre'][i]} supply [?${n(g+'_delivered')}|1]/[?${n(g+'_need')}|1]`,`${['Зерно','Свёкла','Волокно'][i]} [?${n(g+'_delivered')}|1]/[?${n(g+'_need')}|1]`),3));
icon('nat_export_icon','export',8,276,3);
text('nat_reserve',38,278,492,label(n('reserve_line'),'储备目标：[?RUS_nat_reserve|1]季  预计出口：[?RUS_nat_preview_income|0]','Reserve: [?RUS_nat_reserve|1] quarters  Expected exports: [?RUS_nat_preview_income|0]','Резерв: [?RUS_nat_reserve|1] кварт.  Экспорт: [?RUS_nat_preview_income|0]'),3);
[.5,1,2].forEach((q,i)=>button('nat_reserve_'+i,10+i*165,307,label(n('reserve_'+i),`${q}季储备`,`${q} quarter reserve`,`Резерв: ${q} кв.`),v('reserve',q),3));
['generic','fra','eng'].forEach((o,i)=>{
 icon('nat_order_icon_'+o,'orders',8,350+i*43,3);
 text('nat_order_'+o,38,352+i*43,322,label(n('order_'+o),`${['一般','法国','英国'][i]}：[GetRUSNatOrder${o}] [?${n(o+'_quantity')}|0]  [GetRUSNatAccept${o}]`,`${['General','France','Britain'][i]}: [GetRUSNatOrder${o}] [?${n(o+'_quantity')}|0] [GetRUSNatAccept${o}]`,`${['Общий','Франция','Британия'][i]}: [GetRUSNatOrder${o}] [?${n(o+'_quantity')}|0] [GetRUSNatAccept${o}]`),3,20);
 text('nat_order_rank_'+o,38,372+i*43,348,label(n('order_rank_'+o),`优先级 [?${n(o+'_priority')}|0]`,`Priority [?${n(o+'_priority')}|0]`,`Приоритет [?${n(o+'_priority')}|0]`),3,18);
 button('nat_accept_'+o,369,349+i*43,label(n('toggle'),'接单/取消','Accept/Cancel','Заказ/Отмена'),iff(ck(o+'_accept','=',1),v(o+'_accept',0),v(o+'_accept',1)),3,ck(o+'_quantity','>',0));
});
['fra','eng'].forEach((o,i)=>{text('nat_morder_'+o,10,490+i*40,350,label(n('morder_'+o),`${i?'英国':'法国'}农机：[?${n(o+'_machine_quantity')}|0]  [GetRUSNatMachineAccept${o}]`,`${i?'British':'French'} machinery: [?${n(o+'_machine_quantity')}|0] [GetRUSNatMachineAccept${o}]`,`${i?'Британия':'Франция'}, техника: [?${n(o+'_machine_quantity')}|0] [GetRUSNatMachineAccept${o}]`),3);button('nat_maccept_'+o,369,487+i*40,n('toggle'),iff(ck(o+'_machine_accept','=',1),v(o+'_machine_accept',0),v(o+'_machine_accept',1)),3,ck(o+'_machine_quantity','>',0));});
button('nat_priority',10,570,label(n('priority'),'订单顺序轮换','Rotate Priority','Порядок заказов'),['generic','fra','eng'].map(o=>add(o+'_priority',1)+iff(ck(o+'_priority','>',3),v(o+'_priority',1))).join(''),3);
icon('nat_income_icon','income',8,141,4);
text('nat_report_head',38,143,492,label(n('report_head'),'上季：第[?RUS_nat_last_season|0]季  出口：[?RUS_nat_last_income|0]  农机损耗：[?RUS_nat_last_loss|1]','Season: [?RUS_nat_last_season|0]  Exports: [?RUS_nat_last_income|0]  Machinery lost: [?RUS_nat_last_loss|1]','Сезон: [?RUS_nat_last_season|0]  Экспорт: [?RUS_nat_last_income|0]  Износ: [?RUS_nat_last_loss|1]'),4);
text('nat_report_weather',10,180,520,label(n('report_weather'),'实际天气：[?RUS_nat_last_weather|2]  农机行情：[?RUS_nat_last_machine_market|2]','Actual weather: [?RUS_nat_last_weather|2]  Machinery market: [?RUS_nat_last_machine_market|2]','Погода: [?RUS_nat_last_weather|2]  Рынок техники: [?RUS_nat_last_machine_market|2]'),4);
crops.forEach((c,i)=>text('nat_report_'+c,10,221+i*38,520,label(n('report_'+c),`$${a(c)}$：产量 [?${n(c+'_last_yield')}|1]，实际行情 [?${n(c+'_last_market')}|2]`,`$${a(c)}$: yield [?${n(c+'_last_yield')}|1], actual market [?${n(c+'_last_market')}|2]`,`$${a(c)}$: урожай [?${n(c+'_last_yield')}|1], рынок [?${n(c+'_last_market')}|2]`),4));
text('nat_report_supply',10,427,520,label(n('report_supply'),'供给：粮[?RUS_nat_food_last_ratio|0]% 糖[?RUS_nat_beet_last_ratio|0]% 纺[?RUS_nat_textile_last_ratio|0]%','Supply: Food [?RUS_nat_food_last_ratio|0]% Beet [?RUS_nat_beet_last_ratio|0]% Fibre [?RUS_nat_textile_last_ratio|0]%','Снабжение: зерно [?RUS_nat_food_last_ratio|0]% свёкла [?RUS_nat_beet_last_ratio|0]% волокно [?RUS_nat_textile_last_ratio|0]%'),4);
text('nat_report_shortage',10,469,520,label(n('report_shortage'),'粮食短缺等级：[?RUS_nat_shortage|0]  上年平均供给：[?RUS_nat_last_annual|0]%','Food shortage level: [?RUS_nat_shortage|0]  Last year: [?RUS_nat_last_annual|0]%','Нехватка продовольствия: [?RUS_nat_shortage|0]  Прошлый год: [?RUS_nat_last_annual|0]%'),4);
text('nat_report_pp',10,510,520,label(n('report_pp'),'上季政治点：+[?RUS_nat_last_pp|1]  本年内需积分：[?RUS_nat_domestic_year|1]/12','Last political power: +[?RUS_nat_last_pp|1]  Annual supply points: [?RUS_nat_domestic_year|1]/12','Политвласть: +[?RUS_nat_last_pp|1]  Очки снабжения: [?RUS_nat_domestic_year|1]/12'),4);
text('nat_report_orders',10,552,520,label(n('report_orders'),'已交付：农产品[?RUS_nat_last_crop_orders|0]单，农机[?RUS_nat_last_machine_orders|0]单','Delivered: [?RUS_nat_last_crop_orders|0] crop orders, [?RUS_nat_last_machine_orders|0] machinery orders','Поставлено: [?RUS_nat_last_crop_orders|0] заказов культур, [?RUS_nat_last_machine_orders|0] заказов техники'),4);
for(let i=0;i<triggers.length;i++)if(/^nat_(report_|income_icon)/.test(triggers[i]))triggers[i]=triggers[i].replace('= {','= { has_country_flag = RUS_nat_has_report');
text('nat_empty_report',10,145,520,label(n('empty_report'),'尚无已结算的季度报告。','No quarter has been settled yet.','Завершённых квартальных отчётов пока нет.'));
triggers.push('nat_empty_report_visible = { check_variable = { RUS_nat_page = 4 } NOT = { has_country_flag = RUS_nat_has_report } }');
write('interface/RUS_national_agriculture.gui',`guiTypes = { containerWindowType = { name = "RUS_national_agriculture_window" position = { x = 0 y = 0 } size = { width = 100% height = 625 } clipping = yes\n${ui.join('\n')}\n} }\n`);
write('common/scripted_guis/RUS_national_agriculture.txt',`scripted_gui = { RUS_national_agriculture_gui = { context_type = decision_category window_name = "RUS_national_agriculture_window" dirty = global.RUS_agri_management_update ai_enabled = { always = no } visible = { ${mode} } triggers = { ${triggers.join('\n')} } effects = { ${clicks.join('\n')} } } }\n`);
const sl=[];
function scripted(name,entries,fallback){sl.push(`defined_text = { name = ${name}\n${entries.map(([trigger,key])=>`text = { trigger = { ${trigger} } localization_key = ${key} }`).join('\n')}\ntext = { localization_key = ${fallback} } }`);}
label(n('strong'),'偏强','Strong','Рост');label(n('stable'),'平稳','Stable','Стабильно');label(n('weak'),'偏弱','Weak','Спад');label(n('none'),'无','None','Нет');label(n('accepted'),'已接单','Accepted','Принят');label(n('cancelled'),'未接单','Declined','Отклонён');label(n('delivered'),'已交付','Delivered','Поставлен');
label(n('plan_locked'),'方案已确认','Plan confirmed','План утверждён');label(n('plan_open'),'方案待确认','Plan unconfirmed','План не утверждён');
scripted('GetRUSNatPlan',[[flag('RUS_agri_allocation_locked'),n('plan_locked')]],n('plan_open'));
label(n('saturation'),'饱和','Saturated','Избыток');label(n('no_saturation'),'','','');
crops.forEach(c=>scripted(`GetRUSNat${c}Saturation`,[[flag('RUS_agri_saturation_'+c),n('saturation')]],n('no_saturation')));
label(n('weather_good'),'有利','Favourable','Благоприятно');label(n('weather_normal'),'平常','Normal','Обычно');label(n('weather_bad'),'不利','Adverse','Неблагоприятно');
scripted('GetRUSNatWeather',[[`check_variable = { RUS_agri_weather_forecast > 0 }`,n('weather_good')],[`check_variable = { RUS_agri_weather_forecast < 0 }`,n('weather_bad')]],n('weather_normal'));
label(n('next_machines'),'追加农机调度','Machinery coordination','Координация техники');label(n('next_storage'),'改善仓储运输','Storage and transport','Хранение и перевозки');
scripted('GetRUSNatNext',[[flag('RUS_agri_next_machinery'),n('next_machines')],[flag('RUS_agri_next_storage'),n('next_storage')]],n('none'));
label(n('promise_pending'),'承诺履行中','Promise in progress','Обещание выполняется');label(n('promise_kept'),'承诺已履行','Promise fulfilled','Обещание выполнено');label(n('promise_failed'),'承诺未兑现','Promise failed','Обещание не выполнено');label(n('promise_none'),'尚未作出农机生产承诺','No machinery promise made','Обещание о производстве техники не дано');
scripted('GetRUSNatPromise',[[flag('RUS_max_landreform_tractor_promise_kept'),n('promise_kept')],[flag('RUS_max_landreform_tractor_promise_failed'),n('promise_failed')],[flag('RUS_max_landreform_tractor_promise_active'),n('promise_pending')]],n('promise_none'));
crops.forEach(c=>scripted(`GetRUSNat${c}Market`,[[`check_variable = { ${a(c+'_forecast')} > 0 }`,n('strong')],[`check_variable = { ${a(c+'_forecast')} < 0 }`,n('weak')]],n('stable')));
scripted('GetRUSNatMachineryMarket',[[ck('machine_forecast','>',0),n('strong')],[ck('machine_forecast','<',0),n('weak')]],n('stable'));
['generic','fra','eng'].forEach(o=>{scripted('GetRUSNatOrder'+o,crops.map((c,i)=>[ck(o+'_crop','=',i+1),a(c)]),n('none'));scripted('GetRUSNatAccept'+o,[[ck(o+'_shipped','=',1),n('delivered')],[ck(o+'_accept','=',1),n('accepted')]],n('cancelled'));});
['fra','eng'].forEach(o=>scripted('GetRUSNatMachineAccept'+o,[[ck(o+'_machine_shipped','=',1),n('delivered')],[ck(o+'_machine_accept','=',1),n('accepted')]],n('cancelled')));
label(n('task_1'),'全部内需达标','Meet all domestic needs','Обеспечить все потребности');label(n('task_2'),'三类储备达到一季','One-quarter reserves in all categories','Квартальный запас всех категорий');label(n('task_3'),'四种作物各配置至少3点','Allocate 3+ to at least four crops','Выделить по 3 ед. четырём культурам');
scripted('GetRUSNatTask',[[ck('task','=',1),n('task_1')],[ck('task','=',2),n('task_2')]],n('task_3'));
label(n('target150'),'150','150','150');label(n('target100'),'100','100','100');
label(n('days540'),'540','540','540');label(n('days270'),'270','270','270');
scripted('GetRUSNatTarget',[[mode,n('target150')]],n('target100'));
scripted('GetRUSNatTractorDays',[[mode,n('days540')]],n('days270'));
label(n('tractor_requirement'),'\\n还须累计自产农机§Y3000§!单位（当前[?RUS_nat_produced|0]）。','\\nAlso produce §Y3000§! machinery units in total (currently [?RUS_nat_produced|0]).','\\nТакже произвести §Y3000§! ед. техники (сейчас [?RUS_nat_produced|0]).');
label(n('empty'),'','','');scripted('GetRUSNatTractorRequirement',[[mode,n('tractor_requirement')]],n('empty'));
label(n('unlock_tt'),'解锁§Y国家农业系统§!。\\n最高纲领派将开始更加“§4大刀阔斧§!”的改革，请确保您有足够的§R时间与精力§!！！！','Unlock the §YNational Agriculture System§!.\\nThe Maximalists will begin even more §4sweeping§! reforms. Make sure you have enough §Rtime and energy§!!!!','Открывает §Yгосударственную систему сельского хозяйства§!.\\nМаксималисты начнут ещё более §4решительные§! реформы. Убедитесь, что у вас достаточно §Rвремени и сил§!!!!');
label(n('reform_goal_tt'),'土地改革分数：[?RUS_maximalist_land_reform_score|1]/[GetRUSNatTarget]','Land reform score: [?RUS_maximalist_land_reform_score|1]/[GetRUSNatTarget]','Очки земельной реформы: [?RUS_maximalist_land_reform_score|1]/[GetRUSNatTarget]');
label(n('tractor_goal_tt'),'完成3次推广拖拉机（当前[?RUS_max_landreform_tractor_promise_count|0]次）。[GetRUSNatTractorRequirement]','Promote tractors three times (currently [?RUS_max_landreform_tractor_promise_count|0]).[GetRUSNatTractorRequirement]','Трижды распространить тракторы (сейчас [?RUS_max_landreform_tractor_promise_count|0]).[GetRUSNatTractorRequirement]');
['simp_chinese','english','russian'].forEach(lang=>{
 const source=fs.readFileSync(path.join(root,`localisation/${lang}/RUS_stalin_maximalist_land_reform_l_${lang}.yml`),'utf8');
 const keys=['RUS_maximalist_land_reform_category_desc','RUS_maximalist_land_reform_mission_desc','RUS_maximalist_land_reform_score_status_tt','RUS_maximalist_land_reform_next_stage_100','RUS_max_landreform_tractor_promise_mission_desc','rus_maximalist_land_reform_events.11.c.tt'];
 const lines=source.split(/\r?\n/).filter(line=>keys.some(key=>line.trimStart().startsWith(key+':'))).map(line=>line.replace(/\b100\b/g,'[GetRUSNatTarget]').replace(/\b270\b/g,'[GetRUSNatTractorDays]').replace(/"\s*$/,line.includes('tractor_promise_mission_desc')||line.includes('11.c.tt')?'[GetRUSNatTractorRequirement]"':'"'));
 if(lines.length!==keys.length)throw Error('Missing reform localization in '+lang);
 write(`localisation/replace/RUS_national_agriculture_reform_l_${lang}.yml`,`l_${lang}:\n`+lines.join('\n')+'\n',true);
});
write('common/scripted_localisation/RUS_national_agriculture_loc.txt',sl.join('\n'));
label('RUS_nat_industry','全国农业供给与农机生产','National Agriculture and Machinery','Снабжение и сельхозмашиностроение');
label('RUS_national_agriculture.1.t','国家农业年度报告','Annual Agricultural Report','Годовой сельскохозяйственный отчёт');
label('RUS_national_agriculture.1.d','农业委员会已完成本年度供给评估。平均内需满足率为[?RUS_nat_last_annual|1]%。新一年的农业生产现已开始。','The Agriculture Board has completed its annual assessment. Average domestic supply reached [?RUS_nat_last_annual|1]%. The new agricultural year has begun.','Аграрный комитет завершил годовую оценку. Внутренние потребности удовлетворены на [?RUS_nat_last_annual|1]%. Начался новый сельскохозяйственный год.');
label('RUS_national_agriculture.1.a','继续建设社会主义农业。','Continue building socialist agriculture.','Продолжим строительство социалистического сельского хозяйства.');
const overrides={
 RUS_agricultural_quarterly_management_category:['国家农业系统','National Agriculture','Государственное сельское хозяйство'],
 RUS_agricultural_quarterly_management_category_desc:['从田间的耕作与仓库的储备，到农业机械的生产与对外贸易，农业委员会统筹着共和国的粮食安全与农村重建。','From cultivation and reserves to machinery and foreign trade, the Agriculture Board coordinates the republic\'s food security and rural reconstruction.','Аграрный комитет координирует продовольственную безопасность и восстановление села: от посевов и запасов до производства техники и внешней торговли.'],
 RUS_agri_export_orders_unlock_tt:['解锁§Y英法季度订单§!：存在的英法各增加1份农产品订单与1份农机订单，从下一季生效。已交付订单售价倍率§G+0.10§!。','Unlock §YBritish and French quarterly orders§!: each existing country provides one crop and one machinery order from the next quarter. Delivered orders gain §G+0.10§! to their price multiplier.','Открывает §Yквартальные заказы Британии и Франции§!: каждая существующая страна даёт заказ культур и техники со следующего квартала. Множитель цены выполненных заказов §G+0.10§!.'],
 RUS_agri_annual_shortfall_desc:['上一农业年度的国内供给未能达到安全水平，国家必须调拨更多资源填补缺口。','Domestic supply fell below safe levels in the previous agricultural year, requiring additional state resources.','В прошлом сельскохозяйственном году внутреннее снабжение упало ниже безопасного уровня и требует дополнительных ресурсов.'],
};
['simp_chinese','english','russian'].forEach((lang,i)=>{
 const source=fs.readFileSync(path.join(root,`localisation/${lang}/RUS_future_foreign_policy_mechanics_l_${lang}.yml`),'utf8');
 const old=source.match(/^\s*RUS_future_foreign_002_effect_tt:(?:0)?\s*"(.*)"$/m);if(!old)throw Error('Missing western comrades tooltip');
 const extra=['\\n每季增加1份普通农产品订单，从下一季生效。','\\nOne ordinary crop order each quarter, starting next quarter.','\\nОдин обычный заказ культур каждый квартал, начиная со следующего.'][i];
 write(`localisation/replace/RUS_national_agriculture_ui_l_${lang}.yml`,`l_${lang}:\n`+Object.entries(overrides).map(([k,t])=>` ${k}:0 "${t[i]}"`).join('\n')+`\n RUS_future_foreign_002_effect_tt:0 "${old[1]}${extra}"\n`,true);
});
write('events/RUS_national_agriculture_events.txt','add_namespace = RUS_national_agriculture\ncountry_event = { id = RUS_national_agriculture.1 title = RUS_national_agriculture.1.t desc = RUS_national_agriculture.1.d picture = GFX_report_event_RUS_ustinov is_triggered_only = yes option = { name = RUS_national_agriculture.1.a } }\n');
['simp_chinese','english','russian'].forEach((language,i)=>write(`localisation/${language}/RUS_national_agriculture_l_${language}.yml`,`l_${language}:\n`+Object.entries(loc).map(([key,values])=>` ${key}:0 "${values[i]}"`).join('\n')+'\n',true));
console.log('Generated national agriculture scripts, four-page GUI and three locales.');
