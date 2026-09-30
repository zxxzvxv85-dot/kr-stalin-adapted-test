#!/usr/bin/env node
// Read-only regression check for the Kamenev / All-Russian Union of Labour split.
//
// HOI4 keeps completed focus nodes rendered even after their allow_branch turns
// them hidden. The Kamenev transition tree and the historical Levitsky/Sulimov
// line reuse the same grid cells below RUS_internationalists, so a run that is
// pushed into the Kamenev tree *after* it already completed the historical line
// renders both trees in the same place. That is why the branch has to be
// committed once, on RUS_syndicalists (RUS_vst_course_committed), instead of
// being re-decided by the daily on_action.
//
// This tool reports:
//   * per-scenario collisions (must be zero), and
//   * the union overlap that appears when both branches are live at once.
//
// Usage: node tools/check_kamenev_vst_overlap.cjs [focusFile]
// Exit code is 1 when a single scenario overlaps; the union overlap is reported
// as the diagnostic that motivates the committed-flag guard.
const fs = require('fs');
const path = require('path');

const MOD_ROOT = path.resolve(__dirname, '..');
const DEFAULT_FOCUS = path.join(MOD_ROOT, 'common', 'national_focus', 'RUS focus (Russia).txt');

function tokenize(text) {
  const tokens = [];
  let i = 0;
  while (i < text.length) {
    const ch = text[i];
    if (ch === '#') { while (i < text.length && text[i] !== '\n') i += 1; continue; }
    if (ch === ' ' || ch === '\t' || ch === '\r' || ch === '\n') { i += 1; continue; }
    if (ch === '{' || ch === '}' || ch === '=') { tokens.push({ t: ch }); i += 1; continue; }
    if (ch === '"') {
      let s = '';
      i += 1;
      while (i < text.length && text[i] !== '"') { s += text[i]; i += 1; }
      i += 1;
      tokens.push({ t: 'val', v: s });
      continue;
    }
    let s = '';
    while (i < text.length && !' \t\r\n{}=#"'.includes(text[i])) { s += text[i]; i += 1; }
    tokens.push({ t: 'val', v: s });
  }
  return tokens;
}

function parseScript(text) {
  const tokens = tokenize(text);
  let p = 0;
  function parseStatements(inside) {
    const out = [];
    while (p < tokens.length) {
      const tk = tokens[p];
      if (tk.t === '}') { p += 1; if (inside) return out; continue; }
      if (tk.t !== 'val') { p += 1; continue; }
      const key = tk.v;
      p += 1;
      if (tokens[p] && tokens[p].t === '=') {
        p += 1;
        const nt = tokens[p];
        if (nt && nt.t === '{') { p += 1; out.push({ key, block: parseStatements(true) }); }
        else if (nt) { p += 1; out.push({ key, value: nt.v }); }
        else { out.push({ key }); }
      } else {
        out.push({ key });
      }
    }
    return out;
  }
  return parseStatements(false);
}

function serializeBlock(block) {
  return block
    .map((s) => (s.block ? `${s.key} = { ${serializeBlock(s.block)} }` : `${s.key} = ${s.value}`))
    .join(' ');
}

function evalStmt(s, ctx) {
  if (s.key === 'OR') return s.block.some((x) => evalStmt(x, ctx));
  if (s.key === 'AND') return s.block.every((x) => evalStmt(x, ctx));
  if (s.key === 'NOT') return !s.block.every((x) => evalStmt(x, ctx));
  if (s.key === 'if' || s.key === 'custom_override_tooltip') {
    const limit = s.block.find((x) => x.key === 'limit');
    return limit ? evalStmt(limit, ctx) : true;
  }
  const atom = s.block ? `${s.key} = { ${serializeBlock(s.block)} }` : `${s.key} = ${s.value}`;
  if (Object.prototype.hasOwnProperty.call(ctx.atoms, atom)) return ctx.atoms[atom];
  return ctx.defaultValue;
}

function evalBlock(block, ctx) {
  return block.every((s) => evalStmt(s, ctx));
}

const pick = (block, key) => block.filter((s) => s.key === key);

function scalar(block, key, fallback) {
  const s = pick(block, key)[0];
  if (!s || s.value === undefined) return fallback;
  return Number(s.value);
}

function collectFocusNodes(stmts, out = []) {
  for (const s of stmts) {
    if (s.key === 'focus' && s.block) out.push(s);
    else if (s.block) collectFocusNodes(s.block, out);
  }
  return out;
}

