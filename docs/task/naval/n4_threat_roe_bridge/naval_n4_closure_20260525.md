# Naval N4 Closure

Status: `2026-05-25` closed as a pre-fire N4 bridge and active-entry gate.

Language:

- English canonical: `naval_n4_closure_20260525.md`
- Chinese companion:
  [naval_n4_closure_20260525.zh.md](naval_n4_closure_20260525.zh.md)

Inputs:

- [N4 integration acceptance](naval_n4_integration_acceptance_20260525.md)
- [N4 RL task surface preflight](naval_n4_rl_task_surface_preflight_20260525.md)
- [Naval active training entries](../../../../examples/config/training/active/naval/README.md)
- [Naval current progress](../naval_current_progress_20260524.md)

## Decision

The N4 bridge is closed for the current naval workline.

Closure means:

- `ddg51_take1_screen_threat_roe_v1` is the accepted pre-fire scenario;
- `naval_screen_threat_roe_geometry` is the scenario-level N4 contract;
- threat/ROE, engagement authority, and assigned-target provenance are present
  on maintained tasking surfaces;
- the two accepted N4-compatible RL task ids now have maintained active
  smoke/probe entrypoints;
- the boundary against N5 weapon engagement and N6 damage outcome remains
  explicit and testable.

Closure does not mean:

- a learned naval policy exists;
- a dedicated naval observation/action/reward/eval package exists;
- cooperative naval training is promoted;
- weapon release, hit/intercept, damage, or kill outcome is available as an N4
  task objective.

## Domain Structure

N4 sits on top of the existing N1-N3 naval screen/contact base.

| Layer | N4 closure posture |
| --- | --- |
| Platform and environment | DDG/T-AKE/red surface contact and maritime state remain the fixed public-platform baseline |
| Motion and station | N3 screen geometry remains the maneuver gate; N4 does not add fleet maneuver doctrine |
| Sensor and report chain | Contact source, shared track, and report continuity remain required backing evidence |
| C2 and ROE | `roe_state`, engagement authority, assigned target, and assigned-target provenance are the N4 additions |
| Weapon release | Explicitly excluded from N4; any release belongs to a later N5 package |
| Damage and termination | Explicitly excluded from N4; any damage outcome belongs to N6+ |
| RL entry | Active smoke/probe gates exist, but they are not learned-policy evidence |

## Closure Matrix

| Gate | Artifact | Closed state |
| --- | --- | --- |
| Scenario | `scenarios/naval/ddg51_take1_screen_threat_roe_v1.json` | N4 pre-fire scenario accepted |
| Contract | `tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json` | threat/ROE screen geometry contract accepted |
| Integration | `naval_n4_integration_acceptance_20260525.md` | command-chain/runtime evidence accepted |
| RL preflight | `naval_n4_rl_task_surface_preflight_20260525.md` | observation/action/reward/termination/eval surface frozen |
| Active entries | `examples/config/training/active/naval/*.json` | two smoke/probe entries exist and use maintained world-batch execution |
| Regression gate | `tests/training/test_naval_active_training_entries.py` and `tests/training/test_naval_n4_closure_gate.py` | N4 metadata, scenario, docs, and non-claims are checked |

## Active Entry Scope

Closed active entries:

- `naval_contact_report_threat_roe_v1`
- `naval_screen_station_hold_threat_aware_v1`

Both entries are smoke/probe gates. They use a temporary no-release action
surface because the current execution action APIs are not yet naval-specific.
They must remain marked as `entry_and_gate_only` until a later package defines
dedicated naval observations, actions, rewards, curriculum, and evaluation.

## N5 Opening Gate

N5 remains blocked. Opening `naval_limited_engagement_v1` requires a separate
package with:

- launch request and launch/reject event contract;
- valid-track, ROE, range, arc, cooldown, and inventory preconditions;
- explicit rejection reasons;
- action masking for RL;
- non-damage proof for one controlled release;
- no dependency on hit probability, intercept success, or damage outcome.

## Validation

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/training/test_naval_active_training_entries.py tests/training/test_naval_n4_closure_gate.py

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json

git diff --check -- docs/task/naval examples/config/training/active/naval tests/training/test_naval_n4_closure_gate.py tests/training/test_naval_active_training_entries.py
```

## Next Work

The next naval package should not reopen N4. It should either:

- implement the dedicated naval observation/action/reward/eval package behind
  the N4 active entries; or
- open a separate N5 limited-engagement package with the gates above.
