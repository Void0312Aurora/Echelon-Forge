<!-- Machine-translated draft generated on 2026-05-18 from docs/task/air_combat/air_combat_1v1_entry_analysis_20260516.zh.md. Review before treating this file as authoritative. -->

# Air Combat 1v1 Entry Analysis

Status: `2026-05-16` Task Analysis Version.

Related Documents:

- [P8 Cooperative Execution Pipeline Discovery and Plan](../../plan/cooperative/p8_cooperative_execution_pipeline_findings_and_plan.zh.md)
- [Multi-Agent Cooperative Training Base and Performance Plan](../../plan/cooperative/multi_agent_cooperative_training_foundation_and_performance_plan.zh.md)
- [HMoE Strict Terminal Eval (2026-05-15)](../../plan/results/hmoe_strict_terminal_eval_20260515.md)
- [Reinforcement Learning and Self-Play Outlook](../../forward/rl_selfplay.md)

Document Positioning:

- This document is used to confirm the actual entry point for current repository into `1v1` air combat work.
- The goal is not to directly authorize implementation, but first to clearly explain “which stable mainline should we stand on to enter combat”.
- This document focuses on the currently maintained training entry, runtime environment, observation/action contract, and evaluation capabilities, and does not restate the full design of cooperative execution.

## 1. Current Trusted Premises

As of `2026-05-16`, the trusted premises that can serve as a `1v1` starting point are:

1. `execution` single aircraft execution training mainline remains the most mature, stable, and comprehensive execution entry.
2. `cooperative_execution` has proven in the recent HMoE and strict terminal eval that the training chain of “multiple controllable entities sharing world-step / reset in the same world” is usable, but it currently serves same-team cooperation, not adversarial confrontation.
3. The existing evaluation entry [tools/eval/eval_sb3.py](../../../tools/eval/eval_sb3.py) only maintains `single` and `cooperative` modes, without a `versus` / `combat_1v1` mode.
4. The old [Reinforcement Learning and Self-Play Outlook](../../forward/rl_selfplay.md) remains at the outlook level; the files `examples/training/train_self_play.py` and `examples/training/selfplay_config.json` mentioned in the text do not exist in the current repository and cannot be regarded as ready mainline entries.
5. The current `ScenarioCompiler` / `ScenarioLoader` maintained mainline only compiles `objectives` where `type = "conditional"` into the runtime; do not directly treat the `capture_zone` explanation from old documents as available mainline capability for `1v1`.

## 2. Current Status Directly Related to 1v1

### 2.1 Training Entry Status

[train.py](../../../train.py) currently accepts only three types of `agent_layer`:

- `execution`
- `leader`
- `cooperative_execution`

Where:

- `execution` uses [UniversalEnv](../../../gym_envs/universal_env.py) or [WorldBatchVecEnv](../../../python/rl/runtime/world_batch_vec_env.py), essentially “one active `agent_id` per world”.
- `cooperative_execution` uses [CooperativeWorldBatchVecEnv](../../../python/rl/runtime/cooperative_world_batch_vec_env.py), essentially “multiple same-team controllable roster members in the same world expanded into flat slots, sharing the same world step / reset”.

There are currently no maintained training entries such as:

- `combat_execution`
- `versus_execution`
- `selfplay_execution`

### 2.2 Runtime Environment Status

[WorldBatchVecEnv](../../../python/rl/runtime/world_batch_vec_env.py) still has single active agent semantics:

- Each world maintains only one `handle.agent_id`
- Observation reading, action issuing, and mission/tasking synchronization are organized around this single entity

[CooperativeWorldBatchVecEnv](../../../python/rl/runtime/cooperative_world_batch_vec_env.py) already has:

- active controllable roster
- `world_index + entity_id` granularity slot expansion
- `policy_route` / role / formation metadata
- multiple entities in the same world sharing step/reset

But its world-level director, success semantics, and slot flattening method are currently built around “same-team cooperation to complete a common objective”, not adversarial confrontation.

### 2.3 Scenario / Roster Status

[python/scenario_runtime.py](../../../python/scenario_runtime.py) already supports:

- Declaring multiple entities in the same world
- Parsing `active_controllable_roster` / `cooperative_roster`
- Preserving metadata such as `team_id`, `element_id`, `role_code`, `policy_route`, `reference_entity_id` for roster members

This means:

- The current base can already express “there are two or more controllable aircraft in the same world”.
- But the currently maintained roster semantics are closer to “same-team cooperative control plane” rather than “blue vs red adversarial control plane”.

### 2.4 Observation and Action Status

The `full` action mode of [UniversalEnv](../../../gym_envs/universal_env.py) already contains basic control semantics valuable for air combat:

- Flight controls
- Radar switch and scan
- `master_arm`
- `fire_weapon`
- `fire_gun`
- `weapon_select_id`

Current observations already include:

- `instruments`
- `contacts`
- `rwr`
- `mission`

Among them, `instruments` already has `missiles_remaining`, and `contacts` / `rwr` already have basic adversarial perception semantics.

But one current constraint needs to be clarified:

- `PilotAction.master_arm / fire_weapon / fire_gun / weapon_select_id` are already exposed in the action interface;
- The current weapon mainline does not directly trigger missile launches from these `PilotAction` fields;
- The actually usable launch entry in the repository is still the underlying [SimulationKernel.fire_missile(...)](../../../src/interfaces/python/bindings_core.cpp) API.
- Support for runtime ammo also varies across different platforms in the database; for example, `F-16C_Block50` currently still has `has_ammo: false`, while `Su-35S_Flanker-E` already has observable ammo/runtime fire state.

This shows that:

