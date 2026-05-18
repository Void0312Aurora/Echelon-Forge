# Standards Docs vs Code Review

## conventions.md

### Verified
- ENU world frame, NAV heading conventions, relative azimuth, Transform angles, Detection.bearing, TrackData.azimuth, Sensor.fov_deg, AgentObservation units, simulation time — all verified against `src/components/basic/common.h`, `src/components/systems/sensor.h`, `src/core/interfaces/observation.h`.

### Mismatches
- **Claim**: "get_all_units().heading is derived from velocity and returned as NAV degrees"
  **Reality**: Heading is copied directly from `Transform.heading` component (factory-time computation, not query-time derivation from velocity).
  Severity: P2

- **Claim**: "NAV deg = 90 - math deg, wrapped to [0, 360)"
  **Reality**: Formula approximately correct but incomplete for negative math angles. Actual conversion uses `to_radians(90.0 - heading_deg)` plus `normalize_heading_deg`. Severity: P3

---

## scenario_guide.md

### Verified
- JSON top-level keys (`meta`, `environment`, `entities`, `objectives`, `rewards`) match actual scenario files.

### Mismatches
- **Claim**: Top-level key is `scenario_name`
  **Reality**: Actual key is `meta` (containing `max_steps`, not a name string). Severity: P1

- **Claim**: `max_steps` inside `environment`
  **Reality**: `max_steps` is inside `meta`, not `environment`. Severity: P1

- **Claim**: `terrain_type` field supported with value `flat`
  **Reality**: No `terrain_type` key exists. Terrain uses `zones` with surface types like `HardPacked`. Severity: P1

---

## modularization_plan.md

### Verified
- Core module ownership, component data definitions, system dependencies, Python bindings dependency on core, `IUnitFactory`/`IEffectsModel`/`ISensorModel` interfaces — all verified.

### Mismatches
- **Claim**: "`content/` depends on: none (data only)"
  **Reality**: `content/unit_definition.h` includes from `components/basic/common.h`, `components/combat/health.h`, `components/command/command_link.h`, `components/physics/performance.h`, `components/systems/sensor.h`, etc. Hard include dependency on components. Also contains inline logic. Severity: P1

- **Claim**: Module map lists 7 top-level modules
  **Reality**: Missing `src/core/interfaces/` (C++ abstract interfaces like `IUnitFactory`, `ISensorModel`) — distinct from `src/interfaces/python/` (Python bindings). Severity: P2

- **Claim**: "One-way dependencies: core → systems → interfaces (no back edges)"
  **Reality**: CMake builds everything as single `ef_core` target. No per-module library boundaries enforced. Severity: P2

- **Claim**: "`components/` purpose: pure data components (no logic)"
  **Reality**: `src/components/systems/track_management.h` contains ~260 lines including decision functions (`track_has_recent_local_support`, `resolved_track_source`, etc.). Severity: P2

---

## air/act.md (Pilot Action Space)

### Verified
- All primary/secondary/sensor/weapon controls present in `PilotAction` struct. Continuous action requirement met.

### Mismatches (P0)
- **Claim**: "stick_pitch: Pulling back is **negative** (pitch up)"
  **Reality**: `PilotAction.stick_pitch` comment says `"positive = nose up"`. Code at `default_control_model.cpp` line 296: `q_cmd = stick_pitch_f * kQMaxRadS` — positive stick_pitch produces positive pitch rate (nose up). **SIGN IS INVERTED**: doc says NEGATIVE = nose up, code says POSITIVE = nose up.
  **Severity: P0** — a model trained with the doc convention will behave inverted.

- **Claim**: `jettison_btn` under weapon management
  **Reality**: Present as `jettison_emergency` in `PilotAction`. Naming differs. Severity: P3

---

## air/obs.md (Pilot Observation Space)

### Verified
- Flight dynamics variables (`heading`, `pitch`, `roll`, `speed`) present in `AgentObservation`.

### Mismatches (P1)
- **Claim**: 20+ detailed observation variables (`alt_baro`, `alt_radar`, `ias`, `mach`, `vvi`, `aoa`, `beta`, `g_load`, `p/q/r`, `engine_rpm_pct`, `fuel_internal`, `throttle_pos`, `rwr_state`, `radar_contacts`, `missile_count`, target variables)
  **Reality**: `AgentObservation` struct contains only: `x, y, z, vx, vy, vz, heading, pitch, roll, speed, health, gear_state, throttle, missiles_remaining`. The documented variables do NOT exist in the agent observation. Some exist in `InstrumentState` (separate component, not exposed to agent).
  **Severity: P1**

---

## air/aim.md (Mission Command Standard)

### Verified
- Command fields (`cmd_heading_deg`, `cmd_altitude_m`, `cmd_speed_mps`), command codes (0-4), formation offsets, tactical target ID — all verified in `MissionCommandCore`/`MissionCommandAir`.

### Mismatches
- **Claim**: `cmd_vvi` (target vertical speed) field
  **Reality**: Does not exist anywhere in codebase. Severity: P2

- **Claim**: `tac_jettison` field
  **Reality**: Does not exist in mission command layer. Only `jettison_emergency` in `PilotAction`. Severity: P2

- **Claim**: `form_pos_id` field
  **Reality**: Code has `formation_id`. Naming differs. Severity: P3

---

## air/rep.md (Pilot Reporting)

### Verified
- All acknowledgment, status, tactical brevity, mission progress, and emergency codes present in `CommMsgType` enum.

### Mismatches (P2)
- **Claim**: Structured report data fields (`status_fuel.{Joker, Bingo, State}`, `status_ammo`, `status_pos`)
  **Reality**: `PilotReportCore` has only generic `status_value` (double) and `entity_ref` (uint64_t). Report semantics exist as message TYPE labels only, not as structured data fields.

---

## Services Documents (air_force.md, army.md, navy.md)

### Verified
All service hierarchy descriptions, layer separation, and joint-vs-service-specific fields accurately match code. No mismatches found.

---

## joint/command_and_modeling_baseline.md

### Verified
All `CommandRelationship` enums, `TacticalUnitType` enums, `TaskOrderCore` fields, and separation of core vs air-specific fields verified. No mismatches.

---

## naval/ship_unit_references.md

### Verified
All DDG-51 and T-AKE-1 dimensions, displacements, HP values, and sensor specifications match corresponding JSON files. No mismatches.

---

## naval/minimal_task_structure.md + README.md

### Verified
Task shapes, semantic mappings, and naval-vocabulary separation verified. No mismatches.

---

## Summary

| Severity | Count | Key Items |
|----------|-------|-----------|
| P0 | 1 | **`stick_pitch` sign inverted** in `air/act.md` vs `pilot_action.h` |
| P1 | 5 | `scenario_guide.md` JSON schema wrong (3 items); `obs.md` over-describes observation space; `content/` dependency claim violated |
| P2 | 7 | Heading derivation claim; missing `cmd_vvi`/`tac_jettison` fields; `core/interfaces` omitted from module map; build not enforcing boundaries; components contain logic; report struct fields missing |
| P3 | 4 | NAV formula imprecision; jettison naming; form_pos_id naming; future fields understated |
