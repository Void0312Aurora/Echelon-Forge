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

## Program Tracks

| Track | Scope | Primary target | Key risk |
| --- | --- | --- | --- |
| T1 DTO single-source completion | world-batch (~211 fields), engagement remainder (~445 fields, 29 classes), command/tasking umbrella-slice-codec family, GPU packed views | Move the remaining ~2,400 manual sync statements into schema ownership | Member order is ABI; JSON codec aliases; partial-exposure views |
| T2 Runtime substrate unification | B-2 residual cycle break (lazy package init or dispatch inversion, plus AST-gate blind-spot fixes), `WorldBatchCore` extraction, execution/cooperative/leader mode plugins, adapter and single/leader runtime collapse | One batch substrate, ~1,400 duplicated lines removed, one-way layering | Monkeypatch seams; shared-memory and leader special paths |
| T3 C++ structural boundaries | `ef_core` split into engine/mission/facade/content link units with include-direction gates; facade result-projection dedup; table-driven `unit_definition_loader` after T1 proves codec escape hatches | Enforced layer boundaries; loader's 1,881-line hand mapping owned by schema | Link order and initialization; NaN-sentinel config semantics |
| T4 Exact-runtime alignment | Support WP4 hot-path switchover to `WorldBatchRuntime`; retire Python per-step builders superseded by C++ ownership; re-freeze the exact-runtime plan document | Python stepping layer thins instead of ossifying | Divergent double-ownership during migration |
| T5 Declarative configuration completion | Training-config bases+deltas generator with freshness gate (24-file air-combat matrix first), opt-in report envelope, second argparse batch | Config matrices maintained as deltas, not copies | Docs-pinned config paths must stay stable |
| T6 Test-infrastructure rationalization | Machine-baseline-red repairs (allowlist path-separator matcher, winsock harness link, GBK probe decoding, weapon-guidance 45-case environment failure), authority-table data extraction retry, wrappers contract cluster | Validation signal-to-noise: zero expected-red entries on this machine | Baseline repairs must not mask real regressions |
| T7 Final residual audit | Two consecutive clean audit passes over the whole program surface; classify every survivor as intentional, held, or uneconomic | Auditable completion per the consolidation stop conditions | Textual absence is not proof; caller/behavior audit required |

## Sequencing And Dependencies

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
