const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {parse,get,effects,triggers,country,check,exec,read,root} = require('./test_agri_development.cjs');
const crops=['wheat','rye','beet','flax','cotton'];
const run=(c,key)=>exec(effects.get('RUS_nat_'+key),c);
const set=(c,k,v)=>c.vars['RUS_nat_'+k]=v;
const val=(c,k)=>c.vars['RUS_nat_'+k]||0;
const day=(c)=>{c.vars['global.num_days']++;run(c,'daily');};
const fresh=(doy=59, factories=0)=>{
 const c=country(); c.vars['global.num_days']=706640+doy;c.civCapacity=100;c.vars.num_of_civilian_factories_available_for_projects=100;c.flags.RUS_first_five_year_plan_mission_started=true;
 run(c,'enable');if(factories){set(c,'requested',factories);run(c,'set_factories');}return c;
};
let count=0;
const test=(name,f)=>{f();count++;console.log('PASS '+name);};
test('calendar is anchored to all 365 game days, including partial winter',()=>{
 for(let d=0;d<365;d++){
  const c=fresh(d);const s=d<59||d>=334?4:d<151?1:d<243?2:3;
  assert.equal(val(c,'season'),s);assert.ok(val(c,'remaining')>0);assert.ok(val(c,'remaining')<=92);
  assert.equal(c.events.length,0);
 }
});
test('enabling twice cannot duplicate starting stocks or reset factory production',()=>{
 const c=fresh();set(c,'produced',40);set(c,'wheat_stock',1);run(c,'enable');assert.equal(val(c,'produced'),40);assert.equal(val(c,'wheat_stock'),1);
});
test('unlimited available factory allocation, dilution, releasing, loss and no same-day double production',()=>{
 const c=fresh(59,20);assert.equal(val(c,'factories'),20);set(c,'efficiency',6000);set(c,'requested',40);run(c,'set_factories');assert.equal(val(c,'efficiency'),4500);
 set(c,'requested',20);run(c,'set_factories');assert.equal(val(c,'efficiency'),4500);set(c,'requested',1000);run(c,'set_factories');assert.equal(val(c,'factories'),100);
 c.civCapacity=5;c.vars.num_of_civilian_factories_available_for_projects=-95;day(c);assert.equal(val(c,'factories'),5);
 const produced=val(c,'produced');run(c,'daily');assert.equal(val(c,'produced'),produced);
 set(c,'requested',0);run(c,'set_factories');day(c);assert.equal(val(c,'daily'),0);
});
test('current five-year score and engine modifiers drive output in both directions',()=>{
 const c=fresh(59,3);c.vars.RUS_first_five_year_plan_score=150;run(c,'parameters');const high=val(c,'daily');c.vars.RUS_first_five_year_plan_score=0;run(c,'parameters');assert.ok(val(c,'daily')<high);
 c.vars['modifier@industrial_capacity_factory']=.2;c.vars['modifier@production_factory_max_efficiency_factor']=.2;c.vars['modifier@production_factory_efficiency_gain_factor']=.1;run(c,'parameters');assert.equal(val(c,'cap'),7500);assert.equal(val(c,'output'),1.1);assert.equal(val(c,'growth'),1.05);
});
test('hidden markets and weather never change previews or redraw on refresh',()=>{
 const c=fresh(243);c.vars.RUS_agri_wheat_investment=8;run(c,'refresh');const y=val(c,'wheat_yield'),money=val(c,'preview_income'),seed=c.seed;
 c.vars.RUS_agri_weather=-.4;c.vars.RUS_agri_wheat_market=.4;run(c,'refresh');assert.equal(val(c,'wheat_yield'),y);assert.equal(val(c,'preview_income'),money);assert.equal(c.seed,seed);
});
test('market prices cannot change physical harvest',()=>{
 const c=fresh();c.vars.RUS_agri_wheat_investment=10;set(c,'fraction',1);set(c,'actual',1);run(c,'yield');const y=val(c,'wheat_yield');c.vars.RUS_agri_wheat_market=-.4;run(c,'yield');assert.equal(val(c,'wheat_yield'),y);
});
test('allocation stays bounded, public automation handles a partial quarter without reading outcomes',()=>{
 const c=fresh(269);run(c,'auto_allocate');assert.equal(val(c,'allocated'),20);for(const crop of crops)assert.ok(c.vars['RUS_agri_'+crop+'_investment']<=10);
 const allocations=crops.map(x=>c.vars['RUS_agri_'+x+'_investment']);c.vars.RUS_agri_weather=.4;for(const crop of crops)c.vars['RUS_agri_'+crop+'_market']=.4;run(c,'auto_allocate');assert.deepEqual(crops.map(x=>c.vars['RUS_agri_'+x+'_investment']),allocations);
});
test('150 target and 3000 production condition isolate other ministers',()=>{
 const c=country();c.vars.RUS_maximalist_land_reform_score=100;assert.ok(check(triggers.get('RUS_nat_reform_complete'),c));c.flags.RUS_nat_enabled=true;assert.ok(!check(triggers.get('RUS_nat_reform_complete'),c));c.vars.RUS_maximalist_land_reform_score=150;assert.ok(check(triggers.get('RUS_nat_reform_complete'),c));
 c.vars.RUS_max_landreform_tractor_promise_count=3;set(c,'produced',2999);assert.ok(!check(triggers.get('RUS_nat_tractor_complete'),c));set(c,'produced',3000);assert.ok(check(triggers.get('RUS_nat_tractor_complete'),c));c.vars.RUS_max_landreform_tractor_promise_count=2;assert.ok(!check(triggers.get('RUS_nat_tractor_complete'),c));
});
test('domestic needs grant at most 3 reform points per full quarter and 50 PP',()=>{
 const c=fresh();c.flags.RUS_maximalist_land_reform_in_progress=true;
 for(const g of ['food','beet','textile']){set(c,g+'_ratio',1);set(c,g+'_left',0);}
 set(c,'mean_coverage',0);set(c,'task',3);set(c,'fraction',1);set(c,'eligible_days',92);run(c,'award');assert.equal(c.vars.RUS_agri_last_quarter_score,3);assert.equal(c.pp,50);
 c.flags.RUS_maximalist_land_reform_failure=true;run(c,'award');assert.equal(c.vars.RUS_agri_last_quarter_score,0);
});
test('success transfers excess once and keeps the 150 floor when spending',()=>{
 const c=fresh();c.flags.RUS_maximalist_land_reform_success=true;c.vars.RUS_maximalist_land_reform_score=162;
 exec(effects.get('RUS_agri_refresh_score_account'),c);exec(effects.get('RUS_agri_refresh_score_account'),c);assert.equal(c.vars.RUS_agri_spendable_score,12);assert.equal(c.vars.RUS_maximalist_land_reform_score,150);
 c.temps.RUS_agri_purchase_cost=8;exec(effects.get('RUS_agri_spend_score'),c);assert.equal(c.vars.RUS_agri_spendable_score,4);assert.equal(c.vars.RUS_maximalist_land_reform_score,150);
});
test('quarter settles once across native-date boundary and serialised reload',()=>{
 let c=fresh(150,3);c.flags.RUS_maximalist_land_reform_in_progress=true;day(c);assert.equal(val(c,'season'),2);assert.equal(val(c,'remaining'),92);assert.equal(val(c,'last_season'),1);assert.ok(val(c,'last_pp')<1);
 let clone=JSON.parse(JSON.stringify(c));for(let i=0;i<10;i++){day(c);day(clone);}assert.equal(JSON.stringify(c),JSON.stringify(clone));
 const snapshot=JSON.stringify(c);run(c,'daily');assert.equal(JSON.stringify(c),snapshot);
});
test('deadline settles only elapsed production and cannot award twice',()=>{
 const c=fresh(243);c.flags.RUS_maximalist_land_reform_in_progress=true;for(let i=0;i<20;i++)day(c);run(c,'deadline');const score=c.vars.RUS_maximalist_land_reform_score,pp=c.pp,stocks=crops.map(x=>val(c,x+'_stock'));run(c,'deadline');assert.equal(c.vars.RUS_maximalist_land_reform_score,score);assert.equal(c.pp,pp);assert.deepEqual(crops.map(x=>val(c,x+'_stock')),stocks);
});
test('stock accounting, full orders and military equipment counters are separate',()=>{
 const c=fresh();set(c,'actual',1);set(c,'fraction',1);set(c,'wheat_work',20);set(c,'rye_work',0);set(c,'beet_work',2);set(c,'flax_work',4);set(c,'cotton_work',0);run(c,'consume');assert.equal(val(c,'wheat_work'),12);
 set(c,'generic_crop',1);set(c,'generic_quantity',4);set(c,'generic_accept',1);set(c,'generic_priority',1);set(c,'machine_work',0);run(c,'trade');assert.equal(val(c,'wheat_work'),8);assert.equal(val(c,'generic_shipped'),1);assert.ok(val(c,'income')>0);run(c,'trade');assert.equal(val(c,'income'),0);
});
test('political support has two quarterly slots and no direct reform-score effect',()=>{
 const defs=parse(read('common/decisions/RUS_national_agriculture_decisions.txt'))[0].value;const c=fresh();
 for(const id of ['food','repair']){const d=get(defs,'RUS_nat_support_'+id);assert.ok(check(get(d,'available'),c));exec(get(d,'complete_effect'),c);assert.ok(!check(get(d,'available'),c));}
 assert.equal(val(c,'support_count'),2);assert.ok(!check(get(get(defs,'RUS_nat_support_emergency'),'available'),c));assert.equal(c.vars.RUS_maximalist_land_reform_score||0,0);
});
test('4500 machinery storage halts production without manufacturing promise progress',()=>{
 const c=fresh(59,8);set(c,'installed',400);set(c,'machine_stock',4500);const before=val(c,'produced');day(c);assert.equal(val(c,'daily'),0);assert.equal(val(c,'produced'),before);set(c,'machine_stock',4499.9);day(c);assert.ok(val(c,'produced')-before<=.10001);assert.ok(val(c,'machine_stock')<=4500);
});
test('adverse weather and repairs modify fixed quarterly wear, never warehouse stock',()=>{
 const c=fresh();set(c,'elapsed',92);set(c,'fraction',1);set(c,'installed',400);set(c,'machine_stock',100);set(c,'coverage_sum',92);set(c,'eligible_days',92);set(c,'boundary',1);set(c,'wear',.25);set(c,'repair_support',.05);c.vars.RUS_agri_weather=-.4;c.flags.RUS_agri_allocation_locked=true;run(c,'settle');assert.equal(val(c,'last_loss'),100);assert.equal(val(c,'installed'),400);assert.equal(val(c,'machine_stock'),0);
});
test('hard annual caps: domestic score 12, political power 200, including repeated partial arithmetic',()=>{
 const c=fresh();c.flags.RUS_maximalist_land_reform_in_progress=true;for(const g of ['food','beet','textile']){set(c,g+'_ratio',1);set(c,g+'_left',0);}set(c,'task',3);set(c,'mean_coverage',0);set(c,'fraction',1);set(c,'eligible_days',92);
 for(let i=0;i<6;i++)run(c,'award');assert.equal(val(c,'domestic_year'),12);assert.equal(c.pp,200);assert.equal(c.vars.RUS_maximalist_land_reform_score,12);
});
test('emergency procurement fills only the food gap and never yields export surplus',()=>{
 const c=fresh();set(c,'fraction',1);set(c,'emergency_purchase',1);set(c,'wheat_work',6);set(c,'rye_work',0);run(c,'emergency_fill');assert.equal(val(c,'wheat_work'),7.2);assert.equal(val(c,'emergency_purchase'),0);run(c,'emergency_fill');assert.equal(val(c,'wheat_work'),7.2);
});
test('machine orders observe domestic installation, reserve and distinct shipment counters',()=>{
 const c=fresh();set(c,'actual',1);set(c,'installed',400);set(c,'machine_work',250);set(c,'produced',3000);set(c,'fra_machine_quantity',100);set(c,'eng_machine_quantity',100);set(c,'machine_market',0);run(c,'trade');assert.equal(val(c,'fra_machine_shipped'),1);assert.equal(val(c,'eng_machine_shipped'),0);assert.equal(val(c,'machine_work'),150);assert.equal(val(c,'income'),16500);assert.equal(val(c,'produced'),3000);
});
test('fixed-point eight-factory production can reach 3000 in 540 days without exports',()=>{
 const c=fresh(59,8);c.precision=1000;
 for(let d=1;d<=540;d++){c.vars.RUS_first_five_year_plan_score=Math.min(150,d/5);day(c);}
 assert.ok(val(c,'produced')>=3000);assert.ok(val(c,'machine_stock')<=4500);assert.ok(val(c,'efficiency')<=val(c,'cap'));console.log('Fixed-point production at day 540:',val(c,'produced'));
});
test('3600-day simulations remain bounded and succeed with existing reform decisions as auxiliary points',()=>{
 let low=Infinity,high=0,successes=0;
 for(let seed=1;seed<=24;seed++){
 const c=fresh(59,8);c.seed=seed;c.precision=1000;c.flags.RUS_maximalist_land_reform_in_progress=true;c.ideas.RUS_aleksey_ustinov_advisor=true;c.ideas.RUS_andrey_kolegayev_advisor=true;c.ideas.RUS_irina_kakhovskaya_advisor=true;
 for(let d=1;d<=720;d++){c.vars.RUS_first_five_year_plan_score=Math.min(150,d/5);day(c);}
 run(c,'deadline');const points=c.vars.RUS_maximalist_land_reform_score;low=Math.min(low,points);high=Math.max(high,points);
 // This scenario assumes 90 auxiliary points from existing reform decisions;
 // it does not assert that farming alone can reach the 150-point goal.
 if(points+90>=150)successes++;
 c.flags.RUS_maximalist_land_reform_success=true;delete c.flags.RUS_maximalist_land_reform_in_progress;c.countries=['ENG','FRA'];c.focuses.push('RUS_future_foreign_002','RUS_future_foreign_017');
 for(let d=721;d<=3600;d++){day(c);assert.ok(val(c,'budget')<=24);assert.ok(val(c,'machine_stock')<=4500);assert.ok(val(c,'installed')<=500);assert.ok(c.surplus<=Math.ceil(d/90)*63000);}
 }
 console.log(JSON.stringify({seeds:24,agricultureScore720:[low,high],passesWith90Auxiliary:successes}));assert.equal(successes,24);
});
test('unstarted five-year plan is zero, current parameters clamp and do not use historic maxima',()=>{
 const c=fresh(59,8);delete c.flags.RUS_first_five_year_plan_mission_started;c.vars.RUS_first_five_year_plan_score=150;run(c,'parameters');assert.equal(val(c,'score'),0);
 c.flags.RUS_first_five_year_plan_mission_started=true;c.vars.RUS_first_five_year_plan_score=999;c.vars['modifier@industrial_capacity_factory']=99;c.vars['modifier@production_factory_max_efficiency_factor']=99;c.vars['modifier@production_factory_efficiency_gain_factor']=99;run(c,'parameters');assert.equal(val(c,'score'),150);assert.equal(val(c,'cap'),10000);assert.equal(val(c,'growth'),2);assert.equal(val(c,'output'),2);
 c.vars.RUS_first_five_year_plan_score=-99;c.vars['modifier@industrial_capacity_factory']=-99;c.vars['modifier@production_factory_max_efficiency_factor']=-99;c.vars['modifier@production_factory_efficiency_gain_factor']=-99;set(c,'efficiency',10000);run(c,'parameters');assert.equal(val(c,'score'),0);assert.equal(val(c,'cap'),4500);assert.equal(val(c,'efficiency'),4500);assert.equal(val(c,'growth'),.25);assert.equal(val(c,'output'),.5);
});
test('zero-floored available factories still detect wartime factory losses',()=>{
 const c=fresh(59,50);c.civCapacity=2;c.vars.num_of_civilian_factories_available_for_projects=0;day(c);assert.equal(val(c,'factories'),2);assert.ok(val(c,'daily')<2);assert.equal(c.vars.num_of_civilian_factories_available_for_projects,0);
 set(c,'efficiency',6000);set(c,'requested',0);run(c,'set_factories');for(let i=0;i<400;i++)day(c);assert.equal(val(c,'efficiency'),3000);
});
test('minister appointment is the only automatic entry; other options do not enable agriculture',()=>{
 const events=parse(read('events/RUS events (Russia).txt'));const ev=events.find(e=>Array.isArray(e.value)&&get(e.value,'id')==='russia_socialist_events.332').value;
 const opts=ev.filter(e=>e.key==='option');assert.equal(opts.length,3);
 for(const o of opts){const text=JSON.stringify(o);assert.equal(text.includes('RUS_nat_enable'),get(o.value,'name')==='russia_socialist_events.332.c');}
 const cats=read('common/decisions/categories/RUS_agricultural_quarterly_management_categories.txt');assert.ok(cats.includes('visible_when_empty = yes'));assert.ok(cats.includes('scripted_gui = RUS_national_agriculture_gui'));
});
test('mission extension, deadline production and success-only outlook hooks are present',()=>{
 const evs=parse(read('events/RUS stalin maximalist land reform events.txt'));const ev=id=>evs.find(e=>Array.isArray(e.value)&&get(e.value,'id')===`rus_maximalist_land_reform_events.${id}`).value;
 const reform=JSON.stringify(ev(70)),promise=JSON.stringify(ev(110));assert.ok(reform.includes('add_days_mission_timeout'));assert.ok(reform.includes('180'));assert.ok(promise.includes('270'));
 assert.ok(JSON.stringify(ev(2)).includes('RUS_agricultural_management.3'));assert.ok(!JSON.stringify(ev(3)).includes('RUS_agricultural_management.3'));assert.ok(!JSON.stringify(effects.get('RUS_nat_enable')).includes('RUS_agricultural_management.3'));
 const missions=parse(read('common/decisions/RUS stalin maximalist land reform decisions.txt'))[0].value;assert.ok(JSON.stringify(get(get(missions,'RUS_max_landreform_tractor_promise_mission'),'timeout_effect')).includes('RUS_nat_daily'));
});
test('completed reform preserves promise decisions; failure closes them without stopping production',()=>{
 const c=fresh(59,8);c.flags.RUS_maximalist_land_reform_success=true;c.flags.RUS_max_landreform_tractor_promise_active=true;c.vars.RUS_maximalist_land_reform_score=150;c.vars.RUS_max_landreform_tractor_promise_count=2;
 assert.ok(check(triggers.get('RUS_nat_promote_allowed'),c));assert.ok(check(triggers.get('RUS_nat_reform_decision_closed'),c));
 exec(effects.get('RUS_maximalist_land_reform_add_score_5'),c);assert.equal(c.vars.RUS_maximalist_land_reform_score,150);assert.equal(c.vars.RUS_agri_spendable_score,5);
 delete c.flags.RUS_maximalist_land_reform_success;c.flags.RUS_maximalist_land_reform_failure=true;assert.ok(!check(triggers.get('RUS_nat_promote_allowed'),c));const before=val(c,'produced');day(c);assert.ok(val(c,'produced')>before);assert.ok(!check(triggers.get('RUS_agri_exchange_unlocked'),c));
});
test('other-minister monthly points are preserved; national agriculture has no passive points',()=>{
 const c=country();c.flags.RUS_maximalist_land_reform_in_progress=true;c.ideas.RUS_aleksey_ustinov_advisor=true;c.ideas.RUS_andrey_kolegayev_advisor=true;c.ideas.RUS_irina_kakhovskaya_advisor=true;
 exec(effects.get('RUS_maximalist_land_reform_apply_monthly_advisor_score'),c);assert.equal(c.vars.RUS_maximalist_land_reform_score,3);c.flags.RUS_nat_enabled=true;exec(effects.get('RUS_maximalist_land_reform_apply_monthly_advisor_score'),c);assert.equal(c.vars.RUS_maximalist_land_reform_score,3);
 for(const score of [99,100,149]){c.vars.RUS_maximalist_land_reform_score=score;exec(effects.get('RUS_maximalist_land_reform_update_stage_idea'),c);assert.equal(c.vars.RUS_maximalist_land_reform_stage,4);}c.vars.RUS_maximalist_land_reform_score=150;exec(effects.get('RUS_maximalist_land_reform_update_stage_idea'),c);assert.equal(c.vars.RUS_maximalist_land_reform_stage,5);
});
test('orders only appear next quarter and existing contracts survive a buyer disappearing',()=>{
 const c=fresh(59);assert.equal(val(c,'generic_quantity'),0);assert.equal(val(c,'fra_quantity'),0);
 c.focuses.push('RUS_future_foreign_002','RUS_future_foreign_017');c.countries=['FRA','ENG'];run(c,'refresh');assert.equal(val(c,'fra_quantity'),0);run(c,'start_quarter');assert.ok(val(c,'generic_quantity')>=2);assert.ok(val(c,'fra_machine_quantity')>=60);
 const before=val(c,'fra_quantity');c.countries=[];run(c,'refresh');assert.equal(val(c,'fra_quantity'),before);run(c,'start_quarter');assert.equal(val(c,'fra_quantity'),0);assert.equal(val(c,'eng_machine_quantity'),0);assert.ok(val(c,'generic_quantity')>0);
});
test('domestic supply and reserves have priority; cancellation and priority do not duplicate stocks',()=>{
 const c=fresh();set(c,'actual',1);set(c,'fraction',1);set(c,'food_ratio',1);set(c,'beet_ratio',1);set(c,'textile_ratio',1);set(c,'food_reserve',8);set(c,'food_left',10);set(c,'wheat_work',10);set(c,'generic_crop',1);set(c,'generic_quantity',2);set(c,'fra_crop',1);set(c,'fra_quantity',2);set(c,'generic_priority',2);set(c,'fra_priority',1);run(c,'trade');assert.equal(val(c,'fra_shipped'),1);assert.equal(val(c,'generic_shipped'),0);assert.equal(val(c,'wheat_work'),8);
 set(c,'fra_shipped',0);set(c,'fra_accept',0);set(c,'wheat_work',10);set(c,'food_left',10);run(c,'trade');assert.equal(val(c,'generic_shipped'),1);assert.equal(val(c,'fra_shipped'),0);
 set(c,'generic_shipped',0);set(c,'wheat_work',50);set(c,'food_left',50);set(c,'beet_ratio',.5);run(c,'trade');assert.equal(val(c,'income'),0);assert.equal(val(c,'wheat_work'),50);
});
test('all domestic reward thresholds and partial-quarter political rewards',()=>{
 for(const [ratio,expected] of [[.899,0],[.9,1],[.999,1],[1,2]]){const c=fresh();c.flags.RUS_maximalist_land_reform_in_progress=true;set(c,'food_ratio',ratio);set(c,'beet_ratio',0);set(c,'textile_ratio',0);set(c,'task',3);set(c,'fraction',1);set(c,'eligible_days',92);run(c,'award');assert.equal(c.vars.RUS_agri_score_award,expected);}
 const c=fresh();for(const [g] of [['food'],['beet'],['textile']])set(c,g+'_ratio',1);set(c,'task',3);set(c,'fraction',.5);run(c,'award');assert.equal(c.pp,25);assert.equal(c.vars.RUS_agri_score_award,0);
});
test('annual ideas replace earlier tiers; supply and reserves determine the tier',()=>{
 const c=fresh();set(c,'year_weight',4);set(c,'year_supply',3.5);run(c,'annual');assert.ok(c.ideas.RUS_agri_annual_shortfall);
 set(c,'year_weight',4);set(c,'year_supply',4);for(const g of ['food','beet','textile'])set(c,g+'_left',0);run(c,'annual');assert.ok(c.ideas.RUS_agri_annual_surplus);assert.ok(!c.ideas.RUS_agri_annual_shortfall);
 set(c,'year_weight',4);set(c,'year_supply',4);for(const g of ['food','beet','textile'])set(c,g+'_left',val(c,g+'_demand'));run(c,'annual');assert.ok(c.ideas.RUS_agri_annual_bumper_surplus);assert.ok(!c.ideas.RUS_agri_annual_surplus);
 set(c,'year_weight',4);set(c,'year_supply',3.6);run(c,'annual');assert.ok(!Object.keys(c.ideas).some(k=>k.startsWith('RUS_agri_annual_')));
});
test('food shortage recovers gradually and even small industrial-crop shortages affect output',()=>{
 const c=fresh();set(c,'food_ratio',.5);set(c,'beet_ratio',.99);set(c,'textile_ratio',1);for(let i=0;i<5;i++)run(c,'penalties');assert.equal(val(c,'shortage'),3);assert.equal(val(c,'stability'),-.06);assert.equal(val(c,'consumer'),.05);assert.equal(val(c,'factory_penalty'),-.03);
 set(c,'textile_ratio',.99);run(c,'penalties');assert.equal(val(c,'factory_penalty'),-.05);for(const g of ['food','beet','textile'])set(c,g+'_ratio',1);run(c,'penalties');assert.equal(val(c,'shortage'),2);assert.equal(val(c,'factory_penalty'),0);
});
test('next-quarter organisation bonuses never add equipment and only activate once across winter',()=>{
 const c=fresh(58);c.flags.RUS_agri_next_machinery=true;run(c,'start_quarter');assert.ok(c.flags.RUS_agri_active_machinery);assert.equal(val(c,'produced'),0);assert.equal(val(c,'installed'),100);assert.equal(c.vars.RUS_agri_wheat_base,1.1);day(c);assert.ok(!c.flags.RUS_agri_active_machinery);assert.equal(c.vars.RUS_agri_wheat_base,1.25);
 c.flags.RUS_agri_active_storage=true;c.vars.RUS_agri_wheat_base=.4;c.vars.RUS_agri_wheat_fatigue=0;c.vars.RUS_agri_wheat_investment=1;set(c,'fraction',1);set(c,'actual',0);run(c,'yield');assert.equal(val(c,'wheat_rate'),.55);c.vars.RUS_agri_wheat_base=1.25;run(c,'yield');assert.equal(val(c,'wheat_rate'),1.25);
});
test('three locales, declared GUI keys, sprites and fixed page boundaries',()=>{
 let expected;const keys=new Set();for(const lang of ['simp_chinese','english','russian']){
 const bytes=fs.readFileSync(path.join(root,'localisation',lang,`RUS_national_agriculture_l_${lang}.yml`));assert.equal(bytes.subarray(0,3).toString('hex'),'efbbbf');const ids=bytes.toString('utf8').split(/\r?\n/).slice(1).filter(Boolean).map(l=>l.trim().split(':')[0]);assert.equal(new Set(ids).size,ids.length);if(expected)assert.deepEqual(ids,expected);expected=ids;ids.forEach(k=>keys.add(k));
 }
 const gui=get(parse(read('interface/RUS_national_agriculture.gui')),'guiTypes');assert.ok(gui);
 for(const m of read('interface/RUS_national_agriculture.gui').matchAll(/(?:text|buttonText|pdx_tooltip) = "([^"]+)"/g))assert.ok(keys.has(m[1])||m[1].startsWith('RUS_agri_'),'Missing UI key '+m[1]);
});
test('four page buttons switch only visibility, retain allocations and show complete help',()=>{
 const c=fresh(59,8);run(c,'auto_allocate');
 const sg=get(get(parse(read('common/scripted_guis/RUS_national_agriculture.txt')),'scripted_gui'),'RUS_national_agriculture_gui');
 const clicks=get(sg,'effects'),visibility=get(sg,'triggers');
 const before=crops.map(crop=>c.vars['RUS_agri_'+crop+'_investment']);
 for(let page=1;page<=4;page++){
  exec(get(clicks,'nat_tab_'+(page-1)+'_click'),c);assert.equal(val(c,'page'),page);
  assert.deepEqual(crops.map(crop=>c.vars['RUS_agri_'+crop+'_investment']),before);
  assert.equal(check(get(visibility,'nat_wheat_name_visible'),c),page===1);
  assert.equal(check(get(visibility,'nat_machine_0_visible'),c),page===2);
  assert.equal(check(get(visibility,'nat_stock_wheat_visible'),c),page===3);
 }
 const zh=read('localisation/simp_chinese/RUS_national_agriculture_l_simp_chinese.yml');
 assert.ok(zh.includes('“§4大刀阔斧§!”'));assert.ok(zh.includes('§R时间与精力§!'));
 for(let i=0;i<4;i++)assert.ok(zh.includes(`RUS_nat_tab_${i}_tt:`));
});
console.log(count+' national agriculture regression groups passed; native HOI4 QA remains required.');
