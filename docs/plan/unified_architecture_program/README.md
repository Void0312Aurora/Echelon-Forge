# Unified Architecture Program

Language:
- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Document kind: `plan`
Lifecycle: `maintained`
Canonical: `docs/plan/unified_architecture_program/README.md`
Owner: `unified architecture program workline`
Last verified: `2026-07-20`

Status: active program on branch `codex/redundancy-consolidation`, extending
the completed text-level consolidation phases (I1-I19) and the blueprint
waves W1-W2 (I20-I24) into a single frozen roadmap for the remaining
architecture-level unification work.

## Objective

Replace the remaining hand-maintained parallel infrastructure with owned,
generated, or composed systems, so that the marginal cost of adding a DTO
field, a training line, a probe, or a domain slice drops to one edit at one
owner. The program may change architecture where the evidence supports it,
but behavior preservation, byte/ABI parity evidence, public-surface
compatibility, and bounded capability claims remain absolute constraints.

## Governance

- The iteration ledger stays in the
  [Repository Consolidation Plan](../repository_consolidation/README.md)
  register. Program iterations continue the same `I<n>` numbering and the
  same analyze/implement/validate/register/commit protocol. This document
  owns the roadmap and track definitions only; it must not become a second
  ledger.
- Critical phases (DTO family conversions, substrate extraction, C++ target
  splits) receive one independent review before landing, per the owner
  decision recorded at W2. Other iterations land on parity gates alone.
- Every family conversion ships with regeneration freshness gates
  (`tools/maintenance/dto_schema/generate.py --check`) and, where behavior
  could drift, embedded-reference parity tests in the I8/I19 style.

## Design Principles

The program optimizes for long-horizon maintainability over short-term line
counts. Concretely:

1. **Prefer systems over patches.** A schema, generator, registry, or
   substrate that owns a whole class of change is preferred over one-off
   deduplication, even when its upfront line cost is higher. Net line
   increases are acceptable when they buy a single owner (the I18/I20
   precedent) and must be recorded honestly in the ledger.
2. **Every consolidation ships its extension contract.** A track item is
   not complete until the next consumer's path is documented and gated:
   how the next DTO field, domain slice, training line, probe, or config
   variant plugs in through registered extension points rather than by
   copying an existing implementation.
3. **Domain symmetry is an extension socket, not dead weight.** The thin
   naval/ground slices mirror the air slice deliberately. T1 command-family
   and T3 loader work must formalize per-domain registration (schema
   groups, profile adapters, taxonomy entries) so a future domain attaches
   by registration, not by editing air-specific code.
4. **Build so the C++ takeover shrinks Python.** Nothing in the Python
   substrate may ossify logic that the exact-runtime mainline (WP4/WP5)
   is scheduled to own; generated builders and plugins must be deletable
   per family once C++ ownership lands.
5. **Reversibility and audit.** Generated artifacts stay in-tree with
   freshness gates; every architectural move keeps a compatibility shell
   until the final residual audit retires it deliberately.

## Performance Boundary

Performance optimization itself stays owned by the exact-runtime mainline
([plan](../exact_runtime/cpp_exact_runtime_refactor_plan.md)) and the
architecture/performance research line; it is intentionally not a track of
this program. The program delivers performance *enablers* and must not
foreclose them: the DTO schema layer must be able to emit alternative
layouts (for example SoA or packed device views for the future
`ExactStateStore`) from the same field source; substrate unification must
leave exactly one hot stepping loop to optimize; and the T3 target split
must produce link units that profiling and backend work can iterate on in
isolation. Any measured-performance work item discovered during the program
is routed to the exact-runtime line instead of widening this program.

## Global Structure: Load-Bearing Invariants

Local consolidation without a stated global structure risks manufacturing
hub coupling ("shared" owners that everyone depends on). The program is
therefore governed by six global invariants; a local work item that serves
none of them is dropped by default.

- **G1 Two worlds, one contract.** The system is exactly a Simulation World
  (C++ owns truth and time) and an Experiment World (Python owns
  composition: scenarios, training, evaluation, diagnostics). One boundary
  contract exists between them (facade plus schema-generated DTO
  vocabulary). The number of cross-boundary paths is an architecture
  health metric and its target value is one.
