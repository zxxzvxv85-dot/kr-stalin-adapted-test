// Runs the actual cooperation script subset; HOI4 runtime QA is still required.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const read = file => fs.readFileSync(path.join(root, file), 'utf8');
function parse(source) {
  const tokens = source.match(/#[^\r\n]*|"(?:\\.|[^"\\])*"|[{}]|[<>!=]=?|[^\s{}=<>!#]+/g).filter(t => !t.startsWith('#'));
  let i = 0;
  function block(nested = false) {
    const result = [];
    while (i < tokens.length && tokens[i] !== '}') {
      const key = tokens[i++];
      if (!['=', '<', '>'].includes(tokens[i])) {
        result.push({key, op:null, value:null});
        continue;
      }
      const op = tokens[i++];
      assert.ok(['=', '<', '>'].includes(op), 'Unexpected operator: ' + op);
      let value = tokens[i++];
      if (value === '{') value = block(true);
      result.push({key, op, value});
    }
    if (nested) assert.equal(tokens[i++], '}');
    return result;
  }
  const result = block();
  assert.equal(i, tokens.length);
  return result;
}
const get = (block, key) => block.find(n => n.key === key)?.value;
const load = file => parse(read(file));
const effects = new Map(load('common/scripted_effects/RUS_future_foreign_cooperation_effects.txt').map(n => [n.key, n.value]));
const triggers = new Map(load('common/scripted_triggers/RUS_future_foreign_cooperation_triggers.txt').map(n => [n.key, n.value]));
const country = id => ({id, exists:true, socialist:true, wars:[], focuses:[], pp:0, vars:{}, guarantees:[], opinions:[], ideas:[]});
function check(block, c, world, origin) {
  return block.every(n => {
    const v = n.value;
    if (n.key === 'NOT') return !check(v, c, world, origin);
    if (n.key === 'AND') return check(v, c, world, origin);
    if (n.key === 'OR') return v.some(item => check([item], c, world, origin));
    if (n.key === 'FRA') return check(v, world.FRA, world, origin);
    if (n.key === 'exists') return c.exists === (v === 'yes');
    if (n.key === 'has_socialist_government') return c.socialist === (v === 'yes');
    if (n.key === 'has_completed_focus') return c.focuses.includes(v);
    if (n.key === 'has_war_with') return c.wars.includes(v === 'ROOT' ? origin.id : v);
    if (n.key === 'has_political_power') { assert.equal(n.op, '<'); return c.pp < Number(v); }
    if (triggers.has(n.key)) return check(triggers.get(n.key), c, world, origin);
    throw Error('Unsupported trigger ' + n.key);
  });
}
function run(block, c, world, origin = c) {
  let previousIf = false;
  for (const n of block) {
    const v = n.value;
    if (n.key === 'if') {
      previousIf = check(get(v, 'limit'), c, world, origin);
      if (previousIf) run(v.filter(x => x.key !== 'limit'), c, world, origin);
    } else if (n.key === 'else') {
      if (!previousIf) run(v, c, world, origin);
    } else if (n.key === 'FRA') run(v, world.FRA, world, origin);
    else if (n.key === 'set_variable') for (const x of v) c.vars[x.key] = Number(x.value);
    else if (n.key === 'add_political_power') c.pp += Number(v);
    else if (n.key === 'give_guarantee') c.guarantees.push(v === 'ROOT' ? origin.id : v);
    else if (n.key === 'add_opinion_modifier') c.opinions.push({target:get(v, 'target') === 'ROOT' ? origin.id : get(v, 'target'), modifier:get(v, 'modifier')});
    else if (n.key === 'add_timed_idea') c.ideas.push({idea:get(v, 'idea'), days:Number(get(v, 'days'))});
    else if (effects.has(n.key)) run(effects.get(n.key), c, world, origin);
    else throw Error('Unsupported effect ' + n.key);
  }
}
let cases = 0;
for (const rusWar of [false, true]) for (const fraWar of [false, true]) {
  const world = {RUS:country('RUS'), FRA:country('FRA')};
  if (rusWar) world.RUS.wars.push('GER');
  if (fraWar) world.FRA.wars.push('GER');
  run(effects.get('RUS_future_foreign_joint_deterrence'), world.RUS, world);
  for (const [id, other] of [['RUS','FRA'], ['FRA','RUS']]) {
    assert.deepEqual(world[id].guarantees, [other]);
    assert.equal(world[id].opinions[0].target, other);
    assert.equal(world[id].ideas[0].days, rusWar && fraWar ? 365 : 180);
  }
  cases++;
}
for (const invalid of ['missing', 'hostile', 'notSocialist']) {
  const world = {RUS:country('RUS'), FRA:country('FRA')};
  if (invalid === 'missing') world.FRA.exists = false;
  if (invalid === 'hostile') world.FRA.wars.push('RUS');
  if (invalid === 'notSocialist') world.FRA.socialist = false;
  run(effects.get('RUS_future_foreign_joint_deterrence'), world.RUS, world);
  assert.equal(world.RUS.ideas.length + world.FRA.ideas.length + world.RUS.guarantees.length, 0);
  cases++;
}
const localText = load('common/scripted_localisation/RUS_future_foreign_cooperation_scripted_loc.txt')[0].value;
for (const complete of [false, true]) for (const pp of [23.9, 24, 24.1, 29.9, 30, 30.1]) {
  const c = country('RUS');
  c.pp = pp;
  if (complete) c.focuses.push('RUS_future_foreign_056');
  const cost = complete ? 24 : 30;
  assert.equal(check(triggers.get('RUS_future_foreign_can_pay_aid_pp'), c, {}, c), pp >= cost);
  const displayed = localText.filter(n => n.key === 'text').find(n => !get(n.value, 'trigger') || check(get(n.value, 'trigger'), c, {}, c));
  assert.equal(get(displayed.value, 'localization_key'), 'RUS_future_foreign_aid_pp_' + cost);
  run(effects.get('RUS_future_foreign_pay_aid_pp'), c, {});
  assert.ok(Math.abs(c.pp - (pp - cost)) < 1e-8);
  cases++;
}
for (const complete of [false, true]) {
  const c = country('RUS');
  c.vars.existing_research = 0.05;
  if (complete) c.focuses.push('RUS_future_foreign_056');
  for (let i = 0; i < 100; i++) run(effects.get('RUS_future_foreign_refresh_red_flags'), c, {});
  for (const [suffix, value] of [['political_power', .05], ['relations_cost', -.25], ['volunteers', 2]]) {
    assert.equal(c.vars['RUS_soviets_and_phalanstere_' + suffix], complete ? value : 0);
  }
  assert.equal(c.vars.existing_research, .05);
  cases++;
}
const decisions = load('common/decisions/RUS_future_foreign_policy_decisions.txt')[0].value;
for (const type of ['military', 'civil']) {
  const decision = get(decisions, 'RUS_future_foreign_' + type + '_aid');
  assert.equal(get(get(decision, 'custom_cost_trigger'), 'RUS_future_foreign_can_pay_aid_pp'), 'yes');
  assert.equal(get(get(get(decision, 'complete_effect'), 'hidden_effect'), 'RUS_future_foreign_pay_aid_pp'), 'yes');
  assert.equal(get(decision, 'custom_cost_text'), 'RUS_future_foreign_' + type + '_aid_scaled_cost');
}
assert.equal(get(get(decisions, 'RUS_future_foreign_joint_develop_pokrovsk_tungsten'), 'cost'), '40');
assert.equal(get(get(decisions, 'RUS_future_foreign_joint_develop_zlatoust_chromium'), 'cost'), '45');
const focuses = load('common/national_focus/00_RUS_future_foreign_policy_skeleton.txt').filter(n => n.key === 'shared_focus');
for (const id of ['046', '056']) {
  const matches = focuses.filter(n => get(n.value, 'id') === 'RUS_future_foreign_' + id);
  assert.equal(matches.length, 1);
  const focus = matches[0].value;
  assert.ok(get(focus, 'completion_reward'));
  assert.equal(get(get(focus, 'ai_will_do'), 'factor'), '10');
  assert.notEqual(get(focus, 'available')?.find(n => n.key === 'always')?.value, 'no');
  if (id === '046') {
    assert.equal(get(get(focus, 'completion_reward'), 'RUS_future_foreign_joint_deterrence'), 'yes');
    assert.equal(get(get(focus, 'completion_reward'), 'custom_effect_tooltip'), undefined);
  } else {
    assert.ok(get(focus, 'completion_reward').some(n => n.value === 'RUS_future_foreign_aid_discount_tt'));
  }
}
for (const file of ['common/national_focus/00_RUS_future_foreign_policy_skeleton.txt', 'common/national_focus/RUS focus (Russia).txt']) {
  const source = read(file);
  for (const name of ['faction_fourth_internationale', 'faction_eastern_front_of_the_internationale']) {
    const expression = new RegExp('create_faction_from_template = \\{ template = faction_template_internationale name = ' + name + '[^\\n]*\\n\\s*set_faction_manifest = faction_manifest_world_revolution');
    assert.match(source, expression);
  }
}
const modifier = get(load('common/dynamic_modifiers/RUS_future_foreign_policy_dynamic_modifiers.txt'), 'RUS_soviets_and_phalanstere');
assert.equal(get(modifier, 'political_power_factor'), 'RUS_soviets_and_phalanstere_political_power');
assert.equal(get(modifier, 'improve_relations_maintain_cost_factor'), 'RUS_soviets_and_phalanstere_relations_cost');
assert.equal(get(modifier, 'send_volunteer_size'), 'RUS_soviets_and_phalanstere_volunteers');
assert.ok(get(modifier, 'research_speed_factor'));
assert.ok(get(modifier, 'country_resource_oil'));
assert.match(read('common/scripted_effects/RUS_future_foreign_policy_effects.txt'), /RUS_future_foreign_refresh_red_country_count = \{\s*RUS_future_foreign_refresh_red_flags = yes/);
const idea = get(get(get(load('common/ideas/RUS_future_foreign_cooperation_ideas.txt'), 'ideas'), 'country'), 'RUS_franco_russian_joint_deterrence');
assert.equal(get(get(idea, 'modifier'), 'war_support_factor'), '0.05');
assert.equal(get(get(idea, 'modifier'), 'planning_speed'), '0.10');
assert.equal(get(get(get(load('common/opinion_modifiers/RUS_future_foreign_cooperation_opinions.txt'), 'opinion_modifiers'), 'RUS_future_foreign_joint_deterrence_opinion'), 'value'), '25');
const allKeys = [];
for (const lang of ['simp_chinese', 'english', 'russian']) {
  const file = path.join(root, `localisation/${lang}/RUS_future_foreign_cooperation_l_${lang}.yml`);
  assert.equal(fs.readFileSync(file).subarray(0, 3).toString('hex'), 'efbbbf');
  const lines = fs.readFileSync(file, 'utf8').trim().split(/\r?\n/).slice(1);
  const keys = lines.map(line => {
    assert.match(line, /^ \w+:0 "(?:[^"\\]|\\.)*"$/);
    return line.trim().split(':')[0];
  });
  assert.equal(new Set(keys).size, keys.length);
  allKeys.push(keys);
}
assert.deepEqual(allKeys[0], allKeys[1]);
assert.deepEqual(allKeys[0], allKeys[2]);
const parisBranch = new Set(['RUS_future_foreign_006']);
for (let changed = true; changed;) {
  changed = false;
  for (const {value: focus} of focuses) {
    const id = get(focus, 'id');
    const prerequisites = focus.filter(n => n.key === 'prerequisite').flatMap(n => n.value).map(n => n.value);
    if (!parisBranch.has(id) && prerequisites.some(p => parisBranch.has(p))) {
      parisBranch.add(id); changed = true;
    }
  }
}
assert.deepEqual([...parisBranch].sort(), ['006', '016', '017', '032', '046', '047', '056'].map(id => 'RUS_future_foreign_' + id));
for (const {value: focus} of focuses) {
  const threat = (get(focus, 'completion_reward') || []).filter(n => n.key === 'add_threat');
  assert.deepEqual(threat.map(n => n.value), parisBranch.has(get(focus, 'id')) ? ['2.0'] : []);
}
function threatCount(nodes) {
  return nodes.reduce((count, n) => count + (n.key === 'add_threat' ? 1 : 0) + (Array.isArray(n.value) ? threatCount(n.value) : 0), 0);
}
for (const decision of decisions) {
  const aid = ['RUS_future_foreign_military_aid', 'RUS_future_foreign_civil_aid'].includes(decision.key);
  assert.equal(threatCount(decision.value), aid ? 1 : 0);
  if (aid) assert.equal(get(get(decision.value, 'complete_effect'), 'add_threat'), '1.0');
}
console.log(`${cases} behavioral cases passed; aid hooks, resource prices, modifier values and three-language BOM/key parity passed. Seven Paris-branch rewards and one-time aid threat hooks verified.`);
