// Real GUI/effect scripts with bounded building and factory-reservation semantics.
const assert = require('node:assert/strict');
const {parse, get, read, country, effects, exec, check, num} = require('./test_support/agriculture.cjs');
const gui = get(get(parse(read('common/scripted_guis/RUS_national_agriculture.txt')), 'scripted_gui'), 'RUS_national_agriculture_gui');
const actions = get(gui, 'effects'), conditions = get(gui, 'triggers');
for (const n of parse(read('common/scripted_effects/RUS_national_agriculture_shutdown_effects.txt'))) effects.set(n.key, n.value);
const run = (c, key) => exec(effects.get('RUS_nat_' + key), c);
const click = (c, key = 'nat_convert_mil') => exec(get(actions, key + '_click'), c);
const enabled = c => check(get(conditions, 'nat_convert_mil_click_enabled'), c);
const value = (c, key) => c.vars['RUS_nat_' + key] || 0;
function fresh(civilian = 0, military = 6) {
  const c = country();
  c.civCapacity = civilian;
  c.vars.num_of_civilian_factories_available_for_projects = civilian;
  c.vars['global.num_days'] = 706699;
  c.states = [{owner:'RUS',controller:'RUS',buildings:{arms_factory:military}}];
  run(c, 'enable');
  return c;
}
const near = (a, b) => assert.ok(Math.abs(a - b) < 0.00001, `${a} != ${b}`);

// A demolition must start production even when no ordinary civilian factory is free.
for (const easy of [false, true]) {
  const c = fresh();
  if (easy) c.flags.RUS_easy_mode_enabled = true;
  assert.ok(enabled(c));
  click(c);
  assert.equal(num(c, 'num_of_military_factories'), 5);
  assert.equal(value(c, 'base_civilian_factories'), 1);
  assert.equal(value(c, 'factories'), 1, 'Converted capacity was not assigned to production');
  assert.equal(value(c, 'civilian_use'), 0);
  near(value(c, 'daily'), 0.36);
  const installed = value(c, 'installed');
  run(c, 'production_day');
  assert.ok(value(c, 'produced') > 0);
  near(value(c, 'installed') - installed, value(c, 'produced'));
  assert.equal(value(c, 'available'), 0, 'Already assigned converted capacity was offered again');
  click(c, 'nat_max');
  assert.equal(value(c, 'factories'), 1);
}

// No fifth-plus conversion, no off-map/occupied-only demolition, no unpaid production.
const capped = fresh();
for (let i = 1; i <= 5; i++) {
  click(capped);
  assert.equal(value(capped, 'factories'), i);
  assert.equal(value(capped, 'base_civilian_factories'), i);
  assert.equal(value(capped, 'civilian_use'), 0);
}
assert.equal(enabled(capped), false);
const afterCap = structuredClone(capped);
click(capped);
assert.deepEqual(capped, afterCap);
for (const scenario of ['no_factory', 'offmap_only', 'occupied', 'foreign_owned']) {
  const c = fresh(0, 0);
  if (scenario === 'offmap_only') c.offmapMilitary = 5;
  if (scenario === 'occupied') c.states = [{owner:'RUS',controller:'GER',buildings:{arms_factory:5}}];
  if (scenario === 'foreign_owned') c.states = [{owner:'GER',controller:'RUS',buildings:{arms_factory:5}}];
  assert.equal(enabled(c), false, scenario);
  const before = structuredClone(c); click(c); assert.deepEqual(c, before, scenario);
}

// Converted units take no extra civilian reservation; ordinary units still do.
for (const civilian of [0, 1, 8]) {
  const c = fresh(civilian);
  c.vars.RUS_nat_requested = civilian; run(c, 'set_factories');
  c.vars.RUS_nat_efficiency = 6000;
  click(c);
  assert.equal(value(c, 'factories'), civilian + 1);
  assert.equal(value(c, 'civilian_use'), civilian);
  near(value(c, 'efficiency'), (civilian * 6000 + 3000) / (civilian + 1));
  assert.equal(value(c, 'available'), 0);
  c.civCapacity = 0;
  run(c, 'production_day');
  assert.equal(value(c, 'factories'), 1, 'Ordinary factory losses removed permanent converted capacity');
  assert.equal(value(c, 'civilian_use'), 0);
  click(c, 'nat_stop');
  assert.equal(value(c, 'daily'), 0);
  assert.equal(value(c, 'factories'), 0);
  assert.equal(value(c, 'available'), 1);
  const produced = value(c, 'produced'); run(c, 'production_day');
  assert.equal(value(c, 'produced'), produced);
  click(c, 'nat_max');
  assert.equal(value(c, 'factories'), 1);
  c.vars.RUS_nat_installed = 8000; c.vars.RUS_nat_machine_stock = 5000;
  const atCap = value(c, 'produced'); run(c, 'production_day');
  assert.equal(value(c, 'produced'), atCap);
}

// Existing credited conversions remain usable without another military-factory loss.
const existing = fresh(3);
existing.vars.RUS_nat_base_civilian_factories = 2;
run(existing, 'factory_capacity'); run(existing, 'parameters');
assert.equal(value(existing, 'available'), 5);
click(existing, 'nat_max');
assert.equal(value(existing, 'factories'), 5);
assert.equal(value(existing, 'civilian_use'), 3);
assert.equal(num(existing, 'num_of_military_factories'), 6);
for (let i = 0; i < 20; i++) {
  run(existing, 'factory_capacity'); run(existing, 'refresh');
  assert.equal(value(existing, 'factories'), 5);
  assert.equal(value(existing, 'civilian_use'), 3);
  assert.equal(value(existing, 'available'), 0);
}
delete existing.vars.RUS_nat_civilian_use;
run(existing, 'refresh');
assert.equal(value(existing, 'civilian_use'), 3, 'Normal refresh did not rebuild the reservation');
existing.vars.RUS_agri_display_score = 201;
run(existing, 'close_system_effect');
assert.equal(value(existing, 'factories'), 0);
assert.equal(value(existing, 'civilian_use'), 0);
assert.equal(existing.vars.num_of_civilian_factories_available_for_projects, 3);
console.log('Factory conversion passed: immediate production, real building cost, 5-unit cap, reservation, stop/restart, losses, storage and existing credits.');
