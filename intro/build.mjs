// A Space Shuttle orbiter model on a pitch sector in a wind-tunnel test section. Its upper skin
// lifts off to show the structure the OSP builder lays out for it: frames and bulkheads, longerons,
// the crew module, a 40 ft container in the bay, the propellant tanks, wing spars and ribs, the
// thrust structure and three engines. Every size comes from the builder's Shuttle preset (shuttle.json).
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import * as k from "../../kit/iso-kit.mjs";
import * as G from "../../kit/lathe.mjs";
import { tubePieces, tubeSvg } from "../../kit/tube.mjs";
import * as A from "../../kit/audit.mjs";
import { kitScript } from "../../scripts/inline-kit.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const THEME = process.argv.includes("--light") ? "light" : process.argv.includes("--osp") ? "osp" : "dark";
const DEG = Math.PI / 180;
const D = JSON.parse(readFileSync(join(HERE, "shuttle.json"), "utf8")).derived;

// ── scale and attitude ────────────────────────────────────────────────────────────────────────
const U = 8.4; // world units per metre
const ALPHA = 12; // angle of attack the sector is set to, degrees
const LM = D.length; // 37.2 m
const XREF = D.mass.balanceFull; // pitch centre: the loaded centre of gravity
const RM = 2.81; // fuselage radius, m (the preset's maximum half-width)
const N = 24; // panels round the fuselage
const SKIN = 0.08; // skin thickness, m (drawn)

const W = 980;
const H = 640;
const AZ = 66;
const EL = 28;

const CA = Math.cos(ALPHA * DEG);
const SA = Math.sin(ALPHA * DEG);
const AX = [CA, 0, -SA]; // nose to tail
const UP = [SA, 0, CA]; // model up
const SIDE = [0, 1, 0]; // model starboard
const C = [0, 0, 132]; // the pitch centre in the world
// a model point in metres (x from the nose, y to starboard, z up) to the world
const M = (x, y = 0, z = 0) => G.add3(C, G.add3(G.mul3(AX, (x - XREF) * U), G.add3(G.mul3(SIDE, y * U), G.mul3(UP, z * U))));
const AXF = (y = 0, z = 0) => G.frameOf(M(0, y, z), AX, SIDE, UP); // s in world units from the nose station

const R0 = RM * U;
const COS = Math.cos(Math.PI / N);
const vertex = (j, r) => {
  const a = Math.PI / N + (j * 2 * Math.PI) / N;
  return [r * Math.cos(a), r * Math.sin(a)];
};
const RIN = R0 - SKIN * U; // inner skin, at the vertices
const FR_OUT = RIN * COS; // frames touch the inner skin at its flats

// ── the stand ─────────────────────────────────────────────────────────────────────────────────
const FLOOR = { x: -176, y: -78, w: 380, d: 150, r: 8 };
const FLOOR_H = 12;
const FOOT_H = 7;
const SECTOR_R = (LM - XREF + 4.6) * U; // arc radius about the pitch centre
const STING_R = 0.36 * U;
const STING_Z = -1.9; // m below the axis, between the lower bells and the body flap

const P = k.fitProjection(
  [...k.boxCorners(FLOOR, -FLOOR_H - FOOT_H, 0), M(-0.5, 0, RM), M(0, 0, RM + 1), M(LM + 2, 0, 9), M(30, 12.5, 0), M(30, -12.5, 0), M(LM+6, 0, -14)],
  W,
  H,
  { pad: 28, azimuth: AZ, elevation: EL },
);
const V = G.viewOf(P);
const KS = G.scaleOf(P);
const at = (p) => k.iso(p, P);
const S = (paths, style) => k.solidSvg(paths, style);
const Ln = (d, style) => k.lineSvg(d, style);
const Dots = (points, style) => k.dotsSvg(points, style);

// ── assemblies ────────────────────────────────────────────────────────────────────────────────
const lift = (v, d) => G.mul3(v, d);
const PIECES = {
  nose: { name: "Nose cap and forward fuselage", move: lift(AX, -7.5 * U) },
  skin: { name: "Upper skin, payload-bay doors and fin", move: lift(UP, 6.6 * U) },
  wingskin: { name: "Upper wing skins", move: [0, 0, 0] },
  payload: { name: "40 ft container", move: lift(UP, 4.8 * U) },
  engines: { name: "Three main engines", move: lift(AX, 1.3 * U) },
  structure: { name: "Primary structure", move: [0, 0, 0] },
  stand: { name: "Pitch sector and sting", move: [0, 0, 0] },
};
const STAGGER = ["nose", "skin", "wingskin", "payload", "engines", "structure", "stand"];
const SPRING = { stagger: 0.05, stiffness: 52, damping: 13, substeps: 4 };
const R = A.recorder(P, { order: STAGGER, spring: SPRING });
const { items, nameFor } = R;
const record = R.solid;

