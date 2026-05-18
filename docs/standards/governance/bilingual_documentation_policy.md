# Bilingual Documentation Policy

Language:
- English canonical: `governance/bilingual_documentation_policy.md`
- Chinese companion: [bilingual_documentation_policy.zh.md](bilingual_documentation_policy.zh.md)

Status: `2026-05-18` authoritative for maintained documentation language layout.

This policy defines how the repository separates English and Chinese
documentation so the mainline stays readable, batch-translation friendly, and
easy to audit.

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

- `docs/task/flight_dynamics/README.md`
- `docs/task/flight_dynamics/README.zh.md`
- `docs/plan/runtime_facade/runtime_facade_contract_plan.md`
- `docs/plan/runtime_facade/runtime_facade_contract_plan.zh.md`

## Authority Rules

- If an English canonical file and a Chinese companion diverge, the English
  `.md` file wins.
- A machine-translated draft is not authoritative until a human review removes
  or replaces the draft marker.
- A Chinese-only `.zh.md` file is a transitional legacy state, not the target
  steady state.

Transitional rule during migration:

- If a maintained document currently exists only as `.zh.md`, it may still be
- used as a working source, but it should be queued for an English companion in
- the next relevant batch.

## Where Bilingual Companions Are Expected

Chinese companions are expected for maintained, operator-facing, or authority
documents under:

- `docs/plan/`
- `docs/task/`
- `docs/standards/`
- `docs/manual/`

Chinese companions are optional for:

- short README catalogs under `src/`, `tools/`, `tests/`, `examples/`
- low-level implementation notes whose primary audience is active developers
- archived material under `docs/Archive/`
- archived material under local `docs/**/archive/` mirrors
- temporary or scratch analysis under `docs/**/temp/`, `docs/temp/`,
  and `docs/plan/results/`

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
- Chinese companion: [README.zh.md](../README.zh.md)
```

If a companion is not available yet, say so explicitly rather than mixing both
languages throughout the body.

## Cluster Registry Convention

Maintained bilingual pairs should also participate in the machine-readable
cluster registry:

- [Bilingual Document Clusters](bilingual_document_clusters.md)
- registry file: `../bilingual_document_clusters.json`

Each cluster record tracks:

- `pair_id`
- `source_of_truth`
- `last_verified`
- current `english_hash` / `chinese_hash` baseline values

The registry is used to determine whether one language has been edited without
its peer following along. A translated batch should refresh the touched pair
records so the baseline stays current.

Audit interpretation rule:

- Treat audit output as baseline-relative, not as an automatic semantic drift
  verdict.
- `docs/Archive/` and `docs/**/archive/` are outside the default maintained
  drift verdict, even if they retain mirrored bilingual files for traceability.
- After a bulk doc sweep or directory move, regenerate the registry first with
  `clusters --write`, then rerun `audit`.
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
  `docs/task/flight_dynamics/weapon_guidance/`
- run a link/path sanity check after each batch

This keeps terminology more consistent and makes review easier.

## Tooling Policy

The maintained batch translator for this repo is:

- [tools/maintenance/translate_docs_batch.py](../../../tools/maintenance/translate_docs_batch.py)

Tool requirements:

- use an OpenAI-compatible external API
- preserve Markdown structure, code fences, and relative links
- normalize repository-internal file links to relative targets
- support audit mode before translation
- support `--only-missing` so incremental reruns are cheap

## Acceptance Criteria

A directory can be treated as bilingual-ready when:

- maintained entrypoint docs link to English canonical files first
- Chinese companions exist for the maintained authority docs in that slice
- no maintained canonical doc contains large mixed-language paragraphs
- generated drafts are either reviewed or clearly marked as drafts
- bilingual cluster registry entries are updated when paired docs change
- local links still resolve after migration

Temporary and local-only directories are excluded from this acceptance bar:

- `docs/**/temp/`
- `docs/temp/`
- `docs/Archive/`
- `docs/**/archive/`
- `docs/plan/results/`

## Related Docs

- [docs/README.md](../../README.md)
- [docs/plan/documentation_bilingual_migration_plan_20260518.md](../../plan/documentation_bilingual_migration_plan_20260518.md)
- [document_alignment_map.md](../overview/document_alignment_map.md)
