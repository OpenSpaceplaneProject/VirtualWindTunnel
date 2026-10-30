import json, math, os, sys
sys.argv=['x']; exec(open('run1d.py').read().split("res = {}")[0])
with sync_playwright() as pw:
    b = pw.chromium.launch(args=FLAGS); pg = b.new_page(); pg.set_default_timeout(3600000)
    pg.goto('file://' + os.path.join(HERE, 'r.html'))
    name='C2H4-O2 stoich'; dx=0.4e-3; M = model(name, dx); L = 0.24; nx = int(round(L / dx)); D = M['Dcj']; dt = 0.3 * dx / (1.8 * D)
    cfg = dict(nx=nx, ny=2, L=L, H=2 * dx, areaDef=dict(type='const', Ac=1.0), gas=M['gas'], chem=M['chem'], AtAw=0.1, p0=0.0, T0=300.0, pa=101325.0, closed=True, Dcj=D, dt=dt,
               init=dict(h=1.0, pFresh=101325.0, wIgn=0.01, back=0.5 * L, pIgn=CJ[name]['cj']['p'], TIgn=CJ[name]['cj']['T'], uIgn=D * (1 - CJ[name]['cj']['rho1'] / CJ[name]['cj']['rho2']), TBurn=3000.0), samples=4, every=150, stride=6)
    print(json.dumps(M['gas'])); 
    for o in pg.evaluate('c => prof(c)', cfg): print(o['t'], o['row'][:60])
    b.close()
