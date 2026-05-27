# Naval N4 Closure

Status: `2026-05-27` closed as a pre-fire N4 bridge and active-entry gate,
with maintained contact-report, station-hold, and off-station recovery entries
on the dedicated naval action/observation surface and single-policy-slot
cooperative runtime.

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
- the accepted N4-compatible RL task ids now have maintained active smoke/probe
  entrypoints, including a stable off-station recovery gate;
- those entrypoints use `naval_station3`, `naval_screen_station_v1`, and the
  accepted one-policy-slot cooperative roster path;
- `tools/eval/eval_naval_n4_baseline.py` provides a maintained cooperative
  zero-action baseline gate for the N4 active entries;
- the boundary against N5 weapon engagement and N6 damage outcome remains
  explicit and testable.

Closure does not mean:

- a learned naval policy exists;
- a complete naval training curriculum or learned-policy acceptance package
  exists;
- general multi-agent naval training is promoted;
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
| RL entry | Active smoke/probe gates use dedicated N4 naval action/observation surfaces and one DDG policy slot, but they are not learned-policy evidence |

## Closure Matrix

| Gate | Artifact | Closed state |
| --- | --- | --- |
| Scenario | `scenarios/naval/ddg51_take1_screen_threat_roe_v1.json` | N4 pre-fire scenario accepted |
| Contract | `tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json` | threat/ROE screen geometry contract accepted |
| Integration | `naval_n4_integration_acceptance_20260525.md` | command-chain/runtime evidence accepted |
| RL preflight | `naval_n4_rl_task_surface_preflight_20260525.md` | observation/action/reward/termination/eval surface frozen |
| Active entries | `examples/config/training/active/naval/*.json` | contact-report, station-hold, and off-station recovery smoke/probe entries exist and use cooperative single-policy-slot execution |
| Baseline eval | `tools/eval/eval_naval_n4_baseline.py` | zero-action N4 cooperative baseline checks roster, required naval reward terms, and forbidden air/weapon/damage terms |
| Regression gate | `tests/training/test_naval_active_training_entries.py` and `tests/training/test_naval_n4_closure_gate.py` | N4 metadata, scenario, docs, and non-claims are checked |

## Active Entry Scope

Closed active entries:

- `naval_contact_report_threat_roe_v1`
- `naval_screen_station_hold_threat_aware_v1`
- `naval_screen_station_recovery_threat_aware_v1`

These entries are smoke/probe gates. They use the dedicated no-release
`naval_station3` station-order action surface, the `naval_screen_station_v1`
policy observation surface, and the accepted single-policy-slot cooperative
runtime. They must remain marked as `entry_and_gate_only` until a later package
defines complete curriculum, learned-policy acceptance, and broader cooperative
policy semantics.

The recovery entry uses
`ddg51_take1_screen_threat_roe_offstation_recovery_v1`, where the DDG starts
`1800 m` inside the nominal screen station and the station-recovery progress
reward is enabled. This closes a maintained scripted-recovery gate under the
fixed original-task reward reference; it is not a learned recovery policy.

Active-entry scenario paths are now enforced at training bootstrap and by the
maintained N4 eval tool. A config with `naval_entry.scenario_path` must be
launched or evaluated with the declared scenario, so the nominal station-hold
and off-station recovery gates cannot be silently swapped at runtime.
The declared `naval_entry.contract_path` must also point at a contract whose
internal `scenario` field matches that same scenario.
The active-entry tests now execute the unique declared contracts directly, so
the config-to-scenario-to-contract chain is guarded by both declaration checks
and live contract execution.
Training bootstrap and the maintained N4 eval tool also reject any
`naval_entry` config that resolves to an action or observation surface other
than `naval_station3` plus `naval_screen_station_v1`, preventing active naval
entries from silently falling back to an air or generic policy surface.

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

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/training/test_train_bootstrap.py

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_threat_roe_offstation_recovery.json

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/eval/test_eval_naval_n4_baseline.py

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/eval/eval_naval_n4_baseline.py --scenario scenarios/naval/ddg51_take1_screen_threat_roe_v1.json --train_config examples/config/training/active/naval/naval_screen_station_hold_threat_aware_smoke_v1.json --steps 1200

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/eval/eval_naval_n4_baseline.py --mode offstation_probe --scenario scenarios/naval/ddg51_take1_screen_threat_roe_offstation_recovery_v1.json --train_config examples/config/training/active/naval/naval_screen_station_recovery_threat_aware_smoke_v1.json --steps 300

git diff --check -- docs/task/naval examples/config/training/active/naval tests/training/test_naval_n4_closure_gate.py tests/training/test_naval_active_training_entries.py
```

## Next Work

The next naval package should not reopen N4. It should either:

- expand the N4 active entries from baseline eval gates into a full curriculum
  and learned-policy acceptance package; or
- open a separate N5 limited-engagement package with the gates above.
