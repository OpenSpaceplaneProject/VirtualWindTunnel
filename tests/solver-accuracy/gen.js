// Pull the compressible solver kernels out of the app so the harness runs the shipped code.
const fs = require('fs');
const html = fs.readFileSync(__dirname + '/../../index.html', 'utf8');
const js = html.split('<script>')[1].split('</script>')[0];
const o = new Function(js.split('const GRIDS')[0] + ';return {EULER_WGSL};')();
fs.writeFileSync(__dirname + '/eul_src.js', 'window.EULER_WGSL = ' + JSON.stringify(o.EULER_WGSL) + ';');
