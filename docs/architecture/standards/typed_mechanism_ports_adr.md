# ADR: typed mechanism ports and recursive composition

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