function put(piece, ref, svg, { bias = 0, move, ride, shapes = [], name } = {}) {
  R.put({ piece, ride: ride ?? piece, at: ref, bias, svg, move: move ?? PIECES[piece].move, shapes, name: name ?? nameFor(`${piece}.item`) });
}
function prism(piece, F, poly, s0, s1, style = {}, { extra = "", bias = 0, move, ride, name, ground, owner } = {}) {
  const id = nameFor(name ?? `${piece}.prism`);
  const mid = (s0 + s1) / 2;
  const c = poly.reduce((acc, [u, v]) => [acc[0] + u / poly.length, acc[1] + v / poly.length], [0, 0]);
  const ref = G.add3(F.o, G.add3(G.mul3(F.a, mid), G.add3(G.mul3(F.u, c[0]), G.mul3(F.v, c[1]))));
  const shape = record(A.prism(F, poly, s0, s1, { name: id, ...(owner ? { owner } : {}), ...(ground ? { ground: true } : {}) }));
  put(piece, ref, S(G.prismOf(F, poly, s0, s1, P), { tone: "hi", ...style }) + extra, { bias, move, ride, name: id, shapes: [shape] });
  return shape;
}
function turned(piece, F, meridian, style = {}, { extra = "", inner = "", bias = 0, move, name, hole, smooth, steps } = {}) {
  const id = nameFor(name ?? `${piece}.turned`);
  const paths = G.lathe(meridian, F, P, { ...(hole ? { hole } : {}), ...(smooth !== undefined ? { smooth } : {}), ...(steps ? { steps } : {}) });
  const s = meridian.map(([v]) => v);
  const mid = (Math.min(...s) + Math.max(...s)) / 2;
  const shape = record(A.lathe(F, meridian, { name: id }));
  put(piece, G.add3(F.o, G.mul3(F.a, mid)), S(paths, { tone: "hi", ...style, inner }) + extra, { bias, move, name: id, shapes: [shape] });
  return shape;
}
const box2 = (u0, u1, v0, v1) => [[u0, v0], [u1, v0], [u1, v1], [u0, v1]];

// ── frames: every station the builder places, bulkheads full ──────────────────────────────────
const NOSE_END = 7.0; // m: the nose lathe ends where the parallel body starts
const noseR = (x) => R0 * Math.sqrt(Math.max(0, 1 - (1 - Math.min(x, NOSE_END) / NOSE_END) ** 2)) * Math.cos(Math.PI / N);
const STR = D.structure;
const FRAMES = STR.frames.filter((f) => f.x > 4.0 && f.x < LM - 0.1);
const FRAME_T = Math.max(0.6, STR.frames[0].thickness * U);
const FRAME_D = (f) => Math.max(1.4, f.depth * U);
const BIG = new Set(["pressure", "thrust", "bay", "spar", "fin", "gear"]);

// Everything that runs inside the frames is cut at their faces, as the real parts are: a long
// part inside a ring is in front of half of it and behind the other half, which no order can draw.
const SLABS = FRAMES.map((f) => [f.x * U - FRAME_T / 2, f.x * U + FRAME_T / 2]);
const spans = (s0, s1) => {
  const out = [];
  let a = s0;
  for (const [f0, f1] of SLABS) {
    if (f1 <= a || f0 >= s1) continue;
    if (f0 > a + 0.05) out.push([a, f0]);
    a = Math.max(a, f1);
  }
  if (s1 > a + 0.05) out.push([a, s1]);
  return out;
};
function prismCut(piece, F, poly, s0, s1, style, options = {}, extraOf = null) {
  spans(s0, s1).forEach(([a, b], index, list) => prism(piece, F, poly, a, b, extraOf ? { ...style, inner: extraOf(a, b, index, list.length) } : style, options));
}
function latheCut(piece, F, rOf, s0, s1, style, options = {}) {
  for (const [a, b] of spans(s0, s1)) {
    const n = Math.max(2, Math.ceil((b - a) / 1.2));
    const prof = Array.from({ length: n + 1 }, (_, i) => { const t = a + ((b - a) * i) / n; return [t, Math.max(0.01, rOf(t)), 1]; });
    turned(piece, F, [[a, 0], ...prof, [b, 0]], style, { smooth: true, ...options });
  }
}
const BAY = [8.89, 21.08];
const inBay = (f) => f.x >= BAY[0] - 0.01 && f.x <= BAY[1] + 0.01;
const OPEN = [37.5, 142.5]; // the bay frames are U-shaped, open above the sills: the doors close the top
for (const f of FRAMES) {
  const s = f.x * U;
  const outer = f.x < NOSE_END ? noseR(f.x) - SKIN * U - 0.05 : FR_OUT;
  const F = AXF();
  const tone = BIG.has(f.kind) ? "mid" : "lo";
  const depth = FRAME_D(f) * (BIG.has(f.kind) ? 1.3 : 1);
  if (f.full) {
    turned("structure", F, [[s - FRAME_T / 2, 0], [s - FRAME_T / 2, outer], [s + FRAME_T / 2, outer], [s + FRAME_T / 2, 0]], { tone }, {
      name: `structure.bulkhead-${f.kind}`,
      extra: Ln(G.circleOf(F, s + FRAME_T / 2, outer - 2.2, P), { tone: "faint" }) + Ln(G.spokesOf(F, s + FRAME_T / 2, 3, outer - 2.6, 8, P), { tone: "faint" }),
    });
  } else if (inBay(f)) {
    for (let j = 0; j < N; j++) {
      const mid = (360 * (j + 1)) / N;
      if (mid > OPEN[0] && mid < OPEN[1]) continue;
      const poly = [vertex(j, RIN), vertex(j + 1, RIN), vertex(j + 1, RIN - depth), vertex(j, RIN - depth)];
      prism("structure", F, poly, s - FRAME_T / 2, s + FRAME_T / 2, { tone }, { name: `structure.bay-frame${j}` });
    }
  } else {
    const inner = outer - depth;
    turned("structure", F, [[s - FRAME_T / 2, inner], [s - FRAME_T / 2, outer], [s + FRAME_T / 2, outer], [s + FRAME_T / 2, inner]], { tone }, { name: `structure.frame-${f.kind}`, hole: [s, inner] });
  }
}

