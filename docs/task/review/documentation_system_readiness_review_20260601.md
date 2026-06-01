# Documentation System Readiness Review

Status: `2026-06-01` implementation-backed documentation review.

Scope: top-level README files, `docs/`, maintained README surfaces under
`src/`, `python/`, `gym_envs/`, `tools/`, `scripts/`, `examples/`,
`scenarios/`, `tests/`, and reference-artifact indexes. Historical archives,
temporary notes, and A2 retained/signoff dirty artifacts were intentionally left
outside this readiness claim.

## Verdict

The documentation system is materially closer to the current implementation,
but it is not fully ready.

It is now reasonable for a reader to understand the project as a multi-domain
simulation and reinforcement-learning research codebase rather than an
air-combat-only project. The maintained entry surfaces now distinguish mature
air/execution paths, cooperative/world-batch integration, bounded naval N4
tasking/contact evidence, and early ground tasking/schema bootstrap.

It is still not reasonable to present the documentation set as a polished,
fully synchronized product manual. Several historical directories retain old
machine-translation markers, obsolete absolute paths, and superseded architecture
language. Those files are archival, but the archive/current boundary must remain
visible so readers do not treat old records as current truth.

## What Now Matches The Implementation

| Area | Current documentation posture | Implementation-backed boundary |
| --- | --- | --- |
| Project identity | Multi-domain simulation/RL research platform | Air/execution is the mature runtime baseline; naval and ground are staged by evidence level. |
| C++ core | Runtime/facade/ECS/component layers are real maintained surfaces | `RuntimeFacade`, `WorldBatchRuntime`, `SimulationKernel`, component/tasking/command slices exist; capability differs by domain. |
| Python/RL | World-batch and cooperative paths are the maintained training direction | Raw `UniversalEnv` remains compatibility/debug/eval-adjacent and should not be described as the primary modern path without qualification. |
| Naval | N4 pre-fire tasking/contact/evidence path is present | Platform components, command/tasking DTOs, token runtime, contact/report plumbing, and limited engagement evidence hooks exist; full naval combat outcome authority is not claimed. |
| Ground | Early tasking/schema/runtime bootstrap | `UnitType::Ground`, typed platform-schema evidence, tasking/profile fixtures, and aircraft/terrain contact primitives exist; full movement, sensing, terrain ownership, fires, damage, and active RL remain held. |
| Examples/scenarios/tests | Active/frozen/diagnostic/archive boundaries are clearer | Active configs and runtime/test assets are evidence gates, not learned-policy or full-domain acceptance by themselves. |

## Remaining Readiness Gaps

| ID | Gap | Risk | Recommended action |
| --- | --- | --- | --- |
| DOC-READY-001 | Archive and temp folders still contain old absolute paths, machine-translation markers, and superseded language. | Search results can still surface obsolete claims unless readers respect archive boundaries. | Keep archive warnings prominent; clean only high-traffic archive indexes unless a historical cleanup pass is explicitly scheduled. |
| DOC-READY-002 | `docs/task/naval/n5_rl_action_surface_split/` name still suggests N5/active-RL semantics while much of the content is an N4 pre-fire/training-entry repair. | Readers may overestimate naval RL and weapon-outcome maturity. | Either rename in a dedicated migration or add an even stronger local banner explaining the directory-name mismatch. |
| DOC-READY-003 | Raw `UniversalEnv`, eval helpers, and diagnostics still need a stricter maintained/compatibility split. | Documentation can drift back toward treating compatibility paths as primary execution surfaces. | Decide whether to migrate tools to WorldBatch/facade or explicitly quarantine them as compatibility/debug paths. |
| DOC-READY-004 | Active cooperative/combined configs still lack a uniform scenario-path/manifest pairing rule. | Config and scenario documentation can imply tighter active acceptance than the implementation enforces. | Add config/schema tests or manifest rules before upgrading those docs from "entry/runtime gate" to broader acceptance. |
| DOC-READY-005 | Air-combat Stage 1-3 scenario files are not the same as maintained active training/runtime evidence. | Scenario-only assets can be mistaken for active runtime support. | Either add focused runtime smoke coverage or mark those stages as planning/scenario-only wherever indexed. |
| DOC-READY-006 | A2 retained/signoff artifacts were not audited in this pass. | Local dirty evidence packets may contain status wording that conflicts with the maintained docs. | Audit A2/signoff separately; do not let that subtree define whole-project maturity. |

## Documentation Operating Rule

Use the maintained root, `docs/README*`, `docs/task/README*`, domain READMEs,
and local README files as the current navigation layer. Treat `archive`,
`Archive`, `temp`, retained artifacts, and dated cluster packets as supporting
records unless a current README explicitly promotes them.

Before upgrading any domain statement, require all three of these to exist:

1. A maintained implementation owner.
2. A maintained runtime/config/test surface.
3. Documentation that names the evidence level without implying a higher one.

## Validation Notes

The readiness pass should be revalidated with:

- `git diff --check`
- a relative Markdown-link check over changed Markdown files
- a stale-wording scan over changed current-entry Markdown files, excluding
  `archive`, `Archive`, `temp`, `retained_artifacts`, and explicitly dirty A2
  signoff paths

Current conclusion: the documentation system is no longer obviously stale at the
maintained entry surfaces, but it should be treated as "implementation-aligned
with known residuals", not "complete".
