const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process');
const {parse,get,read,root,country,check,exec,effects}=require('./test_agri_development.cjs');
const gui=get(get(parse(read('common/scripted_guis/RUS_national_agriculture.txt')),'scripted_gui'),'RUS_national_agriculture_gui');
const panels=get(parse(read('common/scripted_guis/RUS_agriculture_order_panels.txt')),'scripted_gui');
const foreignPanel=get(panels,'RUS_agriculture_foreign_panel');
const allClickEffects=[...get(gui,'effects'),...get(foreignPanel,'effects')];
const baseline=get(get(parse(cp.execFileSync('git',['show','HEAD:common/scripted_guis/RUS_national_agriculture.txt'],{cwd:root,encoding:'utf8'})),'scripted_gui'),'RUS_national_agriculture_gui');
for(const entry of get(baseline,'effects')) assert.deepEqual(get(allClickEffects,entry.key),entry.value,'Preserve original effect '+entry.key);
for(const crop of ['wheat','rye','beet','flax','cotton']) {
 assert.deepEqual(get(get(gui,'effects'),`card_${crop}_add_click`),get(get(gui,'effects'),`nat_${crop}_plus_click`));
 assert.deepEqual(get(get(gui,'triggers'),`card_${crop}_add_click_enabled`),get(get(gui,'triggers'),`nat_${crop}_plus_click_enabled`));
}
const triggers=get(gui,'triggers'),c=country();
for(let p=0;p<=4;p++){
 c.vars.RUS_nat_page=p;
 const backgrounds=[1,2,3,4].filter(i=>check(get(triggers,`card_nav_selected_${i-1}_visible`),c));
 assert.deepEqual(backgrounds,[p===0?1:p]);
 assert.equal(check(get(triggers,'nat_wheat_plus_visible'),c),p<=1);
}
c.vars.RUS_nat_page=1;
for(const v of [0,1,5,10]){
 c.vars.RUS_agri_wheat_investment=v;
 assert.equal(Array.from({length:10},(_,i)=>check(get(triggers,`card_allocation_wheat_${i}_visible`),c)).filter(Boolean).length,v);
}
for(const lang of ['simp_chinese','english','russian']){
 const buf=fs.readFileSync(path.join(root,`localisation/${lang}/RUS_agriculture_cards_l_${lang}.yml`));assert.equal(buf.subarray(0,3).toString('hex'),'efbbbf');
 const keys=[...buf.toString('utf8').matchAll(/^\s+(\S+):0/gm)].map(m=>m[1]);assert.equal(keys.length,new Set(keys).size);
 for(const crop of ['wheat','rye','beet','flax','cotton'])assert.ok(buf.toString().includes(`[?RUS_agri_${crop}_fatigue|0]`),'Detailed live values must remain in tooltips');
 assert.ok(!/\$RUS_[\w.]+\$/.test(buf.toString()),'GUI localisation must not leave nested dollar references');
}
console.log('Dashboard: original click effects preserved; one page visible including unset page; allocation bars exact; three locales retain detailed tooltips.');

assert.ok(!/[<>]=/.test(read('common/scripted_guis/RUS_national_agriculture.txt')), 'Native HOI4 parser rejects inline >= and <= here; use NOT with the opposite strict comparison');

for(const lang of ['simp_chinese','english','russian']){
 const expanded=read(`localisation/replace/RUS_agriculture_expanded_l_${lang}.yml`);
 assert.ok(!/\$[\w.]+\$/.test(expanded));
 assert.ok(expanded.includes('RUS_nat_report_cotton:0'));
 assert.ok(expanded.includes('[?RUS_nat_cotton_last_yield|1]'));
}

