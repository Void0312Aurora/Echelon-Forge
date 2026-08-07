# Simulation Conventions

Language:
- English canonical: `foundation/conventions.md`
- Chinese companion: [conventions.zh.md](conventions.zh.md)

Status: `2026-05-18` authoritative for engine-neutral conventions.

This document defines the lowest stable conventions shared across runtime truth
carriers, observation assembly, and numeric interfaces.

It belongs to the standards-tree foundation layer. It does not own:

- service-profile organization
- joint command relationships or ROE semantics
- mission-observation mode taxonomy
- air- or naval-specific execution vocabulary

Those belong in:

- [Service Profile Overview](../../domains/joint/service_profiles/README.md)
- [Joint Command and Modeling Baseline](../../domains/joint/standards/command_and_modeling_baseline.md)
- [Joint Command-Link and Reporting Baseline](../../domains/joint/standards/command_link_and_reporting_baseline.md)
- [Runtime Workflow and Contract Baseline](../bridge/runtime_workflow_and_contract_baseline.md)
- [Air Platform Specialization](../../domains/air/README.md)
- [Naval Specialization](../naval/README.md)

## Coordinate And Unit Conventions

- World frame: `ENU` (East-North-Up).
- Position units: meters.
- Velocity units: meters per second.
- Altitude, range, distance-to-go, cross-track, and offset fields use meters.
- Time values such as `sim_time`, `time_since_update`, and interval fields use
  seconds.

These conventions should remain stable across C++, Python bindings, scenario
loader bridges, and visualization helpers.

## Angle Conventions

- Heading uses NAV degrees: `0 = North`, positive clockwise, wrapped to
  `[0, 360)`.
- Relative azimuth and relative bearing use NAV degrees in `[-180, 180]`,
  positive clockwise.
- Pitch and roll are stored in degrees.
- `TrackData.azimuth` and `RWREvent.bearing` use the same relative-angle sign
  convention.

Reference conversion:

- mathematical angle from `atan2(dy, dx)` uses `0 = East`, counterclockwise
  positive
- `nav_deg = 90 - math_deg`, then wrap to `[0, 360)`

## Truth-Carriers vs Environment Observation

The repository uses more than one observation-like surface. This distinction is
standardized here.

### `AgentObservation` is a truth/status carrier

The C++ `AgentObservation` structure is the low-level state carrier exposed by
the kernel side. It includes:

- own-state kinematics such as `x/y/z`, `vx/vy/vz`, `heading/pitch/roll`, and
  `speed`
- status fields such as `health`, `missiles_remaining`, `can_fire`,
  `gear_state`, `throttle`, and `total_reward`
- contact and warning containers such as `contacts` and `rwr_warnings`

It should be treated as a structured truth/status DTO, not as the final RL
observation schema.

### Environment observations are assembled products

The Python environment assembles observation products into fixed keys such as:

- `instruments`
- `contacts`
- `rwr`
- `mission`
- optional `proprio`

Those products are bridge-level arrays derived from truth, instruments,
mission-command state, and runtime products. They are not identical to the raw
`AgentObservation` layout.

## Sensor And Track Conventions

### `TrackData`

The maintained neutral interpretation is:

- `id`: track identifier
- `range`: meters
- `azimuth`: relative NAV degrees from own nose
- `elevation`: degrees relative to local horizon
- `closing_speed`: meters per second, positive meaning approaching
- `time_since_update`: seconds since track refresh
- `quality`, `confidence`, and `classification_confidence`: normalized scores
  in `[0.0, 1.0]`

The `source`, `classification`, `status`, and `usability` fields are maintained
as small enumerated codes. Their exact doctrinal interpretation belongs in the
domain-specific sensor standards once those stabilize further.

### `RWREvent`

The maintained neutral interpretation is:

- `bearing`: relative NAV degrees
- `signal_strength`: dimensionless signal-intensity value
- `is_lock`: tracking or lock indication
- `is_launch`: launch or guidance indication

These fields are warning semantics, not a full emitter-intelligence ontology.

## Array Assembly Conventions

When the environment assembles array observations, the following neutral rules
apply across maintained code paths.

### Numeric type and shape stability

- assembled numeric observation arrays should be `float32`
- `contacts` is shaped as `[max_contacts, 5]`
- `rwr` is shaped as `[max_rwr, 4]`
- `proprio`, when present, is a flat vector aligned to the environment action
  shape

### Fill, truncation, and sanitization

- contact and RWR arrays are zero-filled when fewer entries are available than
  the configured maxima
- excess entries are truncated at the configured maxima
- non-finite numeric values are sanitized to `0.0`
- assembled instrument vectors are clipped to `[-1e6, 1e6]` before conversion
  to `float32`

These are runtime-stability rules, not domain doctrine.

### Mission observation vectors remain mode-dependent

The `mission` array is a mode-dependent vector product. This file only owns the
fact that:

- it is a fixed-order numeric vector
- its values are assembled through the runtime workflow bridge
- field visibility is mode-dependent rather than free-form

The actual field taxonomy and mode names belong in the maintained air-specific
and runtime-workflow documents.

## Action-Surface Conventions

This document does not redefine the maintained `PilotAction` field list. That
belongs in [air/act.md](../../domains/air/standards/pilot_action_contract.md).

The neutral rules that do belong here are:

- environment-facing action arrays should use stable numeric ordering
- action history reused as `proprio` should preserve that ordering
- validity flags such as `active` gate whether a command or action surface is
  considered live

Detailed takeoff, formation, weapon, or avionics semantics are owned by the
specialized documents, not by this foundation layer.

## Determinism And Workflow Boundaries

- command generation and command delivery are separate concepts
- runtime products should be deterministic functions of prepared inputs at the
  pure-computation layer
- Python-side loading, normalization, and product application are bridge stages,
  not reasons to redefine low-level units or numeric semantics

Those workflow boundaries are documented in more detail in
[Runtime Workflow and Contract Baseline](../bridge/runtime_workflow_and_contract_baseline.md).

## Related Documents

- [Standards Overview](../README.md)
- [Joint Command and Modeling Baseline](../../domains/joint/standards/command_and_modeling_baseline.md)
- [Runtime Workflow and Contract Baseline](../bridge/runtime_workflow_and_contract_baseline.md)
- [Air Platform Specialization](../../domains/air/README.md)
