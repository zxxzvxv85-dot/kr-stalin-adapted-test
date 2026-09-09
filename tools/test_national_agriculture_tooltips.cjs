const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {execFileSync} = require('node:child_process');
const {parse, get, root} = require('./test_agri_development.cjs');
const read = file => fs.readFileSync(path.join(root,file),'utf8');
const entries = text => [...text.matchAll(/^\s*([\w.]+):(?:0)?\s*"(.*)"$/gm)].map(m=>[m[1],m[2]]);
const plain = text => text.replace(/§./g,'').replace(/£[^£]+£/g,'').replace(/\\n/g,' ').replace(/\s+/g,' ')
  .replace('。 每厂日产 = 1.20 × 效率 × 产出系数 ', '，日产为每厂1.20×效率×产出系数。')
  .replace('Daily output per factory = 1.20 x efficiency x output factor ', 'Daily output per factory is 1.20 x efficiency x output factor. ')
  .replace('Выпуск завода в сутки = 1,20 x эффективность x коэффициент выпуска ', 'Выпуск одного завода в сутки: 1,20 x эффективность x коэффициент выпуска. ')
  .replace(/\s+/g,' ').trim();
const sprites = new Map(get(parse(read('interface/RUS_national_agriculture.gfx')),'spriteTypes').map(s=>[get(s.value,'name'),get(s.value,'texturefile')]));
const gui = get(get(parse(read('interface/RUS_national_agriculture.gui')),'guiTypes'),'containerWindowType');
for (const lang of ['simp_chinese','english','russian']) {
  const file = `localisation/${lang}/RUS_national_agriculture_l_${lang}.yml`;
  const content = read(file), pairs = entries(content), loc = new Map(pairs);
  assert.equal(content.charCodeAt(0),0xfeff,'UTF-8 BOM required');
  assert.equal(pairs.length,loc.size,'Duplicate localization key');
  const previous = new Map(entries(execFileSync('git',['show',`HEAD:${file}`],{cwd:root,encoding:'utf8'})));
  for (const [key,value] of loc) {
    let open = false;
    for (const marker of value.matchAll(/§(.)/g)) {
      if(marker[1]==='!') { assert.ok(open,`${lang} ${key}: unmatched reset`); open=false; }
      else { assert.ok(!open,`${lang} ${key}: nested color`); open=true; }
    }
    assert.ok(!open,`${lang} ${key}: unclosed color`);
    assert.ok(!value.includes('undefined'));
    for (const icon of value.matchAll(/£([^£]+)£/g)) {
      const texture = sprites.get('GFX_'+icon[1]);
      assert.ok(texture,`${lang} ${key}: unknown text icon ${icon[1]}`);
      assert.ok(fs.existsSync(path.join(root,texture)),texture);
    }
    if(previous.has(key) && !/^RUS_nat_(task_3|reserve_[012]|(?:m?order)_(?:fra|eng))$/.test(key)) {
      assert.equal(plain(value),plain(previous.get(key)),`${lang} ${key}: unintended rule/text change`);
    }
  }
  for (let i=0;i<4;i++) {
    const value=loc.get(`RUS_nat_tab_${i}_tt`);
    for (const marker of ['§4','§Y','§R','£RUS_nat_text_','\\n\\n']) assert.ok(value.includes(marker),`${lang}: unstyled tooltip ${i}`);
  }
  for (let i=0;i<3;i++) {
    const button=gui.find(w=>w.key==='buttonType'&&get(w.value,'name')===`nat_reserve_${i}`);
    assert.equal(get(button.value,'pdx_tooltip'),`RUS_nat_reserve_${i}_tt`);
    assert.ok(loc.get(`RUS_nat_reserve_${i}_tt`).includes('25%'));
  }
}
console.log('Tooltip checks passed: three locales, preserved mechanics text, colors, icons, reserve bindings and BOM/unique keys.');