for(const crop of ['wheat','rye','beet','flax','cotton']) for(const locked of [false,true]) for(const amount of [0,9,10]) for(const right of [false,true]) {
 const state=country();state.vars.RUS_agri_investment_limit=50;state.vars.RUS_nat_page=1;
 state.vars[`RUS_agri_${crop}_investment`]=amount;state.vars.RUS_nat_allocated=amount;
 if(locked)state.flags.RUS_agri_allocation_locked=true;
 exec(get(get(gui,'effects'),`card_${crop}_adjust_${right?'right_click':'click'}`),state);
 assert.equal(state.vars[`RUS_agri_${crop}_investment`],locked?amount:Math.max(0,Math.min(10,amount+(right?-1:1))));
}
console.log('Card left/right click: five crops, zero/cap boundaries and locked plans passed.');

{
 const state=country(); state.vars['global.num_days']=706699;state.civCapacity=100;
 exec(effects.get('RUS_nat_enable'),state);
 state.vars.RUS_nat_page=3;
 const crops=['wheat','rye','beet','flax','cotton'];const before=crops.map(k=>state.vars[`RUS_nat_${k}_stock`]);
 exec(get(get(gui,'effects'),'card_reserve_zero_click'),state);
 for(const group of ['food','beet','textile']) {
  assert.equal(state.vars[`RUS_nat_${group}_reserve`],0);
  assert.ok(Math.abs(state.vars[`RUS_nat_${group}_target_total`]-state.vars[`RUS_nat_${group}_need`]-state.vars[`RUS_nat_${group}_order_need`])<1e-5);
 }
 assert.deepEqual(crops.map(k=>state.vars[`RUS_nat_${k}_stock`]),before);
 assert.equal(check(get(triggers,'card_reserve_selected_0_visible'),state),true);
 for(let i=1;i<4;i++)assert.equal(check(get(triggers,`card_reserve_selected_${i}_visible`),state),false);
 exec(effects.get('RUS_nat_refresh'),state);assert.equal(state.vars.RUS_nat_reserve,0);
 exec(get(get(gui,'effects'),'nat_reserve_1_click'),state);assert.equal(state.vars.RUS_nat_reserve,1);
 console.log('Zero reserve: targets and ledger refresh, stock preserved, selection and switching back passed.');
}

const mainWindow=get(get(parse(read('interface/RUS_national_agriculture.gui')),'guiTypes'),'containerWindowType');
assert.ok(!mainWindow.some(n=>n.key==='containerWindowType'&&/card_orders_.*_scroll/.test(get(n.value,'name'))),'Native scroll backgrounds must not be nested unconditionally in the main page');
for(const part of ['domestic','foreign']){
 const panel=get(panels,`RUS_agriculture_${part}_panel`);assert.equal(get(panel,'parent_scripted_gui'),'RUS_national_agriculture_gui');
 for(let page=0;page<=4;page++)for(let category=0;category<=1;category++){
  const c=country();c.flags.RUS_nat_enabled=true;c.vars.RUS_nat_page=page;c.vars.RUS_nat_order_category=category;
  assert.equal(check(get(panel,'visible'),c),page===3&&category===(part==='foreign'?1:0));
 }
}
for(let row=0;row<10;row++){
 const c=country();c.temps.RUS_nat_order_row=row;
 for(let candidate=0;candidate<10;candidate++)assert.equal(check(get(get(foreignPanel,'triggers'),`card_order_${candidate}_card_visible`),c),candidate===row);
}
console.log('Native panel roots isolated across all pages/categories; one row variant visible at a time.');

const roots=get(parse(read('interface/RUS_national_agriculture.gui')),'guiTypes');
for(const part of ['domestic','foreign']){
 const window=roots.find(n=>get(n.value,'name')===`card_orders_${part}_scroll`).value;
 assert.equal(get(get(window,'position'),'y'),'0');
 const viewport=window.find(n=>n.key==='containerWindowType').value;
 assert.equal(get(viewport,'name'),`card_orders_${part}_viewport`);
 assert.equal(get(get(viewport,'position'),'x'),'10');assert.equal(get(get(viewport,'position'),'y'),'403');
 assert.equal(get(get(viewport,'size'),'height'),'156');assert.equal(get(viewport,'verticalScrollbar'),'right_vertical_slider');
}
console.log('Scroll viewports use explicit offsets inside zero-origin child roots.');
