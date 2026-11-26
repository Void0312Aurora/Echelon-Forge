# ADR: force-package and group composition

Language:
- English canonical: `force_package_composition_adr.md`
- Chinese companion: [force_package_composition_adr.zh.md](force_package_composition_adr.zh.md)

Document kind: `standard`
Lifecycle: `proposed`
Canonical: `docs/architecture/standards/force_package_composition_adr.md`
Owner: `architecture/joint-contracts`
Last verified: `2026-11-26`

**Status:** proposed qualification design; existing scenario expansion and
Joint/tasking contracts remain authoritative.

## Decision

Define a reusable versioned force-package authoring projection for unit
assemblies, roles, containment, command relationships and layout. Compile it
to the existing scenario entities and Joint/tasking contracts. Do not make the
generic compiler a second ECS, command or domain-tactics authority.

Package members may reference platform assemblies from the platform blueprint
contract or finite nested packages. Expansion must be a deterministic DAG:
cycles, duplicate scoped IDs, unresolved imports and contradictory side/role
constraints fail before entity creation.

## Separate relationships

Membership/containment, task authority, communications links and dynamic orders
are distinct. Nesting does not grant command authority, radio reachability or
information rights. A shared package schema owns stable IDs, roles, provenance
and generic anchor/layout references; Air, Naval and Ground adapters own
formation, embarked inventory and domain geometry rules.

The existing CSG compiler is retained through an explicit adapter and remains
covered by its regression suite. Generic roles cannot silently absorb
Naval-specific roles such as carrier or escort semantics.

## Bounded proof and gates

The qualification proof should compile one Air formation, one Naval group and
one Ground squad, plus a nested package. Negative fixtures cover cycle,
duplicate ID, missing member, wrong side/role capability, invalid frame and
invalid placement. Compare normalized expansion with existing CSG behavior and
assert no mutation on rejection.

Production activation requires reviewed schema/version ownership, deterministic
identity, native Joint/tasking admission and domain-owner approval. Runtime
orders remain the authority for dynamic group changes.

## Option comparison and implementation checkpoint

| Option | Disposition in this proposed ADR |
| --- | --- |
| Generalize CSG in place | retains geometry/inventory owners but mixes organization into a domain-specific format |
| Organization frontend lowering through scenario/CSG owners | proposed bounded route; placement and commands keep existing owners |
| Separate runtime per force/package family | rejected; creates competing world and placement authorities |

Compiled relationships now survive identity calculation with instance-scoped endpoints. Nested role capabilities and reused package instances are validated; frame, anchor and provenance are retained. The qualification CSG adapter binds explicit entity and assembly maps to each existing compiled group, checks group/entity/inventory metadata, and delegates a fresh fully qualified snapshot to the existing loader. Full named and mirror S0 fixtures preserve native entity positions and replay frames. CSG placement, geodesy and native materialization remain its owners. Executable command/inventory migration remains open; relationships are evidence, not granted authority.

See [qualification evidence and remaining gates](../work/issues/rfc_qualified_composition_implementation.md). Lifecycle remains proposed; this checkpoint does not establish owner approval or production admission.

## Qualification snapshot and digest ownership (Issue #294)

The adapter retains the existing `CsgForcePackageQualification` fields and digest
encodings. A frozen qualification contains scalar values and tuples of scalar
values; the compiled scenario still contains mutable dictionaries. Freezing the
outer dataclass does not protect those dictionaries between qualification and
publication. Publication therefore validates the current inputs before calling
the existing `load_compiled_scenario` exactly once. This is a synchronous
between-phase mutation guard, not authentication of evidence supplied by a caller
or support for concurrent mutation during validation/loading.

