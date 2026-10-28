#!/usr/bin/env python3
"""Baseline CAD from a tunnel design package (osp-spaceplane-design v1) with build123d.

    python cad/build_spaceplane.py shuttle.design.json [--out build/]

Writes <name>.step (outer mould line, control surfaces, nozzles and the internal boxes as
named solids), <name>.stl (outer mould line), and <name>.cad-report.json, which compares the
CAD with what the tunnel assumed. This is the deterministic starting point that the CAD agent
(cad/AGENT.md) refines; it builds only what the package states, in the tunnel's frame:
x aft from the nose, y to port, z up, metres.
"""
import argparse, json, math, pathlib
from build123d import Axis, Box, Compound, Cone, Cylinder, Face, Location, Plane, Solid, Sphere, Wire, export_step, export_stl, mirror


def superellipse(sec, n=48):
    """Section of the fuselage at sec['x']: superellipse half-width b, top/bottom half-heights about
    centreZ, cut flat at the bottom. Returns a closed list of (y, z)."""
    b, zc, top, bot, q = sec["halfWidth"], sec["centreZ"], sec["top"], sec["bottom"], sec["squareness"]
    # the lower half-height is not in the package when the flat bottom cuts it; the cut is what shows
    aT, aB = max(top - zc, 1e-4), max(sec.get("lowerHalfHeight", zc - bot), 1e-4)
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        c, s = math.cos(t), math.sin(t)
        y = b * math.copysign(abs(c) ** (2 / q), c)
        a = aT if s > 0 else aB
        z = zc + a * math.copysign(abs(s) ** (2 / q), s)
        pts.append((y, max(z, bot)))
    return pts


def fuselage(sections):
    wires = []
    for sec in sections:
        if sec["halfWidth"] < 1e-3 or sec["top"] - sec["bottom"] < 1e-3:
            continue
        x = sec["x"]
        pts = [(x, y, z) for (y, z) in superellipse(sec)]
        wires.append(Wire.make_polygon(pts, close=True))
    return Solid.make_loft(wires, ruled=False)


def naca(tc, chord, n=40):
    """Symmetric NACA 4-digit section, closed trailing edge; (x, z) from the leading edge."""
    up, lo = [], []
    for i in range(n + 1):
        u = 0.5 * (1 - math.cos(math.pi * i / n))
        yt = 5 * tc * chord * (0.2969 * math.sqrt(u) - 0.126 * u - 0.3516 * u**2 + 0.2843 * u**3 - 0.1036 * u**4)
        up.append((u * chord, yt)); lo.append((u * chord, -yt))
    return up + lo[::-1][1:-1]


def wing(w):
    P, zmid, tc, dih = w["planformHalf"], w["zMid"], w["thicknessRatio"], math.radians(w["dihedralDeg"])
    (xr, yr), (xt, yt), (xtt, _), (xrt, _) = P
    root_c = xrt - xr
    tip_c = max(xtt - xt, 0.02 * root_c)
    sec = lambda x0, y, c, z: Wire.make_polygon([(x0 + px, y, z + pz) for (px, pz) in naca(tc, c)], close=True)
    dz = (yt - yr) * math.tan(dih)
    half = Solid.make_loft([sec(xr, 0.0, root_c, zmid), sec(xr, max(yr, 1e-3), root_c, zmid), sec(xt, yt, tip_c, zmid + dz)], ruled=True)
    return half + mirror(half, Plane.XZ)


def plate(points_xy, z, thickness):
    """A flat plate from a planform polygon (x, y) at height z."""
    w = Wire.make_polygon([(x, y, z - thickness / 2) for x, y in points_xy], close=True)
    return Solid.extrude(Face(w), (0, 0, thickness))


