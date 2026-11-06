---
name: osa-design
description: The design track of the Open Spaceplane Agent. Takes a vehicle brief to an analysed design, CAD and a design bill of materials using the Virtual Windtunnel's MCP tools, with no contract, authorities or regulatory gates. Use for "design a spaceplane/vehicle", "get me a BOM", or an OSA programme that needs its Design stage done. Regulation, export, cost and sourcing are handed to the programme track (osa) as flags, never halts.
---

# osa-design

OSA runs a whole programme, from brief to operation. Its gates (contract, authorities, licensing, export screening) belong to the programme, and they stop it before the engineering is done. This skill runs only OSA's stages 1–3 (Brief, Concept, Design) as engineering. It ends with a design pack that OSA's programme track (stages 4–9) can take up separately.

## What it never does

- **It never halts on a non-technical gap.** No licence class, an export-controlled technology, an unknown supplier, an unpriced part, a missing contract: each becomes a line in `programme_flags.md`, and the design carries on. Being unable to get to orbit is a technical gap. Not knowing who licenses the flight is not.
- **It needs no `contract.json` and no `authorities.json`.** It spends nothing, contacts no one and commits to nothing, so there is nothing to authorise.
- **It never prices or sources.** The BOM states what the design is (parts, counts, sizes, masses), and costing and suppliers are the programme's job. A rough cost class can be noted as a flag when it decides feasibility.
- **It keeps OSA's honesty rules:** no confabulation, provenance on every artefact, and a halt after the same technical gap three times without progress.

## Tools

The Virtual Windtunnel MCP server (`mcp/vwt-mcp.mjs`, registered by `.mcp.json`) is the catalogue's design tool:

- **Design:** `get_design`, `set_design`. The record holds fuselage, wing, tail, controls, internal layout and engines. Lengths are fractions of `L`.
- **Analysis:**
  - `set_mode` with `set_controls`, then `wait_converged` and `results`, for low-speed aerodynamics;
  - the Test › Mission tab for ascent, entry and heat shield;
  - `export` with `aero_table`, `trajectory`, `aerothermal` or `heat_shield`;
  - `engine_run` for the RDE stand.
- **Search:** `find_controls` finds any setting by name.
- **Outputs:**
  - `export` `bom` for the design BOM as CSV;
  - `export` `cad_package` for the CAD input;
  - `cad_build` for STEP, STL and the CAD report (`cad/AGENT.md` is the guide for refining the CAD);
  - `screenshot` for figures.
- **Optimisation:** `optimise` runs the shape optimiser; `run_test` runs the solver verification suites.

If the server isn't available, say so and stop at the concept stage. Don't produce a design the tools haven't checked.

## Procedure

Write into an OSA programme folder, with the same layout, so that `osa` can continue it:

```
programme_root/
├── brief.md                   what was asked, and what was assumed
├── stages/02_concept/         requirements.md, configuration.json, trajectory.json, prior_art.md
├── stages/03_design/          design.json, bom.csv, cad/, sim/, design_report.md
├── gaps/                      technical gaps, and any skill acquired for one
├── programme_flags.md         everything non-technical, for the programme track
├── ledger.jsonl
└── summary.md
```

1. **Brief.** Restate the goal: payload, destination, reuse, crew, and any configuration or heritage reference. Ask only what changes the design. Budget, jurisdiction and timeline go to `programme_flags.md` if given, and are not asked for.
2. **Concept.**
   - Search prior art on the vehicle class (`prior_art.md`).
   - Close the capability budget (Δv, mass ratio, payload) and pick a configuration (`configuration.json`, `requirements.md`).
   - Load a starting design: the Build screen's library presets via `find_controls` "Starting point", or build one with `set_design`.
3. **Design loop,** until the requirements close or a technical gap is found:
   1. `set_design` with the configuration.
   2. Run the analyses the requirements need: aero table, ascent margin, entry heating and heat shield, balance (from the `bom` and `design` exports), and engine performance (Build's engine and chemistry).
   3. Compare with `requirements.md`. Change the record, or run `optimise`, and repeat.

   Log each iteration in `ledger.jsonl`: what changed, why, and the figures that moved.
4. **Outputs.**
   - `export` the `design` record to `stages/03_design/design.json`.
   - `export` the `bom` to `bom.csv`.
   - `cad_build` the CAD into `cad/`.
   - Save the analysis tables into `sim/`.
   - Write `design_report.md` with each requirement against what the tools showed, the margins, and what wasn't analysed.
5. **Handoff.** Write `programme_flags.md`: regulatory class and likely pathway, export-controlled items (with the BOM line numbers they touch), long-lead or single-source parts, items needing a partner or a test facility, and the open cost drivers. Write `summary.md`, then stop. Pricing, sourcing, authorisation and building are OSA's stages 4–9, run under its contract and authorities.

## Technical gaps

When a subsystem has no tool here (a precooler, a docking mechanism, avionics), follow OSA's order: look harder, search outwards, then name a partner or tool. Record it in `gaps/`, mark the BOM line `basis: gap`, and carry on with the rest of the design. Halt only if the gap makes the whole design meaningless (the vehicle cannot close its Δv, say), and then say what would unblock it.

## OSA itself

`osa-design-track.patch`, beside this file, applies the same split to OSA's own `skill/SKILL.md`: stages 1–3 become a design track whose non-technical gaps are flags, not halts. Apply it in the OSA repository with `patch -p1 < osa-design-track.patch`.
