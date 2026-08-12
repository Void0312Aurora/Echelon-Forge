# Bilingual Document Clusters

Language:
- English canonical: `bilingual_document_clusters.md`
- Chinese companion: [bilingual_document_clusters.zh.md](bilingual_document_clusters.zh.md)

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/engineering/documentation/reference/bilingual_document_clusters.md`
Owner: `engineering/documentation-governance`
Last verified: `2026-08-12`

Status: `2026-08-12` reference for the machine-readable bilingual sync registry.

This document defines the lightweight cluster record used to tell whether a
matched `name.md` / `name.zh.md` pair is still in sync.

## Verification Boundary

- Canonical registry data:
  [bilingual_document_clusters.json](bilingual_document_clusters.json)
- Producer and auditor:
  [tools/maintenance/translate_docs_batch.py](../../../../tools/maintenance/translate_docs_batch.py)
- Verified scope: the strict maintained bilingual surface selected by the
  shared documentation-scope rules as of `2026-08-12`.
- The registry verifies path membership and baseline-relative file hashes. It
  does not prove that two languages are semantically equivalent.

Archive rule:

- `docs/Archive/` and any local `archive/` subtree under `docs/**/archive/`
  are excluded from the maintained bilingual cluster audit by default.
- work surfaces (any path with a `work` directory component) are Tier B
  English-only and stay outside the strict registry scope, even under owner
  prefixes such as `docs/operations/` that are otherwise strict.
- local architecture review scratch under `docs/plan/architecture/review/`
  is also excluded from the maintained cluster audit by default.
- Archived mirrors may still keep bilingual files for traceability, but they
  are not part of the active drift verdict.
- The default registry scope is the strict maintained bilingual surface rather
  than the whole shared docs tree. Use the tool's full-tree override only when
  deliberately auditing broader English/Chinese coverage.

## What A Cluster Records

Each bilingual pair is tracked by a `pair_id` derived from the canonical
English path without the `.md` suffix. The identifier is stable while that
canonical path is stable; moving the pair changes its `pair_id` and requires
the old record to be removed and the new record to be registered together.

Each record stores:

- `pair_id`
- `english`
- `chinese`
- `source_of_truth`
- `last_verified`
- `english_hash`
- `chinese_hash`

The live sync state is computed from the registry baseline plus the current
file hashes.

Hash normalization rule:

- line-ending differences such as `LF` vs `CRLF` do not count as bilingual
  drift by themselves
- leading machine-generated draft markers are stripped before hash comparison
  so regenerated draft notes do not invalidate the whole registry alone

## Sync States

- `synced`
- `needs-en-update`
- `needs-zh-update`
- `diverged`
- `missing-en`
- `missing-zh`

## Update And Reverification Triggers

Whenever a translation batch lands, the touched pair records should be
refreshed together so the registry baseline moves forward with the sync.

Use repeated `clusters --write --pair <pair_id>` arguments for a bounded
review. Unselected records, including their hashes and `last_verified` values,
must remain unchanged. A full rewrite is reserved for a full-surface bilingual
review. A canonical-path or registry-path migration may also require a full
rewrite to remove obsolete identifiers, but the resulting diff must be audited
to confirm that unrelated pair records did not drift.

If one side is edited manually afterward, the audit command should show which
peer is now stale.

## Limitations And Interpretation

- Treat `audit` output as relative to the current registry baseline, not as a
  semantic truth oracle.
- Archived trees are outside the default verdict surface; if they appear in an
  audit, it usually means the scan was run with an explicit include override or
  before the exclusion rule was updated.
- If the registry baseline is stale after a bounded doc sweep, manually review
  the changed pairs and selectively refresh only those records before deciding
  whether a reported gap is true drift or ordinary follow-up maintenance.
- `needs-en-update` / `needs-zh-update` usually means one-sided maintenance
  lag.
- `diverged` means both sides changed relative to the recorded baseline and
  should be manually checked against the latest intent before being called a
  real drift.

## Tooling

- [Cluster writer](../../../../tools/maintenance/translate_docs_batch.py):
  `clusters`
- [Registry auditor](../../../../tools/maintenance/translate_docs_batch.py):
  `audit`
