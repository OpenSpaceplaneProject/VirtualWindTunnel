# Open Spaceplane Project — Virtual Windtunnel

A browser-based virtual wind tunnel for anything from paper planes and Cessnas to fighters, rockets and spaceplanes going to and from orbit. It runs entirely on your GPU through WebGPU — no install, no server.

Brought to you with 💖 & determination by [Supernova Labs](https://supernovalabs.co.uk).

## Run it

Open https://windtunnel.supernovalabs.co.uk in a WebGPU-capable browser (recent Chrome or Edge; Safari 26+; Firefox with WebGPU enabled). To run locally, serve the folder over HTTP (for example `python3 -m http.server`) and open `http://localhost:8000` — opening `index.html` straight from disk blocks the model file from loading.

**Intro.** On first load the app opens with an explainer: the Space Shuttle preset as a tunnel model whose skin lifts off to show the structure the builder lays out (frames, bulkheads, longerons, tanks, payload, spars and ribs). It is drawn with [Anatomy](https://github.com/wheresryan22/anatomy) from the preset's own numbers; see `intro/`. "Don't show this again" hides it, "What is this?" under the title brings it back, and `?intro=1` or `?intro=0` forces it.

**Line art.** Display › Render style draws the body the way the intro figure does: four flat light bands, bone ink on silhouettes, creases, part seams and (for builder designs) the main frame stations. "Line art" keeps the surface colours (pressure, heating, stress, livery); "Line art, plain" drops them. It only changes the final shading, so the simulation and its fields are untouched. On Lite it draws silhouettes only.

**Phones, tablets and slow PCs.** Lite mode starts on the coarse grid at half resolution, takes longer render steps and reads surface heating from the solver's cells instead of per pixel. It switches on by itself for touch devices and machines with 4 or fewer cores or 4 GB or less of memory. Add `?lite=1` or `?lite=0` to the address to force it, or toggle it under Display. Auto resolution, on by default, lowers the render resolution while frames take over 40 ms and restores it when they speed up. Without WebGPU the Build screen still works; Test needs WebGPU.

## What's inside

- **Solver chain, picked per regime:** lattice-Boltzmann (D3Q19, LES) at low speed; a compressible finite-volume solver (MUSCL + HLLC, ghost-cell immersed boundary) from transonic to hypersonic; modified-Newtonian / free-molecular panel methods with Knudsen-number bridging for rarefied flight.
- **Wall friction in the flowfield:** a wall model applies boundary-layer shear (Blasius or White's turbulent law at Eckert's reference temperature, Sutherland viscosity) in the near-wall cells, so friction drag and its momentum loss are part of the solution.
- **Equilibrium air:** above about 1,500 K total temperature the high-speed solver uses an 11-species equilibrium-air table built with Cantera (dissociation and ionisation to 20,000 K).
- **Engines:** ideal-rocket bell and aerospike exhausts; intakes (pitot, external-, mixed-compression) with an engine face that sets back pressure (rig, turbojet demand, ramjet combustor); full-flowpath ramjet and scramjet with heat release in the combustor.
- **Structure:** voxel finite elements (bricks with incompatible bending modes) loaded by the flow's surface pressure with inertia relief; optional heat soak along the entry and thermal stress.
- **Trust tools:** convergence detection with uncertainty bands, a grid-sensitivity check, local refinement by a nested finer grid, and a validation suite against exact and published answers.
- **Spaceplane builder:** component-built spaceplanes (fuselage, NACA-section wing, strakes, seven tail layouts, hinged elevons, rudder and body flap, canards, nacelles), engines from the ideal-rocket model and simulated as plumes, RCS sizing, internal boxes with a balance-driven placement solver, livery; a reference library of 15 designs.
- **CAD hand-off:** design packages for `cad/build_spaceplane.py` (build123d → STEP) and the CAD agent brief in `cad/AGENT.md`.
- **Shape optimiser:** the builder's design scored over the whole mission (ascent drag, entry heating, cross-range, landing speed, packing, stability), plus a Sears–Haack benchmark scored by the flow solver.
- **Ascent and staging:** multi-stage ascent to orbit with pitch kick, gravity turn, closed-loop insertion, max-Q, staging and losses; drag from the model's measured geometry.
- **Entry simulation, aerothermal loads, import** (STL, OBJ, GLB, STEP) as before.

All results are physical approximations from the models named above — useful for design exploration, not a substitute for validated CFD, FEA or test.

## Files

- `index.html` — the whole application (HTML, CSS, JS and WGSL shaders).
- `METHODS.md` — how each part works, its assumptions and how to read it, by panel tab (moved out of the app so the panel carries controls and results only).
- `patch.png`, `favicon-32.png`, `apple-touch-icon.png` — mission patch and icons.
- `models/redarrow.json` — default spaceplane model.
- `.github/workflows/pages.yml` — optional GitHub Pages deploy on every push to `main`. The live site is served by Vercel at https://windtunnel.supernovalabs.co.uk (static, no build step).
