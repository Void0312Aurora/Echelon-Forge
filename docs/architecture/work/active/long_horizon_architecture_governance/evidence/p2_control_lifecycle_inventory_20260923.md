# P2-A Control Lifecycle Inventory Evidence

Status: `2026-09-23` — the active suite declarations now carry checked
lifecycle metadata; the full program remains open.

P2-A attaches lifecycle data to the four manifests that actually declare and
execute the current test gates:

- `tests/smoke/ci_smoke_suite.json`;
- `tests/smoke/ci_contract_suite.json`;
- `tests/suites/architecture_guard_suite.json`;
- `tests/suites/governance_audit_suite.json`.

The metadata is kept beside each existing manifest. The validator is a small
shape and expiry check; it does not generate a second registry, rewrite suite
membership, or become a runtime authority.

## Current census

| Kind | Count | Controls |
| --- | ---: | --- |
| `permanent` | 5 | architecture guard, governance audit, document-link retrieval, CI smoke, CI contract smoke |
| `migratory` | 2 | runtime-facade compatibility migration, archive-retirement transition |
| `renewable` | 0 | none currently admitted |
| `evidentiary` | 0 | evidence remains attached to the owning gate or P2-B measurement packet |

Every row records `owner`, `invariant`, `kind`, `created`, `expiry`,
`successor`, `renewal_count`, `removal_proof`, and a coverage path. Permanent
controls have no expiry or successor. Migratory controls expire on
`2027-03-31`, have a named successor, and currently have zero renewals. A
renewal is accepted only with a sponsor and forced removal date, and the
validator caps the count at one.

The architecture tier manifest partition assigns every current
`tests/architecture/test_*.py` file to exactly one of the guard or governance
manifests. Individual test files therefore remain coverage entries owned by
their suite control; a new per-test registry is not introduced.

## Verification

Executed in the isolated `codex/long-horizon-governance-architecture`
worktree:

```powershell
$env:CMO_BUILD_DIR='build-long-horizon-p5d-wheel'
python -m pytest -q `
  tests/architecture/governance/test_control_lifecycle_metadata.py `
  tests/runners/test_pytest_suite_manifests.py
python -m ruff check tests/architecture/governance/test_control_lifecycle_metadata.py
```

Results: **10 tests passed** and Ruff passed. The manifest partition check
now covers the previously unlisted build, composition, runtime-contract,
runtime-host, and web-visualization architecture tests as well as the new
lifecycle validator.

## Expiry and removal boundary

The two remaining migratory rows are intentionally still active because their
physical successors are not all complete: full maintained-facade parity, the
P7-A retention decision, and the corresponding replacement evidence remain
open. The UniversalEnv compatibility row was retired in the first P7-B cleanup
slice after its zero-entry inventory and successor facade/VecEnv gates were
verified.
At the simulated date `2027-04-01`, each row is due for disposition; it cannot
be silently renewed. The next allowed action is removal after successor proof,
one bounded sponsored renewal with a forced removal date, or permanent
semantic re-admission through a new decision.

P2-B still owns measured control yield, false positives, CI/evidence cost,
and representative sustainability. This packet establishes lifecycle
ownership and disposition rules; it does not claim P2-A/P2-B or the overall
program accepted.

Document kind: `evidence`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/evidence/p2_control_lifecycle_inventory_20260923.md`
Owner: `cross-domain architecture`
Last verified: `2026-09-23`
