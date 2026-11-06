#!/usr/bin/env node
// MCP server for the OSP Virtual Windtunnel. It drives the app in a Chromium it starts (WebGPU on), and
// serves the app's own agent tools (vwt.tools in index.html: controls, modes, results, design, exports,
// engine runs, optimiser), plus three of its own: a screenshot, the repo's test suites and the CAD build.
//
//   node mcp/vwt-mcp.mjs            (stdio)
//   VWT_URL      page to drive (default: this repo's index.html)
//   VWT_HEADED=1 show the browser window
//   VWT_SOFTWARE=1 software WebGPU (SwiftShader) for machines without a GPU; slow
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { ListToolsRequestSchema, CallToolRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { chromium } from "playwright";
import { spawn } from "node:child_process";
import { mkdtempSync, writeFileSync, readFileSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const URL_ = process.env.VWT_URL || pathToFileURL(path.join(REPO, "index.html")).href + "?lite=1";
const GPU = ["--enable-unsafe-webgpu", "--enable-features=Vulkan,WebGPU", "--ignore-gpu-blocklist", "--disable-gpu-watchdog"];
const SOFT = ["--use-vulkan=swiftshader", "--use-webgpu-adapter=swiftshader", "--disable-vulkan-surface", "--use-angle=swiftshader"];

let page = null, browser = null;
async function app() {
  if (page && !page.isClosed()) return page;
  browser = browser || (await chromium.launch({ headless: !process.env.VWT_HEADED, args: GPU.concat(process.env.VWT_SOFTWARE ? SOFT : []) }));
  page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  page.setDefaultTimeout(0);
  await page.addInitScript(() => { try { localStorage.setItem("vwt.intro", "0"); } catch (e) {} });
  await page.goto(URL_);
  await page.waitForFunction(() => window.vwt && window.vwt.ready, null, { timeout: 120000 });
  if (!(await page.evaluate(() => vwt.gpu))) throw new Error("no WebGPU in this browser: set VWT_SOFTWARE=1 to use the software adapter");
  return page;
}

// the repo's own checks; each runs its own headless browser
const SUITES = {
  rde_1d: ["tests/rde/run1d.py"], rde_goto: ["tests/rde/goto.py"], propulsion: ["tests/propulsion/check.py"],
  microwave_beam: ["tests/microwave-beam/brun.py"], energy_deposition: ["tests/energy-deposition/hrun.py"],
  solver_accuracy: ["tests/solver-accuracy/run.py", "tests/solver-accuracy/cases.json", "tests/solver-accuracy/results.jsonl"],
};
function run(cmd, args, opts = {}) {
  return new Promise((res) => {
    const p = spawn(cmd, args, { cwd: REPO, env: { ...process.env, ...(opts.env || {}) } }); let out = "";
    p.stdout.on("data", (d) => (out += d)); p.stderr.on("data", (d) => (out += d));
    const to = setTimeout(() => p.kill("SIGTERM"), (opts.timeout_s || 3600) * 1000);
    p.on("close", (code) => { clearTimeout(to); res({ code, out }); });
  });
}
const OWN = [
  { name: "screenshot", description: "A PNG of the app as it is now.", inputSchema: { type: "object", properties: {} },
    run: async () => ({ content: [{ type: "image", mimeType: "image/png", data: (await (await app()).screenshot()).toString("base64") }] }) },
  { name: "run_test", description: "Run one of the repo's verification suites and return its output: " + Object.keys(SUITES).join(", ") + ". env passes options the suite reads (e.g. {\"ONLY\": \"C2H4-O2 stoich|0.0004\"} for rde_1d).",
    inputSchema: { type: "object", properties: { suite: { type: "string", enum: Object.keys(SUITES) }, env: { type: "object" }, timeout_s: { type: "number" } }, required: ["suite"] },
    run: async (a) => { const r = await run("python3", SUITES[a.suite], { env: a.env, timeout_s: a.timeout_s }); return text({ exit: r.code, output: r.out.slice(-20000) }); } },
  { name: "cad_build", description: "Build the current builder design as CAD with cad/build_spaceplane.py (build123d): STEP and STL plus a report checking the CAD against the tunnel. Returns the report and the file paths.", inputSchema: { type: "object", properties: { out_dir: { type: "string" } } },
    run: async (a) => {
      const pkg = await (await app()).evaluate(() => vwt.call("export", { kind: "cad_package" }));
      const dir = a.out_dir || mkdtempSync(path.join(tmpdir(), "vwt-cad-")), f = path.join(dir, "design.json"); writeFileSync(f, pkg.text);
      const r = await run("python3", ["cad/build_spaceplane.py", f, "--out", dir], { timeout_s: 1800 });
      const rep = path.join(dir, "design.cad-report.json");
      return text({ exit: r.code, dir, report: existsSync(rep) ? JSON.parse(readFileSync(rep, "utf8")) : null, output: r.out.slice(-4000) });
    } },
];
const text = (o) => ({ content: [{ type: "text", text: typeof o === "string" ? o : JSON.stringify(o, null, 1) }] });

const server = new Server({ name: "osp-virtual-windtunnel", version: "1.0.0" }, { capabilities: { tools: {} } });
server.setRequestHandler(ListToolsRequestSchema, async () => {
  const p = await app(); const pageTools = await p.evaluate(() => vwt.tools);
  return { tools: pageTools.concat(OWN.map(({ run, ...t }) => t)) };
});
server.setRequestHandler(CallToolRequestSchema, async (req) => {
  const { name, arguments: args = {} } = req.params;
  try {
    const own = OWN.find((t) => t.name === name); if (own) return await own.run(args);
    const p = await app();
    return text(await p.evaluate(([n, a]) => vwt.call(n, a), [name, args]));
  } catch (e) { return { isError: true, content: [{ type: "text", text: String(e && e.message ? e.message : e) }] }; }
});
await server.connect(new StdioServerTransport());
process.on("SIGINT", async () => { if (browser) await browser.close(); process.exit(0); });
