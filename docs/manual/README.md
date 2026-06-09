# Manual

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

### Archive

Outdated historical design notes.

| Document | Description |
|----------|-------------|
| [Takeoff to Cruise Mixed Mode](archive/takeoff_to_cruise_mixedmode_notes.md) | Historical P3 experiment baseline, references 20260316 experiment artifacts |

Landing task design moved to [docs/task/flight_dynamics/landing_task_notes.md](../task/flight_dynamics/landing_task_notes.md).

---

Maintenance rules: reference docs should be updated alongside code changes. How-to docs should be updated when tooling changes. Historical design notes move to `archive/` once the implementation lands.