| Qualification digest | Owner and covered content | Classification and publication check |
| --- | --- | --- |
| `package_identity_digest` | Generic force-package compiler: schema, package reference, entities (including role, side, assembly and provenance), relationships, package instances (including frame/anchor/provenance), assembly/native-type bindings | Public identity evidence and TOCTOU guard. Check the independently supplied compiled package reference and identity, and recompute its complete v1 identity with `CompiledForcePackage.is_fresh()`. A stored digest alone does not prove that frozen records were not replaced or modified through their dictionaries. |
| `entity_bindings_digest` | CSG adapter: sorted explicit scoped-ID/native-name pairs | Public binding evidence and TOCTOU guard for the qualification's binding table. Recompute once per qualification; also validate ordering, cardinality, uniqueness, projection scope and full CSG entity coverage. It does not independently prove role/type/member correctness. |
| `scenario_digest` | Scenario compiler/CSG adapter: the complete merged scenario, including entity geometry, `csg_member` identities, inventories, metadata and environment | Public snapshot evidence and the complete scenario TOCTOU guard. Compare the current validated digest with the qualified value. After a successful `scenario.is_fresh()`, reuse its identical `semantic_digest`; if absent on legacy output, hash the merged scenario explicitly. A newly compiled changed scenario is fresh but still fails the qualified snapshot comparison. |
| `embarked_inventory_digest` | CSG owner: the selected group's complete embarked inventory | Public domain evidence, derived from a subset already covered by `scenario_digest`. Retain and recompute once per qualification to validate this public field and preserve consumer compatibility; it is not a separate inventory authority. |
| `geometry_digest` | CSG owner: the complete `meta.csg.geometry` projection | Public domain evidence, derived from a subset already covered by `scenario_digest`. Compute once per qualification phase and once per publication call, share with the evidence reference, and retain comparison so changing the evidence field still rejects. |
| `compiled_relationships_digest` | Generic package relationships projected by the adapter, including package ownership | Public relationship evidence, derived from a subset of the package identity. Recompute once per qualification during publication and compare the explicit `relationship_edges` too. These are evidence and grant no command authority. |

`evidence_refs` repeats package, relationship, scenario and geometry identities as
human-readable references. It is a descriptive index, not an additional digest or
admission credential. `entity_binding_projection` and `relationship_edges` are
explicit evidence, not digests; both retain their publication comparisons.

### Repeated-check audit

| Check in qualification and/or publication | Classification and decision |
| --- | --- |
| Scenario freshness, including imported-file mtimes and OOB provenance existence | Necessary TOCTOU validation in both phases. Share validation code but execute it each time; never substitute equality with a remembered digest. |
| Maintained CSG schema, equality of runtime CSG metadata with merged CSG metadata, valid unique group metadata | Necessary validation in both phases. Runtime metadata is a separate mutable projection and is not protected by the merged scenario digest alone. |
| Package DAG, references, side/capabilities, scoped relationships, frame/anchor and native-type binding compilation | Qualification establishes validity. Publication verifies the independently supplied package's complete current identity; it does not re-expand an authoring graph or introduce another compiler/loader. |
| Declared ships versus expanded CSG membership; inventory host existence and integral nonnegative counts | Qualification establishes domain validity. Publication's whole-scenario snapshot comparison protects these exact validated values; binding coverage also remains checked directly. No domain rule is removed. |
| Explicit binding scope, uniqueness, assembly type, role and side projection | Necessary admission checks. Qualification establishes the projection; publication checks it against both the independently compiled package and the current CSG entities, retaining member-reference and native-type checks. Build the native-type lookup once per qualification. |
| Complete group qualification and exact compiled-package scope | Publication-only admission checks, retained before loader invocation. Missing/duplicate groups and extra/missing package identities reject. |
| Re-hash merged scenario immediately after `is_fresh()` hashed the same canonical payload | Redundant derivation for compiler output with a semantic digest; reuse only after successful freshness validation. Keep explicit hashing when the semantic digest is empty. |
| Re-hash geometry to format its `evidence_refs` entry | Redundant derivation; reuse the already computed geometry digest. |
| Fetch and check the same compiled package reference/identity/relationship digest twice inside one publication loop | Redundant within one synchronous validation pass; combine into one block with complete package freshness and explicit edge comparison. |

The v1 package identity JSON encoding and all qualification digest values remain
compatible. `CompiledForcePackage.as_dict()` exports detached record dictionaries
so editing exported evidence cannot mutate compiled entities, relationships or
package instances. The native CSG loader, geometry/geodesy, inventories, replay
and Joint/tasking admission keep their existing owners.

Negative fixtures cover geometry and guide coordinates, inventory count/type/host,
role and side, entity/member/group binding and membership, package graph/frame/
anchor/provenance/native-type drift, and scenario metadata/environment. Scenario
mutations are exercised in place, with an empty semantic digest and coherent
runtime CSG metadata, and as newly compiled fresh replacements. Every rejection
must occur before a recording loader is called. Each public digest also has a
tamper fixture, and dependency freshness is checked at both phases. Named and
mirror S0 scenarios compare full native replay frames at two seeds; nested
packages also compare native metadata and replay with the maintained path.
