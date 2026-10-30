# Methods and notes

How each part of the Virtual Windtunnel works, what it assumes and how to read it. Organised by panel tab.

## Model

### Fix model orientation

For imported models that arrive pointing the wrong way. The nose should face into the flow, the wings run sideways and the belly face down. Yaw 180° turns a model that arrives tail-first. Use the Flight tab for angle of attack.

### Build and Test

Two screens, switched at the top centre.

- **Build:** the design alone, in its part colours, with nothing simulated, so every slider responds immediately. Pick a component from the chips, or click it in the plan or side drawing, and only its sliders show.
- **Test:** the design (or any library body) in the tunnel, with every analysis and the optimiser. What changed in Build is analysed when Test opens.

Parts are linked by relations rather than placed independently. Wing roots sit on the fuselage side. Fins stand on whatever surface is under their root: the fuselage's top, or the wing's upper skin at that chord station, or the wing-tip chord. Elevons hinge on the wing's trailing edge and the body flap on the underside's.

### Spaceplane builder

A spaceplane as components, each with sliders:

- **Fuselage:** elliptic nose with droop, width-to-height ratio, section squareness, planform from round to triangular, upper surface falling aft as on lifting bodies, flat underside, tail closure, blunt base.
- **Wing:** apex, root chord, semi-span (from the centreline, like a published span), sweep, taper, height, NACA 4-digit thickness ratio, dihedral. The root sits on the fuselage side.
- **Control surfaces:**
  - elevons: a fraction of the local chord, between span stations, deflected about their hinge line;
  - a rudder on the fin, opening both ways as a speed brake (the shape is mirrored, so a single-sided yaw deflection isn't possible yet);
  - a body flap hinged at the underside's trailing edge.
- **Other components:**
  - strakes from the body side;
  - tails: single fin, fin and tailplane, cruciform, twin, twin plus centre, V, or tip fins on the wing-tip chord;
  - canards;
  - engine nacelles along the span.
- **Engines:** the Engines tab's ideal-rocket model. Chemistry follows the tanks unless set. The exit area is what gives the vacuum thrust asked for at the chosen area ratio. Bells are 80 % bells, and mass comes from thrust-to-weight. While the builder is the model it owns the engines: the Engines tab shows and simulates them (plumes in the flow solver, thrust and Isp in a single-stage ascent), and edits there come back to the builder. An RS-25-class engine (2,279 kN vacuum, area ratio 69) comes out at 1,878 kN and 365 s at sea level and 443 s in vacuum, against the published 1,860 kN, 366 s and 452 s.
- **RCS:** a forward cluster and two aft pods, sized by thruster force and count. The builder reports quarter-turn times in pitch, yaw and roll, from inertias estimated from the mass layout.

Each group has Randomise, within ranges where real spaceplanes sit.

**Inside**, cabin, payload and tanks stack nose to tail in the listed order. Each is sized to fit the hull where it sits:

- **Tanks** are pressure vessels. The choice is a capsule (cylinder with hemispherical ends) on the centreline, two side by side in a wide, flat section, or an integral tank filling 80 % of the section, as the Shuttle II and X-33 studies used. The shortest wins. Integral tanks count 20 % longer for their non-circular wall, and are at least 0.6 of their height long.
- **Payload** is an ISO 668 container when the hull can take one: 40 ft (12.19 × 2.44 × 2.59 m) if it fits, otherwise 20 ft. It allows 0.1 m clearance all round and 0.15 m at each end, and the floor rises where a round section needs it. Otherwise the bay is the set length.
- **Main gear** sits just behind the landing balance point. It goes in the wing roots when they are deep enough, as on the Shuttle, and otherwise low in the body. The bay is about one tyre-and-strut deep (0.25 m × landing mass in tonnes^⅓). The nose gear sits under the cabin. Nothing overlaps a gear bay: items above one sit higher, and tanks shrink to suit. The stack is laid out three times, because the gear follows the balance point.
- **Engine bay** is sized by the engines.
- **Fill the hull with propellant** solves for the most propellant the tanks can take in the length left over, in the set mixture ratio, by bisection on the layout. That becomes the design's propellant, so ascent, entry and the optimiser all fly it, and a bigger hull carries more. The builder reports the ideal vacuum Δv and the share of usable volume the layout takes. Tanks grow only lengthwise: space above and below the cabin and payload stays empty.

**Structure** is laid out from the design and its layout. Main frames go where something needs one:
- a pressure bulkhead at each end of the cabin;
- a bulkhead at each end of an integral tank, and support frames at each end of a capsule tank;
- the payload bay ends and the gear bays;
- the wing and fin spars where they meet the body;
- the thrust frame ahead of the engines, the nose cap and the base.

Plain frames fill the gaps at the set pitch. A keel runs along the bottom, a chine along the widest line each side, and sills along the payload bay's top edges. Wing spars sit at the set chord fractions, with ribs streamwise at the rib pitch. A spar carries through the body as a wing box unless a cabin, bay or tank is in the way at the wing's height; otherwise its spar frame takes the load round. The thrust structure runs from each engine to the thrust frame. All of it goes into the CAD package. The baseline CAD script builds the frames as section rings or bulkhead discs, the longerons as bars, the spars as lofted webs and the ribs as aerofoil plates.

**Sculpting.** With Fuselage chosen, orange handles on the drawing set the half-width (plan) and the upper and lower half-heights (side) at seven stations. They scale what the sliders make, smoothly between stations. Reset sculpting puts it back.

"Place for least balance shift" tries every order (tanks split fore and aft as well) and keeps the one whose balance point moves least between full and landing.

**Mass** is a first-order sizing estimate: structure per m² wetted, heat shield, tanks per m³, engines, RCS and an "other" allowance. Of the allowance, 3.5 % of the landing mass is landing gear, placed at the bays. The rest (avionics, power, hydraulics, life support, crew) goes where a designer would put it to balance the vehicle. Its centre is solved so the landing balance point sits a 2 % L static margin ahead of the planform centroid, which is where Newtonian lift acts at entry angles of attack. Anything that cannot reach is nose ballast, listed as such. The Test screen's trim and pitching moment are the real check. The landing mass and balance point feed the entry and pitching moments.

**Livery:** part colours, an optional dark underside, and paint in three projections, sampled by surface normal.

### From analysis to CAD

The tunnel's SDF is for analysis: it rebuilds in milliseconds and never fails a union, which the solvers and the optimiser need. Exact geometry is the next stage.

"Export for CAD" writes a design package: the record, everything the tunnel derived from it in metres (sections, planforms, fins, control surfaces, engines, boxes, RCS, mass), and what the analysis found. `cad/build_spaceplane.py` turns that package into STEP with build123d: outer mould line, deflected elevons and body flap, bells, nacelles and the internal boxes. It also writes a report comparing the CAD with the tunnel. `cad/AGENT.md` is the brief for the CAD agent that refines it into engineering geometry and reports back.

The reference library holds the Shuttle orbiter, Buran, X-37B, Dream Chaser, HL-20, X-24B, MiG-105, Hermes, HOPE-X, X-15, Skylon, X-33, the OSP concept, and the two SSTO cases from the Spaceplane Source analyses. Dimensions and masses are public figures, rounded.

### Optimise shape

**Spaceplane, whole mission.** Starts from the built design and varies the numeric fields of the chosen groups within their ranges. Mass and balance point follow the shape. Every candidate is flown through the whole mission:

- ascent drag loss;
- peak nose heating on an entry that has to reach the ground (an entry that skips back out is penalised, not rewarded for its low heating);
- hypersonic L/D;
- landing speed;
- whether the tanks and bay fit;
- pitch stability.

The score is the sum of the first three relative to the start, weighted by priority, plus penalties.

The problem is a descent in many dimensions, with each slider a coordinate:

- **Gradient descent:** SPSA. Each step perturbs every free parameter at once by ± a random sign and scores the two candidates, so a step costs two evaluations however many parameters are free. Adam takes the steps, in the sliders' logistic coordinates, so bounds are never crossed.
- **Simplex:** Nelder–Mead, kept for comparison.
- **Sensitivity:** nudges each free parameter up and down (2n evaluations) and shows, per 10 % of each slider's range, how the score moves and which way improves it. Hovering a row shows the effect on heating, L/D, ascent drag, landing speed and mass.

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

Bipropellant performance comes from NASA CEA (Gordon & McBride), run through RocketCEA by `tools/propellant_tables.py`. For each propellant the script finds the equilibrium chamber state, then expands it isentropically, either in shifting equilibrium (the composition keeps adjusting) or frozen at the throat. It tabulates c*, chamber temperature, vacuum Isp, exit pressure and the exit temperature, molar mass and γ over O/F, chamber pressure (0.1–40 MPa) and area ratio (1.5–400). The app interpolates the tables: within 1% of direct CEA calls at random off-grid points (`tests/propulsion/check.py`). Thrust is ṁ·g₀·Isp_vac − p_a·A_e with ṁ = p_c·A_t / c*. The figures are ideal, with no kinetic, divergence or boundary-layer losses. Flight engines reach 93–98% of them: RS-25 0.978, RL10B-2 0.967, RD-180 0.942, Merlin 1D Vacuum 0.934 and AJ10-190 0.944 of the app's figure. The XLR99 reaches 0.877, outside that band; its O/F is assumed. Monopropellant hydrazine, cold nitrogen and Custom still use the perfect-gas ideal rocket from Tc, γ and molar mass. In the flow solver each exit plane is a source boundary that injects that exit state, so the plume, its shock cells, base pressure and any interaction with the airframe are solved. The exhaust is carried as the solver's gas with the true exit density, velocity and pressure, so mass flow, momentum and pressure are right, while its temperature and sound speed follow air's properties. For an aerospike only the primary nozzle is modelled this way; the spike is geometry, so its thrust appears in the surface pressure. Thrust shown here is the nozzle exit thrust; pressure on the spike and base adds to it through the force coefficients.

### Energy ahead of the nose

Conditions › Energy ahead of the nose adds heat to the air ahead of the body, as a microwave or laser beam focused there would. It's a source term in the compressible solver's energy equation: a spherical Gaussian spot, q = q₀·exp(−r²/r₀²), cut off at 3r₀, centred a set distance ahead of the nose.

The nose is the mean position of the most upstream solid cells. Power is set as η = P / (½ρ∞V³A), a multiple of the free stream's kinetic energy flux through the frontal area, which is the usual measure in the energy-deposition literature. The panel shows the equivalent watts at the current flight condition. The spot radius is never below 1.5 cells, so the grid resolves it.

The heated gas is hotter and faster than anything in the free stream, so the time step is bounded the same way as for a hot exhaust. That bound comes from the total enthalpy of a parcel crossing the spot's centre at half the free-stream speed.

With Source set to Spot, the power is fixed and goes where it's put. Set to Microwave beam, the beam is traced and the gas decides where it goes.

#### Microwave beam

A Gaussian beam leaves an emitter at the nose and travels upstream along the flight axis, with power, frequency, waist and focus distance as inputs. Every frame, each ray in the beam's column marches cell by cell from the emitter to the far boundary. In each cell it reads the gas state and does the following:

- **Electron density and temperature** come from a second Cantera table over the same density and energy axes as the real-gas table. This holds equilibrium 11-species air, so ionisation is equilibrium.
- **Collision frequency** is electron–neutral plus electron–ion: ν = n·1e-19 m²·√(8kT/πm) + 2.91e-11·nₑ·T_eV^-1.5.
- **Permittivity** is cold-plasma Drude, ε = 1 − ωp²/(ω² + ν²) + i·ωp²ν/(ω(ω² + ν²)), giving the attenuation α = 2(ω/c)·Im√ε. The power absorbed in the cell goes into the energy equation.
- **Cut-off.** When Re ε < 0 and ν < ω, the plasma is above the critical density, 1.24e16·f² m⁻³ with f in GHz. The beam is reflected there, and the reflected part is tallied and not traced further.
- **Breakdown.** Where the beam's rms field beats the threshold for air, the gas breaks down. The model takes the threshold from Taylor et al., as used by Cook et al. (2010) at 110 GHz: E = p·√(1+ω²/ν_c²)·3.75·[D/(pΛ²) + 6.4e4]^(3/16) V/cm. Here ν_c = 5.3e9·p s⁻¹, p is in Torr, D is free-electron diffusion at 2 eV, and Λ is the local beam radius / π. A broken-down cell is set to at least the critical density, so it absorbs strongly or reflects.

The panel shows where the power went: absorbed at breakdown, absorbed in hot gas, reflected by plasma, passed upstream, or hit the body.

**Limits:**
- Rays travel straight. There's no refraction, diffraction or interference.
- Reflected power is dropped rather than followed.
- Breakdown is a threshold switch. It doesn't model avalanche growth or the filament arrays seen in experiments.
- Ionisation is equilibrium. At high altitude that overestimates electrons; see the RAM-C check in tests/VALIDATION.md.

Check, run with the app's own solver kernels: a cylinder at Mach 4, inviscid, 8 cells to the radius, with the spot 1.5 radii ahead and 2.5 cells in radius.
- Without the spot: the shock stands 0.62 R off, against 0.52 R from Billig's correlation, which is within a cell. The drag coefficient is 1.42.
- With η = 1: the shock moves forward to the spot and the drag coefficient falls to 0.92 (−35%).
- With η = 2: the drag coefficient is 0.89 (−37%), so most of the gain comes early.

All three runs ran to the same flow time and their drag settled. The grid is coarse, and other grids weren't tried.

### Rotating detonation engine

The Engine bench runs a rotating detonation chamber of your own geometry: inner diameter, channel width, length, plug angle, injector area ratio and plenum pressure. It uses the engine's gaseous propellant (ethylene, methane or hydrogen with oxygen) at the engine's O/F.

**Grid and equations.** The annulus is unrolled: one axis runs round the circumference and is periodic, the other runs downstream from the injector face to the tip of the conical plug. The flow area can change downstream, which models the plug expansion as a confined nozzle out to the outer diameter. This quasi-2D layout is the same as NASA Glenn's Q2D code (Paxson; Miki et al. 2020). The equations are the reactive Euler equations, second-order MUSCL with an HLLE flux and two-stage Runge–Kutta, run on the GPU.

**Gas model.** It is NRL's two-γ model (Schwer & Kailasanath):
- Reactants carry the heat of reaction.
- Products take the equilibrium γ and molar mass of the Chapman–Jouguet (CJ) state, the ideal detonation.
- The heat of reaction is calibrated so the model's CJ speed equals the equilibrium CJ speed from Cantera.

`tools/cj.py` computes those CJ speeds. They agree with the Caltech detonation database to within 0.1%: H₂–air 1969 m/s, C₂H₄–O₂ 2374 m/s, CH₄–O₂ 2390 m/s.

**Chemistry.** It is an ignition-delay model with a temperature gate, the way NASA's Q2D code gates its reaction:
- Gas hotter than 0.65 of the post-shock temperature counts down a fixed ignition delay.
- When the delay runs out, the reactants convert.
- The delay and the conversion each take half a cell's transit behind the lead shock, so the burn is close to instant once the gate opens. That is Q2D's approach on coarse grids.
- Gas below the gate never ignites.
- Because ignition only happens behind shocks, the model cannot split one wave into several the way hot spots and contact-surface burning do in a real engine. The wave count is set at the start by the number of igniters, spaced evenly round the ring; a run then shows whether the design holds that count or collapses to fewer.
- The gas must also be above a pressure gate, 0.06 × the mixture's CJ pressure ratio × the plenum pressure: about 2.0 × plenum for ethylene, 1.8 for methane and 1.1 for hydrogen. A fixed 2 × plenum stopped hydrogen, whose detonation compresses only about 19 times, from relighting once the start-up overdrive had decayed.

The gate stops fresh propellant from burning where the numerics smear it into hot products. That happened at the injector between waves with a one-step Arrhenius rate.

A delay that also shortens with temperature, the usual induction model, decoupled the lead shock on these grids at every steepness tried (θ = 3–20), and the wave fell to 60% of CJ. A gate at 0.75 failed the same way.

With two-cell zones, a 1D detonation held, but in the Goto engine the starting wave died in the 10 mm fresh layer. The reaction zone has to be many times thinner than the layer the wave runs through.

1D check (`tests/rde/run1d.py`), C₂H₄–O₂ at 1 atm:
- 1.2% below CJ on the 0.4 mm grid.
- 0.2% below CJ on the 0.2 mm grid.

**Reaction zone.** Real reaction zones are tenths of a millimetre, so detonations here are thicker than real ones. The cells must be small against the fresh-propellant layer the wave runs through, a few millimetres in small rigs.

**Injector and outlet.**
- Each injector-face cell draws premixed propellant from the plenum through a throat of the set area ratio, choked when the chamber pressure is low enough. It acts as a wall while its pressure is above the plenum's.
- The outlet passes supersonic flow out, and holds ambient pressure where the flow is subsonic.

**Outputs.** Mass flow and thrust at the outlet, Isp, number of waves and their speed, and mean pressure 8 mm before the end of the annulus. All are averaged over the second half of the run.

**Not modelled:**
- Propellant mixing: the propellant is premixed.
- Injector recovery dynamics beyond the choked or unchoked throat.
- Heat loss to the walls.
- Viscosity.
- A plug's free outer jet boundary: the confined expansion is the over-expanded limit.

Real rigs run their waves at 70–90% of the CJ speed, mostly because of mixing. Expect the solver's waves to run faster than measured. See tests/VALIDATION.md for the comparison with the Goto et al. (2021) ethylene/oxygen sled-test engine.

**Across the gap.** With one cell across the gap, the annulus is unrolled at its mean radius (above). With more cells, the gap is resolved on a mesh between the inner body and the outer casing. The inner body is the plug surface downstream, at the radius that gives the area A(y). Each cell is a ring sector, and its faces are computed exactly per unit angle:
- Meridional area and ∫r dA from the vertex radii.
- The sloped faces' radial and axial area components.
- The axial faces' annular areas.

A fourth momentum component carries the radial velocity. The cylindrical terms are added as sources: (p + ρu_θ²)/r̄ radially and −ρu_r u_θ/r̄ azimuthally. Together with the face areas, they keep gas at rest at rest exactly, including against the sloped plug (checked to 10⁻⁴ m/s after 400 steps). Both walls are slip walls.

Near the plug tip the circumference shrinks towards zero, so the azimuthal metric holds the radius at no less than half the mean radius. Otherwise those cells would set a time step tens of times smaller.

The mesh spreads its cells across the widening gap beyond the annulus, so the plug flow is coarser across than along. The 2D views show the gap-averaged state, plus one column across the gap just behind the leading wave. The 3D cutaway draws the cells against each wall and the full gap on its cut faces. Flows and thrust are summed over the gap exactly.

One cell reproduces the quasi-2D solver to rounding error on the Goto engine. With 4 cells, mass flow and peak pressure stay within about 3% of the one-cell run over the first 41 µs, the same times compared.

**Wave count.** The model holds fewer waves than real engines at the same feed. The mass balance h = ṁ / (n ρ w D) gives the fresh-layer height each of n waves meets. A real wave needs h above about 12 detonation cells, and cells shrink as pressure rises, so higher pressure allows more waves. Here the smeared front needs a layer some number of grid cells deep instead. That depth doesn't shrink with pressure, so raising the plenum pressure adds density but not height. More waves need a finer grid.

**MAV class.** The preset is NASA's 7K lbf RDRE (Teasley et al., AIAA 2023): 142 mm inner body, 8.4 mm gap, 69.5 mm from the injector to the throat and a 30° plug. It runs on methane/oxygen at O/F 3.5 and a 5 MPa plenum, about 8.7 kg/s. That is about one MAV engine's share of thrust. The start-up fill scales with the plenum pressure (0.1 p₀ when that is above ambient) so the igniter clears the ignition gate.

**Ionisation and magnet.** This is a feasibility map, not a coupled solver. It works from the run's time-averaged flow, cell by cell:
- Thermal electrons from the Saha equation for the seed: potassium 4.34 eV, caesium 3.89 eV, or 1% O₂ at 12.07 eV unseeded. Chemi-ionisation in the reaction zone is not included.
- The electron density a target conductivity needs, σ = n_e e² / (m_e ν), with ν = N · 10⁻¹⁹ m² · v_e at the set electron temperature.
- The microwave power to hold it above the thermal level, W β (n_req² − n_T²): 50 eV per electron made and recombination at 2 × 10⁻¹³ m³/s.
- Electron and ion Hall parameters at the set field. Ion–neutral collisions use 10⁻¹⁸ m².
- The interaction parameter S = σ_eff B² L / ρ|u|, with σ_eff = σ / (1 + β_e²) for Hall currents free to flow. L is the annulus length in the chamber and the plug length on the spike. Each region's S is its total magnetic drag over its total momentum flux.
- The skin depth √(2 / μ₀ σ ω) at the microwave frequency, which holds while collisions outpace the wave.

The constants are order-of-magnitude. The power scales as density squared, so the expanded flow on the spike is far cheaper to ionise than the chamber.

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
