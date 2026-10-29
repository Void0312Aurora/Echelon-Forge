# ADR: versioned platform blueprints and capability assembly

Language:
- English canonical: `platform_blueprint_assembly_adr.md`
- Chinese companion: [platform_blueprint_assembly_adr.zh.md](platform_blueprint_assembly_adr.zh.md)

Document kind: `standard`
Lifecycle: `proposed`
Canonical: `docs/architecture/standards/platform_blueprint_assembly_adr.md`
Owner: `architecture/content-contracts`
Last verified: `2026-10-29`

**Status:** proposed qualification design; legacy unit JSON and native
materialization remain authoritative.

## Decision

Add an opt-in authoring projection for reusable platform blueprints and
assemblies. Compile it to the existing `UnitDefinition`,
`CapabilityBundle` and `ResolvedPlatformSpawnPlan` contracts; the bounded
`platform_blueprint_adapter` may project a resolved qualification plan into the maintained
`TypedPlatformSpawnRequest` shape only when it is bound to an unchanged legacy
`UnitDefinition` snapshot. A plan that changes module bindings or overrides must
first use the existing legacy lowering and loader path. Do not replace the unit database or
`DefaultUnitFactory`. The native factory remains the only owner allowed to
materialize ECS entities.

The logical artifacts are deliberately separate:

- research/equipment evidence, which never becomes spawnable automatically;
- versioned module definitions with stable IDs, units and capability family;
- a platform blueprint with typed slots and structural constraints;
- an assembly containing explicit module selections and allowlisted overrides;
- a scenario instance; and
- a canonical resolved spawn plan consumed by native admission/materialization.

## Validation and identity

Validation is layered and fail-closed before publication: shape and schema
version, stable reference kind/version, existence and dependency closure, slot
cardinality, unit/physical bounds, capability compatibility, evidence status,
and native plan validation. Diagnostics use stable `code + path + reference`
fields. Unknown required references, duplicate slots, unsupported required
capabilities and illegal overrides reject without mutation.

Assembly identity is canonicalized from logical IDs, schema versions,
resolved references and typed override values. File paths and traversal order
are never semantic identity. Existing legacy content is handled by an explicit
adapter; missing optional defaults are recorded in evidence rather than
silently invented.

## Bounded proof

The qualification prototype should lower one existing Air platform and one
Naval or Ground platform, compare the generated native plan with current
content, and exercise unknown reference, wrong family, duplicate slot, unit
and schema-version failures. The bounded typed adapter now covers an Air
assembly: slot cardinality, module digest/native-reference identity and native
capability-family checks happen before DTO publication; the existing native
validator also rejects source, bundle and resolved-capability drift. The
request is then materialized by `RuntimeFacade` and the existing factory, with
observation parity against `WorldSpawnRequest`. It must preserve
`load_database` and `spawn_unit` behavior and remain outside the production
profile until reviewed.

This ADR does not define arbitrary plugins, a new behavior engine, or a mass
rewrite of existing JSON. Mechanism behavior remains governed by RFC #229 and
the existing provider/model contracts.

## Option comparison and implementation checkpoint

| Option | Disposition in this proposed ADR |
| --- | --- |
| Add all blueprint fields to UnitDefinition | keeps the loader owner but widens a legacy flat record |
| Explicit typed authoring projection to existing content | proposed bounded route; native factory still materializes entities |
| Load research/template documents directly | rejected; draft evidence is not admitted executable content |

The prototype records module parameter digests and native references, applies finite numeric bounds, and explicitly maps selections to existing UnitDefinition fields. Bounded mass, power-budget and slot-mount checks reject incompatible assemblies before publication. Explicit hardpoint contracts and loadout selections validate mount class, allowed module kind, quantity, capacity, physical metadata and native identity; these values are included in the canonical plan identity. Legacy lowering requires a declared loadout path and matching evidence, so a selected loadout cannot disappear during projection. `UnitDefinition::default_loadout` retains the legacy one-string form and also accepts an ordered string array for multiple stores on a station. Native factory admission checks each reference and missile type and rejects empty arrays, invalid station capacity, invalid store mass, and summed store mass above the hardpoint capacity. Materialization preserves deterministic order, assigns stable child names to extra stores, and resolves each released store back to its indexed weapon definition. F-16's two AIM-120C-7 stores now use 300 kg stations 2 and 8; the two AIM-9X stores remain on 150 kg wingtip rails. The authored-content census leaves Su-35 unresolved because two R-73 references do not resolve and its 190 kg R-77-1 stores exceed the 150 kg wingtip capacities. The typed bridge preserves selection quantity in the native projection and request identity, binds the full legacy definition digest into its IDs, and rejects a plan whose lowering would change that snapshot. It also uses a versioned qualification mapping from authored capability keys to the native capability-family vocabulary, records that mapping digest in the typed request identity, and rejects unknown keys before DTO publication. It compares the shared source type and capability semantics with a plan returned by the native factory; family, capability type, implementation reference, and required/supported flags must match. `WorldBatchRuntime` now exposes that factory-resolved plan through a read-only query for qualification diagnostics; the factory remains the only materialization owner. The database-backed F-16 factory plan is explicitly queried, and a partial authored mapping is rejected before typed DTO publication. Policy admission binds the maintained observation view identity/version before model context publication. F-16 and Ground infantry loader/factory observation parity is exercised at setup and after four steps. Owner-approved mapping, rollback behavior, broader native unit compatibility and production review remain open.

See [qualification evidence and remaining gates](../work/issues/rfc_qualified_composition_implementation.md). Lifecycle remains proposed; this checkpoint does not establish owner approval or production admission.
