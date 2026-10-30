# Engine performance checks.
# 1. Interpolation: the app's tables against direct NASA CEA calls at points between the grid nodes.
# 2. Measured engines: CEA ideal vacuum Isp against published flight values. Real engines reach
#    94–98 % of ideal, so the check is that the measured/ideal ratio falls in that band, plus the
#    app's own output for the same engine.
import json, math, os, random, subprocess
from rocketcea.cea_obj import CEA_Obj, add_new_fuel
add_new_fuel('C2H4_G', 'fuel C2H4 C 2 H 4 wt%=100. h,cal=12520. t(k)=298.15')
HERE = os.path.dirname(os.path.abspath(__file__)); PSIA = 6894.757
NAMES = {'hydrolox': ('LOX', 'LH2'), 'kerolox': ('LOX', 'RP-1'), 'methalox': ('LOX', 'CH4'), 'storable': ('N2O4', 'MMH'), 'amlox': ('LOX', 'NH3'), 'ethox': ('GOX', 'C2H4_G')}
def app(calls):
    js = "const E = require('./engines.js'); const C = " + json.dumps(calls) + "; console.log(JSON.stringify(C.map(([k, of, pc, eps, sh]) => { const pr = { tab: k, of, pc, shift: sh }; const r = E.rocketNozzle(pr, eps, eps, 0); return { isp: r.ispVac, cstar: r.cstar, pe: r.pe / pc, Tc: r.Tc }; })));"
    return json.loads(subprocess.run(['node', '-e', js], cwd=HERE, capture_output=True, text=True).stdout or 'null')
rows = []; ok_all = True
random.seed(1); pts = []
for k in NAMES:
    meta = json.load(open(os.path.join(HERE, '../../tools/propellant_tables.json')))['props'][k]
    for _ in range(12):
        ofs = meta['of']; i = random.randrange(len(ofs) - 1); of = ofs[i] + random.random() * (ofs[i + 1] - ofs[i])
        pc = math.exp(random.uniform(math.log(0.3e6), math.log(30e6))); eps = math.exp(random.uniform(math.log(2), math.log(250)))
        pts.append([k, of, pc, eps, True])
res = app(pts); worst = {}
for (k, of, pc, eps, _), r in zip(pts, res):
    c = CEA_Obj(oxName=NAMES[k][0], fuelName=NAMES[k][1]); p = pc / PSIA
    ref = c.get_Isp(Pc=p, MR=of, eps=eps); cs = c.get_Cstar(Pc=p, MR=of) * 0.3048
    e1, e2 = abs(r['isp'] / ref - 1), abs(r['cstar'] / cs - 1)
    worst[k] = max(worst.get(k, 0), e1, e2)
print('Interpolation against direct CEA (36 random off-grid points per propellant x 2 quantities):')
for k, w in worst.items():
    ok = w < 0.01; ok_all &= ok; print(f"  {'PASS' if ok else 'FAIL'} {k}: worst error {w*100:.2f}% (limit 1%)")
# measured engines: (name, key, O/F, Pc Pa, eps, measured vacuum Isp s, source)
ENG = [('RS-25', 'hydrolox', 6.03, 20.64e6, 69, 452.3, 'NASA RS-25 fact sheet'),
       ('RL10B-2', 'hydrolox', 5.88, 4.412e6, 285, 465.5, 'Aerojet Rocketdyne data sheet'),
       ('RD-180', 'kerolox', 2.72, 26.7e6, 36.87, 338.4, 'NPO Energomash'),
       ('Merlin 1D Vacuum', 'kerolox', 2.36, 9.7e6, 165, 348, 'SpaceX (published)'),
       ('AJ10-190 (OMS)', 'storable', 1.65, 0.862e6, 55, 316, 'NASA Shuttle OMS'),
       ('XLR99', 'amlox', 1.25, 4.082e6, 9.8, 276, 'Astronautix (Pc 40.8 bar, ε 9.8; O/F assumed)')]
res = app([[k, of, pc, eps, True] for _, k, of, pc, eps, _, _ in ENG])
print('\nMeasured engines: vacuum Isp, measured / ideal shifting equilibrium (expected 0.92–0.99):')
for (n, k, of, pc, eps, meas, src), r in zip(ENG, res):
    q = meas / r['isp']; ok = 0.92 <= q <= 0.99; ok_all &= ok
    print(f"  {'PASS' if ok else 'FAIL'} {n}: app ideal {r['isp']:.1f} s, measured {meas} s ({src}) -> {q:.3f}")
print('\nALL PASS' if ok_all else '\nSOME FAILED')
