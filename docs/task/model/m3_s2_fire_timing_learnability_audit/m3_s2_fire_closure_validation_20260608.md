# M3-S2 Fire-Closure Validation 2026-06-08

Status: `fire behavior reproduced / focused stochastic gate cleaned after A5
master-arm alignment fix; batch closure pending`.

## Question

Can the current active M3-S2 model prove firing closure if the gate is limited
to executable legal `fire_once` release behavior, while leaving damage/effects
and kill-chain outcomes outside the claim? If not, what blocks the gate?

Current model:

- `experiments_tmp/m3s2_direct_fire_boundary_initfrom_8k_20260608_r1/final_model.zip`

Gate used for this check:

- `fire_once_requested_count >= 1`
- `fire_once_accepted_count >= 1`
- `release_count >= 1`
- `authorized_release_count >= 1`
- `violation_release_count = 0`
- `repeat_release_before_assessment_count = 0`
- clean closure also requires `fire_once_rejected_count = 0` in stochastic
  probes, or a bounded documented reason for any rejection.

## Evidence

Existing 2400-step deterministic probe:

- artifact:
  `experiments_tmp/m3s2_direct_fire_boundary_initfrom_8k_20260608_r1/m3s2_deterministic_probe.json`
- seed: `20260525`
- first release: step `423`
- requested / accepted / rejected: `1 / 1 / 0`
- release / authorized / violation / repeat-before-assessment: `1 / 1 / 0 / 0`
- verdict: clean firing gate passes.

New 2400-step deterministic reproduction:

- artifact:
  `experiments_tmp/m3s2_fire_closure_validation_20260608_r1/deterministic_seed20260608_ep1.json`
- seed: `20260608`
- first release: step `423`
- requested / accepted / rejected: `1 / 1 / 0`
- release / authorized / violation / repeat-before-assessment: `1 / 1 / 0 / 0`
- verdict: clean firing gate passes.

New 800-step deterministic short-window reproduction:

- artifact:
  `experiments_tmp/m3s2_fire_closure_validation_20260608_r1/deterministic_seed20260609_ep1_800.json`
- seed: `20260609`
- first release: step `423`
- requested / accepted / rejected: `1 / 1 / 0`
- release / authorized / violation / repeat-before-assessment: `1 / 1 / 0 / 0`
- verdict: clean firing gate passes inside the known release window.

Existing 2400-step stochastic probe before the A5 master-arm alignment fix:

- artifact:
  `experiments_tmp/m3s2_direct_fire_boundary_initfrom_8k_20260608_r1/m3s2_stochastic_probe.json`
- seed: `20260525`
- first release: step `290`
- requested / accepted / rejected: `2 / 1 / 1`
- rejection reason: `{"weapon_not_ready": 1}`
- release / authorized / violation / repeat-before-assessment: `1 / 1 / 0 / 0`
- verdict before fix: progress gate passes, clean firing closure fails.

New 800-step stochastic reproduction before the A5 master-arm alignment fix:

- artifact:
  `experiments_tmp/m3s2_fire_closure_validation_20260608_r1/stochastic_seed20260608_ep1_800.json`
- seed: `20260608`
- first release: step `290`
- requested / accepted / rejected: `2 / 1 / 1`
- rejection reason: `{"weapon_not_ready": 1}`
- release / authorized / violation / repeat-before-assessment: `1 / 1 / 0 / 0`
- verdict before fix: progress gate passes, clean firing closure fails.

Root cause:

- At the rejected stochastic step, policy sampling produced a `fire_once` pulse
  while the same flat transport frame sampled `master_arm = 0`.
- A5 correctly interpreted that combination as `weapon_not_ready`.
- This was a transport-alignment fault: `fire_once` had become the policy-facing
  event, but the legacy flat `master_arm` switch could still independently
  disable that event in the same frame.

Patch:

- `gym_envs/universal_env_parts/air_combat_event_action.py` now derives
  `master_arm = 1` on the A5/C2-ROE effective transport frame whenever a
  `fire_once` pulse is present before support evaluation.
- `tests/runtime/air_combat/test_air_combat_a5_event_action_runtime.py` adds a
  regression where `fire=True, master_arm=False` under authorized support is
  accepted as a composite `fire_once` event.

After-fix stochastic checks:

- artifact:
  `experiments_tmp/m3s2_fire_closure_validation_20260608_r1/stochastic_seed20260608_ep1_800_after_master_arm_fix.json`
- seed: `20260608`
- first release: step `283`
- requested / accepted / rejected: `1 / 1 / 0`
- release / authorized / violation / repeat-before-assessment: `1 / 1 / 0 / 0`
- verdict: clean focused stochastic firing gate passes.

- artifact:
  `experiments_tmp/m3s2_fire_closure_validation_20260608_r1/stochastic_seed20260525_ep1_800_after_master_arm_fix.json`
- seed: `20260525`
- first release: step `283`
- requested / accepted / rejected: `1 / 1 / 0`
- release / authorized / violation / repeat-before-assessment: `1 / 1 / 0 / 0`
- verdict: clean focused stochastic firing gate passes.

## Decision

The current model plus the A5 master-arm alignment fix can now prove a narrower
fact: deterministic learned-policy execution and the checked stochastic
trajectories emit one legal accepted authorized `fire_once` release without
rejection, violation, or repeat-before-assessment.

This clears the previously localized `weapon_not_ready` transport fault. It is
still not a formal batch closure result because this note only reruns focused
single-episode deterministic/stochastic checks around the known release window.
The next gate is a bounded multi-episode/multi-seed validation run.

Damage/effects observations are explicitly not part of this decision. They
remain A8/task evidence, not the firing-closure gate.

## Next Verification Step

Before upgrading the status to closure, run a bounded batch validation that
requires all checked episodes to satisfy:

- exactly one accepted authorized release;
- zero violation releases;
- zero repeat-before-assessment releases;
- zero rejected `fire_once` requests, or an explicitly accepted bounded reject
  exception;
- reported first-release timing and event-mode support.

If stochastic rejects return in batch validation, the next model/runtime work
should target request cleanliness and readiness alignment, not kill-chain
effects.
