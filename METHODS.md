# Methods and notes

How each part of the Virtual Windtunnel works, what it assumes and how to read it. Organised by panel tab.

## Model

### Fix model orientation

For imported models that arrive pointing the wrong way. The nose should face into the flow, the wings run sideways and the belly face down. Yaw 180° turns a model that arrives tail-first. Use the Flight tab for angle of attack.

### Spaceplane builder

A spaceplane as components: fuselage (elliptic nose with optional droop, width-to-height ratio, section squareness from round to boxy, planform from round to triangular, upper surface falling aft as on lifting bodies, flat underside, tail closure, blunt base), wing (apex, root chord, semi-span, leading-edge sweep, taper, height, thickness, dihedral), strakes, tail (single fin, fin and tailplane, cruciform, twin, twin plus centre, V, or tip fins, with cant), canards, engine nacelles along the span, and a body flap. One design record generates the SDF shape, the internal layout, the mass and the balance point.

Inside, the fuel tanks, oxidiser tanks and payload bay are packed nose to tail in the listed order, from behind the nose cone to the engine bay. Each takes the length its volume needs at 80 % of the local cross-section. If they don't fit, the overrun is shown.

Mass is a first-order sizing estimate:

- structure per m² of wetted area;
- heat shield at 10 kg/m² windward and 4 kg/m² leeward;
- tanks per m³ by propellant;
- engines;
- an "other" allowance (systems, gear, crew, margin).

Building applies the landing mass and landing balance point to the vehicle, so pitching moments and the entry use them.

The reference library holds the Shuttle orbiter, Buran, X-37B, Dream Chaser, HL-20, X-24B, MiG-105, Hermes, HOPE-X, X-15, Skylon, X-33, the OSP concept, and the two SSTO cases from the Spaceplane Source analyses. Dimensions and masses are public figures, rounded. Each shape is a component approximation, and "other" is set so the dry or gross mass matches the published figure.

### Optimise shape

**Spaceplane, whole mission.** Starts from the builder's design and varies the numeric fields of the chosen groups (fuselage, wing, strakes, tail, canards) within their ranges. Mass and balance point follow the shape. Every candidate is flown through the whole mission:

- ascent drag loss, from the ascent simulator with the candidate's drag curve;
- peak nose heating, from the entry simulator with the candidate's own α table;
- hypersonic L/D (cross-range), best between 15° and 45°;
- landing speed at α 15° (Helmbold lift slope plus Polhamus vortex lift on the planform);
- whether the tanks and bay still fit, and pitch stability (dCm/dα over 30–45°, about the landing balance point).

The score is the sum of the first three relative to the starting shape, weighted by the priority. Tanks that don't fit, landing above the limit and pitch instability are penalties. Surface models only (Newtonian), so a candidate takes seconds and the flowfield is paused. Up to 300 candidates; with many groups free the simplex moves slowly, so free one or two groups at a time.

**Least wave drag body (benchmark).** Five radii of a body of revolution at fixed length and volume, each candidate scored by the flow solver's pressure drag. Linear theory's answer is the Sears–Haack body, so this checks the optimiser and solver find a known optimum before you trust them on your own problems.

### Edit shape as code

Write `fn sdf(p: vec3f) -> f32`; negative is solid. Body frame: x downstream from the nose, y span, z up, one unit = the vehicle length above. It runs on the GPU at every cell, so booleans and lattices cost nothing extra. Library: `sdSphere sdBox sdRoundBox sdEllipsoid sdCapsule sdCylinderX sdRoundCone sdTorus sdWing sdDeltaWing sdPlate sdTri2 sdGyroid stl opUnion opSub opInter opSmoothUnion opSmoothSub rotX rotY rotZ`.

## Flight

### Ascent

