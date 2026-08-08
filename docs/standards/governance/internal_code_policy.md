# Internal Code Naming Policy

Language:
- English canonical: `governance/internal_code_policy.md`
- Chinese companion: [internal_code_policy.zh.md](internal_code_policy.zh.md)

Status: `2026-08-07` authoritative governance policy for project-internal
tracking codes and implementation-stage aliases.

## Purpose

This policy keeps planning shorthand from becoming an undocumented runtime or
public contract. The repository uses work-package, review-batch, iteration, and
implementation-stage labels to organize development. Those labels are useful
inside their owning plan, but their meaning is not stable enough to lead source
interfaces, runtime diagnostics, schemas, or entry-point documentation.

This policy does not ban technical abbreviations. Domain terms such as `C2`,
`GPU`, `CUDA`, `ECS`, and `SoA` need an owning standard and suitable local
explanation, but they are not work-tracking codes merely because they are short.

## Classification

| Class | Examples | Stability | Permitted primary use |
| --- | --- | --- | --- |
| Semantic name | `flight_dynamics`, `control_preparation`, `observation_projection` | Stable while the capability meaning is stable | Source, runtime diagnostics, schemas, maintained documentation |
| Work-tracking code | `RB7`, `CR2-5a`, `WP15-C`, `I94` | Local to a plan, review batch, or iteration | Owning task plan, historical evidence, commit or review description |
| Implementation-stage alias | `Phase B`, `phase_b`, `kPhaseD...` | Local to one execution decomposition | A defining plan or an explicitly marked compatibility seam |
| Domain abbreviation | `C2`, `EW`, `LOS` | Owned by a domain or joint standard | Stable interfaces when locally expanded and unambiguous |

A short label can move between classes only through an explicit standards
decision. Repeated use does not make a work-tracking code semantic.

## Source And Runtime Rules

Maintained production source under `src/`, `python/`, and `gym_envs/` follows
these rules:

1. Public and internal interfaces lead with semantic capability names.
2. Exceptions, log messages, counters, trace labels, and validation messages do
   not expose work-package, review-batch, or iteration identifiers.
3. File names, types, functions, state fields, and kernels do not use lettered
   implementation phases as their primary name.
4. Tests may record historical identifiers when verifying migration behavior,
   but new assertions should prefer the semantic message or interface.
5. A compatibility alias is allowed only when changing it would break a stable
   serialized or external contract. The preceding or same source line must carry
   `internal-code: compatibility`, and the owning standards/task record must name
   the semantic replacement and removal condition.

For example, a fixed-air dynamics error should name the unsupported capability,
not the review batch that first implemented it. A kernel should be named for
dynamics integration or observation projection, not only for a lettered phase.

## Documentation Rules

Maintained entry points and README files must be understandable without a
separate codebook:

1. Expand a work-tracking code at its first local use and link its owning plan.
2. Use the semantic name in headings and navigation; keep the code in
   parentheses only when it is needed to locate historical evidence.
3. Do not reuse the same short code for unrelated concepts in one maintained
   navigation surface. Add an owner prefix or replace it with a semantic name.
4. Historical plans and accepted evidence may retain their original identifiers,
   but their nearest maintained README must summarize the resulting capability
   semantically.
5. A central glossary is supporting material, not a substitute for local first-use
   expansion.

## Schema And Compatibility Migration

Do not mass-rename serialized keys, trace schema names, artifact fields, or
external protocol values. A migration must:

- define the semantic replacement
- identify readers and writers
- choose a versioned dual-read, dual-write, or explicit breaking transition
- test old and new representations
- state the removal condition for the compatibility alias

An internal code embedded in an unpublished test fixture may be renamed in one
slice when all readers are updated and the fixture is demonstrably not an
external contract.

## Incremental Enforcement

The maintained scanner is:

```bash
python -m tools.maintenance.internal_code_governance \
  --changed-from <base-revision>
```

It audits only added lines relative to the selected base. This prevents new
high-confidence debt without making unrelated changes fail on the existing
historical backlog.

Current severity:

- error: work-tracking codes in production identifiers or runtime strings
- error: new lettered-phase production identifiers without a compatibility marker
- warning: work-tracking codes in source comments
- warning: bare internal codes in maintained documentation

Source matching decomposes snake case and CamelCase/PascalCase identifiers and
checks every production path component. Semantic words that merely contain the
letters `phase`, such as `broadphase_batch`, are not implementation-stage
aliases. C and C++ line and block comments remain comment warnings even when a
selected changed line is inside a block that began on an unchanged line.

Documentation warnings remain non-blocking for the historical and long-tail
documentation backlog. The maintained entry-point baseline is stricter: the
root README pair, `docs/README`, `docs/plan/README`, `docs/task/README`,
`docs/standards/README` pairs, and `tools/README.md` must remain finding-free.
`test_maintained_entry_points_have_no_bare_internal_codes` enforces that bounded
set. Add another entry surface only after remediating it and confirming scanner
precision on the complete file.

## Implementation Size And Ownership

The scanner is owned by `tools/maintenance/internal_code_governance/`; its tests
are owned by `tests/architecture/governance/`. Each module in that package must
remain below 1000 physical lines. If detection grows, split matching policy,
diff collection, reporting, and format-specific parsing instead of growing one
general-purpose script.

## Validation

```bash
python -m pytest -q \
  tests/architecture/governance/test_internal_code_governance.py
python tools/maintenance/translate_docs_batch.py audit --root docs \
  --registry docs/standards/bilingual_document_clusters.json
python -m tools.maintenance.internal_code_governance \
  --changed-from <base-revision>
git diff --check
```

Runtime remediation slices must also run their focused native, facade, contract,
or architecture tests.

## Related Documents

- [Standards Maintenance Policy](standards_maintenance_policy.md)
- [Document Lifecycle Policy](document_lifecycle_policy.md)
- [Bilingual Documentation Policy](bilingual_documentation_policy.md)
- [Repository Consolidation Plan](../../plan/repository_consolidation/README.md)
