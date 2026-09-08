const assert = require('node:assert/strict');
const {parse,get,effects,country,exec,read} = require('./test_agri_development.cjs');
const run=(c,id)=>exec(effects.get(id),c);
const fresh=()=>{
 const c=country();c.vars['global.num_days']=706699;
 run(c,'RUS_nat_enable');c.flags.RUS_maximalist_land_reform_in_progress=true;return c;
};
let count=0;
function test(name,body){body();count++;console.log('PASS '+name);}
const decisions=get(parse(read('common/decisions/RUS stalin maximalist land reform decisions.txt')),'RUS_maximalist_land_reform_category');
const awarding=decisions.filter(d=>JSON.stringify(d.value).includes('RUS_nat_decision_score_'));
const complete=(c,d)=>exec(get(d,'remove_effect').filter(n=>n.key!=='log'),c);

test('all four initial and four repeat decisions use the source-specific cap',()=>{
 assert.equal(awarding.length,8);
 const initial=awarding.filter(d=>get(d.value,'fire_only_once')==='yes');assert.equal(initial.length,4);
 assert.ok(!JSON.stringify(decisions).includes('RUS_maximalist_land_reform_add_score_'));
 const c=fresh();for(const d of initial)complete(c,d.value);
 assert.equal(c.vars.RUS_nat_decision_score,40);assert.equal(c.vars.RUS_maximalist_land_reform_score,40);
 for(let i=0;i<50;i++)run(c,'RUS_nat_decision_score_5');
 assert.equal(c.vars.RUS_nat_decision_score,90);assert.equal(c.vars.RUS_maximalist_land_reform_score,90);
});
test('partial awards stop exactly at 90, including simultaneous completions',()=>{
 for(const used of [0,40,85,88,89.75,90])for(const amount of [5,10]){
  const c=fresh();c.vars.RUS_nat_decision_score=used;c.vars.RUS_maximalist_land_reform_score=used;
  run(c,'RUS_nat_decision_score_'+amount);const expected=Math.min(90,used+amount);
  assert.equal(c.vars.RUS_nat_decision_score,expected);assert.equal(c.vars.RUS_maximalist_land_reform_score,expected);
 }
 const c=fresh();c.vars.RUS_nat_decision_score=85;
 run(c,'RUS_nat_decision_score_10');run(c,'RUS_nat_decision_score_5');
 assert.equal(c.vars.RUS_nat_decision_score,90);assert.equal(c.vars.RUS_maximalist_land_reform_score,5);
});
test('events and farming remain uncapped and losses never restore decision allowance',()=>{
 const c=fresh();c.vars.RUS_nat_decision_score=90;c.vars.RUS_maximalist_land_reform_score=90;
 run(c,'RUS_maximalist_land_reform_add_score_10');assert.equal(c.vars.RUS_maximalist_land_reform_score,100);
 c.vars.RUS_agri_score_award=9;run(c,'RUS_agri_credit_score');assert.equal(c.vars.RUS_maximalist_land_reform_score,109);
 run(c,'RUS_maximalist_land_reform_subtract_score_3');run(c,'RUS_nat_decision_score_10');
 assert.equal(c.vars.RUS_maximalist_land_reform_score,106);assert.equal(c.vars.RUS_nat_decision_score,90);
});
test('other ministers retain unrestricted original decision awards',()=>{
 const c=country();c.flags.RUS_maximalist_land_reform_in_progress=true;
 for(let i=0;i<20;i++)run(c,'RUS_nat_decision_score_10');
 run(c,'RUS_nat_decision_score_5');assert.equal(c.vars.RUS_maximalist_land_reform_score,205);
 assert.equal(c.vars.RUS_nat_decision_score,undefined);
});
test('at the cap tractor promise progress and attached events still execute',()=>{
 const c=fresh();c.vars.RUS_nat_decision_score=90;c.vars.RUS_maximalist_land_reform_score=120;
 c.flags.RUS_max_landreform_tractor_promise_active=true;c.vars.RUS_max_landreform_tractor_promise_count=2;
 complete(c,get(decisions,'RUS_max_landreform_promote_tractors'));
 assert.equal(c.vars.RUS_max_landreform_tractor_promise_count,3);
 assert.equal(c.vars.RUS_maximalist_land_reform_score,120);assert.ok(c.events.length>0);
});
test('no-credit states do not consume allowance and success cannot bypass the cap',()=>{
 const c=fresh();delete c.flags.RUS_maximalist_land_reform_in_progress;
 run(c,'RUS_nat_decision_score_5');assert.equal(c.vars.RUS_nat_decision_score,0);
 c.flags.RUS_maximalist_land_reform_failure=true;run(c,'RUS_nat_decision_score_10');assert.equal(c.vars.RUS_nat_decision_score,0);
 delete c.flags.RUS_maximalist_land_reform_failure;c.flags.RUS_maximalist_land_reform_success=true;
 c.vars.RUS_maximalist_land_reform_score=150;c.vars.RUS_nat_decision_score=88;
 run(c,'RUS_nat_decision_score_5');assert.equal(c.vars.RUS_agri_spendable_score,2);
 run(c,'RUS_nat_decision_score_10');assert.equal(c.vars.RUS_agri_spendable_score,2);
 assert.equal(c.vars.RUS_maximalist_land_reform_score,150);assert.equal(c.vars.RUS_nat_decision_score,90);
});
test('the lifetime allowance survives quarterly resets, annual resets and serialization',()=>{
 let c=fresh();c.vars.RUS_nat_decision_score=88;
 run(c,'RUS_nat_start_quarter');c.vars.RUS_nat_year_supply=4;c.vars.RUS_nat_year_weight=4;run(c,'RUS_nat_annual');
 c=JSON.parse(JSON.stringify(c));run(c,'RUS_nat_enable');run(c,'RUS_nat_decision_score_5');
 assert.equal(c.vars.RUS_nat_decision_score,90);assert.equal(c.vars.RUS_maximalist_land_reform_score,2);
});
test('three locales include allowance and cap-reached text',()=>{
 for(const lang of ['simp_chinese','english','russian']){
  const text=read(`localisation/${lang}/RUS_national_agriculture_l_${lang}.yml`);
  for(const id of ['decision_score_line','decision_cap_full','decision_cap_open','decision_score_5_tt','decision_score_10_tt'])assert.equal([...text.matchAll(new RegExp('^ '+ 'RUS_nat_'+id+':','gm'))].length,1);
 }
});
console.log(count+' decision-cap regression groups passed; native save/load QA remains outstanding.');
