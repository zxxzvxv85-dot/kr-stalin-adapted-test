const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),{execFileSync}=require('node:child_process');
const {parse,get,root,country,check}=require('./test_agri_development.cjs');
const read=file=>fs.readFileSync(path.join(root,file),'utf8');
const traitsFile='common/country_leader/RUS_stalin_relationship_scaled_advisor_tiers.txt';
const traits=get(parse(read(traitsFile)),'leader_traits');
const previous=execFileSync('git',['show',`HEAD:${traitsFile}`],{cwd:root,encoding:'utf8'});
const strip=t=>t.replace(/^\s*custom_modifier_tooltip\s*=.*$/gm,'').replace(/\s+/g,'');
assert.equal(strip(read(traitsFile)),strip(previous),'Advisor numeric effects must not change');
const effectsFile='common/scripted_effects/RUS_stalin_relationship_scaled_advisor_tier_effects.txt';
assert.equal(read(effectsFile).replace(/\r/g,''),execFileSync('git',['show',`HEAD:${effectsFile}`],{cwd:root,encoding:'utf8'}).replace(/\r/g,''),'Do not alter advisor tier selection');
const defined=parse(read('common/scripted_localisation/RUS_maximalist_advisor_agriculture_loc.txt'));
for(const slug of ['ustinov','kolegayev','kakhovskaya']) {
  const key=`RUS_maximalist_advisor_${slug}_agriculture_tt`;
  for(let tier=0;tier<=5;tier++) {
    const trait=get(traits,`RUS_relationship_scaled_${slug}_tier_${tier}`);
    assert.equal(trait.filter(x=>x.key==='custom_modifier_tooltip'&&x.value===key).length,1);
    assert.ok(!trait.some(x=>x.value==='RUS_maximalist_advisor_land_reform_monthly_tt'));
  }
  const definition=defined.find(x=>get(x.value,'name')===`GetRUSMaximalistAgriculture${slug}`);
  for(const [enabled,score,outcome] of [[true,0,''],[true,150,'success'],[true,60,'failure'],[false,0,''],[false,80,''],[false,100,''],[false,100,'success'],[false,40,'failure']]) {
    const c=country();c.vars.RUS_maximalist_land_reform_score=score;
    if(enabled)c.flags.RUS_nat_enabled=true;
    if(outcome)c.flags[`RUS_maximalist_land_reform_${outcome}`]=true;
    const selected=definition.value.find(x=>x.key==='text'&&(!get(x.value,'trigger')||check(get(get(x.value,'trigger'),'RUS'),c)));
    const expected=enabled?`RUS_maximalist_advisor_${slug}_national_tt`:score>=100||outcome?'RUS_maximalist_advisor_agriculture_empty':'RUS_maximalist_advisor_land_reform_monthly_tt';
    assert.equal(get(selected.value,'localization_key'),expected);
  }
}
for(const lang of ['simp_chinese','english','russian']) {
  const text=read(`localisation/${lang}/RUS_stalin_relationship_scaled_advisor_tiers_l_${lang}.yml`);
  assert.equal(text.charCodeAt(0),0xfeff);
  const pairs=[...text.matchAll(/^\s*([\w.]+):\s*"(.*)"$/gm)].map(m=>[m[1],m[2]]),loc=new Map(pairs);
  assert.equal(pairs.length,loc.size);
  for(const slug of ['ustinov','kolegayev','kakhovskaya']) {
    assert.equal(loc.get(`RUS_maximalist_advisor_${slug}_agriculture_tt`),`[GetRUSMaximalistAgriculture${slug}]`);
    const description=loc.get(`RUS_maximalist_advisor_${slug}_national_tt`);
    for(const marker of ['£RUS_nat_text_','§4','§G','§R'])assert.ok(description.includes(marker));
    assert.equal([...description.matchAll(/§[^!]/g)].length,[...description.matchAll(/§!/g)].length);
  }
  const ui=read(`localisation/${lang}/RUS_national_agriculture_l_${lang}.yml`);
  for(const tag of ['fra','eng'])for(const prefix of ['order','morder']){
    const line=ui.split(/\r?\n/).find(l=>l.includes(`RUS_nat_${prefix}_${tag}:`));
    assert.ok(line.includes(`[${tag.toUpperCase()}.GetName]`));
  }
}
const cats=read('common/decisions/categories/RUS_agricultural_quarterly_management_categories.txt');
assert.equal([...cats.matchAll(/picture = GFX_decision_cat_RUS_national_agriculture/g)].length,2);
assert.ok(!cats.includes('GFX_decision_cat_RUS_economy'));
const sprite=get(parse(read('interface/RUS_national_agriculture_category.gfx')),'spriteTypes')[0].value;
assert.ok(fs.existsSync(path.join(root,get(sprite,'texturefile'))));
console.log('Passed: 18 advisor tiers, 24 route/outcome cases, unchanged modifiers/selection, three locales, country names and category image.');
