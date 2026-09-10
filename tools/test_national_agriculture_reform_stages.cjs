const assert=require('node:assert/strict');
const {parse,get,effects,country,exec,check,read}=require('./test_agri_development.cjs');
const thresholds=[0,20,40,60,80,110,140,170,200];
const ids=thresholds.map((_,i)=>'RUS_nat_land_reform_stage_'+i),bonus=ids[8]+'_tractor_bonus';
const ideas=get(get(parse(read('common/ideas/RUS_national_agriculture_reform_ideas.txt')),'ideas'),'country');
const original=get(get(parse(read('common/ideas/RUS stalin maximalist land reform ideas.txt')),'ideas'),'country');
const mods=(defs,id)=>Object.fromEntries(get(get(defs,id),'modifier').filter(n=>n.key!=='custom_modifier_tooltip').map(n=>[n.key,+n.value]));
const run=(c,id)=>exec(effects.get(id),c);
const refresh=c=>run(c,'RUS_maximalist_land_reform_update_stage_idea');
const fresh=(score=0)=>{const c=country();c.flags.RUS_nat_enabled=true;c.flags.RUS_agri_management_unlocked=true;c.flags.RUS_maximalist_land_reform_in_progress=true;c.vars.RUS_maximalist_land_reform_score=score;return c;};
let count=0;
const test=(name,f)=>{f();count++;console.log('PASS '+name);};