def fin(spec):
    """Fin from its (x, span) profile, rooted at spec['root'], canted outward by cantDeg."""
    (_, y0, z0), cant = spec["root"], math.radians(spec["cantDeg"])
    t = spec["thickness"]
    w = Wire.make_polygon([(x, -t / 2, s) for x, s in spec["profileXS"]], close=True)
    f = Solid.extrude(Face(w), (0, t, 0))
    # span direction (sin c, cos c) in (y, z): rotate about x, then move to the root
    f = f.rotate(Axis.X, -math.degrees(cant)).moved(Location((0, y0, z0)))
    return [f, mirror(f, Plane.XZ)] if spec["mirrored"] else [f]


def split_elevons(wing_solid, w, elev):
    """Cut the elevons out of the wing behind the hinge line and deflect them about it."""
    (xr, yr), (xt, yt), (xtt, _), (xrt, _) = w["planformHalf"]
    cr, ct = xrt - xr, xtt - xt
    y_a = yr + elev["spanFrom"] * (yt - yr); y_b = yr + elev["spanTo"] * (yt - yr)
    lerp = lambda y0, y1, v0, v1, y: v0 + (v1 - v0) * (y - y0) / max(y1 - y0, 1e-9)
    te = lambda y: lerp(yr, yt, xrt, xtt, y)
    hinge = lambda y: te(y) - elev["chordFraction"] * lerp(yr, yt, cr, ct, y)
    out_fixed, moving = wing_solid, []
    for sgn in (1, -1):
        poly = [(hinge(y_a), sgn * y_a), (te(y_a) + 1, sgn * y_a), (te(y_b) + 1, sgn * y_b), (hinge(y_b), sgn * y_b)]
        region = plate(poly, w["zMid"], 50.0)
        piece = wing_solid & region
        out_fixed = out_fixed - region
        h0 = (hinge(y_a), sgn * y_a, w["zMid"]); h1 = (hinge(y_b), sgn * y_b, w["zMid"])
        if abs(elev["deflectionDeg"]) > 1e-6:
            piece = piece.rotate(Axis(h0, tuple(b - a for a, b in zip(h0, h1))), sgn * elev["deflectionDeg"])
        moving.append(piece)
    return out_fixed, moving


def bells(engines):
    parts = []
    for e in engines:
        if e["type"] != "bell":
            continue
        L, re, rt = e["bellLength"], e["exitRadius"], e["throatRadius"]
        wall = max(0.06 * re, 0.01)
        outer = Cone(rt + wall, re, L, align=None, rotation=(0, 90, 0))
        inner = Cone(max(rt - 0.3 * wall, 0.005), re - wall, L * 1.02, align=None, rotation=(0, 90, 0))
        shell = (outer - inner).moved(Location((e["xThroat"], e["y"], e["z"])))
        parts.append(shell)
    return parts


