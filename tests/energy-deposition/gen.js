const fs=require('fs');
const html=fs.readFileSync('../../index.html','utf8');
const js=html.split('<script>')[1].split('</script>')[0];
const head=js.split('const GRIDS')[0];
const o=new Function(head+';return {EULER_WGSL};')();
fs.writeFileSync('eul_src.js', 'window.EULER_WGSL = ' + JSON.stringify(o.EULER_WGSL) + ';');
