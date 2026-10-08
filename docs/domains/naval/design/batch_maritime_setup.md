# Batch maritime scenario setup

Full scenario setup carries a per-world `WorldMaritimeAssignment` through the
schema-owned `BatchWorldSetupRequest`, backend setup request, and Flecs CPU
runtime. A configured assignment applies sea state, wave heading and wave
period using the same environment model policy as single-world layout setup.
An omitted assignment or `configured=false` clears any previous override,
restoring the per-platform fallback. Plain episode reset remains distinct from
full scenario setup.

Duplicate assignments, invalid world indices and nonfinite configured values
are rejected before setup mutates worlds. Legacy injected Python appliers
cannot carry authored maritime configuration and therefore refuse such scenes.

The request field is additive and optional for callers. Rebuild native bindings
and their consumers together after this DTO/ABI change. Native regression tests
read both the world environment and snapshots exported through the typed facade;
Python tests verify compiled transport for one and multiple worlds and refusal
of the legacy injection path.
