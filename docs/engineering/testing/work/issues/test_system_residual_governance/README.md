# Test System Residual Governance

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/engineering/testing/work/issues/test_system_residual_governance/README.md`
Owner: `engineering/testing`
Last verified: `2026-08-08`

This retained issue records test-system residuals that must remain visible
after the scoped
[test-system governance](../../../reviews/test_system_governance_20260621/README.md)
slice is accepted.

Owner thread: test-system governance and downstream runtime/test owners.

First observed: `2026-06-21`, during the closeout pass now retained as the
[test-system governance review](../../../reviews/test_system_governance_20260621/README.md).

Issue class: cross-cutting test governance residual. These items block broad
test-health, behavior-preservation, or coverage-sufficiency claims, but they do
not block acceptance of the current audit/simplification/tiering slice.

## Summary

The test-system governance slice created a repeatable active-test audit,
documented coverage semantics, split selected oversized tests, clarified smoke
membership, and documented the `weapon_guidance_realism` wrapper/mixin
collection surface.

Four residual groups should stay outside the accepted slice:

- airframe geometry behavior preservation still needs a dependency-complete
  machine because the local focused run skips through existing optional
  `scipy` / `shapely` gates;
- `tests/architecture/damage_model/` no longer has `oversized_test_item`
  findings, but several files remain literal-heavy or source-scan-heavy at the
  file level;
- `tests/runtime/air_combat/weapon_guidance_realism/` now has visible wrappers
  and documentation, but the package-level focused run fails;
- coverage statements remain scoped to measured Python roots and do not
  establish C++ or whole-project coverage sufficiency.

## Current Evidence

- Test-system acceptance record:
  [test_system_governance_acceptance_20260620.md](../../../reviews/test_system_governance_20260621/test_system_governance_acceptance_20260620.md)
- Current status:
  [test_system_governance_current_status_20260620.md](../../../reviews/test_system_governance_20260621/test_system_governance_current_status_20260620.md)
- Audit runner:
  [tools/runners/audit_test_system.py](../../../../../../tools/runners/audit_test_system.py)
- Test-system README:
  [tests/README.md](../../../../../../tests/README.md)
- Weapon-guidance wrapper README:
  [tests/runtime/air_combat/weapon_guidance_realism/README.md](../../../../../../tests/runtime/air_combat/weapon_guidance_realism/README.md)

Measured facts from the `2026-06-21` closeout pass:

| Surface | Evidence | Boundary |
| --- | --- | --- |
| Active audit | 343 active tracked test files, 256 active tracked Python files, 1990 corrected static test items, 152 risk-flagged Python files. | Static audit only; does not prove semantic redundancy or coverage sufficiency. |
| Pytest collection | `2000 tests collected` with `tests --ignore=tests/archive`. | Collection only; emitted existing Eventlet and nanobind side-effect diagnostics. |
| Current accepted focused batch | `205 passed, 30 skipped` for runner, split tools, split damage-model, and suite-manifest tests. | Skips are the existing optional airframe dependency boundary. |
| Smoke suite | `340 passed, 41 subtests passed`. | Does not include failing `weapon_guidance_realism` package. |
| Python coverage | `34376` statements, `11916` missed, `65%` covered from local `.coverage`. | Python roots only; no C++ `src/` or branch coverage acceptance. |
| Weapon-guidance package | `192 tests collected`; focused package run reported `45 failed, 167 passed, 221 subtests passed`. | Local/focused surface only; not accepted for smoke promotion. |

## Impact

- Blocks claims that the whole test system is healthy or sufficiently covered.
- Blocks behavior-preservation acceptance for the split airframe geometry tests
  until a dependency-complete run executes rather than skips.
- Blocks smoke promotion of `weapon_guidance_realism`.
- Blocks treating the remaining damage-model literal/source-scan files as fully
  simplified, even though the oversized single-test-item sweep is complete.
- Requires future coverage reports to name measured roots and distinguish
  Python, C++, smoke, focused, and full-suite evidence.

## Non-Claims

- This issue does not reopen the accepted audit runner, suite-manifest, or
  structural split work.
- This issue does not authorize runtime/model behavior rewrites inside the
  test-system governance subproject.
- This issue does not justify deleting literal-heavy tests without replacement
  evidence.
- This issue does not claim the failing `weapon_guidance_realism` expectations
  are correct or incorrect; it only preserves the failure as a gate.

## Hypotheses

1. The airframe split probably preserved behavior, but the local machine lacks
   the optional geometry dependencies required to prove that by execution.
2. The remaining damage-model source-scan and literal-heavy checks may need a
   data-contract extraction pass, or an explicit focused/local tier
   justification when source scanning is the intended guard.
3. The `weapon_guidance_realism` failures appear to be behavior or expectation
   drift in the active air-combat lethality/guidance surface, not a collection
   problem.
4. Coverage confusion comes from mixing static audit counts, pytest collection,
   local Python coverage, C++ coverage tooling, and smoke-suite execution in one
   narrative.

## Next Gates

1. **Airframe behavior gate**: run the split `tests/tools` airframe geometry
   checks on a dependency-complete machine and record pass/fail evidence.
2. **Damage-model data-contract gate**: decide whether remaining literal-heavy
   and source-scan-heavy checks should become shared data contracts, helpers, or
   documented focused/local guards.
3. **Weapon-guidance behavior gate**: reconcile the failing
   `weapon_guidance_realism` expectations with the current runtime behavior,
   rerun the package green, and only then consider suite promotion.
4. **Coverage gate**: produce separate Python and C++ coverage records with
   measured roots, toolchain prerequisites, and no cross-surface overclaim.

## Closure Criteria

This issue can move from active to retained/closed when all active blockers
above either have fresh passing evidence or have been split into narrower
domain-owned issue records with explicit acceptance gates.