// ── longerons: keel, chines, bay sills (bars lying on the frames' inner rims) ───────────────────
const LONG_A = 0.9; // bar size, world units
let KEEL_TOP = 0;
const ringIn = (f) => (f.full ? 0 : FR_OUT - FRAME_D(f) * (BIG.has(f.kind) ? 1.3 : 1));
for (const lg of STR.longerons) {
  const x0 = Math.max(lg.x[0], NOSE_END), x1 = Math.min(lg.x[1], LM - 0.2);
  const within = FRAMES.filter((f) => f.x >= x0 && f.x <= x1);
  const rr = Math.min(...within.filter((f) => !f.full).map(ringIn)) - LONG_A / 2;
  if (lg.kind === "keel") KEEL_TOP = -rr + LONG_A / 2;
  const spots = { keel: [-90], chine: [0, 180], sill: [OPEN[0] - 4, OPEN[1] + 4] }[lg.kind];
  for (const deg of spots) {
    const c = [rr * Math.cos(deg * DEG), rr * Math.sin(deg * DEG)];
    const h = LONG_A / 2;
    prismCut("structure", AXF(), box2(c[0] - h, c[0] + h, c[1] - h, c[1] + h), x0 * U, x1 * U, { tone: "mid" }, { name: `structure.${lg.kind}` });
  }
}

// ── skin: 24 panels round the body between the main joints; the upper ones lift ────────────────
const JOINTS = [NOSE_END, 8.56, 14.82, 21.08, 24.93, 28.42, 34.19, LM];
for (let i = 0; i + 1 < JOINTS.length; i++) {
  for (let j = 0; j < N; j++) {
    const a0 = vertex(j, R0), a1 = vertex(j + 1, R0), b1 = vertex(j + 1, RIN), b0 = vertex(j, RIN);
    const mid = (Math.PI * 2 * (j + 1)) / N; // the flat's centre angle
    const upper = Math.sin(mid) > 0.05;
    const n = G.add3(G.mul3(SIDE, Math.cos(mid)), G.mul3(UP, Math.sin(mid)));
    const piece = upper ? "skin" : "structure";
    const move = PIECES[piece].move;
    const seam = i === 2 && upper ? "" : "";
    prism(piece, AXF(), [a0, a1, b1, b0], JOINTS[i] * U, JOINTS[i + 1] * U, { tone: upper ? "hi" : "mid" }, { move, ride: piece, name: `${piece}.panel${i}-${j}`, extra: seam });
  }
}

// ── nose: an elliptical cap, a shell open at the back ───────────────────────────────────────────
{
  const F = AXF();
  const ell = (x) => R0 * Math.sqrt(Math.max(0, 1 - (1 - x / NOSE_END) ** 2));
  const outer = [];
  for (let i = 0; i <= 28; i++) {
    const t = i / 28;
    const x = NOSE_END * (1 - Math.cos((t * Math.PI) / 2)) ** 1;
    outer.push([x * U, ell(x), 1]);
  }
  const inner = outer.slice().reverse().map(([s, r]) => [s, Math.max(0, r - SKIN * U), 1]).filter(([s, r]) => s >= 0.35 * U && r > 0.5);
  const meridian = [[0, 0], ...outer.slice(1), [NOSE_END * U, inner[0][1]], ...inner.slice(1), [inner[inner.length - 1][0], 0]];
  const win = [];
  const sOf = (x) => x * U, rOf = (x) => ell(x);
  for (const [xa, xb, a0, a1] of [[3.9, 4.75, 62, 78], [3.9, 4.75, 82, 98], [3.9, 4.75, 102, 118], [4.95, 5.7, 52, 68], [4.95, 5.7, 112, 128]]) {
    const pts = [[xa, a0], [xb, a0 - 2], [xb, a1 + 2], [xa, a1]].map(([x, a]) => G.pointOf(F, sOf(x), rOf(x) + 0.05, a * DEG));
    const facing = Math.min(...[a0, a1].map((a) => G.facingOf(F, a * DEG, P)));
    if (facing > 0.08) win.push(k.pathOf(pts.map(at), true));
  }
  turned("nose", F, meridian, { tone: "hi" }, { name: "nose.cap", smooth: true, hole: [NOSE_END * U, ell(NOSE_END) - SKIN * U], extra: Ln(win.join(""), { tone: "mid" }) });
}

// ── crew module: a pressure vessel between the two pressure bulkheads ───────────────────────────
{
  const F = AXF(0, 0.35);
  const x0 = 4.09 * U + FRAME_T / 2, x1 = 8.56 * U - FRAME_T / 2, r = 1.75 * U;
  const cap = 4.5;
  const rOf = (t) => (t < x0 + cap ? r * Math.sqrt(Math.max(0, 1 - ((x0 + cap - t) / cap) ** 2 * 0.75)) : t > x1 - cap ? r * Math.sqrt(Math.max(0, 1 - ((t - x1 + cap) / cap) ** 2 * 0.75)) : r);
  latheCut("structure", F, rOf, x0, x1, { tone: "hi" }, { name: "structure.crew-module" });
}

