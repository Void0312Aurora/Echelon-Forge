# Internal-Code Residual Audit — 2026-08-07

Language:

- English canonical: `task/review/internal_code_residual_audit_20260807.md`
- Chinese companion: [internal_code_residual_audit_20260807.zh.md](internal_code_residual_audit_20260807.zh.md)

Status: measured residual inventory after the first internal-code governance
pass. This record is an audit baseline, not a claim that the repository is
finding-free.

## Scope And Method

The inventory covers tracked production source files under `src/`, `python/`,
and `gym_envs/` with the source suffixes recognized by the maintained scanner.
Documentation, archives, build output, and third-party source are outside this
measurement. The command was run against complete files, not only changed
lines:

```powershell
$paths = git ls-files gym_envs python src |
  Where-Object { $_ -match '\.(c|cc|cpp|cu|cuh|h|hpp|inc|py)$' }
python -m tools.maintenance.internal_code_governance `
  --paths $paths --format text --fail-on never
```

## Measured Result

| Snapshot | Files | Lines | Errors | Warnings | Total findings |
| --- | ---: | ---: | ---: | ---: | ---: |
| Before active-source cleanup | 692 | 162,383 | 488 | 133 | 621 |
| After active-source cleanup | 692 | 162,384 | 368 | 106 | 474 |
| After detector hardening and probe retirement | 692 | 162,064 | 375 | 106 | 481 |
| After compiled-fragment and literal hardening | 824 | 169,975 | 315 | 146 | 461 |

The one-line increase is the direct standard-library include required to
compile the candidate-admission test as an independent MSVC object. The cleanup
removed 147 findings without suppressing or reclassifying detector output.
The final snapshot is not a regression delta against 474: it uses the hardened
detector, which newly covers CamelCase/PascalCase identifiers and all production
path components. Retiring the obsolete resource-capture implementation accounts
for the lower line count. The latest snapshot adds all 132 tracked `.inc`
fragments (7,911 lines) and 40 comment warnings. Tight phase-letter boundaries
remove 53 semantic-word false positives, high-confidence acronym boundaries
remove 7 technical-abbreviation false positives, and multiline-literal state
reclassifies 37 runtime strings that previously appeared as source tokens.

The current 461 findings break down as follows:

| Finding class | Count | Meaning |
| --- | ---: | --- |
| Runtime tracking labels | 209 | A runtime string still exposes a work-tracking label. |
| Source tracking labels | 65 | An identifier or non-comment source token still uses a work-tracking label. |
| Lettered implementation-stage identifiers | 34 | An implementation identifier still names a lettered stage rather than a capability. |
| Production-path tracking labels | 7 | An existing production path still includes a work-tracking label; new and renamed paths are blocked. |
| Source-comment tracking labels | 146 | A comment still depends on plan-local shorthand. |

## Remediated In This Pass

- CUDA resident candidate-admission and device-state tests now use capability
  names for macros, test cases, request identifiers, entities, and errors.
- Runtime-facade and Python-binding comments now name allocators, evidence
  producers, opt-in behavior, and schema ownership directly.
- Eleven maintained entry-point documents form a complete-file, zero-finding
  blocking baseline.
- Changed-line enforcement prevents new production identifiers, runtime text,
  and lettered implementation-stage aliases from increasing the backlog.

## Retained Residual Classes

### Frozen Resource Evidence

The CUDA resource-evidence contract and its experimental probe sessions retain
versioned schema values, captured symbols, and recorded source hashes. Renaming
those values without a new capture would make historical evidence appear
current when it is not. Their cleanup requires a versioned evidence recapture,
updated readers, and an explicit retirement condition for the old records.
The legacy resource-capture executable now exits with failure before collection;
historical readers remain available for the frozen artifacts, while any new
capture requires a new schema and kernel catalog.

### Historical Provenance

The backend-profile registry retains paths and change reasons that identify
archived review evidence. These are provenance values, not active runtime
terminology. They should change only with a migration that preserves lookup of
the archived records.

### Active Long-Tail Source

The remaining non-frozen findings are concentrated in decision-command
adapters, runtime profile adapters, architecture classification registries, and
older broad test surfaces. They are genuine cleanup debt, but they are outside
the CUDA-focused migration completed here. Owners should replace each label
with a domain or capability name while preserving serialized compatibility
where applicable.

One touched file, `src/interfaces/python/bindings_runtime.cpp`, remains a
pre-existing large module: 1,542 physical lines at both the branch base and the
current snapshot. This pass changed comments only and introduced no line
growth. Splitting it belongs in a separate binding-ownership migration because
registration order and field coverage are compatibility-sensitive. A safe
split should group registration by contract family and gate exported Python
surface parity before moving each group.

## Governance Boundary

The accepted state is no-growth plus a measured residual inventory, not
repository-wide zero debt:

1. Changed production lines fail on high-confidence runtime and identifier
   findings.
2. Maintained entry-point documents fail on any complete-file finding.
3. Historical documentation and source comments remain visible as warnings.
4. Frozen evidence is migrated only through a versioned recapture.
5. A document joins the strict entry-point baseline only after its complete
   file scans cleanly.

The next high-value iteration is the versioned CUDA resource-evidence recapture;
ordinary long-tail cleanup can then proceed by semantic owner without mixing
historical evidence changes into unrelated work.

## Related Documents

- [Internal Code Naming Policy](../../standards/governance/internal_code_policy.md)
- [CUDA Resident Semantic Stage Migration](../../plan/exact_runtime/cuda_resident_semantic_stage_migration_20260807.md)
