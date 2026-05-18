<!-- Machine-translated draft generated on 2026-05-18 from docs/task/air_combat/air_combat_1v1_freeze_plan_20260516.zh.md. Review before treating this file as authoritative. -->

# Air Combat 1v1 Freeze Plan

Status: `2026-05-16` Freeze execution version.

Related documents:

- [Air Combat 1v1 Entry Analysis](air_combat_1v1_entry_analysis_20260516.md)
- [P8 Collaborative Execution Pipeline Discovery and Plan](../../../plan/cooperative/p8_cooperative_execution_pipeline_findings_and_plan.zh.md)
- [Multi-Agent Collaborative Training Base and Performance Plan](../../../plan/cooperative/multi_agent_cooperative_training_foundation_and_performance_plan.zh.md)
- [HMoE Strict Terminal Eval (2026-05-15)](../../../plan/results/hmoe_strict_terminal_eval_20260515.md)

Document positioning:

- This document converges "entering air combat `1v1`" into an executable task list.
- This round only freezes the first phase of `1v1`, and does not package `2v2`, self-play, and multi-policy confrontation together.
- This document does not authorize "rewriting the cooperative mainline on the fly", nor does it authorize direct divergence into a complete adversarial training platform.

Verification method:

```bash
source tools/maintenance/cmo_env.sh
cmo_env_summary
```

If this round touches the Python / training / runtime / eval mainline, at least supplement:

```bash
source tools/maintenance/cmo_env.sh
cmo_python -m pytest -q
```

If this round touches `ef_py`, ScenarioLoader, or air combat termination/reward base, at least supplement:

```bash
cmake -S . -B build-workshop -DCMAKE_BUILD_TYPE=Release
cmake --build build-workshop --target ef_core ef_py -j4
```

## I. Objective

The goal of this round is not to "immediately build a complete self-play system", but to establish the minimum maintainable mainline for air combat `1v1`.

Core issues to be resolved in this round:

1. Establish a clear training mainline entry for `1v1`.
2. Establish maintainable scenario, reward, termination, and evaluation contracts for `1v1`.
3. Enable the minimum baseline of `1v1` to run "single learner vs single script/frozen opponent".
4. Leave clean interfaces for subsequent `2v2` and self-play, but do not implement them in this round.

## II. Freeze Scope

This document only freezes five work packages:

1. `WP1`: `1v1` task contract and scenario baseline
2. `WP2`: Integration of `1v1` training entry into the `execution` mainline
3. `WP3`: `1v1` evaluation and result metrics
4. `WP4`: Script/frozen opponent baseline
5. `WP5`: Interfaces reserved but not implemented for subsequent `2v2` / self-play

This document explicitly does NOT cover:

1. `2v2` cooperative-vs-cooperative adversarial training
2. True bilateral simultaneously-updated self-play PPO loop
3. Historical policy pool, Elo, league training
4. Direct experiments of HMoE on the adversarial pipeline
5. Multi-policy route adversarial training loop

## III. Overall Strategy

The execution order is fixed:

1. First establish the `1v1` task contract.
2. Then make the `execution` mainline able to run this task.
3. Then supplement `1v1` evaluation and result metrics.
4. Then integrate script/frozen opponents.
5. Finally, only reserve extension slots for `2v2` / self-play, without entering them in this round.

Rationale:

1. The current biggest gap is not that the "reasoning framework is not complex enough", but that the adversarial task contract lacks a maintainable definition.
2. Without clear reward / termination / eval, directly jumping to self-play will mix up the issues.
3. The `execution` mainline is already mature and is the most suitable carrier for the first phase.

## IV. Work Packages

### WP1: `1v1` Task Contract and Scenario Baseline

Objectives:

- Establish a minimal maintainable task contract for air combat `1v1`.
- Clarify the scenario boundaries, friendly/enemy sides, success/failure conditions, and reward objectives for the first phase.

Freeze scope:

- Add or organize `1v1` air combat scenarios under `scenarios/`.
- Necessary `ScenarioLoader` / reward / termination contract configuration.
- Related documentation and minimal contract tests.

Issues that must be clarified in this phase:

1. Who is the blue learner.
2. Who is the red opponent.
3. How win/loss conditions are defined.
4. How disengagement / timeout / ammunition exhaustion / both sides surviving final states are defined.
5. Whether the first phase allows using navigation-style mission blocks or requires new combat mission blocks.

Recommended freeze direction:

1. The first phase supports only "single learner vs single script/frozen opponent".
2. The first phase does not require the mission observation to introduce complex adversarial-specific large vectors at once.
3. Prioritize reuse of existing `instruments / contacts / rwr / mission` structures, only make minimal necessary extensions to mission task semantics.
4. The first phase should not treat `capture_zone` from old documents as an existing mainline capability; if spatial-occupancy-based win/loss determination is needed, either complement a clear implementation or switch to `conditional` / explicit evaluation path.
5. The first phase should not assume that the `fire_weapon` action is directly linked to weapon launch; the launch main chain needs separate design and verification.

Acceptance criteria:

1. A repeatable `1v1` scenario input exists in the repository.
2. Clear definitions exist for `1v1` win/loss / timeout / disengagement / resource exhaustion metrics.
3. At least one focused test verifies that termination reasons and reward main items are functional.

### WP2: Integration of `1v1` Training Entry into `execution` Mainline

Objectives:

- Do not add a new large flat training entry file.
- Integrate the `1v1` task into the currently maintained `execution` mainline.

