# CAD agent: from a tunnel design to engineering geometry

The pipeline has two stages, and each stage has its own owner.

1. **Analysis (the tunnel, SDF).** The Builder tab defines the vehicle as a design record. The tunnel turns that record into a signed distance field. It flies the vehicle through the flow solvers, entry, ascent and the optimiser, and settles the shape.
2. **Geometry (this stage, CAD).** "Export for CAD" writes `<name>.design.json`. You turn that file into exact, manufacturable geometry, and you report back anything that disagrees with what the tunnel assumed.

The design record is the source of truth. Never edit geometry in a way that cannot be written back into the record. If the record cannot express something you need (a fairing, a chine, a door), list it in the report as a proposed new field. Don't silently add it.

## Input: `osp-spaceplane-design` v1

- **Frame:** x runs aft from the nose, y to port and z up. Everything is in metres.
- `design` holds the record exactly as the Builder holds it. Lengths are fractions of `design.L`.
- `derived` holds what the tunnel computed from the record, in metres. Build from this, not from the record:
  - `fuselageSections`: 41 stations, each superelliptic (`squareness`), with a flat underside at `bottom`;
  - `wing.planformHalf` and `strake`: planform corners;
  - `fins`: root, cant and an (x, span) profile;
  - `tailplane`, `canards`, `elevons`, `bodyFlap` (hinge and deflection), `nacelles`;
  - `engines`: positions and bell sizes from the ideal-rocket model, with `enginePerformance`;
  - `boxes`: the internal layout. Every item is an axis-aligned box inside the hull. `mirrored` means there is a starboard copy;
  - `rcs` clusters, `mass` (breakdown and balance points), `areas`, `volumes`.
- `analysis` holds the generated SDF and what the tunnel measured with it: the α table, entry nose heating and ascent. Use it to know what must not change.

## Baseline

`python cad/build_spaceplane.py <name>.design.json --out build/` gives the deterministic starting point. It's written with build123d (OpenCascade) and produces:

- **`<name>.step`:** the outer mould line, elevons and body flap as separate solids (deflected), the nozzle bells, nacelles, and the internal boxes as named solids.
- **`<name>.stl`:** the outer mould line only.
- **`<name>.cad-report.json`:** volumes and areas against the tunnel's figures, and every box checked inside the hull.

## Your job, in order

1. **Run the baseline and read its report.** Boxes outside the hull, or a wetted area more than 5 % from the tunnel's, are findings to report. Don't hide them.
2. **Outer mould line:** keep the stations, and replace the polyline lofts with splines through them. Blend the wing–body and fin–body junctions with fillets no larger than the tunnel's (wing 0.025 L, fins 0.012 L). Give the leading edges the aerofoil's own radius.
3. **Control surfaces:** split them on their hinge lines with a gap of 0.002 L. Model the hinge axis as a datum, and keep the deflections at zero in the master.
4. **Structure from the boxes:**
   - Frames go at every box boundary.
   - Wing spars run at 15 % and 65 % of the chord, and the rear spar carries the elevon hinges.
   - Tank walls follow the box outlines, rounded to the section. Tank volume must stay at or above the box volume × 0.8, the tunnel's packing factor.
   - The thrust structure runs from the engine bay to the nearest frame.
5. **Engines:** bells as revolved 80 % bell contours from throat to exit (`throatRadius`, `exitRadius`, `bellLength`), each with a gimbal point 1.5 throat diameters ahead of the throat.
6. **RCS:** a thruster at each cluster point, firing ±x, ±y and ±z, recessed flush with the hull.
7. **Check against the tunnel:**
   - **Mass properties:** volume within 2 % of `outerMouldLineVolumeM3` and planform area within 2 % of `areas.planformM2`.
   - **Balance:** with the structural masses spread as the tunnel spread them, the balance point within 0.5 % L of `mass.balanceLanding`.
8. **Write back:** produce `<name>.cad-report.json` with what changed, every disagreement with the tunnel, and any proposed record fields. Re-analyse in the tunnel whenever the outer mould line moves by more than one solver cell, about 1 % L.

## Rules

- **Units and frame:** never change them. One STEP per vehicle, with parts named as in `parts` of the baseline report.
- **Flow-wetted surfaces:** don't change these without re-running the analysis. Internal structure is free to change.
- **Tools:** use build123d or CadQuery for B-rep work. PicoGK suits lattices, tank-wall infill and heat-exchanger structure, where voxel CAD does better than B-rep.
