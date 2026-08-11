# MLF-9 Pk Statistical Trends Task Clusters

Status: `2026-06-19` finite task-cluster plan for
[MLF-9 Pk Statistical Trends](README.md).

## Boundary Decision

MLF-9 may consume accepted, replayable MLF-5 through MLF-8 simulation facts and
produce synthetic statistical trend reports. It may not claim real-world Pk,
weapon-specific lethality, target-specific lethality, calibration authority,
reward authority, entity deletion, or debris physics.

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MLF9-P0` | main thread | n/a | Create the durable subproject surface and parent A2 links. | `docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_pk_statistical_trends/**`; parent A2 README files | Runtime implementation; Pk value claim | `git diff --check -- docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602`; local Markdown link inspection | README, task clusters, dispatch queue, status, and archive placeholder exist and are linked | First; serial | 1 | pass |
| `MLF9-P1` | main thread or read-only diagnostics worker | high | Inventory replayable inputs from MLF-5 through MLF-8 and current diagnostics exports. | MLF-9 inventory/status docs only | Runtime physics edits; metric decisions before inventory | Read-only scan; docs diff check | Accepted input fields, missing joins, and safe implementation write sets are named | After P0; can be read-only parallel by source area | 1 + 1 repair | pass |
| `MLF9-P2` | main thread | high | Define the metric contract and align the diagnostics row surface needed by the contract. | MLF-9 contract docs; `tools/diagnostics/**`; focused diagnostics tests | Real Pk calibration; public-source fitting; runtime damage physics | Contract inspection; py-compile; focused diagnostics tests | Contract can be implemented without implying real-world probability, and accepted MLF-5..8 stages are visible in the row surface | After P1; serial | 2 | initial pass |
| `MLF9-P3` | implementation worker | high | Implement deterministic trend extraction from controlled replay rows or fixtures. | `tools/diagnostics/**` or test-only fixture helpers; focused tests | Reward shaping; entity deletion; changing upstream MLF-5..8 facts | Focused pytest/C++ tests for deterministic summaries; `git diff --check` | Controlled fixture reports are reproducible and bounded | After P2; serial with P4 | 2 | initial pass |
| `MLF9-P4` | integration worker | medium | Expose reports as retained artifacts or diagnostics output without consumer leakage. | MLF-9 docs; diagnostics report paths; optional probe surface | Training success claim; reward authority; calibration promotion | Focused diagnostics tests; report shape inspection | Reports name sample source, denominator, trend labels, and non-claims | After P3 | 2 | initial pass |
| `MLF9-P5` | main thread | medium | Validate focused and smoke lanes. | MLF-9 validation/status docs; test updates if failures reveal scoped gaps | Broad suite cleanup unrelated to MLF-9 | Focused tests; relevant smoke; docs diff check | Validation results are recorded and residuals named | After P4 | 1 + 1 repair | pass |
| `MLF9-P6` | main thread | n/a | Accept, hold, or re-scope MLF-9 and sync indexes/archive. | MLF-9 README/status/acceptance/archive; parent A2 README/archive registry if accepted | Closing with missing evidence; overclaiming Pk | Docs link/path inspection; `git diff --check` | Status and parent indexes match evidence | Last; serial | 1 | pass |

## Dispatch Rules

- Every worker packet must map to exactly one cluster above.
- Do not edit archived MLF evidence packages except for
  link-only maintenance.
- Keep `MLF9-P2`, `MLF9-P5`, and `MLF9-P6` serial.
- If a cluster exceeds its round cap, stop and re-scope before adding a new
  wave.
- Follow
  [Subagent Usage Policy](../../../../../../engineering/automation/standards/subagent_usage_policy.md).

## Worker Packet Requirements

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## Validation Plan

```bash
git diff --check -- docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602
python3 -m py_compile tools/diagnostics/air_combat_weapon_employment_process_probe.py \
  tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/lethality_chain.py \
  tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/lethality_rows.py \
  tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/lethality_snapshot.py \
  tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/schema.py \
  tools/diagnostics/lethality_chain_contract.py \
  tools/diagnostics/mlf9_statistical_trends.py \
  tools/diagnostics/air_combat_weapon_employment_process_probe.py
PYTHONPATH=build-workshop:. pytest -q \
  tests/runtime/air_combat/test_diagnostics_process_probe_lethality.py \
  tests/runtime/air_combat/test_diagnostics_process_probe_summary.py \
  tests/runtime/air_combat/test_diagnostics_process_probe_snapshot.py::DiagnosticsProcessProbeSnapshotTests::test_run_probe_payload_and_chain_csv_include_lethality_chain_rows \
  tests/training/test_fire_timing_fault_localization_contracts.py \
  tests/tools/test_mlf9_statistical_trends.py
```

## Acceptance Criteria

- MLF-9 reports are deterministic for controlled inputs.
- Every reported trend states its sample source, denominator, outcome bucket,
  and uncertainty label.
- Tests prevent trend reports from becoming reward, deletion, or calibration
  authority.
- Real-world Pk, weapon-specific lethality, and target-specific truth remain
  refused.

## Residual Map

Immediate:

- No additional implementation is required for the accepted MLF-9
  simulation-trend/report slice.

Follow-on:

- Sync physical archive and archive registry only if the user asks to archive
  MLF-9.

Deferred:

- MLF-10 calibration gates, public-source outcome admission, and selected
  weapon/target calibration.
