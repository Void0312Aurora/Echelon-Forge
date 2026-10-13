# ADR: typed mechanism ports and recursive composition

Language:
- English canonical: `typed_mechanism_ports_adr.md`
- Chinese companion: [typed_mechanism_ports_adr.zh.md](typed_mechanism_ports_adr.zh.md)

Document kind: `standard`
Lifecycle: `proposed`
Canonical: `docs/architecture/standards/typed_mechanism_ports_adr.md`
Owner: `architecture/mechanism-contracts`
Last verified: `2026-10-12`

**Status:** proposed qualification design; no production activation.

## Decision

Use a separate mechanism-graph authoring layer that compiles into the existing
composition and stage contracts. Do not add a second runtime execution engine
or an untyped `execute(anything)` ABI. Primitive mechanism adapters declare
versioned input/output ports, units, reference frames, clock semantics,
visibility, required capabilities, state ownership and effect obligations.

The compiler validates a graph before provider or world publication. It emits a
canonical, qualification-only graph artifact that is then admitted through the
existing composition requested/resolved artifacts and native execution graph.
The native runtime remains the sole execution authority.

The lowering path has three explicit owners. The authoring node and edge IDs
are canonicalized by this frontend; the existing composition requested/resolved
artifacts carry the qualification identity; `StageNodeManifest` and native
system contributions decide the admitted shards, barriers and realized Flecs
systems. One authored node may lower to several native systems, and a composite
identity never grants execution rights by itself.

## Contract layers

1. **Port schema:** stable mechanism/port IDs, schema major/minor, physical
   units, coordinate frame, timestamp/freshness, truth-vs-belief visibility,
   optionality and explicit adapter policy.
2. **Execution contract:** state shards, read/write ownership, barriers, clock
   domain, latency and effect kind (pure transform, state update or world
   event).
3. **Graph identity:** canonical node/edge order, implementation references,
   parameters and admitted backend/clock policy. The identity is evidence for
   the existing composition owner; it is not a replacement hash authority.
4. **Failure boundary:** child failure reports committed effects and unknown
   state through the existing failure-domain taxonomy. A valid static graph
   does not imply successful dynamic execution or atomic rollback.

The minimum semantic table is: physical unit and frame are checked at the port
edge; per-second values are integrated by the owning stateful model while
per-tick values are explicitly marked; sampling/freshness is part of the port
contract; state writes become visible only at the owning publication/commit
barrier; delayed feedback names its delay window and state owner. These checks
do not prove numerical calibration or timestep invariance.

## Compatibility and recursion

Connections require compatible schema versions, units, frames, freshness and
visibility. When an owner supplies a schema vocabulary, unknown port schemas
are rejected before publication. The vocabulary is an immutable, versioned
qualification artifact: each schema entry names its owner reference, and the
vocabulary digest participates in the graph identity. Explicit conversion or
estimation nodes are required when a connection would otherwise fabricate
information. Instantaneous same-window cycles are rejected; delayed/stateful
feedback must declare its delay and state owner. A composite exports a typed
public port set and state/effect contract, so it can be validated as a node in
a parent graph.

The first proof should use two primitive adapters and one stateful adapter in a
qualification lane. It must include one compatible edge, one unit/frame or
schema mismatch, one forbidden cycle, one child fault, and one recursive
composite. Existing `builtin.default_compatibility` behavior and facade/Cordis
parity remain unchanged.

## Alternatives rejected

- Extending `Provider` handles alone does not express producer/consumer schema,
  units or information provenance.
- A second executable graph would create competing scheduling and failure
  authorities.
- Treating stage `after` declarations as realized Flecs phases would overclaim
  scheduler guarantees; compare against the existing realized topology
  evidence instead.

## Follow-up gates

Implementation issues may be opened only after this design is reviewed. Any
prototype must remain qualification-only, fail before publication on invalid
graphs, and reuse the existing composition identity, stage manifest and
failure-domain ownership.

## Option comparison and implementation checkpoint

| Option | Disposition in this proposed ADR |
| --- | --- |
| Extend native Provider/stage contracts directly | requires owner review for port/schema and shard admission |
| Non-executing typed frontend compiled to existing owners | proposed qualification route; does not realize a new scheduler |
| Independent execution graph/runtime | rejected because scheduling and world truth would have competing owners |

The prototype checks complete recursive input closure, capabilities, information
layers, clock compatibility and multiple producers. A qualification adapter now
consumes an owner-provided `StageNodeManifest` snapshot, requires one-to-one
node bindings and rejects adapter/diagnostic-only stages before checking the
explicit native-system mapping against exported realized order. The native
`WorldBatchRuntime` also exposes a read-only copy of the maintained manifest
registry for qualification diagnostics; it does not install or mutate scheduler
nodes. Immutable
parameters, backend reference and clock policy participate in graph/composite
identity. Strict stage admission additionally requires the owner contract fields
and rejects duplicate state-shard writers; the default qualification mode remains
compatible with the smaller evidence fixtures. A separate static projection
records each authored-node binding, the owner contract snapshot and stable graph,
registry and edge digests. It consumes the native snapshot object shape directly;
an optional realized-system name is only supplemental order evidence. The
projection is marked non-executable and rejects invalid, duplicate,
adapter-only and diagnostics-only bindings.

This remains a static mechanism-graph contract pilot. Qualification/shadow
compilation and production admission are separate gates; an artifact emitted
through the existing manifest machinery is not automatically executable.

The bounded Air seeker proof uses the maintained native relative-angle-to-LOS,
LOS/range-to-world-position and stateful CV tracker implementations. It distinguishes
window publication from numerical rates per second. A fixed measurement schedule
and four timesteps reach the same four-second horizon within the documented
tolerance. A test-lane child exception after tracker mutation but before outer
packet publication projects an unknown outcome through #251; it proves no rollback.
The selected Air lane now enforces an explicit, versioned six-schema
qualification vocabulary while compiling; every entry names one of the three
maintained native implementations and the resulting vocabulary digest is
bound into the graph identity. This is a bounded owner mapping, not a
repository-wide packet vocabulary.
The snapshot publication seam is diagnostic only and does not install authored
graphs into native scheduling. Cross-domain schema selection and authored-graph
admission remain separate gates.

See [qualification evidence and remaining gates](../work/issues/rfc_qualified_composition_implementation.md). Lifecycle remains proposed; this checkpoint does not establish owner approval or production admission.
