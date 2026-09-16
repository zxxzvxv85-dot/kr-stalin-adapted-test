const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process');
const {parse,get,read,root,country,check}=require('./test_agri_development.cjs');
const gui=get(get(parse(read('common/scripted_guis/RUS_national_agriculture.txt')),'scripted_gui'),'RUS_national_agriculture_gui');
const baseline=get(get(parse(cp.execFileSync('git',['show','HEAD:common/scripted_guis/RUS_national_agriculture.txt'],{cwd:root,encoding:'utf8'})),'scripted_gui'),'RUS_national_agriculture_gui');
assert.deepEqual(get(gui,'effects'),get(baseline,'effects'),'Presentation must preserve every original click effect');
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
