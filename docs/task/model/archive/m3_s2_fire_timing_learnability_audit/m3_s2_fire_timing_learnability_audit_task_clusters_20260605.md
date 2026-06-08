# M3-S2 Fire-Timing Learnability Audit Task Clusters

Status: `archived historical task-cluster plan; dispatch closed on 2026-06-08`.

The retained write scope is the archived evidence package. The original
`docs/task/model/m3_s2_fire_timing_learnability_audit/` path is now a pointer
README only.

## Boundary Decision

M3-S2 is an audit and diagnosis slice. It may add diagnostics, tests, and
evidence docs. It must not open a new training tune, weaken C2/ROE, or claim
learned-policy success.

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `M3S2-P0 Boundary` | main thread | n/a | Define the masked edge-triggered stopping object and breakpoints. | `docs/task/model/archive/m3_s2_fire_timing_learnability_audit/**` | New algorithm claims; training changes. | Markdown inspection. | README names formal object, scope, and acceptance gate. | First; serial. | 1 | pass |
| `M3S2-P1 Diagnostic Tooling` | main thread | n/a | Add hold and legal-mask oracle pulse modes plus aggregate verdict runner. | `tools/diagnostics/air_combat_stage0_process_probe.py`; `tools/diagnostics/air_combat_fire_timing_learnability_audit.py`; focused tests | Reward tuning; policy changes; C2/ROE weakening. | `py_compile`; focused pytest. | Tooling can distinguish hold, early high, legal pulse, delayed legal pulse. | After P0; serial. | 2 | pass |
| `M3S2-P2 Oracle Evidence` | read-only diagnostics worker | n/a | Run bounded Stage-1 oracle audit and retain artifact. | `experiments_tmp/air_combat_fire_timing_learnability_audit_20260605.json`; evidence note | Long training; model acceptance. | Audit command exits 0; JSON verdict present. | Verdict names release reachability, reward delta, timing spread, effects visibility, and edge hazard. | After P1; serial. | 1 | pass |
| `M3S2-P3 Root-Cause Synthesis` | main thread | n/a | Decide whether current blocker is action adapter, reward/effects observability, or optimizer. | Current status and oracle evidence docs | Opening P4 remediation in the same packet. | Markdown inspection; evidence links. | Status names primary and secondary breakpoint without overclaim. | After P2; serial. | 1 | accepted |
| `M3S2-P4 Remediation Selection` | future worker | n/a | Draft the next implementation slice from the accepted diagnosis. | New task or follow-up plan only | Implementing before selected; M2 release by assumption. | Review against P3 evidence. | One bounded next slice is selected or explicitly held. | After P3; serial. | 1 | held / follow-on only |

## Historical Dispatch Rules

No active worker dispatch remains in this archive; these rules are retained as
historical constraints for the sealed packet.

- Every worker packet must map to one cluster above.
- Diagnostics workers may write experiment artifacts only under `experiments_tmp/`
  unless explicitly assigned docs.
- No worker may change reward, C2/ROE legality, missile effects, or model losses
  while this audit is still deciding the breakpoint.

## Worker Packet Requirements

- State the scenario, train config, command, seed, episode count, and max steps.
- Report release count, accepted/rejected fire count, effects event count,
  damage report count, target health drop, total reward, and release steps.
- Separate release-vs-hold reward from legal timing reward spread.
- State whether any claim is diagnostic-only.

## Validation Plan

```bash
python -m py_compile \
  tools/diagnostics/air_combat_stage0_process_probe.py \
  tools/diagnostics/air_combat_fire_timing_learnability_audit.py \
  tests/diagnostics/test_air_combat_process_probe.py \
  tests/diagnostics/test_air_combat_fire_timing_learnability_audit.py

python -m pytest \
  tests/diagnostics/test_air_combat_process_probe.py \
  tests/diagnostics/test_air_combat_fire_timing_learnability_audit.py -q

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_fire_timing_learnability_audit.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s1_grouped_stopping_state_completed_world_batch_probe_v1.json \
  --episodes 2 \
  --seed 31 \
  --max_steps 2000 \
  --delays 0,31,63 \
  --json_out experiments_tmp/air_combat_fire_timing_learnability_audit_20260605.json
```

## Acceptance Criteria

- Focused diagnostics tests pass.
- Audit verdict is reproduced from a retained artifact.
- Root-cause status distinguishes release reachability from legal timing
  identifiability.
- Follow-up work is framed as a model/environment contract decision, not as
  coefficient tuning.

## Residual Map

- `legal_timing_unidentifiable_from_current_return`: primary breakpoint.
- `cumulative_prewindow_hazard_support_collapse`: primary learned-policy
  support-collapse breakpoint.
- `edge_trigger_adapter_credit_hazard`: secondary transport breakpoint.
- `post_release_effect_observable=false`: requires environment/effects/reward
  investigation before timing-quality acceptance can be claimed.