Planar point-mass ascent over a rotating spherical Earth, serial stages. Thrust follows back pressure (F = F_vac − p·A_e, exit area from the two Isps); an optional g limit throttles down to 40 %. Guidance: vertical rise to 60 m/s, a pitch kick, a gravity turn while the air matters (dynamic pressure above 1 kPa or below 40 km), then zero-effort-miss steering that zeroes the climb rate at the target altitude as the speed reaches circular, for direct insertion. The kick angle is searched for the most Δv left at insertion. Losses are integrated along the path: gravity, drag, steering.

Drag is the tunnel model's zero-lift drag on its frontal area, by component build-up from the measured geometry: turbulent skin friction on the wetted area (Schlichting, compressible), base drag (Hoerner), and wave drag from the slender-body area rule of the voxel S(x) — rising through the transonic drag rise and blending to the Newtonian pressure drag of the actual shape by Mach 5. Where S(x) falls faster than an 8° boat-tail the flow is taken as separated: the drop counts as base area. Launchers: class presets with their stack drawn as a cylinder with an ogive nose for drag. A fairing is carried and dropped above 110 km unless the model rides outside. 1 % of each stage's propellant is unusable. "This vehicle, single stage" flies the builder's design on its own propellant and engines. Vertical rocket ascent only: horizontal take-off, wing lift during the climb and air-breathing modes are not modelled yet.

### Controls

Keyboard: W/S pitch, A/D roll, Q/E yaw; hold Shift for faster rates. Mouse: while flying, left-drag is the stick and right-drag orbits the camera. Gamepad: left stick pitch and roll, right stick yaw. The artifact viewer may block gamepads; opening the page in its own tab avoids that.

### How the timeline works

Each event fires once, in order, when its condition is met: at entry, after a time, once braking reaches a number of g, below a Mach number or altitude, or at the top of a skip. It sets a new bank angle and, optionally, a new angle of attack. The vehicle turns towards them at 5° per second in bank and 1° per second in angle of attack, as a real one would, so a roll reversal passes through wings-level and briefly lifts the vehicle. Lift and drag at each angle of attack come from analyses of the actual shape at −10° to 60°. The profiles are representative of the published Shuttle and Artemis I entries, not flight data. This is a planar model: bank sets how much lift points up, not the turn, so cross-range isn't computed.

Playing the entry steps through the trajectory faster than real time. The axes, flowfield Mach, attitude and heating follow it; the heating map uses the conditions at each moment.

### Reading results while moving

Time runs in flow-throughs: the time air takes to pass one body length. Real fighter manoeuvres take about 5–20; shorter durations exaggerate the lag of separated flow, which shows as a wider loop in the lift trace. At low speed the surface moves with the body. The high-speed flowfield treats motion as a series of steady states, and the heating and entry results update when the motion stops.

The flow patterns are meaningful while moving; the force numbers during fast motion are rough. Air swept up or released by the moving body isn't counted in the force yet, which reads drag low during a rapid pitch-up. Hold an attitude for a flow-through or two before reading loads.

### Edit shape as code

Airspeed and altitude are set on the axes around the scene, or by dragging the dot between them.

## Engines

### How intakes and air-breathing engines are modelled

The intake, spike, cowl and diffuser are geometry, so the cone and cowl shocks, the terminal shock, spillage round the lip, and buzz or unstart are all solved by the inviscid flow solver. Without viscosity there is no boundary layer, so shock–boundary-layer separation, bleed and the losses that come with them are missing: real recoveries are a few per cent lower.

At the engine face the duct ends in a boundary that sets the static pressure, as an engine does. Behind it the engine is lumped into a plenum whose pressure rises when more air arrives than leaves. A turbojet's compressor draws a fixed mass flow. A ramjet burns kerosene-class fuel to the set combustor temperature (fuel flow from the heat balance), and its choked nozzle throat passes a mass flow proportional to pressure over the square root of temperature; the exhaust then leaves the base through an ideal nozzle as a jet the solver carries on. The exhaust is treated as air (γ 1.4) and the dump into the combustor keeps the static pressure, so its losses are included. Combustion is complete and the nozzle ideal, so ramjet thrust and specific impulse are an ideal cycle: real engines read roughly 15–30 % lower.

