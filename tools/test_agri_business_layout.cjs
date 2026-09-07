// Measures the new compact rows with installed game font metrics, not a live GUI test.
const fs = require("node:fs");
const path = require("node:path");
const assert = require("node:assert/strict");
const root = path.resolve(__dirname, "..");
const fonts = process.argv[2];
assert.ok(fonts, "Pass the game's gfx/fonts directory");
for (const lang of ["simp_chinese", "english", "russian"]) {
  const metrics = new Map();
  const fontFiles = lang === "simp_chinese"
    ? fs.readdirSync(path.join(fonts, "chinese")).filter(f => /^hoi_16mbs_.*\.fnt$/.test(f)).map(f => path.join(fonts, "chinese", f))
    : [path.join(fonts, "hoi_16mbs.fnt"), ...(lang === "russian" ? [path.join(fonts, "hoi_16mbs_cryllic.fnt")] : [])];
  for (const f of fontFiles) {
    for (const line of fs.readFileSync(f, "utf8").split(/\r?\n/).filter(l => l.startsWith("char "))) {
      const pairs = Object.fromEntries([...line.matchAll(/(\w+)=\s*(-?\d+)/g)].map(m => [m[1], +m[2]]));
      metrics.set(pairs.id, pairs.xadvance);
    }
  }
  const keys = new Map();
  for (const stem of ["RUS_agri_business", "RUS_agricultural_quarterly_management"]) {
    const text = fs.readFileSync(path.join(root, "localisation", lang, stem + "_l_" + lang + ".yml"), "utf8");
    for (const m of text.matchAll(/^ ([\w.]+):0 "(.*)"$/gm)) keys.set(m[1], m[2]);
  }
  const width = text => [...text.replace(/§./g, "")].reduce((sum, c) => {
    assert.ok(metrics.has(c.codePointAt(0)), "Missing glyph " + c + " in " + lang);
    return sum + metrics.get(c.codePointAt(0));
  }, 0);
  const crop = ["wheat", "rye", "beet", "flax", "cotton"].map(x => keys.get("RUS_agri_" + x))
    .sort((a, b) => width(b) - width(a))[0];
  const status = ["RUS_agri_order_ready", "RUS_agri_order_pending"].map(x => keys.get(x))
    .sort((a, b) => width(b) - width(a))[0];
  const expand = text => text.replace(/\[RUSAgriOrder[12]Crop\]/g, crop)
    .replace(/\[RUSAgriOrder[12]Status\]/g, status)
    .replace(/\[RUSAgriOrderScoreReward\]/g, keys.get("RUS_agri_order_point_reward"))
    .replace(/\[\?([^|]+)\|(\d)\]/g, (_, key, decimals) =>
      key.endsWith("progress") ? "10" : decimals === "0" ? "5" : decimals === "2" ? "2.60" : "-30.0");
  const result = {};
  for (const [key, limit] of [["RUS_agri_preview_summary", 520], ["RUS_agri_business_header", 92],
    ["RUS_agri_order_1_line", 520], ["RUS_agri_order_2_line", 520], ["RUS_agri_wheat_business_value", 92]]) {
    const measured = width(expand(keys.get(key)));
    assert.ok(measured <= limit, lang + " " + key + " exceeds width: " + measured + "/" + limit);
    result[key] = measured;
  }
  console.log(lang, result);
}
