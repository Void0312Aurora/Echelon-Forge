# A7 Config And Diagnostics Evidence

Status: `2026-06-04` `A7-EVC-E Config And Diagnostics` pass as an
implementation and diagnostics slice. This is not learned-policy evidence and
does not release M2.

Parent: [README.md](README.md). Cluster plan:
[a7_event_value_advantage_credit_head_task_clusters_20260604.md](a7_event_value_advantage_credit_head_task_clusters_20260604.md).

## Scope

`A7-EVC-E` exposes the A7 event-credit mechanism through a maintained active
training config and adds diagnostics for the two signals that must be checked
before a learned-policy run:

- event-credit values and advantage signs:
  `Q_hold`, `Q_fire_once`, and `A_event = Q_fire_once - Q_hold`;
- cumulative pre-window stochastic fire probability:
  `P_early = 1 - product(1 - h_t)`.

The slice keeps A3/A5 legal masks, `FiredAssess`, shot budget, and one-shot
suppression authoritative. It does not change missile physics, launch
envelopes, Pk/fuze/damage authority, doctrine, `2v2`, self-play, or HMoE
routing architecture.

## Implementation

Active config:

- `examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json`

The entry keeps the Stage-1 C2/ROE temporal shaped surface and launch-window
gate, but disables the A6 hazard loss:

- `a6_first_event_hazard_coef = 0.0`;
- `a6_first_event_curriculum_coef = 0.0`;
- `a6_first_event_deadline_weight = 0.0`.

It enables the A7 credit path:

- `hybrid_event_credit_head_lr_scale = 6.0`;
- `a7_event_credit_value_coef = 0.4`;
- `a7_event_credit_delta_align_coef = 0.15`;
- positive and negative per-window mass caps are both `1.0`;
- pre-window hold and early-accepted weights move to A7 credit labels.

Callback diagnostics:

- `python/training/diagnostics.py` records A7 event-credit value means,
  advantage sign fractions, open-window advantage stats, and label-aware
  pre-window / quality-window subsets when first-event labels are present.
- The same callback path records label-aware cumulative pre-window stochastic
  fire probability when event probabilities and first-event labels are
  available in the observation batch.

Process-probe diagnostics:

- `tools/diagnostics/air_combat_stage0_process_probe.py` records
  `policy_event_q_hold`, `policy_event_q_fire_once`, and
  `policy_event_advantage` per row.
- Episode summaries reconstruct the configured launch window and report
  pre-window count, quality-window count, pre-window cumulative fire
  probability, and advantage sign fractions by window.

PPO credit-loss logging was implemented in `A7-EVC-D` and remains live through
`a7/event_credit_loss`, `a7/event_credit_value_loss`, and
`a7/event_credit_delta_align_loss` when the A7 active config is used.

## Validation

```bash
python -m json.tool \
  examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json
```

Observed: pass.

```bash
python -m compileall -q \
  python/training/diagnostics.py \
  tools/diagnostics/air_combat_stage0_process_probe.py
```

Observed: pass.

```bash
pytest tests/training/test_a6_event_value_active_config.py -q
```

Observed: `6 passed`.

```bash
pytest tests/training/test_a6_event_value_diagnostics_callback.py -q
```

Observed: `5 passed`.

```bash
pytest tests/diagnostics/test_a6_event_value_process_probe.py -q
```

Observed: `3 passed`.

```bash
pytest tests/training/test_air_combat_active_training_entries.py -q
```

Observed: `13 passed`.

```bash
pytest tests/training/test_cooperative_diagnostics_callback.py -q
```

Observed: `13 passed`.

```bash
pytest tests/diagnostics/test_air_combat_process_probe.py -q
```

Observed: `9 passed`.

## Interpretation

`A7-EVC-E` is complete for config and diagnostics. It proves that the maintained
training entry can activate A7 credit loss and that both callback and process
probe surfaces can expose the advantage signs and cumulative early-fire hazard.

It does not prove learned behavior. `A7-EVC-F Focused Validation Sweep` has
since passed, `A7-EVC-G Short Learned Evidence` has since completed as a held
outcome, and `A7-EVC-I Target Construction And Credit Sign Audit` has since
identified missing shadow-quality target repair. `A7-EVC-J Shadow Quality
Target Repair` has since fixed that label-censoring path, but the learned-policy
repair probe remains held. The current next step is `A7-EVC-K Legal-State
Projection And Coupling Audit`.

## Worker Packet

```md
status: pass
touched files:
- examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json
- examples/config/training/active/air_combat/README.md
- examples/config/training/active/air_combat/README.zh.md
- python/training/diagnostics.py
- tools/diagnostics/air_combat_stage0_process_probe.py
- tests/training/test_a6_event_value_active_config.py
- tests/training/test_air_combat_active_training_entries.py
- tests/training/test_a6_event_value_diagnostics_callback.py
- tests/diagnostics/test_a6_event_value_process_probe.py
commands/outcomes:
- python -m json.tool <A7 active config> -> pass
- python -m compileall -q python/training/diagnostics.py tools/diagnostics/air_combat_stage0_process_probe.py -> pass
- pytest tests/training/test_a6_event_value_active_config.py -q -> 6 passed
- pytest tests/training/test_a6_event_value_diagnostics_callback.py -q -> 5 passed
- pytest tests/diagnostics/test_a6_event_value_process_probe.py -q -> 3 passed
- pytest tests/training/test_air_combat_active_training_entries.py -q -> 13 passed
- pytest tests/training/test_cooperative_diagnostics_callback.py -q -> 13 passed
- pytest tests/diagnostics/test_air_combat_process_probe.py -q -> 9 passed
remaining paths:
- `A7-EVC-I Target Construction And Credit Sign Audit` has since closed as
  repair-required evidence.
- `A7-EVC-J Shadow Quality Target Repair` has since closed as repair-pass but
  behavior-held evidence.
- `A7-EVC-K Legal-State Projection And Coupling Audit` and `A7-EVC-L
  Legal-State Projection Contract` have since closed; the active follow-on is
  `A7-EVC-M Projected Legal-Open Credit Prototype`.
behavior risks:
- A7-G proved the active config can move through live credit-loss training, but
  quality-window advantage stays negative.
integration notes:
- A3/A5 legality remains runtime authority.
- HMoE redesign remains held under the issue-board task.
```
