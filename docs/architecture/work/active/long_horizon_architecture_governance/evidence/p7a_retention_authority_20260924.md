# P7-A Retention Authority Evidence

Status: `2026-09-28` — bounded local retention authority accepted; broader
provider operations are outside the current acceptance.

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
  backup, provider, and provider-migration metadata;
- require a per-acceptance-local SQLite backup/restore check owned by release
  engineering.

The lifecycle policy, Chinese companion, archive gate, governance suite, and
active program README are bound to the same authority. This is a policy and
repository-contract baseline. External providers and quarterly operations are
explicitly outside the current acceptance boundary.

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

Initial baseline result: **41 passed** before the later P7-B manifest additions.

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
checkout and passed **42 tests**. The SQLite-backed restore/admission file also
passed **8 tests**. The complete governance suite now passes **79 tests** after
the refreshed P2-B local baseline; these results refresh local evidence only
and do not establish an external provider restore or production rollback-window
operation. Those are post-acceptance governance probes, not blockers.

The two additional checks build and validate an in-memory, provider-neutral
evidence-manifest projection from the actual local SQLite `stable`
admission/retention projection, including its digest, restore owner, access,
backup, provider, and migration policy fields; the same digest is revalidated
after restoring the SQLite backup into a distinct local ledger root. The
manifest is also stored as a separate `evidence-short` ArtifactLedger blob
and re-read after the distinct-root restore. This is local evidence only and
does not claim an external provider drill.

## Boundary and next work

P7-A accepts the local SQLite retention/restore route for the bounded scope.
External object-store/provider availability, quarterly operations, and
production rollback-window observation are non-blocking post-acceptance
governance work. Historical archive routing remains governed by the registered
owner-local route.

Document kind: `evidence`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/evidence/p7a_retention_authority_20260924.md`
Owner: `cross-domain architecture`
Last verified: `2026-09-25`
