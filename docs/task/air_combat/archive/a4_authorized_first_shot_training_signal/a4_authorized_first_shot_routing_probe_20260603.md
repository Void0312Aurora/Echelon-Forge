# A4 Authorized First-Shot Routing Probe - 2026-06-03

Status: `2026-06-03`, routing implementation evidence. A4 remains held; this
record does not accept the learned policy or release M2.

Language:

- English canonical: `a4_authorized_first_shot_routing_probe_20260603.md`
- Chinese companion:
  [a4_authorized_first_shot_routing_probe_20260603.zh.md](a4_authorized_first_shot_routing_probe_20260603.zh.md)

## Scope

The reward-only A4 probe showed that once-per-episode authorized weapon-chain
shaping still left deterministic policies at `0` fire attempts and `0`
releases. The next bounded change is therefore policy mechanics:

- stop routing `air_combat_c2_roe_v1` mission observations into generic
  `nav/vector`;
- give the maintained C2/ROE probes a real routed HMoE family for weapons
  employment;
- keep pulse-prior experiments separate from the retained routing change.

This does not change missile physics, ammunition runtime, launch envelopes,
damage authority, Pk/fuze authority, or real-world BVR doctrine.

## Implementation

`python/rl/policy_algo/hmoe_routing.py` now adds:

- `FAMILY_COMBAT_WEAPONS = 4`;
- default family counts `[3, 2, 3, 1, 3]`;
- combat subexperts:
  - `weapons_hold`;
  - `authorized_first_shot`;
  - `post_launch_assess`.

The 20-field `air_combat_c2_roe_v1` mission layout is detected before the
navigation/formation heuristics. It routes to:

- `authorized_first_shot` when the target contact is present, fire is
  authorized, WCS is not hold, shot policy is active, shot budget remains, and
  no pending assessment is active;
- `post_launch_assess` when pending assessment, own missiles in flight, or an
  exhausted active shot budget is visible;
- `weapons_hold` otherwise.

`python/rl/policy_algo/policies.py` logs the new stats as:

- `hmoe/fam/combat`;
- `hmoe/sub/combat/hold`;
- `hmoe/sub/combat/first_shot`;
- `hmoe/sub/combat/assess`.

The two maintained A3/A4 C2/ROE active configs now set:

- `family_subexpert_counts: [3, 2, 3, 1, 3]`;
- `hmoe_head_lr_scale: 0.35`;
- `hmoe_residual_start_factor: 0.25`.

No pulse-prior relaxation is retained in `train.py`. A follow-up routed 32k
probe tested a naive A4-only relaxation and rejected it because it increased
violation releases without making deterministic policy fire.

## Validation

Commands:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/policy/test_routing_contracts.py \
  tests/policy/test_execution_policy_surface.py
```

Result:

- `27 passed in 3.70s`.

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/training/test_air_combat_training_entry_contracts.py
```

Result:

- `9 passed, 8 subtests passed in 13.84s`.

## Interpretation

The previous failure mode is now split more cleanly:

- reward-only shaping was insufficient;
- C2/ROE mission semantics now reach a dedicated weapons family instead of the
  generic nav/vector route;
- pulse-prior relaxation remains an unaccepted hypothesis, not retained code.

This is still not learned-policy acceptance. The follow-up routed temporal
probe is recorded in
[a4_authorized_first_shot_post_routing_probe_20260603.md](a4_authorized_first_shot_post_routing_probe_20260603.md).

## Superseded Next Evidence

The next evidence command that originally followed this routing review is now
superseded by the retained post-routing run
`a4_authorized_first_shot_routed_retained_temporal_32k_20260603` and the binary
diagnostics packet:

- [a4_authorized_first_shot_post_routing_probe_20260603.md](a4_authorized_first_shot_post_routing_probe_20260603.md)
- [a4_authorized_first_shot_binary_diagnostics_20260603.md](a4_authorized_first_shot_binary_diagnostics_20260603.md)

M2 remains held. The remaining failure is now narrowed to supervised/curriculum
binary pulse optimization or route-specific initialization, not generic routing.
