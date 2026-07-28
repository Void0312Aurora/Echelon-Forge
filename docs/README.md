# Docs Index

Language:
- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

`docs/` is the repository navigation surface for Echelon Forge as a
multi-domain simulation and reinforcement-learning engineering platform. The
tree now covers air combat and flight execution, cooperative execution and
training, naval work, ground work, visualization/game proxy work, model and
world-model planning, and contract-backed runtime/testing evidence at different
levels of maturity.

Use this index to choose the right document class before using any individual
page as authority. A task checkpoint can be accurate history without being the
current rule; a standard can own naming while a task page owns a scoped
implementation plan; a manual can describe code boundaries without authorizing
new work.

## Maintained Entry Surfaces

- [plan/README.md](plan/README.md)
  - Architecture/program authority, runtime-facade and exact-runtime plans,
    cooperative plan material, frozen execution scopes, and plan governance.
  - [Repository consolidation plan](plan/repository_consolidation/README.md)
    records the reviewed iteration protocol, accepted commits, residual
    candidates, and completion conditions for repository-wide simplification.
- [task/README.md](task/README.md)
  - Domain/task worklines, implementation packages, progress checkpoints, and
    archive indexes. Start from each local README before following dated files.
- [standards/README.md](standards/README.md)
  - Joint/service/domain modeling standards, platform baselines, governance
    rules, and bridge contracts. Standards own shared vocabulary and layer
    ownership.
  - [Document lifecycle policy](standards/governance/document_lifecycle_policy.md)
    defines document kinds, lifecycle states, metadata, archive, evidence,
    generated-output, configuration-index, and maintained-link rules.
- [agent/README.md](agent/README.md)
  - Agent-facing authority map and reusable project-orientation prompts that
    index the maintained standards, task, manual, test, and governance surfaces.
- [manual/](manual/README.md)
  - Maintainer and operator manuals: code layer map, engine capabilities,
    physics inventory, visualization guide, and task notes.
- [reference_artifacts.md](reference_artifacts.md)
  - Retained config, scenario, and artifact provenance notes for evidence that
    still matters to maintained work.
- [../tests/README.md](../tests/README.md)
  - Test-system orientation outside `docs/`: runtime suites, JSON contracts,
    focused/local suite manifests, and selected contract batch behavior.

## Domain And Task Navigation

- Air and execution:
  [task/air_combat/](task/air_combat/README.md),
  [task/flight_dynamics/](task/flight_dynamics/README.md),
  [retained performance-runtime planning history](task/archive/performance_runtime/README.md),
  [plan/runtime_facade/](plan/runtime_facade/README.md), and
  [tests/runtime/execution/](../tests/runtime/execution).
- Cooperative:
  [plan/cooperative/](plan/cooperative/README.md),
  [task/simulation_architecture/](task/simulation_architecture/README.md), and
  [tests/runtime/multi_agent/](../tests/runtime/multi_agent).
- Naval:
  [task/naval/](task/naval/README.md),
  [standards/naval/](standards/naval/README.md),
  [tests/runtime/naval/](../tests/runtime/naval), and
  [tests/contracts/unit/naval/](../tests/contracts/unit/naval).
- Ground:
  [task/ground/](task/ground/README.md),
  [standards/ground/](standards/ground/README.md),
  [tests/runtime/ground/](../tests/runtime/ground), and
  [tests/contracts/unit/ground/](../tests/contracts/unit/ground).
- Visualization and game proxy work:
  [task/viz/](task/viz/README.md),
  [task/game/](../game/README.md), and
  [manual/howto/visualization_guide.md](manual/howto/visualization_guide.md).
- Model, policy, and world-model work:
  [standards/model/](standards/model/README.md),
  [task/model/](task/model/README.md),
  [forward/models/hierarchical_moe_execution_policy.md](forward/models/hierarchical_moe_execution_policy.md),
  [../python/world_model/](../python/world_model), and
  [tests/contracts/unit/world_model/](../tests/contracts/unit/world_model).
- Runtime contracts and architecture closure:
  [task/simulation_architecture/](task/simulation_architecture/README.md),
  [plan/architecture/](plan/architecture/README.md),
  [manual/reference/src_layer_map.md](manual/reference/src_layer_map.md), and
  [../tests/contracts/](../tests/contracts).

## Document Classes

| Surface | Use for | Authority boundary |
|---------|---------|--------------------|
| `plan/` | Architecture direction, frozen scopes, contract plans, and route governance | Authoritative when the plan is current or explicitly frozen; archived plan records are history |
| `task/` | Active domain work, dated task packages, progress records, and closeout evidence | Local README pages state the current entry point; deep dated files are supporting records unless promoted |
| `standards/` | Shared vocabulary, service/domain ownership, public-source admission, bilingual policy, and governance | Wins for naming, layer ownership, and modeling boundaries when task docs disagree |
| `agent/` | Agent-facing prompts and document-authority routing | Indexes current rules for AI/agent work; it does not override root docs, standards, code, tests, or user instructions |
| `manual/` | Code maps, operator notes, capability inventories, and practical workflows | Describes maintained behavior; verify against current code and tests before changing implementation |
| `forward/` | Backlogs, roadmaps, and design ideas not yet scheduled as implementation work | Not implementation authority until promoted into `plan/` or `task/` |
| `Archive/`, nested `archive/`, `temp/`, `log/`, `book/`, `results/` | Provenance, local retention, scratch, generated/reference material, or historical snapshots | Not default authority for current work unless a maintained README explicitly points there |

## Maturity And Authority Boundaries

- Directory presence is not a capability claim. This tree contains stable
  standards, accepted baselines, active implementation lanes, exploratory
  prototypes, and retired records side by side.
- Air/execution and runtime-facade material is the most mature mainline surface,
  but it still includes historical checkpoints and forward-looking slices.
- Cooperative, naval, ground, model/world-model, and visualization/game lines
  have different maturity levels. Read each local README for its current
  accepted, active, held, or exploratory status.
- Ground currently has accepted tasking/schema evidence, but broader movement,
  sensing, terrain, fires, damage, and full runtime behavior may still be held
  by the local task entry.
- Game and visualization work is simulation-authoritative proxy work unless a
  maintained task page says otherwise; frontend experiments do not redefine
  simulation truth.
- Tests and JSON contracts provide executable evidence for the selected runner
  or suite. Passing a contract does not automatically promote a whole domain to
  mature, and failing selected batches still fails operationally according to
  the test runner policy.
- Current code and maintained contracts outrank stale task text. For code
  changes, read the relevant `plan/` or `task/` entry first, then verify against
  the current code tree and tests.

## Language And License Notes

- The strict bilingual maintenance surface is intentionally narrower than the
  whole docs tree: it focuses on entry navigation, standards/governance,
  operator manuals, and stable plan authority.
- High-churn task histories, dated checkpoints, and forward-looking idea docs
  should be treated as English-canonical by default unless a narrower slice is
  explicitly promoted into the bilingual maintained surface.
- Avoid treating mixed-language pages as the target steady state.
- Maintained documentation is covered by the repository-level Apache-2.0
  license unless a file or retained third-party artifact states otherwise.
  Third-party assets, datasets, source excerpts, and retained input artifacts
  keep their own rights and license status; see
  [../LICENSE](../LICENSE) and
  [../THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).

## Usage Rule

- If a task needs code changes, prefer reading the relevant `plan/` or `task/`
  entry first, then verify against the current code tree and tests.
- If a document links to historical artifacts, confirm the target still exists
  in the workspace before treating it as an actionable entry point.
