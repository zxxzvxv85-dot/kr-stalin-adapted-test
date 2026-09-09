const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {parse,get,root}=require('./test_agri_development.cjs');
const fonts=process.argv[2];assert.ok(fonts,'Pass installed gfx/fonts path');
const gui=get(get(parse(fs.readFileSync(path.join(root,'interface/RUS_national_agriculture.gui'),'utf8')),'guiTypes'),'containerWindowType');
for(const widget of gui.filter(x=>['instantTextBoxType','buttonType','iconType'].includes(x.key))){
 const b=widget.value,pos=get(b,'position'),sprite=get(b,'quadTextureSprite')||get(b,'spriteType')||'';
 const width=widget.key==='instantTextBoxType'?+get(b,'maxWidth'):widget.key==='buttonType'?(sprite.includes('naval_')?33:123):sprite.includes('crop_')?32:24;
 const height=widget.key==='instantTextBoxType'?+get(b,'maxHeight'):widget.key==='buttonType'?(sprite.includes('naval_')?33:34):width;
 assert.ok(+get(pos,'x')>=0&&+get(pos,'x')+width<=502,`${get(b,'name')} exceeds native 502px decision grid`);
 assert.ok(+get(pos,'y')>=0&&+get(pos,'y')+height<=625,`${get(b,'name')} exceeds page height`);
}
const defined=parse(fs.readFileSync(path.join(root,'common/scripted_localisation/RUS_national_agriculture_loc.txt'),'utf8'));
const widget = name => gui.find(w => Array.isArray(w.value) && get(w.value,'name') === name).value;
for (const crop of ['wheat','rye','beet','flax','cotton']) {
 const amount=widget(`nat_${crop}_amount`),minus=get(widget(`nat_${crop}_minus`),'position'),plus=get(widget(`nat_${crop}_plus`),'position'),pos=get(amount,'position');
 assert.equal(get(amount,'format'),'center');
 assert.equal(+get(pos,'x'),+get(minus,'x')+33);
 assert.equal(+get(pos,'x') + +get(amount,'maxWidth'),+get(plus,'x'));
 // hoi_16mbs digits have yoffset 2 and a 13px glyph, including their shadow.
 assert.equal(+get(pos,'y')+2+13/2,+get(minus,'y')+33/2);
 const soil=widget(`nat_${crop}_soil`);
 assert.ok(+get(get(soil,'position'),'y') >= +get(minus,'y')+33);
 assert.ok(+get(get(soil,'position'),'x') + +get(soil,'maxWidth') < +get(get(widget(`nat_${crop}_market`),'position'),'x'));
}
for (const [above,below] of [['nat_needs','nat_task'],['nat_task','nat_next'],['nat_next','nat_preview_income'],['nat_preview_income','nat_auto']]) {
 const a=widget(above),b=widget(below);
 assert.ok(+get(get(a,'position'),'y') + +get(a,'maxHeight') <= +get(get(b,'position'),'y'));
}
let errors=0;
for(const lang of ['simp_chinese','english','russian']){
 const metric=new Map();const files=lang==='simp_chinese'?fs.readdirSync(path.join(fonts,'chinese')).filter(f=>/^hoi_16mbs_.*\.fnt$/.test(f)).map(f=>path.join(fonts,'chinese',f)):[path.join(fonts,'hoi_16mbs.fnt'),...(lang==='russian'?[path.join(fonts,'hoi_16mbs_cryllic.fnt')]:[])];
 for(const file of files)for(const line of fs.readFileSync(file,'utf8').split(/\r?\n/).filter(l=>l.startsWith('char '))){const pairs=Object.fromEntries([...line.matchAll(/(\w+)=\s*(-?\d+)/g)].map(m=>[m[1],+m[2]]));metric.set(pairs.id,pairs.xadvance);}
 const loc=new Map();for(const stem of ['RUS_national_agriculture','RUS_agricultural_quarterly_management','RUS_agri_development'])for(const m of fs.readFileSync(path.join(root,'localisation',lang,`${stem}_l_${lang}.yml`),'utf8').matchAll(/^\s*([\w.]+):(?:0)?\s*"(.*)"$/gm))loc.set(m[1],m[2]);
 const width=t=>[...t.replace(/§./g,'')].reduce((s,c)=>s+(metric.get(c.codePointAt(0))||8),0);
 const countryNames={simp_chinese:['法兰西公社','不列颠联盟'],english:['Commune of France','Union of Britain'],russian:['Французская коммуна','Британский Союз']}[lang];
 function expand(t,depth=0){if(depth>5)return '';return t.replace(/\[(FRA|ENG)\.GetName\]/g,(_,tag)=>countryNames[tag==='FRA'?0:1]).replace(/\$([\w.]+)\$/g,(_,k)=>expand(loc.get(k)||k,depth+1)).replace(/\[\?([^|]+)\|(%?)(\d)\]/g,(_,key,pct,d)=>pct?'-100%':key.includes('produced')?'99999':key.includes('income')?'99000':key.includes('stock')?'4500.0':d==='0'?'100':d==='1'?'100.0':'1.25').replace(/\[([^\]]+)\]/g,(_,name)=>{const block=defined.find(n=>get(n.value,'name')===name);if(!block)return '';return block.value.filter(n=>n.key==='text').map(n=>expand(loc.get(get(n.value,'localization_key'))||'',depth+1)).sort((a,b)=>width(b)-width(a))[0]||'';});}
 for(const widget of gui.filter(x=>['instantTextBoxType','buttonType'].includes(x.key))){const b=widget.value;const key=get(b,widget.key==='buttonType'?'buttonText':'text');if(!key)continue;assert.ok(loc.has(key),`${lang}: missing ${key}`);const text=expand(loc.get(key));const limit=widget.key==='buttonType'?115:+get(b,'maxWidth');const measured=width(text);if(measured>limit){console.log('OVERFLOW',lang,key,measured,limit,text);errors++;}const pos=get(b,'position');assert.ok(+get(pos,'y')+(widget.key==='buttonType'?34:+get(b,'maxHeight'))<=625);}
}
assert.equal(errors,0,'Native-font text overflows');console.log('National agriculture native-font layout checks passed in three languages; not a runtime screenshot test.');
