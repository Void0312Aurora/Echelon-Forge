# ADR: force-package and group composition

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
