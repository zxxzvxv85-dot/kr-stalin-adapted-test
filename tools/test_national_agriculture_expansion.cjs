const assert=require('node:assert/strict');
const {parse,get,effects,triggers,country,check,exec,read}=require('./test_agri_development.cjs');
const crops=['wheat','rye','beet','flax','cotton'];
const run=(c,k)=>exec(effects.get('RUS_nat_'+k),c);
const val=(c,k)=>c.vars['RUS_nat_'+k]||0;
const set=(c,k,v)=>c.vars['RUS_nat_'+k]=v;
const fresh=(doy=59)=>{const c=country();c.vars['global.num_days']=706640+doy;c.civCapacity=100;c.vars.num_of_civilian_factories_available_for_projects=100;run(c,'enable');return c;};
const day=c=>{c.vars['global.num_days']++;run(c,'daily');};
const plan=(c,total)=>{for(const k of crops){c.vars['RUS_agri_'+k+'_investment']=Math.min(total,10);total=Math.max(0,total-10);}c.flags.RUS_nat_manual_plan=true;run(c,'refresh');};
const near=(a,b)=>assert.ok(Math.abs(a-b)<1e-8,`${a} != ${b}`);
let count=0;const test=(name,f)=>{f();count++;console.log('PASS '+name);};
test('free budget and expansion boundary prices',()=>{
 const c=fresh();assert.equal(val(c,'budget'),10);assert.equal(val(c,'allocated'),10);
 for(const [amount,price] of [[0,0],[10,0],[11,.005],[15,.025],[16,.035],[20,.075],[50,.375]]){plan(c,amount);near(val(c,'expansion_preview'),price);assert.equal(val(c,'consumer'),0);}
 c.flags.RUS_maximalist_land_reform_success=true;c.flags.RUS_max_landreform_tractor_promise_kept=true;run(c,'start_quarter');assert.equal(val(c,'budget'),14);plan(c,15);near(val(c,'expansion_preview'),.005);
});
test('crop buttons cross free allowance but retain per-crop cap',()=>{
 const c=fresh();plan(c,10);exec(effects.get('RUS_agri_increase_rye'),c);assert.equal(val(c,'allocated'),11);
 for(let i=0;i<15;i++)exec(effects.get('RUS_agri_increase_rye'),c);
 assert.equal(c.vars.RUS_agri_rye_investment,10);assert.equal(val(c,'allocated'),20);
});
test('charge starts at boundary, survives reload, expires next boundary without stacking',()=>{
 let c=fresh(150);plan(c,20);near(val(c,'expansion_active'),0);day(c);near(val(c,'expansion_active'),.075);
 c=JSON.parse(JSON.stringify(c));plan(c,10);const end=val(c,'quarter_end');
 while(c.vars['global.num_days']<end-1){day(c);near(val(c,'expansion_active'),.075);}
 day(c);near(val(c,'expansion_active'),0);const snapshot=JSON.stringify(c);run(c,'daily');assert.equal(JSON.stringify(c),snapshot);
});
test('machinery coverage scales all crops 60 to 110 percent',()=>{
 const c=fresh();set(c,'elapsed',0);
 for(const [installed,factor] of [[0,.6],[100,.725],[200,.85],[400,1.1],[800,1.1]]){set(c,'installed',installed);run(c,'yield');near(val(c,'mechanisation'),factor);}
 set(c,'elapsed',10);set(c,'coverage_sum',2.5);set(c,'installed',400);run(c,'yield');near(val(c,'mechanisation'),.725);
});
test('beet weekly loss and textile penalties recover and stack with food',()=>{
 const c=fresh();plan(c,10);set(c,'food_ratio',1);set(c,'textile_ratio',1);
 for(const [ratio,weekly] of [[1,0],[.5,-.002],[0,-.004]]){set(c,'beet_ratio',ratio);run(c,'penalties');near(val(c,'beet_weekly'),weekly);}
 set(c,'textile_ratio',.5);run(c,'penalties');near(val(c,'stability'),-.06);near(val(c,'consumer'),.025);
 set(c,'food_ratio',0);for(let i=0;i<4;i++)run(c,'penalties');near(val(c,'stability'),-.12);near(val(c,'consumer'),.05);
 set(c,'food_ratio',1);set(c,'textile_ratio',1);set(c,'beet_ratio',1);for(let i=0;i<3;i++)run(c,'penalties');near(val(c,'stability'),0);near(val(c,'consumer'),0);near(val(c,'beet_weekly'),0);
 const dm=read('common/dynamic_modifiers/RUS_national_agriculture_modifiers.txt');assert.ok(dm.includes('stability_weekly = RUS_nat_beet_weekly'));assert.ok(!dm.includes('industrial_capacity_factory'));
});
test('4000 self-produced promise and 5000 warehouse preserve capacity',()=>{
 const c=fresh();c.vars.RUS_max_landreform_tractor_promise_count=3;
 for(const [amount,complete] of [[3999.999,false],[4000,true]]){set(c,'produced',amount);assert.equal(check(triggers.get('RUS_nat_tractor_complete'),c),complete);}
 set(c,'requested',10);run(c,'set_factories');set(c,'installed',400);set(c,'machine_stock',5000);const before=val(c,'produced');day(c);near(val(c,'produced'),before);
 set(c,'machine_stock',4999.9);day(c);near(val(c,'machine_stock'),5000);near(val(c,'produced'),before+.1);
});
const balkanTags=['SER','ROM','GRE','ALB','BUL'];
const buyers=(c,tags=balkanTags)=>{
 c.world=Object.fromEntries(tags.map(tag=>{const buyer=country();buyer.id=tag;buyer.flags.KR_is_socialist=true;return [tag,buyer];}));
};
test('Balkan countries create separate orders without increasing total procurement',()=>{
 for(const enabled of [false,true])for(const focus of [false,true]){
  const c=enabled?fresh():country();buyers(c);if(focus)c.focuses.push('RUS_future_foreign_019');run(c,'draw_orders');
  assert.equal(val(c,'generic_quantity'),0);
  for(const tag of balkanTags)assert.equal(val(c,tag.toLowerCase()+'_quantity'),enabled&&focus?1:0);
 }
 const c=fresh();buyers(c);c.focuses.push('RUS_future_foreign_002','RUS_future_foreign_017','RUS_future_foreign_019');c.countries=['FRA','ENG'];
 delete c.world.ROM.flags.KR_is_socialist;c.world.GRE.exists=false;run(c,'draw_orders');run(c,'refresh');
 assert.equal(val(c,'balkan_order_count'),3);assert.equal(val(c,'rom_quantity'),0);assert.equal(val(c,'gre_quantity'),0);
 assert.ok(val(c,'generic_quantity')>=2&&val(c,'generic_quantity')<=4);
 for(const tag of ['ser','alb','bul'])assert.equal(val(c,tag+'_quantity'),1);
 assert.deepEqual(c.arrays.RUS_nat_foreign_order_rows,[0,1,2,3,4,5,8,9]);
 const gui=get(get(parse(read('common/scripted_guis/RUS_national_agriculture.txt')),'scripted_gui'),'RUS_national_agriculture_gui');
 const before=val(c,'ser_accept');exec(get(get(gui,'effects'),'card_order_5_switch_click'),c);assert.equal(val(c,'ser_accept'),1-before);
 assert.equal(val(c,'alb_accept'),1);assert.equal(val(c,'bul_accept'),1);assert.equal(val(c,'generic_accept'),1);
 c.world={};run(c,'refresh');assert.equal(val(c,'ser_quantity'),1);
 run(c,'start_quarter');for(const tag of balkanTags)assert.equal(val(c,tag.toLowerCase()+'_quantity'),0);
});
test('Independent shipments respect domestic reserves and never pay twice',()=>{
 const c=fresh();buyers(c);c.focuses.push('RUS_future_foreign_019');run(c,'draw_orders');
 for(const tag of balkanTags)set(c,tag.toLowerCase()+'_crop',1);
 set(c,'actual',1);for(const g of ['food','beet','textile'])set(c,g+'_ratio',1);
 set(c,'food_reserve',8);set(c,'food_left',12);set(c,'wheat_work',12);c.vars.RUS_agri_wheat_capacity=100;c.vars.RUS_agri_wheat_market=0;
 set(c,'ser_accept',0);run(c,'trade');assert.equal(val(c,'ser_shipped'),0);assert.equal(val(c,'income'),4000);assert.equal(val(c,'wheat_work'),8);
 for(const tag of ['rom','gre','alb','bul'])assert.equal(val(c,tag+'_shipped'),1);
 run(c,'trade');assert.equal(val(c,'income'),0);
 set(c,'ser_accept',1);run(c,'trade');assert.equal(val(c,'ser_shipped'),0);
 set(c,'food_left',9);set(c,'wheat_work',9);run(c,'trade');assert.equal(val(c,'income'),1000);assert.equal(val(c,'ser_shipped'),1);assert.equal(val(c,'wheat_work'),8);
 run(c,'trade');assert.equal(val(c,'income'),0);
 const settled=fresh();buyers(settled);settled.focuses.push('RUS_future_foreign_019');run(settled,'draw_orders');
 for(const tag of balkanTags)set(settled,tag.toLowerCase()+'_crop',1);
 for(const crop of crops){settled.vars['RUS_agri_'+crop+'_investment']=0;set(settled,crop+'_stock',30);}
 set(settled,'elapsed',92);set(settled,'coverage_sum',92);run(settled,'settle');assert.equal(val(settled,'last_crop_orders'),5);
 const earned=settled.surplus;run(settled,'settle');assert.equal(settled.surplus,earned);
});
test('Balkan order generator and three locales preserve the implemented order contract',()=>{
 const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
 const root=path.resolve(__dirname,'..'),outputs=new Map();
 const fakeFs={...fs,mkdirSync(){},writeFileSync(file,text){outputs.set(path.relative(root,file).replaceAll('\\','/'),text);}};
 vm.runInNewContext(read('tools/generate_national_agriculture.cjs'),{__dirname,require:id=>id==='node:fs'?fakeFs:require(id),console:{log(){}}});
 const generated=get(parse(outputs.get('common/scripted_effects/RUS_national_agriculture_effects.txt')),'RUS_nat_draw_orders');
 assert.deepEqual(generated,effects.get('RUS_nat_draw_orders'));
 for(const language of ['simp_chinese','english','russian']){
  const file=`localisation/${language}/RUS_national_agriculture_l_${language}.yml`,text=read(file),keys=[...text.matchAll(/^\s+(\S+):\d*\s+"/gm)].map(m=>m[1]);
  assert.equal(text.charCodeAt(0),0xfeff);assert.equal(keys.length,new Set(keys).size);assert.ok(!text.includes('\ufffd'));
  for(const key of ['RUS_nat_generic_order','RUS_nat_balkan_order','RUS_nat_joint_order','RUS_nat_order_generic']){
   const pattern=new RegExp('^ '+key+':.*$','m');assert.equal(text.match(pattern)[0],outputs.get(file).match(pattern)[0]);
  }
  assert.ok(text.match(/^ RUS_nat_tab_2_tt:.*$/m)[0].includes(outputs.get(file).match(/^ RUS_nat_tab_2_tt:.*$/m)[0].split('\\n\\n£RUS_nat_text_export£').at(-1)));
 }
});
console.log(count+' expansion regression groups passed. Engine save/load QA remains outstanding.');
