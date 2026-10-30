import os
import base64, re, struct, json, math, sys
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ramc_electron_density.py')).read().split("data = [")[0]
ns = {}; exec(src, ns)
html = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'index.html')).read()
raw = base64.b64decode(re.search(r'const EQAIR_B64 = "([^"]+)"', html).group(1)); eqt = list(struct.unpack(f'<{len(raw)//4}f', raw))
cases, refs = [], {}
for alt, V, tag in [(40, 5000, 'rg40k5'), (60, 7000, 'rg60k7')]:
    T1, p1 = ns['us76'](alt * 1000); rho1 = p1 / (287.05 * T1); a = math.sqrt(1.4 * 287.05 * T1); M = V / a
    r1, t1, post, stag = ns['shock'](alt * 1000, V)
    refs[tag] = dict(alt=alt, V=V, M=M, rho1=rho1, post_T=post[0], post_eps=r1 / post[2], stag_T=stag[0], cp_stag=(stag[1] - p1) / (0.5 * r1 * V * V), stag_rho=stag[2] / r1)
    base = dict(NX=68, NY=84, NZ=4, R0=8, M=M, T=108.8, cyl=True, dep=None, cx=38)
    cases.append(dict(base, name=f'cyl {tag} R8 real', rg=[1, math.log10(rho1), math.log10(V * V), 0], eqt=eqt))
    cases.append(dict(base, name=f'cyl {tag} R8 perfect'))
json.dump(cases, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cases_realgas.json'), 'w')); json.dump(refs, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'refs_realgas.json'), 'w'), indent=1); print(json.dumps(refs, indent=1))