- The action/perception foundation for `1v1` is not from scratch.
- The real gap is not “whether weapon fields exist”, but “how to organize adversarial objectives, launch main chain, termination conditions, rewards, scenario constraints, and evaluation metrics into a maintained training mainline”.

### 2.5 Task / Mission Semantics Status

The current maintained mission observation taxonomy still focuses on:

- `basic`
- `nav_v1`
- `nav_v2`
- `nav_v2_formation_v1`
- `nav_v2_formation_role_v1`
- `nav_v2_cooperative_takeoff_v1`

This indicates that the current mission blocks are still biased toward:

- Waypoint following
- Formation
- Cooperative takeoff / cruise

Rather than:

- Air combat engagement phases
- Offensive/defensive postures
- Adversarial engagement rules

Therefore, for `1v1` to follow the maintained mainline, at least one new adversarial task semantics block needs to be added; it is not acceptable to directly force the `nav_v2_*` observation mode into a dogfight and pretend it works.

### 2.6 Evaluation Status

[tools/eval/eval_sb3.py](../../../tools/eval/eval_sb3.py) currently only supports:

- `single`
- `cooperative`

It does not yet have:

- Win/loss statistics for both sides
- Blue/Red survival
- Engagement duration
- Disengagement
- Hit / kill chain results

These are the most basic evaluation metrics for `1v1`.

Therefore, `1v1` cannot only supplement the training entry without supplementing the evaluation metrics.

## 3. Why Not Enter 1v1 Directly from cooperative_execution

`cooperative_execution` has indeed been the most active new line recently, but it is not suitable as the direct carrier for the `1v1` first cut, for the following reasons:

1. Its current success semantics are “multiple friendlies in the same world completing a common task”, not “one side wins under adversarial confrontation”.
2. Its current director/roster design defaults to maintaining a set of cooperative intents, while the first phase of `1v1` needs to first stabilize the “single fighter vs single enemy execution loop”.
3. Starting directly with `cooperative_execution` would amplify the problem to include all of:
   - Multiple controllable roster
   - Adversarial modeling for both sides
   - Multi-policy or self-play routing
   - New evaluation metrics
   - New reward/termination contracts
4. The current value of `cooperative_execution` is more suitable for reuse in `2v2`, because `2v2` naturally requires a two-layer semantics of “same-team cooperation + enemy confrontation”.

Conclusion:

- `cooperative_execution` is not irrelevant, but is more suitable as the direct base for the `2v2` phase.
- The first phase of `1v1` should instead reuse the stable `execution` mainline and independently build the adversarial task loop.

## 4. Recommended Entry Points

### 4.1 First Phase: Extend `1v1` Adversarial Tasks Based on `execution` Mainline

Recommended to advance on the `execution` mainline for the first phase, for these reasons:

1. The training entry is the most stable.
2. The reward / done / info / eval contract for a single active agent is already mature.
3. The current actions/observations already have basic air combat control semantics.
4. Variables can be controlled to the minimum set of “single learning agent + single enemy script/frozen opponent”.

The corresponding implications are:

- In the first phase, do not rush into true bilateral simultaneous learning.
- First, make the `1v1` scenario, reward, termination, evaluation, logging, and configuration entry a maintained mainline.
- The opponent should first use a script or a frozen policy body, rather than starting with self-play.

### 4.2 Second Phase: Introduce Frozen Opponent / Policy Pool on `1v1` Mainline

Once the `1v1` task loop in the first phase is stable, add:

- Frozen checkpoint as opponent
- Simple opponent pool
- Adversarial evaluation script

This phase can still maintain:

- Only one `execution` policy on the learning side
- Opponent side not entering the same PPO update loop

### 4.3 Third Phase: Then Consider Self-Play or Bilateral Adversarial Training

Only enter self-play when the following capabilities are stable:

1. `1v1` adversarial reward / termination / eval metrics are stable
2. Script/frozen opponent baselines are reproducible
3. Training and evaluation entries can stably record win rate, duration, end-game reason

Otherwise, directly entering self-play can easily mix “unstable task contract” with “unstable policy learning”.

## 5. Implications for Subsequent 2v2

If `1v1` progresses along the above path, the handover for subsequent `2v2` will be clearer:

1. `1v1` phase accumulates:
   - Adversarial scenario contract
   - Reward / termination contract
   - Adversarial eval metrics
   - Script / frozen opponent mechanism
2. `2v2` phase reuses:
   - Cooperative roster / slot expansion
   - `policy_route`
   - Multi-entity step/reset in same world
   - World-level coordination director

In other words:

- `1v1` first solves “what is the adversarial task”.
- `2v2` then solves “how to do same-team cooperation under the adversarial task”.

## 6. Recommended Task Boundary

The most reasonable task boundary currently should be frozen as:

1. First do `1v1`, do not directly merge into `2v2`.
2. First do “single learning agent vs script/frozen opponent”, do not directly enter bilateral self-play.
3. First extend adversarial tasks based on the `execution` mainline, do not directly modify `cooperative_execution` into the adversarial main entry.
4. First supplement the four items: training, scenario, reward/termination, evaluation; then talk about HMoE, dual policy routing, or historical policy pool.

## 7. Conclusion

The current repository already has many infrastructure pieces for entering `1v1`, but the truly reliable entry point is not “directly start self-play” nor “reverse cooperative as an adversarial environment”.

The safer path, more consistent with the current project evolution state, is:

1. Use `execution` as the training mainline for the first phase;
2. Create new `1v1` air combat scenario / reward / termination / eval contract;
3. First use scripts or frozen opponents to stabilize the minimal adversarial loop;
4. Then in the second phase, enter stronger frozen-opponent / policy-pool;
5. Finally, bring in true self-play and `2v2` cooperative adversarial combat.
