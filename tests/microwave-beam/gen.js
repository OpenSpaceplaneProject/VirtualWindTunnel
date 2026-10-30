// Pull the beam kernel out of the app so the test runs the shipped code.
const fs = require('fs');
const html = fs.readFileSync(__dirname + '/../../index.html', 'utf8');
const js = html.split('<script>')[1].split('</script>')[0];
const head = js.split('const GRIDS')[0];
const o = new Function(head + ';return {BEAM_WGSL};')();
fs.writeFileSync(__dirname + '/beam_src.js', 'window.BEAM_WGSL = ' + JSON.stringify(o.BEAM_WGSL) + ';');