Capture is the mass flow reaching the face over the flow through the cowl lip area in free stream. Recovery is the mass-averaged total pressure at the face over free stream. The characteristic sweep raises the back pressure step by step, then lowers it again, holding each step for one and a half flow-throughs (the shock moves only as fast as the duct fills or empties). Net thrust is uninstalled: jet momentum and pressure thrust minus the momentum of the captured air; cowl and spillage drag show in CD.

The full-flowpath engines have no lumped parts: intake, combustor and nozzle are geometry and the whole duct is solved, so shocks travel through the engine. Fuel is released as heat in the combustor volume, in proportion to the air passing through it (fuel flow from the equivalence ratio, complete combustion at 98 % efficiency). Mixing, ignition delay, dissociation and the fuel's own mass are not modelled, and the gas stays at γ 1.4, which overstates heat release at the highest temperatures. Thrust is the net axial pressure force on all the hardware, inside and out, so it is installed thrust without skin friction.

Exhaust plumes are solved by the high-speed flow solver, above Mach 0.6. Low-speed jets come with the landing work.

### How engines are modelled

Each nozzle is ideal-rocket theory: frozen, isentropic, one-dimensional flow from the chamber to the exit area ratio, which gives exit Mach number, pressure, velocity and mass flow. Real engines lose a few per cent; the presets are representative, not certified data. In the flow solver each exit plane is a source boundary that injects that exit state, so the plume, its shock cells, base pressure and any interaction with the airframe are solved. The exhaust is carried as the solver's gas with the true exit density, velocity and pressure, so mass flow, momentum and pressure are right, while its temperature and sound speed follow air's properties. For an aerospike only the primary nozzle is modelled this way; the spike is geometry, so its thrust appears in the surface pressure. Thrust shown here is the nozzle exit thrust; pressure on the spike and base adds to it through the force coefficients.

### Air-breathing engine

The intake is solved by the high-speed flow solver, above Mach 0.6.

Solved end to end: intake, combustor and nozzle are all geometry, and the fuel's heat is released in the combustor volume.

### Chamber conditions

Editing these switches the propellant to Custom. Values from CEA or RPA for your mixture ratio give the best numbers.

## Solver

### What the suite checks

Cone surface pressure at Mach 2 and 6 against the exact Taylor–Maccoll solution; sphere stagnation pressure at Mach 3 against the Rayleigh pitot formula, and at 6 km/s in equilibrium air against a Cantera equilibrium calculation; pitot-intake recovery at Mach 1.6 against the normal shock; and low-speed sphere drag at Re 10⁴ against the standard drag curve. Each runs on the current grid until it settles (at most 10 flow-throughs or 10 minutes) and is marked * if it did not. Exact references are computed at the solver's own γ. Hover a row for details. Your case is restored afterwards.

### Low-speed solver settings

Sharp-edged bodies such as the delta wing separate at the edge, so their vortices barely depend on Reynolds number. Rounded bodies need more cells across the boundary layer than any browser grid gives, so treat their drag as rough.

### How the flowfield is calculated

The flow solver resolves shock waves, expansions and the wake, and gives a second opinion on surface pressure. It has no friction layer, so heating comes from the engineering estimates on the Heat tab. Shocks are about two cells thick, so a thin shock layer needs a finer grid or a bigger body. (Inviscid MUSCL–HLLE finite volume, two-stage Runge–Kutta, slip walls, perfect gas.)

### How engines are modelled

Picked automatically from the airspeed (switches at Mach 0.6). Click to override.

### Local refinement

Click a point on the body first (a lip, a gap, a leading edge). The finer grid takes its boundaries from the current solution, so settle that first. High-speed flowfield only.

## Heat

### How this is calculated

Heat conducts through the layers in one dimension (straight through the skin, not sideways). The outer face is heated by the air and cools by radiating. Heat keeps soaking inwards for 20 minutes after the run, which is often when the airframe peaks. Material values are typical published figures, not supplier data, so check them before relying on the margins. Ablating shields (PICA) are treated as if they don't erode.

