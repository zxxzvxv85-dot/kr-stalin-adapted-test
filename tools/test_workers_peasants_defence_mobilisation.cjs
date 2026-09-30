const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const read = file => fs.readFileSync(path.join(root, file), 'utf8');

function parse(source) {
  const tokens = source.match(/#[^\r\n]*|"(?:\\.|[^"\\])*"|[{}=]|[^\s{}=#]+/g).filter(t => !t.startsWith('#'));
  let index = 0;
  function block(nested = false) {
    const nodes = [];
    while (index < tokens.length && tokens[index] !== '}') {
      const key = tokens[index++];
      assert.equal(tokens[index++], '=', `expected assignment after ${key}`);
      let value = tokens[index++];
      if (value === '{') value = block(true);
      nodes.push({key, value});
    }
    if (nested) assert.equal(tokens[index++], '}');
    return nodes;
  }
  const result = block();
  assert.equal(index, tokens.length, 'balanced script blocks');
  return result;
}
const get = (nodes, key) => nodes.find(n => n.key === key)?.value;
const load = file => parse(read(file));
const law = load('common/ideas/RUS_workers_peasants_defence_mobilisation_law.txt');
const economy = get(get(law, 'ideas'), 'economy');
const base = 'RUS_workers_peasants_defence_mobilisation_law';
const ids = [1, 2, 3, 4].map(n => `${base}_stage_${n}`).concat(base);
const expected = [
  [.05, .25, .1, 0, 0, 0, 0, 0],
  [.06, .26, .075, .01, -.01, .025, .05, .025],
  [.07, .27, .05, .025, -.025, .05, .1, .05],
  [.08, .28, .025, .04, -.04, .075, .15, .075],
  [.1, .3, 0, .05, -.05, .1, .2, .1]
];
const changingKeys = [
  'political_power_gain', 'consumer_goods_expected_value',
  'production_speed_arms_factory_factor', 'production_speed_buildings_powered_factor',
  'production_cost_arms_factory_factor', 'local_resources_factor',
  'mobilization_speed', 'global_building_slots_factor'
];
for (const [tier, id] of ids.entries()) {
  const idea = get(economy, id);
  assert.ok(idea, `missing law tier ${tier + 1}`);
  assert.equal(get(idea, 'level'), '3');
  assert.equal(get(idea, 'picture'), 'FRA_national_mobilization_focus');
  assert.equal(get(get(idea, 'allowed'), 'always'), 'no');
  assert.equal(get(get(get(idea, 'allowed_to_remove'), 'NOT'), 'country_exists'), 'GER');
  const modifier = get(idea, 'modifier');
  for (const [i, key] of changingKeys.entries()) {
    assert.equal(Number(get(modifier, key) || 0), expected[tier][i], `${id}: ${key}`);
  }
  for (const [key, value] of Object.entries({
    unit_limit_law_bonus: 8,
    conversion_cost_civ_to_mil_factor: -.1,
    conversion_cost_mil_to_civ_factor: -.1,
    fuel_gain_factor: -.1
  })) assert.equal(Number(get(modifier, key)), value, `${id}: ${key}`);
  assert.equal(get(modifier, 'custom_modifier_tooltip'), `${base}_stage_${tier + 1}_progress_tt`);
}
const effects = load('common/scripted_effects/RUS_workers_peasants_defence_mobilisation_effects.txt');
const apply = get(effects, 'RUS_apply_workers_peasants_defence_mobilisation_law');
const branches = apply.filter(n => ['if', 'else_if', 'else'].includes(n.key));
assert.equal(branches.length, 5);
assert.deepEqual(branches.map(n => get(get(n.value, 'limit') || [], 'has_country_flag') || null),
  ['RUS_fr_reform_stage_4', 'RUS_fr_reform_stage_3', 'RUS_fr_reform_stage_2', 'RUS_fr_reform_stage_1', null]);
assert.deepEqual(branches.map(n => get(get(n.value, 'if'), 'add_ideas')),
  [ids[4], ids[3], ids[2], ids[1], ids[0]]);
const refresh = get(effects, 'RUS_refresh_workers_peasants_defence_mobilisation_law');
assert.deepEqual(get(get(get(refresh, 'if'), 'limit'), 'OR').map(n => n.value), ids);
const reform = read('common/scripted_effects/RUS_fr_military_reform_effects.txt');
for (const name of ['one', 'two', 'three', 'four']) {
  const start = reform.indexOf(`RUS_fr_apply_rectification_stage_${name} = {`);
  const next = reform.indexOf('\nRUS_fr_', start + 1);
  assert.ok(reform.slice(start, next).includes('RUS_refresh_workers_peasants_defence_mobilisation_law = yes'), name);
}
const event = read('events/RUS_socialist_parallel_flavour_events.txt');
assert.ok(event.includes('RUS_apply_workers_peasants_defence_mobilisation_law = yes'));
assert.ok(event.includes('RUS_refresh_workers_peasants_defence_mobilisation_law = yes'));
assert.ok(event.includes('add_ideas = partial_economic_mobilisation'));
const onActions = read('common/on_actions/RUS_fr_military_reform_on_actions.txt');
assert.equal((onActions.match(/RUS_refresh_workers_peasants_defence_mobilisation_law = yes/g) || []).length, 2);
for (const language of ['simp_chinese', 'english', 'russian']) {
  const loc = read(`localisation/${language}/${base}_l_${language}.yml`);
  for (const id of ids) assert.ok(loc.includes(` ${id}:`), `${language}: ${id}`);
  for (let tier = 1; tier <= 5; tier++) {
    assert.ok(loc.includes(` ${base}_stage_${tier}_progress_tt:`), `${language}: progress tooltip ${tier}`);
  }
}
console.log('Five decree tiers, reform hooks, event grant and localisation: OK');
