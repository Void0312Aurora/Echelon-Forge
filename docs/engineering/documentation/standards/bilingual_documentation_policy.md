# Bilingual Documentation Policy

Language:
- English canonical: `bilingual_documentation_policy.md`
- Chinese companion: [bilingual_documentation_policy.zh.md](bilingual_documentation_policy.zh.md)

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/engineering/documentation/standards/bilingual_documentation_policy.md`
Owner: `engineering/documentation-governance`
Last verified: `2026-08-08`

Status: `2026-08-08` authoritative for maintained documentation language layout.

This policy defines how the repository separates English and Chinese
documentation so the mainline stays readable, batch-translation friendly, and
easy to audit.

It applies to tracked maintained documentation. Archived, scratch, and
local-only material remains outside the default bilingual maintenance verdict.

## Goals

- English `.md` files are the canonical maintained documents.
- Chinese `.zh.md` files are companion documents, not mixed inline duplicates.
- Maintained docs should avoid paragraph-level Chinese/English mixing in the
  same file.
- Translation work should be batchable by directory and safe to automate with
  an external API.

## File Pairing Rules

- Canonical English document: `name.md`
- Chinese companion: `name.zh.md`
- Canonical English README: `README.md`
- Chinese README companion: `README.zh.md`

Examples:

- `docs/engineering/documentation/README.md`
- `docs/engineering/documentation/README.zh.md`
- `docs/systems/physics/work/issues/physics_engine_roadmap.md`
- `docs/systems/physics/work/issues/physics_engine_roadmap.zh.md`

## Authority Rules

- If an English canonical file and a Chinese companion diverge, the English
  `.md` file wins.
- A machine-translated draft is not authoritative until a human review removes
  or replaces the draft marker.
- A Chinese-only `.zh.md` file is a transitional legacy state, not the target
  steady state.

Transitional rule during migration:

- If a maintained document currently exists only as `.zh.md`, it may still be
  used as a working source, but it should be queued for an English companion in
  the next relevant batch.

## Maintained Surface Tiers

This repo follows a layered maintenance model rather than treating the entire
`docs/` tree as one bilingual SLA surface.

Tier A: strict bilingual maintained surface

- root navigation: `docs/README.md`
- project and ownership-root navigation under `docs/project/`,
  `docs/architecture/`, `docs/domains/`, `docs/systems/`, `docs/learning/`,
  `docs/operations/`, `docs/engineering/`, and `docs/research/`
- agent-facing authority, prompts, and rules under `docs/engineering/automation/`
- retained-reference index: `docs/reference_artifacts.md`
- owner-local standards and references admitted to the strict maintained
  surface, including `docs/engineering/documentation/standards/` and
  `docs/engineering/documentation/reference/`
- migrated Air, Ground, and Naval standards/reference under
  `docs/domains/air/standards/`, `docs/domains/ground/standards/`, and
  `docs/domains/naval/{standards,reference}/`
- migrated Joint common-core and service-profile authority under
  `docs/domains/joint/`
- migrated policy/model architecture standards under `docs/learning/standards/`
- cross-domain owner standards under `docs/architecture/standards/`,
  `docs/systems/standards/`, and `docs/research/standards/`
- operator-facing reference and how-to material under `docs/operations/`
- stable owner README, standards, and admitted reference entry points created
  by the completed plan/task migration, including architecture, domain,
  systems, learning, operations, and engineering-testing routes

Tier B: English canonical, Chinese companion optional or delayed

- owner-local draft plans and open issues under `docs/*/work/issues/`
- owner-local active work, detailed plans, checkpoints, and analysis documents
  that remain current but change quickly

Tier C: history, archive, scratch, and local-only retention

- archived material under `docs/Archive/`
- archived material under local `docs/**/archive/` mirrors
- all remaining material under retired `docs/plan/` and `docs/task/` roots,
  which must contain an `archive` path component
- temporary or scratch analysis under `docs/**/temp/` and `docs/temp/`

Chinese companions are expected for Tier A. They are optional for Tier B and
outside the default maintenance verdict for Tier C.

## Writing Rules

- Keep one language per file body whenever practical.
- Do not alternate Chinese and English bullet-by-bullet inside maintained
  canonical docs.
- Keep code, paths, CLI flags, API names, env vars, and identifiers unchanged.
- Translate human-readable headings, prose, captions, and link labels.
- Use parenthetical glosses sparingly when a domain term is easier to search in
  both languages, for example `mission command (任务指挥)`.
- For links that point to files inside this repository, use relative Markdown
  targets rather than machine-specific absolute workspace paths.

Allowed mixed-language exceptions:

- file paths such as `python/rl/runtime/world_batch_vec_env.py`
- identifiers such as `MissionCommand` or `CommandLink`
- published doctrine names, product names, and source titles
- short glossary-style clarifications

## Navigation Block Convention

Maintained bilingual pairs should include a short language block near the top:

```md
Language:
- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)
```

If a companion is not available yet, say so explicitly rather than mixing both
languages throughout the body.

## Cluster Registry Convention

Maintained bilingual pairs should also participate in the machine-readable
cluster registry:

- [Bilingual Document Clusters](../reference/bilingual_document_clusters.md)
- registry file: `../reference/bilingual_document_clusters.json`

Each cluster record tracks:

- `pair_id`
- `source_of_truth`
- `last_verified`
- current `english_hash` / `chinese_hash` baseline values

The registry is used to determine whether one language has been edited without
its peer following along. A translated batch should refresh the touched pair
records so the baseline stays current.

Operational note:

- cluster hashes intentionally ignore leading machine-generated draft markers
  and normalize line endings so workspace checkout format alone does not
  trigger full-tree bilingual drift noise

Audit interpretation rule:

- Treat audit output as baseline-relative, not as an automatic semantic drift
  verdict.
- `docs/Archive/` and `docs/**/archive/` are outside the default maintained
  drift verdict, even if they retain mirrored bilingual files for traceability.
- After reviewing changed pairs, refresh only those pair records with repeated
  `clusters --write --pair <pair_id>` arguments, then rerun `audit`.
- A full `clusters --write` is allowed after a full-surface bilingual review.
  It is also allowed for a canonical-path or registry-path migration when the
  pre-migration baseline audit is clean and the registry diff proves that
  unrelated records retain their paths, hashes, and verification dates. It must
  not be used to hide unrelated legacy divergence.
- `needs-en-update` / `needs-zh-update` usually indicates one-sided follow-up
  work.
- `diverged` means both sides changed relative to the recorded baseline and
  should be manually checked before calling it a real drift.

## Translation Workflow

For new maintained docs:

1. Write the English canonical `.md` first.
2. Generate or author `name.zh.md` as the companion.
3. Review terminology, links, and code references.
4. Add the pair to the nearest README index when the document becomes a real
   entrypoint.

For existing Chinese-only docs:

1. Keep the current `.zh.md` file in place.
2. Generate the English `name.md` companion in the same directory.
3. Mark generated output as a machine-translated draft until reviewed.
4. After review, update README navigation so the English file is linked first.

## Batch Translation Rules

Batch work should be organized by sibling directory, not by arbitrary file
selection across the whole repo.

Recommended batch shape:

- one directory at a time
- `4-8` files per translation batch
- keep one batch within a single subject area such as
  `docs/engineering/documentation/standards/` or `docs/domains/joint/`
- run a link/path sanity check after each batch

This keeps terminology more consistent and makes review easier.

## Tooling Policy

The maintained batch translator for this repo is:

- [tools/maintenance/translate_docs_batch.py](../../../../tools/maintenance/translate_docs_batch.py)

Tool requirements:

- use an OpenAI-compatible external API
- preserve Markdown structure, code fences, and relative links
- normalize repository-internal file links to relative targets
- support audit mode before translation
- support `--only-missing` so incremental reruns are cheap

## Acceptance Criteria

A directory or maintained slice can be treated as bilingual-ready when:

- Tier A entrypoint docs link to English canonical files first
- Chinese companions exist for the Tier A authority docs in that slice
- Tier B docs follow English-canonical ownership even if Chinese companions lag
- no maintained canonical doc contains large mixed-language paragraphs
- generated drafts are either reviewed or clearly marked as drafts
- bilingual cluster registry entries are updated when Tier A paired docs change
- local links still resolve after migration

Temporary, historical, and local-only directories are excluded from this
acceptance bar:

- `docs/**/temp/`
- `docs/temp/`
- `docs/Archive/`
- `docs/**/archive/`
- `docs/plan/results/`
- `docs/plan/architecture/review/`

## Related Docs

- [docs/README.md](../../../README.md)
- [Archived bilingual migration record](../../../plan/archive/documentation_bilingual_migration_plan_20260518.md)
- [document_alignment_map.md](../reference/document_alignment_map.md)
