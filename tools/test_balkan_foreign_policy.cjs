// Execute the relevant production scripts; this does not replace HOI4 runtime QA.
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
      if (!['=', '<', '>'].includes(tokens[i + 1])) {
        // Bare value list such as prioritize = { 249 251 256 399 651 }
        while (i < tokens.length && tokens[i] !== '}') result.push({ key: tokens[i++], op: 'value', value: null });
        break;
      }
      const key = tokens[i++];
      const op = tokens[i++];
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
const get = (nodes, key) => nodes.find(n => n.key === key)?.value;
const effects = new Map(parse(read('common/scripted_effects/RUS_future_foreign_policy_effects.txt')).map(n => [n.key, n.value]));
const focuses = parse(read('common/national_focus/00_RUS_future_foreign_policy_skeleton.txt')).filter(n => n.key === 'shared_focus');
const focus = suffix => focuses.find(n => get(n.value, 'id') === 'RUS_future_foreign_' + suffix).value;
const tags = ['SER', 'ROM', 'GRE', 'ALB', 'BUL'];
const prefix = 'RUS_third_international_gendarme_';
function country(id) { return {id, exists:true, socialist:true, focuses:[], flags:[], vars:{}, temp:{}, pp:0, pacts:[], modifiers:[]}; }
const number = (v, c) => Number.isNaN(Number(v)) ? c.temp[v] ?? c.vars[v] ?? 0 : Number(v);
function check(nodes, c, world) {
  return nodes.every(({key, value:v}) => {
    if (key === 'NOT') return !check(v, c, world);
    if (key === 'custom_trigger_tooltip') return check(v.filter(n => n.key !== 'tooltip'), c, world);
    if (key === 'has_country_flag') return c.flags.includes(v);
    if (key === 'exists') return c.exists === (v === 'yes');
    if (key === 'has_socialist_government') return c.socialist === (v === 'yes');
    if (key === 'has_completed_focus') return c.focuses.includes(v);
    if (key === 'has_dynamic_modifier') return c.modifiers.includes(get(v, 'modifier'));
    if (key === 'check_variable') return v.every(n => n.op === '>' ? number(n.key,c) > number(n.value,c) : number(n.key,c) === number(n.value,c));
    if (world[key]) return check(v, world[key], world);
    throw Error('Unsupported trigger: ' + key);
  });
}
function run(nodes, c, world) {
  for (const {key, value:v} of nodes) {
    if (key === 'if') { if (check(get(v, 'limit'), c, world)) run(v.filter(n => n.key !== 'limit'), c, world); }
    else if (key === 'hidden_effect') run(v, c, world);
    else if (key === 'custom_effect_tooltip') continue;
    else if (key === 'add_political_power') c.pp += Number(v);
    else if (key === 'add_dynamic_modifier') c.modifiers.push(get(v, 'modifier'));
    else if (key === 'diplomatic_relation') { assert.equal(get(v,'relation'), 'non_aggression_pact'); c.pacts.push(get(v,'country')); }
    else if (effects.has(key)) run(effects.get(key), c, world);
    else if (world[key]) run(v, world[key], world);
    else if (/^(set|add_to|multiply)_(temp_)?variable$/.test(key)) {
      const target = key.includes('temp') ? c.temp : c.vars;
      for (const n of v) {
        const rhs = number(n.value, c);
        if (key.startsWith('set')) target[n.key] = rhs;
        else if (key.startsWith('add')) target[n.key] = (target[n.key] ?? 0) + rhs;
        else target[n.key] = (target[n.key] ?? 0) * rhs;
      }
    } else throw Error('Unsupported effect: ' + key);
  }
}
let cases = 0;
for (const completed of [false, true]) for (const victories of [0, 1, 9, 12]) for (let state = 0; state < 243; state++) {
  const world = Object.fromEntries(['RUS', ...tags].map(id => [id, country(id)]));
  const c = world.RUS;
  c.focuses.push('RUS_future_foreign_004');
  if (completed) c.focuses.push('RUS_future_foreign_035');
  c.vars[prefix + 'victories'] = victories;
  let encoded = state, eligible = 0;
  for (const tag of tags) {
    const status = encoded % 3; encoded = Math.floor(encoded / 3);
    world[tag].exists = status !== 0;
    world[tag].socialist = status === 2;
    eligible += status === 2 ? 1 : 0;
  }
  const count = completed ? eligible : 0;
  const refresh = effects.get('RUS_future_foreign_refresh_third_international_gendarme');
  for (let i = 0; i < 3; i++) run(refresh, c, world);
  assert.equal(c.vars[prefix + 'balkan_socialist_count'], eligible, 'Focus preview counts socialist Balkan countries before the focus');
  assert.equal(c.vars[prefix + 'balkan_count'], count);
  assert.equal(c.vars[prefix + 'volunteer_limit'], Math.min(1 + victories, 5));
  assert.ok(Math.abs(c.vars[prefix + 'volunteer_experience'] - (Math.min(1 + victories, 10) * .05 + count * .05)) < 1e-9);
  assert.ok(Math.abs(c.vars[prefix + 'non_core_attack'] - (victories * .005 + count * .002)) < 1e-9);
  assert.equal(c.modifiers.length, 1, 'Repeated refresh must not duplicate the spirit');
  if (completed) {
    run(get(focus('035'), 'completion_reward'), c, world);
    assert.equal(c.pp, eligible * 50);
    for (const tag of tags) {
      assert.equal(world[tag].pp, 0, 'Political Power belongs to Russia');
      assert.deepEqual(world[tag].pacts, world[tag].exists && world[tag].socialist ? ['ROOT'] : []);
      world[tag].socialist = false;
    }
    run(refresh, c, world);
    assert.equal(c.vars[prefix + 'balkan_count'], 0, 'Government changes remove the dynamic Balkan bonus');
    assert.equal(c.pp, eligible * 50, 'Refresh must not repeat Political Power rewards');
  }
  cases++;
}
const c = country('RUS');
// The agriculture minigame only decides whether the order line is listed in the focus
// tooltip; it must never lock the Paris-Moscow treaty itself.
assert.equal(get(focus('017'), 'available'), undefined, 'the Paris-Moscow treaty must not require agriculture');
const orderLine = get(focus('017'), 'completion_reward').find(n => n.key === 'if'
  && (get(n.value, 'limit') || []).some(x => x.key === 'has_country_flag' && x.value === 'RUS_nat_enabled'));
