import goto, json, os, sys, base64
from playwright.sync_api import sync_playwright
test, dx, every, n = int(sys.argv[1]), float(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
p0 = float(sys.argv[5]) if len(sys.argv) > 5 else 7e5
with sync_playwright() as pw:
    b = pw.chromium.launch(args=goto.FLAGS); pg = b.new_page(); pg.set_default_timeout(3600000)
    pg.goto('file://' + os.path.join(goto.HERE, 'r.html'))
    rz = float(sys.argv[6]) if len(sys.argv) > 6 else 4; c = goto.cfg(test, p0, dx, 1e-4, cells_rz=rz); c['every'] = every
    for k, o in enumerate(pg.evaluate('([c, n]) => snaps(c, n)', [c, n])):
        open(f'/tmp/claude-0/-home-claude/58293f53-d536-583f-8935-9c12432ae7fa/scratchpad/snap{k}.png', 'wb').write(base64.b64decode(o['png'].split(',')[1]))
        print(k, f"t {o['t']*1e6:.1f} us pmax {o['pmax']/1e5:.1f} bar nan {o['nanc']} mIn {o['mIn']:.3f} mOut {o['mOut']:.3f} F {o['F']:.0f}")
    b.close()
