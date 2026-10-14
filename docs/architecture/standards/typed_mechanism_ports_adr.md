# ADR: typed mechanism ports and recursive composition

Language:
- English canonical: `typed_mechanism_ports_adr.md`
- Chinese companion: [typed_mechanism_ports_adr.zh.md](typed_mechanism_ports_adr.zh.md)

Document kind: `standard`
Lifecycle: `proposed`
Canonical: `docs/architecture/standards/typed_mechanism_ports_adr.md`
Owner: `architecture/mechanism-contracts`
Last verified: `2026-10-11`

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

## Compatibility and recursion

Connections require compatible schema versions, units, frames, freshness and
visibility. Explicit conversion or estimation nodes are required when a
connection would otherwise fabricate information. Instantaneous same-window
cycles are rejected; delayed/stateful feedback must declare its delay and state
owner. A composite exports a typed public port set and state/effect contract,
so it can be validated as a node in a parent graph.

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
layers, clock compatibility and multiple producers. An explicit native-system
mapping is checked against exported realized order. Immutable parameters, backend
reference and clock policy participate in graph/composite identity.

The bounded Air seeker proof uses the maintained native relative-angle-to-LOS,
LOS/range-to-world-position and stateful CV tracker implementations. It distinguishes
window publication from numerical rates per second. A fixed measurement schedule
and four timesteps reach the same four-second horizon within the documented
tolerance. A test-lane child exception after tracker mutation but before outer
packet publication projects an unknown outcome through #251; it proves no rollback.
This does not install authored graphs into native scheduling. Unknown-schema
admission, shard ownership and freshness enforcement remain open.

See [qualification evidence and remaining gates](../work/issues/rfc_qualified_composition_implementation.md). Lifecycle remains proposed; this checkpoint does not establish owner approval or production admission.
