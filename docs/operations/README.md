# Operations Documentation

Language: English canonical; [Chinese companion](README.zh.md).

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/operations/README.md`
Owner: `operations documentation`
Last verified: `2026-08-06`

Reference documentation and how-to guides for developers and users, organized by category.

## Directory

### Reference ("What is")

Current-state descriptions of system capabilities, code structure, and physics implementation.

| Document | Description |
|----------|-------------|
| [Engine Capabilities](reference/engine_capabilities.md) | Current engine capabilities, key limitations, RL interface |
| [Source Layer Map](reference/src_layer_map.md) | Navigation entry from `src/` → `python/` → `gym_envs/` → `tests/` → `tools/` with recommended reading order |
| [Physics Engine Inventory](reference/physics_engine_inventory.md) | Code entry points for ECS pipeline, motion integration, control models, environment models, data sources |

### How-To ("How to do X")

| Document | Description |
|----------|-------------|
| [Remote Visualization](howto/visualization_guide.md) | SSH port forwarding + Web real-time simulation view |

### Legacy Archive

Outdated historical design notes.

| Document | Description |
|----------|-------------|
| [Takeoff to Cruise Mixed Mode](../manual/archive/takeoff_to_cruise_mixedmode_notes.md) | Frozen historical P3 experiment baseline; archive sources are not part of the maintained migration |

Landing task design remains at [docs/task/flight_dynamics/landing_task_notes.md](../task/flight_dynamics/landing_task_notes.md) until the Air owner migration.

---

Maintenance rules: reference docs follow code changes and how-to docs follow
workflow or tooling changes. Completed operational work is promoted to a
maintained reference or closed through the owning area's archive route.
