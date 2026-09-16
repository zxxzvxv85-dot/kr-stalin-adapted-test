/* Executes the actual agricultural script subset. Not a substitute for HOI4 runtime QA. */
const fs = require("node:fs");
const path = require("node:path");
const assert = require("node:assert/strict");
const root = path.resolve(__dirname, "..");
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
  return c.temps[x] ?? c.vars[x] ?? 0;
}
const compare = (a, op, b) => ({
  "=": a === b, "<": a < b, ">": a > b, "<=": a <= b, ">=": a >= b, "!=": a !== b
})[op];
function check(b, c, donor = c, args = {}) {
  return b.filter(n => n.key !== "tooltip").every(n => {
    const v = n.value;
    switch (n.key) {
      case "NOT": return !check(v, c, donor, args);
      case "AND": case "custom_trigger_tooltip": return check(v, c, donor, args);
      case "OR": return v.some(x => check([x], c, donor, args));
      case "FROM": return check(v, donor.target, donor, args);
      case "ROOT": return check(v, donor, donor, args);
      case "always": return v === "yes";
      case "has_country_flag": return !!c.flags[v];
      case "has_idea": return Object.hasOwn(c.ideas, v);
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
    else if (k === "add_political_power") c.pp = (c.pp || 0) + num(c, v);
    else if (k === "add_dynamic_modifier") c.dynamic = get(v, "modifier");
    else if (k === "force_update_dynamic_modifier") {
      if (c.civCapacity !== undefined) c.vars.num_of_civilian_factories_available_for_projects = Math.max(0, c.civCapacity - (c.vars.RUS_nat_factories || 0));
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
const run = (key, c) => exec(effects.get(ag(key)), c);
const set = (c, key, value) => c.vars[ag(key)] = value;
const value = (c, key) => c.vars[ag(key)] ?? 0;
const flag = (c, key) => c.flags[ag(key)] = true;
const unlocked = () => { const c = country(); flag(c, "management_unlocked"); return c; };
const completed = (balance = 0) => {
  const c = unlocked(); c.flags[lr("success")] = true; c.vars[lr("score")] = 100;
  set(c, "spendable_score", balance); return c;
};
const buy = (c, key) => exec(get(decisions.get(ag("exchange_" + key)), "complete_effect"), c);
const expire = c => {
  for (const bag of [c.ideas, c.flags]) for (const [key, days] of Object.entries(bag)) {
    if (typeof days === "number" && --bag[key] <= 0) delete bag[key];
  }
};
if (require.main !== module) {
  module.exports = {parse, get, effects, triggers, country, num, check, exec, read, root};
} else {
let tests = 0;
function test(name, fn) { fn(); tests++; console.log("PASS " + name); }
test("exchange decisions have valid IDs and scalar payment calls with unchanged prices", () => {
  const prices = {rations: 8, mechanisation: 10, reserves: 8, materials: 10,
    export: 6, machinery: 4, storage: 4, aid_food: 8, aid_technicians: 10, aid_front: 8};
  assert.equal(decisions.size, 10);
  assert.ok(!decisions.has("ai_will_do"));
  for (const [key, cost] of Object.entries(prices)) {
    const definition = decisions.get(ag("exchange_" + key));
    assert.equal(get(get(definition, "ai_will_do"), "base"), "0");
    let calls = 0;
    function visit(nodes) {
      nodes.forEach((node, index) => {
        if (node.key === ag("spend_score")) {
          calls++;
          assert.equal(node.value, "yes", "Payment must not use the failing COST parameter block");
          assert.equal(nodes[index-1].key, "set_temp_variable");
          assert.equal(get(nodes[index-1].value, ag("purchase_cost")), String(cost));
        }
        if (Array.isArray(node.value)) visit(node.value);
      });
    }
    visit(get(definition, "complete_effect"));
    assert.equal(calls, 1);
  }
  assert.ok(!read("common/scripted_effects/RUS_agri_development_effects.txt").includes("$COST$"));
});
test("payment checks funds, rejects missing or nonpositive cost, and consumes it once", () => {
  for (const cost of [undefined, 0, -8, 4, 6, 8, 10, 11]) {
    const c = completed(10);
    if (cost !== undefined) c.temps[ag("purchase_cost")] = cost;
    run("spend_score", c);
    const paid = cost > 0 && cost <= 10;
    assert.equal(value(c, "spendable_score"), paid ? 10-cost : 10);
    assert.equal(!!c.flags[ag("purchase_paid")], paid);
    assert.equal(c.temps[ag("purchase_cost")], 0);
    assert.equal(c.vars[lr("score")], 100);
    run("spend_score", c);
    assert.equal(value(c, "spendable_score"), paid ? 10-cost : 10);
    assert.ok(!c.flags[ag("purchase_paid")]);
  }
});
test("score is locked before reform and after failure", () => {
  for (const mode of ["not_started", "failed"]) {
    const c = unlocked(); set(c, "score_award", 6);
    if (mode === "failed") { c.flags[lr("failure")] = true; c.flags[lr("in_progress")] = true; }
    run("credit_score", c); assert.equal(value(c, "score_award"), 0); assert.equal(value(c, "spendable_score"), 0);
  }
});
test("success transfers excess once, spending preserves reform and stage", () => {
  const c = unlocked(); c.flags[lr("in_progress")] = true; c.vars[lr("score")] = 99;
  set(c, "score_award", 4); run("credit_score", c);
  assert.equal(c.vars[lr("score")], 103); assert.equal(c.vars[lr("stage")], 5);
  assert.equal(check(triggers.get(ag("exchange_unlocked")), c), false);
  c.flags[lr("success")] = true; delete c.flags[lr("in_progress")];
  run("refresh_score_account", c); run("refresh_score_account", c);
  assert.equal(c.vars[lr("score")], 100); assert.equal(value(c, "spendable_score"), 3);
  set(c, "score_award", 5); run("credit_score", c);
  buy(c, "rations"); assert.equal(value(c, "spendable_score"), 0);
  assert.equal(c.vars[lr("score")], 100); assert.equal(c.vars[lr("stage")], 5);
  assert.equal(value(c, "display_score"), 100);
  c.ideas.RUS_aleksey_ustinov_advisor = true;
  exec(effects.get(lr("apply_monthly_advisor_score")), c);
  assert.equal(value(c, "spendable_score"), 0);
});
test("quarter yield boundaries, half-limit ceiling and zero investment", () => {
  for (const [returns, expected] of [[9.999, 0], [10, 1], [10.499, 1], [10.5, 2], [11.999, 2], [12, 3]]) {
    const c = completed(); set(c, "total_investment", 10); set(c, "quarter_investment_limit", 20);
    set(c, "crop_returns", returns); run("award_quarter_score", c);
    assert.equal(value(c, "last_quarter_score"), expected);
  }
  for (const [invest, expected] of [[0, 0], [5, 0], [6, 3]]) {
    const c = completed(); set(c, "total_investment", invest); set(c, "quarter_investment_limit", 11);
    set(c, "crop_returns", invest * 1.25); run("award_quarter_score", c);
    assert.equal(value(c, "last_quarter_score"), expected);
  }
});
test("annual tiers, first-year proration, emergency cap and idempotency", () => {
  for (const [tier, points] of [["shortfall", 0], ["balanced", 2], ["surplus", 4], ["bumper", 6]]) {
    for (let quarters = 1; quarters <= 4; quarters++) for (const emergency of [false, true]) {
      const c = completed(); flag(c, "annual_tier_" + tier); set(c, "year_quarters", quarters);
      if (emergency) flag(c, "last_year_emergency");
      run("award_annual_score", c); run("award_annual_score", c);
      assert.equal(value(c, "spendable_score"), Math.floor(Math.min(points, emergency ? 4 : 6) * quarters / 4));
    }
  }
});
test("domestic two-slot cap, no repeat, expiry frees slots", () => {
  const c = completed(80); buy(c, "rations"); buy(c, "mechanisation");
  assert.equal(value(c, "spendable_score"), 62); assert.equal(value(c, "domestic_active_count"), 2);
  buy(c, "rations"); buy(c, "materials"); assert.equal(value(c, "spendable_score"), 62);
  for (let i = 0; i < 179; i++) expire(c);
  assert.ok(c.ideas.RUS_agri_development_rations);
  expire(c); buy(c, "materials"); assert.equal(value(c, "spendable_score"), 52);
  assert.equal(value(c, "domestic_active_count"), 1);
});
test("exports give exactly 15000, cooldown 180 days and no slot", () => {
  const c = completed(30); buy(c, "export"); buy(c, "export");
  assert.equal(c.surplus, 15000); assert.equal(value(c, "spendable_score"), 24);
  assert.equal(value(c, "domestic_active_count"), 0);
  for (let i = 0; i < 180; i++) expire(c);
  buy(c, "export"); assert.equal(c.surplus, 30000); assert.equal(value(c, "spendable_score"), 18);
});
test("aid requires valid peaceful socialist target, focus, funds and recipient slot", () => {
  const c = completed(30); c.focuses.push("RUS_future_foreign_003"); c.target = country(); c.target.id = "FRA";
  for (const field of ["exists", "enemy", "government"]) {
    const old = c.target[field]; c.target[field] = field === "exists" ? false : field === "enemy" ? true : "democratic";
    buy(c, "aid_food"); assert.equal(value(c, "spendable_score"), 30); c.target[field] = old;
  }
  buy(c, "aid_front"); assert.equal(value(c, "spendable_score"), 30);
  buy(c, "aid_food"); buy(c, "aid_technicians"); assert.equal(value(c, "spendable_score"), 22);
  assert.equal(c.target.ideas.RUS_agri_development_aid_food, 180);
  assert.equal(c.target.manpower, 10000);
  buy(c, "aid_food"); assert.equal(c.target.manpower, 10000);
  c.target.enemy = true;
  for (let i = 0; i < 180; i++) expire(c.target);
  assert.equal(value(c, "spendable_score"), 22);
  c.target.enemy = false; c.target.war = true; buy(c, "aid_front");
  assert.equal(value(c, "spendable_score"), 14);
  for (const fail of ["focus", "funds"]) {
    const x = completed(fail === "funds" ? 7 : 20); x.target = country(); x.target.id = "FRA";
    if (fail === "funds") x.focuses.push("RUS_future_foreign_003");
    const before = value(x, "spendable_score"); buy(x, "aid_food");
    assert.equal(value(x, "spendable_score"), before); assert.deepEqual(x.target.ideas, {});
  }
});
test("each successful foreign aid adds one threat to the donor, failed purchases add none", () => {
  for (const kind of ["food", "technicians", "front"]) {
    const definition = decisions.get(ag("exchange_aid_" + kind));
    assert.equal(get(get(get(definition, "complete_effect"), "effect_tooltip"), "add_threat"), "1.0");
    for (const failure of [null, "missing", "hostile", "government", "funds", "focus", "slot", "peace"]) {
      const c = completed(failure === "funds" ? 0 : 30);
      c.target = country(); c.target.id = "FRA"; c.target.war = true;
      if (failure !== "focus") c.focuses.push("RUS_future_foreign_003");
      if (failure === "missing") c.target.exists = false;
      if (failure === "hostile") c.target.enemy = true;
      if (failure === "government") c.target.government = "democratic";
      if (failure === "slot") c.target.ideas.RUS_agri_development_aid_food = 180;
      if (failure === "peace") c.target.war = false;
      const succeeds = failure === null || (failure === "peace" && kind !== "front");
      buy(c, "aid_" + kind);
      assert.equal(c.threat || 0, succeeds ? 1 : 0, kind + ": " + failure);
      assert.equal(c.target.threat || 0, 0);
      buy(c, "aid_" + kind);
      assert.equal(c.threat || 0, succeeds ? 1 : 0, "No increase when aid slot is occupied");
    }
  }
});
test("next-quarter purchases are exclusive, deferred, one-time and cross-year", () => {
  const c = completed(20); set(c, "season", 4); set(c, "capital", 10); run("start_quarter", c);
  buy(c, "machinery"); buy(c, "storage"); assert.equal(value(c, "spendable_score"), 16);
  run("set_base_rates", c); assert.equal(value(c, "wheat_base"), 1);
  set(c, "days_remaining", 0); run("settle_quarter", c);
  run("start_new_year", c); assert.ok(c.flags.RUS_agri_active_machinery);
  assert.equal(value(c, "wheat_base"), 1.35); assert.ok(!c.flags.RUS_agri_next_machinery);
  run("set_base_rates", c); assert.equal(value(c, "wheat_base"), 1.35);
  set(c, "days_remaining", 0); run("settle_quarter", c);
  assert.ok(!c.flags.RUS_agri_active_machinery); assert.equal(value(c, "wheat_base"), 1);
});
test("storage only rescues losses and clamps at break-even", () => {
  const c = completed(); flag(c, "active_storage");
  crops.forEach((crop, i) => set(c, crop + "_final", [.4, .9, 1, 1.25, .85][i]));
  run("apply_storage", c);
  assert.deepEqual(crops.map(x => value(c, x + "_final")), [.55, 1, 1, 1.25, 1]);
});
test("seasonal 0.40 losses, treaty, saturation and 1.50 maximum", () => {
  const c = completed(); set(c, "capital", 20); set(c, "season", 3); run("start_quarter", c);
  set(c, "weather", 0);
  c.focuses.push("RUS_future_foreign_017"); flag(c, "active_machinery"); run("set_base_rates", c);
  assert.equal(value(c, "cotton_base"), 1.45);
  set(c, "cotton_market", .15); run("calculate_final_rates", c); assert.equal(value(c, "cotton_final"), 1.5);
  delete c.flags.RUS_agri_active_machinery; run("set_base_rates", c);
  flag(c, "previous_dominant_wheat"); set(c, "wheat_investment", 10); set(c, "rye_investment", 1);
  run("refresh_totals", c); assert.ok(c.flags.RUS_agri_saturation_wheat);
  set(c, "wheat_market", -.2); run("calculate_final_rates", c); assert.equal(value(c, "wheat_final"), .4);
});
test("settlement pre-cap rewards, manual and auto, no duplicate settlement", () => {
  for (const manual of [true, false]) {
    const c = completed(); set(c, "capital", 30); set(c, "season", 2); run("start_quarter", c);
    set(c, "weather", 0);
    set(c, "order_1_crop", 0); set(c, "order_2_crop", 0);
    crops.forEach(x => set(c, x + "_capacity", 10));
    run("balance_allocation", c);
    if (manual) run("confirm_allocation", c);
    crops.forEach(x => set(c, x + "_market", .1));
    set(c, "days_remaining", 0); run("settle_quarter", c);
    assert.equal(value(c, "last_quarter_score"), 2); assert.equal(value(c, "capital"), 30);
    const balance = value(c, "spendable_score"); run("settle_quarter", c);
    assert.equal(value(c, "spendable_score"), balance); assert.equal(value(c, "year_quarters"), 1);
  }
});
test("all five independent market forecasts vary and GUI reads each own value", () => {
  const c = country(), counts = crops.map(() => [0, 0, 0]);
  const outcomes = [[0, 0, 0], [0, 0, 0], [0, 0, 0]];
  let mixed = 0;
  const gui = get(parse(read("common/scripted_guis/RUS_agricultural_quarterly_management.txt")), "scripted_gui")[0].value;
  const visibility = get(gui, "triggers");
  for (let i = 0; i < 3000; i++) {
    run("draw_market", c);
    const states = crops.map((crop, j) => {
      const v = value(c, crop + "_forecast"), state = v > 0 ? 2 : v < 0 ? 0 : 1;
      const actual = value(c, crop + "_market");
      outcomes[state][actual > 0 ? 2 : actual < 0 ? 0 : 1]++;
      counts[j][state]++;
      for (const label of ["weak", "stable", "strong"]) {
        assert.equal(check(get(visibility, ag(crop + "_forecast_" + label + "_visible")), c),
          label === ["weak", "stable", "strong"][state]);
      }
      return state;
    });
    if (new Set(states).size > 1) mixed++;
    assert.equal(["strong", "stable", "weak"].filter(x => c.flags[ag("forecast_" + x)]).length, 1);
  }
  assert.ok(mixed > 2700);
  for (const crop of counts) for (const n of crop) assert.ok(n > 800 && n < 1200);
  for (let state = 0; state < 3; state++) {
    const total = outcomes[state].reduce((a, b) => a + b);
    const rates = outcomes[state].map(n => n / total);
    const expected = [[.7, .2, .1], [.2, .6, .2], [.1, .2, .7]][state];
    rates.forEach((rate, i) => assert.ok(Math.abs(rate - expected[i]) < .04));
  }
  // GUI edits must not redraw either forecasts or hidden results.
  const before = crops.map(crop => [value(c, crop + "_forecast"), value(c, crop + "_market")]);
  set(c, "capital", 10); run("balance_allocation", c); run("confirm_allocation", c); run("reopen_allocation", c);
  assert.deepEqual(crops.map(crop => [value(c, crop + "_forecast"), value(c, crop + "_market")]), before);
});
test("real-month initialisation, emergency top-up, multi-year save round trip", () => {
  for (let month = 1; month <= 12; month++) {
    const c = completed(); c.month = month; run("start_initial_year", c);
    assert.equal(value(c, "season"), month < 3 || month === 12 ? 4 : Math.floor((month - 3) / 3) + 1);
  }
  let c = completed(9); set(c, "capital", .4); set(c, "season", 2); run("start_quarter", c);
  assert.equal(value(c, "capital"), 1); assert.ok(c.flags.RUS_agri_emergency_advance_used);
  run("start_new_year", c);
  for (let year = 0; year < 3; year++) {
    for (let q = 0; q < 4; q++) {
      c = JSON.parse(JSON.stringify(c));
      for (let day = 0; day < 90; day++) run("daily_update", c);
    }
    assert.equal(value(c, "year_quarters"), 4);
    assert.ok(c.flags.RUS_agri_annual_score_paid);
    assert.equal(Object.keys(c.ideas).filter(k => k.startsWith("RUS_agri_annual_")).length <= 1, true);
    const balance = value(c, "spendable_score");
    run("start_new_year", c);
    assert.equal(value(c, "spendable_score"), balance); assert.equal(value(c, "capital"), 10);
  }
});
test("new localisation BOM, keys, quoting, parity and decision references", () => {
  const allKeys = [];
  for (const lang of ["simp_chinese", "english", "russian"]) {
    const file = path.join(root, "localisation", lang, "RUS_agri_development_l_" + lang + ".yml");
    const bytes = fs.readFileSync(file); assert.equal(bytes.subarray(0, 3).toString("hex"), "efbbbf");
    const lines = bytes.toString("utf8").trimEnd().split(/\r?\n/).slice(1);
    const keys = lines.map(line => { assert.match(line, /^ [\w.]+:0 "(?:[^"\\]|\\.)*"$/); return line.trim().split(":")[0]; });
    assert.equal(new Set(keys).size, keys.length); allKeys.push(keys.sort());
    for (const [id] of decisions) for (const suffix of ["", "_desc", "_available_tt", "_effect_tt"]) assert.ok(keys.includes(id + suffix), id + suffix);
  }
  assert.deepEqual(allKeys[0], allKeys[1]); assert.deepEqual(allKeys[1], allKeys[2]);
});
test("unstarted minigame stays locked through 400 daily ticks", () => {
  const c = country(); c.focuses.push("RUS_future_foreign_002");
  const actions = get(parse(read("common/on_actions/RUS_agricultural_quarterly_management_on_actions.txt")), "on_actions");
  const daily = get(get(actions, "on_daily"), "effect");
  for (let day = 0; day < 400; day++) exec(daily, c);
  assert.deepEqual(c.vars, {}); assert.deepEqual(c.events, []);
  const categories = parse(read("common/decisions/categories/RUS_agricultural_quarterly_management_categories.txt"));
  const category = get(categories, "RUS_agricultural_quarterly_management_category");
  assert.equal(check(get(category, "visible"), c), false);
  const gui = get(parse(read("common/scripted_guis/RUS_agricultural_quarterly_management.txt")), "scripted_gui")[0].value;
  assert.equal(check(get(gui, "visible"), c), false);
  assert.equal(check(triggers.get(ag("exchange_unlocked")), c), false);
});
test("legacy launch stays hidden and optional agricultural proposal remains read-only", () => {
  const start = get(parse(read("common/decisions/RUS_agricultural_quarterly_management_decisions.txt"))[0].value,
    "RUS_start_agricultural_quarterly_management");
  const eventFile = parse(read("events/RUS_agricultural_quarterly_management_events.txt"));
  const event = id => eventFile.find(n => n.key === "country_event" && get(n.value, "id") === id).value;
  const outlook = event("RUS_agricultural_management.3"), proposal = event("RUS_agricultural_management.4");
  assert.equal(get(start, "fire_only_once"), "yes");
  assert.equal(get(outlook, "is_triggered_only"), "yes");
  assert.equal(get(proposal, "is_triggered_only"), "yes");
  const options = outlook.filter(n => n.key === "option").map(n => n.value);
  assert.equal(options.length, 2);
  assert.deepEqual(options[0].map(n => n.key), ["name"]);
  assert.deepEqual(options[1].map(n => n.key), ["name", "country_event"]);
  assert.equal(get(get(options[1], "country_event"), "id"), "RUS_agricultural_management.4");
  assert.deepEqual(get(proposal, "option").map(n => n.key), ["name"]);
  for (let month = 1; month <= 12; month++) {
    const c = country(); c.month = month; c.focuses.push("RUS_future_foreign_002");
    assert.equal(check(get(start, "visible"), c), false);
    exec(get(start, "complete_effect"), c);
    assert.equal(check(get(start, "visible"), c), false);
    assert.equal(c.events.length, 1);
    assert.equal(get(c.events[0], "id"), "RUS_agricultural_management.3");
    assert.equal(value(c, "season"), month < 3 || month === 12 ? 4 : Math.floor((month - 3) / 3) + 1);
    const before = JSON.stringify({...c, events: []});
    exec(options[0], c);
    assert.equal(c.events.length, 1);
    exec(options[1], c);
    assert.equal(get(c.events[1], "id"), "RUS_agricultural_management.4");
    exec(get(proposal, "option"), c);
    assert.equal(c.events.length, 2);
    assert.equal(JSON.stringify({...c, events: []}), before);
  }
  for (const prefix of ["RUS_agri_outlook_events", "RUS_vst_right_revolt"]) {
    const keys = [];
    for (const lang of ["simp_chinese", "english", "russian"]) {
      const folder = prefix === "RUS_vst_right_revolt" ? "replace" : lang;
      const bytes = fs.readFileSync(path.join(root, "localisation", folder, prefix + "_l_" + lang + ".yml"));
      assert.equal(bytes.subarray(0, 3).toString("hex"), "efbbbf");
      const lines = bytes.toString("utf8").trimEnd().split(/\r?\n/).slice(1);
      keys.push(lines.map(line => {
        assert.match(line, /^ [\w.]+:0 "(?:[^"\\]|\\.)*"$/);
        return line.trim().split(":")[0];
      }));
      assert.equal(new Set(keys.at(-1)).size, keys.at(-1).length);
    }
    assert.deepEqual(keys[0], keys[1]); assert.deepEqual(keys[1], keys[2]);
    assert.equal(keys[0].length, prefix === "RUS_vst_right_revolt" ? 3 : 7);
  }
});
test("annual event button cannot restart an already active year", () => {
  const option = get(get(parse(read("events/RUS_agricultural_quarterly_management_events.txt")), "country_event"), "option");
  const c = completed(20); flag(c, "annual_score_paid"); set(c, "year", 1);
  exec(option, c); assert.equal(value(c, "year"), 2);
  set(c, "capital", 17); exec(option, c);
  assert.equal(value(c, "year"), 2); assert.equal(value(c, "capital"), 17);
});
test("event declarations are unique and new keys do not duplicate a language", () => {
  const ids = new Set();
  for (const file of fs.readdirSync(path.join(root, "events")).filter(f => f.endsWith(".txt"))) {
    for (const event of parse(read("events/" + file)).filter(n => ["country_event", "news_event", "state_event"].includes(n.key))) {
      const id = get(event.value, "id");
      assert.ok(!ids.has(id), "Duplicate declared event " + id); ids.add(id);
    }
  }
  for (const lang of ["simp_chinese", "english", "russian"]) {
    const ours = ["RUS_agri_development", "RUS_agricultural_quarterly_management", "RUS_agri_business"]
      .map(stem => read("localisation/" + lang + "/" + stem + "_l_" + lang + ".yml")).join("\n");
    const keys = new Set([...ours.matchAll(/^ ([\w.]+):/gm)].map(m => m[1]));
    const counts = new Map();
    const intentionalOverrides = new Set(["RUS_agricultural_quarterly_management_category", "RUS_agricultural_quarterly_management_category_desc", "RUS_agri_annual_shortfall_desc"]);
    function scan(dir) {
      for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
        const file = path.join(dir, ent.name);
        if (ent.isDirectory()) scan(file);
        else if (ent.name.endsWith("_l_" + lang + ".yml")) {
          const text = fs.readFileSync(file, "utf8");
          for (const m of text.matchAll(/^ ([\w.]+):/gm)) if (keys.has(m[1])) {
            const locations = counts.get(m[1]) || [];
            locations.push(file); counts.set(m[1], locations);
          }
        }
      }
    }
    scan(path.join(root, "localisation"));
    for (const key of keys) {
      const locations = counts.get(key) || [];
      assert.equal(locations.length, intentionalOverrides.has(key) ? 2 : 1, "Duplicate key " + key + " in " + lang);
      if (intentionalOverrides.has(key)) assert.ok(locations.includes(path.join(root, "localisation/replace", "RUS_national_agriculture_ui_l_" + lang + ".yml")));
    }
  }
});
test("weather forecasts are fallible and extreme weather/markets remain uncommon", () => {
  const c = country(), counts = [[0, 0, 0], [0, 0, 0], [0, 0, 0]];
  let extremeWeather = 0, extremeMarkets = 0;
  const weatherValues = new Set(), marketValues = new Set();
  for (let i = 0; i < 6000; i++) {
    run("draw_weather", c); run("draw_market", c);
    const forecast = value(c, "weather_forecast"), actual = value(c, "weather");
    counts[forecast + 1][Math.sign(actual) + 1]++;
    weatherValues.add(actual);
    if (Math.abs(actual) === .4) extremeWeather++;
    for (const crop of crops) {
      const market = value(c, crop + "_market"); marketValues.add(market);
      if (Math.abs(market) === .4) extremeMarkets++;
    }
  }
  for (let i = 0; i < 3; i++) {
    const total = counts[i].reduce((a, b) => a + b, 0);
    assert.ok(total > 1700 && total < 2300);
    const expected = [[.7, .2, .1], [.2, .6, .2], [.1, .2, .7]][i];
    counts[i].forEach((n, j) => assert.ok(Math.abs(n / total - expected[j]) < .04));
  }
  for (const values of [weatherValues, marketValues])
    assert.deepEqual([...values].sort(), [-.4, -.2, -.1, 0, .1, .2, .4].sort());
  assert.ok(extremeWeather / 6000 > .07 && extremeWeather / 6000 < .13);
  assert.ok(extremeMarkets / 30000 > .07 && extremeMarkets / 30000 < .13);
});
test("shared weather reverses seasonal winners and losers without bypassing bounds", () => {
  const c = country();
  for (const [base, weather, market, final] of [
    [.4, .4, .4, 1.2], [1.25, -.4, -.4, .45],
    [1.25, .4, .4, 1.5], [.4, -.4, -.4, .4], [1, .2, 0, 1.2]
  ]) {
    set(c, "weather", weather);
    crops.forEach(crop => { set(c, crop + "_base", base); set(c, crop + "_market", market); });
    run("calculate_final_rates", c);
    crops.forEach(crop => assert.equal(value(c, crop + "_final"), final));
  }
  set(c, "season", 1); c.focuses.push("RUS_future_foreign_017");
  flag(c, "active_machinery"); flag(c, "saturation_beet"); flag(c, "active_storage");
  run("set_base_rates", c); set(c, "weather", .4); set(c, "beet_market", .4);
  run("calculate_final_rates", c); assert.equal(value(c, "beet_final"), 1.25);
  set(c, "weather", -.4); set(c, "beet_market", -.4);
  run("calculate_final_rates", c); run("apply_storage", c);
  assert.equal(value(c, "beet_final"), .55);
});
test("allocation edits, daily refresh and serialized saves never reroll hidden conditions", () => {
  let c = completed(); set(c, "capital", 10); set(c, "season", 2); run("start_quarter", c);
  const conditions = c => ["weather", "weather_forecast", ...crops.flatMap(x => [x + "_forecast", x + "_market"])]
    .map(x => value(c, x));
  const initial = conditions(c), seed = c.seed;
  for (const action of ["balance_allocation", "increase_wheat", "decrease_wheat", "clear_allocation",
    "confirm_allocation", "reopen_allocation", "refresh_totals", "set_base_rates", "daily_update"]) {
    run(action, c); assert.deepEqual(conditions(c), initial); assert.equal(c.seed, seed);
  }
  c = JSON.parse(JSON.stringify(c));
  run("daily_update", c); assert.deepEqual(conditions(c), initial); assert.equal(c.seed, seed);
  const daily = JSON.stringify(effects.get(ag("daily_update")));
  assert.ok(!daily.includes(ag("draw_weather")));
});
test("settlement snapshots survive a new quarter/year and ledger is read-only", () => {
  const gui = get(parse(read("common/scripted_guis/RUS_agricultural_quarterly_management.txt")), "scripted_gui")[0].value;
  const visibility = get(gui, "triggers"), clicks = get(gui, "effects");
  const ledger = get(clicks, ag("ledger_click"));
  const event = parse(read("events/RUS_agricultural_quarterly_management_events.txt"))
    .find(n => n.key === "country_event" && get(n.value, "id") === "RUS_agricultural_management.2").value;
  for (const season of [2, 4]) {
    const c = completed(); set(c, "season", season); set(c, "year", 3); set(c, "capital", 10);
    run("start_quarter", c);
    assert.equal(check(get(visibility, ag("ledger_visible")), c), false);
    exec(ledger, c); assert.equal(c.events.length, 0);
    set(c, "weather", -.4);
    crops.forEach((crop, i) => set(c, crop + "_market", [-.4, -.2, 0, .2, .4][i]));
    set(c, "days_remaining", 0); run("settle_quarter", c);
    assert.equal(value(c, "last_weather"), -.4);
    assert.equal(value(c, "last_season"), season); assert.equal(value(c, "last_year"), 3);
    crops.forEach((crop, i) => assert.equal(value(c, "last_" + crop + "_market"), [-.4, -.2, 0, .2, .4][i]));
    const snapshots = () => Object.fromEntries(Object.entries(c.vars).filter(([k]) => k.startsWith("RUS_agri_last_")));
    const saved = snapshots(), balance = value(c, "spendable_score");
    if (season === 4) run("start_new_year", c);
    assert.deepEqual(snapshots(), saved);
    assert.equal(check(get(visibility, ag("ledger_visible")), c), true);
    const before = JSON.parse(JSON.stringify(c));
    exec(ledger, c); exec(get(event, "option"), c);
    assert.equal(c.events.at(-1), "RUS_agricultural_management.2");
    assert.deepEqual(c.vars, before.vars); assert.deepEqual(c.flags, before.flags);
    assert.equal(c.seed, before.seed); assert.equal(value(c, "spendable_score"), balance);
  }
});
test("weather UI and ledger localization are complete, bounded and hide live actuals", () => {
  const sets = [];
  for (const lang of ["simp_chinese", "english", "russian"]) {
    const file = path.join(root, "localisation", lang, "RUS_agricultural_quarterly_management_l_" + lang + ".yml");
    const bytes = fs.readFileSync(file); assert.equal(bytes.subarray(0, 3).toString("hex"), "efbbbf");
    const lines = bytes.toString("utf8").trimEnd().split(/\r?\n/).slice(1).filter(x => x.trim());
    lines.forEach(line => assert.match(line, /^ [\w.]+:0 "(?:[^"\\]|\\.)*"$/));
    const keys = lines.map(line => line.trim().split(":")[0]).sort();
    assert.equal(new Set(keys).size, keys.length); sets.push(keys);
    const report = lines.find(l => l.startsWith(" RUS_agricultural_management.2.d:"));
    assert.equal([...report.matchAll(/\[\?(RUS_agri_[\w]+)\|/g)].every(m => m[1].startsWith("RUS_agri_last_")), true);
    for (const state of ["strong", "stable", "weak"]) {
      const text = lines.find(l => l.startsWith(" RUS_agri_weather_" + state + ":"));
      assert.ok(text && !text.includes("[?"), "Forecast label cannot disclose actual weather");
    }
  }
  assert.deepEqual(sets[0], sets[1]); assert.deepEqual(sets[1], sets[2]);
  const layout = read("interface/RUS_agricultural_quarterly_management.gui");
  assert.ok(layout.includes('name = "RUS_agri_ledger" position = { x = 406 y = 434 }'));
  assert.ok(406 + 123 <= 540 && 394 + 34 < 436);
  const gui = get(parse(read("common/scripted_guis/RUS_agricultural_quarterly_management.txt")), "scripted_gui")[0].value;
  const visibility = get(gui, "triggers"), c = country();
  for (let forecast = -1; forecast <= 1; forecast++) {
    set(c, "weather_forecast", forecast);
    ["weak", "stable", "strong"].forEach((s, i) =>
      assert.equal(check(get(visibility, ag("weather_" + s + "_visible")), c), forecast === i - 1));
  }
});
test("capacity tiers price only surplus units and preserve exact receipts", () => {
  for (const [units, expected] of [[0, 0], [3, 3.75], [4, 4.7], [5, 5.65], [6, 6.2], [10, 8.4]]) {
    const c = country(); set(c, "wheat_capacity", 3); set(c, "wheat_investment", units); set(c, "wheat_final", 1.25);
    run("apply_capacity_rates", c); run("compute_crop_returns", c);
    assert.equal(value(c, "wheat_return"), expected);
    assert.ok(value(c, "wheat_final") >= .4 && value(c, "wheat_final") <= 1.5);
  }
  const c = country(); set(c, "wheat_capacity", 3); set(c, "wheat_investment", 10); set(c, "wheat_final", 1.25);
  flag(c, "active_storage"); run("apply_capacity_rates", c); run("apply_storage", c); run("compute_crop_returns", c);
  assert.equal(value(c, "wheat_return"), 9.9);
  assert.equal(value(c, "wheat_final"), .99);
});
test("public capacity and distinct feasible orders draw once and favour off-season crops", () => {
  const capacityValues = new Set(), orderCounts = new Set();
  for (let season = 1; season <= 4; season++) for (let capital = 1; capital <= 30; capital++) {
    const c = completed(); c.seed = season * 997 + capital * 79;
    set(c, "capital", capital); set(c, "season", season); run("start_quarter", c);
    crops.forEach(x => { const cap = value(c, x + "_capacity"); capacityValues.add(cap); assert.ok(cap >= 3 && cap <= 5); });
    const one = value(c, "order_1_crop"), two = value(c, "order_2_crop");
    assert.ok(one >= 1 && one <= 5); assert.notEqual(one, two);
    assert.ok(value(c, "order_1_quantity") + value(c, "order_2_quantity") <= Math.min(capital, 20));
    orderCounts.add(two > 0 ? 2 : 1);
    if (season === 1) assert.ok([3, 4, 5].includes(one));
    if (season === 3) assert.ok([1, 2].includes(one));
    if (season === 4) assert.equal(one, 3);
    for (const slot of [1, 2]) {
      const q = value(c, "order_" + slot + "_quantity");
      assert.ok(q <= 4); assert.ok(q > 0 || slot === 2 && !two);
      assert.ok(Math.abs(value(c, "order_" + slot + "_cash") - q * .65) < 1e-6);
    }
    const conditions = () => [c.seed, ...crops.map(x => value(c, x + "_capacity")),
      ...[1, 2].flatMap(s => ["crop", "quantity", "cash"].map(k => value(c, "order_" + s + "_" + k)))];
    const saved = conditions();
    for (const action of ["balance_allocation", "clear_allocation", "confirm_allocation", "reopen_allocation", "daily_update"])
      run(action, c);
    assert.deepEqual(conditions(), saved);
    const loaded = JSON.parse(JSON.stringify(c));
    assert.deepEqual(loaded.vars, c.vars);
  }
  assert.deepEqual([...capacityValues].sort(), [3, 4, 5]); assert.equal(orderCounts.size, 2);
});
test("rotation increases only next-quarter fatigue, restores with reduced planting and survives years", () => {
  const c = completed(); set(c, "capital", 20); set(c, "season", 2); run("start_quarter", c);
  set(c, "wheat_investment", 6); set(c, "rye_investment", 4); run("refresh_totals", c);
  for (let i = 0; i < 5; i++) { run("refresh_totals", c); assert.equal(value(c, "wheat_fatigue"), 0); }
  for (let i = 1; i <= 5; i++) {
    run("update_rotation", c); run("refresh_business_display", c);
    assert.equal(value(c, "wheat_fatigue"), Math.min(i, 3)); assert.equal(value(c, "rye_fatigue"), 0);
  }
  run("start_new_year", c);
  assert.equal(value(c, "wheat_fatigue"), 3); assert.equal(value(c, "wheat_rotation_penalty"), .45);
  set(c, "wheat_investment", 2); set(c, "rye_investment", 2); run("refresh_totals", c);
  run("update_rotation", c); assert.equal(value(c, "wheat_fatigue"), 2);
  set(c, "rye_investment", 0); run("refresh_totals", c);
  run("update_rotation", c); assert.equal(value(c, "wheat_fatigue"), 3, "Small but concentrated investment still tires the crop");
  set(c, "wheat_investment", 0); run("refresh_totals", c);
  for (let i = 0; i < 5; i++) run("update_rotation", c);
  assert.equal(value(c, "wheat_fatigue"), 0);
});
test("orders pay at settlement only and obey reform eligibility without affecting crop yield", () => {
  for (const mode of ["not_started", "in_progress", "success", "failure"]) {
    const c = unlocked(); set(c, "capital", 10); set(c, "season", 2); run("start_quarter", c);
    if (mode === "in_progress") c.flags[lr("in_progress")] = true;
    if (mode === "success") { c.flags[lr("success")] = true; c.vars[lr("score")] = 100; }
    if (mode === "failure") { c.flags[lr("in_progress")] = true; c.flags[lr("failure")] = true; }
    set(c, "order_1_crop", 1); set(c, "order_1_quantity", 3); set(c, "order_1_cash", 2.4);
    set(c, "order_2_crop", 2); set(c, "order_2_quantity", 2); set(c, "order_2_cash", 1.6);
    set(c, "wheat_investment", 3); set(c, "rye_investment", 1); run("refresh_totals", c);
    assert.equal(value(c, "preview_order_cash"), 2.4);
    assert.equal(value(c, "spendable_score"), 0);
    assert.equal(c.vars[lr("score")] || 0, mode === "success" ? 100 : 0);
    set(c, "weather", -.4); crops.forEach(x => set(c, x + "_market", -.4));
    run("confirm_allocation", c); set(c, "days_remaining", 0); run("settle_quarter", c);
    assert.equal(value(c, "last_orders_completed"), 1); assert.equal(value(c, "last_order_cash"), 2.4);
    assert.equal(value(c, "last_order_score"), ["in_progress", "success"].includes(mode) ? 1 : 0);
    assert.equal(value(c, "last_quarter_score"), value(c, "last_order_score"), "Losing crops must not score from order bonuses");
    const before = JSON.stringify(c); run("settle_quarter", c); assert.equal(JSON.stringify(c), before);
  }
});
test("zero confirmed investment cannot claim orders; auto-allocation uses its actual quantities", () => {
  const c = completed(); set(c, "capital", 10); set(c, "season", 2); run("start_quarter", c);
  run("clear_allocation", c); run("confirm_allocation", c); set(c, "days_remaining", 0); run("settle_quarter", c);
  assert.equal(value(c, "last_orders_completed"), 0); assert.equal(value(c, "last_order_score"), 0);
  assert.equal(value(c, "last_capital"), 10);
  set(c, "order_1_crop", 1); set(c, "order_1_quantity", 2); set(c, "order_1_cash", 1.6);
  set(c, "order_2_crop", 0); set(c, "wheat_investment", 9); run("refresh_totals", c);
  set(c, "days_remaining", 0); run("settle_quarter", c);
  assert.equal(value(c, "last_orders_completed"), 1);
  assert.equal(value(c, "last_order_cash"), 1.6);
});
test("baseline preview is weather-independent, includes reserves once and matches neutral settlement", () => {
  for (const season of [1, 2, 3, 4]) for (const support of ["none", "machinery", "storage"]) {
    const c = completed(); set(c, "capital", 20); set(c, "season", season); run("start_quarter", c);
    c.focuses.push("RUS_future_foreign_017");
    if (support !== "none") flag(c, "active_" + support);
    set(c, "wheat_fatigue", 2); flag(c, "previous_dominant_wheat");
    set(c, "wheat_investment", 8); set(c, "rye_investment", 2); set(c, "beet_investment", 3);
    set(c, "order_1_crop", 3); set(c, "order_1_quantity", 3); set(c, "order_1_cash", 2.4); set(c, "order_2_crop", 0);
    run("set_base_rates", c); run("refresh_totals", c);
    const baseline = () => ["preview_receipts", "preview_capital", "preview_profit", "preview_order_cash",
      ...crops.map(x => x + "_preview_return")].map(k => value(c, k));
    const before = baseline(), seed = c.seed;
    for (const weather of [-.4, .4]) {
      set(c, "weather", weather); crops.forEach(x => set(c, x + "_market", weather));
      run("refresh_totals", c); assert.deepEqual(baseline(), before); assert.equal(c.seed, seed);
    }
    assert.equal(value(c, "unallocated_funds"), 7);
    const expected = value(c, "preview_capital"), receipts = value(c, "preview_crop_returns");
    set(c, "weather", 0); crops.forEach(x => set(c, x + "_market", 0));
    run("confirm_allocation", c); set(c, "days_remaining", 0); run("settle_quarter", c);
    assert.equal(value(c, "last_capital"), expected);
    assert.equal(value(c, "crop_returns"), receipts);
  }
});
test("preview respects the capital ceiling and all public rows fit the existing panel", () => {
  const c = completed(); set(c, "capital", 30); set(c, "season", 2); run("start_quarter", c);
  set(c, "cotton_investment", 3); set(c, "order_1_crop", 5); set(c, "order_1_quantity", 3); set(c, "order_1_cash", 2.4);
  set(c, "order_2_crop", 0); run("refresh_totals", c);
  assert.equal(value(c, "preview_capital"), 30); assert.equal(value(c, "preview_profit"), 0);
  run("clear_allocation", c); assert.equal(value(c, "preview_receipts"), 0); assert.equal(value(c, "preview_capital"), 30);
  const layout = parse(read("interface/RUS_agricultural_quarterly_management.gui"));
  const panel = get(get(layout, "guiTypes"), "containerWindowType");
  assert.equal(get(get(panel, "size"), "height"), "610");
  for (const name of ["RUS_agri_preview_summary", "RUS_agri_order_1_line", "RUS_agri_order_2_line", "RUS_agri_export_fra_line", "RUS_agri_export_eng_line", ...crops.map(x => ag(x + "_business_value"))]) {
    const box = panel.find(x => Array.isArray(x.value) && get(x.value, "name") === name).value;
    const p = get(box, "position");
    assert.ok(Number(get(p, "x")) + Number(get(box, "maxWidth")) <= 540);
    assert.ok(Number(get(p, "y")) + Number(get(box, "maxHeight")) <= 610);
  }
});
test("treaty orders are additional, country-specific, random and bounded at quarter start", () => {
  for (const treaty of [false, true]) for (const countries of [[], ["FRA"], ["ENG"], ["FRA", "ENG"]]) {
    const seen = {fra: new Set(), eng: new Set()};
    const c = completed(); c.countries = countries;
    if (treaty) c.focuses.push("RUS_future_foreign_017");
    for (let i = 0; i < 150; i++) {
      set(c, "capital", i % 20 + 1); set(c, "season", i % 4 + 1); run("start_quarter", c);
      assert.ok(value(c, "order_1_crop") > 0, "Domestic orders remain present");
      for (const buyer of ["fra", "eng"]) {
        const crop = value(c, "export_" + buyer + "_crop"), quantity = value(c, "export_" + buyer + "_quantity");
        const eligible = treaty && countries.includes(buyer.toUpperCase());
        assert.equal(crop > 0, eligible);
        assert.equal(quantity > 0, eligible);
        if (eligible) {
          seen[buyer].add(crop);
          assert.ok(crop <= 5 && quantity <= 4 && quantity <= value(c, "quarter_investment_limit"));
        }
      }
      if (treaty && countries.length === 2) assert.notEqual(value(c, "export_fra_crop"), value(c, "export_eng_crop"));
    }
    for (const buyer of countries) if (treaty) assert.equal(seen[buyer.toLowerCase()].size, 5);
  }
});
test("foreign premiums affect only fully ordered units before clamps and storage", () => {
  const clamp = n => Math.max(.4, Math.min(1.5, n));
  for (const crop of crops) for (const actual of [false, true]) for (const base of [.4, 1, 1.45])
  for (const investment of [0, 3, 4, 8]) for (const weather of [-.9, 0, .8]) for (const storage of [false, true]) {
    const c = completed(); set(c, "capital", 20); set(c, "season", 1); run("start_quarter", c);
    set(c, "order_1_crop", 0); set(c, "order_2_crop", 0);
    set(c, "export_fra_crop", crops.indexOf(crop) + 1); set(c, "export_fra_quantity", 4);
    set(c, crop + "_investment", investment); set(c, crop + "_base", base);
    set(c, crop + "_capacity", 3); set(c, crop + "_fatigue", 1);
    set(c, "weather", weather); set(c, crop + "_market", .1);
    if (storage) flag(c, "active_storage");
    run("refresh_totals", c);
    if (actual) {
      run("calculate_final_rates", c); run("apply_capacity_rates", c);
      c.temps.RUS_agri_export_actual = 1; run("apply_export_premiums", c);
      run("apply_storage", c); run("compute_crop_returns", c);
    }
    const raw = base - value(c, crop + "_rotation_penalty") - (c.flags[ag("saturation_" + crop)] ? .15 : 0) + (actual ? weather + .1 : 0);
    let expected = 0;
    for (let unit = 1; unit <= investment; unit++) {
      const premium = investment >= 4 && unit <= 4 ? .1 : 0;
      expected += clamp(clamp(raw + premium) - (unit <= 3 ? 0 : unit <= 5 ? .3 : .7));
    }
    if (storage && expected < investment) expected = Math.min(investment, expected + investment * .15);
    assert.ok(Math.abs(value(c, crop + (actual ? "_return" : "_preview_return")) - expected) < .0001,
      JSON.stringify({crop,actual,base,investment,weather,storage,expected}));
  }
});
test("orders survive refresh and serialization, start next quarter, and reset missing buyers", () => {
  let c = completed(); c.countries = ["FRA", "ENG"]; set(c, "capital", 10); set(c, "season", 3); run("start_quarter", c);
  c.focuses.push("RUS_future_foreign_017"); run("refresh_totals", c);
  assert.equal(value(c, "export_fra_crop"), 0);
  run("start_quarter", c);
  const orders = () => ["fra", "eng"].map(b => [value(c, "export_" + b + "_crop"), value(c, "export_" + b + "_quantity")]);
  const before = orders(), seed = c.seed;
  for (let i = 0; i < 30; i++) {
    run("balance_allocation", c); run("confirm_allocation", c); run("reopen_allocation", c);
    c = JSON.parse(JSON.stringify(c)); run("daily_update", c);
    assert.deepEqual(orders(), before); assert.equal(c.seed, seed);
  }
  c.countries = []; run("start_quarter", c);
  assert.deepEqual(orders(), [[0, 0], [0, 0]]);
});
test("both export orders settle once with manual or automatic allocation and capital stays capped", () => {
  for (const manual of [false, true]) {
    const c = completed(); c.countries = ["FRA", "ENG"]; c.focuses.push("RUS_future_foreign_017");
    set(c, "capital", 30); set(c, "season", 2); run("start_quarter", c);
    set(c, "export_fra_crop", 1); set(c, "export_fra_quantity", 2);
    set(c, "export_eng_crop", 2); set(c, "export_eng_quantity", 2);
    set(c, "weather", 0); crops.forEach(x => set(c, x + "_market", 0));
    run("balance_allocation", c); if (manual) run("confirm_allocation", c);
    const preview = value(c, "preview_capital");
    set(c, "days_remaining", 0); run("settle_quarter", c);
    assert.equal(value(c, "capital"), preview); assert.ok(value(c, "capital") <= 30);
    const settled = JSON.stringify(c); run("settle_quarter", c); assert.equal(JSON.stringify(c), settled);
  }
});
test("export UI localization and focus reward resolve in all three languages", () => {
  const sets = [];
  for (const lang of ["simp_chinese", "english", "russian"]) {
    const file = "localisation/" + lang + "/RUS_agri_export_orders_l_" + lang + ".yml";
    assert.equal(fs.readFileSync(path.join(root, file)).subarray(0, 3).toString("hex"), "efbbbf");
    const lines = read(file).trimEnd().split(/\r?\n/).slice(1);
    lines.forEach(line => assert.match(line, /^ [\w.]+:0 "(?:[^"\\]|\\.)*"$/));
    sets.push(lines.map(line => line.trim().split(":")[0]));
    assert.equal(new Set(sets.at(-1)).size, 3);
  }
  assert.deepEqual(sets[0], sets[1]); assert.deepEqual(sets[1], sets[2]);
  const focus = parse(read("common/national_focus/00_RUS_future_foreign_policy_skeleton.txt"))
    .find(n => n.key === "shared_focus" && get(n.value, "id") === "RUS_future_foreign_017").value;
  assert.ok(get(focus, "completion_reward").some(n => n.key === "custom_effect_tooltip" && n.value === "RUS_agri_export_orders_unlock_tt"));
});
test("business localisation and dynamic crop names resolve in all three languages", () => {
  const keysets = [];
  const definitions = parse(read("common/scripted_localisation/RUS_agri_business_scripted_loc.txt"));
  for (const lang of ["simp_chinese", "english", "russian"]) {
    const p = "localisation/" + lang + "/RUS_agri_business_l_" + lang + ".yml";
    assert.equal(fs.readFileSync(path.join(root, p)).subarray(0, 3).toString("hex"), "efbbbf");
    const lines = read(p).trimEnd().split(/\r?\n/).slice(1);
    lines.forEach(l => assert.match(l, /^ [\w.]+:0 "(?:[^"\\]|\\.)*"$/));
    const keys = lines.map(l => l.trim().split(":")[0]).sort(); keysets.push(keys);
    assert.equal(new Set(keys).size, keys.length);
    const all = new Set([...read("localisation/" + lang + "/RUS_agricultural_quarterly_management_l_" + lang + ".yml").matchAll(/^ ([\w.]+):/gm)].map(m => m[1]).concat(keys));
    for (const def of definitions) for (const text of def.value.filter(n => n.key === "text"))
      assert.ok(all.has(get(text.value, "localization_key")));
  }
  assert.deepEqual(keysets[0], keysets[1]); assert.deepEqual(keysets[1], keysets[2]);
});
function baselineReceipts(c, allocation) {
  const total = allocation.reduce((a, b) => a + b, 0);
  let receipts = 0;
  crops.forEach((crop, i) => {
    const qty = allocation[i], cap = value(c, crop + "_capacity") || 10;
    const saturation = c.flags[ag("previous_dominant_" + crop)] && qty * 2 > total ? .15 : 0;
    const rate = Math.max(.4, Math.min(1.5, value(c, crop + "_base") - value(c, crop + "_rotation_penalty") - saturation));
    const middle = Math.min(2, Math.max(0, qty - cap)), excess = Math.max(0, qty - cap - 2);
    let ret = Math.min(qty, cap) * rate + middle * Math.max(.4, rate - .3) + excess * Math.max(.4, rate - .7);
    if (c.flags[ag("active_storage")] && ret < qty) ret = Math.min(qty, ret + qty * .15);
    receipts += ret;
  });
  for (const slot of [1, 2]) {
    const crop = value(c, "order_" + slot + "_crop"), qty = value(c, "order_" + slot + "_quantity");
    if (crop && qty && allocation[crop - 1] >= qty) receipts += value(c, "order_" + slot + "_cash");
  }
  return receipts;
}
function businessStrategy(c, strategy) {
  const limit = value(c, "investment_limit"), allocation = [0, 0, 0, 0, 0];
  if (strategy === "balanced") { for (let i = 0; i < limit; i++) allocation[i % 5]++; return allocation; }
  if (strategy === "concentrated") {
    const ranking = crops.map((crop, i) => [i, value(c, crop + "_base")]).sort((a, b) => b[1] - a[1]);
    allocation[ranking[0][0]] = Math.min(10, limit); allocation[ranking[1][0]] = Math.max(0, limit - 10); return allocation;
  }
  let best = allocation, bestProfit = 0;
  // Enumerate taking neither, either, or both orders, then invest only at positive marginal return.
  for (let mask = 0; mask < 4; mask++) {
    const trial = [0, 0, 0, 0, 0];
    for (const slot of [1, 2]) {
      const crop = value(c, "order_" + slot + "_crop");
      if (crop && mask & (1 << (slot - 1))) trial[crop - 1] = value(c, "order_" + slot + "_quantity");
    }
    if (trial.reduce((a, b) => a + b) > limit) continue;
    while (trial.reduce((a, b) => a + b) < limit) {
      let candidate = -1, gain = 0;
      const before = baselineReceipts(c, trial);
      for (let i = 0; i < 5; i++) if (trial[i] < 10) {
        trial[i]++; const marginal = baselineReceipts(c, trial) - before - 1; trial[i]--;
        if (marginal > gain + 1e-8) { gain = marginal; candidate = i; }
      }
      if (candidate < 0) break;
      trial[candidate]++;
    }
    const profit = baselineReceipts(c, trial) - trial.reduce((a, b) => a + b);
    if (profit > bestProfit) { bestProfit = profit; best = trial; }
  }
  return best;
}
test("multi-year public-information policies have bounded non-compounding capital", () => {
  for (const strategy of ["balanced", "concentrated", "public_baseline"]) {
    let sum = 0, capped = 0, max = 0, count = 0;
    for (let seed = 1; seed <= 240; seed++) {
      const c = completed(); c.seed = seed * 7919;
      for (let year = 0; year < 5; year++) {
        run("start_new_year", c); assert.equal(value(c, "capital"), 10);
        for (let quarter = 0; quarter < 4; quarter++) {
          const allocation = businessStrategy(c, strategy);
          crops.forEach((crop, i) => set(c, crop + "_investment", allocation[i]));
          run("refresh_totals", c);
          assert.ok(Math.abs(value(c, "preview_receipts") - baselineReceipts(c, allocation)) < .001);
          run("confirm_allocation", c); set(c, "days_remaining", 0); run("settle_quarter", c);
          assert.ok(value(c, "capital") >= 0 && value(c, "capital") <= 30);
        }
        const ending = value(c, "capital"); sum += ending; max = Math.max(max, ending);
        if (ending >= 30) capped++; count++;
      }
    }
    console.log(JSON.stringify({strategy, years: count, meanEndingCapital: +(sum / count).toFixed(2), capRate: +(capped / count).toFixed(3), max}));
    if (strategy === "public_baseline") {
      assert.ok(sum / count < 24, "Routine baseline strategy should not make the ceiling the normal result");
      assert.ok(capped / count < .1, "Do not rely on the capital cap to suppress runaway ordinary returns");
    }
  }
});
console.log(tests + " scripted regression groups passed. HOI4 runtime, rendering and native save loading still require live QA.");
}
