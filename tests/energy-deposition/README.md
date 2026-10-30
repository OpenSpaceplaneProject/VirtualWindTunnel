# Energy deposition check

This runs the app's own compressible-solver kernels (`EULER_WGSL`) on a cylinder at Mach 4, without and with an energy spot ahead of it. It reports the drag coefficient (sampled through the run), the shock standoff on the stagnation line, and the peak temperature.

```sh
node gen.js                     # extracts EULER_WGSL from ../../index.html into eul_src.js
python3 hrun.py '{"NX":66,"NY":60,"NZ":4,"R0":8,"M":4,"T":90,"cyl":true,"dep":null}'
python3 hrun.py '{"NX":66,"NY":60,"NZ":4,"R0":8,"M":4,"T":90,"cyl":true,"dep":{"P":1,"d":12,"r0":2.5}}'
```

You need headless Chromium with WebGPU; on a machine with no GPU, SwiftShader's software Vulkan works. Each run takes 2–7 minutes in software.

Results (also in METHODS.md):

| Run | Drag coefficient | Standoff |
|---|---|---|
| Without the spot | 1.42 | 0.62 R |
| η = 1 | 0.92 | 14 cells |
| η = 2 | 0.89 | — |

Point `gen.js` at the repo's `index.html` if you run it from here.
