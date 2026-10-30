// Loads the app's engine code (from "// ── Engines ──" to the radiative-equilibrium helper) into Node.
const fs = require('fs');
const html = fs.readFileSync(__dirname + '/../../index.html', 'utf8');
const a = html.indexOf('// ── Engines ──'), b = html.indexOf('// Radiative-equilibrium wall temperature');
const src = 'const G0 = 9.80665; const atob = (s) => Buffer.from(s, "base64").toString("binary");\n' + html.slice(a, b) + '\nreturn { PROP_TAB, PROPELLANTS, propPerf, rocketNozzle, idealExpandedF, engPr };';
module.exports = new Function(src)();
