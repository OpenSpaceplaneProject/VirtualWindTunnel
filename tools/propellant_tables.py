# Rocket performance tables for the Engines tab, from NASA CEA (Gordon & McBride; Fortran via RocketCEA).
# For each propellant: O/F × chamber pressure × area ratio → c*, chamber T, vacuum Isp with shifting
# and frozen equilibrium, exit pressure ratio, and exit T, molar mass and γ (for the flow solver's exit
# boundary). Infinite-area combustor, ideal (no losses). Output: tools/propellant_tables.json, which the
# app embeds as PROP_TABLES. Run: pip install rocketcea (needs gfortran); python3 tools/propellant_tables.py
import json, math, os
from rocketcea.cea_obj import CEA_Obj, add_new_fuel
add_new_fuel('C2H4_G', 'fuel C2H4 C 2 H 4 wt%=100. h,cal=12520. t(k)=298.15')  # gaseous ethylene, ΔHf 52.4 kJ/mol
PSIA = 6894.757
PROPS = {   # key: (oxidiser, fuel, O/F grid, name)
    'hydrolox': ('LOX', 'LH2', [4, 5, 5.5, 6, 6.5, 7, 8], 'Hydrogen / oxygen'),
    'kerolox': ('LOX', 'RP-1', [2.0, 2.3, 2.56, 2.72, 2.9, 3.1, 3.4], 'Kerosene / oxygen'),
    'methalox': ('LOX', 'CH4', [2.6, 3.0, 3.3, 3.6, 3.8, 4.0, 4.4], 'Methane / oxygen'),
    'storable': ('N2O4', 'MMH', [1.2, 1.4, 1.65, 1.9, 2.1, 2.3, 2.6], 'NTO / MMH'),
    'amlox': ('LOX', 'NH3', [0.9, 1.1, 1.25, 1.4, 1.6, 1.8, 2.0], 'Ammonia / oxygen'),
    'ethox': ('GOX', 'C2H4_G', [1.5, 2.0, 2.4, 2.8, 3.42, 4.0, 5.0], 'Ethylene / oxygen (gaseous)'),
    'gmethox': ('GOX', 'GCH4', [2.6, 3.0, 3.3, 3.89, 4.2, 4.6, 5.0], 'Methane / oxygen (gaseous)'),
    'ghydrox': ('GOX', 'GH2', [4, 5, 6, 7, 8, 10, 12], 'Hydrogen / oxygen (gaseous)'),
}
PC = [0.1e6, 0.3e6, 1e6, 3e6, 10e6, 20e6, 30e6, 40e6]          # Pa
EPS = [1.5, 2, 3, 5, 8, 12, 20, 35, 60, 100, 160, 250, 400]
out = {'pc': PC, 'eps': EPS, 'props': {}}
for key, (ox, fu, ofs, name) in PROPS.items():
    c = CEA_Obj(oxName=ox, fuelName=fu)
    T = {'name': name, 'of': ofs, 'cstar': [], 'Tc': [], 'ispV': [], 'ispF': [], 'pe': [], 'Te': [], 'MWe': [], 'ge': []}
    for of in ofs:
        rc, rT, rV, rF, rP, rTe, rM, rg = [], [], [], [], [], [], [], []
        for pc in PC:
            p = pc / PSIA
            rc.append(round(c.get_Cstar(Pc=p, MR=of) * 0.3048, 1)); rT.append(round(c.get_Tcomb(Pc=p, MR=of) / 1.8, 1))
            v, f, pe, te, mw, ge = [], [], [], [], [], []
            for e in EPS:
                v.append(round(c.get_Isp(Pc=p, MR=of, eps=e), 2)); f.append(round(c.get_Isp(Pc=p, MR=of, eps=e, frozen=1), 2))
                pe.append(float(f'{1 / c.get_PcOvPe(Pc=p, MR=of, eps=e):.5g}'))
                temps = c.get_Temperatures(Pc=p, MR=of, eps=e); te.append(round(temps[2] / 1.8, 1))
                m, g = c.get_exit_MolWt_gamma(Pc=p, MR=of, eps=e); mw.append(round(m, 3)); ge.append(round(g, 4))
            rV.append(v); rF.append(f); rP.append(pe); rTe.append(te); rM.append(mw); rg.append(ge)
        for k, v in zip(['cstar', 'Tc', 'ispV', 'ispF', 'pe', 'Te', 'MWe', 'ge'], [rc, rT, rV, rF, rP, rTe, rM, rg]): T[k].append(v)
    out['props'][key] = T; print(key, 'done', flush=True)
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'propellant_tables.json')
json.dump(out, open(path, 'w'), separators=(',', ':')); print(path, os.path.getsize(path), 'bytes')

# Pack for the app: IEEE half precision (3 significant figures: 0.25 s of Isp at 450 s), per propellant in PROP_FIELDS order; 2D fields [of][pc], 3D [of][pc][eps].
import base64, struct
FIELDS = ['cstar', 'Tc', 'ispV', 'ispF', 'pe', 'Te', 'MWe', 'ge']
flat, meta = [], {'pc': PC, 'eps': EPS, 'fields': FIELDS, 'props': {}}
for key, T in out['props'].items():
    meta['props'][key] = {'name': T['name'], 'of': T['of'], 'at': len(flat)}
    for f in FIELDS:
        for a in T[f]:
            for b in a:
                flat.extend(b if isinstance(b, list) else [b])
meta['b64'] = base64.b64encode(struct.pack(f'<{len(flat)}e', *flat)).decode()
js = 'const PROP_TAB = ' + json.dumps(meta, separators=(',', ':')) + ';'
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'propellant_tables.js'), 'w').write(js)
print('js', len(js), 'chars')
