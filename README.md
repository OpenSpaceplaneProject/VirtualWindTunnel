# Open Spaceplane Project — Virtual Windtunnel

A browser-based virtual wind tunnel for anything from paper planes and Cessnas to fighters, rockets and spaceplanes going to and from orbit. It runs entirely on your GPU through WebGPU — no install, no server.

Brought to you with 💖 & determination by [Supernova Labs](https://supernovalabs.co.uk).

## Run it

Open https://windtunnel.supernovalabs.co.uk in a WebGPU-capable browser (recent Chrome or Edge; Safari 26+; Firefox with WebGPU enabled). To run locally, serve the folder over HTTP (for example `python3 -m http.server`) and open `http://localhost:8000` — opening `index.html` straight from disk blocks the model file from loading.

**Intro.** On first load the app opens with an explainer: the Space Shuttle preset as a tunnel model whose skin lifts off to show the structure the builder lays out (frames, bulkheads, longerons, tanks, payload, spars and ribs). It is drawn with [Anatomy](https://github.com/wheresryan22/anatomy) from the preset's own numbers; see `intro/`. "Don't show this again" hides it, "What is this?" under the title brings it back, and `?intro=1` or `?intro=0` forces it.

**Line art.** Setup › Display › Render style draws the body the way the intro figure does: four flat light bands, bone ink on silhouettes, creases, part seams and (for builder designs) the main frame stations. "Line art" keeps the surface colours (pressure, heating, stress, livery); "Line art, plain" drops them. It only changes the final shading, so the simulation and its fields are untouched. On Lite it draws silhouettes only.

**Shells.** Setup › Display › Show › Shells draws nested level surfaces of the flow, CT-scan style. In the compressible solver they are density over freestream at 1.3, 2.5 and 4.5 (shock layer and expansion); in the low-speed solver, speed over freestream at 0.35, 0.8 and 1.2 (wake and the fast flow over the body). Each is drawn where the render march crosses its level and is shaded by the field's gradient, denser where it turns away so its edges read as outlines. In line art they become bone ink. Display only.

**Layout.** Build is the design, and that includes the engine: type, propellant, O/F and chamber are set once, in Build › Engines. Test has four tabs, left to right in the order the work usually goes, though you can open any of them at any time:
- **Conditions:** the body, attitude, flying it, engines firing and throttle, and energy deposition.
- **Mission:** ascent, entry with its bank events, heat shield and heating model.
- **Results:** structure, time-averaged pressure and exports.
- **Setup:** solver, grid, validation and display.

Engine is a bench for a closer look at one component, at higher fidelity than the vehicle pass.

**Find and setups.** Press `/`, or the magnifier on the headline card, to search every setting by name. Picking one opens the right mode, tab and section and highlights it. In the same box, Copy setup puts the whole setup on the clipboard as JSON (mode, builder design, every control's value), and Load setup applies one pasted in. Scripts and agents get the same through `window.vwt`: `list()`, `find(text)`, `get(id)`, `set(id, value)`, `state()`, `load(setup)`, `show(id)`. Setting a value goes through the control itself, so it behaves exactly like a user's edit.

**Engine stand.** The Engine mode, next to Build and Test, runs a rotating detonation engine of your own geometry on the GPU. It has a 3D view of the chamber and plug and the unrolled annulus beside it. The feed is either a fixed pressure or a resonant plenum, and you can add injector teeth and an exit throat. Its outputs are thrust, Isp, the azimuthal mode spectrum with the cavity frequencies marked, and a lock-range sweep that maps which mode the engine settles into as the feed changes. The Waves strip under the views sets the injector teeth and the feed for a chosen number of waves, scaled from the Goto et al. rig, and the panel fields it changes flash as it moves. METHODS.md › Rotating detonation engine has the model and its limits.

**VR.** In a WebXR browser (Quest Browser, or Chrome with a PC headset), Setup › Display › View in VR headset appears. In the headset:
- The model stands in front of you, coloured by surface pressure and refreshed every two seconds. Squeeze to grab and turn it; squeeze with both hands to scale it.
- A panel on the left sets airspeed, altitude, angle of attack, sideslip and model size: point at it and pull the trigger.
- A readout of Mach, airspeed, altitude, CL, CD and L/D follows your view.

The solver keeps running on WebGPU. The headset scene is WebGL2 (three.js, loaded when you enter VR), because Quest can't present WebGPU frames in WebXR yet. Use the site, not an embedded copy: frames usually can't open immersive sessions.

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
