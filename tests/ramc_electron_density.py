# RAM-C II nose-region peak electron density: equilibrium prediction (Cantera, 11-species air) against
# the reflectometer data (Grantham, NASA TN D-6062, 1970): at body station x/D = 0.15 the 20 % reflection
# onset means N_e,peak = 0.63 N_e,crit at that band, N_e,crit = 1.24e16 f² m⁻³ (f in GHz).
import cantera as ct, math
k_B = 1.380649e-23
def us76(h):   # geometric altitude (m) -> T (K), p (Pa), US Standard Atmosphere 1976, below 86 km
    r0 = 6356766.0; H = r0 * h / (r0 + h)
    L = [(0, 288.15, -0.0065, 101325.0), (11000, 216.65, 0.0, 22632.06), (20000, 216.65, 0.001, 5474.889), (32000, 228.65, 0.0028, 868.0187),
         (47000, 270.65, 0.0, 110.9063), (51000, 270.65, -0.0028, 66.93887), (71000, 214.65, -0.002, 3.956420)]
    for Hb, Tb, a, pb in reversed(L):
        if H >= Hb:
            T = Tb + a * (H - Hb)
            p = pb * math.exp(-9.80665 * 0.0289644 / 8.31432 * (H - Hb) / Tb) if a == 0 else pb * (Tb / T) ** (9.80665 * 0.0289644 / (8.31432 * a))
            return T, p
g = ct.Solution('airNASA9.yaml')
def ne(): return g.P / (k_B * g.T) * g['e-'].X[0]
def shock(h_alt, V):
    T1, p1 = us76(h_alt); g.TPX = T1, p1, 'N2:0.7808,O2:0.2195'; rho1 = g.density; h1 = g.enthalpy_mass
    eps = 0.1
    for _ in range(60):
        p2 = p1 + rho1 * V * V * (1 - eps); h2 = h1 + 0.5 * V * V * (1 - eps * eps)
        g.HPX = h2, p2, 'N2:0.7808,O2:0.2195'; g.equilibrate('HP')
        eps_n = rho1 / g.density
        if abs(eps_n - eps) < 1e-9: break
        eps = 0.5 * eps + 0.5 * eps_n
    post = (g.T, g.P, g.density, ne()); s2 = g.entropy_mass; h0 = h1 + 0.5 * V * V
    # stagnation: isentropic to rest, h = h0 at s = s2 (iterate on pressure)
    p = p2
    for _ in range(80):
        g.SPX = s2, p, 'N2:0.7808,O2:0.2195'; g.equilibrate('SP')
        dh = h0 - g.enthalpy_mass
        if abs(dh) < 1.0: break
        p *= math.exp(dh * g.density / p * 0.5)
    stag = (g.T, g.P, g.density, ne())
    return rho1, T1, post, stag
data = [(84.0, 3.348, 'S'), (80.0, 9.21, 'X'), (71.93, 35.0, 'Ka')]
V = 25000 * 0.3048
print(f"V = {V:.0f} m/s")
for alt, f, band in data:
    meas = 0.63 * 1.24e16 * f * f
    rho1, T1, post, stag = shock(alt * 1000, V)
    print(f"{alt:6.2f} km  {band:2s} measured peak N_e {meas:.2e} m^-3 | equilibrium: behind shock T {post[0]:.0f} K, N_e {post[3]:.2e};  stagnation T {stag[0]:.0f} K, N_e {stag[3]:.2e}  -> ratio {stag[3]/meas:.1f}x")

# The app's embedded table (NE_B64 in index.html) must give the same N_e at these stagnation states.
import base64, re, struct, os
html = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'index.html')).read()
raw = base64.b64decode(re.search(r'const NE_B64 = "([^"]+)"', html).group(1)); tab = struct.unpack(f'<{len(raw)//4}f', raw)
g.TPX = 200, 1e4, 'N2:0.79,O2:0.21'; off = g.int_energy_mass - g.cv_mass * 200
def lookup(rho, e):
    fr = min(max((math.log10(rho) + 8) / 9.5 * 39, 0), 38.999); fe = min(max((math.log10(e) - math.log10(1.2e5)) / (math.log10(8e7) - math.log10(1.2e5)) * 63, 0), 62.999)
    i, j = int(fr), int(fe); a, b = fr - i, fe - j; v = lambda i, j: tab[2 * (i * 64 + j)]
    return 10 ** ((1 - a) * ((1 - b) * v(i, j) + b * v(i, j + 1)) + a * ((1 - b) * v(i + 1, j) + b * v(i + 1, j + 1)))
bad = 0
for alt, f, band in data:
    rho1, T1, post, stag = shock(alt * 1000, V)
    g.TD = stag[0], stag[2]; g.equilibrate('TV'); e = g.int_energy_mass - off; app = lookup(stag[2], e)
    r = app / stag[3]; bad += not (0.95 < r < 1.05)
    print(f"{alt:6.2f} km  app table N_e {app:.2e} vs Cantera {stag[3]:.2e}  ({r:.2f}x)")
print('table check', 'PASS' if not bad else 'FAIL', '(±5 %)')
