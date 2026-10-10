# ADR: versioned platform blueprints and capability assembly

Language:
- English canonical: `platform_blueprint_assembly_adr.md`
- Chinese companion: [platform_blueprint_assembly_adr.zh.md](platform_blueprint_assembly_adr.zh.md)

Document kind: `standard`
Lifecycle: `proposed`
Canonical: `docs/architecture/standards/platform_blueprint_assembly_adr.md`
Owner: `architecture/content-contracts`
Last verified: `2026-10-10`

**Status:** proposed qualification design; legacy unit JSON and native
materialization remain authoritative.

## Decision

Add an opt-in authoring projection for reusable platform blueprints and
assemblies. Compile it to the existing `UnitDefinition`,
`CapabilityBundle` and `ResolvedPlatformSpawnPlan` contracts; do not replace
the unit database or `DefaultUnitFactory`. The native factory remains the only
owner allowed to materialize ECS entities.

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
and schema-version failures. It must preserve `load_database` and `spawn_unit`
behavior and remain outside the production profile until reviewed.

This ADR does not define arbitrary plugins, a new behavior engine, or a mass
rewrite of existing JSON. Mechanism behavior remains governed by RFC #229 and
the existing provider/model contracts.