- **G2 One-way layer rings.** Python: contracts -> substrate -> domain
  semantics -> experiment orchestration. C++: contracts -> engine ->
  mission -> facade. Shared needs sink downward, never sideways.
  Anti-hub clauses: neutral layers must be dependency-terminal, substrates
  stage-local, owners single-purpose.
- **G3 Monotone state-ownership topology.** Every piece of state has
  exactly one owner, and ownership only migrates toward the kernel
  (exact-runtime direction). The ownership map is a maintained artifact
  (T0 census output), not folklore.
- **G4 Information-state layering is the one cross-boundary semantic
  invariant.** Every observation/reward consumer names its layer
  (Truth/Sensed/Track/Picture/Observation/Belief); enforcement moves from
  documentation to gates.
- **G5 Extension is registration.** Domains, modes, probes, and configs
  attach through declared sockets; an extension that requires editing
  shared code is by definition a design defect.
- **G6 Representations are projections of descriptions.** Cross-boundary
  shapes are generated from schemas. This is the precondition for G4's
  provenance-rich layering not collapsing into hand-written plumbing.

## Baseline Critique And Proposed Amendments

The SCAL baseline is adopted as target ontology with an explicit critique.
Strengths: the information-state layering, the causal-temporal split with
versioned feedback, and capability composition. Deficiencies this program
records and routes: (1) the seven graphs are taxonomy without composition
mechanics — only the temporal DAG has runtime reality; (2) intent is
enforced by review culture instead of a small constructively-enforced
kernel invariant set (G1-G6 are that compression); (3) the linear P0-P10
vocabulary is in tension with multi-rate, event-driven sub-pipelines and
must become stage contracts with declared sub-graphs; (4) the Learning
face is shallow while the repository's churn concentrates exactly there;
(5) an Experiment face is missing — scenario x config x seeds x curriculum
x evaluation protocol has no first-class home, and the config-matrix
sprawl is the direct symptom; (6) the rich epistemic ontology lacks a
paired representation strategy, which G6 supplies. Amendment candidates
(a: Experiment face; b: stage contracts with sub-graphs; c: kernel
invariant list; d: representation-strategy section) are proposed to the
baseline's own governance rather than edited into it by this program.

## Systemic Alignment: SCAL Conformance

The engineering tracks below are necessary but not sufficient. The repository
already owns a conceptual architecture baseline —
[Simulation System Architecture Design](../architecture/simulation_system_architecture_design.md)
(SCAL faces, graph-of-graphs, the six information-state layers, the canonical
`P0-P10` semantic lifecycle, the causal-temporal execution model, and
capability-composition domain extension) — and the maintained code does not
yet structurally embody it. Known conformance gaps include: the scenario
loader concentrating several lifecycle stages in one object; observation
modes split between compiled-core and Python adapters without a declared
`ObservationViewSpec` boundary; `MissionCommand` existing as five
representations instead of one typed contract vocabulary; and
`spawn_unit(type_name)` not yet expanding to typed capability bundles.

This program therefore treats the baseline as its target ontology, not just
its background reading:

- **T0 (new): semantic-lifecycle and information-state conformance.** Produce
  a stage-conformance census that maps every maintained runtime function to
  its `P0-P10` stage and information-state layer, register each violation
  (stage-crossing ownership, truth leaks into policy paths, parallel
  lifecycles), and drive the gap register down through the other tracks.
- **T2 reframed:** `WorldBatchCore` is not merely a deduplication vessel; it
  is the maintained Python projection of the staged tick pipeline. Mode
  plugins must be stage-local (agency-graph adapters), and the substrate's
  stage boundaries must match the lifecycle table so WP4 can migrate stages
  to C++ one at a time.
- **T1 anchored:** the command/tasking schema family implements the typed
  contract vocabulary of the Semantic face; schema groups should follow the
  baseline's packet taxonomy rather than inventing a parallel naming.
- **T3 anchored:** domain registration follows the capability-composition
  model (`PlatformFamily`/`SensorFamily`/... extension families), moving
  content loading toward typed capability bundles.

## Program Tracks

