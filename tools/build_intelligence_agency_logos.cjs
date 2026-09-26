// Engine packing only: the transparent KGB artwork is retained under art_sources.
// Match KR's 233x119 two-frame strips and the selector's existing 0.7 scale.
const fs = require('node:fs');
const path = require('node:path');
const {createCanvas, loadImage} = require('@napi-rs/canvas');

const root = path.resolve(__dirname, '..');
const source = 'tools/art_sources/intelligence_agencies/kgb_cutout_source.png';
const output = 'gfx/interface/operatives/agencies/agency_logo_RUS_KGB.png';

async function generate() {
  const emblem = await loadImage(path.join(root, source));
  if (emblem.width !== 1254 || emblem.height !== 1254) {
    throw new Error('KGB master changed: review the export crop and native-size preview.');
  }
  // Visible subject bounds plus four source pixels of edge padding; faint distant
  // alpha specks in the generated canvas are outside this export rectangle.
  const crop = {x: 303, y: 3, width: 648, height: 1244};
  const height = 106;
  const width = height * crop.width / crop.height;
  const canvas = createCanvas(233, 119);
  const ctx = canvas.getContext('2d');
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = 'high';
  // Both states retain the same size and position. The odd total width follows
  // vanilla/KR strips exactly; each frame is sampled by the game as half a strip.
  for (const centerX of [58, 174.5]) {
    ctx.drawImage(emblem, crop.x, crop.y, crop.width, crop.height,
      centerX - width / 2, 4, width, height);
  }
  return {[output]: canvas.toBuffer('image/png')};
}

async function main() {
  const args = process.argv.slice(2);
  let write = false;
  let outputRoot = root;
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--write') write = true;
    else if (args[i] === '--check') continue;
    else if (args[i] === '--output-root' && args[i + 1]) outputRoot = path.resolve(args[++i]);
    else throw new Error(`Unknown or incomplete argument: ${args[i]}`);
  }
  if (args.includes('--write') && args.includes('--check')) throw new Error('Choose --write or --check.');
  const files = await generate();
  for (const [relative, content] of Object.entries(files)) {
    const destination = path.join(outputRoot, relative);
    if (write) {
      fs.mkdirSync(path.dirname(destination), {recursive: true});
      fs.writeFileSync(destination, content);
    } else if (!fs.existsSync(destination) || !fs.readFileSync(destination).equals(content)) {
      throw new Error(`Generated asset differs: ${relative}`);
    }
  }
  console.log(`${write ? 'Wrote' : 'Checked'} KGB agency strip: 233x119, two frames, 106px emblem height.`);
}

module.exports = {generate};
if (require.main === module) main().catch(error => {console.error(error.message); process.exitCode = 1;});
