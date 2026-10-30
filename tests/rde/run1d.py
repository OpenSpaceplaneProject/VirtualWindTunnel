# 1D detonation check: the solver's detonation speed against the model CJ speed, over grid sizes.
import json, math, os, subprocess, sys
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
subprocess.run(['node', os.path.join(HERE, 'gen.js')], check=True)
CJ = json.load(open(os.path.join(HERE, '../../tools/cj.json')))
THETA = 8.0
FLAGS = ['--enable-unsafe-webgpu', '--enable-features=Vulkan,WebGPU', '--use-vulkan=swiftshader', '--use-webgpu-adapter=swiftshader', '--disable-vulkan-surface', '--ignore-gpu-blocklist']
def model(name, dx, cells_rz=4, EaRT=8.0):
    c = CJ[name]; m = c['model']; D = c['cj']['D']; T0, p1 = 300.0, 101325.0
    g1, R1 = m['gam1'], m['R1']; c1 = math.sqrt(g1 * R1 * T0); M = D / c1
    TvN = T0 * (2 * g1 * M * M - (g1 - 1)) * ((g1 - 1) * M * M + 2) / ((g1 + 1) ** 2 * M * M)
    Ea = EaRT * R1 * TvN
    # particle speed behind the lead shock (shock frame) sets the reaction length: L = u_vN · τ
    uvN = D * ((g1 - 1) * M * M + 2) / ((g1 + 1) * M * M)
    k = uvN / (cells_rz * dx) * math.exp(EaRT)
    return dict(gas=m, chem=dict(theta=THETA, TvN=TvN, tau=dx / uvN, k=uvN / dx, Tign=0.6 * TvN), Dcj=D, TvN=TvN)
res = {}
with sync_playwright() as pw:
    b = pw.chromium.launch(args=FLAGS); pg = b.new_page(); pg.set_default_timeout(3600000)
    pg.goto('file://' + os.path.join(HERE, 'r.html'))
    for name in ['C2H4-O2 stoich', 'H2-air stoich']:
        for dx in [0.4e-3, 0.2e-3, 0.1e-3]:
            M = model(name, dx); L = 0.24; nx = int(round(L / dx)); D = M['Dcj']
            dt = 0.3 * dx / (1.8 * D); tEnd = 0.4 * L / D; every = max(1, int(tEnd / dt / 24))
            cfg = dict(nx=nx, ny=2, L=L, H=2 * dx, areaDef=dict(type='const', Ac=1.0), gas=M['gas'], chem=M['chem'], AtAw=0.1, p0=0.0, T0=300.0, pa=101325.0, closed=True, Dcj=D, dt=dt,
                       init=dict(h=1.0, pFresh=101325.0, wIgn=0.01, back=0.5 * L, pIgn=CJ[name]['cj']['p'], TIgn=CJ[name]['cj']['T'], uIgn=D * (1 - CJ[name]['cj']['rho1'] / CJ[name]['cj']['rho2']), TBurn=3000.0), samples=24, every=every)
            r = pg.evaluate('c => det1d(c)', cfg)
            if 'err' in r: print(name, dx, r['err']); continue
            xs = r['xs'][len(r['xs']) // 2:]
            n = len(xs); mt = sum(t for t, _ in xs) / n; mx = sum(x for _, x in xs) / n
            Dn = sum((t - mt) * (x - mx) for t, x in xs) / sum((t - mt) ** 2 for t, _ in xs)
            pk = sum(r['ps'][len(r['ps']) // 2:]) / len(r['ps'][len(r['ps']) // 2:]) / 101325
            res[f'{name} dx={dx*1e3:.1f}mm'] = dict(D=Dn, Dcj=D, err=Dn / D - 1, ppeak=pk)
            print(f"{name} dx {dx*1e3:.1f} mm: D {Dn:.0f} m/s vs model CJ {D:.0f} ({100*(Dn/D-1):+.2f}%), peak p/p1 {pk:.1f} (CJ {CJ[name]['cj']['p']/101325:.1f})", flush=True)
    b.close()
json.dump(res, open(os.path.join(HERE, 'results_1d.json'), 'w'), indent=1)
