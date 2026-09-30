// Node renderers share the Python writer and its batch/path validation.
const path = require('node:path');
const {spawnSync} = require('node:child_process');

function cli(render_outputs, {root, argv = process.argv.slice(2)} = {}) {
  const outputs = render_outputs();
  if (JSON.stringify(outputs) !== JSON.stringify(render_outputs())) {
    throw Error('Renderer is not deterministic within one process');
  }
  if (argv.length === 1 && argv[0] === '--json') {
    process.stdout.write(JSON.stringify(outputs));
    return;
  }
  const result = spawnSync('python', ['-B', path.join(__dirname, 'generation_io_bridge.py'), root, ...argv], {
    input: JSON.stringify(outputs), encoding: 'utf8', stdio: ['pipe', 'inherit', 'inherit'],
  });
  if (result.error) throw result.error;
  process.exitCode = result.status === null ? 1 : result.status;
}

module.exports = {cli};
