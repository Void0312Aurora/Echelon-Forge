# A5 Surface Audit

Status: `2026-06-03` pass. Read-only worker packet from current-session subagent
`Lagrange` (`019e8d3a-ae5a-7641-a153-7e3691d27dd2`) accepted by the main thread
after local spot-checks.

Parent: [README.md](README.md).

## Worker Packet Summary

```md
status: pass
cluster: A5-EAM-B Surface Audit
model/reasoning: inherited model / xhigh
scope: read-only surface audit
commands/outcomes:
  Read required A5/A3/A4/M1 docs and scanned code with rg/nl.
  No tests run; this was a read-only audit.
touched files: none
```

The worker did not edit files. The main thread spot-checked the action,
mission-observation, reward-runtime, and policy surfaces before accepting the
packet.

## Surface Map

| Surface | Files and symbols | A5 relevance |
| --- | --- | --- |
| Action space | `gym_envs/universal_env_parts/spaces.py`: `AIR_COMBAT_HYBRID_V1_ACTION_MODE`, `AIR_COMBAT_HYBRID_V1_ACTION_DIM`, `make_action_space()` | Current accepted S1 action transport remains 12D flat `air_combat_hybrid_v1`. |
| Action adapter | `gym_envs/universal_env_parts/actions.py`: `air_combat_hybrid_effective_action()`, `build_pilot_action()`, `radar_active`, `tms_up`, `master_arm`, `fire_weapon`, `fire_gun`, `weapon_select_id` | Current `fire_weapon` is a rising-edge pulse at the adapter, but still policy-facing binary threshold/logit semantics. |
| Single/world-batch runtime | `gym_envs/universal_env.py`, `python/rl/runtime/world_batch_vec_env.py` | These paths apply hybrid rising-edge semantics before `PilotAction`; A5 event support must align with both. |
| C++ release latch | `src/systems/combat/pilot_weapon_release_system.h`, `src/core/engine/simulation_kernel_weapon_release_service.cpp` | Existing release latch prevents held-trigger repeat after success, but low-high-low can still reattempt; A5 cannot rely on this as the event contract. |
| Mission observation taxonomy | `python/mission_obs_taxonomy.py`: `MISSION_OBS_AIR_COMBAT_C2_ROE_V1`, `authorization_to_fire`, `shot_policy_state`, `shot_budget_remaining`, `pending_assessment`, `own_missiles_in_flight_count` | Existing 20D C2/ROE vector already carries the core mask components and post-launch state hints. |
| Mission observation builder | `gym_envs/scenario_loader/mission_observation.py`: `_air_combat_c2_roe_vector()` | Dynamically decrements `shot_budget_remaining` and sets `pending_assessment` / `own_missiles_in_flight_count` from observed releases. |
| HMoE routing | `python/rl/policy_algo/hmoe_routing.py` | Routes 20D C2/ROE observations to `combat_weapons` subexperts; routing is not action support. |
| Reward/runtime release classification | `gym_envs/scenario_loader/reward_runtime/air_combat.py`: `air_combat_c2_roe_state_from_mapping()`, `classify_air_combat_c2_roe_event()`, `_c2_roe_authorized_action_window()`, `_apply_c2_roe_release_discipline()` | Buckets are useful diagnostics, but A5 legality must move to mask/state-machine support rather than penalty learning. |
| Policy distribution | `python/rl/policy_algo/policies.py`: `_HybridActionLayout`, `_HybridActionDistribution`, `HierarchicalMoEExecutionPolicy` | Hybrid params are currently continuous + Bernoulli + categorical; deterministic binary actions use `logit >= 0`. A5 event mask belongs here, not only in runtime. |
| Diagnostics | `tools/diagnostics/air_combat_stage0_process_probe.py`, `python/training_callbacks.py` | Extend to report event state, mask, request/accept/reject, suppression, and policy event probabilities. |
| Active configs/tests | `examples/config/training/active/air_combat/*c2_roe*_probe_v1.json`; tests under `tests/runtime`, `tests/policy`, `tests/training`, `tests/diagnostics` | First implementation should target active S1 C2/ROE shaped configs only. |

## Implementation Risks

- Existing adapter/runtime latches solve held-trigger repeat, not C2/ROE event
  legality. A low-high-low command can still reattempt.
- HMoE route labels such as `authorized_first_shot` are not action support.
  Treating route selection as the contract would leave binary `fire_weapon`
  unchanged.
- Mission-observation field order is hard-coded in routing and tests. Adding
  fields requires synchronized taxonomy, observation, batching, routing, and
  tests.
- Some runtime paths outside `WorldBatchVecEnv` may need follow-up if they enter
  A5 training/eval routes.

## Contract Recommendations

Freeze these names for A5-EAM-C:

- `engagement_state`
- `fire_mask`
- `event_action = {hold, fire_once}`
- `fire_once_requested`
- `fire_once_accepted`
- `fire_once_rejected_reason`
- `release_executed`
- `post_launch_suppressed`
- `reattack_ready`

Recommended `engagement_state` values:

- `Hold`
- `AuthorizedReady`
- `FiredAssess`
- `ReattackReady`
- `Winchester`

Freeze mask components, not only the final bit:

- C2 authorization
- target present
- shot budget
- pending assessment
- weapon/ammo readiness
- reattack permission

## Acceptance Result

`A5-EAM-B Surface Audit` is accepted as `pass`. It unlocks the A5-EAM-C event
contract draft. It does not authorize runtime or policy implementation before
the contract names are frozen.
