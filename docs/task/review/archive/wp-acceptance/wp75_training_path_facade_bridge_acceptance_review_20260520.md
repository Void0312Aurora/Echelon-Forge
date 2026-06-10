# WP7.5 Training Path Facade Bridge Acceptance Review

Status: `2026-05-20` accepted.

Language:

- English canonical: `wp75_training_path_facade_bridge_acceptance_review_20260520.md`
- Chinese companion:
  [wp75_training_path_facade_bridge_acceptance_review_20260520.zh.md](wp75_training_path_facade_bridge_acceptance_review_20260520.zh.md)

Reviewed inputs:

- [WP7.5 Training Path Facade Bridge](../simulation_architecture/wp75_training_path_facade_bridge/training_path_facade_bridge_wp75_20260520.md)
- [WP8 SCAL Learning Face](../simulation_architecture/wp8_learning_face/learning_face_wp8_20260520.md)

## 1. Required Acceptance Artifacts

The `WP7.5` acceptance packet is incomplete unless all artifacts below exist and
stay aligned:

- `docs/task/simulation_architecture/wp75_training_path_facade_bridge/training_path_facade_bridge_wp75_20260520.md`
- `docs/task/simulation_architecture/wp75_training_path_facade_bridge/training_path_facade_bridge_wp75_20260520.zh.md`
- `docs/task/review/wp75_training_path_facade_bridge_acceptance_review_20260520.md`
- `docs/task/review/wp75_training_path_facade_bridge_acceptance_review_20260520.zh.md`

Missing artifact rule:

- Any missing artifact forces the overall result to `fail`.
- A present artifact without gate verdicts and required evidence also forces
  `fail`.

## 2. Review Decision Vocabulary

Each gate and the overall line may end only as:

- `pass`: all required evidence is present and not contradicted.
- `fail`: required evidence is missing, contradicted, or replaced by
  intention-only wording.
- `blocked`: environment or machine limitations prevent a required check. This
  keeps the gate open and does not count as acceptance.

Blocked wording rule:

- A blocked gate must name the exact command, exact blocker, and next
  environment needed.
- `Blocked` must not be restated as “ready”, “accepted pending tests”, or any
  equivalent soft pass.

## 3. Gate Checklist

| Gate | Required evidence that must appear in this review | Decision rule |
|------|---------------------------------------------------|---------------|
| `WP7.5-A Step Execution Mainline` | Maintained training-path files checked for step execution, maintained facade surface used for batch stepping, and the exact validation commands or tests proving the maintained mainline no longer depends on raw runtime episode stepping. | Pass only with concrete maintained-path evidence. |
| `WP7.5-B Observation Packet Mainline` | Maintained observation bridge files checked, observation request/result surface consumed, and the exact validation commands or tests proving the maintained path consumes the facade observation packet flow. | Pass only with packet-flow evidence and no maintained-path regression to direct observation getters outside approved seams. |
| `WP7.5-C Compatibility Escape Hatch Reduction` | Explicit list of every remaining acceptable `RuntimeFacade.runtime()` or raw `WorldBatchRuntime` use, with each item classified as compatibility-only or diagnostics-only. | Pass only if all remaining escape hatches are explicitly documented and not promoted into maintained training or learning APIs. |
| `WP7.5-D Validation And Integration Sync` | Confirmation that all required artifacts exist, the narrow regression guard remains in place, and `WP8` cites `WP7.5` for the maintained training-path migration. | Pass only if publication, validation, and `WP8` bridge references are all internally consistent. |

## 4. Reviewer Recording Rule

For every gate, this review should record:

1. The verdict: `pass`, `fail`, or `blocked`.
2. The required evidence actually observed.
3. The exact commands run, if any.
4. The exact blocker and next environment, if blocked.

Absence rule:

- If the review does not explicitly record the verdict and required evidence for
  a gate, that gate is `fail`.

## 5. Current State

Gate snapshot as of `2026-05-20`:

| Gate | Verdict | Evidence observed in this review | Commands / blocker |
|------|---------|----------------------------------|--------------------|
| `WP7.5-A Step Execution Mainline` | `pass` | The maintained mainline code now routes batch step requests through `RuntimeFacade.step_execution_batch()` and the focused regression test records the outer batch-request flags at `tests/world_batch/test_world_batch_vec_env.py`. Static inspection shows the maintained mainline consumes `ExecutionBatchStepResult.observation_packet`. | Passed on this machine: `python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "mainline_step_prefers_batch_step_observation_packet or reset_uses_runtime_facade_compatibly"` and `python -m pytest tests/world_batch/test_world_batch_vec_env.py -q`. The earlier blocked result applies to a separate machine missing either RL dependencies (`torch`, `gymnasium`, `stable-baselines3`) or that machine's `ef_py` build artifact. |
| `WP7.5-B Observation Packet Mainline` | `pass` | Static inspection shows maintained observation reads in `python/rl/runtime/world_batch/adapter.py`, `python/rl/runtime/world_batch_vec_env.py`, and `python/rl/runtime/cooperative_world_batch_vec_env.py` now route through `ObservationBatchRequest` / `ObservationBatchPacket`, and the maintained vec-env regression test rejects direct observation getters on the maintained path. | Passed on this machine: `python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "mainline_step_prefers_batch_step_observation_packet or reset_uses_runtime_facade_compatibly"` and `python -m pytest tests/world_batch/test_world_batch_vec_env.py -q`. On the separate blocked machine, restore `ef_py` with `cmake --build build-workshop --target ef_core ef_py -j4` and install the RL extra or equivalent direct dependencies before rerunning. |
| `WP7.5-C Compatibility Escape Hatch Reduction` | `pass` | The remaining maintained seam is explicitly allowlisted as `compatibility-only`: `python/rl/runtime/world_batch/adapter.py`, `RuntimeFacadeAdapter.__init__`, where `self.facade.runtime()` or fallback `ef_py.WorldBatchRuntime(...)` creates the centralized compatibility adapter root. Test-only raw `WorldBatchRuntime` construction in `tests/runtime/facade/test_runtime_facade.py` is `compatibility-only` fixture coverage. Engagement tests that use `facade.runtime().world(...)` to seed live evidence fixtures are `diagnostics-only`, `test-only`, and not maintained training inputs. | Static audit command used: `rg -n "RuntimeFacade\\.runtime\\(|\\.runtime\\(\\)|WorldBatchRuntime" python/rl/runtime tests/architecture tests/runtime tests/world_batch --glob "*.py"`. Guard evidence passed: `python -m pytest -q tests/architecture/runtime_facade/test_layering.py tests/architecture/runtime_facade/test_design_boundary_gates.py`. |
| `WP7.5-D Validation And Integration Sync` | `pass` | All required `WP7.5` artifacts now exist, the regression guard is documented in the task family and test file, and `WP8` cross references `WP7.5` as the maintained training-path bridge rather than redefining the migration. | Documentation checks completed from the current worktree; no additional runtime blocker applies to artifact existence. |

Overall decision: `pass`.

Reason:

- Acceptance rules are now explicit and review artifacts exist.
- Runtime validation for `WP7.5-A/B` now passes on this machine; the remaining
  environment split is limited to the separate machine and should be handled by
  installing the declared `.[rl]` dependency set plus an `ef_py` build on that
  machine.
- `WP7.5-C` now has an explicit allowlist and guard coverage, and no remaining
  escape hatch is promoted into a maintained policy, training, or learning API.