function loadFocuses(file) {
  const nodes = collectFocusNodes(parseScript(fs.readFileSync(file, 'utf8')));
  const focuses = [];
  for (const node of nodes) {
    const idStmt = pick(node.block, 'id')[0];
    if (!idStmt) continue;
    focuses.push({
      id: idStmt.value,
      rel: (pick(node.block, 'relative_position_id')[0] || {}).value || null,
      x: scalar(node.block, 'x', 0),
      y: scalar(node.block, 'y', 0),
      dynamic: String((pick(node.block, 'dynamic')[0] || {}).value) === 'yes',
      offsets: pick(node.block, 'offset').map((o) => ({
        x: scalar(o.block, 'x', 0),
        y: scalar(o.block, 'y', 0),
        trigger: pick(o.block, 'trigger')[0] || null,
      })),
      allow: pick(node.block, 'allow_branch')[0] || null,
      parents: pick(node.block, 'prerequisite')
        .flatMap((p) => pick(p.block, 'focus').map((f) => f.value)),
    });
  }
  return focuses;
}

// Positions follow the wiki rules: offsets stack, and allow_branch is inherited
// from the prerequisite chain when a focus does not declare its own.
function resolve(focuses, ctx) {
  const byId = new Map(focuses.map((f) => [f.id, f]));
  const cache = new Map();
  const inProgress = new Set();
  function chain(f) {
    if (cache.has(f.id)) return cache.get(f.id);
    if (inProgress.has(f.id)) return { x: 0, y: 0 };
    inProgress.add(f.id);
    const base = f.rel && byId.has(f.rel) ? chain(byId.get(f.rel)) : { x: 0, y: 0 };
    inProgress.delete(f.id);
    let x = base.x + f.x;
    let y = base.y + f.y;
    for (const off of f.offsets) {
      if (off.trigger && !evalBlock(off.trigger.block, ctx)) continue;
      x += off.x;
      y += off.y;
    }
    const result = { x, y };
    cache.set(f.id, result);
    return result;
  }
  for (const f of focuses) {
    f.pos = chain(f);
    f.ownAllow = f.allow ? evalBlock(f.allow.block, ctx) : null;
  }
  const visCache = new Map();
  function effectiveVisible(f) {
    if (visCache.has(f.id)) return visCache.get(f.id);
    visCache.set(f.id, true);
    let ok;
    if (f.ownAllow !== null) ok = f.ownAllow;
    else if (f.parents.length === 0) ok = true;
    else ok = f.parents.every((p) => (byId.has(p) ? effectiveVisible(byId.get(p)) : true));
    visCache.set(f.id, ok);
    return ok;
  }
  for (const f of focuses) f.visible = effectiveVisible(f);
  return focuses;
}

const KAMENEV = 'has_country_flag = RUS_auto_kamenev_vst_left_path';
const RETIRED = 'has_country_flag = RUS_kamenev_focus_tree_retired';

function scenarioAtoms({ kamenev, retired }) {
  return {
    'RUS_VST = yes': true,
    [KAMENEV]: kamenev,
    [RETIRED]: retired,
    'has_country_flag = RUS_stalin_has_defeated_zinoviev': retired,
    'always = yes': true,
    'has_completed_focus = RUS_syndicalists': true,
    'has_completed_focus = RUS_russian_congress': true,
    'has_completed_focus = RUS_internationalists': true,
    'is_ai = no': true,
    'is_ai = yes': false,
  };
}

function visibleSet(file, cfg) {
  const ctx = { atoms: scenarioAtoms(cfg), defaultValue: false };
  return resolve(loadFocuses(file), ctx).filter((f) => f.visible && !f.dynamic);
}

function collisions(list) {
  const byCell = new Map();
  for (const f of list) {
    const key = `${f.pos.x},${f.pos.y}`;
    if (!byCell.has(key)) byCell.set(key, []);
    byCell.get(key).push(f.id);
  }
  return [...byCell].filter(([, ids]) => ids.length > 1).sort((a, b) => a[0].localeCompare(b[0]));
}

const file = process.argv[2] || DEFAULT_FOCUS;
const SCENARIOS = [
  ['historical (RUS_vst_course_committed)', { kamenev: false, retired: false }],
  ['kamenev transition', { kamenev: true, retired: false }],
  ['kamenev retired (Stalin won)', { kamenev: true, retired: true }],
];

console.log(`focus file: ${file}`);
let bad = 0;
const sets = {};
for (const [label, cfg] of SCENARIOS) {
  const list = visibleSet(file, cfg);
  sets[label] = list;
  const hits = collisions(list);
  console.log(`scenario ${label}: visible=${list.length} collisions=${hits.length}`);
  for (const [cell, ids] of hits) {
    bad += 1;
    console.log(`  OVERLAP ${cell}: ${ids.join(', ')}`);
  }
}

const historical = sets[SCENARIOS[0][0]];
const kamenev = sets[SCENARIOS[1][0]];
const historicalIds = new Set(historical.map((f) => f.id));
const union = [...historical, ...kamenev.filter((f) => !historicalIds.has(f.id))];
const unionHits = collisions(union);
console.log('');
console.log('--- both branches rendered at once (the state the committed guard prevents) ---');
console.log(`union visible=${union.length} collisions=${unionHits.length}`);
for (const [cell, ids] of unionHits) console.log(`  ${cell}: ${ids.join(', ')}`);

process.exitCode = bad === 0 ? 0 : 1;
