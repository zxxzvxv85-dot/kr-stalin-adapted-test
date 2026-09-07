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
  "common/scripted_effects/RUS_stalin_maximalist_land_reform_effects.txt"
]) for (const n of parse(read(file))) {
  assert.ok(!effects.has(n.key), "Duplicate effect " + n.key);
  effects.set(n.key, n.value);
}
const triggers = new Map(parse(read("common/scripted_triggers/RUS_agri_development_triggers.txt")).map(n => [n.key, n.value]));
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
    else if (["hidden_effect", "effect", "text"].includes(k)) exec(v, c, donor, args);
    else if (k === "meta_effect") exec(get(v, "text"), c, donor, args);
    else if (k === "FROM") exec(v, donor.target, donor, args);
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
        else throw Error(k);
        target[name] = Math.round(result * 1e6) / 1e6;
      }
    } else if (k === "random_list") {
      c.seed = (Math.imul(c.seed, 1664525) + 1013904223) >>> 0;
      const total = v.reduce((sum, x) => sum + Number(x.key), 0);
      let roll = c.seed / 4294967296 * total;
      for (const x of v) { roll -= Number(x.key); if (roll < 0) { exec(x.value, c, donor, args); break; } }
    } else if (k === "add_manpower") c.manpower = (c.manpower || 0) + num(c, v);
    else if (k === "add_timed_idea") c.ideas[get(v, "idea")] = num(c, get(v, "days"));
    else if (k === "add_ideas") c.ideas[v] = true;
    else if (k === "remove_ideas") {
      for (const id of Array.isArray(v) ? v.map(x => x.key) : [v]) delete c.ideas[id];
    } else if (k === "country_event") c.events.push(v);
    else if (k === "add_cic") c.surplus += num(c, v);
    else if (["custom_effect_tooltip", "set_variable_to_random", "name",
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
    const ours = read("localisation/" + lang + "/RUS_agri_development_l_" + lang + ".yml");
    const keys = new Set([...ours.matchAll(/^ (\w+):/gm)].map(m => m[1]));
    let count = 0;
    function scan(dir) {
      for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
        const file = path.join(dir, ent.name);
        if (ent.isDirectory()) scan(file);
        else if (ent.name.endsWith("_l_" + lang + ".yml")) {
          const text = fs.readFileSync(file, "utf8");
          for (const m of text.matchAll(/^ (\w+):/gm)) if (keys.has(m[1])) count++;
        }
      }
    }
    scan(path.join(root, "localisation"));
    assert.equal(count, keys.size, "Duplicate new key in " + lang);
  }
});
console.log(tests + " scripted regression groups passed. HOI4 runtime, rendering and native save loading still require live QA.");
