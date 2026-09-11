const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {execFileSync} = require('node:child_process');
const {parse, get, root} = require('./test_agri_development.cjs');
const {chinesePresentation} = require('./national_agriculture_tooltip_style.cjs');
const read = file => fs.readFileSync(path.join(root,file),'utf8');
const entries = text => [...text.matchAll(/^\s*([\w.]+):(?:0)?\s*"(.*)"$/gm)].map(m=>[m[1],m[2]]);
const plain = text => text.replace(/§./g,'').replace(/£[^£]+£/g,'').replace(/\\n/g,' ').replace(/\s+/g,' ')
  .replace('。 每厂日产 = 1.20 × 效率 × 产出系数 ', '，日产为每厂1.20×效率×产出系数。')
  .replace('Daily output per factory = 1.20 x efficiency x output factor ', 'Daily output per factory is 1.20 x efficiency x output factor. ')
  .replace('Выпуск завода в сутки = 1,20 x эффективность x коэффициент выпуска ', 'Выпуск одного завода в сутки: 1,20 x эффективность x коэффициент выпуска. ')
  .replace(/\s+/g,' ').trim();
const sprites = new Map(get(parse(read('interface/RUS_national_agriculture.gfx')),'spriteTypes').map(s=>[get(s.value,'name'),get(s.value,'texturefile')]));
const gui = get(get(parse(read('interface/RUS_national_agriculture.gui')),'guiTypes'),'containerWindowType');
const balanceChanges=new Set(['RUS_nat_header','RUS_nat_score_line','RUS_nat_tab_1_tt','RUS_nat_tab_3_tt','RUS_nat_machine_2','RUS_nat_machine_3','RUS_nat_machine_4','RUS_nat_machine_5','RUS_nat_tractor_requirement','RUS_national_agriculture.2.d']);
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
    if(previous.has(key) && !balanceChanges.has(key) && !/^RUS_nat_(title|plan_open|tab_0_tt|needs|report_supply|supply_(?:food|beet|textile)|task_3|reserve_[012](?:_tt)?|(?:wheat|rye|beet|flax|cotton)_info|(?:m?order)_(?:fra|eng))$/.test(key)) {
      const expected = lang === 'simp_chinese' ? chinesePresentation(previous.get(key), key) : previous.get(key);
      assert.equal(plain(value),plain(expected),`${lang} ${key}: unintended rule/text change`);
    }
  }
  for (let i=0;i<4;i++) {
    const value=loc.get(`RUS_nat_tab_${i}_tt`);
    for (const marker of ['§4','§Y','§R','£RUS_nat_text_','\\n\\n']) assert.ok(value.includes(marker),`${lang}: unstyled tooltip ${i}`);
    if (lang === 'simp_chinese') {
      assert.ok(!value.includes('；'), 'Semicolon clauses must become paragraphs');
      assert.ok(!value.includes('个百分点'), 'Use percentage notation consistently');
      assert.ok(!/\d[分点]/.test(plain(value)), 'No score/allocation suffix after a number');
      assert.equal(chinesePresentation(value, `RUS_nat_tab_${i}_tt`),value,'Presentation must be idempotent');
    }
  }
  for (let i=0;i<3;i++) {
    const button=gui.find(w=>w.key==='buttonType'&&get(w.value,'name')===`nat_reserve_${i}`);
    assert.equal(get(button.value,'pdx_tooltip'),`RUS_nat_reserve_${i}_tt`);
    assert.ok(loc.get(`RUS_nat_reserve_${i}_tt`).includes('25%'));
  }
  for (const crop of ['wheat','rye','beet','flax','cotton']) {
    const value = loc.get(`RUS_nat_${crop}_info`);
    assert.ok(value.includes(`[?RUS_nat_${crop}_preview_rate|2]`), 'Unit yield must be a decimal quantity');
    assert.ok(!value.includes('|%'), 'Unit yield is not a percentage');
    if (lang === 'simp_chinese') assert.ok(value.includes('单位产量'));
  }
  assert.ok(plain(loc.get('RUS_nat_tab_0_tt')).includes({simp_chinese:'手动调整即时保存',english:'Manual edits are saved immediately',russian:'Ручные изменения сохраняются сразу'}[lang]));
  for(const group of ['food','beet','textile']) assert.ok(plain(loc.get(`RUS_nat_supply_${group}`)).includes(`[?RUS_nat_${group}_preview|2]%`));
  for(const [key,suffix] of [['needs','preview'],['report_supply','last_ratio']]) for(const group of ['food','beet','textile']) assert.ok(loc.get(`RUS_nat_${key}`).includes(`[?RUS_nat_${group}_${suffix}|2]`));
  if(lang==='simp_chinese') for(const [key,value] of loc) assert.ok(!value.includes('不是'),key);
}
assert.equal(chinesePresentation('甲；乙；丙'),'甲。\\n\\n乙。\\n\\n丙');
assert.equal(chinesePresentation('§Y0.1§!个百分点 §G+5§!个百分点'),'§Y0.1%§! §G+5%§!');
assert.equal(chinesePresentation('§Y20§!点，§G+2点§!，§Y12分§!'),'§Y20§!，§G+2§!，§Y12§!');
assert.equal(chinesePresentation('§Y30%§!，§Y1.20§!，540天，3次，3000单位'),'§Y30%§!，§Y1.20§!，540天，3次，3000单位');
console.log('Tooltip checks passed: three locales, preserved mechanics text, colors, icons, reserve bindings and BOM/unique keys.');
const cn = new Map(entries(read('localisation/simp_chinese/RUS_national_agriculture_l_simp_chinese.yml')));
const oldCn = new Map(entries(execFileSync('git',['show','HEAD:localisation/simp_chinese/RUS_national_agriculture_l_simp_chinese.yml'],{cwd:root,encoding:'utf8'})));
for (const [key, value] of cn) {
  assert.equal(chinesePresentation(value, key), value, `${key}: not idempotent`);
  const old = oldCn.get(key);
  const refs = s => [...s.matchAll(/\[\?([^|\]]+)/g)].map(m => m[1]);
  if(!old || /^RUS_nat_supply_(food|beet|textile)$/.test(key)) {
    const scripts = read('common/scripted_effects/RUS_national_agriculture_effects.txt')+read('common/scripted_effects/RUS_agri_development_effects.txt');
    for(const ref of refs(value)) assert.ok(scripts.includes(ref),`${key}: undeclared ${ref}`);
    continue;
  }
  const crop = /^RUS_nat_(wheat|rye|beet|flax|cotton)_(info|market_line)$/.exec(key);
  const expected = crop ? crop[2] === 'info' ? [`RUS_nat_${crop[1]}_yield`, `RUS_nat_${crop[1]}_preview_rate`] : [`RUS_nat_${crop[1]}_preview_income`] : key === 'RUS_nat_preview_income_line' ? ['RUS_nat_preview_income'] : refs(old || '');
  assert.deepEqual(refs(value), expected, `${key}: variable references changed`);
}
assert.ok(plain(cn.get('RUS_nat_tab_2_tt')).includes('粮食内需额外+2、纺织原料内需额外+1'));
assert.ok(plain(cn.get('RUS_nat_tab_2_tt')).includes('小麦12、黑麦12、甜菜6、亚麻6、棉花6'));
assert.ok(plain(cn.get('RUS_nat_tab_1_tt')).includes('仓库农机不参与在役损耗'));
assert.ok(plain(cn.get('RUS_nat_tab_3_tt')).includes('不包含下列储备、农机覆盖和任务积分'));
assert.ok(!cn.get('RUS_nat_machine_5').includes('\\n'));
