import goto, json, os
from playwright.sync_api import sync_playwright
os.environ['FEED'] = 'res'
with sync_playwright() as pw:
    b = pw.chromium.launch(args=goto.FLAGS); pg = b.new_page(); pg.set_default_timeout(3600000)
    pg.goto('file://' + os.path.join(goto.HERE, 'r.html'))
    c = goto.cfg(1, 8.5e5, 1e-3, 2e-5); c['teeth'] = dict(n=3, depth=0.5)
    r = pg.evaluate('c => engine(c)', c)
    print(r.get('err'))
    for h in r['hist'][::max(1, len(r['hist']) // 6)]: print({k: h[k] for k in ['t', 'mIn', 'pHead', 'pPl', 'F']}, 'amp', h['amp'][:4])
    b.close()
