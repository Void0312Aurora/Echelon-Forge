# Naval N4 Training Entries

This directory holds maintained active smoke/probe entries for the accepted
DDG/T-AKE `N4` threat/ROE bridge.

## Scope

- Scenario pairing for this line is:
  - [ddg51_take1_screen_threat_roe_v1.json](../../../../../scenarios/naval/ddg51_take1_screen_threat_roe_v1.json)
- Contract pairing is:
  - [naval_screen_threat_roe_geometry.json](../../../../../tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json)
- Current baseline is an entry/runtime gate, not a trained naval policy.

These entries deliberately stay at the pre-fire `N4` boundary. They validate
that the scenario, config, and maintained world-batch execution path can be
paired for RL experiments. They do not expose a weapon-release action, do not
use damage or kill rewards, and do not claim learned screen or engagement
behavior.

## Entries

- [naval_contact_report_threat_roe_smoke_v1.json](naval_contact_report_threat_roe_smoke_v1.json)
  - Minimal contact-report/threat-ROE smoke probe.
  - Uses the accepted N4 scenario and threat/ROE contract as the gate source.

- [naval_screen_station_hold_threat_aware_smoke_v1.json](naval_screen_station_hold_threat_aware_smoke_v1.json)
  - Minimal screen-station threat-aware smoke probe.
  - Uses the same N4 scenario while tracking the second accepted RL task id.

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
```

## Design Notes

- The active action surface is a dedicated no-release naval station-order probe:
  `action_mode=naval_station3`. It adjusts station bearing, station radius, and
  bounded speed intent through the naval task/command chain while keeping the
  ship pilot-action carrier neutral.
- The active observation surface is the naval station/contact mode:
  `mission_obs_mode=naval_screen_station_v1`. It exposes station geometry,
  contact visibility, support-track/report-chain state, ROE, and assigned target
  provenance without inheriting air formation or takeoff field names.
- The trainer path is `agent_layer=execution` with
  `runtime.world_batch_vec_env=true`, so it stays on the maintained world-batch
  runtime rather than the quarantined raw-kernel compatibility path.
- `cooperative_execution` is intentionally not used here yet. The current naval
  roster includes a non-agent support ship, and cooperative slot accounting needs
  a separate gate before this entry can be promoted to a multi-slot naval path.
- Promotion beyond these smoke/probe entries still requires richer packet
  ownership, action masks, reward shaping, cooperative slots, and eval gates.

## Validation

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/training/test_naval_active_training_entries.py
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json
```