| Track | Scope | Primary target | Key risk |
| --- | --- | --- | --- |
| T0 SCAL conformance | Stage-conformance census across the maintained runtime (loader, vec-envs, facade consumers); information-state layer audit of every observation/reward consumer; gap register with per-gap routing into T1-T4 | Code structurally embodies the architecture baseline; no parallel lifecycles | Census requires judgment; gaps must route to tracks, not spawn ad-hoc rewrites |
| T1 DTO single-source completion | world-batch (~211 fields), engagement remainder (~445 fields, 29 classes), command/tasking umbrella-slice-codec family, GPU packed views | Move the remaining ~2,400 manual sync statements into schema ownership | Member order is ABI; JSON codec aliases; partial-exposure views |
| T2 Runtime substrate unification | B-2 residual cycle break (lazy package init or dispatch inversion, plus AST-gate blind-spot fixes), `WorldBatchCore` extraction, execution/cooperative/leader mode plugins, adapter and single/leader runtime collapse | One batch substrate, ~1,400 duplicated lines removed, one-way layering | Monkeypatch seams; shared-memory and leader special paths |
| T3 C++ structural boundaries | `ef_core` split into engine/mission/facade/content link units with include-direction gates; facade result-projection dedup; table-driven `unit_definition_loader` after T1 proves codec escape hatches | Enforced layer boundaries; loader's 1,881-line hand mapping owned by schema | Link order and initialization; NaN-sentinel config semantics |
| T4 Exact-runtime alignment | Support WP4 hot-path switchover to `WorldBatchRuntime`; retire Python per-step builders superseded by C++ ownership; re-freeze the exact-runtime plan document | Python stepping layer thins instead of ossifying | Divergent double-ownership during migration |
| T5 Declarative configuration completion | Training-config bases+deltas generator with freshness gate (24-file air-combat matrix first), opt-in report envelope, second argparse batch | Config matrices maintained as deltas, not copies | Docs-pinned config paths must stay stable |
| T6 Test-infrastructure rationalization | Machine-baseline-red repairs (allowlist path-separator matcher, winsock harness link, GBK probe decoding, weapon-guidance 45-case environment failure), authority-table data extraction retry, wrappers contract cluster | Validation signal-to-noise: zero expected-red entries on this machine | Baseline repairs must not mask real regressions |
| T7 Final residual audit | Two consecutive clean audit passes over the whole program surface; classify every survivor as intentional, held, or uneconomic | Auditable completion per the consolidation stop conditions | Textual absence is not proof; caller/behavior audit required |

## Sequencing And Dependencies

0. T0's census is the program's opening research move (together with three
   supporting investigations: the WP4 interface archaeology between the C++
   episode controller and the Python stepping logic, the domain-asymmetry
   inventory of air-specific leakage in shared paths, and the schema
   escape-hatch survey for the command/content families). Its gap register
   re-freezes the write sets of T1-T4 before their critical phases start.
1. T2.B-2 (residual cycle break) lands before deeper substrate extraction so
   plugin work starts from a one-way layer graph.
2. T1 world-batch family lands before T3 facade projection dedup, which
   consumes the generated packet schemas.
3. T1 command/tasking family exercises the schema escape hatches
   (inheritance registration, JSON aliases, hidden slices) before T3 makes
   `unit_definition_loader` table-driven on the same machinery.
4. T4 follows the T1 families it depends on (episode is done; world-batch
   next) and coordinates with the exact-runtime plan rather than this
   document.
5. T6 baseline repairs may land at any point; earlier is better for gate
   fidelity. T7 runs last, twice.

## Non-Goals

- Documentation compaction and archive normalization (P7) stay out of scope
  per the owner decision; evidence packs remain immutable.
- No runtime reflection layers, no new third-party dependencies, no
  generator participation in the normal CMake build.
- No public Python name, CLI flag, config key, or JSON schema changes
  without an explicit compatibility shell and migration note.

## Related Authority

- [Repository Consolidation Plan](../repository_consolidation/README.md)
  (iteration ledger and protocol)
- [Exact Runtime Refactor Plan](../exact_runtime/cpp_exact_runtime_refactor_plan.md)
- [Document Lifecycle Policy](../../standards/governance/document_lifecycle_policy.md)
- [Agent Document Authority Map](../../agent/rules/document_authority_map.md)
