# Cordis Simulation Composition Contract — 2026-08-17

Status: `2026-08-17` P1-B contract baseline and P2-A native realization/identity
repair implemented and validated; production-provider migration remains P2-B.

Language:

- English canonical: `cordis_simulation_composition_contract_20260817.md`
- Chinese companion: [cordis_simulation_composition_contract_20260817.zh.md](cordis_simulation_composition_contract_20260817.zh.md)

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/cordis_simulation_composition_kernel/cordis_simulation_composition_contract_20260817.md`
Owner: `architecture/runtime-composition`
Last verified: `2026-08-17`

Parent: [Cordis Simulation Composition Kernel](README.md)

## Decision

P1-B freezes a host-neutral requested manifest and a deterministic resolved
envelope. Cordis, a native static profile, Python tooling, or a future Node host
may produce the requested JSON shape. Native code remains responsible for
revalidation, capability/stage admission, provider construction, scope
transactions, executable graph realization, and evidence export.

The contract is deliberately split into five artifact classes:

| Artifact | Authority and purpose |
| --- | --- |
| [`simulation_composition_contract.py`](../../../../../tools/maintenance/simulation_composition_contract.py) | executable schema source, normalization rules, stable diagnostics, deterministic graph ordering, and compatibility-fixture generator |
| [`simulation_composition_manifest.v1.schema.json`](../../../../../src/runtime/contracts/composition/simulation_composition_manifest.v1.schema.json) | generated host-neutral transport schema |
| [`resolved_simulation_composition.v1.schema.json`](../../../../../src/runtime/contracts/composition/resolved_simulation_composition.v1.schema.json) | generated closed resolved-envelope transport schema |
| [`simulation_composition_contract.h`](../../../../../src/runtime/contracts/simulation_composition_contract.h) | JSON-library-independent C++ value contract, stable service keys, scopes, versions, and error codes |
| default requested/resolved fixtures | frozen cross-implementation conformance and migration baseline |

The Python executable specification is not a runtime owner. The native
resolver/validator now recomputes the same requested/resolved SHA-256 against
these fixtures and proves diagnostic-code and ordering parity before constructing
any provider.

## Versioned Envelopes

Requested manifest schema:

```text
echelon_forge.simulation_composition_manifest.v1
```

Resolved envelope schema:

```text
echelon_forge.resolved_simulation_composition.v1
```

Resolver contract:

```text
echelon_forge.simulation_composition_resolver.v1
```

The requested manifest contains no self-hash. The resolved envelope carries:

- normalized requested manifest;
- requested-manifest SHA-256;
- dependency-safe provider construction order;
- deterministic system registration order;
- resolver contract version;
- resolved-manifest SHA-256.

The resolved SHA-256 preimage is the resolved envelope with only
`resolved_manifest_sha256` omitted. This avoids an undefined self-referential
hash while keeping every other identity-bearing field covered.

## Requested Manifest Fields

| Field | Rule |
| --- | --- |
| `schema_version` | exact supported schema ID; unknown versions fail before resolution |
| `composition_id` | stable lower-case semantic ID, independent of host/discovery order |
| `contract_versions` | composition, runtime, content, and stage contract versions |
| `requested_profile` | profile ID and version; selecting a profile does not itself grant capabilities |
| `plugins[]` | implementation/version, host support, determinism class, artifact identity, requirements, conflicts, and canonical configuration |
| `providers[]` | scope, offered/required services, capability requirements, conflicts, restart/teardown policy, and explicit ordering dependencies |
| `service_bindings[]` | exact consumer/service/provider edges; implicit last-registration-wins is forbidden |
| `component_contributions[]` | stable component identity and registration identity |
| `system_contributions[]` | registration factory, domain, service/component requirements, stage joins, state shards, barriers, capabilities, conflicts, and graph edges |
| `backend_request` | requested backend profile and provider that offers `runtime.world_batch_backend` |
| `scope_policies[]` | complete application/backend/batch/world/episode hierarchy |
| `reconfiguration_policy` | truth-affecting change rebuilds a scope generation and is forbidden during an active episode |
| `evidence_policy` | mandatory canonicalization, SHA-256, provider-version, graph-hash, and scope-generation evidence |
| `compatibility_claims[]` | explicit temporary migration claims; never implicit fallback authority |

Objects are closed by default: unknown fields are rejected. This forces schema
versioning instead of allowing hosts to add private authority-bearing fields.

## Canonicalization

Canonicalization ID:

```text
echelon_forge.sorted_utf8_json.v1
```

Rules:

1. all strings and object keys are normalized to Unicode NFC;
2. object keys are serialized in ascending Unicode order;
3. JSON is UTF-8 with no insignificant whitespace and no ASCII-only escaping;
4. booleans and `null` use standard JSON literals;
5. numeric values are signed 64-bit integers only;
6. floating-point values are forbidden in v1 configuration; physical decimals
   must use a schema-owned integer unit or a normalized decimal string;
7. entity arrays are sorted by their stable semantic ID;
8. set-like arrays are unique and sorted by UTF-8 byte order;
9. provider and system execution orders are derived by stable topological sort,
   using semantic IDs only to break ties;
10. source-file order, plugin discovery order, map insertion order, filesystem
    paths, process IDs, timestamps, and object addresses are not hash inputs.

The canonical contract remains Unicode NFC. The P2-A native v1 admission
profile currently accepts ASCII strings and object keys only. ASCII is already
NFC, so this is a deterministic subset rather than a second hash language.
Non-ASCII input fails closed until the Python/Cordis producer and native runtime
share one normalization implementation; Cordis producer conformance must not be
claimed for the wider Unicode domain before that gate passes.

The floating-point restriction is intentional. It avoids cross-language number
rendering ambiguity in the foundational contract. A later version may adopt a
separately tested numeric canonicalization standard, but it cannot silently
change v1 hashes.

## Scope And Binding Rules

The fixed scope order is:

```text
application -> backend -> batch -> world -> episode
```

A provider may supply a service to the same scope or a descendant. A child
provider cannot be retained by a parent consumer. Every required provider or
system service has exactly one explicit binding in v1. Collection, reducer,
chain, fallback, or priority semantics require a later explicit contract; v1
does not infer them.

The frozen service-key set covers:

- environment, unit factory, effects, sensor, acoustic, control, and guidance;
- engagement event recorder;
- weapon-release damage bridge and release service;
- world-batch backend;
- composition evidence sink.

These keys name semantic services. They do not expose C++ pointers, Flecs
singletons, Cordis object identities, or binding-language objects.

## Resolution And Failure Semantics

The P1-B executable specification performs the deterministic, resource-free
portion of resolution:

1. reject unsupported schema/contract versions and malformed IDs;
2. reject duplicate plugin/provider/component/system IDs and duplicate set
   entries;
3. validate plugin/provider ownership and stable service keys;
4. require exactly one explicit binding for every required service;
5. verify the selected provider offers the bound service;
6. reject child-to-parent scope capture;
7. reject selected provider/system conflicts;
8. build provider dependency edges from service bindings and explicit
   `after_provider_ids`;
9. build system dependency edges from `after` and `before`;
10. reject dependency cycles with stable diagnostic codes;
11. require the backend provider to offer the semantic backend SPI;
12. validate the complete scope hierarchy and immutable-episode policy;
13. normalize, topologically order, serialize, and hash the result.

Capability admission, semantic-stage ownership, domain maturity, backend
promotion, artifact authenticity, and runtime resource construction are not
granted by this resolver. P2/P3/P4 must join the existing owner contracts and
fail closed before realization.

Stable diagnostic codes are mirrored in C++ and include duplicate IDs, missing
or ambiguous bindings, unknown services, scope capture, provider/system
conflicts and cycles, backend mismatch, invalid policies, and noncanonical
numbers.

## Default Compatibility Profile

The generated default fixture freezes the pre-migration composition inventory:

| Surface | Frozen count |
| --- | ---: |
| built-in plugin descriptors | 1 |
| providers including CPU backend | 11 |
| kernel model/factory providers | 7 |
| kernel service/event providers | 3 |
| component contributions | 82 |
| system contributions | 34 |
| scope policies | 5 |

The 34 system contributions are chained to reproduce the current registration
order. Exact-stage names are attached where a current exact descriptor exists.
Empty semantic-stage/read-write/barrier fields are explicit compatibility gaps,
not proof that those systems need no contract. P3 must fill and validate them
against stage/domain owners before the central registration list can retire.

The requested fixture has a repository-source artifact identity and a null
artifact SHA-256 because P1-B does not build or sign a distributable artifact.
Resolved runtime evidence must replace that with admitted artifact provenance
before external package acceptance.

## Conformance Evidence

The P1-B architecture suite proves:

- generated schema and requested/resolved fixtures are fresh;
- schema objects are closed and host-neutral;
- C++ versions, scopes, service keys, and error codes match the executable
  specification;
- the default fixture exactly tracks the 82 component and 34 system calls in
  `simulation_kernel_systems.cpp`;
- every required service has one explicit scope-safe binding;
- 32 input permutations resolve to identical bytes, hashes, and orders;
- resolved self-hash exclusion is exact;
- a 10-case invalid-manifest matrix fails closed for version, duplicate,
  missing/ambiguous binding, scope capture, conflict, cycle, backend, and number
  violations;
- Draft 2020-12 schema validation accepts the default fixture;
- the C++ value header passes an MSVC C++20 syntax check.

## P1-B Closure And P2 Entry

P1-B passes at the contract boundary. It does not claim a native runtime
resolver, provider construction, rollback, generation-checked handles, system
graph realization, Cordis package, Node host, or behavior parity.

P2-A subsequently implemented these constraints in the isolated
`ef_composition` library:

- native parsing and validation must reproduce the frozen fixtures and stable
  diagnostic codes;
- no runtime resource is created before complete manifest and graph admission;
- scope construction is transactional and disposal reverses the realized
  dependency graph;
- handles carry scope generation and reject stale access;
- successful native realization recomputes and exports the requested/resolved
  hashes using the frozen canonical field rules rather than trusting a producer
  claim or creating a private identity;
- replacement rebuild accepts a newly validated manifest/catalog, preserves the
  old identity on failure, and requires token/generation-safe effect handover;
- the Python executable specification remains a conformance oracle and never
  enters the maintained simulation step path.

This implementation checkpoint does not amend the P1-B hash semantics. It adds
native canonical-byte/hash recomputation, a generated resolved-envelope schema,
typed-scope fail-closed validation, and Python/schema/native parity repairs.
Byte-for-byte Cordis producer conformance, Unicode implementation diversity,
artifact provenance, production provider construction, and behavior parity
remain later gates beginning in P2-B/P2-C1. P2-C0 separately owns the
producer-neutral high-level request and owner-derived catalog-lock contracts;
it does not amend these frozen P1-B low-level fields or hash semantics.
