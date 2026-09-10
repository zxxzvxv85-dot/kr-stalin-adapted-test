const assert=require('node:assert/strict');
const {parse,get,effects,country,check,exec,read}=require('./test_agri_development.cjs');
const crops=['wheat','rye','beet','flax','cotton'];
const run=(c,k)=>exec(effects.get('RUS_nat_'+k),c);
const val=(c,k)=>c.vars['RUS_nat_'+k]||0;
const set=(c,k,v)=>c.vars['RUS_nat_'+k]=v;
const ids=c=>c.events.map(e=>get(e,'id'));
const plan=c=>crops.map(k=>c.vars['RUS_agri_'+k+'_investment']);
const fresh=(doy=59,ai=false)=>{
 const c=country();c.ai=ai;c.vars['global.num_days']=706640+doy;c.civCapacity=100;
 c.vars.num_of_civilian_factories_available_for_projects=100;run(c,'enable');return c;
};
const step=c=>{c.vars['global.num_days']++;run(c,'daily');};
const gui=get(get(parse(read('common/scripted_guis/RUS_national_agriculture.txt')),'scripted_gui'),'RUS_national_agriculture_gui');
const clicks=get(gui,'effects'),click=(c,k)=>exec(get(clicks,'nat_'+k+'_click'),c);
const definitions=parse(read('events/RUS_national_agriculture_events.txt')).filter(e=>e.key==='country_event');
const event=n=>definitions.find(e=>get(e.value,'id')==='RUS_national_agriculture.'+n).value;
let count=0;
const test=(name,f)=>{f();count++;console.log('PASS '+name);};
test('guide is free, repeatable, player-only and does not reset the system',()=>{
 const d=get(parse(read('common/decisions/RUS_national_agriculture_decisions.txt'))[0].value,'RUS_nat_guide_decision');
 assert.equal(get(d,'cost'),'0');assert.equal(get(d,'fire_only_once'),'no');
 assert.ok(!check(get(d,'visible'),country()));assert.ok(!check(get(d,'visible'),fresh(59,true)));
 const c=fresh();assert.deepEqual(ids(c),['RUS_national_agriculture.2']);run(c,'enable');assert.equal(c.events.length,1);
 const saved=structuredClone(c);for(let i=0;i<5;i++){assert.ok(check(get(d,'visible'),c));exec(get(d,'complete_effect'),c);}
 assert.deepEqual(c.vars,saved.vars);assert.deepEqual(c.flags,saved.flags);assert.equal(c.surplus,saved.surplus);
 assert.deepEqual(ids(c),Array(6).fill('RUS_national_agriculture.2'));assert.equal(fresh(59,true).events.length,0);
 assert.ok(!get(clicks,'nat_guide_click'),'Guide entry belongs in decisions');
});
test('manual drafts, including intentional zero, survive settlement and seasonal rollover',()=>{
 for(const doy of [150,242,333,58]) {
  const c=fresh(doy);click(c,'clear');click(c,'wheat_plus');click(c,'beet_plus');
  const saved=plan(c);assert.ok(c.flags.RUS_nat_manual_plan);assert.ok(!c.flags.RUS_agri_allocation_locked);
  step(c);assert.deepEqual(plan(c),saved);assert.ok(!c.flags.RUS_agri_allocation_locked);
  assert.ok(val(c,'wheat_last_yield')>0);assert.ok(val(c,'beet_last_yield')>0);
  for(const crop of ['rye','flax','cotton']) assert.equal(val(c,crop+'_last_yield'),0);
 }
 const c=fresh(150);click(c,'clear');step(c);assert.deepEqual(plan(c),[0,0,0,0,0]);
 for(const crop of crops) assert.equal(val(c,crop+'_last_yield'),0);
});
test('confirm/reopen preserves drafts; auto mode clears manual selection and ignores hidden outcomes',()=>{
 const c=fresh();click(c,'clear');click(c,'rye_plus');click(c,'confirm');assert.ok(c.flags.RUS_agri_allocation_locked);
 const saved=plan(c);click(c,'reopen');assert.ok(!c.flags.RUS_agri_allocation_locked);assert.deepEqual(plan(c),saved);
 click(c,'auto');assert.ok(!c.flags.RUS_nat_manual_plan);assert.equal(val(c,'allocated'),20);
 const a=structuredClone(c),b=structuredClone(c);a.vars.RUS_agri_weather=-.4;b.vars.RUS_agri_weather=.4;
 for(const crop of crops){a.vars['RUS_agri_'+crop+'_market']=-.4;b.vars['RUS_agri_'+crop+'_market']=.4;}
 click(a,'auto');click(b,'auto');assert.deepEqual(plan(a),plan(b));
 c.vars['global.num_days']=706791;run(c,'start_quarter');assert.equal(val(c,'allocated'),20);
 assert.ok(!c.flags.RUS_nat_manual_plan);
});
test('deadline reminders fire once, survive reload and suppress confirmed/AI plans',()=>{
 let c=fresh(143);c.events=[];step(c);assert.deepEqual(ids(c),['RUS_national_agriculture.4']);
 c=JSON.parse(JSON.stringify(c));for(let i=0;i<6;i++)step(c);
 assert.deepEqual(ids(c),['RUS_national_agriculture.4']);run(c,'daily');assert.equal(c.events.length,1);
 step(c);assert.equal(ids(c).at(-1),'RUS_national_agriculture.3');assert.ok(!c.flags.RUS_nat_deadline_reminded);
 for(const ai of [false,true]){const x=fresh(143,ai);x.events=[];if(!ai)click(x,'confirm');step(x);assert.equal(x.events.length,0);}
});
test('quarter and annual notifications are exclusive and partial deadlines do not fake a new quarter',()=>{
 for(const [doy,id] of [[150,3],[242,3],[333,3],[58,1]]) {
  const c=fresh(doy);c.events=[];step(c);assert.deepEqual(ids(c),['RUS_national_agriculture.'+id]);
  run(c,'daily');assert.equal(c.events.length,1);
  const ai=fresh(doy,true);step(ai);assert.equal(ai.events.length,0);
 }
 const c=fresh(100);step(c);c.events=[];run(c,'deadline');run(c,'deadline');assert.equal(c.events.length,0);
});
test('all active crop orders differ across seeds and missing countries without changing quantities',()=>{
 const c=fresh();c.focuses=['RUS_future_foreign_002','RUS_future_foreign_017'];
 for(const countries of [[],['FRA'],['ENG'],['FRA','ENG']]) for(let seed=1;seed<=100;seed++) {
  c.countries=countries;c.seed=seed;run(c,'draw_orders');
  const active=['generic','fra','eng'].filter(k=>val(c,k+'_quantity')>0);
  assert.equal(active.length,countries.length+1);assert.equal(new Set(active.map(k=>val(c,k+'_crop'))).size,active.length);
  for(const k of active){assert.ok(val(c,k+'_crop')>=1&&val(c,k+'_crop')<=5);assert.ok([2,3,4].includes(val(c,k+'_quantity')));}
  const frozen=active.map(k=>[val(c,k+'_crop'),val(c,k+'_quantity')]);c.countries=[];run(c,'refresh');
  assert.deepEqual(active.map(k=>[val(c,k+'_crop'),val(c,k+'_quantity')]),frozen);
 }
});
test('ledger totals include domestic needs, reserves and accepted orders without spending inventory',()=>{
 for(const war of [false,true]) for(const doy of [59,100]) {
  const c=fresh(doy);c.war=war;run(c,'start_quarter');click(c,'clear');
  set(c,'generic_crop',1);set(c,'generic_quantity',3);set(c,'fra_crop',3);set(c,'fra_quantity',2);
  set(c,'eng_crop',4);set(c,'eng_quantity',4);run(c,'refresh');
  const before=crops.map(k=>val(c,k+'_stock')),cash=c.surplus,seed=c.seed;
  for(const [g,cs,orders] of [['food',['wheat','rye'],3],['beet',['beet'],2],['textile',['flax','cotton'],4]]) {
   assert.equal(val(c,g+'_stock_now'),cs.reduce((s,k)=>s+val(c,k+'_stock'),0));
   assert.equal(val(c,g+'_order_need'),orders);
   assert.ok(Math.abs(val(c,g+'_need')-val(c,g+'_demand')*val(c,'fraction'))<1e-5);
   assert.ok(Math.abs(val(c,g+'_target_total')-val(c,g+'_need')-val(c,g+'_reserve')-orders)<1e-5);
   assert.ok(Math.abs(val(c,g+'_all_gap')-Math.max(0,val(c,g+'_target_total')-val(c,g+'_stock_now')-val(c,g+'_new_yield')))<1e-5);
  }
  const gap=val(c,'food_all_gap');click(c,'priority');assert.equal(val(c,'food_all_gap'),gap);
  click(c,'accept_generic');assert.equal(val(c,'food_order_need'),0);assert.ok(Math.abs(val(c,'food_all_gap')-Math.max(0,gap-3))<1e-5);
  click(c,'ledger');assert.equal(ids(c).at(-1),'RUS_national_agriculture.5');
  assert.deepEqual(crops.map(k=>val(c,k+'_stock')),before);assert.equal(c.surplus,cash);assert.equal(c.seed,seed);
 }
});
test('event navigation never pays rewards and confirmation uses the existing plan',()=>{
 assert.equal(new Set(definitions.map(e=>get(e.value,'id'))).size,7);
 for(const def of definitions) {
  assert.equal(get(def.value,'is_triggered_only'),'yes');
  for(const option of def.value.filter(n=>n.key==='option')) {
   const c=fresh();click(c,'clear');click(c,'wheat_plus');const before=structuredClone(c);
   exec(option.value.filter(n=>n.key!=='trigger'),c);
   assert.deepEqual(plan(c),plan(before));assert.equal(c.surplus,before.surplus);assert.equal(c.pp,before.pp);
   assert.equal(c.vars.RUS_maximalist_land_reform_score,before.vars.RUS_maximalist_land_reform_score);
   assert.deepEqual(crops.map(k=>val(c,k+'_stock')),crops.map(k=>val(before,k+'_stock')));
  }
 }
 const confirm=get(event(4).filter(n=>n.key==='option').find(n=>get(n.value,'name')==='RUS_nat_event_confirm').value,'trigger');
 const c=fresh();assert.ok(check(confirm,c));click(c,'confirm');assert.ok(!check(confirm,c));
});
test('guide explains fallible weather/markets and physical output without revealing hidden outcomes',()=>{
 for(const lang of ['simp_chinese','english','russian']) {
  const loc=new Map([...read(`localisation/${lang}/RUS_national_agriculture_l_${lang}.yml`).matchAll(/^\s*([\w.]+):0 "(.*)"$/gm)].map(m=>[m[1],m[2]]));
  for(const def of definitions) {
   for(const k of ['title','desc'])assert.ok(loc.has(get(def.value,k)));
   for(const opt of def.value.filter(n=>n.key==='option'))assert.ok(loc.has(get(opt.value,'name')));
  }
  for(const i of [2,6,7])assert.ok(!loc.get(`RUS_national_agriculture.${i}.d`).includes('[?'),'Static guide must not reveal hidden outcomes');
  const weather=loc.get('RUS_national_agriculture.6.d'),indicators=loc.get('RUS_national_agriculture.7.d');
  assert.ok(weather.includes('§b1.25§! + §b0.20§! = §b1.45§!'));
  assert.ok(indicators.includes('\\n\\n'));
  if(lang==='simp_chinese') {
   for(const term of ['概率倾向','实际天气和行情到季末','预测词语也不会直接加进预估数字'])assert.ok(weather.includes(term));
   for(const term of ['单位产量','地力疲劳','市场饱和','销售容量','无可交付订单','预计新增产量 =','单笔收入 ='])assert.ok(indicators.includes(term));
  }
  for(const i of [2,3,4,5,6,7]) {
   assert.ok(!loc.get(`RUS_national_agriculture.${i}.d`).includes('§Y'),'No yellow emphasis on event paper');
   let color='';
   for(const token of loc.get(`RUS_national_agriculture.${i}.d`).match(/§.|£[^£]+£|\[[^\]]+\]|[+-]?\d+(?:[.,]\d+)?%?|./g)) {
    if(token.startsWith('§'))color=token[1]==='!'?'':token[1];
    else if(/^(?:[+-]?\d|\[\?)/.test(token))assert.equal(color,'b',`${lang}: black event figure ${token}`);
   }
  }
 }
});
console.log(count+' feedback regression groups passed; in-game UI testing remains required.');
