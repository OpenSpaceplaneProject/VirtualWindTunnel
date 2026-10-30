# Equilibrium-air tables for the app, from Cantera's 11-species air (airNASA9: N2 O2 NO N O, their
# ions, e-; NASA 9-coefficient thermodynamics). Axes: log10 density 1e-8..10^1.5 kg/m³ (40), log10
# internal energy 1.2e5..8e7 J/kg (64), energy zero at absolute zero for cold air.
# Each state is found by bisection on temperature with fixed-volume (TV) equilibria, which converge
# everywhere; the earlier UV equilibria failed at low density and high energy (185 of 2,560 points,
# filled from neighbours, so thin very hot air was too cool).
# Outputs: γ̃ = 1 + p/(ρe); κ = a²ρ/p with a² = (∂p/∂ρ)_s from TV equilibria,
#   (∂p/∂ρ)_s = p_ρ + p_T (p/ρ² − u_ρ)/u_T;  log10 electron density (m⁻³);  T (K).
import cantera as ct, numpy as np, math, json, base64, struct
k_B = 1.380649e-23
g = ct.Solution('airNASA9.yaml')
g.TPX = 200, 1e4, 'N2:0.79,O2:0.21'; u0, cv0 = g.int_energy_mass, g.cv_mass; off = u0 - cv0 * 200
NR, NE = 40, 64
lr = np.linspace(-8, 1.5, NR); le = np.linspace(math.log10(1.2e5), math.log10(8e7), NE)
def eq(T, rho):
    g.TDX = T, rho, 'N2:0.79,O2:0.21'; g.equilibrate('TV'); return g.int_energy_mass, g.P
def T_for(rho, target):
    lo, hi = 50.0, 80000.0
    for _ in range(80):
        mid = math.sqrt(lo * hi)
        if eq(mid, rho)[0] < target: lo = mid
        else: hi = mid
        if hi / lo < 1 + 1e-7: break
    return math.sqrt(lo * hi)
GT = np.zeros((NR, NE)); KA = np.zeros((NR, NE)); LNE = np.zeros((NR, NE)); TT = np.zeros((NR, NE))
for i, l in enumerate(lr):
    rho = 10 ** l
    for j, m in enumerate(le):
        e = 10 ** m; T = T_for(rho, e + off)
        u, p = eq(T, rho); n = p / (k_B * T); ne = n * g['e-'].X[0]
        dT = T * 1e-4; dr = rho * 1e-4
        uTp, pTp = eq(T + dT, rho); uTm, pTm = eq(T - dT, rho)
        urp, prp = eq(T, rho + dr); urm, prm = eq(T, rho - dr)
        uT = (uTp - uTm) / (2 * dT); pT = (pTp - pTm) / (2 * dT); ur = (urp - urm) / (2 * dr); pr = (prp - prm) / (2 * dr)
        a2 = pr + pT * (p / rho ** 2 - ur) / uT
        GT[i, j] = 1 + p / (rho * e); KA[i, j] = a2 * rho / p; LNE[i, j] = math.log10(max(ne, 1.0)); TT[i, j] = T
pack = lambda A, B: base64.b64encode(b''.join(struct.pack('<ff', float(A[i, j]), float(B[i, j])) for i in range(NR) for j in range(NE))).decode()
open('eqair2.b64', 'w').write(pack(GT, KA)); open('ne2.b64', 'w').write(pack(LNE, TT))
json.dump({'gt': GT.round(5).tolist(), 'ka': KA.round(5).tolist(), 'lne': LNE.round(4).tolist(), 'T': TT.round(1).tolist(), 'lr': lr.tolist(), 'le': le.tolist()}, open('eqair2.json', 'w'))
print('γ̃ range', GT.min(), GT.max(), ' κ range', KA.min(), KA.max())
