import goto, json, os, sys
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    b = pw.chromium.launch(args=goto.FLAGS); pg = b.new_page(); pg.set_default_timeout(3600000)
    pg.goto('file://' + os.path.join(goto.HERE, 'r.html'))
    for pa in [101325.0, 1000.0]:
        c = goto.cfg(1, 7e5, 1e-3, 1e-4); c['pa'] = pa; c['init']['pFresh'] = max(pa, 2e4); c['every'] = 100
        out = pg.evaluate('([c, n]) => snaps(c, n)', [c, 6])
        print(pa, [(round(o['t']*1e6), round(o['pmax']/1e5,1), o['nanc']) for o in out])
    b.close()
