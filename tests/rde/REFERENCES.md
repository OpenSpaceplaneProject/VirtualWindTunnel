# RDE validation data

These cases are taken from the Supernova Labs RDE library (Google Drive, "Rotating Detonation Engine", 49 items). The numbers are quoted from the papers.

## Goto et al., "Thrust Validation of Rotating Detonation Engine System by Moving Rocket Sled Test", JPP, doi:10.2514/1.B38037

Engine and propellants:

| Quantity | Value |
|---|---|
| Propellants | gaseous C₂H₄ / gaseous O₂ |
| Inner diameter Dᵢ | 60.5 mm |
| Channel width Δ | 3.2 mm |
| Combustor length | 48 mm |
| Plug | 30° conical, not truncated |
| Nozzle expansion ratio | 5.5 |
| Injectors | 72 × 0.5 mm fuel holes, 0.3 mm oxidiser slot |
| Exhaust | sea level |

Results (± is the paper's uncertainty):

| Test | ṁ, g/s | Φ | CTAP₄₀, MPa | F, N | Isp, s | Waves | v_det, m/s |
|---|---|---|---|---|---|---|---|
| Stand 1 | 125 ± 10 | 1.1 ± 0.2 | 0.18 ± 0.02 | 172 ± 14 | 141 ± 23 | 3 | 1748 ± 35 |
| Stand 2 | 137 ± 11 | 1.2 ± 0.2 | 0.18 ± 0.02 | 183 ± 17 | 137 ± 23 | 3 | 1606 ± 235 |
| Stand 3 | 141 ± 12 | 0.6 ± 0.1 | 0.15 ± 0.03 | 140 ± 19 | 102 ± 23 | 4 | 1471 ± 197 |
| Sled | 143 ± 5 | 1.0 ± 0.1 | 0.19 ± 0.03 | 201 ± 29 | 144 ± 26 | 3–4 | 1460–1800 |

Near stoichiometric, the paper reports 78–85% of the ideal Isp for correct expansion (CEA, constant pressure). It puts the shortfall down to over-expansion at sea level.

## Harroun, Heister, Sardeshmukh, Ruf, "Effect of Aerospike Nozzles on RDE Performance for Rocket Applications", AIAA 2019-0197

Purdue rocket RDE, test #53:

| Quantity | Value |
|---|---|
| Propellants | natural gas / O₂, O:F 3.89 |
| ṁ | 1.15 kg/s |
| CTAP | 8.6 atm |
| Thrust | 2.3 kN (Isp ≈ 204 s) |
| Waves | 2 at 13.8 kHz |
| Wave speed | 88% of CJ |
| Detonation pressure ratio (CEA, from the paper) | 31.8 |

The paper's Loci/CHEM simulations (not test data) give these results:
- An aerospike improves Isp by up to 16% over no nozzle.
- The oscillating exit pressure deepens base drag without a nozzle by up to about 10%.

## Miki, Paxson, Perkins, Yungster, "RDE Nozzle Computational Design Methodology", AIAA 2020-3872

The approach is Q2D, NASA GRC's quasi-2D code:
- Euler equations on the unrolled annulus, single species, calorically perfect gas.
- Roe flux, MUSCL, RK2.
- Finite-rate reaction gated by a reaction temperature.
- Loss models for the inlets and wall heat transfer.

Its exit flow feeds a 3D nozzle calculation.

Validation is the Naval Postgraduate School H₂/air rig at Pt 131.7 psia, Tt 510 °R, Pexit 14.7 psia, φ 0.972, air 1.51 kg/s. Q2D predicted mass flow, detonation speed and two time-averaged pressures. Its gross thrust was within 15% of measured.

The best of the five nozzles tested gave 3.2% more thrust than the baseline.

## Schwer & Kailasanath, "Numerical Study of the Effects of Engine Size on RDEs" (NRL)

The model:
- 2D unrolled annulus.
- Micro-injector inflow boundary.
- An induction-parameter model, ∂τ/∂t + ∇·(τv) = ρ/T_ind, with T_ind from the NRL H₂–O₂ fit. When τ/ρ > 1 the reactant is converted.
- Isp = F/(g₀ ṁ).

Baseline case:

| Quantity | Value |
|---|---|
| Dᵢ / Dₒ | 130 / 150 mm |
| Length L | 177 mm |
| Azimuthal length | 439.8 mm |
| Depth δ | 10 mm |
| Injector area ratio Aₜ/A_w | 0.2 |

The fuel-based Isp for H₂/air spans 3300 to 5500 s, depending on pressure and length.

## Shah, "Computer Modeling of a Rotating Detonation Engine in a Rocket Configuration", AFIT thesis 2015

This is a reduced-order, four-stream NPSS model. Peak Isp is about 5500 s air-breathing (fuel-based) and about 150 s as a rocket.

## Teasley, NASA MSFC release, 2022

The NASA / IN Space regeneratively cooled RDRE:
- More than 4000 lbf for 15 s.
- 620 psia mean injector-face pressure.
- 4–5 co-rotating waves.
- 17 starts and over 600 s of total run time.
