const D = __DATA__;
const root = document.querySelector(".sp");
const stage = root.querySelector(".sp-stage");
const model = stage.querySelector(".sp-model");
const live = root.querySelector("[data-live]");
const readout = root.querySelector("[data-readout]");
const partButtons = [...root.querySelectorAll(".sp-part")];
const still = matchMedia("(prefers-reduced-motion: reduce)");

const nodes = [...model.querySelectorAll(".it")].map((el) => ({
  el,
  piece: el.dataset.piece,
  ride: el.dataset.ride || el.dataset.piece,
  key: Number(el.dataset.k),
  m: el.dataset.m.split(",").map(Number),
  shown: "",
}));
for (const node of nodes) node.lift = node.m[0] * D.V[0] + node.m[1] * D.V[1] + node.m[2] * D.V[2];
let order = nodes.map((_, index) => index);

const IDS = Object.keys(D.pieces);
const piece = Object.fromEntries(IDS.map((id) => [id, { x: 0, v: 0, target: 0, pending: null }]));
let clock = 0, apart = false, selected = null, inside = false, leaveTimer = 0;
let touring = !still.matches, tourClock = -1.2, idleTimer = 0, visible = false, frame = 0, last = 0;

const say = (text) => { if (readout.textContent !== text) readout.textContent = text; };
function describe() {
  const text = selected ? D.pieces[selected].say : apart ? D.apartSay : D.restSay;
  if (stage.getAttribute("aria-valuetext") !== text) stage.setAttribute("aria-valuetext", text);
  if (live && live.textContent !== text) live.textContent = text;
}
function setApart(on) {
  if (apart === on) return;
  apart = on;
  const goal = on ? 1 : 0;
  let index = 0;
  for (const id of on ? D.stagger : [...D.stagger].reverse()) {
    if (piece[id].target === goal) piece[id].pending = null;
    else piece[id].pending = { value: goal, at: clock + (still.matches ? 0 : index++ * D.spring.stagger) };
  }
  describe();
  run();
}
function select(id) {
  if (id === "stand") id = null;
  if (selected === id) return;
  selected = id;
  for (const node of nodes) id !== null && node.piece === id ? node.el.setAttribute("data-on", "") : node.el.removeAttribute("data-on");
  id ? stage.setAttribute("data-focus", "") : stage.removeAttribute("data-focus");
  partButtons.forEach((button) => (button.dataset.part === id ? button.setAttribute("data-on", "") : button.removeAttribute("data-on")));
  stage.setAttribute("aria-valuenow", String(id ? D.order.indexOf(id) + 1 : 0));
  describe();
}
function steer(state, dt, calm) {
  if (state.pending && clock >= state.pending.at) { state.target = state.pending.value; state.pending = null; }
  if (calm) { state.x = state.target; state.v = 0; return false; }
  for (let i = 0; i < D.spring.substeps; i++) {
    const h = dt / D.spring.substeps;
    state.v += ((state.target - state.x) * D.spring.stiffness - state.v * D.spring.damping) * h;
    state.x += state.v * h;
  }
  if (Math.abs(state.target - state.x) < 2e-4 && Math.abs(state.v) < 2e-4) { state.x = state.target; state.v = 0; return state.pending !== null; }
  return true;
}
function place() {
  for (const node of nodes) {
    const share = piece[node.ride].x;
    const tx = (D.EX[0] * node.m[0] + D.EY[0] * node.m[1] + D.EZ[0] * node.m[2]) * share;
    const ty = (D.EX[1] * node.m[0] + D.EY[1] * node.m[1] + D.EZ[1] * node.m[2]) * share;
    const text = share === 0 ? "" : `translate(${tx.toFixed(2)} ${ty.toFixed(2)})`;
    if (text !== node.shown) { node.shown = text; text ? node.el.setAttribute("transform", text) : node.el.removeAttribute("transform"); }
  }
  const next = nodes.map((_, i) => i).sort((a, b) => nodes[a].key + nodes[a].lift * piece[nodes[a].ride].x - (nodes[b].key + nodes[b].lift * piece[nodes[b].ride].x));
  if (next.some((index, at) => index !== order[at])) {
    const fragment = document.createDocumentFragment();
    for (const index of next) fragment.appendChild(nodes[index].el);
    model.appendChild(fragment);
    order = next;
  }
}
const STEP = 1.9;
function tourAt(t) {
  const from = 0.3, listFrom = from + 1.1, listTo = listFrom + D.order.length * STEP;
  if (t < from) return { apart: false, part: null };
  if (t < listFrom) return { apart: true, part: null };
  if (t < listTo) return { apart: true, part: D.order[Math.floor((t - listFrom) / STEP)] };
  if (t < listTo + 3.2) return { apart: false, part: null };
  return null;
}
function quietTour() {
  touring = false;
  clearTimeout(idleTimer);
  idleTimer = setTimeout(() => { if (inside) return quietTour(); touring = !still.matches; tourClock = -0.4; run(); }, 4200);
}
function idleText() {
  if (selected) return D.pieces[selected].say;
  const moving = IDS.some((id) => Math.abs(piece[id].x - piece[id].target) > 0.002 || piece[id].pending);
  if (moving) return apart ? "lifting the skin" : "closing up";
  return apart ? D.apartSay : D.restSay;
}
function tick(now) {
  const dt = last ? Math.min((now - last) / 1000, 1 / 30) : 1 / 60;
  last = now;
  clock += dt;
  if (touring) {
    tourClock += dt;
    let step = tourAt(tourClock);
    if (!step) { tourClock = -0.6; step = { apart: false, part: null }; }
    setApart(step.apart);
    select(step.part);
  }
  let moving = false;
  for (const id of IDS) if (steer(piece[id], dt, still.matches)) moving = true;
  place();
  say(idleText());
  frame = visible && (moving || touring) ? requestAnimationFrame(tick) : 0;
}
function run() { if (!frame && visible) { last = 0; frame = requestAnimationFrame(tick); } }
new IntersectionObserver((entries) => { visible = entries[entries.length - 1].isIntersecting; if (visible) run(); }, { rootMargin: "120px 0px" }).observe(stage);