test('all nine thresholds and fractional boundaries select one spirit, not additive rewards',()=>{
 const c=fresh();c.ideas.RUS_agri_annual_surplus=true;
 for(const score of [...thresholds,...thresholds.slice(1).map(x=>x-.001),175].sort((a,b)=>a-b)){
  c.vars.RUS_maximalist_land_reform_score=score;refresh(c);
  const index=thresholds.findLastIndex(x=>score>=x);
  assert.equal(c.vars.RUS_nat_reform_stage,index);
  assert.deepEqual([...ids,bonus].filter(id=>c.ideas[id]),[ids[index]]);
  assert.equal(c.vars.RUS_maximalist_land_reform_stage,index===8?5:Math.min(index,4));
  assert.ok(c.ideas.RUS_agri_annual_surplus);
 }
});
test('consumer expectations, military construction and absolute slots match the approved table',()=>{
 const consumer=[.2,.14,.08,.02,.01,0,-.03,-.07,-.1],arms=[0,0,0,0,0,0,.05,.1,.15],slots=[0,0,0,0,0,0,0,1,2];
 ids.forEach((id,i)=>{const m=mods(ideas,id);assert.equal(m.consumer_goods_expected_value,consumer[i]);assert.equal(m.production_speed_arms_factory_factor||0,arms[i]);assert.equal(m.global_building_slots||0,slots[i]);assert.equal(m.global_building_slots_factor,undefined);assert.equal(m.supply_node_range||0,i===8?.1:i===7?.05:0);});
 for(let i=0;i<4;i++)assert.deepEqual(mods(ideas,ids[i]),mods(original,'RUS_maximalist_land_reform_stage_'+i));
 const final=mods(ideas,ids[8]);for(const [key,value] of Object.entries(mods(original,'RUS_maximalist_land_reform_stage_5')))if(key!=='consumer_goods_expected_value')assert.equal(final[key],value);
});
test('completed machinery promise gives minus 12 percent, not a second stacked spirit',()=>{
 const c=fresh(200);c.flags.RUS_maximalist_land_reform_tractor_bonus=true;
 for(let i=0;i<4;i++)refresh(c);
 assert.deepEqual([...ids,bonus].filter(id=>c.ideas[id]),[bonus]);
 const m=mods(ideas,bonus);assert.equal(m.consumer_goods_expected_value,-.12);assert.equal(m.economy_cost_factor,-.2);assert.equal(m.production_speed_arms_factory_factor,.15);assert.equal(m.global_building_slots,2);assert.equal(m.supply_node_range,.1);
});
test('promise reward applies both before final reform and after it is complete',()=>{
 const event=parse(read('events/RUS stalin maximalist land reform events.txt')).find(n=>n.key==='country_event'&&get(n.value,'id')==='rus_maximalist_land_reform_events.15');
 const option=get(event.value,'option');
 assert.equal(+get(option,'add_stability'),.05);
 for(const score of [140,200]){
  const c=fresh(score);refresh(c);exec(option.filter(n=>n.key!=='add_stability'),c);
  assert.equal(c.pp,50);assert.ok(c.flags.RUS_maximalist_land_reform_tractor_bonus);
  if(score===140){assert.ok(c.ideas[ids[6]]);assert.ok(!c.ideas[bonus]);c.vars.RUS_maximalist_land_reform_score=200;refresh(c);}
  assert.ok(c.ideas[bonus]);assert.ok(!c.ideas[ids[8]]);
 }
});
test('old ministers retain the original six tiers and original tractor bonus',()=>{
 for(const score of [0,20,40,60,80,100,149,150]){
  const c=country();c.vars.RUS_maximalist_land_reform_score=score;refresh(c);
  const tier=score>=100?5:Math.floor(score/20);
  assert.ok(c.ideas['RUS_maximalist_land_reform_stage_'+tier]);assert.ok(!ids.some(id=>c.ideas[id]));assert.equal(c.vars.RUS_maximalist_land_reform_stage,tier);
 }
 const c=country();c.vars.RUS_maximalist_land_reform_score=100;c.flags.RUS_maximalist_land_reform_tractor_bonus=true;refresh(c);
 assert.ok(c.ideas.RUS_maximalist_land_reform_stage_5_tractor_bonus);assert.equal(mods(original,'RUS_maximalist_land_reform_stage_5_tractor_bonus').consumer_goods_expected_value,-.05);
});
test('score losses downgrade correctly, while spending after success preserves the final tier',()=>{
 const c=fresh(170);refresh(c);run(c,'RUS_maximalist_land_reform_subtract_score_3');assert.ok(c.ideas[ids[6]]);assert.ok(!c.ideas[ids[7]]);
 c.vars.RUS_maximalist_land_reform_score=218;c.flags.RUS_maximalist_land_reform_success=true;refresh(c);
 assert.equal(c.vars.RUS_maximalist_land_reform_score,200);assert.equal(c.vars.RUS_agri_spendable_score,18);assert.ok(c.ideas[ids[8]]);
 c.vars.RUS_agri_purchase_cost=18;run(c,'RUS_agri_spend_score');refresh(c);assert.equal(c.vars.RUS_agri_spendable_score,0);assert.ok(c.ideas[ids[8]]);
});
test('failure cleanup removes every new spirit, including the machinery variant',()=>{
 const event=parse(read('events/RUS stalin maximalist land reform events.txt')).find(n=>n.key==='country_event'&&get(n.value,'id')==='rus_maximalist_land_reform_events.3');
 const c=fresh(135);for(const id of [...ids,bonus])c.ideas[id]=true;
 exec(get(event.value,'option'),c);assert.ok(![...ids,bonus].some(id=>c.ideas[id]));assert.ok(c.ideas.RUS_maximalist_land_reform_stagnation);
});
test('stage and next-threshold localisation distinguish nine new tiers from the legacy five-step display',()=>{
 const definitions=parse(read('common/scripted_localisation/RUS_national_agriculture_loc.txt'));
 const select=(name,c)=>{const block=definitions.find(n=>get(n.value,'name')===name);return get(block.value.find(n=>n.key==='text'&&(!get(n.value,'trigger')||check(get(n.value,'trigger'),c))).value,'localization_key');};
 thresholds.forEach((score,i)=>{const c=fresh(score);assert.equal(select('GetRUSNatCurrentStage',c),'RUS_nat_stage_number_'+i);assert.equal(select('GetRUSNatNextStage',c),i===8?'RUS_maximalist_land_reform_next_stage_complete':'RUS_nat_next_stage_'+thresholds[i+1]);});
 assert.equal(select('GetRUSNatStageCount',fresh()),'RUS_nat_stage_total9');assert.equal(select('GetRUSNatStageCount',country()),'RUS_nat_stage_total5');
 for(const lang of ['simp_chinese','english','russian']){
  const text=read(`localisation/${lang}/RUS_national_agriculture_l_${lang}.yml`);
  for(const id of [...ids,bonus])for(const suffix of ['', '_desc'])assert.equal([...text.matchAll(new RegExp('^ '+id+suffix+':','gm'))].length,1);
  const replacement=read(`localisation/replace/RUS_national_agriculture_reform_l_${lang}.yml`);
  assert.equal((replacement.match(/\[GetRUSNatStageCount\]/g)||[]).length,2);
  assert.ok(!replacement.includes('§Y100§!'),'Coloured 100 must resolve to the route-specific target');
  assert.equal((replacement.match(/\[GetRUSNatTarget\]/g)||[]).length,4);
 }
});
console.log(count+' reform-stage regression groups passed; native rendering/save QA remains outstanding.');
