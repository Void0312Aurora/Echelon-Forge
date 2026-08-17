# `src/runtime/composition` Boundary

Status: `2026-08-17` P2-A native lifecycle baseline and independent-review repair
pass implemented and focused-test validated; no engine, provider-family, system,
backend-facade, binding, or Cordis migration is claimed.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

## Purpose

This directory realizes the host-neutral composition values from
[`runtime/contracts`](../contracts/README.md) as an isolated native lifecycle
library. It parses closed JSON envelopes, recomputes requested/resolved identity,
verifies the graph and stable order, freezes a provider catalog, constructs scoped provider
instances transactionally, publishes staged lifecycle effects only at commit,
and tears down in reverse realized dependency order.

The target is `ef_composition`. It deliberately does not link `ef_core`,
`ef_facade`, Flecs, nanobind, Node, or Cordis. Its only implementation-only
dependency is `nlohmann_json` for the native JSON ingestion boundary.

## Lifecycle Model

1. Parse the closed requested or resolved JSON envelope. Missing/extra fields,
   invalid types, floating-point configuration values, and unknown scopes fail
   before factory lookup.
2. Freeze `ProviderCatalog`; registration after freeze is rejected.
3. Recompute and verify requested/resolved SHA-256, stable provider/system
   orders, service bindings, scope capture, conflict/cycle, backend, policy, and
   immutable factory metadata rules.
4. Construct providers in the verified dependency order. A factory must register
   every external side effect immediately through `ILifecycleEffect`.
5. Commit all staged effects only after every provider exists. Any construction
   or effect-commit failure destroys candidate instances and rolls effects back
   in reverse order without publishing a runnable runtime.
6. Freeze the runtime and expose generation-checked `ServiceHandle<T>` values.
7. Rebuild a scope and all descendants as a candidate generation, optionally
   from a newly validated resolved manifest and catalog. Failure keeps the old
   generation and identity live; success performs a no-allocation record/plan
   swap, invalidates old handles, and disposes retired providers in reverse order.
8. Stop is idempotent and invalidates handles, reverses external effects, then
   destroys instances in reverse provider order.

## Handle And Barrier Contract

`ServiceHandle<T>` is non-owning. Consumers retain the handle, not the pointer
returned by `try_get()`. Lifecycle rebuild/stop is permitted only at an already
quiescent governed barrier; it must not race active simulation-stage access.
This matches the parent architecture rule that truth-affecting reconfiguration
occurs at `pre_run`, `world_rebuild`, or `episode_end`, never mid-step.

The handle control block carries provider ID, scope, generation, and an atomic
active bit. It rejects access after successful rebuild or stop. It does not make
an ungoverned raw pointer retained by a caller safe; such retention remains a
forbidden consumer behavior and must be removed during provider migration.
Lifecycle control operations are serialized by the native runtime. The runtime
is move-constructible but deliberately not move-assignable, so a callback cannot
destroy the active implementation through an implicit move assignment.

## Effect Contract

`ILifecycleEffect` represents external publication that ordinary C++ RAII inside
the provider instance cannot reverse by itself.

- `commit()` publishes a staged effect and may fail;
- `rollback()` reverses either staged or committed state and is idempotent;
- `dispose()` performs normal committed teardown and is idempotent;
- `supports_replacement_handover()` is required when old and new generations
  both publish external state; opting in promises token/generation-owned cleanup;
- both terminal methods are `noexcept` so unwinding always completes.

Factories must stage rather than irreversibly publish external state during
`construct()`. A provider that cannot meet this rule is not admissible to this
lifecycle kernel without a separately accepted handover design.

## Public Surface

- `composition_json.h`: closed native JSON ingestion into P1-B value types;
- `composition_identity.h`: shared manifest/resolved canonical-byte SHA-256;
- `provider_catalog.h`: factory catalog, provider/effect interfaces, typed
  generation-checked handles, and construction context;
- `composition_runtime.h`: native validation, realization, service lookup,
  replacement-aware scoped rebuild, immutable identity queries, generation
  queries, and deterministic stop;
- `composition_error.h`: stable native lifecycle error codes and result values.

## Current Evidence And Residuals

The focused C++ suite parses and validates the frozen 11-provider/82-component/
34-system fixture and tests catalog freeze, hash tamper rejection, invalid typed
scope rejection, self-cycle rejection, immutable factory identity, typed service
lookup, failure cleanup order, lifecycle reentrancy, effect-commit failure, full
rollback, replacement-aware scope rebuild, handover admission, stale-handle
rejection, and reverse teardown. The focused executable passes 13 test cases and
286 assertions in both the normal MSVC build and a RelWithDebInfo MSVC
AddressSanitizer build. The architecture contract suite passes 20 tests with one
toolchain-dependent skip.

This baseline recomputes and exposes the P1-B requested/resolved identity using
the same frozen fixtures and canonical field rules; it does not create a private
runtime identity. Artifact provenance/signature verification and byte-for-byte
Cordis producer conformance remain later admission gates. Default model
construction and all simulation behavior remain on the existing path until
later migration clusters supply parity evidence.
