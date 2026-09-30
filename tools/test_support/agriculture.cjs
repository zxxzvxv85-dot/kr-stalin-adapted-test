/* Executes the actual agricultural script subset. Not a substitute for HOI4 runtime QA. */
const fs = require("node:fs");
const path = require("node:path");
const assert = require("node:assert/strict");
const root = path.resolve(__dirname, "../..");
const read = p => fs.readFileSync(path.join(root, p), "utf8");
function parse(text) {
  const tokens = text.match(/#[^\r\n]*|"(?:\\.|[^"\\])*"|[{}]|[<>!=]=?|[^\s{}=<>!#]+/g)
    .filter(t => !t.startsWith("#"));
  let i = 0;
  const scalar = t => t.startsWith('"') ? t.slice(1, -1) : t;
  function block(nested = false) {
    const out = [];
    while (i < tokens.length && tokens[i] !== "}") {
      const key = scalar(tokens[i++]);
      if (!["=", "<", ">", "<=", ">=", "!="].includes(tokens[i])) {
        out.push({ key, op: null, value: null });
        continue;
      }
      const op = tokens[i++];
      let value;
      if (tokens[i] === "{") { i++; value = block(true); }
      else { assert.ok(i < tokens.length, "Missing value"); value = scalar(tokens[i++]); }
      out.push({ key, op, value });
    }
    if (nested) assert.equal(tokens[i++], "}", "Unclosed block");
    return out;
  }
  const result = block();
  assert.equal(i, tokens.length, "Unexpected closing brace");
  return result;
}
const get = (b, k) => b.find(n => n.key === k)?.value;
const has = (b, k) => b.some(n => n.key === k);
const effects = new Map();
for (const file of [
  "common/scripted_effects/RUS_agricultural_quarterly_management_effects.txt",
  "common/scripted_effects/RUS_agri_development_effects.txt",
  "common/scripted_effects/RUS_agri_business_effects.txt",
  "common/scripted_effects/RUS_agri_export_orders_effects.txt",
  "common/scripted_effects/RUS_national_agriculture_effects.txt",
  "common/scripted_effects/RUS_agriculture_order_browser_effects.txt",
  "common/scripted_effects/RUS_stalin_maximalist_land_reform_effects.txt"
]) for (const n of parse(read(file))) {
  assert.ok(!effects.has(n.key), "Duplicate effect " + n.key);
  effects.set(n.key, n.value);
}
const triggers = new Map(parse(read("common/scripted_triggers/RUS_agri_development_triggers.txt")).map(n => [n.key, n.value]));
for (const node of parse(read("common/scripted_triggers/RUS_national_agriculture_triggers.txt"))) triggers.set(node.key, node.value);
// Use the loaded mod's socialist-government flag semantics for foreign buyers.
const socialistGovernment = parse(read("common/scripted_triggers/_government_scripted_triggers.txt"))
  .find(node => node.key === "has_socialist_government");
triggers.set(socialistGovernment.key, socialistGovernment.value);
const decisions = new Map(parse(read("common/decisions/RUS_agri_development_decisions.txt"))
  .flatMap(n => n.value).map(n => [n.key, n.value]));
const crops = ["wheat", "rye", "beet", "flax", "cotton"];
const machineryReservation = get(parse(read('common/dynamic_modifiers/RUS_national_agriculture_modifiers.txt'))[0].value, 'civilian_factory_use');
const ag = key => "RUS_agri_" + key;
const lr = key => "RUS_maximalist_land_reform_" + key;
function country() {
  return { id: "RUS", exists: true, government: "totalist", war: false, enemy: false,
    vars: {}, temps: {}, flags: {}, ideas: {}, focuses: [], events: [], seed: 187, surplus: 0, month: 9 };
}
function num(c, x, args = {}) {
  if (Array.isArray(x)) {
    let value = num(c, get(x, "value"), args);
    if (has(x, "subtract")) value -= num(c, get(x, "subtract"), args);
    if (has(x, "round")) value = Math.round(value);
    if (has(x, "clamp")) {
      const bounds = get(x, "clamp");
      value = Math.max(num(c, get(bounds, "min")), Math.min(num(c, get(bounds, "max")), value));
    }
    return value;
  }
  if (/^\$.+\$$/.test(x)) return num(c, args[x.slice(1, -1)]);
  if (Number.isFinite(Number(x))) return Number(x);
  if (x === 'political_power') return c.pp || 0;
  if (x === 'arms_factory') return c.buildings?.arms_factory || 0;
  if (x === 'num_of_military_factories' && c.states) return (c.offmapMilitary || 0) + c.states.filter(s => s.owner === c.id && s.controller === c.id).reduce((total, s) => total + (s.buildings.arms_factory || 0), 0);
  return c.temps?.[x] ?? c.vars?.[x] ?? 0;
}
const compare = (a, op, b) => ({
  "=": a === b, "<": a < b, ">": a > b, "<=": a <= b, ">=": a >= b, "!=": a !== b
})[op];
function check(b, c, donor = c, args = {}) {
  return b.filter(n => n.key !== "tooltip").every(n => {
    const v = n.value;
    switch (n.key) {
      case "NOT": return !check(v, c, donor, args);
      case "AND": case "hidden_trigger": case "custom_trigger_tooltip": case "custom_override_tooltip": return check(v, c, donor, args);
      case "OR": return v.some(x => check([x], c, donor, args));
      case "FROM": return check(v, donor.target, donor, args);
      case "ROOT": return check(v, donor, donor, args);
      case "always": return v === "yes";
      case "has_country_flag": return !!c.flags[v];
      case "has_idea": return Object.hasOwn(c.ideas, v);
      case "has_dynamic_modifier": return c.dynamic === get(v, 'modifier');
      case "has_variable": return Object.hasOwn(c.vars, v);
      case "has_completed_focus": return c.focuses.includes(v);
      case "exists": return c.exists === (v === "yes");
      case "country_exists": return (c.countries || []).includes(v);
      case "tag": return c.id === (v === "ROOT" ? donor.id : v);
      case "original_tag": return c.id === v;
      case "is_ai": return !!c.ai === (v === "yes");
      case "has_war_with": return c.enemy;
      case "has_government": return c.government === v;
      case "has_war": return c.war === (v === "yes");
      case "date": {
        const date = Number("1936." + String(c.month).padStart(2, "0") + "15");
        const parts = v.replace("[YEAR]", "1936").split(".");
        const threshold = Number(parts[0] + "." + parts[1].padStart(2, "0") + parts[2].padStart(2, "0"));
        return compare(date, n.op, threshold);
      }
      case "check_variable": return v.every(x => compare(num(c, x.key, args), x.op, num(c, x.value, args)));
      case "num_of_military_factories": return compare(num(c, n.key, args), n.op, num(c, v, args));
      case "arms_factory": return compare(num(c, n.key, args), n.op, num(c, v, args));
      case "is_controlled_by": return c.controller === (v === 'ROOT' ? donor.id : v);
      case "any_owned_state": return (c.states || []).some(s => s.owner === c.id && check(v, s, donor, args));
      default:
        if (triggers.has(n.key)) return check(triggers.get(n.key), c, donor, args) === (v === "yes");
        if (/^[A-Z0-9]{3}$/.test(n.key) && Array.isArray(v)) {
          const target = c.world?.[n.key];
          return !!target && check(v, target, donor, args);
        }
        throw Error("Unsupported trigger: " + n.key);
    }
  });
}
function exec(b, c, donor = c, args = {}) {
  let branch = false;
  for (const n of b) {
    const k = n.key, v = n.value;
    if (k === "if" || k === "else_if") {
      if (k === "if") branch = false;
      if (!branch && check(get(v, "limit"), c, donor, args)) { branch = true; exec(v.filter(x => x.key !== "limit"), c, donor, args); }
    } else if (k === "else") { if (!branch) exec(v, c, donor, args); branch = true; }
    else if (k === "while_loop_effect") {
      let iterations = 0;
      while (check(get(v, "limit"), c, donor, args)) {
        assert.ok(++iterations < 10000, "Loop limit");
        exec(v.filter(x => x.key !== "limit"), c, donor, args);
      }
    }
    else if (["hidden_effect", "effect", "text"].includes(k)) exec(v, c, donor, args);
    else if (k === 'random_owned_controlled_state') {
      // Selection identity is irrelevant to arithmetic tests; execute one eligible state.
      const state = (c.states || []).find(s => s.owner === c.id && s.controller === c.id && check(get(v, 'limit') || [], s, donor, args));
      if (state) exec(v.filter(n => n.key !== 'limit'), state, donor, args);
    }
    else if (k === 'remove_building') {
      const type = get(v, 'type');
      c.buildings[type] = Math.max(0, (c.buildings[type] || 0) - num(c, get(v, 'level')));
    }
    else if (k === "meta_effect") exec(get(v, "text"), c, donor, args);
    else if (k === "FROM") exec(v, donor.target, donor, args);
    else if (k === "clear_array") { c.arrays ||= {}; c.arrays[v] = []; }
    else if (k === "add_to_array") { c.arrays ||= {}; const a=v[0]; (c.arrays[a.key] ||= []).push(num(c,a.value,args)); }
    else if (k === "set_country_flag") {
      if (Array.isArray(v)) c.flags[get(v, "flag")] = num(c, get(v, "days"));
      else c.flags[v] = true;
    } else if (k === "clr_country_flag") delete c.flags[v];
    else if (k.endsWith("_variable") || k.endsWith("_temp_variable")) {
      const target = k.includes("temp") ? c.temps : c.vars;
      if (k.startsWith("clamp")) {
        const name = get(v, "var");
        target[name] = Math.max(num(c, get(v, "min")), Math.min(num(c, get(v, "max")), num(c, name)));
      } else {
        assert.equal(v.length, 1, k);
        const name = v[0].key, value = num(c, v[0].value, args), old = num(c, name);
        let result;
        if (k.startsWith("set_")) result = value;
        else if (k.startsWith("add_to")) result = old + value;
        else if (k.startsWith("subtract_from")) result = old - value;
        else if (k.startsWith("multiply")) result = old * value;
        else if (k.startsWith("divide")) result = old / value;
        else if (k.startsWith("modulo")) result = old % value;
        else throw Error(k);
        const precision = c.precision || 1e6;
        target[name] = Math.round(result * precision) / precision;
      }
    } else if (k === "random_list") {
      c.seed = (Math.imul(c.seed, 1664525) + 1013904223) >>> 0;
      const total = v.reduce((sum, x) => sum + Number(x.key), 0);
      let roll = c.seed / 4294967296 * total;
      for (const x of v) { roll -= Number(x.key); if (roll < 0) { exec(x.value, c, donor, args); break; } }
    } else if (k === "add_manpower") c.manpower = (c.manpower || 0) + num(c, v);
    else if (k === "add_threat") c.threat = (c.threat || 0) + num(c, v);
    else if (k === "add_timed_idea") c.ideas[get(v, "idea")] = num(c, get(v, "days"));
    else if (k === "add_ideas") c.ideas[v] = true;
    else if (k === "remove_ideas") {
      for (const id of Array.isArray(v) ? v.map(x => x.key) : [v]) delete c.ideas[id];
    } else if (k === "country_event") c.events.push(v);
    else if (k === "add_cic") c.surplus += num(c, v);
    else if (k === "add_stability") c.stability = (c.stability || 0) + num(c, v);
    else if (k === "add_political_power") c.pp = (c.pp || 0) + num(c, v);
    else if (k === "add_dynamic_modifier") c.dynamic = get(v, "modifier");
    else if (k === "remove_dynamic_modifier") { if (c.dynamic === get(v, 'modifier')) delete c.dynamic; }
    else if (k === "force_update_dynamic_modifier") {
      if (c.civCapacity !== undefined) c.vars.num_of_civilian_factories_available_for_projects = Math.max(0, c.civCapacity - num(c, machineryReservation));
    }
    else if (["custom_effect_tooltip", "effect_tooltip", "set_variable_to_random", "name",
      "RUS_stalin_update_advisor_relationship_multipliers", "RUS_stalin_apply_max_advisor_trait_tier"].includes(k)) {
      // External advisor refresh/engine presentation do not participate in arithmetic.
    } else if (effects.has(k)) {
      const params = Array.isArray(v) ? Object.fromEntries(v.map(x => [x.key, x.value])) : args;
      exec(effects.get(k), c, donor, params);
    } else throw Error("Unsupported effect " + k);
  }
}

module.exports = {parse, get, has, effects, triggers, country, num, check, exec, read, root, decisions, crops, ag, lr};
