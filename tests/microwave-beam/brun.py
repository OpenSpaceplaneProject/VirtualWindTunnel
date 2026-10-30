# Runs the shipped beam kernel (SwiftShader WebGPU, headless Chromium) on uniform gas slabs and scores
# it against closed-form Drude propagation and the Taylor breakdown threshold. Usage: python3 brun.py
import json, math, os, subprocess, sys
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
subprocess.run(['node', os.path.join(HERE, 'gen.js')], check=True)
FLAGS = ['--enable-unsafe-webgpu', '--enable-features=Vulkan,WebGPU', '--use-vulkan=swiftshader', '--use-webgpu-adapter=swiftshader', '--disable-vulkan-surface', '--ignore-gpu-blocklist']
C = 2.998e8; ETA = 376.7; MN = 4.81e-26

def case(f, ne, T, rho, gam=1.4, P=1e3, dx=1e-3, nx=64, n=17, w0=3.0, zr=1e9, solidX=None):
    om = 2 * math.pi * f
    # solver units: ρ∞ = rho, U∞ = 1000 m/s, so rs = 1, es = e / U∞²; pick e so p comes out from T
    e = (rho / MN) * 1.380649e-23 * T / (rho * (gam - 1))
    return dict(dims=[nx, n, n], ax=[nx - 1, n / 2, n / 2, n / 2 - 0.5], bm=[nx / 2, w0, zr, P], ph=[om, dx, rho, 1000.0], rg=[gam, 0, 0, 0],
                rs=1.0, es=e / 1e6, ne=ne, T=T, solidX=solidX, _p=(gam - 1) * rho * e, _om=om)

def nu_model(rho, ne, T):  # the kernel's collision frequency, for the analytic side
    return rho / MN * 1e-19 * 6211 * math.sqrt(T) + 2.91e-11 * ne * (T / 11604.5) ** -1.5

def alpha(om, ne, nu):  # exact Drude power attenuation coefficient
    wp2 = 3182.6 * ne
    eps = complex(1 - wp2 / (om * om + nu * nu), wp2 * nu / (om * (om * om + nu * nu)))
    return 2 * om / C * (eps ** 0.5).imag

def colfrac(c):  # fraction of the Gaussian beam's power on the cells inside the column (as the kernel samples it)
    nx, n, _ = c['dims']; ay, az, R = c['ax'][1:4]; w = c['bm'][1]; s = 0
    for y in range(n):
        for z in range(n):
            r2 = (y + .5 - ay) ** 2 + (z + .5 - az) ** 2
            if r2 <= R * R: s += 2 / (math.pi * w * w) * math.exp(-2 * r2 / (w * w))
    return s

def taylor(p_torr, om, lam_cm):  # Taylor et al. as quoted by Cook et al. 2010 / Sci. Rep. 9, 18233 (2019); V/m rms
    nuc = 5.3e9 * p_torr
    return 100 * p_torr * math.sqrt(1 + (om / nuc) ** 2) * 3.75 * (6.64e5 / (p_torr ** 2 * lam_cm ** 2) + 6.4e4) ** 0.1875

rows = []
def check(name, got, want, tol, note=''):
    ok = abs(got - want) <= tol * max(abs(want), 1e-12)
    rows.append((name, got, want, tol, ok, note)); print(f"{'PASS' if ok else 'FAIL'}  {name}: {got:.5g} vs {want:.5g} (±{tol*100:.1f}%) {note}", flush=True)

