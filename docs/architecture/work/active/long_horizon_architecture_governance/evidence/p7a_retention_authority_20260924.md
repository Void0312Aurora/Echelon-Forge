# P7-A Retention Authority Evidence

Status: `2026-09-25` — P7-A implementation baseline; P7-B cleanup and
provider/restore drills remain open.

## Scope

P7-A resolves the contradiction between the document lifecycle standard and
the archive-retirement gate without treating repository cleanup as a substitute
for the runtime-governance program. The maintained retention authority is
`docs/engineering/documentation/reference/retention_authority.json`.

The authority makes the default retired-document route explicit:

- retrieve retired documents from Git history through the owner ledger;
- allow only the existing owner-local Cordis archive root, with an archived
  README, owner metadata, and bilingual index routes;
- reject every other in-tree `archive` path unless it is explicitly registered;
- retain ArtifactLedger-backed evidence manifests with restore, access,
  backup, provider, and provider-migration fields;
- require a quarterly restore drill owned by release engineering.

The lifecycle policy, Chinese companion, archive gate, governance suite, and
active program README are bound to the same authority. This is a policy and
repository-contract baseline; it is not evidence that an external provider has
performed a restore drill.

## Verification

Focused governance verification in the isolated worktree:

```powershell
python -m pytest -q `
  tests/architecture/governance/test_p7a_retention_authority.py `
  tests/architecture/governance/test_archive_retirement.py `
  tests/architecture/governance/test_document_link_audit.py `
  tests/architecture/governance/test_document_tier_census.py `
  tests/architecture/governance/test_test_authority_audit.py `
  tests/architecture/governance/test_control_lifecycle_metadata.py
```

Result: **39 passed**.

```powershell
python tools/maintenance/translate_docs_batch.py audit `
  --root docs `
  --registry docs/engineering/documentation/reference/bilingual_document_clusters.json `
  --show-missing none
```

Result: **148 maintained Markdown files; 74 English/74 Chinese; 0 missing;
74 synchronized; 0 diverged**.

```powershell
python tools/runners/audit_test_authority.py --format markdown
git diff --check
```

The derived authority audit and diff check passed. The current derived
inventory is 113 architecture tests and 113 manifest entries; the remaining
source-scan residuals are diagnostic and are not silently retired by P7-A.

The complete local governance suite was also exercised. It produced **65
passed and 3 failed**. Two failures were stale document-link and tier-census
baselines and are green in the focused rerun above. The remaining failure is
the pre-existing P2-B sustainability baseline returning `needs-disposition` in
this environment; it is not a P7-A retention failure and prevents a full-suite
green claim.

## Current revalidation

On `2026-09-25`, the focused retention/archive set was rerun in the current
checkout and passed **41 tests**. The SQLite-backed restore/admission file also
passed **8 tests**. The complete governance suite now passes **78 tests** after
the refreshed P2-B local baseline; these results refresh local evidence only
and do not establish an external provider restore or production rollback-window
operation.

The two additional checks build and validate a provider-neutral evidence
manifest from the actual local SQLite `stable` admission/retention projection,
including its digest, restore owner, access, backup, provider, and migration
policy fields; the same digest is revalidated after restoring the SQLite
backup into a distinct local ledger root. The manifest is local evidence only
and does not claim an external provider drill.

## Boundary and next work

P7-A does not claim:

- external object-store/provider availability or migration;
- a completed quarterly restore drill;
- removal of all historical archive files;
- P7-B retirement cleanup; or
- P8 acceptance.

P7-B must use this authority to finish residual retirement decisions, preserve
retrieval proof, and execute or record the first restore/provider drill when a
real provider is admitted.

Document kind: `evidence`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/evidence/p7a_retention_authority_20260924.md`
Owner: `cross-domain architecture`
Last verified: `2026-09-25`
