# Chapman–Jouguet detonation states with Cantera (equilibrium products), and the two-γ model constants
# the RDE solver uses. CJ speed is the minimum wave speed over equilibrium states on the Hugoniot
# (the tangency of the Rayleigh line). Usage: python3 tools/cj.py
import cantera as ct, math, json, os

def hug_state(g, rho1, p1, h1, rho2, Tguess):
    # equilibrium state at density rho2 satisfying the Hugoniot h2 - h1 = ½(p2 - p1)(1/rho1 + 1/rho2)
    T = Tguess
    for _ in range(60):
        g.TD = T, rho2; g.equilibrate('TV')
        f = g.enthalpy_mass - h1 - 0.5 * (g.P - p1) * (1 / rho1 + 1 / rho2)
        dT = 1.0; g.TD = T + dT, rho2; g.equilibrate('TV')
        f2 = g.enthalpy_mass - h1 - 0.5 * (g.P - p1) * (1 / rho1 + 1 / rho2)
        step = -f / ((f2 - f) / dT); T = max(300.0, T + max(-500, min(500, step)))
        if abs(step) < 1e-3: break
    g.TD = T, rho2; g.equilibrate('TV'); return T

def cj(mech, X, T1=300.0, p1=101325.0):
    g = ct.Solution(mech); g.TPX = T1, p1, X; rho1, h1 = g.density, g.enthalpy_mass
    gam1 = g.cp_mass / g.cv_mass; R1 = ct.gas_constant / g.mean_molecular_weight; X0 = g.X.copy()
    best = None; T = 3000.0
    def w(r):
        nonlocal T
        g.TPX = T1, p1, X0
        T = hug_state(g, rho1, p1, h1, r * rho1, T)
        return math.sqrt(max(g.P - p1, 0) / (rho1 * (1 - 1 / r))), g.P, g.T, g.mean_molecular_weight
    lo, hi = 1.3, 2.4                      # golden-section search for the minimum speed in r = rho2/rho1
    gr = (math.sqrt(5) - 1) / 2
    a, b = hi - gr * (hi - lo), lo + gr * (hi - lo); fa, fb = w(a), w(b)
    for _ in range(40):
        if fa[0] < fb[0]: hi, b, fb = b, a, fa; a = hi - gr * (hi - lo); fa = w(a)
        else: lo, a, fa = a, b, fb; b = lo + gr * (hi - lo); fb = w(b)
    D, p2, T2, M2 = fa if fa[0] < fb[0] else fb
    # equilibrium isentropic exponent at the CJ state, from the CJ condition D - u2 = a2 (equilibrium)
    r = (fa if fa[0] < fb[0] else fb); rho2 = rho1 * (a if fa[0] < fb[0] else b)
    u2 = D * (1 - rho1 / rho2); a2 = D - u2; gs = a2 * a2 * rho2 / p2
    return dict(D=D, p=p2, T=T2, MW=M2, rho2=rho2, gamma_s=gs, gam1=gam1, R1=R1, MW1=g.mean_molecular_weight, rho1=rho1, T1=T1, p1=p1)

def two_gamma(c):
    # Model: reactants (γ1, R1, cv1) carry heat q per kg; products have γ2 = equilibrium γ at CJ and
    # R2 = R/MW_CJ. q is chosen so the model's CJ speed equals the equilibrium one (closed form for
    # a two-γ gas; Schwer & Kailasanath use the same calibration).
    g1, g2, R1, R2 = c['gam1'], c['gamma_s'], c['R1'], 8314.46 / c['MW']
    cp1, cp2 = g1 * R1 / (g1 - 1), g2 * R2 / (g2 - 1); p1, rho1, T1 = c['p1'], c['rho1'], c['T1']
    def Dmodel(q):
        h1 = cp1 * T1 + q; best = 1e9
        for i in range(1, 400):
            r = 1.05 + i * 0.005; v1, v2 = 1 / rho1, 1 / (r * rho1)
            # h2 = cp2 T2 = cp2 p2 v2 / R2; Hugoniot: cp2 p2 v2/R2 - h1 = ½(p2 - p1)(v1 + v2)
            k = cp2 * v2 / R2 - 0.5 * (v1 + v2); p2 = (h1 - 0.5 * p1 * (v1 + v2)) / k
            if p2 <= p1: continue
            best = min(best, math.sqrt((p2 - p1) / (rho1 * rho1 * (v1 - v2))))
        return best
    lo, hi = 1e5, 2e7
    for _ in range(60):
        m = 0.5 * (lo + hi)
        if Dmodel(m) < c['D']: lo = m
        else: hi = m
    return dict(gam1=g1, R1=R1, gam2=g2, R2=R2, q=0.5 * (lo + hi))

CASES = {   # name: (mechanism, mixture, published D_CJ m/s at 300 K / 1 atm or as stated, source)
    'H2-air stoich': ('gri30.yaml', 'H2:2, O2:1, N2:3.76', 1968, 'Shepherd/SDToolbox; Kaneshige & Shepherd detonation database'),
    'C2H4-O2 stoich': ('gri30.yaml', 'C2H4:1, O2:3', 2376, 'Kaneshige & Shepherd detonation database'),
    'CH4-O2 stoich': ('gri30.yaml', 'CH4:1, O2:2', 2392, 'Kaneshige & Shepherd detonation database'),
}
if __name__ == '__main__':
    res = {}
    for n, (m, X, Dp, src) in CASES.items():
        c = cj(m, X); tg = two_gamma(c); res[n] = dict(cj=c, model=tg, published=Dp, source=src)
        print(f"{n}: D_CJ {c['D']:.0f} m/s (published {Dp}, {100*(c['D']/Dp-1):+.2f}%), p_CJ/p1 {c['p']/c['p1']:.2f}, T_CJ {c['T']:.0f} K, γ_s {c['gamma_s']:.3f} | model q {tg['q']/1e6:.3f} MJ/kg γ1 {tg['gam1']:.3f} γ2 {tg['gam2']:.3f}")
    json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cj.json'), 'w'), indent=1)

def ethylene_oxygen(phi, p1=1.5 * 101325.0, T1=300.0):
    # C2H4 + 3 O2 at φ = 1; φ scales the fuel
    c = cj('gri30.yaml', f'C2H4:{phi}, O2:3', T1, p1); return dict(cj=c, model=two_gamma(c))

# Table for the app: two-γ constants and CJ state over equivalence ratio for the gaseous propellants,
# at 1.5 atm and 300 K (CJ speed changes by ~1 % between 1 and 3 atm).
APP_MIX = {'ethox': ('C2H4', 3.0, 1.0), 'gmethox': ('CH4', 2.0, 1.0), 'ghydrox': ('H2', 1.0, 2.0)}
APP_PHI = [0.5, 0.6, 0.8, 1.0, 1.2, 1.5, 2.0]
def app_table():
    out = {'phi': APP_PHI, 'mix': {}}
    for k, (fu, o2, nfu) in APP_MIX.items():
        rows = []
        for phi in APP_PHI:
            c = cj('gri30.yaml', f'{fu}:{nfu * phi}, O2:{o2}', 300.0, 1.5 * 101325.0); m = two_gamma(c)
            rows.append([round(m['gam1'], 4), round(m['R1'], 2), round(m['gam2'], 4), round(m['R2'], 2), round(m['q']), round(c['D'], 1), round(c['p'] / c['p1'], 3), round(c['T'], 1), round(c['rho2'] / c['rho1'], 4)])
        out['mix'][k] = rows; print(k, 'done', flush=True)
    return out