assert.ok(orderLine, 'the export-order tooltip must be conditional on RUS_nat_enabled');
assert.ok(orderLine.value.some(n => n.key === 'custom_effect_tooltip' && n.value === 'RUS_agri_export_orders_unlock_tt'));
assert.equal(check(get(orderLine.value, 'limit'), c, {}), false, 'the order line stays hidden without the minigame');
c.flags.push('RUS_nat_enabled');
assert.equal(check(get(orderLine.value, 'limit'), c, {}), true, 'the order line shows once the minigame is active');
assert.ok(JSON.stringify(get(focus('019'), 'completion_reward')).includes('RUS_future_foreign_balkan_aid_unlocked'));
assert.ok(!JSON.stringify(get(focus('019'), 'completion_reward')).includes('add_political_power'));
for (const lang of ['simp_chinese', 'english', 'russian']) {
  const text = read(`localisation/${lang}/RUS_future_foreign_policy_mechanics_l_${lang}.yml`);
  assert.ok(text.startsWith('\uFEFF'));
  for (const key of ['RUS_future_foreign_035_effect_tt', 'RUS_future_foreign_019_effect_tt', 'RUS_future_foreign_019_agri_orders_tt',
    'RUS_future_foreign_agriculture_enabled_tt', 'RUS_future_foreign_balkan_invite', 'RUS_future_foreign_balkan_invite_desc',
    'RUS_future_foreign_balkan_invite_available_tt'])
    assert.equal(text.split(/\r?\n/).filter(line => line.startsWith(' ' + key + ':')).length, 1);
  const effect = text.split(/\r?\n/).find(line => line.startsWith(' RUS_future_foreign_019_effect_tt:'));
  assert.ok(effect.includes('$RUS_future_foreign_balkan_invite$'), `${lang}: the faction invitation must be announced`);
}
// The Red Ghost of the Balkans: the minigame only gates the order line, and the new
// decision is offered to Balkan socialist regimes that are in no faction at all.
const decisionFile = parse(read('common/decisions/RUS_future_foreign_policy_decisions.txt'));
const decisions = new Map(get(decisionFile, 'RUS_Spreading_the_Revolution_decisions').map(n => [n.key, n.value]));
const invite = decisions.get('RUS_future_foreign_balkan_invite');
assert.ok(invite, 'the Balkan faction invitation decision must exist');
assert.equal(get(invite, 'cost'), 'RUS_diplomacy_pp_cost_20?20');
assert.equal(get(get(invite, 'target_root_trigger'), 'has_completed_focus'), 'RUS_future_foreign_019');
const inviteFilter = get(get(invite, 'target_trigger'), 'FROM');
assert.equal(get(inviteFilter, 'RUS_future_foreign_balkan_socialist_target'), 'yes');
assert.equal(get(inviteFilter, 'is_in_faction'), 'no');
const inviteRequirements = get(get(invite, 'available'), 'custom_trigger_tooltip');
assert.equal(get(inviteRequirements, 'is_faction_leader'), 'yes');
assert.equal(get(get(inviteRequirements, 'FROM'), 'is_in_faction'), 'no');
const inviteEffect = get(get(invite, 'complete_effect'), 'if');
const inviteTargetEffect = get(inviteEffect, 'FROM');
assert.equal(get(inviteTargetEffect, 'add_to_faction'), 'ROOT');
const agriLine = get(focus('019'), 'completion_reward').find(n => n.key === 'if'
  && (get(n.value, 'limit') || []).some(x => x.key === 'has_country_flag' && x.value === 'RUS_nat_enabled'));
assert.ok(agriLine, 'the Balkan order line must be conditional on RUS_nat_enabled');
assert.ok(agriLine.value.some(n => n.key === 'custom_effect_tooltip' && n.value === 'RUS_future_foreign_019_agri_orders_tt'));
console.log(`${cases} Balkan country-state/victory cases passed: bonus arithmetic, preview count, repeated refresh, pacts, 50 PP per country, agriculture display gate, faction invitation and localisation.`);
