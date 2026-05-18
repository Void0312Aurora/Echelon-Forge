# Documentation Bilingual Migration Plan

Language:
- English canonical: `documentation_bilingual_migration_plan_20260518.md`
- Chinese companion: [documentation_bilingual_migration_plan_20260518.zh.md](documentation_bilingual_migration_plan_20260518.zh.md)

Status: `2026-05-18` active rollout plan.

This plan turns the repository documentation into an English-primary bilingual
system with Chinese companions, while keeping the migration batchable and safe
for ongoing work.

## Baseline Inventory

Repository snapshot from the local audit on `2026-05-18`:

- total Markdown files under `docs/`: `195`
- Chinese companion or Chinese-only files matching `*.zh.md`: `57`
- `.zh.md` files missing an English peer: `56`

Current friction points:

- some maintained indexes still mix Chinese and English in the same file
- some directories still treat Chinese long-form plans as the primary reading
  path
- the earlier migration scope treated too much of `docs/task/**` as if it were
  a stable bilingual authority surface
- entrypoint READMEs in a few areas still deep-link into dated status,
  taskboard, or freeze snapshots instead of stable local README navigation
- some local-only directories such as `docs/plan/archive/` and
  `docs/plan/results/` may exist in one workspace but be ignored from the
  shared remote, so maintained navigation should not rely on them as canonical
  entry surfaces

## Target End State

- English `name.md` is the canonical maintained document.
- Chinese `name.zh.md` is the companion document.
- Maintained entry surfaces stop mixing large Chinese and English paragraphs in
  the same file.
- The default bilingual maintenance surface is intentionally small and
  authority-focused.
- High-churn task/history material can remain English-canonical without
  immediate Chinese parity.
- Translation batches can be executed directory-by-directory with a consistent
  tool and review loop.

## Migration Priorities

### Phase 1: Entry Surfaces

Translate or split the entrypoints that shape how contributors navigate the
repo:

- `docs/README.md`
- `docs/plan/README.md`
- `docs/task/README.md`
- `docs/standards/README.md`
- active area README files such as `docs/task/flight_dynamics/README.md`
- authority index pages such as `docs/plan/architecture/README.md`

Goal:

- stop the most visible mixed-language navigation pages from setting conflicting
  expectations

### Phase 2: Authority Docs

Backfill English canonical docs for the maintained authority records:

- `docs/plan/architecture/*.zh.md`
- `docs/plan/runtime_facade/*.zh.md`
- `docs/plan/cooperative/*.zh.md`
- `docs/manual/*.md`
- selected `docs/standards/` long-form baselines if a Chinese companion is
  later needed

Goal:

- make repo-level planning and architecture authority readable from the English
  mainline

### Phase 3: Stable Task Navigation

Keep the task tree navigable without putting every dated work record onto a
strict bilingual SLA:

- `docs/task/README.md`
- `docs/task/task_archive_convergence_plan_20260518.md`
- subproject README entrypoints under `docs/task/*/README.md`
- deeper README navigation pages under `docs/task/flight_dynamics/*/README.md`

Goal:

- make contributors enter task areas through stable README surfaces instead of
  through dated status/taskboard/freeze docs

### Phase 4: Selective Active Task Backfill

Translate detailed task docs only when they are still current enough to justify
ongoing maintenance:

- the task doc is still the active execution authority
- no local README or newer current-status doc can replace it as the stable
  entry surface
- the area owner explicitly wants Chinese parity for that active slice

Goal:

- keep English mainline readability without turning the whole task/history tree
  into a permanent translation treadmill

## Batch Execution Rules

Translation should run in batches that are easy to review:

- one sibling directory per batch
- `4-8` files per batch
- keep the source total small enough for terminology review
- do not mix architecture, task, and standards docs in one batch

Recommended order inside a directory:

1. README / index
2. authority or contract doc
3. current status / progress checkpoint when it is still genuinely active
4. deeper analysis and implementation packages only when they remain live

## Review Gates

Each batch should clear these gates before being treated as maintained:

- English peer files were generated in the expected `name.md` locations.
- The pair links between `.md` and `.zh.md` are present where the doc is an
  entry surface.
- Relative links still resolve.
- Code identifiers, paths, CLI flags, and doctrine titles were preserved.
- A human reviewer removed or accepted the machine-translation draft note.

## Tooling

The maintained translation tool is:

- [tools/maintenance/translate_docs_batch.py](../../tools/maintenance/translate_docs_batch.py)

The tool is designed for an OpenAI-compatible external API and supports:

- audit mode
- directory scanning
- `--only-missing`
- chunked Markdown translation
- draft-note insertion for generated files

## Example Commands

Audit the current doc tree:

```bash
python3 tools/maintenance/translate_docs_batch.py audit --root docs
```

Backfill missing English peers for one maintained authority slice:

```bash
python3 tools/maintenance/translate_docs_batch.py translate \
  --root docs/plan/architecture \
  --pattern '*.zh.md' \
  --source-lang zh \
  --target-lang en \
  --only-missing
```

Generate Chinese companions from reviewed English docs:

```bash
python3 tools/maintenance/translate_docs_batch.py translate \
  --files docs/plan/architecture/README.md \
          docs/standards/joint/README.md \
  --source-lang en \
  --target-lang zh
```

## Ownership Notes

- The English canonical doc is the merge target for future maintenance edits.
- Chinese companions should track Tier A authority/navigation scope, but they
  should not block fast documentation updates to the English mainline.
- If an area is under heavy churn, it is acceptable to land the English peer
  first and review the Chinese companion in the next batch or skip it for Tier
  B task/history material.

## Acceptance Criteria For The Overall Migration

The migration can be considered complete for the maintained surface when:

- maintained `docs/`, `docs/plan/`, `docs/task/`, and `docs/standards/`
  entrypoints are English-primary
- the Tier A authority surface has bilingual peers
- mixed-language README entry surfaces are removed
- task trees use stable README navigation instead of stale dated deep links
- the translation tool and audit workflow are part of normal doc maintenance

## Related Docs

- [docs/standards/governance/bilingual_documentation_policy.md](../standards/governance/bilingual_documentation_policy.md)
- [docs/task/flight_dynamics/README.md](../task/flight_dynamics/README.md)
- [docs/plan/architecture/README.md](architecture/README.md)