Freeze scope:

- [train.py](../../../../train.py)
- [python/env_config.py](../../../../python/env_config.py)
- [gym_envs/universal_env.py](../../../../gym_envs/universal_env.py)
- Necessary training configs

Recommended freeze direction:

1. The first phase does not add a new `agent_layer = "combat_execution"`.
2. The first phase prefers to attach `1v1` as a new task line under the `execution` task family.
3. If a new mode is truly necessary, prioritize adding a narrow config branch rather than copying a complete vec env.

Not recommended for this round:

1. Directly transform `cooperative_execution` into a bilateral adversarial entry.
2. Directly introduce a new agent layer that trains two policies simultaneously.
3. Create a new isolated `TwoShipCombatEnv`.

Acceptance criteria:

1. The existing `train.py` entry remains compatible.
2. The `1v1` config can be launched through the maintained mainline training entry.
3. Not required to complete self-play in this round, but must be able to complete a minimal rollout and checkpoint saving.

### WP3: `1v1` Evaluation and Result Metrics

Objectives:

- Establish evaluation metrics for `1v1` that are independent of `single` / `cooperative`.
- Enable subsequent frozen opponents, self-play, and `2v2` to reuse the same adversarial result statistics fields.

Freeze scope:

- [tools/eval/eval_sb3.py](../../../../tools/eval/eval_sb3.py) or evaluation entries in the same domain.
- Necessary JSON output schema.
- Necessary evaluation documentation and regression tests.

Minimum recommended result fields:

1. Blue win rate
2. Red win rate
3. Draw / timeout rate
4. Average engagement steps
5. Termination reason counts
6. Blue resource consumption or survival status
7. Red resource consumption or survival status

Acceptance criteria:

1. The `1v1` evaluation script can run independently.
2. Output no longer uses only waypoint-success metrics to interpret results.
3. At least one focused test proves that `1v1` evaluation JSON can be generated and fields are stable.

### WP4: Script / Frozen Opponent Baseline

Objectives:

- Provide a stable and reproducible opponent for the first phase `1v1`.
- Avoid attributing early training instability to self-play.

Freeze scope:

- Integration of script opponent or frozen checkpoint opponent.
- Opponent configuration and switching method.
- Necessary smoke / eval tests.

Recommended order:

1. First script opponent
2. Then frozen checkpoint opponent
3. Finally consider policy pool

Rationale:

1. Script opponent is easiest for tuning reward / termination / scene contract.
2. Frozen opponent is better for building a strong baseline after the first version of the contract is stable.
3. Starting directly with a policy pool introduces too many debugging dimensions.

Acceptance criteria:

1. At least one stable opponent can be repeatedly loaded.
2. The distribution of multiple evaluation results under the same configuration is interpretable.
3. The documentation clearly states "what the current baseline opponent is and what it is not."

### WP5: Reserve Interfaces for `2v2` / Self-Play, but Do Not Implement

Objectives:

- Ensure that the first phase `1v1` does not block the subsequent `2v2` path.
- But do not undermine this round's convergence with "future-proofing."

Only the following interface directions are allowed to be reserved in this phase:

1. The evaluation schema allows extended multi-entity statistics for both sides.
2. The scenario/config layer allows expressing blue and red rosters in the future.
3. The opponent loading interface allows subsequent switching to a frozen pool.

Explicitly NOT done in this phase:

1. Formal merging of `cooperative_execution` with the adversarial pipeline.
2. Unified world runtime for multi-controllable rosters on both friendly and enemy sides.
3. Bilateral simultaneous learning optimizer / replay / league mechanisms.

## V. Recommended Entry Point

This round is recommended to proceed in the following order:

1. First draft a `1v1` scenario and contract.
2. Then supplement a minimal training config for the `execution` line.
3. Then supplement the `1v1` result metrics for `eval`.
4. Finally integrate a script opponent and run one round of smoke test.

Risk points to prioritize:

1. Whether the current reward / termination is still overly bound to waypoint-success semantics.
2. Whether the current mission observation is insufficient to carry the minimal air combat task phase.
3. Under the current single `agent_id` path, whether the opponent control surface should be placed in the script chain, scenario behavior chain, or frozen execution policy chain.

## VI. Stopping Conditions

Once the following situations occur, expansion should stop and a new task ticket should be opened:

1. Need to complete `1v1` and `2v2` simultaneously.
2. Need to rewrite `cooperative_execution` synchronously as the main adversarial entry.
3. Need to directly integrate a complete self-play league.
4. Need to significantly modify the existing HMoE / cooperative mainline for `1v1`.

## VII. Expected Deliverables

After this round, the repository should at least have:

1. A maintained `1v1` scenario and task contract.
2. A set of `1v1` configs that can start training.
3. A `1v1` eval path that can output win/loss and final state metrics.
4. A stable script/frozen opponent baseline.
5. A set of minimal smoke / focused tests.

## VIII. Conclusion

Entering air combat `1v1` is a reasonable next step, but the first phase must control variables.

The most suitable approach currently is:

1. Enter through the already stable `execution` mainline.
2. Freeze the goal as "single learner vs single script/frozen opponent."
3. First stabilize the four components: scenario, reward, termination, and evaluation.
4. Clearly defer `2v2` and self-play to the next phase.

This path leverages the recently stabilized cooperative/HMoE infrastructure while avoiding loss of control by prematurely making the problem "multi-agent coordination + confrontation + self-play."
