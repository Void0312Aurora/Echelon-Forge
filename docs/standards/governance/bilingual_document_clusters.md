# Bilingual Document Clusters

Language:
- English canonical: `governance/bilingual_document_clusters.md`
- Chinese companion: [bilingual_document_clusters.zh.md](bilingual_document_clusters.zh.md)

Status: `2026-05-18` machine-readable bilingual sync registry.

This document defines the lightweight cluster record used to tell whether a
matched `name.md` / `name.zh.md` pair is still in sync.

Archive rule:

- `docs/Archive/` and any local `archive/` subtree under `docs/**/archive/`
  are excluded from the maintained bilingual cluster audit by default.
- local architecture review scratch under `docs/plan/architecture/review/`
  is also excluded from the maintained cluster audit by default.
- Archived mirrors may still keep bilingual files for traceability, but they
  are not part of the active drift verdict.
- The default registry scope is the strict maintained bilingual surface rather
  than the whole shared docs tree. Use the tool's full-tree override only when
  deliberately auditing broader English/Chinese coverage.

## What A Cluster Records

Each bilingual pair is tracked by a stable `pair_id` derived from the
canonical English path without the `.md` suffix.

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

## Update Rule

Whenever a translation batch lands, the touched pair records should be
refreshed together so the registry baseline moves forward with the sync.

Use repeated `clusters --write --pair <pair_id>` arguments for a bounded
review. Unselected records, including their hashes and `last_verified` values,
must remain unchanged. A full rewrite is reserved for a full-surface bilingual
review.

If one side is edited manually afterward, the audit command should show which
peer is now stale.

## Interpretation Rule

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

- `tools/maintenance/translate_docs_batch.py clusters`
- `tools/maintenance/translate_docs_batch.py audit`