// ── payload: the 40 ft container on the bay keel ────────────────────────────────────────────────
const CONT = D.boxes.find((b) => b.kind === "pay");
{
  const F = AXF();
  const [y0, y1] = CONT.y, [z0, z1] = CONT.z;
  const xa = CONT.x[0] * U, xb = CONT.x[1] * U;
  const face = (x, y, z) => G.add3(F.o, G.add3(G.mul3(F.a, x), G.add3(G.mul3(F.u, y), G.mul3(F.v, z))));
  const end = [];
  for (const y of [-0.75, -0.3, 0.3, 0.75]) end.push(k.segment(face(xb, y * U, z0 * U), face(xb, y * U, z1 * U), P));
  prismCut("payload", F, box2(y0 * U, y1 * U, z0 * U, z1 * U), xa, xb, { tone: "hi" }, { name: "payload.container" }, (a, b, index, count) => {
    const lines = [];
    for (let x = xa + 2.6; x < xb - 2.2; x += 1.55) if (x > a + 0.2 && x < b - 0.2) lines.push(k.segment(face(x, y1 * U, z0 * U), face(x, y1 * U, z1 * U), P));
    lines.push(k.segment(face(a, y1 * U, z1 * U - 1.2), face(b, y1 * U, z1 * U - 1.2), P), k.segment(face(a, y1 * U, z0 * U + 1.2), face(b, y1 * U, z0 * U + 1.2), P));
    if (index === count - 1) lines.push(...end);
    return Ln(lines.join(""), { tone: "faint" });
  });
  // fittings: the container stands on four blocks on the keel, between frames
  const gaps = spans(xa, xb).filter(([a, b]) => b - a > 3);
  for (const [a, b] of [gaps[1], gaps[Math.floor(gaps.length / 3)], gaps[Math.floor((2 * gaps.length) / 3)], gaps[gaps.length - 2]]) {
    const m = (a + b) / 2;
    prism("structure", F, box2(-0.8, 0.8, KEEL_TOP, z0 * U), m - 0.8, m + 0.8, { tone: "mid" }, { name: "structure.payload-fitting" });
  }
}

// ── tanks: fuel and oxidiser, hemispherical ends, mirrored, on a deck between the bay frames ──────
let TANK_FLOOR = 0;
for (const t of D.boxes.filter((b) => b.shape === "cylinder")) {
  for (const sgn of t.mirrored ? [1, -1] : [1]) {
    const yc = ((t.y[0] + t.y[1]) / 2) * sgn, zc = (t.z[0] + t.z[1]) / 2, r = t.radius * U;
    const F = AXF(yc, zc);
    const xa = t.x[0] * U, xb = t.x[1] * U;
    const rOf = (s) => (s < xa + r ? Math.sqrt(Math.max(0, r * r - (xa + r - s) ** 2)) : s > xb - r ? Math.sqrt(Math.max(0, r * r - (s - xb + r) ** 2)) : r);
    latheCut("structure", F, rOf, xa, xb, { tone: t.kind === "ox" ? "hi" : "mid" }, { name: `structure.tank-${t.kind}` });
    TANK_FLOOR = Math.min(TANK_FLOOR, zc * U - r);
  }
}

{
  const tanks = D.boxes.filter((b) => b.shape === "cylinder");
  const x0 = Math.min(...tanks.map((t) => t.x[0])) * U, x1 = Math.max(...tanks.map((t) => t.x[1])) * U;
  const halfW = Math.sqrt(FR_OUT ** 2 - TANK_FLOOR ** 2) - 0.2;
  prismCut("structure", AXF(), box2(-halfW, halfW, TANK_FLOOR - 1, TANK_FLOOR), x0, x1, { tone: "mid" }, { name: "structure.tank-deck" });
}

// ── engines: powerhead and bell on each engine axis ─────────────────────────────────────────────
for (const e of D.engines) {
  const F = AXF(e.y, e.z);
  const xt = LM - 0.15 * e.bellLength;
  const hs = 34.19 * U + FRAME_T / 2, he = xt * U;
  latheCut("engines", F, (s) => (s < he - 2 ? 0.42 * U : 0.42 * U + ((e.throatRadius * 1.4 - 0.42) * U * (s - he + 2)) / 2), hs, he, { tone: "mid" }, { name: "engines.powerhead" });
  const bell = [];
  for (let i = 0; i <= 18; i++) {
    const t = i / 18, s = xt + t * e.bellLength * 0.85;
    bell.push([s * U, (e.throatRadius + (e.exitRadius - e.throatRadius) * Math.pow(t, 0.62)) * U, 1]);
  }
  const seams = [0.35, 0.7].map((t) => { const i = Math.round(t * 18); return G.arcOf(F, bell[i][0], bell[i][1], P, { slope: (bell[i + 1][1] - bell[i - 1][1]) / (bell[i + 1][0] - bell[i - 1][0]) }); });
  turned("engines", F, [[xt * U, 0], ...bell, [bell[bell.length - 1][0], 0]], { tone: "hi" }, { name: "engines.bell", smooth: true, inner: Ln(seams.join(""), { tone: "faint" }) });
}

