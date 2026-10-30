// Pull the RDE solver (RDE_WGSL + rdeCreate) out of the app so the tests run the shipped code.
const fs = require('fs');
const h = fs.readFileSync(__dirname + '/../../index.html', 'utf8');
const a = h.indexOf('// ── RDE ──'), b = h.indexOf('// ── end RDE ──');
fs.writeFileSync(__dirname + '/rde_src.js', h.slice(a, b));
