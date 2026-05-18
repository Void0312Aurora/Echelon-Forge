<!-- Machine-translated draft generated on 2026-05-18 from docs/task/air_combat/air_combat_scenario_level_ammo_design_20260516.zh.md. Review before treating this file as authoritative. -->

# Air Combat Scenario-Level Ammo Design and Implementation

Status: `2026-05-16` Implemented and validated.

Related documents:

- [Air Combat 1v1 Freeze Plan](air_combat_1v1_freeze_plan_20260516.md)
- [Air Combat 1v1 Weapon Chain Progress](air_combat_1v1_weapon_chain_progress_20260516.md)
- [Air Combat 1v1 Weapon Chain Regression Test](../../../tests/runtime/test_air_combat_1v1_fire_missile.py)

## 1. Problem Background

In the current repository, the real runtime source of `Ammo` mainly came from:

1. Unit database definition;
2. The platform default chain `UnitDefinition -> DefaultUnitFactory -> Ammo`;
3. `fire_missile()` / `missiles_remaining` / `can_fire` also directly read the `Ammo` component on the entity.

This led to a practical issue:

1. By design, mission-level ammunition configuration is better placed at the scenario layer;
2. But implementation-wise, scenario `entities[]` could not reliably override entity `Ammo` before;
3. Consequently, `1v1`/`2v2` mission contracts were bound by platform defaults instead of being explicitly controlled by scenarios.

## 2. Design of This Freeze

This freeze consolidates "platform default ammo" and "scenario-level ammo override" into the following maintainable semantics:

1. The platform database still provides default `Ammo` / `WeaponCooldown`.
2. The scenario layer can explicitly write `ammo` and `weapon_cooldown` in `entities[]`.
3. If the scenario does not write them, the platform default values remain unchanged.
4. If the scenario explicitly writes them, the scenario override takes precedence over the platform defaults.

Recommended scenario fields:

```json
{
  "name": "Blue_Fighter",
  "type": "F-16C_Block50",
  "side": "Blue",
  "is_agent": true,
  "pos": [0.0, 0.0, 1200.0],
  "vel": [0.0, 180.0, 0.0],
  "heading": 0.0,
  "ammo": {
    "missiles_remaining": 2,
    "max_missiles": 6
  },
  "weapon_cooldown": {
    "cooldown_s": 0.75,
    "last_fire_time": -1.0
  }
}
```

## 3. Currently Supported Field Scope

This freeze only connects the following minimal maintainable fields:

1. `ammo.missiles_remaining`
2. `ammo.max_missiles`
3. `weapon_cooldown.cooldown_s`
4. `weapon_cooldown.last_fire_time`

The following are still out of scope for this round:

1. Position-level / type-level detailed weapon inventory;
2. Automatic mapping from `default_loadout` to runtime ammo;
3. `weapon_select_id` binding to specific munition types;
4. Automatically generating runtime generic ammunition after the scenario layer declares the actual payload per hardpoint.

## 4. Implementation Path

This round establishes two maintenance paths:

1. Single world:
   - `ScenarioLoader`
   - `apply_world_layout_to_kernel(...)`
   - `SimulationKernel.set_unit_ammo(...)`
   - `SimulationKernel.set_weapon_cooldown(...)`
2. Batch world:
   - `CompiledWorldLayoutTemplate`
   - `WorldSpawnRequest`
   - `WorldBatchRuntime.spawn_units_batch(...)`
   - `WorldBatchRuntime.apply_world_setup_batch(...)`

This means:

1. The same scenario definition has consistent ammo override semantics under both single world and batch world.
2. Later `execution` / `world_batch_vec_env` / `cooperative_world_batch_vec_env` can all reuse the same scenario-level configuration surface.

## 5. Direct Significance for 1v1

After this implementation, the `1v1` effort can proceed more naturally:

1. `F-16C_Block50` can remain as the platform real airframe;
2. Ammo can be explicitly supplemented via the scenario layer instead of falling back to the generic `Aircraft` for the ammunition chain;
3. Subsequent `1v1` and `2v2` mission contracts can also more clearly specify "initial ammunition for each side in this mission."

## 6. Verification

This round has verified:

1. Scenario-level `ammo` override takes effect on the `ScenarioLoader` path;
2. The same scenario also takes effect on the compiled + batch runtime path;
3. The overridden `missiles_remaining` can be stably read from the observation surface.

Focus commands:

```bash
source tools/maintenance/cmo_env.sh
cmo_python -m pytest -q tests/runtime/test_air_combat_1v1_fire_missile.py
cmo_python -m pytest -q tests/world_batch/test_world_batch_runtime.py -k 'load_compiled_scenario_batch or scenario_loader_and_batch_runtime_share_setup_semantics'
```

Current results:

```text
4 passed
3 passed, 15 deselected
```

## 7. Suggested Next Steps

With this design already implemented, the most natural next steps are:

1. Switch the `1v1` fixture from generic `Aircraft` to `F-16C_Block50`;
2. Explicitly declare both sides' `ammo` via the scenario layer;
3. Continue freezing the termination / reward contracts for `1v1`.
