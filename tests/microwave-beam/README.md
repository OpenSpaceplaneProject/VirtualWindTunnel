# Microwave beam kernel

`brun.py` pulls `BEAM_WGSL` out of `../../index.html` (`gen.js`). It runs the kernel in headless Chromium on SwiftShader WebGPU, on uniform gas slabs, and scores it against closed-form results:

- transparent gas: all the power leaves upstream;
- collisional under-dense plasma: absorbed fraction against 1 − exp(−αL), with the exact Drude α, plus the decay rate along the axis and power closure;
- over-dense, weakly collisional plasma: reflected at the first cell;
- over-dense, collision-dominated plasma (ν > ω): no cut-off, absorbed;
- a wall: it takes the transmitted power;
- breakdown threshold against pressure at 110 GHz and 303 GHz: the power is bisected to the onset and compared with the Taylor formula. The formula is also checked against the 37 kV/cm worked value in Sci. Rep. 9, 18233 (2019).

Run it with `python3 brun.py`. It writes `results.json`.
