const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {parse,get,root}=require('./test_agri_development.cjs');
const fonts=process.argv[2];assert.ok(fonts,'Pass installed gfx/fonts path');
const gui=get(get(parse(fs.readFileSync(path.join(root,'interface/RUS_national_agriculture.gui'),'utf8')),'guiTypes'),'containerWindowType');
const dimensions=JSON.parse(fs.readFileSync(path.join(root,'output/agri-gui/card-sprite-sizes.json'),'utf8'));
for(const widget of gui.filter(x=>['instantTextBoxType','buttonType','iconType'].includes(x.key))){
 const b=widget.value,pos=get(b,'position'),sprite=get(b,'quadTextureSprite')||get(b,'spriteType')||'',scale=+get(b,'scale')||1;
 const size=dimensions[sprite.replace('GFX_RUS_card_','')];
 const width=widget.key==='instantTextBoxType'?+get(b,'maxWidth'):size?size[0]:64*scale;
 const height=widget.key==='instantTextBoxType'?+get(b,'maxHeight'):size?size[1]:64*scale;
 assert.ok(+get(pos,'x')>=0&&+get(pos,'x')+width<=502,`${get(b,'name')} exceeds native decision width`);
 assert.ok(+get(pos,'y')>=0&&+get(pos,'y')+height<=625,`${get(b,'name')} exceeds page height`);
}
const defined=parse(fs.readFileSync(path.join(root,'common/scripted_localisation/RUS_national_agriculture_loc.txt'),'utf8'));
const widget = name => gui.find(w => Array.isArray(w.value) && get(w.value,'name') === name).value;
let errors=0;
for(const lang of ['simp_chinese','english','russian']){
 const metric=new Map();const files=lang==='simp_chinese'?fs.readdirSync(path.join(fonts,'chinese')).filter(f=>/^hoi_16mbs_.*\.fnt$/.test(f)).map(f=>path.join(fonts,'chinese',f)):[path.join(fonts,'hoi_16mbs.fnt'),...(lang==='russian'?[path.join(fonts,'hoi_16mbs_cryllic.fnt')]:[])];
 for(const file of files)for(const line of fs.readFileSync(file,'utf8').split(/\r?\n/).filter(l=>l.startsWith('char '))){const pairs=Object.fromEntries([...line.matchAll(/(\w+)=\s*(-?\d+)/g)].map(m=>[m[1],+m[2]]));metric.set(pairs.id,pairs.xadvance);}
 const loc=new Map();for(const stem of ['RUS_national_agriculture','RUS_agricultural_quarterly_management','RUS_agri_development','RUS_agriculture_dashboard','RUS_agriculture_cards'])for(const m of fs.readFileSync(path.join(root,'localisation',lang,`${stem}_l_${lang}.yml`),'utf8').matchAll(/^\s*([\w.]+):(?:0)?\s*"(.*)"$/gm))loc.set(m[1],m[2]);
 const width=t=>[...t.replace(/§./g,'')].reduce((s,c)=>s+(metric.get(c.codePointAt(0))||8),0);
 const countryNames={simp_chinese:['法兰西公社','不列颠联盟'],english:['Commune of France','Union of Britain'],russian:['Французская коммуна','Британский Союз']}[lang];
 function expand(t,depth=0){if(depth>5)return '';return t.replace(/\[(FRA|ENG)\.GetName\]/g,(_,tag)=>countryNames[tag==='FRA'?0:1]).replace(/\$([\w.]+)\$/g,(_,k)=>expand(loc.get(k)||k,depth+1)).replace(/\[\?([^|]+)\|(%?)(\d)\]/g,(_,key,pct,d)=>pct?'-100%':/(?:_preview|_last_ratio)$/.test(key)?'100.00':key.includes('produced')?'99999':key.includes('income')?'99000':key.includes('stock')?'4500.0':d==='0'?'100':d==='1'?'100.0':'1.25').replace(/\[([^\]]+)\]/g,(_,name)=>{const block=defined.find(n=>get(n.value,'name')===name);if(!block)return '';return block.value.filter(n=>n.key==='text').map(n=>expand(loc.get(get(n.value,'localization_key'))||'',depth+1)).sort((a,b)=>width(b)-width(a))[0]||'';});}
 for(const widget of gui.filter(x=>['instantTextBoxType','buttonType'].includes(x.key))){const b=widget.value;const key=get(b,widget.key==='buttonType'?'buttonText':'text');if(!key)continue;assert.ok(loc.has(key),`${lang}: missing ${key}`);const text=expand(loc.get(key));const limit=widget.key==='buttonType'?(dimensions[(get(b,'quadTextureSprite')||'').replace('GFX_RUS_card_','')]?.[0]||123)-8:+get(b,'maxWidth');const measured=Math.max(...text.split('\\n').map(width))*(get(b,'font')==='hoi_24header'?1.5:1);if(measured>limit){console.log('OVERFLOW',lang,key,measured,limit,text);errors++;}const pos=get(b,'position');assert.ok(+get(pos,'y')+(widget.key==='buttonType'?34:+get(b,'maxHeight'))<=625);}
}
assert.equal(errors,0,'Native-font text overflows');console.log('National agriculture native-font layout checks passed in three languages; not a runtime screenshot test.');