with sync_playwright() as pw:
    b = pw.chromium.launch(args=FLAGS); pg = b.new_page(); pg.set_default_timeout(600000)
    pg.goto('file://' + os.path.join(HERE, 'b.html'))
    run = lambda c: pg.evaluate('c => run(c)', {k: v for k, v in c.items() if not k.startswith('_')})
    f = 35e9; om = 2 * math.pi * f; nc = om * om / 3182.6
    print(f"n_c at 35 GHz = {nc:.4g} m^-3 (textbook 1.24e16 f^2 = {1.24e16*35**2:.4g})")
    # 1. Transparent gas: everything that enters the column leaves upstream.
    c = case(f, 1e8, 300, 1e-3); r = run(c); t = r['tally']
    check('transparent: passed upstream', t[3], colfrac(c), 0.002)
    check('transparent: absorbed', t[0] + t[1] + 1e-9, 1e-9, 1.0, '(should be ~0)')
    # 2. Collisional underdense plasma: absorbed fraction over 63 cells vs 1 - exp(-αL), and e-folding along the axis.
    for ne_frac, T, rho in [(0.3, 3000, 1e-3), (0.05, 6000, 1e-2), (0.8, 3000, 3e-4)]:
        ne = ne_frac * nc; c = case(f, ne, T, rho); nu = nu_model(rho, ne, T); a = alpha(om, ne, nu)
        L = (c['dims'][0] - 2) * c['ph'][1]  # cells x = nx-1 .. 1
        dx = c['ph'][1]; L = (c['dims'][0] - 1) * dx
        r = run(c); t = r['tally']; cf = colfrac(c)
        want = cf * (1 - math.exp(-a * L))
        check(f'Drude absorption n/nc={ne_frac} ν/ω={nu/om:.2f}', t[1], want, 0.01)
        check(f'  energy closes (abs+pass+refl)', t[1] + t[3] + t[2], cf, 0.005)
        ax = r['axis']; i0, i1 = c['dims'][0] - 5, 10
        if ax[i1] > 0 and ax[i0] > 0:
            fit = math.log(ax[i0] / ax[i1]) / ((i0 - i1) * dx)
            check(f'  axial decay rate α', fit, a, 0.01)
    # 3. Overdense, weakly collisional: reflected at the first cell.
    c = case(f, 1.5 * nc, 3000, 1e-5); nu = nu_model(1e-5, 1.5 * nc, 3000); r = run(c)
    check(f'cut-off n/nc=1.5 ν/ω={nu/om:.3f}: reflected', r['tally'][2], colfrac(c), 0.002)
    # 4. Overdense but collision-dominated (ν > ω): no cut-off, absorbed instead.
    c = case(f, 1.5 * nc, 3000, 1.0); nu = nu_model(1.0, 1.5 * nc, 3000); r = run(c)
    a = alpha(om, 1.5 * nc, nu); L = (c['dims'][0] - 1) * c['ph'][1]
    check(f'collisional overdense ν/ω={nu/om:.1f}: reflected', r['tally'][2] + 1e-9, 1e-9, 1.0, '(should be 0)')
    check(f'  absorbed', r['tally'][1], colfrac(c) * (1 - math.exp(-a * L)), 0.01)
    # 5. Body: a wall at x <= 4 takes what reaches it.
    c = case(f, 1e8, 300, 1e-3, solidX=4); r = run(c)
    check('wall takes the transmitted power', r['tally'][4], colfrac(c), 0.002)
    # 6. Breakdown threshold vs pressure: bisect power until breakdown first appears, compare peak E_rms with Taylor.
    for fb, ptorr in [(110e9, 760), (110e9, 100), (110e9, 10), (110e9, 1), (303e9, 760)]:
        omb = 2 * math.pi * fb; T = 300; rho = ptorr * 133.322 * MN / (1.380649e-23 * T)
        dx = 2e-4; w0 = 5.0  # waist 1 mm
        lo, hi = 1.0, 1e10
        for _ in range(40):
            P = math.sqrt(lo * hi); c = case(fb, 1.0, T, rho, P=P, dx=dx, w0=w0, nx=24, n=21)
            bd = run(c)['tally'][0] > 0
            hi, lo = (P, lo) if bd else (hi, P)
            if hi / lo < 1.002: break
        # the kernel tests cell centres; the on-axis cell sits at r = 0, at the focus (x = nx/2 - 0.5 is a cell centre? no: use 1D peak)
        Imax = 2 * hi / (math.pi * (w0 * dx) ** 2)
        Erms = math.sqrt(Imax * ETA)
        want = taylor(ptorr, omb, w0 * dx * 100 / math.pi)
        check(f'breakdown {fb/1e9:.0f} GHz {ptorr} Torr: E_rms at threshold (kV/cm)', Erms / 1e5, want / 1e5, 0.01)
    # Published worked value: Sci. Rep. 9, 18233 (2019) quote the Taylor threshold at 303 GHz, 1 atm, beam radius λ,
    # as 37 kV/cm field amplitude (their own D and Te choices; this is a cross-check on the formula, not on data).
    lam = 2.998e8 / 303e9; amp = math.sqrt(2) * taylor(760, 2 * math.pi * 303e9, lam * 100 / math.pi) / 1e5
    check('Taylor threshold 303 GHz 1 atm, amplitude (kV/cm) vs published 37', amp, 37.0, 0.05)
    b.close()
print(f"\n{sum(r[4] for r in rows)}/{len(rows)} passed")
json.dump([dict(zip(['name', 'got', 'want', 'tol', 'ok', 'note'], r)) for r in rows], open(os.path.join(HERE, 'results.json'), 'w'), indent=1)