// ── wing: lower skin, spars, ribs and an upper skin that lifts ──────────────────────────────────
const WG = D.wing;
const [[xr, yr], [xt, yt], [xtt], [xrt]] = WG.planformHalf;
const ZW = WG.zMid; // m
const WT = 0.62; // drawn wing depth, m
const halfAt = (z) => {
  // the hull's half-width at height z (m), on its outer panels
  for (let j = 0; j < N; j++) {
    const [y0, z0] = vertex(j, RM), [y1, z1] = vertex(j + 1, RM);
    if (y0 > 0 && y1 > 0 && (z - z0) * (z - z1) <= 0) return y0 + ((y1 - y0) * (z - z0)) / (z1 - z0 || 1);
  }
  return RM;
};
for (const sgn of [1, -1]) {
  const yRoot = halfAt(ZW) - 0.02;
  const le = (y) => xr + ((xt - xr) * (y - yr)) / (yt - yr);
  const te = (y) => xrt + ((xtt - xrt) * (y - yr)) / (yt - yr);
  const plan = [[le(yRoot), yRoot], [xt, yt], [xtt, yt], [te(yRoot), yRoot]].map(([x, y]) => [x * U, y * U * sgn]);
  const WF = G.frameOf(M(0, 0, 0), UP, AX, SIDE); // axis up, u along the body, v to starboard
  const zLo = (ZW - WT / 2) * U, zHi = (ZW + WT / 2) * U, sk = 0.07 * U;
  prism("structure", WF, plan, zLo, zLo + sk, { tone: "mid" }, { name: "structure.wing-lower" });
  const onSkin = (x, y) => G.add3(WF.o, G.add3(G.mul3(WF.a, zHi), G.add3(G.mul3(WF.u, x * U), G.mul3(WF.v, y * U * sgn))));
  const chordAt = (y, u) => le(y) + u * (te(y) - le(y));
  const skinLines = [];
  for (const sp of STR.wingSpars) skinLines.push(k.segment(onSkin(chordAt(yRoot, sp.chordFraction), yRoot), onSkin(chordAt(yt, sp.chordFraction), yt), P));
  const EL = D.elevons, ya = yr + EL.spanFrom * (yt - yr), yb = yr + EL.spanTo * (yt - yr), hu = 1 - EL.chordFraction;
  skinLines.push(k.segment(onSkin(chordAt(ya, hu), ya), onSkin(chordAt(yb, hu), yb), P));
  skinLines.push(k.segment(onSkin(chordAt(ya, hu), ya), onSkin(te(ya), ya), P), k.segment(onSkin(chordAt(yb, hu), yb), onSkin(te(yb), yb), P));
  const ymid = (ya + yb) / 2;
  skinLines.push(k.segment(onSkin(chordAt(ymid, hu), ymid), onSkin(te(ymid), ymid), P));
  prism("wingskin", WF, plan, zHi - sk, zHi, { tone: "hi", inner: Ln(skinLines.join(""), { tone: "faint" }) }, { name: "wingskin.upper", move: G.add3(G.mul3(SIDE, sgn * 9.5 * U), G.mul3(UP, 0.8 * U)) });
  // spars along constant chord fractions, ribs streamwise between them
  const web = 0.06 * U;
  for (const sp of STR.wingSpars) {
    const u = sp.chordFraction;
    const p0 = [le(yRoot) + u * (te(yRoot) - le(yRoot)), yRoot], p1 = [xt + u * (xtt - xt), yt];
    const d = G.unit3([p1[0] - p0[0], (p1[1] - p0[1]) * sgn, 0]);
    const nrm = [-d[1], d[0]];
    const poly = [[p0[0] * U + nrm[0] * web, p0[1] * U * sgn + nrm[1] * web], [p1[0] * U + nrm[0] * web, p1[1] * U * sgn + nrm[1] * web], [p1[0] * U - nrm[0] * web, p1[1] * U * sgn - nrm[1] * web], [p0[0] * U - nrm[0] * web, p0[1] * U * sgn - nrm[1] * web]];
    prism("structure", WF, poly, zLo + sk, zHi - sk, { tone: "mid" }, { name: `structure.${sp.name.toLowerCase().replace(/ /g, "-")}` });
  }
  const fs = STR.wingSpars[0].chordFraction, rs = STR.wingSpars[1].chordFraction;
  STR.wingRibsY.filter((y, i) => y > yRoot + 0.3 && y < yt - 0.2 && i % 2 === 1).forEach((y) => {
    const c0 = le(y), c1 = te(y), ch = c1 - c0;
    const pieces = [[c0 + 0.01 * ch, c0 + fs * ch - 0.04], [c0 + fs * ch + 0.04, c0 + rs * ch - 0.04], [c0 + rs * ch + 0.04, c1 - 0.02 * ch]];
    for (const [a, b] of pieces) prism("structure", WF, box2(a * U, b * U, y * U * sgn - 0.25, y * U * sgn + 0.25), zLo + sk, zHi - sk, { tone: "lo" }, { name: "structure.rib" });
  });
}

