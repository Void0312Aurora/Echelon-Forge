# A2 Missile Lethality Proximity Fuze Realism Task Clusters

Status: `2026-06-16` finite task cluster list for
[README.md](README.md). PF-P5 validation is complete with residuals; PF-P6
closeout is synced.

Chinese companion:
[missile_lethality_proximity_fuze_realism_task_clusters_20260616.zh.md](missile_lethality_proximity_fuze_realism_task_clusters_20260616.zh.md).

## Boundary Decision

This subproject may create public-source research notes, current-runtime gap
audits, surrogate-contract designs, dispatch records, and acceptance criteria.
It may not broaden runtime configs, scenario behavior, training reward, or
authority claims beyond the explicitly accepted PF-P4/PF-P5 surrogate evidence
slice.

It also may not imply real weapon fuze parameters, deterministic fuze authority,
Pk, stock runtime authority, or weapon-specific lethality.

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `PF-P0` | main thread | n/a | Create the `docs/agent`-compliant planning surface and parent navigation. | `docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_proximity_fuze_realism/**`; parent A2 README files | Runtime edits, tests, reward changes | Markdown inspection, local links, `git diff --check` | Subproject is navigable and states the current implementation boundary. | none | 1 | pass |
| `PF-P1` | main thread | high | Admit public mechanism facts at a high level. | `public_mechanism_source_note_20260616.md`; `public_mechanism_source_note_20260616.zh.md` | Real fuze thresholds, weapon-specific target-detecting-device parameters, classified logic | Source admission check, no numeric authority claims | Sources are separated into admitted mechanism facts and rejected authority claims. | after `PF-P0`; can precede runtime audit | 1 + 1 repair | pass |
| `PF-P2` | main thread | high | Audit current runtime behavior against the admitted mechanism facts. | `current_runtime_gap_audit_20260616.md`; `current_runtime_gap_audit_20260616.zh.md` | Code edits, behavior changes | Read-only `rg` / file inspection, focused test inventory | Gap table names proxy assumptions and preserved observed facts. | after `PF-P1`; serial with `PF-P3` | 1 + 1 repair | pass |
| `PF-P3` | main thread | high | Design the future surrogate event and diagnostic contract. | `proximity_fuze_surrogate_contract_20260616.md`; `proximity_fuze_surrogate_contract_20260616.zh.md` | Implementing fields or changing event schemas before approval | Contract review, link check, test-plan inspection | Contract separates nearest approach, detection, trigger, detonation point, and mechanism coverage. | after `PF-P2` | 1 + 1 repair | pass |
| `PF-P4` | main thread | high | Implement only the approved proximity-fuze surrogate. | Runtime contracts, damage system, Python bindings, diagnostics, focused tests | Pk, deterministic fuze, stock weapon truth, reward masking | `ef_py` build; focused runtime, diagnostics, training, binding tests | Runtime behavior matches accepted surrogate evidence contract. | after explicit continuation; serial | 2 | pass |
| `PF-P5` | main thread | high | Run range/initial-offset/height mechanism comparison after implementation. | `validation/pf_r5_proximity_fuze_validation.py`; final CSV/JSON/heatmap/summary artifacts | Training reward presentation, kill probability claims, full calibration | Matrix artifacts, focused runtime script, docs summary | Trends are explainable and residuals are recorded. | after `PF-P4`; serial for this pass | 2 | pass_with_residuals |
| `PF-P6` | main thread | n/a | Decide accepted boundary and sync docs/index/archive. | README/status/acceptance; parent A2 README | Marking surrogate evidence as real fuze or Pk acceptance | Markdown link check, `git diff --check`, accepted validation command summary | Acceptance boundary is explicit and overclaims remain refused. | last, after `PF-P5` | 1 | pass |

## Dispatch Rules

- Every worker packet must map to exactly one cluster above.
- `PF-P1` to `PF-P3` are documentation/design only. They must not modify
  runtime code, tests, configs, reward, or generated training outputs.
- `PF-P4` and `PF-P5` are complete. Future work must open a new scoped packet
  rather than extending this matrix silently.
- No two workers may edit the same normative table, status line, or acceptance
  section concurrently.
- If a cluster exceeds its round cap, stop and re-scope before adding another
  wave.
- Follow
  [Subagent Usage Policy](../../../../../../engineering/automation/standards/subagent_usage_policy.zh.md).

## Worker Packet Requirements

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
authority/overclaim check:
```

## Validation Plan

```bash
git diff --check -- docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_proximity_fuze_realism docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/README.md docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/README.zh.md
```

Implementation validation is recorded in
[proximity_fuze_runtime_implementation_20260616.md](proximity_fuze_runtime_implementation_20260616.md).
PF-P5 validation is recorded in
[validation/pf_r5_proximity_fuze_validation_20260616.md](validation/pf_r5_proximity_fuze_validation_20260616.md).

## Acceptance Criteria

- The planning surface is navigable from the parent A2 README.
- Public-source facts stay mechanism-level and non-parameterized.
- Current runtime gaps are recorded before implementation.
- Implementation remains limited to the PF-P4 surrogate evidence slice.
- PF-P5 validation remains limited to surrogate gating and mechanism trends.
- The docs continue to reject Pk, deterministic fuze authority, and
  weapon-specific lethality.

## Residual Map

Immediate:

- None for this subproject closeout.

Retained:

- Initial launch-offset symmetry is not a pure fuze symmetry test while live
  guidance remains in the loop.

Deferred:

- Real weapon calibration.
- Pk.
- Deterministic fuze authority.
- Trajectory/environment/seeker stochasticity.
- Pilot/control-authority kill-state coupling.
