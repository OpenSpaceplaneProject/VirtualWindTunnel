# Open Spaceplane Project — Virtual Windtunnel

A browser-based virtual wind tunnel for anything from paper planes and Cessnas to fighters, rockets and spaceplanes going to and from orbit. It runs entirely on your GPU through WebGPU — no install, no server.

Brought to you with 💖 & determination by [Supernova Labs](https://supernovalabs.co.uk).

## Run it

Open https://windtunnel.supernovalabs.co.uk in a WebGPU-capable browser (recent Chrome or Edge; Safari 26+; Firefox with WebGPU enabled). To run locally, serve the folder over HTTP (for example `python3 -m http.server`) and open `http://localhost:8000` — opening `index.html` straight from disk blocks the model file from loading.

## What's inside

- **Solver chain, picked per regime:** lattice-Boltzmann (D3Q19) at low speed; a compressible Euler solver (MUSCL + HLLC, ghost-cell immersed boundary) from transonic to supersonic; modified-Newtonian / free-molecular panel methods with Knudsen-number bridging for hypersonic and rarefied flight.
- **Aerothermal loads:** stagnation-point and distributed convective heating, wall temperature and burn-through maps, exportable as CSV.
- **Entry simulation:** 3-DOF point-mass entry over a spherical Earth with an editable bank/α event timeline and playback.
- **Propulsion (stage 1):** ideal-rocket bell and aerospike exhausts as boundary sources in the Euler solver.
- **Import:** STL, OBJ, GLB and STEP (STEP via `occt-import-js`), voxelised into an exact signed-distance field.

All results are physical approximations from the models named above — useful for design exploration, not a substitute for validated CFD or test.

## Files

- `index.html` — the whole application (HTML, CSS, JS and WGSL shaders).
- `patch.png`, `favicon-32.png`, `apple-touch-icon.png` — mission patch and icons.
- `models/redarrow.json` — default spaceplane model.
- `.github/workflows/pages.yml` — optional GitHub Pages deploy on every push to `main`. The live site is served by Vercel at https://windtunnel.supernovalabs.co.uk (static, no build step).
