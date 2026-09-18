const assert=require('node:assert/strict'),fs=require('fs'),cp=require('child_process');
const {parse,get}=require('./test_agri_development.cjs');
const file='common/scripted_guis/RUS_fr_military_reform_dashboard.txt';
const current=get(parse(fs.readFileSync(file,'utf8')),'scripted_gui')[0].value;
const previous=get(parse(cp.execFileSync('git',['show','ccbb684:'+file],{encoding:'utf8'})),'scripted_gui')[0].value;
assert.deepEqual(get(current,'effects'),get(previous,'effects'),'Original guarded click effects must remain byte-semantically identical');
assert.deepEqual(get(current,'properties'),get(previous,'properties'));
const tr=get(current,'triggers');
const defs=parse(fs.readFileSync('common/scripted_triggers/RUS_fr_military_reform_dashboard_triggers.txt','utf8'));
function check(block,c){return block.every(n=>{
 if(['AND'].includes(n.key))return check(n.value,c);
 if(n.key==='OR')return n.value.some(x=>check([x],c));
 if(n.key==='NOT')return !check(n.value,c);
 if(n.key==='has_country_flag')return c.flags.has(n.value);
 if(n.key==='has_completed_focus')return c.focuses.has(n.value);
 if(n.key==='has_idea')return c.ideas.has(n.value);
 if(n.key==='has_dynamic_modifier')return c.final;
 if(n.key==='has_army_experience')return c.xp<100;
 const v=get(defs,n.key);assert.ok(v,'Unknown trigger '+n.key);return check(v,c);
});}
let count=0;
for(let stage=0;stage<=4;stage++)for(let progress=0;progress<=4;progress++)for(const xp of [0,99,100,150])for(const focus of [false,true])for(const final of [false,true]){
 const c={flags:new Set(),focuses:new Set(),ideas:new Set(['RUS_fr_reform_disorganisation_'+(4-stage)]),xp,final};
 for(let j=1;j<=stage;j++)c.flags.add('RUS_fr_reform_stage_'+j);
 if(progress)c.flags.add('RUS_fr_reform_stage_'+progress+'_in_progress');
 if(focus)for(const k of ['military_rectification','unified_military_political_system','national_military_reform_program'])c.focuses.add('RUS_fr_'+k);
 for(let i=1;i<=4;i++){
  const p='RUS_fr_dashboard_stage_'+i;
  const visible=['done','active','ready','locked','waiting'].filter(s=>check(get(tr,p+'_status_'+s+'_visible'),c));
  assert.equal(visible.length,1,JSON.stringify({stage,progress,xp,focus,final,i,visible}));
  assert.equal(check(get(tr,p+'_button_click_enabled'),c),visible[0]==='ready');
 }
 count++;
}
const gui=get(parse(fs.readFileSync('interface/RUS_fr_military_reform_dashboard.gui','utf8')),'guiTypes')[0].value;
const children=gui.filter(n=>Array.isArray(n.value)&&get(n.value,'name'));
const ids=children.map(n=>get(n.value,'name'));assert.equal(ids.length,new Set(ids).size);
for(const node of children){
 const b=node.value,pos=get(b,'position'),x=Number(get(pos,'x')),y=Number(get(pos,'y'));
 if(node.key==='buttonType'){assert.ok(x>=0&&x+234<=498);assert.ok(y>=0&&y+141<=490);}
 if(node.key==='instantTextBoxType'){assert.ok(x+Number(get(b,'maxWidth'))<=498);assert.ok(y+Number(get(b,'maxHeight'))<=490);assert.ok(['hoi_16mbs','hoi_20b'].includes(get(b,'font')));}
}
const clickers=children.filter(n=>n.key==='buttonType');assert.equal(clickers.length,4);
for(let i=0;i<4;i++)for(let j=i+1;j<4;j++){
 const a=get(clickers[i].value,'position'),b=get(clickers[j].value,'position');
 assert.ok(Math.abs(Number(get(a,'x'))-Number(get(b,'x')))>=234||Math.abs(Number(get(a,'y'))-Number(get(b,'y')))>=141);
}
for(const lang of ['simp_chinese','english','russian']){
 const s=fs.readFileSync(`localisation/${lang}/RUS_fr_military_reform_cards_l_${lang}.yml`,'utf8');assert.equal(s.charCodeAt(0),0xfeff);
 const keys=[...s.matchAll(/^ ([\w.]+):/gm)].map(x=>x[1]);assert.equal(keys.length,new Set(keys).size);
}
console.log(count+' state combinations: exclusive status, availability matching, effects preserved, four non-overlapping hit areas inside 498px, fonts and locales passed.');
