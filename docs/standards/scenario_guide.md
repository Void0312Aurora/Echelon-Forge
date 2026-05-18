<!-- Machine-translated draft generated on 2026-05-18 from docs/standards/scenario_guide.zh.md. Review before treating this file as authoritative. -->

<!-- Machine-translated draft generated on 2026-05-18 from docs/standards/scenario_guide.md. Review before treating this file as authoritative. -->

# Scenario Configuration Guide

> Standard alignment note (2026-03-23): This document describes the "current repository JSON scenario implementation specification", not the new joint/service profile standard ontology. For the current primary reference on standardized modeling, please first refer to [docs/standards/README.md](README.md).

This project uses a JSON-driven universal training base. All training tasks, environment settings, and reward mechanisms are defined in `.json` files without modifying Python code.

## File Structure Overview

A complete scenario file consists of the following four main sections:

```json
{
  "scenario_name": "Example Scenario",
  "environment": { ... },
  "entities": [ ... ],
  "objectives": [ ... ],
  "rewards": { ... }
}
```

## Relationship with the New Standard System

Under the new `joint/common core + service profile + platform/task specialization` system, this guide's positioning is:

- Explain how current code writes scenario JSONs
- Specify which fields the existing loader/compiler can directly consume

It does not directly define:

- Joint-level command relationships
- Service organization profiles
- Platform-agnostic common core data models

If, following the new standard, subsequent efforts continue, the scenario layer should eventually explicitly carry:

- `service_profile`
- `task_family`
- `tactical_unit_type`
- `task organization metadata`

However, these fields are not currently mandatory in the existing JSON runtime.

---

## 1. Environment

Defines basic parameters of the simulation environment.

- `time_step` (float): Simulation step (seconds). Typically 0.05 or 0.01.
- `max_steps` (int): Maximum number of simulation steps, after which a Truncated trigger occurs.
- `terrain_type` (string): Terrain type (currently supports `"flat"`).

**Example:**
```json
"environment": {
    "time_step": 0.05,
    "max_steps": 2000,
    "terrain_type": "flat"
}
```

---

## 2. Entities

Defines all participants in the scenario (aircraft, ground targets, missiles, etc.).

- `name` (string): Unique identifier for the entity.
- `type` (string): Entity type, must match the database (e.g., `"Aircraft"`, `"Facility"`, `"Missile"`).
- `side` (string): Faction (`"Blue"`, `"Red"`, `"Neutral"`).
- `pos` (list[float]): Initial position [x, y, z] (meters).
- `vel` (list[float]): Initial velocity [vx, vy, vz] (meters/second).
- `heading` (float): Initial heading (degrees).
- `is_agent` (bool): **Key field**. Entities set to `true` will be controlled by the RL algorithm. Currently only one agent is supported.

**Example:**
```json
"entities": [
    {
        "name": "Blue_F16",
        "type": "Aircraft",
        "side": "Blue",
        "pos": [0.0, 0.0, 500.0],
        "vel": [200.0, 0.0, 0.0],
        "heading": 0.0,
        "is_agent": true
    },
    {
        "name": "Target_Bunker",
        "type": "Facility",
        "side": "Red",
        "pos": [5000.0, 5000.0, 0.0],
        "vel": [0.0, 0.0, 0.0],
        "heading": 0.0
    }
]
```

---

## 3. Objectives

Define criteria for mission success. Multiple objective types are supported.

### Type A: Conditional

Used for state-based tasks (e.g., takeoff, cruise, maintain speed).

- `type`: Fixed to `"conditional"`.
- `reward`: One-time reward upon achieving the goal.
- `conditions`: List of conditions; all must be satisfied simultaneously for success.
    - `property`: Property name. Common flight-task items include
      `"altitude"`, `"altitude_agl"`, `"speed"`, `"gear"`, `"heading"`,
      `"heading_error_deg"`, `"ground_track_error_deg"`, `"runway_cross_abs_m"`,
      `"on_runway_geom"`, `"on_runway"`, `"on_ground"`,
      `"sink_rate_abs_mps"`, `"vertical_speed_abs_mps"`,
      `"ils_localizer_abs"`, `"ils_glideslope_abs"`, `"dme_m"`.
    - `op`: Comparison operator (`">="`, `">"`, `"<="`, `"<"`, `"=="`).
    - `value`: Target value.

**Example: Takeoff task (altitude > 300 and speed > 150)**
```json
{
    "type": "conditional",
    "conditions": [
        {"property": "altitude", "op": ">=", "value": 300.0},
        {"property": "speed",    "op": ">=", "value": 150.0}
    ],
    "reward": 2000.0
}
```

### Type B: Capture Zone

Used for location-based tasks (e.g., reach a designated airspace, strike a target).

- `type`: Fixed to `"capture_zone"`.
- `target`: The `name` of the target entity.
- `radius`: Judgment radius (meters).
- `duration`: Time required to stay in the zone (seconds).
- `reward`: Success reward.

**Example: Approach within 2 km of target and maintain for 10 seconds**
```json
{
    "type": "capture_zone",
    "target": "Target_Bunker",
    "radius": 2000.0,
    "duration": 10.0,
    "reward": 1000.0
}
```

---

## 4. Rewards

Defines dense rewards (shaping rewards) and penalties during training.

- `survival` (float): Reward per time step survived (encourages survival).
- `crash_penalty` (float): Penalty for crashing or dying (typically a large negative number).
- `distance_to_target` (object): Distance-guided reward configuration.
    - `weight`: Weight coefficient for distance (usually negative, meaning closer distance yields larger reward / smaller penalty).

**Example:**
```json
"rewards": {
    "survival": 0.01,
    "crash_penalty": -1000.0,
    "distance_to_target": {
        "weight": -0.001
    }
}
```
