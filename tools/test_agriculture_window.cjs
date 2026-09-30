// Execute the shipped window actions and compare rewards to canonical decisions.
// This checks scopes, payment and lifecycle; it is not an HOI4 rendering test.
const assert = require('node:assert/strict');
const {parse, get, effects, triggers, country, check, exec, read} = require('./test_support/agriculture.cjs');
for (const file of ['RUS_national_agriculture_window_effects', 'RUS_national_agriculture_shutdown_effects']) {
  for (const n of parse(read(`common/scripted_effects/${file}.txt`))) effects.set(n.key, n.value);
}
for (const n of parse(read('common/scripted_triggers/RUS_national_agriculture_window_triggers.txt'))) triggers.set(n.key, n.value);
const panel = get(get(parse(read('common/scripted_guis/RUS_national_agriculture.txt')), 'scripted_gui'), 'RUS_national_agriculture_gui');
const clicks = get(panel, 'effects');
const conditions = get(panel, 'triggers');
const launcher = get(get(parse(read('common/scripted_guis/RUS_national_agriculture_launcher.txt')), 'scripted_gui'), 'RUS_national_agriculture_launcher');
const sourceFiles = ['RUS_national_agriculture_decisions', 'RUS_agri_development_decisions', 'RUS_national_agriculture_shutdown_decision'];
const decisions = new Map(sourceFiles.flatMap(file => parse(read(`common/decisions/${file}.txt`))[0].value).map(n => [n.key, n.value]));
const click = (c, key) => exec(get(clicks, `nat_action_${key}_click`), c);
const available = (c, key) => check(get(conditions, `nat_action_${key}_click_enabled`), c);
const run = (c, key) => exec(effects.get(key), c);
const fresh = () => {
  const c = country();
  c.vars['global.num_days'] = 1936 * 365 + 90;
  c.civCapacity = 24;
  c.vars.num_of_civilian_factories_available_for_projects = 24;
  c.pp = 100;
  c.flags.RUS_maximalist_land_reform_in_progress = true;
  run(c, 'RUS_nat_enable');
  c.flags.RUS_nat_window_open = true;
  c.flags.RUS_maximalist_land_reform_success = true;
  delete c.flags.RUS_maximalist_land_reform_in_progress;
  c.vars.RUS_maximalist_land_reform_score = 200;
  c.vars.RUS_agri_spendable_score = 60;
  run(c, 'RUS_nat_refresh');
  return c;
};
function gameplay(c) {
  const out = structuredClone(c);
  delete out.temps;
  delete out.flags.RUS_nat_window_open;
  for (const key of Object.keys(out.vars)) {
    if (key.startsWith('global.') || key === 'RUS_nat_admin_page') delete out.vars[key];
  }
  return out;
}
assert.equal(get(panel, 'context_type'), 'player_context');
assert.equal(get(launcher, 'parent_window_name'), 'raid_filter');
assert.equal(get(get(launcher, 'ai_enabled'), 'always'), 'no');
const category = parse(read('common/decisions/categories/RUS_agricultural_quarterly_management_categories.txt'))
  .find(n => n.key === 'RUS_agricultural_quarterly_management_category').value;
assert.equal(get(get(category, 'visible'), 'always'), 'no');
assert.ok(!get(category, 'scripted_gui'));
assert.equal(decisions.size, 15);

// The native completion blocks are unchanged inside the guarded GUI execution.
for (const [key, definition] of decisions) {
  const action = get(clicks, `nat_action_${key}_click`);
  const actual = get(get(action, 'hidden_effect'), 'if');
  const expected = get(definition, 'complete_effect');
  const payment = Number(get(definition, 'cost') || 0);
  const execution = actual.filter(n => n.key !== 'limit').slice(payment ? 1 : 0, -1);
  const presentationNormalized = structuredClone(execution);
  if (key === 'RUS_nat_close_system') presentationNormalized.find(n => n.key === 'custom_effect_tooltip').value = 'RUS_nat_close_system_tt';
  assert.deepEqual(presentationNormalized, expected, `${key}: changed canonical rewards`);
  for (const easy of [false, true]) {
    const actualState = fresh();
    if (easy) actualState.flags.RUS_easy_mode_enabled = true;
    const expectedState = structuredClone(actualState);
    assert.ok(available(actualState, key), key);
    expectedState.pp -= payment;
    exec(expected, expectedState);
    if (key === 'RUS_nat_close_system') run(expectedState, 'RUS_nat_window_close_effect');
    else run(expectedState, 'RUS_agri_refresh_gui');
    click(actualState, key);
    assert.deepEqual(gameplay(actualState), gameplay(expectedState), `${key}: payment or rewards differ`);
  }
}

