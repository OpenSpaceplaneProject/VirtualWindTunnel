# python3 run.py cases.json results.jsonl  — each case in a fresh page, results appended as JSON lines.
import json, os, subprocess, sys
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
subprocess.run(['node', os.path.join(HERE, 'gen.js')], check=True)
flags = ['--enable-unsafe-webgpu', '--enable-features=Vulkan,WebGPU', '--use-vulkan=swiftshader', '--use-webgpu-adapter=swiftshader', '--disable-vulkan-surface', '--ignore-gpu-blocklist', '--disable-gpu-watchdog', '--disable-features=GPUWatchdog']
cases = json.load(open(sys.argv[1])); out = sys.argv[2]
only = sys.argv[3:]  # optional case names
with sync_playwright() as p:
    b = p.chromium.launch(args=flags)
    for c in cases:
        if only and c.get('name') not in only: continue
        pg = b.new_page(); pg.set_default_timeout(7200000)
        pg.goto('file://' + os.path.join(HERE, 'harness.html'))
        try: r = pg.evaluate('c => run(c)', c)
        except Exception as e: r = {'err': str(e)[:300]}
        open(out, 'a').write(json.dumps({'case': c.get('name'), 'cfg': {k: v for k, v in c.items() if k != 'eqt'}, 'res': r}) + '\n')
        print(c.get('name'), json.dumps(r)[:200], flush=True); pg.close()
    b.close()
