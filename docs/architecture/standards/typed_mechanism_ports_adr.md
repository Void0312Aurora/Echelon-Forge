# ADR: typed mechanism ports and recursive composition

Language:
- English canonical: `typed_mechanism_ports_adr.md`
- Chinese companion: [typed_mechanism_ports_adr.zh.md](typed_mechanism_ports_adr.zh.md)

Document kind: `standard`
Lifecycle: `proposed`
Canonical: `docs/architecture/standards/typed_mechanism_ports_adr.md`
Owner: `architecture/mechanism-contracts`
Last verified: `2026-11-26`

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
barrier; a delayed edge names a positive delay window and its source node as
the state owner, whose declared state window covers that edge. These checks
do not prove numerical calibration or timestep invariance.

## Compatibility and recursion

Connections require compatible schema versions, units, frames, freshness and
visibility. When an owner supplies a schema vocabulary, unknown port schemas
are rejected before publication. The vocabulary is an immutable, versioned
qualification artifact: each schema entry names its owner reference, and the
vocabulary digest participates in the graph identity. Explicit conversion or
estimation nodes are required when a connection would otherwise fabricate
information. Instantaneous same-window cycles are rejected; delayed/stateful
feedback must declare its positive edge delay and source-owned state boundary.
A composite preserves the maximum declared node/edge delay window and exports a typed
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
Multiple owner vocabularies may be combined into a versioned qualification
registry. Duplicate schema entries are accepted only when they name the same
owner; conflicting ownership fails closed. The registry is a composition seam
for explicit owner evidence, not the repository-wide canonical packet
vocabulary or an executable dispatcher.

## Ownership and retention audit (#292)

The Cordis admitted catalog lock owns descriptor admission: `descriptor_id`,
`owner_id`, category authorities, capabilities, implementation/version,
provenance and trust decision. Its `lock_id`, `lock_version`, contract/schema
versions, request/authority bindings, canonical bytes and `lock_sha256` remain
owned by the existing native composition contracts. The lock does not define
the Air pilot's port schema labels or their units, frames and sampling semantics.
Native `StageNodeManifest` owns stage packet names, shards and publication
policies; packet names alone do not define typed port compatibility. Neither
the vocabulary nor the qualification projection replaces either native owner.

| Qualification type and every field | Semantic owner and retention decision |
| --- | --- |
| `MechanismSchemaVocabulary.vocabulary_id`, `version` | Owner-supplied compiler namespace/revision; retain because these identify port evidence independently of catalog lock and implementation versions. |
| `MechanismSchemaVocabulary.entries` (`schema`, `owner_ref`) | Explicit owner declarations for port labels and implementation references; retain. `owner_ref` is not a Cordis admission or trust decision. `schema_names` is a derived membership view. |
| `MechanismSchemaVocabulary.identity_digest` | Derived frontend qualification evidence; retain its existing payload and bytes, without applying it to native canonicalization. |
| `MechanismSchemaVocabularyRegistry.registry_id`, `version`, `vocabularies` | Compiler input view selecting explicit owner vocabularies, **not a separately persisted artifact or catalog lock**. Retain source identities/revisions, sorted by vocabulary ID. `vocabulary_id` is a compiler interface alias for `registry_id`. |
| `MechanismSchemaVocabularyRegistry.entries`, `schema_names`, `identity_digest` | Derive the merged membership from source vocabularies, without a stored shadow entry tuple. Shared schema names require identical owners; conflicting owners fail at construction. Preserve the existing serialized `entries` view and digest for compatibility. |
| `NativeStageContractProjection.node_id`, `authored_node` | Frontend binding and typed authoring evidence: mechanism/version, ports, statefulness, clock/delay, implementation, capabilities, backend and clock policy. Retain separately from the native owner contract. Parameters remain bound by `graph_identity_digest`. |
| `NativeStageContractProjection.owner_contract` | Detached, frozen native snapshot; retain all selected manifest values verbatim. Never synthesize an owner manifest from authored ports. |
| `NativeStageContractProjection.stage_node_id`, `owner_module` | Derive from `owner_contract.node_id` and `.owner_module`; remove independent storage. Retain the serialized aliases to avoid changing existing qualification hashes. |
| `NativeStageContractProjection.identity_digest` | Derive from the existing serialized binding payload; remove independent storage so it cannot disagree with its frozen owner contract. |
| `StageManifestQualificationProjection.graph_identity_digest` | Retain the authored graph identity, including parameters, port semantics, vocabulary revisions and edges. It is distinct from the owner snapshot identity. |
| `StageManifestQualificationProjection.manifest_registry_digest` | Retain the existing digest of **bound** snapshots in graph-node order, including their versioned node IDs. This is not a hash of the entire runtime registry or a catalog lock. |
| `StageManifestQualificationProjection.node_contracts`, `edge_bindings` | Retain node-to-owner evidence and authored edges, including delayed edge windows/state owners. A native manifest does not own authored graph connectivity. |
| `StageManifestQualificationProjection.identity_digest` | Retain the existing combined qualification identity; no replacement for requested/resolved composition hashes. |
| `StageManifestQualificationProjection.qualification_only`, `executable` | Retain explicit `true`/`false` evidence markers; they grant no scheduler admission. |

The frozen owner contract retains `node_id`, `semantic_stage`, `owner_module`,
`input_packets`, `output_packets`, `read_state_shards`, `write_state_shards`,
`read_snapshot_policy`, `write_commit_policy`, `clock_domain`, `latency_policy`,
`sync_policy`, `allowed_same_window_edges`, `required_barriers`,
`event_families_emitted`, `diagnostic_trace_obligations`, `facade_visibility`
and `adapter_projection_allowed`. Optional legacy `native_system` remains
supplemental realized-order evidence; native manifests do not declare it.
Snapshot validation and hashing consume the same detached values. Strict
field/shape, publish-barrier and event checks remain necessary for caller-supplied
mapping fixtures: the Python binding does not expose the native validator.
Binding coverage, versioned node identity, writer conflicts and realized order
checks validate the authored selection, which the catalog lock does not cover.

Port freshness/visibility and authored numerical/publication clocks remain
distinct from manifest read/commit, latency and facade visibility policies.
None can be inferred from another or removed as a duplicate. The native
manifest has no separate version counter: its versioned `node_id` and complete
snapshot content must both remain in qualification digests. Callers reusing
qualification evidence can supply `expected_manifest_registry_digest` from
their expected snapshot; a different snapshot fails with
`mechanism.native_stage_manifest_stale`, including policy changes under an
unchanged node ID. Without an expected digest, projection qualifies only the
supplied snapshot and makes no claim that it is the current runtime registry.

Regression tests pin pre-change vocabulary, graph, node, manifest and projection
digests, plus the existing Air seeker fixture and recursive composite identity.
The native integration test binds an Air launch-to-observation graph to real
`fire_control_launch.v1` and `observation_export.v1` runtime snapshots. The
three seeker helper functions remain a bounded typed composition proof; the
native registry does not publish individual scheduler manifests for them.
No schema, implementation, manifest or canonicalization version is bumped.

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
