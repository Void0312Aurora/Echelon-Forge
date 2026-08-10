# A2 Proximity Fuze Realism Acceptance Draft

Status: `2026-06-16` PF-R5 focused surrogate validation accepted with
residuals / real fuze and Pk authority rejected.

Chinese companion:
[missile_lethality_proximity_fuze_realism_acceptance_20260616.zh.md](missile_lethality_proximity_fuze_realism_acceptance_20260616.zh.md).

## Accepted Scope

Accepted:

- PF-R1 public mechanism note.
- PF-R2 current runtime gap audit.
- PF-R3 surrogate contract.
- PF-R4 focused non-authoritative runtime evidence implementation.
- PF-R5 focused surrogate matrix validation.

The current completed planning package consists of:

- [public_mechanism_source_note_20260616.md](public_mechanism_source_note_20260616.md)
- [current_runtime_gap_audit_20260616.md](current_runtime_gap_audit_20260616.md)
- [proximity_fuze_surrogate_contract_20260616.md](proximity_fuze_surrogate_contract_20260616.md)
- [proximity_fuze_runtime_implementation_20260616.md](proximity_fuze_runtime_implementation_20260616.md)
- [validation/pf_r5_proximity_fuze_validation_20260616.md](validation/pf_r5_proximity_fuze_validation_20260616.md)
- [validation/pf_r5_proximity_fuze_validation_heatmaps_20260616.png](validation/pf_r5_proximity_fuze_validation_heatmaps_20260616.png)

PF-R5 is accepted only as a surrogate trend validation. It is not real fuze
calibration or kill-probability authority.

## Required Evidence Before Acceptance

- Public-source mechanism note with admitted and rejected claims: complete.
- Current-runtime gap audit that names proxy behavior in the existing fuze path:
  complete.
- Surrogate contract that separates the following: complete.
  - nearest approach;
  - fuze sensor detection;
  - fuze trigger;
  - detonation point;
  - mechanism-specific coverage;
  - no-detonation no-load outcomes.
- Focused runtime tests and validation commands for PF-R4: complete.
- Matrix comparison summary for trigger radius, initial lateral/vertical offset,
  and mechanism-family behavior: complete with residuals.

## Required Validation Commands

Documentation-only checkpoint:

```bash
git diff --check -- docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_proximity_fuze_realism docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/README.md docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/README.zh.md
```

Runtime validation commands and results are recorded in
[proximity_fuze_runtime_implementation_20260616.md](proximity_fuze_runtime_implementation_20260616.md).

PF-R5 validation command:

```bash
.\tools\maintenance\cmo_env.ps1 python docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_proximity_fuze_realism/validation/pf_r5_proximity_fuze_validation.py
```

PF-R5 results are recorded in
[validation/pf_r5_proximity_fuze_validation_20260616.md](validation/pf_r5_proximity_fuze_validation_20260616.md).

## Forbidden Claims

- Real weapon fuze parameter truth.
- Deterministic fuze authority.
- Pk or weapon-specific kill probability.
- Stock runtime replacement.
- Treating PF-R4/PF-R5 surrogate evidence as real fuze calibration or full lethality acceptance.

## Open Residuals

- Public-source mechanism note is complete.
- Current-runtime gap audit is complete.
- Surrogate contract is complete.
- PF-R4 implementation is complete as a focused surrogate evidence slice.
- PF-R5 validation is complete as a focused surrogate matrix.
- Live guidance keeps actual miss distance in a narrow band, so initial launch
  offsets are not pure detonation-position symmetry tests.

## Acceptance Decision

Current decision: `PF-R5 focused surrogate validation accepted with residuals / real fuze-Pk authority rejected`.
