# Naval N4 Training Entries

This directory holds maintained active smoke/probe entries for the accepted
DDG/T-AKE `N4` threat/ROE bridge.

## Scope

- Scenario pairings for this line are:
  - [ddg51_take1_screen_threat_roe_v1.json](../../../../../scenarios/naval/ddg51_take1_screen_threat_roe_v1.json)
  - [ddg51_take1_screen_threat_roe_offstation_recovery_v1.json](../../../../../scenarios/naval/ddg51_take1_screen_threat_roe_offstation_recovery_v1.json)
- Contract pairings are:
  - [naval_screen_threat_roe_geometry.json](../../../../../tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json)
  - [naval_screen_threat_roe_offstation_recovery.json](../../../../../tests/contracts/unit/naval/naval_screen_threat_roe_offstation_recovery.json)
- Current baseline is an entry/runtime gate, not a trained naval policy.
- Maintained baseline evaluation is the cooperative zero-action station gate in
  [naval_station_policy_eval.py](../../../../../tools/eval/naval_station_policy_eval.py).

These entries deliberately stay at the pre-fire `N4` boundary. They validate
that the scenario, config, and current execution runtimes can be paired for RL
experiments. They do not expose a weapon-release action, do not use damage or
kill rewards, and do not claim learned screen or engagement behavior.

## Entries

- [naval_contact_report_threat_roe_smoke_v1.json](naval_contact_report_threat_roe_smoke_v1.json)
  - Minimal contact-report/threat-ROE smoke probe.
  - Uses the accepted N4 scenario and threat/ROE contract as the gate source.
  - Uses `agent_layer=cooperative_execution` with one DDG policy slot while
    retaining the non-agent T-AKE support roster in the scenario loader.

- [naval_screen_station_hold_threat_aware_smoke_v1.json](naval_screen_station_hold_threat_aware_smoke_v1.json)
  - Minimal screen-station threat-aware smoke probe.
  - Uses the same N4 scenario while tracking the second accepted RL task id.
  - Uses `agent_layer=cooperative_execution` with one DDG policy slot while
    retaining the non-agent T-AKE support roster in the scenario loader.

- [naval_screen_station_recovery_threat_aware_smoke_v1.json](naval_screen_station_recovery_threat_aware_smoke_v1.json)
  - Minimal off-station recovery smoke probe.
  - Uses the maintained off-station N4 scenario where the DDG starts `1800 m`
    inside the nominal screen station.
  - Keeps the same pre-fire threat/ROE boundary and one-DDG policy slot while
    enabling the station-recovery progress reward in the scenario.

## Commands

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/naval/ddg51_take1_screen_threat_roe_v1.json \
  --train_config examples/config/training/active/naval/naval_contact_report_threat_roe_smoke_v1.json \
  --output_base experiments/naval \
  --run_name naval_contact_report_threat_roe_smoke_v1

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/naval/ddg51_take1_screen_threat_roe_v1.json \
  --train_config examples/config/training/active/naval/naval_screen_station_hold_threat_aware_smoke_v1.json \
  --output_base experiments/naval \
  --run_name naval_screen_station_hold_threat_aware_smoke_v1

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/naval/ddg51_take1_screen_threat_roe_offstation_recovery_v1.json \
  --train_config examples/config/training/active/naval/naval_screen_station_recovery_threat_aware_smoke_v1.json \
  --output_base experiments/naval \
  --run_name naval_screen_station_recovery_threat_aware_smoke_v1

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/eval/naval_station_policy_eval.py \
  --scenario scenarios/naval/ddg51_take1_screen_threat_roe_v1.json \
  --train_config examples/config/training/active/naval/naval_screen_station_hold_threat_aware_smoke_v1.json \
  --steps 1200 \
  --json_out experiments/naval/naval_station_zero_action_baseline.json

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/eval/naval_station_policy_eval.py \
  --mode offstation_probe \
  --scenario scenarios/naval/ddg51_take1_screen_threat_roe_offstation_recovery_v1.json \
  --train_config examples/config/training/active/naval/naval_screen_station_recovery_threat_aware_smoke_v1.json \
  --steps 300 \
  --json_out experiments/naval/naval_station_offstation_recovery_probe.json
```

## Design Notes

- `naval_entry.scenario_path` is an execution contract, not only documentation:
  `train.py` and the maintained station policy eval tool reject an active entry if
  `--scenario` does not resolve to the declared scenario. This prevents the
  recovery entry from being accidentally run on the nominal station-hold
  scenario or vice versa.
- `naval_entry.contract_path` is bound to the same declared scenario. Bootstrap
  rejects a contract whose internal `scenario` field points at a different
  scenario, so scenario/config/contract triads remain aligned.
- The active action surface is a dedicated no-release naval station-order probe:
  `action_mode=naval_station3`. It adjusts station bearing, station radius, and
  bounded speed intent through the naval task/command chain while keeping the
  ship pilot-action carrier neutral.
- The active observation surface is the naval station/contact mode:
  `mission_obs_mode=naval_screen_station_v1`. It exposes station geometry,
  contact visibility, support-track/report-chain state, ROE, and assigned target
  provenance without inheriting air formation or takeoff field names.
- All active entries use `cooperative_execution` for the accepted
  single-policy-slot case: the DDG receives the policy slot, and the non-agent
  T-AKE remains in the support roster for reference/report-chain context. This
  is not a general multi-agent naval promotion.
- Promotion beyond these smoke/probe entries still requires richer packet
  ownership, action masks, reward shaping, broader cooperative observation
  schema, and eval gates.
- The baseline eval gate is not a trained-policy claim. It verifies that the N4
  cooperative zero-action hold keeps one DDG policy slot, retains the non-agent
  T-AKE support roster, emits required naval station/contact/report/ROE reward
  terms, and does not emit airfield, weapon, damage, or kill reward terms.
- The off-station probe gate is also not a trained-policy claim. It verifies
  that scripted station hold recovers from an off-station start under the fixed
  original task reference, and that `naval_station3` station-order actions
  cannot move the reward reference onto ownship. The maintained recovery entry
  makes this gate a stable scenario/config pairing; useful non-zero policy
  recovery still requires a separate curriculum and learned-policy acceptance.

## Validation

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/training/test_naval_active_training_entries.py
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/training/test_train_bootstrap.py
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/eval/test_evaluation_cli_contracts.py
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/eval/naval_station_policy_eval.py --mode offstation_probe --scenario scenarios/naval/ddg51_take1_screen_threat_roe_offstation_recovery_v1.json --train_config examples/config/training/active/naval/naval_screen_station_recovery_threat_aware_smoke_v1.json --steps 300
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_threat_roe_offstation_recovery.json
```
