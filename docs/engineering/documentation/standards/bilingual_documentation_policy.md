# Bilingual Documentation Policy

Language:
- English canonical: `bilingual_documentation_policy.md`
- Chinese companion: [bilingual_documentation_policy.zh.md](bilingual_documentation_policy.zh.md)

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/engineering/documentation/standards/bilingual_documentation_policy.md`
Owner: `engineering/documentation-governance`
Last verified: `2026-08-13`

Status: `2026-08-13` authoritative for maintained documentation language
layout, including the English-only work/evidence surface and the read-only
Tier D sealed evidence surface.

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
- `docs/domains/air/standards/pilot_action_contract.md`
- `docs/domains/air/standards/pilot_action_contract.zh.md`

A Tier B work document such as
`docs/systems/physics/work/issues/physics_engine_roadmap.md` is maintained as
the English canonical file only and does not carry a `.zh.md` mirror.

## Authority Rules

- If an English canonical file and a Chinese companion diverge, the English
  `.md` file wins.
- A machine-translated draft is not authoritative until a human review removes
  or replaces the draft marker.
- On the Tier A strict bilingual surface, a Chinese-only `.zh.md` file is a
  transitional legacy state, not the target steady state.

Transitional rule during migration:

- If a Tier A document currently exists only as `.zh.md`, it may still be used
  as a working source, but it should be queued for an English companion in the
  next relevant batch.

This transitional rule does not reach Tier D. A Chinese-only page inside a
sealed dated evidence packet is the recorded artifact, not a translation
backlog item, and adding an English canonical peer would not make it more
authoritative. See "Tier D" below.

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

Tier A membership never follows an owner prefix into its `work/` subtrees:
any path with a `work` directory component (for example
`docs/operations/visualization/work/` or `docs/domains/joint/work/`) is
Tier B even when the surrounding owner surface is Tier A.

Tier B: English-only work and evidence surface

- owner-local draft plans and open issues under `docs/*/work/issues/`
- owner-local active work, detailed plans, checkpoints, evidence notes, and
  analysis documents under `docs/*/work/active/` that remain current but
  change quickly
- Tier B documents are maintained as English canonical files without `.zh.md`
  mirrors; the `2026-08-12` work-surface contraction removed the previous
  work-layer mirrors
- a Chinese companion is added only when the owner explicitly promotes the
  document into the Tier A strict bilingual surface; promotion registers both
  file paths (the `.md` and the `.zh.md`) in the `PROMOTED_WORK_DOCUMENTS`
  allowlist inside `tools/maintenance/document_scope.py` and then refreshes
  the new pair record with `clusters --write --pair <pair_id>`
- existing work README pages may keep a `README.zh.md` navigation companion;
  Chinese navigation pages linking English work documents are the expected
  steady state
- a legacy Chinese-only work document (a `.zh.md` without an English peer, or
  one whose Chinese text is still the content superset) keeps its Chinese file
  until the English canonical page is completed; it must not be deleted merely
  to satisfy this tier

Tier C: history, archive, scratch, and local-only retention

- archived material under `docs/Archive/`
- archived material under local `docs/**/archive/` mirrors
- all remaining material under retired `docs/plan/` and `docs/task/` roots,
  which must contain an `archive` path component
- temporary or scratch analysis under `docs/**/temp/` and `docs/temp/`

Tier D: sealed dated evidence

- owner-local review and acceptance packets under a `reviews/` subtree, for
  example `docs/systems/effects/reviews/<packet>_<YYYYMMDD>/` or
  `docs/learning/reviews/<packet>_<YYYYMMDD>/`, including the whole packet
  subtree (`evidence/`, `retained_artifacts/`, `data_collection/`, and peer
  directories)
- a Tier D document records what was inspected on a stated date. It is read
  only: it is not rewritten to reflect later behavior, and a later finding
  belongs in a new dated packet or in `work/active/`
- Tier D carries no bilingual SLA. A page is not translated, is not mirrored,
  and is never queued for a missing English or Chinese companion
- a Chinese-only page in a sealed packet is the retained artifact itself. It is
  outside the transitional Chinese-only rule in "Authority Rules" above
- Tier D content is frequently pinned by SHA-256 entries in a retained-artifact
  manifest. Editing pinned bytes -- including a cosmetic link-depth repair --
  invalidates the pin, so it requires explicit owner authorization and a
  lockstep recomputation of every pin in the affected chain, recorded in the
  packet README. The `2026-08-13` entry in the
  [A2 damage-model packet README](../../../systems/effects/reviews/a2_high_fidelity_damage_model_20260602/README.md)
  is the worked precedent: one ledger link was corrected by owner instruction
  and the `sha256`, `content_hash`, and `size_bytes` pins were re-derived
  through the manifest and gate artifacts until the chain terminated
- when a pin cannot be recomputed, leave the file untouched and record the
  mismatch as an inherited condition instead of "fixing" the bytes

Tier precedence is explicit, because these path rules overlap:

1. an archived or scratch copy is Tier C even under a `reviews/` subtree;
2. a pair the owner promoted into the strict bilingual surface and registered
   in the cluster registry stays Tier A even under a `reviews/` subtree, since
   its bilingual SLA is live;
3. any remaining `reviews/` document is Tier D;
4. everything else is Tier B.

`classify_document` in
[tools/maintenance/document_scope.py](../../../../tools/maintenance/document_scope.py)
is the single source of truth for this decision, and every tracked Markdown
file under `docs/` resolves to exactly one tier. The
`tests/architecture/governance/test_document_tier_census.py` census holds that
partition and its per-tier counts against a checked-in baseline.

Chinese companions are expected for Tier A. They are not maintained for
Tier B unless a document is explicitly promoted, they are outside the default
maintenance verdict for Tier C, and they are prohibited as new work for
Tier D.

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

For new maintained Tier A docs:

1. Write the English canonical `.md` first.
2. Generate or author `name.zh.md` as the companion.
3. Review terminology, links, and code references.
4. Add the pair to the nearest README index when the document becomes a real
   entrypoint.

For new Tier B work docs, write only the English canonical `.md`; do not
create a `.zh.md` mirror unless the document is promoted to Tier A.

For Tier D sealed evidence, there is no translation step at all. Do not batch
these directories, and do not pass them to the translator with
`--include-local-only`.

For existing Tier A Chinese-only docs:

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
- Tier B docs are English-only canonical files, except explicitly promoted
  pairs and retained legacy Chinese sources awaiting an English canonical page
- no maintained canonical doc contains large mixed-language paragraphs
- generated drafts are either reviewed or clearly marked as drafts
- bilingual cluster registry entries are updated when Tier A paired docs change
- local links still resolve after migration

Sealed, temporary, historical, and local-only directories are excluded from
this acceptance bar:

- `docs/**/reviews/` sealed evidence packets outside the registered Tier A
  pairs
- `docs/**/temp/`
- `docs/temp/`
- `docs/Archive/`
- `docs/**/archive/`

The retired `docs/plan/results/` and `docs/plan/architecture/review/` entries
were removed from this list on `2026-08-13`: neither path exists in the tree,
and the surviving `docs/plan/` material is already covered by the `archive`
rule.

## Related Docs

- [docs/README.md](../../../README.md)
- Archived bilingual migration record (`git show 3dc34673:docs/plan/archive/documentation_bilingual_migration_plan_20260518.md`)
- [document_alignment_map.md](../reference/document_alignment_map.md)
