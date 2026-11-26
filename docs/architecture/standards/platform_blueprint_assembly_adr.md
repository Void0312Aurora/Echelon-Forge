# ADR: versioned platform blueprints and capability assembly

Language:
- English canonical: `platform_blueprint_assembly_adr.md`
- Chinese companion: [platform_blueprint_assembly_adr.zh.md](platform_blueprint_assembly_adr.zh.md)

Document kind: `standard`
Lifecycle: `proposed`
Canonical: `docs/architecture/standards/platform_blueprint_assembly_adr.md`
Owner: `architecture/content-contracts`
Last verified: `2026-11-26`

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

## Issue #293: consumers, owners and redundant bridge work

The F-16 and Ground paths share this ownership chain:

1. Authored `PlatformBlueprint`, module records, selections and overrides enter
   `platform_blueprint.resolve_platform_assembly`. This owner checks structural,
   capability, physical and override contracts and creates the canonical plan.
2. `LegacyUnitProjection` binds explicit fields to an immutable source snapshot.
   `lower_to_legacy_unit_definition` remains the compatibility export for changed
   assemblies and versioned legacy JSON imports through `UnitDefinitionLoader`.
3. `platform_blueprint_adapter.to_expanded_typed_platform_request` binds the plan
   to that source snapshot and the capability vocabulary. It emits plain content
   DTOs owned by `capability_bundles.registry`; it cannot change a loaded unit.
4. `capability_bundles.bindings_adapter` constructs the native DTO tree.
   `RuntimeFacade.apply_world_setup` admits the typed setup; the existing
   `DefaultUnitFactory` resolves and materializes the loaded `UnitDefinition`.

| Consumer / owner inventory | Classification and disposition |
| --- | --- |
| `platform_blueprint.py`: authored assembly resolver | Retained boundary: unknown references, duplicate slots/hardpoints, capability closure, bounds, mounts and overrides must be checked before publication. |
| `platform_blueprint_adapter.py`: second assembly resolution | Duplicate for a resolver-owned plan with a matching current digest; retired on that path. Direct construction and `dataclasses.replace` copies carry no resolver seal and retain complete resolution and public-plan equality checks. |
| Resolver seal / current blueprint and selected module owners | Retained boundary: digest covers every public plan field, complete blueprint contract and selected module records, including evidence and per-module capabilities. Current values are rehashed on every bridge call, detecting stale owners and in-place mutation. The private seal is excluded from constructor, equality and `as_dict`; the public v1 identity algorithm is unchanged. |
| Typed bridge: lower a full legacy copy, thaw a second copy, compare, serialize | Duplicate projection: replaced by shared mapped-field checks against the frozen snapshot and its construction-time JSON digest. The bridge never thaws or exports a full snapshot. Replacing the snapshot object rejects the cached identity. |
| `LegacyUnitProjection` and shared field checker | Retained boundary: blueprint version, explicit slot/override/loadout paths, module evidence/native identity/physical values and source name/type. The source is recursively frozen and path lists are copied to tuples; unprojected fields still affect the full snapshot digest. |
| Capability vocabulary and `validate_factory_resolved_capability_plan` | Retained boundary: unknown capability keys, mapping identity, factory source/admission and complete capability semantics. Capability metadata is not executable behavior. |
| `capability_bundles.bindings_adapter.py` / native typed validator | Retained boundary: native DTO construction and native admission remain with their current owners. |
| `UnitDefinitionLoader`, `DefaultUnitFactory`, `RuntimeFacade` | Retained boundary: JSON import, reference resolution, station capacity and store mass validation, sole ECS materialization and runtime state. No second unit factory is introduced. |
| `python/content/unit_loadout.py` | Retained read consumer of authored legacy JSON; it does not resolve blueprint plans or admit units. |
| `tests/content/test_platform_blueprint*.py` | Resolver/projection failures, frozen snapshot identity, external-plan fallback and canonical-path call-count guards; F-16 and Ground native parity fixtures. |
| `tests/architecture/composition/test_rfc_qualified_composition.py` | Retained qualification consumer: legacy F-16/Ground loader parity, explicit hardpoint projection, partial F-16 capability mapping rejection and typed F-16 observations. |
| `tests/runtime/bindings/test_typed_platform_spawn_bindings.py` | Retained native binding/factory-plan comparison consumer. No production content-side callers beyond the bridge were found. |

The bounded typed bridge rejects hardpoint `quantity != 1` (including boolean
quantities). Legacy JSON export/import continues to preserve both string stores
and ordered store arrays; that compatibility does not widen typed admission.
The earlier checkpoint's typed multi-store statement is superseded by this
explicit bounded contract.

The positive fixtures use `f16c_block50.json` and
`ground_infantry_soldier_mvp.json`. Ignored qualification metadata records the
explicit native capability owner references; stripping that metadata leaves the
authored definition exactly unchanged. F-16 station assignments are explicit
single-store hardpoint selections. Ground retains its authored capability and
movement declarations. The tests compare canonical DTOs with fully revalidated
copies, assert that repeat resolution/lowering/thawing does not occur, and check
unchanged full-definition digest semantics. The native fixtures load the lowered
snapshot through the existing JSON loader, compare complete capability semantics
against the actual factory plan, then compare all public observation fields and
F-16 missile inventory at setup and after each of four steps against legacy
spawning. Negative fixtures cover stale blueprint constraints, owner physical
parameters/evidence/capabilities, direct plan mutation and external-plan errors.

Native parity remains a required execution gate on a host with a local `ef_py`
build. The implementation checkout on Windows has no such build; fixture
presence and passing content tests alone do not establish native execution or
production admission.
