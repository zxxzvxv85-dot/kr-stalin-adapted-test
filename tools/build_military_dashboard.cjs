// Rebuild layout from measured assets. Preserve the actual stage click effects.
const fs=require('fs'),path=require('path');
const {parse,get}=require('./test_agri_development.cjs');
const root=path.resolve(__dirname,'..'),read=p=>fs.readFileSync(path.join(root,p),'utf8');
const write=(p,s)=>fs.writeFileSync(path.join(root,p),s,'utf8');
const sgPath='common/scripted_guis/RUS_fr_military_reform_dashboard.txt';
const original=get(parse(read(sgPath)),'scripted_gui');
const old=original[0].value,oldTriggers=get(old,'triggers');
function dump(ns){return ns.map(n=>n.key+' '+(n.op||'=')+' '+(Array.isArray(n.value)?'{ '+dump(n.value)+' }':n.value)).join('\n');}
const prefix='RUS_fr_dashboard_',widgets=[],conditions=[],sprites=[],layout=[];
function icon(id,x,y,sprite,w,h,condition){
 widgets.push(`iconType = { name = "${id}" position = { x = ${x} y = ${y} } spriteType = "${sprite}" alwaystransparent = yes }`);
 layout.push({kind:'icon',id,x,y,w,h,sprite});if(condition)conditions.push(`${id}_visible = { ${condition} }`);
}
function text(id,x,y,w,h,key,font='hoi_16mbs',condition){
 widgets.push(`instantTextBoxType = { name = "${id}" position = { x = ${x} y = ${y} } font = "${font}" text = "${key}" format = center maxWidth = ${w} maxHeight = ${h} fixedsize = yes alwaystransparent = yes }`);
 layout.push({kind:'text',id,x,y,w,h,key,font});if(condition)conditions.push(`${id}_visible = { ${condition} }`);
}
function sprite(name,file,frames=1){sprites.push(`spriteType = { name = "${name}" texturefile = "gfx/interface/rus_fr_dashboard/cards/${file}.png" noOfFrames = ${frames} legacy_lazy_load = no }`);}
sprite('GFX_RUS_fr_console','console');
icon(prefix+'console',0,0,'GFX_RUS_fr_console',498,490);
text(prefix+'title',20,10,458,25,'RUS_fr_console_title','hoi_20b');
text(prefix+'subtitle',20,36,458,21,'RUS_fr_console_subtitle');
// Progress retains the original 158px native bar and dynamic x/frame bindings.
widgets.push(`containerWindowType = { name = "RUS_fr_dashboard_reform_progress_clip" position = { x = 20 y = 66 } size = { width = 158 height = 14 } clipping = yes
 iconType = { name = "RUS_fr_dashboard_reform_progressbar" position = { x = 0 y = 0 } spriteType = "GFX_unit_limit_progressbar" alwaystransparent = yes }
}`);
widgets.push(`iconType = { name = "RUS_fr_console_complete_bar" position = { x = 20 y = 66 } spriteType = "GFX_unit_limit_progressbar" frame = 1 alwaystransparent = yes }`);
conditions.push(`RUS_fr_console_complete_bar_visible = { ${dump(get(oldTriggers,prefix+'reform_progress_complete_visible'))} }`);
for(const suffix of ['idle','complete','stage_1','stage_2','stage_3','stage_4']){
 const id=prefix+'reform_progress_'+suffix;
 text(id,190,61,290,24,id,'hoi_16mbs',dump(get(oldTriggers,id+'_visible')));
}
const zh=['指挥体系整肃','编制与军政关系','训练与战役协同','全国实兵检验'];
const en=['Command reform','Army organisation','Training & coordination','National field trials'];
const ru=['Реформа командования','Организация армии','Подготовка и координация','Полевые испытания'];
const loc={simp_chinese:{},english:{},russian:{}};
function label(key,a,b,c){for(const [lang,value] of [['simp_chinese',a],['english',b],['russian',c]])loc[lang][key]=value;return key;}
label('RUS_fr_console_title','全国军事改革','NATIONAL MILITARY REFORM','ВОЕННАЯ РЕФОРМА');
label('RUS_fr_console_subtitle','国家军事委员会 · 四阶段改革纲领','Military Committee · Four-stage programme','Военный комитет · Четыре этапа');
label('RUS_fr_card_ready','§G点击启动改革§!','§GCLICK TO BEGIN§!','§GНАЧАТЬ РЕФОРМУ§!');
label('RUS_fr_card_locked','§L尚未解锁§!','§LLOCKED§!','§LНЕДОСТУПНО§!');
label('RUS_fr_card_waiting','§Y条件不足 · 悬停查看§!','§YREQUIREMENTS NOT MET§!','§YУСЛОВИЯ НЕ ВЫПОЛНЕНЫ§!');
label('RUS_fr_card_active','§Y进行中 · 剩余 [?RUS_fr_dashboard_reform_days_remaining|0] 日§!','§YIN PROGRESS · [?RUS_fr_dashboard_reform_days_remaining|0] days§!','§YОСТАЛОСЬ [?RUS_fr_dashboard_reform_days_remaining|0] дн.§!');
label('RUS_fr_card_done','§G改革已完成§!','§GCOMPLETED§!','§GЗАВЕРШЕНО§!');
for(let i=1;i<=4;i++){
 const x=10+(i-1)%2*244,y=94+Math.floor((i-1)/2)*151;
 const id=prefix+'stage_'+i,word=['one','two','three','four'][i-1];
 const ready=`RUS_fr_can_start_reform_stage_${word} = yes`;
 const done=dump(get(oldTriggers,id+'_complete_visible')||get(oldTriggers,id+'_done_frame_visible'));
 const active=`NOT = { ${done} } has_country_flag = RUS_fr_reform_stage_${i}_in_progress`;
 const focus=['RUS_fr_military_rectification','RUS_fr_unified_military_political_system','RUS_fr_national_military_reform_program','RUS_fr_national_military_reform_program'][i-1];
 const unlocked=`has_completed_focus = ${focus} `+(i>1?`has_country_flag = RUS_fr_reform_stage_${i-1}`:'');
 const idle=`NOT = { ${done} } NOT = { has_country_flag = RUS_fr_reform_stage_${i}_in_progress } NOT = { ${ready} }`;
 sprite('GFX_RUS_fr_card_'+i,'card_'+i,3);
 widgets.push(`buttonType = { name = "${id}_button" position = { x = ${x} y = ${y} } quadTextureSprite = "GFX_RUS_fr_card_${i}" buttonText = "" buttonFont = "hoi_16mbs" clicksound = click_default pdx_tooltip = "${id}_tt" }`);
 layout.push({kind:'button',id:id+'_button',x,y,w:234,h:141,sprite:'GFX_RUS_fr_card_'+i});
 conditions.push(`${id}_button_click_enabled = { ${ready} }`);
 for(const state of ['ready','active','done']){
  if(i===1)sprite('GFX_RUS_fr_card_'+state,state);
  icon(id+'_'+state+'_frame',x,y,'GFX_RUS_fr_card_'+state,234,141,{ready,active,done}[state]);
 }
 sprite('GFX_RUS_fr_emblem_'+i,'emblem_'+i);
 icon(id+'_emblem',x+10,y+37,'GFX_RUS_fr_emblem_'+i,86,77);
 const title=label('RUS_fr_card_title_'+i,`${i}  ${zh[i-1]}`,`${i}  ${en[i-1]}`,`${i}  ${ru[i-1]}`);
 text(id+'_title',x+8,y+8,218,24,title);
 const cost=label('RUS_fr_card_cost_'+i,'陆军经验\n§Y[?RUS_fr_xp_cost_100|0]§!\n用时 '+(i<3?120:90)+' 日','Army experience\n§Y[?RUS_fr_xp_cost_100|0]§!\n'+(i<3?120:90)+' days','Опыт армии\n§Y[?RUS_fr_xp_cost_100|0]§!\n'+(i<3?120:90)+' дн.');
 text(id+'_cost',x+103,y+41,122,65,cost);
 for(const [state,cond] of Object.entries({done,active,ready,locked:`${idle} NOT = { ${unlocked} }`,waiting:`${idle} ${unlocked}`}))text(id+'_status_'+state,x+6,y+115,222,23,'RUS_fr_card_'+state,'hoi_16mbs',cond);
}
text(prefix+'obstacles_header',12,404,226,22,'RUS_fr_dashboard_obstacles_header');
text(prefix+'achievements_header',258,404,226,22,'RUS_fr_dashboard_achievements_header');
for(const t of oldTriggers){
 if(/^RUS_fr_dashboard_(obstacles|achievements)_.+_visible$/.test(t.key)){
  const id=t.key.slice(0,-8),x=id.includes('obstacles')?12:258;
  text(id,x,427,226,60,id,'hoi_16mbs',dump(t.value));
 }
}
write('interface/RUS_fr_military_reform_dashboard.gui',`guiTypes = { containerWindowType = { name = "RUS_fr_military_reform_dashboard_window" position = { x = 0 y = 0 } size = { width = 498 height = 490 } clipping = yes\n${widgets.join('\n')}\n} }\n`);
write('interface/RUS_fr_military_reform_cards.gfx',`spriteTypes = {\n${sprites.join('\n')}\n}\n`);
write(sgPath,`scripted_gui = { RUS_fr_military_reform_dashboard = { context_type = decision_category window_name = "RUS_fr_military_reform_dashboard_window"\nproperties = { ${dump(get(old,'properties'))} }\ntriggers = { ${conditions.join('\n')} }\neffects = { ${dump(get(old,'effects'))} }\n} }\n`);
for(const [lang,entries] of Object.entries(loc))write(`localisation/${lang}/RUS_fr_military_reform_cards_l_${lang}.yml`,'\ufeffl_'+lang+':\n'+Object.entries(entries).map(([k,v])=>' '+k+':0 "'+v.replaceAll('\n','\\n')+'"').join('\n')+'\n');
fs.mkdirSync(path.join(root,'output/military-dashboard'),{recursive:true});
write('output/military-dashboard/layout.json',JSON.stringify(layout,null,2));
console.log('Console layout built: 498x490; four 234x141 hit areas; original effects preserved.');
