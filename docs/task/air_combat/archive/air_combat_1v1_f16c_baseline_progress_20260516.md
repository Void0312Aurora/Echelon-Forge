<!-- Machine-translated draft generated on 2026-05-18 from docs/task/air_combat/air_combat_1v1_f16c_baseline_progress_20260516.zh.md. Review before treating this file as authoritative. -->

# Air Combat 1v1 F-16C Baseline Switch and Minimal Engagement Contract Progress

Status: `2026-05-16` Current round has landed.

Related Documents:

- [Air Combat 1v1 Freeze Plan](air_combat_1v1_freeze_plan_20260516.md)
- [Air Combat Scene-Level Ammo Design and Implementation](air_combat_scenario_level_ammo_design_20260516.md)
- [Air Combat 1v1 Weapon Chain Progress](air_combat_1v1_weapon_chain_progress_20260516.md)

## 1. What Was Completed This Round

This round formally switched the canonical `1v1` baseline from the generic `Aircraft` to a symmetric `F-16C_Block50 vs F-16C_Block50`.

Currently maintained scenario:

- [air_combat_1v1_headon_sensor_smoke_v1.json](../../../../scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json)

The switch was not made by modifying the platform database default `has_ammo`, but continued using the scene-level override semantics established in the previous round:

1. The platform retains the real aircraft type `F-16C_Block50`;
2. The scene layer explicitly declares `ammo` and `weapon_cooldown` for both sides;
3. Therefore, the baseline training agent can finally return to the real platform, rather than reverting to a generic shell.

## 2. Minimal Engagement Contract Added This Round

This round did not complete the entire `1v1` training system at once, but filled two connection points that truly advance the main line:

1. `mission_command.assigned_target_name / assigned_target_id` will be parsed as the primary target when loaded by the `ScenarioLoader`;
2. The objective input surface of the `execution` main line can now recognize:
   - `target_active`
   - `target_health`
   - `self_active`
   - `self_health`
   - `missiles_remaining`
   - `target_range_m`

Therefore, the current `1v1` scenario can now directly express, using a maintenance `conditional objective`:

1. "The primary target has been destroyed";
2. And map it to a minimal victory termination.

This round also simultaneously added minimal execution termination coverage:

1. `combat_win`
2. `combat_loss`
3. `combat_draw`
4. `combat_timeout`

This is still the first-phase semantics and does not imply the complete adversarial scoring system is finished.

## 3. Firing Bridge Newly Connected This Round

Just switching the scenario is not enough, because the existing `UniversalEnv`'s `fire_weapon` previously did not reach the maintenance `fire_missile()`.

The minimal bridge added this round is:

1. `PilotAction.master_arm && fire_weapon`
2. Prioritize reading `MissionCommand.assigned_target_id`
3. If there is a valid enemy track currently, call `SimulationKernel.fire_missile(attacker_id, target_id)`

This means:

1. The `1v1` baseline scenario no longer relies solely on manually calling `fire_missile()` in tests;
2. The full action surface of `UniversalEnv` finally has a minimally usable missile launch entry point;
3. However, it is still not a complete weapon management system; `weapon_select_id`, weapon type selection, and pylon semantics are not yet connected.

## 4. Parts Clearly Still Incomplete After This Round

After this round, `1v1` has advanced compared to before, but it has not yet reached the completion state where "formal large-scale training can begin".

Key items still not completed:

1. Although the red side can now connect to scripted opponents, it is currently only a minimal baseline, not a strong tactical agent;
2. The `fire_weapon` bridge is currently only a minimal maintenance glue, not a complete weapon system;
3. The `1v1` reward still lacks finer engagement shaping, such as distance, positioning, energy, and resource consumption;
4. The `1v1` evaluation JSON and dedicated eval entry have not yet been frozen;
5. `2v2` should still not be directly entered in this round.

## 5. Scripted Opponent Connection Status

The current canonical `1v1` scenario already supports declaring a red-side scripted opponent at the entity level:

1. `entities[].scripted_agent`
2. The current maintenance implementation is bound to [examples/agents/red_agent.py](../../../../examples/agents/red_agent.py)
3. It is driven by `ScenarioLoader.update_behaviors()` at runtime, therefore:
   - `UniversalEnv`
   - Default `WorldBatchVecEnv`
   - Loader/runtime focused tests
   These maintenance paths will automatically execute the red side script logic.

Current script capability boundaries:

1. It performs minimal intercept/offset/defensive turns based on enemy geometry;
2. When a hostile track exists and is within firing range, it will attempt to launch a missile;
3. The goal is to provide a stable, reproducible first version red-side baseline, not to simulate complete BVR/ACM tactics.

Current known limitations:

1. This scripted opponent relies on the Python behavior update chain;
2. Therefore, it does not cover the specialized path `WorldBatchVecEnv(execution_episode_controller_mainline=True)` that deliberately skips Python behavior updates;
3. If self-play / full compiled mainline is to use the opponent script later, the opponent control needs to be further lowered to the runtime/controller layer.

## 6. Most Natural Next Steps After This Round

After this round, the next steps are very clear:

1. First freeze the `1v1` termination and reward contract;
2. Clarify the reward criteria for Blue win / Blue loss / Double death / Timeout / Ammo depletion without resolution;
3. Then add a minimal red-side script or freeze a standard opponent;
4. Finally, enter the actual `1v1` rollout training and eval entry.

It is recommended to maintain:

1. Training baseline uses `F-16C_Block50 vs F-16C_Block50` first;
2. `F-16C vs Su-35` reserved for subsequent evaluation or stress testing, not as the first training baseline.
