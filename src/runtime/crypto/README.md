# `src/runtime/crypto` Boundary

`src/runtime/crypto` owns dependency-neutral byte hashing primitives used by
runtime composition, contract, host, and diagnostic code. The SHA-256 helper
here provides mechanics only; callers retain canonical serialization, domain
separation, versioning, and public contract ownership.

## Allowed

- Standard-library-only hashing and hexadecimal encoding helpers.
- Runtime owners that need byte hashing for identities, projections, or
  candidate evidence.
- Tests and diagnostics that verify the shared primitive.

## Forbidden

- Runtime state, ECS registration, provider lifecycle, or backend ownership.
- Domain-specific canonicalization or public identity policy.
- Includes from other project groups; this is a neutral leaf.

## Dependency Direction

`runtime/crypto` is a leaf group. Runtime composition, contracts, facade,
host, providers, bindings, GPU helpers, tools, and tests may consume it where
their existing ownership contract permits; the crypto helper must not consume
those groups in return.