// ── fin ─────────────────────────────────────────────────────────────────────────────────────────
{
  const fin = D.fins[0];
  const zRoot = RM * COS; // on the top flat
  const FF = G.frameOf(M(0, 0, 0), SIDE, AX, UP);
  const prof = fin.profileXS.map(([x, s]) => [x * U, (zRoot + s) * U]);
  const t = fin.thickness * U * 0.5;
  prism("skin", FF, prof, -t / 2, t / 2, { tone: "hi" }, { name: "fin.fin" });
}

// ── body flap ───────────────────────────────────────────────────────────────────────────────────
{
  const bf = D.bodyFlap;
  const zb = -RM * COS;
  prism("structure", AXF(), box2(-bf.halfWidth * U, bf.halfWidth * U, zb * U - bf.thickness * U, zb * U), (LM - 0.5) * U, (LM - 0.5 + bf.length) * U, { tone: "mid" }, { name: "structure.body-flap" });
}

// ── sting, sector and the floor ─────────────────────────────────────────────────────────────────
{
  const F = AXF(0, STING_Z);
  const s0 = 34.19 * U + FRAME_T / 2, s1 = (LM + 4.2) * U - 12;
  latheCut("stand", F, (s) => (s < LM * U ? STING_R : STING_R + (0.25 * STING_R * (s - LM * U)) / (s1 - LM * U)), s0, s1, { tone: "mid" }, { name: "stand.sting" });
}
// the pitch sector: an arc about the centre of gravity that the sting carriage rides on
const HOLD = M(LM + 4.2, 0, STING_Z);
const RS = Math.hypot(HOLD[0] - C[0], HOLD[2] - C[2]);
const PHI_H = Math.atan2(-(HOLD[2] - C[2]), HOLD[0] - C[0]) / DEG; // degrees below the horizontal
const PHI_C = PHI_H + 24;
const ARC = [PHI_H - 7, PHI_C + 4];
const ARC_W = 7, ARC_T = 4.5;
const arcPt = (phi, r, y = 0) => [C[0] + r * Math.cos(phi * DEG), y, C[2] - r * Math.sin(phi * DEG)];
const SF = G.frameOf([C[0], 0, C[2]], [0, 1, 0], [1, 0, 0], [0, 0, 1]);
const uvOf = (phi, r) => [r * Math.cos(phi * DEG), -r * Math.sin(phi * DEG)];
{
  const seg = 16;
  for (let i = 0; i < seg; i++) {
    const a0 = ARC[0] + ((ARC[1] - ARC[0]) * i) / seg, a1 = ARC[0] + ((ARC[1] - ARC[0]) * (i + 1)) / seg;
    const poly = [uvOf(a0, RS - ARC_W), uvOf(a0, RS + ARC_W), uvOf(a1, RS + ARC_W), uvOf(a1, RS - ARC_W)];
    const ticks = [];
    for (let d = Math.ceil(a0); d < a1; d++) {
      const alpha = d - PHI_H + ALPHA;
      const major = Math.round(alpha) % 5 === 0;
      ticks.push(k.segment(arcPt(d, RS + ARC_W, ARC_T), arcPt(d, RS + ARC_W - (major ? 3.3 : 2), ARC_T), P));
    }
    prism("stand", SF, poly, -ARC_T, ARC_T, { tone: "mid" }, { name: "stand.sector", owner: "stand.sector", extra: Ln(ticks.join(""), { tone: "lo" }) });
  }
  // carriage: a block straddling the arc, the sting clamped in its inner face
  const cp = [uvOf(PHI_H - 2.6, RS - ARC_W - 5), uvOf(PHI_H - 2.6, RS + ARC_W + 3), uvOf(PHI_H + 2.6, RS + ARC_W + 3), uvOf(PHI_H + 2.6, RS - ARC_W - 5)];
  prism("stand", SF, cp, -ARC_T - 3, ARC_T + 3, { tone: "hi" }, {
    name: "stand.carriage",
    owner: "stand.sector",
    extra: Ln(k.segment(arcPt(PHI_H, RS + ARC_W + 3, ARC_T + 3), arcPt(PHI_H, RS + ARC_W - 5, ARC_T + 3), P), { tone: "lit", free: "end" }) + Dots([at(arcPt(PHI_H - 1.6, RS - ARC_W - 3, ARC_T + 3)), at(arcPt(PHI_H + 1.6, RS - ARC_W - 3, ARC_T + 3)), at(arcPt(PHI_H - 1.6, RS + ARC_W + 1, ARC_T + 3)), at(arcPt(PHI_H + 1.6, RS + ARC_W + 1, ARC_T + 3))], { size: 0.45 }),
  });
  // column under the arc, on a foot flange
  const phiC = PHI_C;
  const cx = arcPt(phiC, RS)[0];
  // the arc's outer (lower) edge above the column's centre
  const top = [cx, 0, C[2] - Math.sqrt((RS + ARC_W) ** 2 - (cx - C[0]) ** 2)];
  const CF = G.frameOf([top[0], 0, 0], [0, 0, 1], [1, 0, 0], [0, 1, 0]);
  turned("stand", CF, [[0, 0], [0, 14], [2.4, 14], [2.4, 0]], { tone: "mid" }, { name: "stand.column-foot", extra: Dots(G.dotsOf(CF, 2.4, 11, 8, P, { all: true }), { size: 0.45 }) });
  turned("stand", CF, [[2.4, 0], [2.4, 7.5], [top[2] - 6, 7.5], [top[2] - 6, 0]], { tone: "mid" }, { name: "stand.column" });
  turned("stand", CF, [[top[2] - 6, 0], [top[2] - 6, 10], [top[2], 10], [top[2], 0]], { tone: "mid" }, { name: "stand.column-head" });
}
const FL = G.frameOf([0, 0, 0], [0, 0, 1], [1, 0, 0], [0, 1, 0]);
for (const [x, y] of k.corners(FLOOR, 20).sort((p, q) => k.depthOf([p[0], p[1], 0], P) - k.depthOf([q[0], q[1], 0], P))) {
  const id = nameFor("stand.foot");
  put("stand", [x, y, -FLOOR_H - FOOT_H], S(k.cylinder(x, y, 8, -FLOOR_H - FOOT_H, 1.8, P, 28), { tone: "lo" }) + S(k.cylinder(x, y, 6, -FLOOR_H - FOOT_H + 1.8, FOOT_H - 1.8, P, 28), { tone: "mid" }), { bias: -2e4, name: id, shapes: [record(A.cylinder(x, y, 8, -FLOOR_H - FOOT_H, FOOT_H, { name: id }))] });
}
const STRIP = { x: FLOOR.x + 22, y: FLOOR.y + FLOOR.d - 16, w: FLOOR.w - 44, d: 7, r: 1 };
const LABEL = { x: FLOOR.x + 18, y: FLOOR.y + 14, w: 46, d: 22, r: 2 };
const floorTop = () => {
  const t = k.topTicks(STRIP.x + 4, STRIP.x + STRIP.w - 4, U / 2, 2, STRIP.y + 0.8, 0.6, [1.8, 3.6], P);
  const screws = k.corners(FLOOR, 9);
  return (
    Ln(k.planOutline(k.insetPlan(FLOOR, 5), 0, P), { tone: "lo" }) +
    Ln(screws.map(([x, y]) => k.ring(x, y, 2.2, 0, P, 16)).join(""), { tone: "lo" }) +
    Dots(screws.map(([x, y]) => at([x, y, 0])), { size: 0.5 }) +
    S(k.slabOf(STRIP, 0, 0.6, P, 3), { tone: "lo", crease: "none" }) + Ln(t.minor, { tone: "lo" }) + Ln(t.major, { tone: "mid" }) +
    S(k.slabOf(LABEL, 0, 0.8, P, 4), { tone: "lo" }) + Ln(k.planOutline(k.insetPlan(LABEL, 1.6), 0.8, P), { tone: "faint" }) +
    Ln([[0, 30], [1, 22], [2, 34]].map(([row, len]) => k.lineOnTop([LABEL.x + 5, LABEL.y + 6 + row * 5], [LABEL.x + 5 + len, LABEL.y + 6 + row * 5], 0.8, P)).join(""), { tone: "lo", free: true }) +
    Dots([at([LABEL.x + 3, LABEL.y + 3, 0.8]), at([LABEL.x + LABEL.w - 3, LABEL.y + LABEL.d - 3, 0.8])], { size: 0.45 })
  );
};
put("stand", [0, 0, -FLOOR_H], S(k.slabOf(FLOOR, -FLOOR_H, FLOOR_H, P, 8, 1.6), { tone: "mid" }) + floorTop(), { bias: -1e4, name: "stand.floor", shapes: [record(A.slab(FLOOR, -FLOOR_H, FLOOR_H, { name: "stand.floor" }))] });

