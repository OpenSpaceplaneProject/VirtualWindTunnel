# Scores solver runs against references. python3 score.py results.jsonl [results_realgas.jsonl refs_realgas.json]
import json, math, sys
g = 1.4
def pitot_cp(M):  # Rayleigh pitot formula, perfect gas
    p02 = ((g + 1) ** 2 * M * M / (4 * g * M * M - 2 * (g - 1))) ** (g / (g - 1)) * (1 - g + 2 * g * M * M) / (g + 1)
    return (p02 - 1) / (0.5 * g * M * M)
def billig(M, cyl): return 0.386 * math.exp(4.67 / M ** 2) if cyl else 0.143 * math.exp(3.24 / M ** 2)
R = {}
for l in open(sys.argv[1]):
    r = json.loads(l); R[r['case']] = r
rows, out = [], []
def row(test, case, got, want, tol, ref):
    ok = None if tol is None else abs(got - want) <= tol * abs(want)
    rows.append(ok); out.append(f"| {test} | {case} | {got:.3f} | {want:.3f} | {'' if tol is None else f'±{tol*100:.0f}%'} | {100*(got/want-1):+.1f}% | {'—' if ok is None else ('pass' if ok else '**fail**')} | {ref} |")
out.append('| Test | Case | Solver | Reference | Tolerance | Error | Result | Reference source |'); out.append('|---|---|---|---|---|---|---|---|')
for name, r in R.items():
    c, s = r['cfg'], r['res']
    if 'err' in s or c.get('dep') or c.get('rg'): continue
    M = c['M']
    row('Stagnation pressure Cp', name, s['cpStag'], pitot_cp(M), 0.03, 'Rayleigh pitot formula')
    row('Stagnation temperature T₀/T∞', name, s['TmaxOverTinf'], 1 + 0.5 * (g - 1) * M * M, 0.02, 'adiabatic energy equation')
    if s['standoffR'] is not None: row('Shock standoff Δ/R', name, s['standoffR'], billig(M, c['cyl']), 0.10, 'Billig (1967) correlation')
print('\n'.join(out))
# grid convergence of drag: Richardson on R0 = 6, 8, 12 (refinement ratios are unequal, so solve for p numerically)
print('\nGrid convergence (drag coefficient, true-surface integral)\n')
print('| Case | R0=6 | R0=8 | R0=12 | Observed order | Extrapolated | R0=12 error vs extrapolated |'); print('|---|---|---|---|---|---|---|')
for kind in ['cyl', 'sph']:
    for M in [2, 4, 6, 10]:
        for dep in ['', ' dep1.0', ' dep2.0']:
            ks = [f'{kind} M{M} R{n}{dep}' for n in (6, 8, 12)]
            if not all(k in R and 'err' not in R[k]['res'] for k in ks): continue
            f = [R[k]['res']['cdSurface'] for k in ks]; h = [1 / 6, 1 / 8, 1 / 12]
            # f = f0 + C h^p: solve for p by bisection on (f1-f2)/(f2-f3)
            q = (f[0] - f[1]) / (f[1] - f[2]) if f[1] != f[2] else float('nan')
            p = None
            if q > 0:
                F = lambda p: (h[0] ** p - h[1] ** p) / (h[1] ** p - h[2] ** p) - q; lo, hi = 0.05, 6
                if F(lo) * F(hi) < 0:
                    for _ in range(80):
                        mid = 0.5 * (lo + hi); lo, hi = (mid, hi) if F(lo) * F(mid) > 0 else (lo, mid)
                    p = 0.5 * (lo + hi)
            if p: C = (f[1] - f[2]) / (h[1] ** p - h[2] ** p); f0 = f[2] - C * h[2] ** p
            print(f"| {kind} M{M}{dep} | {f[0]:.3f} | {f[1]:.3f} | {f[2]:.3f} | {p:.2f} | {f0:.3f} | {100*(f[2]/f0-1):+.1f}% |" if p else f"| {kind} M{M}{dep} | {f[0]:.3f} | {f[1]:.3f} | {f[2]:.3f} | not monotone | — | — |")
# deposition drag change per grid
print('\nDeposition: drag change against the same grid without the spot\n'); print('| Case | CD baseline | CD with spot | Change | Standoff with spot |'); print('|---|---|---|---|---|')
for name, r in R.items():
    if r['cfg'].get('dep') and 'err' not in r['res']:
        b = name.split(' dep')[0]
        if b in R: cb, cd = R[b]['res']['cdSurface'], r['res']['cdSurface']; print(f"| {name} | {cb:.3f} | {cd:.3f} | {100*(cd/cb-1):+.1f}% | {r['res']['standoffR']} |")
if len(sys.argv) > 3:
    refs = json.load(open(sys.argv[3])); RG = {json.loads(l)['case']: json.loads(l) for l in open(sys.argv[2])}
    print('\nReal gas (equilibrium air table) against Cantera equilibrium normal shock and stagnation\n'); print('| Case | Quantity | Solver real gas | Cantera | Error | Solver perfect gas |'); print('|---|---|---|---|---|---|')
    for tag, ref in refs.items():
        a, b = RG.get(f'cyl {tag} R8 real'), RG.get(f'cyl {tag} R8 perfect')
        if not a or 'err' in a['res']: print(f'| {tag} | run failed or missing | | | | |'); continue
        s, sp = a['res'], (b['res'] if b else {})
        print(f"| {ref['alt']} km, {ref['V']} m/s (M {ref['M']:.1f}) | stagnation Cp | {s['cpStag']:.3f} | {ref['cp_stag']:.3f} | {100*(s['cpStag']/ref['cp_stag']-1):+.1f}% | {sp.get('cpStag','')} |")
        print(f"| | stagnation density ρ/ρ∞ | {s['rhoStag']:.2f} | {ref['stag_rho']:.2f} | {100*(s['rhoStag']/ref['stag_rho']-1):+.1f}% | {sp.get('rhoStag','')} |")
        print(f"| | shock standoff Δ/R | {s['standoffR']} | (perfect gas Billig {billig(ref['M'], True):.3f}) | | {sp.get('standoffR','')} |")
print(f"\n{sum(1 for r in rows if r)}/{sum(1 for r in rows if r is not None)} reference checks passed")
