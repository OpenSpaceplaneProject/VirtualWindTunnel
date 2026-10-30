# Goto et al. (JPP, doi:10.2514/1.B38037) C2H4/GOX RDE with a 30° plug. Inputs from the paper: geometry,
# equivalence ratio, mass flow (matched by setting plenum pressure), sea-level ambient. Predicted and
# compared: time-averaged pressure at z = 40 mm (their CTAP40), thrust, Isp, wave number and speed.
import json, math, os, subprocess, sys
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
subprocess.run(['node', os.path.join(HERE, 'gen.js')], check=True)
CJ = json.load(open(os.path.join(HERE, '../../tools/cj_c2h4o2.json')))
FLAGS = ['--enable-unsafe-webgpu', '--enable-features=Vulkan,WebGPU', '--use-vulkan=swiftshader', '--use-webgpu-adapter=swiftshader', '--disable-vulkan-surface', '--ignore-gpu-blocklist']
Di, De, Lc, half = 60.5e-3, 3.2e-3, 48e-3, math.radians(30)
Do = Di + 2 * De; Ac = math.pi / 4 * (Do ** 2 - Di ** 2); Lp = (Di / 2) / math.tan(half)
TESTS = {1: dict(mdot=0.125, phi=1.1, ctap=0.18, F=172, isp=141, waves=3, v=1748),
         2: dict(mdot=0.137, phi=1.2, ctap=0.18, F=183, isp=137, waves=3, v=1606),
         3: dict(mdot=0.141, phi=0.6, ctap=0.15, F=140, isp=102, waves=4, v=1471)}
def cfg(test, p0, dx, t_end, AtAw=0.12, EaRT=8.0, cells_rz=2):
    T = TESTS[test]; c = CJ['1.0' if T['phi'] == 1.0 else str(T['phi'])]; m = c['model']; D = c['cj']['D']
    g1, R1, T0 = m['gam1'], m['R1'], 300.0; M = D / math.sqrt(g1 * R1 * T0)
    TvN = T0 * (2 * g1 * M * M - (g1 - 1)) * ((g1 - 1) * M * M + 2) / ((g1 + 1) ** 2 * M * M)
    uvN = D * ((g1 - 1) * M * M + 2) / ((g1 + 1) * M * M)
    L = math.pi * (Di + De); H = Lc + Lp; nx = int(round(L / dx)); ny = int(round(H / dx))
    dt = 0.3 * dx / (1.8 * D); every = 40; samples = int(t_end / dt / every)
    return dict(nx=nx, ny=ny, L=L, H=H, areaDef=dict(type='plug', Ac=Ac, Lc=Lc, Do=Do, Di=Di, half=half), gas=m, chem=dict(theta=0.0, TvN=TvN, tau=2 * dx / uvN, k=uvN / (2 * dx), Tign=0.65 * TvN),
                AtAw=AtAw, p0=p0, T0=T0, pa=101325.0, closed=False, Dcj=D, dt=dt, probeY=40e-3,
                init=dict(h=10e-3, pFresh=101325.0, wIgn=10e-3, back=0.3 * L, pIgn=c['cj']['p'], TIgn=c['cj']['T'], uIgn=D * (1 - c['cj']['rho1'] / c['cj']['rho2']), TBurn=2500.0),
                samples=samples, every=every)
def summarise(r, c, frac=0.5):
    h = r['hist']; h2 = h[int(len(h) * (1 - frac)):]
    avg = lambda k: sum(x[k] for x in h2) / len(h2)
    # wave speed from peak displacement between consecutive samples (nearest forward peak)
    sp = []
    for a, b in zip(h2, h2[1:]):
        for p in a['peaks']:
            ds = [((q - p) % c['nx']) for q in b['peaks']]; ds = [d for d in ds if 0 < d < c['nx'] / 4]
            if ds: sp.append(min(ds) * c['L'] / c['nx'] / (b['t'] - a['t']))
    sp.sort(); v = sp[len(sp) // 2] if sp else float('nan')
    wv = sorted(x['waves'] for x in h2)[len(h2) // 2]
    mi, mo, F = avg('mIn'), avg('mOut'), avg('F')
    return dict(mIn=mi, mOut=mo, F=F, isp=F / (mi * 9.80665), pProbe=avg('pProbe'), pHead=avg('pHead'), waves=wv, v=v, t=h[-1]['t'], ms=r.get('ms'))
if __name__ == '__main__':
    test = int(sys.argv[1]) if len(sys.argv) > 1 else 1; dx = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5e-3
    t_end = float(sys.argv[3]) if len(sys.argv) > 3 else 0.6e-3; p0 = float(sys.argv[4]) if len(sys.argv) > 4 else 7e5
    with sync_playwright() as pw:
        b = pw.chromium.launch(args=FLAGS); pg = b.new_page(); pg.set_default_timeout(7200000)
        pg.goto('file://' + os.path.join(HERE, 'r.html'))
        target = TESTS[test]['mdot']; tries = []
        for it in range(int(os.environ.get('ITERS', '2'))):
            c = cfg(test, p0, dx, t_end); r = pg.evaluate('c => engine(c)', c)
            if 'err' in r: print('ERR', r['err']); break
            s = summarise(r, c); tries.append((p0, s['mIn']))
            print(json.dumps({'p0': p0, **{k: (round(v, 4) if isinstance(v, float) else v) for k, v in s.items()}}), flush=True)
            if abs(s['mIn'] / target - 1) < 0.03: break
            if len(tries) >= 2: (pa_, ma), (pb, mb) = tries[-2], tries[-1]; p0 = pb + (target - mb) * (pb - pa_) / (mb - ma)
            else: p0 = p0 * target / s['mIn']
        json.dump({'test': test, 'dx': dx, 'p0': p0, 'summary': s, 'ref': TESTS[test], 'hist': r['hist']}, open(os.path.join(HERE, f'goto_t{test}_dx{dx*1e3:.2f}.json'), 'w'))
        b.close()
