// Offline proof from the actual GUI definitions and a simulated save, not a game screenshot.
const fs=require('node:fs'),path=require('node:path');
const {parse,get,read,root,country,exec,effects,check}=require('./test_agri_development.cjs');
const c=country();c.vars['global.num_days']=706699;c.civCapacity=24;c.vars.num_of_civilian_factories_available_for_projects=24;
c.flags.RUS_first_five_year_plan_mission_started=true;c.flags.RUS_maximalist_land_reform_in_progress=true;
c.focuses=['RUS_future_foreign_002','RUS_future_foreign_017'];c.countries=['ENG','FRA'];
exec(effects.get('RUS_nat_enable'),c);c.vars.RUS_nat_requested=8;exec(effects.get('RUS_nat_set_factories'),c);
for(let d=1;d<=196;d++){c.vars['global.num_days']++;c.vars.RUS_first_five_year_plan_score=d/5;exec(effects.get('RUS_nat_daily'),c);}
exec(effects.get('RUS_nat_auto_allocate'),c);
const locale=process.argv[2]||'simp_chinese',loc=new Map();
for(const stem of ['RUS_national_agriculture','RUS_agricultural_quarterly_management','RUS_agri_development'])for(const m of read(`localisation/${locale}/${stem}_l_${locale}.yml`).matchAll(/^\s*([\w.]+):(?:0)?\s*"(.*)"$/gm))loc.set(m[1],m[2]);
const definitions=parse(read('common/scripted_localisation/RUS_national_agriculture_loc.txt'));
function resolve(text,depth=0){if(depth>8)return '';
 return text.replace(/\$([\w.]+)\$/g,(_,key)=>resolve(loc.get(key)||key,depth+1)).replace(/\[\?([^|]+)\|(%?)(\d)\]/g,(_,key,pct,d)=>((c.vars[key]||0)*(pct?100:1)).toFixed(+d)+(pct?'%':'')).replace(/\[([^\]]+)\]/g,(_,key)=>{const b=definitions.find(b=>get(b.value,'name')===key);if(!b)return '';const t=b.value.find(t=>t.key==='text'&&(!get(t.value,'trigger')||check(get(t.value,'trigger'),c)));return resolve(loc.get(get(t?.value||[],'localization_key'))||'',depth+1);}).replace(/§./g,'').replace(/\\n/g,'\n');
}
const gui=get(get(parse(read('interface/RUS_national_agriculture.gui')),'guiTypes'),'containerWindowType');
const scripted=get(get(parse(read('common/scripted_guis/RUS_national_agriculture.txt')),'scripted_gui'),'RUS_national_agriculture_gui');
const triggers=get(scripted,'triggers');const sprites={};
for(const file of ['interface/RUS_agri_crop_icons.gfx','interface/RUS_national_agriculture.gfx'])for(const sprite of get(parse(read(file)),'spriteTypes')){const texture=get(sprite.value,'texturefile')||get(sprite.value,'textureFile');if(texture)sprites[get(sprite.value,'name')]=texture;}
const pages=[];
for(let page=1;page<=4;page++){
 c.vars.RUS_nat_page=page;const widgets=[];
 for(const w of gui.filter(w=>['iconType','instantTextBoxType','buttonType'].includes(w.key))){const name=get(w.value,'name');const visible=get(triggers,name+'_visible');if(visible&&!check(visible,c))continue;
 const pos=get(w.value,'position');const key=get(w.value,'text')||get(w.value,'buttonText');const sprite=get(w.value,'spriteType')||get(w.value,'quadTextureSprite');const enabled=get(triggers,name+'_click_enabled');
 widgets.push({kind:w.key,name,x:+get(pos,'x'),y:+get(pos,'y'),width:+get(w.value,'maxWidth')||123,height:+get(w.value,'maxHeight')||34,format:get(w.value,'format'),text:key?resolve(loc.get(key)||key):sprite?.includes('decrease')?'-':sprite?.includes('increase')?'+':'',sprite:sprites[sprite],scale:+get(w.value,'scale')||1,enabled:!enabled||check(enabled,c)});
 }
 pages.push(widgets);
}
const out=path.join(root,'output/national-agriculture');fs.mkdirSync(out,{recursive:true});fs.writeFileSync(path.join(out,`layout-${locale}.json`),JSON.stringify({locale,pages},null,2));console.log('Saved four-page offline layout state for '+locale);
