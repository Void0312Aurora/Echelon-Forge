# A8-W2 Part Failure Vocabulary

Status: `2026-06-07` partial implementation note for `A8-DEC-D`.

## Scope

This worker maps existing synthetic mechanism-load evidence into named
part-failure modes without changing flight dynamics consumers or claiming
calibrated vulnerability.

Implemented internal vocabulary:

| Mode | Primary input | Existing state entry |
| --- | --- | --- |
| `puncture` | fragment energy, fragment areal density, penetration margin | fuel, propulsion, avionics, structural nicks by system context |
| `cut` | continuous-rod cut margin, penetration margin | control, propulsion, structural loss by system context |
| `blast_deformation` | blast overpressure and impulse | structural overstress, control deformation, propulsion deformation |
| `fuel_leak` | breach-like puncture, cut, or blast load on fuel components | `fuel_leak_severity`, `flammable_fluid_exposure`, fuel integrity |
| `hydraulic_pressure_loss` | breach-like or cut load on hydraulic supply/consumer paths | `hydraulic_pressure_availability`, hydraulic integrity |
| `electrical_loss` | puncture, blast, or thermal load on avionics/power components | avionics and command/navigation integrity |
| `data_loss` | puncture, blast, or power/data damage on mission, sensor, data-link components | avionics, command/navigation, mission crew effectiveness |
| `fire_source` | thermal source on fuel, propulsion, avionics, power components | ignition source and fire severity |
| `structural_weakening` | cut or blast damage on structure, wing, spar, engine, propeller, control structure | structural integrity, overstress, flutter exposure |

## Data Shape

Components may optionally declare either:

```json
"failure_modes": ["fuel_leak", "fire_source"]
```

or:

```json
"failure_mode_weights": {
  "fuel_leak": 1.0,
  "fire_source": 0.8
}
```

When absent, the default effects model infers mode weights from component
system, component name, redundancy group, and existing dependency hints. The
default remains synthetic engineering scaffolding.

## Integration Boundary

W2 records per-component mode severity internally in `ComponentDamageState`.
The public `ComponentMechanismLoadRow` schema and Python bindings live outside
the W2 write set in `src/runtime/contracts/engagement_contracts.h` and
`src/interfaces/python/bindings_runtime.cpp`. To expose vocabulary entries in
shot-effect rows, W1 or the integration pass needs the minimum public fields:

- `component_failure_primary_mode: string`
- `component_failure_mode_severity: vector/map of mode to severity`

Until that lands, tests assert the mapped modes through existing aircraft damage
entries rather than new row fields.