const QUICK = process.argv.includes("--quick");
const APART = process.argv.includes("--apart");
if (!QUICK) A.settle(R, P, process.argv.includes("--audit") ? {} : { states: [...A.uniformStates(10), ...A.prefixStates(STAGGER)] });
const liftOf = (item) => G.dot3(item.move, V);
items.sort((a, b) => (APART ? a.key + liftOf(a) - b.key - liftOf(b) : a.key - b.key));
const groups = items.map((item, index) => {
  const [mx, my, mz] = item.move;
  const t = APART ? ` transform="${k.translateAlong(P, item.move)}"` : "";
  const o = at([0, 0, 0]), q = at(item.move);
  const moving = Math.hypot(q[0] - o[0], q[1] - o[1]) > 0.01;
  const css = moving && !APART ? ` style="--dx:${(q[0] - o[0]).toFixed(2)}px;--dy:${(q[1] - o[1]).toFixed(2)}px"` : "";
  return `<g class="it${moving ? " mv" : ""}"${t}${css} data-piece="${item.piece}" data-k="${item.key.toFixed(2)}" data-m="${mx.toFixed(1)},${my.toFixed(1)},${mz.toFixed(1)}" data-i="${index}">${item.svg}</g>`;
});
const halo = `<path class="iso-halo" d="${k.haloOf(FLOOR, -FLOOR_H - FOOT_H, FLOOR_H, P)}"/>`;
const tf = (n) => Math.round(n).toLocaleString("en-GB");
const nUpper = Array.from({ length: N }, (_, j) => Math.sin((Math.PI * 2 * (j + 1)) / N) > 0.05).filter(Boolean).length;
const nBulk = FRAMES.filter((f) => f.full).length;
const nRibs = items.filter((it) => it.name.startsWith("structure.rib")).length;
const EP = D.enginePerformance;
PIECES.nose.say = `nose cap · forward pressure bulkhead at ${STR.frames[0].x.toFixed(2)} m`;
PIECES.skin.say = `upper skin · ${nUpper} of ${N} panels round × ${JOINTS.length - 1} bays, with the fin`;
PIECES.wingskin.say = `wing skins · ${tf(D.areas.planformM2)} m² planform · t/c ${WG.thicknessRatio}`;
PIECES.payload.say = `40 ft container · ${(CONT.x[1] - CONT.x[0]).toFixed(2)} m in the bay`;
PIECES.engines.say = `3 × ${EP.chemistry.replace(/ \(.*\)/, "")} · ${tf(EP.vacuum.thrustN / 1000)} kN vac each`;
PIECES.structure.say = `${FRAMES.length} frames, ${nBulk} bulkheads · keel, chines, sills · ${STR.wingSpars.length} spars a side`;
PIECES.stand.say = `pitch sector about the CG at ${XREF.toFixed(2)} m · α ${ALPHA}°`;
const ORDER = ["nose", "skin", "wingskin", "payload", "engines", "structure"];
const svg = k.figureSvg({
  width: W,
  height: H,
  label: `A Space Shuttle orbiter model, ${LM} m full scale, on the sting of a wind-tunnel pitch sector set to ${ALPHA} degrees. Its upper skin, fin, upper wing skins, nose cap, payload container and engines come away to show ${FRAMES.length} frames and bulkheads, the keel, chines and bay sills, the crew module, the propellant tanks, and the wing spars and ribs.`,
  body: [halo, `<g class="sp-model">${groups.join("")}</g>`],
});
const unit = (vector) => { const o = at([0, 0, 0]); const p = at(vector); return [p[0] - o[0], p[1] - o[1]]; };
const DATA = {
  V, EX: unit([1, 0, 0]), EY: unit([0, 1, 0]), EZ: unit([0, 0, 1]),
  pieces: Object.fromEntries(Object.entries(PIECES).map(([id, p]) => [id, { name: p.name, say: p.say }])),
  stagger: STAGGER, spring: SPRING, order: ORDER,
  tracks: { nose: [0, 0.75], skin: [0.35, 1.0], wingskin: [0.95, 0.8], payload: [1.45, 0.9], engines: [1.9, 0.7], structure: [0, 0], stand: [0, 0] },
  restSay: `Shuttle preset · ${LM} m · ${tf(D.mass.grossKg / 1000)} t gross · α ${ALPHA}°`,
  apartSay: `apart · ${ORDER.length} assemblies`,
};
const PARTS = ORDER.map((id, index) => `<button type="button" class="sp-part" data-part="${id}"><span class="sp-num">${String(index + 1).padStart(2, "0")}</span>${PIECES[id].name}</button>`).join("");
const corners = `<div class="iso-plate-corners" aria-hidden="true"><span class="iso-plate-corner" data-corner="fig">Fig 1</span><span class="iso-plate-corner" data-corner="title">Shuttle orbiter · tunnel model</span><span class="iso-plate-corner" data-corner="readout" data-readout>${DATA.restSay}</span></div>`;
const stageHtml = `<div class="sp-stage" tabindex="0" role="slider" aria-label="Space Shuttle orbiter on a tunnel pitch sector. Hover, tap or use the arrow keys to take it apart assembly by assembly; Escape puts it back together." aria-valuemin="0" aria-valuemax="${ORDER.length}" aria-valuenow="0" aria-valuetext="${DATA.restSay}">${svg}</div>`;
const controls = `<div class="sp-controls"><span class="sp-hint">Hover the orbiter to lift its skin</span><span class="sp-live" aria-live="polite" data-live></span></div>`;
const caption = `The Space Shuttle preset from the Build screen, as a tunnel model: ${LM} m full scale, ${tf(D.mass.grossKg / 1000)} t gross, its pitch sector turning about the loaded centre of gravity at ${XREF.toFixed(2)} m. Under the skin is the structure the builder lays out for it: ${FRAMES.length} frames, ${nBulk} of them full bulkheads (pressure, thrust), a keel, chines and bay sills, a crew module between the pressure bulkheads, a 40 ft container in the bay, the fuel and oxidiser tanks, and in each wing a front and rear spar with ribs between them. Build designs this; Test puts the same shape in the tunnel.`;
const bodyHtml = `<figure class="iso-figure sp"><div class="iso-plate">${corners}${stageHtml}${controls}</div><figcaption class="iso-legend"><span class="sp-parts">${PARTS}</span><span class="iso-caption">${caption}</span></figcaption></figure>`;
const CSS = readFileSync(join(HERE, "sp.css"), "utf8");
const LIVE = readFileSync(join(HERE, "live.js"), "utf8").replace("__DATA__", JSON.stringify(DATA));
const FONT = `<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,300..800&display=swap">`;
const page = k.pageHtml({ title: "Shuttle orbiter · tunnel model", theme: THEME, body: `<style>${CSS}</style>${bodyHtml}`, script: APART ? "" : LIVE, width: 1020 }).replace("<head>", `<head>${FONT}`);
const base = { light: "spaceplane-light", osp: "intro", dark: "spaceplane" }[THEME];
writeFileSync(join(HERE, base + (APART ? "-apart" : "") + ".html"), page);
console.log("wrote", `${(page.length / 1024).toFixed(0)} KB`, `${items.length} items`);
A.auditOrExit(R, P, {});
