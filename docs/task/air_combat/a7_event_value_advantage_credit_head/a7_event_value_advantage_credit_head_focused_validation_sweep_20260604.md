# A7 Focused Validation Sweep

Status: `2026-06-04` `A7-EVC-F Focused Validation Sweep` pass. This validates
the A7 implementation/config/diagnostics surface before learned-policy probing;
it does not claim learned behavior or release M2.

Parent: [README.md](README.md). Config/diagnostics evidence:
[a7_event_value_advantage_credit_head_config_diagnostics_20260604.md](a7_event_value_advantage_credit_head_config_diagnostics_20260604.md).

## Scope

This sweep re-runs the focused gates covering:

- A7 policy head and PPO auxiliary credit from `A7-EVC-C/D`;
- A7 active config, callback diagnostics, and process-probe diagnostics from
  `A7-EVC-E`;
- JSON parsing, Python compile checks, and diff whitespace checks.

It intentionally does not run learned-policy training. The next cluster,
`A7-EVC-G`, owns short learned evidence.

## Commands And Outcomes

```bash
python -m json.tool \
  examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json
```

Observed: pass.

```bash
python -m compileall -q \
  python/rl/policy_algo/policies.py \
  python/rl/policy_algo/first_event_hazard.py \
  python/rl/policy_algo/ppo_adaptive_kl.py \
  python/training/diagnostics.py \
  tools/diagnostics/air_combat_stage0_process_probe.py
```

Observed: pass.

```bash
pytest \
  tests/hmoe/test_hmoe_policy.py \
  tests/hmoe/test_a6_event_head_update_strength.py \
  tests/hmoe/test_hmoe_ppo_warmup.py \
  -q
```

Observed: `44 passed`.

```bash
pytest \
  tests/training/test_a6_event_value_active_config.py \
  tests/training/test_a6_event_value_diagnostics_callback.py \
  tests/training/test_air_combat_active_training_entries.py \
  -q
```

Observed: `24 passed`.

```bash
pytest \
  tests/diagnostics/test_a6_event_value_process_probe.py \
  tests/diagnostics/test_air_combat_process_probe.py \
  tests/training/test_cooperative_diagnostics_callback.py \
  -q
```

Observed: `25 passed`.

```bash
git diff --check -- \
  docs/task/air_combat/a7_event_value_advantage_credit_head \
  examples/config/training/active/air_combat \
  python/training/diagnostics.py \
  tools/diagnostics/air_combat_stage0_process_probe.py \
  tests/training/test_a6_event_value_active_config.py \
  tests/training/test_a6_event_value_diagnostics_callback.py \
  tests/training/test_air_combat_active_training_entries.py \
  tests/diagnostics/test_a6_event_value_process_probe.py
```

Observed: pass.

```bash
rg -n "[ \t]$" \
  docs/task/air_combat/a7_event_value_advantage_credit_head/a7_event_value_advantage_credit_head_config_diagnostics_20260604.md \
  examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json
```

Observed: no matches.

## Interpretation

The focused validation sweep is clean. A7 now has:

- a zero-safe event-credit policy head;
- PPO auxiliary value credit and event-logit delta alignment;
- an active A7 config that disables A6 hazard loss and enables the credit path;
- callback/process-probe diagnostics for event-credit advantage signs and
  cumulative pre-window stochastic fire probability;
- focused tests covering these surfaces.

This still did not prove that a learned policy fires once inside the quality
window. `A7-EVC-G Short Learned Evidence` has since run and remains held:
deterministic probing records `0` releases, stochastic probing fires early, and
quality-window advantage stays negative. `A7-EVC-I Target Construction And
Credit Sign Audit` has since identified missing shadow-quality target repair;
`A7-EVC-J Shadow Quality Target Repair` has since fixed that label-censoring
path but remains held on learned behavior. `A7-EVC-K Legal-State Projection And
Coupling Audit` and `A7-EVC-L Legal-State Projection Contract` have since
closed; the current next step is `A7-EVC-M Projected Legal-Open Credit
Prototype`.

## Worker Packet

```md
status: pass
touched files:
- docs/task/air_combat/a7_event_value_advantage_credit_head/a7_event_value_advantage_credit_head_focused_validation_sweep_20260604.md
commands/outcomes:
- python -m json.tool <A7 active config> -> pass
- python -m compileall -q python/rl/policy_algo/policies.py python/rl/policy_algo/first_event_hazard.py python/rl/policy_algo/ppo_adaptive_kl.py python/training/diagnostics.py tools/diagnostics/air_combat_stage0_process_probe.py -> pass
- pytest tests/hmoe/test_hmoe_policy.py tests/hmoe/test_a6_event_head_update_strength.py tests/hmoe/test_hmoe_ppo_warmup.py -q -> 44 passed
- pytest tests/training/test_a6_event_value_active_config.py tests/training/test_a6_event_value_diagnostics_callback.py tests/training/test_air_combat_active_training_entries.py -q -> 24 passed
- pytest tests/diagnostics/test_a6_event_value_process_probe.py tests/diagnostics/test_air_combat_process_probe.py tests/training/test_cooperative_diagnostics_callback.py -q -> 25 passed
- git diff --check -- <A7 write set> -> pass
- rg -n "[ \t]$" <new A7 untracked files> -> no matches
remaining paths:
- `A7-EVC-I Target Construction And Credit Sign Audit` has since closed as
  repair-required evidence.
- `A7-EVC-J Shadow Quality Target Repair` has since closed as repair-pass but
  behavior-held evidence.
- `A7-EVC-K Legal-State Projection And Coupling Audit` and `A7-EVC-L
  Legal-State Projection Contract` have since closed; continue with
  `A7-EVC-M Projected Legal-Open Credit Prototype`.
behavior risks:
- A7 can influence event logits through live credit training, but the learned
  credit sign is currently wrong in the quality window.
integration notes:
- No learned-policy training was run in this sweep.
- A3/A5 legality and HMoE redesign boundaries remain unchanged.
```
