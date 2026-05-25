# Naval N4 Integration Acceptance

Status: `2026-05-25` pass / accepted for the pre-fire N4 bridge.

Language:

- English canonical: `naval_n4_integration_acceptance_20260525.md`
- Chinese companion:
  [naval_n4_integration_acceptance_20260525.zh.md](naval_n4_integration_acceptance_20260525.zh.md)

Inputs:

- [N4 threat / ROE bridge task cluster](naval_n4_threat_roe_bridge_cluster_20260524.md)
- [N4 threat / ROE dispatch queue](naval_n4_threat_roe_dispatch_queue_20260524.md)
- [N4 RL task surface preflight](naval_n4_rl_task_surface_preflight_20260525.md)
- [Naval current progress](../naval_current_progress_20260524.md)

## Decision

The N4 `ddg51_take1_screen_threat_roe_v1` bridge is accepted as a pre-fire
scenario expansion. It proves threat/ROE state, engagement authority, and
assigned-target provenance through the maintained command-chain surfaces needed
by the current runtime and RL plumbing.

This acceptance does not open N5 implementation work. A later
`limited_engagement_v1` package may be planned after owner approval, but it must
add launch/reject, range/arc/cooldown/inventory, and non-damage acceptance
gates before any weapon-release task can be claimed.

## Evidence Rollup

| Stream | Result | Accepted evidence |
| --- | --- | --- |
| `N4-A Scenario / Contract Boundary` | pass / accepted | `ddg51_take1_screen_threat_roe_v1` scenario and `naval_screen_threat_roe_geometry` contract exist; N3 screen/contact gates remain in force; no weapon, health, or damage delta is required |
| `N4-B Threat / ROE Semantics` | pass / accepted | maintained fields cover `threat_state`, `roe_state`, engagement authority, assigned target, and assigned-target provenance through command JSON, bindings, naval profile, and loader fallback |
| `N4-C Runtime / Facade Evidence` | pass / accepted | N4 mission-command fields survive maintained world-batch/facade tasking export and Python runtime DTO surfaces |
| `N4-D RL Task Surface Preflight` | pass / accepted | observation/action/reward/termination/eval surfaces are frozen without weapon-release or learned-policy claims |

## Acceptance Checks

| Gate | Result |
| --- | --- |
| N3 screen/contact baseline still passes | accepted through retained contact-report and closing-contact contracts |
| Threat state has track/provenance backing | accepted for the N4 bridge fields and contract window |
| ROE state is observable through maintained contracts | accepted through mission-command shared core and tasking packet export |
| Target assignment cannot be static metadata only | accepted through assigned-target track/source/snapshot provenance fields |
| Unauthorized fire is not success evidence | accepted as out-of-scope/failure posture in the N4 contract and RL preflight |
| Scenario remains N4, not N5/N6 | accepted; launch, hit/intercept, damage, and kill proof remain deferred |
| RL material remains preflight only | accepted; no trainer, reward code, or learned-policy claim is made |

## Validation Record

The N4 queue records the implementation validation packet. The integration
owner reuses that evidence and adds docs-only validation for the new D/E
closure surface:

```bash
git diff --check -- docs/task/naval
```

Relevant accepted implementation evidence from the queue:

```bash
cmake --build build-workshop --target ef_py -j2
# passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json
# PASS

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py
# 33 passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/facade/test_runtime_facade.py
# 30 passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/world_batch/test_world_batch_runtime.py -k "naval or task_order or command_chain or mission_command"
# 7 passed, 22 deselected

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "naval_owner_slice or task_order_naval or command_chain or mission_command"
# 5 passed, 56 deselected
```

## N5 Opening Gate

N5 limited engagement remains blocked until a new package defines:

- launch request and launch/reject event contract;
- valid-track, ROE, range, arc, cooldown, and inventory preconditions;
- explicit rejection reasons;
- non-damage acceptance proof for a single controlled weapon release;
- action masking and failure semantics for RL tasks;
- no dependency on hit probability, intercept success, or damage outcome.

Recommended next planning surface:

- `naval_limited_engagement_v1`, opened as an N5 package only after owner
  approval.

## Residuals

- N4 threat logic is still a bridge-level decision surface, not a complete
  tactical commander.
- The RL task surface is designed, but trainer configs and evaluation commands
  are not implemented in this acceptance slice.
- N6 damage and termination remain deferred.
- Fleet C2, ASW, embarked-air, and UNREP realism stay outside the N4 bridge.