def boxes(bx):
    out = []
    for b in bx:
        (x0, x1), (y0, y1), (z0, z1) = b["x"], b["y"], b["z"]
        if x1 - x0 < 1e-3 or y1 - y0 < 1e-3 or z1 - z0 < 1e-3:
            continue
        c = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
        if b.get("shape") == "cylinder":   # a tank: cylinder along x with hemispherical ends
            r = b["radius"]; lc = max(x1 - x0 - 2 * r, 0.0)
            s = Sphere(r).moved(Location((x0 + r, c[1], c[2]))) + Sphere(r).moved(Location((x1 - r, c[1], c[2])))
            if lc > 1e-4:
                s = s + Cylinder(r, lc, rotation=(0, 90, 0)).moved(Location(c))
        else:
            s = Box(x1 - x0, y1 - y0, z1 - z0).moved(Location(c))
        s.label = b["name"]
        out.append(s)
        if b.get("mirrored"):
            m = mirror(s, Plane.XZ); m.label = b["name"] + " (starboard)"; out.append(m)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("package"); ap.add_argument("--out", default=".")
    a = ap.parse_args()
    pkg = json.loads(pathlib.Path(a.package).read_text())
    assert pkg.get("format") == "osp-spaceplane-design", "not a tunnel design package"
    D, d = pkg["derived"], pkg["design"]
    name = (d.get("name") or "spaceplane").lower().replace(" ", "-").replace(",", "")
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)

    body = fuselage(D["fuselageSections"]); body.label = "Fuselage"
    oml, surfaces = body, []
    if D.get("wing"):
        wg = wing(D["wing"])
        if D.get("elevons"):
            wg, elev = split_elevons(wg, D["wing"], D["elevons"])
            for i, e in enumerate(elev): e.label = f"Elevon {'port' if i == 0 else 'starboard'}"; surfaces.append(e)
        oml = oml + wg
    if D.get("strake"):
        (xs, ys), (xj, yj), _ = D["strake"]
        st = plate([(xs, 0), (xs, ys), (xj, yj), (xj, 0)], D["wing"]["zMid"], 0.4 * D["wing"]["thicknessRatio"] * (D["wing"]["planformHalf"][3][0] - D["wing"]["planformHalf"][0][0]))
        oml = oml + st + mirror(st, Plane.XZ)
    for spec in D.get("fins") or []:
        for f in fin(spec): oml = oml + f
    if D.get("tailplane"):
        T = D["tailplane"]; P = T["planformHalf"]
        tp = plate([(P[0][0], 0), *[tuple(p) for p in P], (P[3][0], 0)], T["z"], T["thickness"])
        oml = oml + tp + mirror(tp, Plane.XZ)
    if D.get("canards"):
        C = D["canards"]; P = C["planformHalf"]
        cn = plate([(P[0][0], 0), *[tuple(p) for p in P], (P[3][0], 0)], 0.0, C["thickness"])
        oml = oml + cn + mirror(cn, Plane.XZ)
    if D.get("bodyFlap"):
        B = D["bodyFlap"]; hx, _, hz = B["hinge"]
        fl = Box(B["length"], 2 * B["halfWidth"], B["thickness"]).moved(Location((hx + B["length"] / 2, 0, hz + B["thickness"] / 2)))
        if abs(B["deflectionDeg"]) > 1e-6: fl = fl.rotate(Axis((hx, 0, hz), (0, 1, 0)), B["deflectionDeg"])
        fl.label = "Body flap"; surfaces.append(fl)
    if D.get("nacelles"):
        N = D["nacelles"]
        nb = Solid.make_cylinder(N["radius"], N["length"] * 0.75, Plane((N["x"] + N["length"] * 0.25, N["y"], N["z"]), z_dir=(1, 0, 0)))
        nn = Solid.make_cone(N["radius"] * 0.35, N["radius"], N["length"] * 0.25, Plane((N["x"], N["y"], N["z"]), z_dir=(1, 0, 0)))
        nc = nb + nn; nc.label = "Nacelle port"; ns = mirror(nc, Plane.XZ); ns.label = "Nacelle starboard"
        surfaces += [nc, ns]
    L = D["length"]
    for e in D["engines"]:
        e["xThroat"] = L - 0.15 * e["bellLength"]
    nz = bells(D["engines"])
    for i, s in enumerate(nz):
        s.label = f"Nozzle {i + 1}"
    inside = boxes(D["boxes"])
    oml.label = "Outer mould line"
    export_step(Compound(children=[oml, *surfaces, *nz, *inside]), str(out / f"{name}.step"))
    export_stl(oml, str(out / f"{name}.stl"))

    # how the CAD compares with what the tunnel assumed
    rep = {"parts": ["Outer mould line", *[x.label for x in surfaces], *[x.label for x in nz]],
           "fuselageVolumeM3": body.volume, "outerMouldLineVolumeM3": oml.volume, "outerMouldLineAreaM2": oml.area,
           "tunnelWettedAreaM2": D["areas"]["wettedM2"], "tunnelUsableVolumeM3": D["volumes"]["usableM3"],
           # inside the outer mould line (a main gear bay may sit in the wing root), within 0.1 % of volume
           "boxesInsideHull": [b.label for b in inside if (b - oml).volume < 1e-3 * max(b.volume, 1e-9)],
           "boxesOutsideHull": {b.label: round((b - oml).volume / max(b.volume, 1e-9), 4) for b in inside if (b - oml).volume >= 1e-3 * max(b.volume, 1e-9)}}
    (out / f"{name}.cad-report.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
