import goto, json, os, time
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    b = pw.chromium.launch(args=goto.FLAGS); pg = b.new_page(); pg.set_default_timeout(3600000)
    pg.goto('file://' + os.path.join(goto.HERE, 'r.html'))
    c = goto.cfg(1, 7e5, 0.5e-3, 0.03e-3); t = time.time(); r = pg.evaluate('c => engine(c)', c)
    print('wall', round(time.time() - t, 1), 's for', c['samples'] * c['every'], 'steps', r.get('err'))
    for h in r['hist'][::3]: print({k: (round(v, 5) if isinstance(v, float) else v) for k, v in h.items() if k != 'peaks'})
    b.close()