function pieceAt(event) {
  const hit = document.elementFromPoint(event.clientX, event.clientY);
  const item = hit && hit.closest ? hit.closest(".it") : null;
  return item ? item.dataset.piece : null;
}
stage.addEventListener("pointermove", (event) => {
  if (event.pointerType === "touch") return;
  inside = true;
  clearTimeout(leaveTimer);
  quietTour();
  setApart(true);
  const id = pieceAt(event);
  select(id === "stand" ? null : id);
  run();
});
stage.addEventListener("pointerleave", () => {
  inside = false;
  clearTimeout(leaveTimer);
  leaveTimer = setTimeout(() => { if (inside) return; select(null); setApart(false); }, 260);
});
stage.addEventListener("pointerdown", (event) => {
  if (event.pointerType !== "touch") return;
  quietTour();
  const id = pieceAt(event);
  if (!id || id === "stand") { select(null); setApart(!apart); } else { setApart(true); select(id); }
  run();
});
partButtons.forEach((button) => {
  const show = () => { quietTour(); clearTimeout(leaveTimer); setApart(true); select(button.dataset.part); run(); };
  const hide = () => {
    clearTimeout(leaveTimer);
    leaveTimer = setTimeout(() => { if (inside || partButtons.some((b) => b.matches(":hover, :focus-visible"))) return; select(null); setApart(false); }, 260);
  };
  button.addEventListener("pointerenter", show);
  button.addEventListener("focus", show);
  button.addEventListener("pointerleave", hide);
  button.addEventListener("blur", hide);
  button.addEventListener("click", show);
});
stage.addEventListener("keydown", (event) => {
  const index = selected ? D.order.indexOf(selected) : -1;
  let next = null;
  if (event.key === "ArrowRight" || event.key === "ArrowDown") next = Math.min(D.order.length - 1, index + 1);
  else if (event.key === "ArrowLeft" || event.key === "ArrowUp") next = Math.max(0, index - 1);
  else if (event.key === "Home") next = 0;
  else if (event.key === "End") next = D.order.length - 1;
  else if (event.key === "Escape") { event.preventDefault(); quietTour(); select(null); setApart(false); run(); return; }
  else if (event.key === " " || event.key === "Enter") { event.preventDefault(); quietTour(); setApart(!apart); if (!apart) select(null); run(); return; }
  if (next === null) return;
  event.preventDefault();
  quietTour();
  setApart(true);
  select(D.order[next]);
  run();
});
if (still.matches) touring = false;
const narrow = matchMedia("(hover: none), (max-width: 480px)");
const hint = root.querySelector(".sp-hint");
const wording = () => hint && (hint.textContent = narrow.matches ? "Tap to lift the skin" : "Hover the orbiter to lift its skin");
wording();
narrow.addEventListener("change", wording);
const asked = new URLSearchParams(location.search).get("theme");
if (asked === "light" || asked === "dark" || asked === "osp") document.body.dataset.theme = asked;
place();
say(idleText());
describe();
if (new URLSearchParams(location.search).get("embed") === "1") {
  document.body.classList.add("embed");
  const report = () => parent.postMessage({ introHeight: document.documentElement.scrollHeight }, "*");
  new ResizeObserver(report).observe(document.body);
  report();
}