// Pay exactly once; reject insufficient PP, repeats and exhausted quarterly slots.
for (const key of [...decisions.keys()].filter(k => k.startsWith('RUS_nat_support_'))) {
  for (const pp of [0, 9, 9.999, 10, 10.001, 20]) {
    const c = fresh(); c.pp = pp;
    assert.equal(available(c, key), pp >= 10);
    click(c, key);
    assert.equal(c.pp, pp >= 10 ? pp - 10 : pp);
    const before = gameplay(c);
    click(c, key);
    assert.deepEqual(gameplay(c), before, 'Repeated support charged again');
  }
  const c = fresh(); c.vars.RUS_nat_support_count = 4;
  const before = gameplay(c); assert.equal(available(c, key), false); click(c, key);
  assert.deepEqual(gameplay(c), before);
}

// Score costs, project exclusivity, investment and export cooldowns remain enforced.
for (const key of [...decisions.keys()].filter(k => k.startsWith('RUS_agri_exchange_'))) {
  const c = fresh(); c.vars.RUS_agri_spendable_score = 0;
  const before = gameplay(c); assert.equal(available(c, key), false); click(c, key);
  assert.deepEqual(gameplay(c), before);
  const paid = fresh(); click(paid, key);
  const after = gameplay(paid); assert.equal(available(paid, key), false); click(paid, key);
  assert.deepEqual(gameplay(paid), after);
}
const capped = fresh();
for (const key of ['rations', 'mechanisation']) click(capped, 'RUS_agri_exchange_' + key);
for (const key of ['reserves', 'materials']) assert.equal(available(capped, 'RUS_agri_exchange_' + key), false);

// Closed windows, AI control, another country and disabled systems cannot operate.
for (const variant of ['window_closed', 'system_closed', 'not_enabled', 'not_unlocked', 'ai', 'other_country']) {
  for (const key of decisions.keys()) {
    const c = fresh();
    if (variant === 'window_closed') delete c.flags.RUS_nat_window_open;
    if (variant === 'system_closed') c.flags.RUS_nat_system_closed = true;
    if (variant === 'not_enabled') delete c.flags.RUS_nat_enabled;
    if (variant === 'not_unlocked') delete c.flags.RUS_agri_management_unlocked;
    if (variant === 'ai') c.ai = true;
    if (variant === 'other_country') c.id = 'FRA';
    const before = gameplay(c); assert.equal(available(c, key), false); click(c, key);
    assert.deepEqual(gameplay(c), before, `${variant}: ${key} still operated`);
  }
}

const c = fresh();
c.vars.RUS_nat_page = 3; c.vars.RUS_nat_admin_page = 1;
run(c, 'RUS_nat_refresh'); const before = gameplay(c);
for (let i = 0; i < 20; i++) {
  exec(get(clicks, 'nat_window_close_click'), c);
  assert.equal(check(get(panel, 'visible'), c), false);
  exec(get(get(launcher, 'effects'), 'nat_window_open_click'), c);
  assert.equal(check(get(panel, 'visible'), c), true);
}
assert.deepEqual(gameplay(c), before, 'Opening/closing changed plans, orders, timers or rewards');
assert.equal(c.vars.RUS_nat_page, 3); assert.equal(c.vars.RUS_nat_admin_page, 1);
for (const score of [199, 200, 200.001, 201]) {
  const state = fresh(); state.vars.RUS_agri_display_score = score;
  assert.equal(available(state, 'RUS_nat_close_system'), score > 200);
  click(state, 'RUS_nat_close_system');
  assert.equal(!!state.flags.RUS_nat_system_closed, score > 200);
  if (score > 200) {
    assert.equal(check(get(launcher, 'visible'), state), false);
    assert.equal(check(get(panel, 'visible'), state), false);
    assert.equal(state.vars.RUS_nat_factories, 0);
    assert.ok(state.flags.RUS_maximalist_land_reform_success);
  }
}
console.log('Independent agriculture window: canonical actions, 30 normal/easy comparisons, 36 PP boundaries, caps, 90 denied calls, open/close retention and shutdown boundaries passed.');