### How heating is calculated

Rounded areas such as the nose and leading edges use the standard blunt-body estimate, from the local curvature. Flatter areas use a flat-plate estimate based on distance from the nose. Each spot takes whichever is higher, so the map leans conservative. Edges sharper than two cells are rounded off to two cells, so refine the grid for sharp leading edges. Whether the flow is smooth or turbulent is the biggest unknown, so try both settings. Once the flowfield has settled, the boundary layer takes its edge pressure and velocity from the flowfield itself, which carries the right entropy along each streamline; before that, and with the flowfield off, it uses Newtonian pressure. Above about 90 km the heating is combined with the free-molecular limit so it never exceeds the energy the air molecules bring. Skin friction from the same boundary layer is added to the drag. (Sutton–Graves with Lees distribution; Eckert reference enthalpy; Schaaf–Chambre free-molecular flow.)

### How the flowfield is calculated

Heating and entry analysis use the high-speed solver. It switches on by itself above Mach 0.6 on the airspeed bar.

### Entry trajectory

Bank and angle of attack follow the entry timeline on the Flight tab.

### Heat shield

Layers from the outside in; the last is the airframe. The burn-through map uses this stack over the whole vehicle. Click the model to check the stack at one spot.

## Display

### Shocks and glow

Glow is auto-exposed, like a camera, so it reads at any altitude; the colours are what change with speed. Hot surfaces glow as blackbodies at their temperature, which is physical. The shock-layer colour is an approximate air-emission palette from the flowfield temperature and density: it shows where air glows and roughly what colour, not radiative heating. Perfect-gas temperatures overshoot at orbital speed, so keep γ near 1.2 there.

## Loads

### How the structure is analysed

Linear elastic finite elements, one eight-node brick per voxel of the model (with incompatible bending modes, so even a one-voxel skin bends correctly: a test cantilever matches beam theory to 0.2 %). The skin is the shell of voxels within the set thickness of the surface; a skin thinner than a voxel is smeared over one voxel with its stiffness and mass scaled down. The load is the flow solver's surface pressure at the current condition. In flight nothing holds the vehicle, so the load is balanced by its own inertia (inertia relief), using the vehicle mass from the Model tab carried on the skin. Spars, ribs and frames are not modelled unless you build them into the shape (Edit shape as code). Stress is at each voxel's centre; the peak quoted ignores the highest 0.5 % of voxels, where the stair-stepped voxel surface makes stress spike.

### Column guide for FE tools

Columns `x,y,z,nx,ny,nz,cp,p_pa`, in metres in the body frame with outward normals; gauge pressure `p = Cp·½ρV²`. Map the points onto your FE faces by nearest neighbour (ParaView Resample With Dataset, or a KD-tree) and apply as a distributed pressure, e.g. CalculiX `*DLOAD … P`. The solver's Reynolds number is capped at one million, so the pressure pattern is scaled from that.

Columns, in the body frame with outward normals: `x_m,y_m,z_m,nx,ny,nz,cp,p_pa,q_cw_w_m2,h_film_w_m2k,t_recovery_k,t_radeq_k,regime,t_peak_k,t_struct_peak_k,burn_through`. Map the points onto your FE faces by nearest neighbour, for example ParaView Resample With Dataset. In CalculiX, apply pressure as `*DLOAD`. Apply heating as `*FILM` with coefficient `h_film` and sink temperature `t_recovery`, which gives the right heat flux at any wall temperature.

### Time-averaged pressure

Start the mean after about two flow-throughs, once the start-up has washed out. The export uses the mean when one is running.

### Export

A spreadsheet of every point on the skin with its position and pressure, scaled to the airspeed and altitude on the axes and the vehicle length on the Model tab.

A spreadsheet of every point on the skin with its position, pressure, heating and temperature at the current moment. It also has the peak temperature over the whole entry and the burn-through flag for the current heat shield.
