# Environment Systems

Language: English canonical; [Chinese companion](README.zh.md).

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/systems/environment/README.md`
Owner: `systems/environment`
Last verified: `2026-08-08`

This owner covers cross-domain environment manifests, source admission,
generation/catalog contracts, projection payloads, compiler ingestion, and
derived environment products. Ground scenarios supplied the first demand case,
but Ground does not own the shared substrate.

## Current Authority

- [Environment Substrate G0 Closure](reviews/environment_substrate_g0_closure_20260606/README.md):
  accepted review record for the static manifest, deterministic
  generator/catalog, inert projection payload, strict compiler ingestion, and
  metadata-only derived-product slices.
- [Arnis Adapter Phase 1](reviews/arnis_adapter_phase1_20260715/README.md):
  accepted review record for frozen real-geography input, continuous metric
  export, fail-closed CMO import, and offline static-scene derivation.
- [Ground specialization](../../domains/ground/README.md): owner of Ground
  task/status semantics and their current capability boundary.

## G0 And G1 Boundary

The names in the historical work packages refer to different scopes:

- Ground `G0/G1` denotes bounded Ground task/status and static scenario
  maturity. It does not grant shared environment-runtime authority.
- Environment-substrate `G0` is the accepted cross-domain data-contract line.
  It stops before runtime setup application, movement, passability, LOS, cover,
  fires, damage, hydrodynamics, or combat.
- Arnis phase 1 supplies provenance-bearing static inputs and an offline
  preview. It is not an environment-runtime `G1` release.

No environment-runtime `G1` work is authorized by these reviews. A later
runtime package must open under `systems/environment/work/active/` with its own
scope and acceptance evidence.

## Current Implementation Routes

- Manifest and validators: `python/scenario/environment_substrate/`
- Scenario compiler ingestion: `python/scenario/compiler/`
- Arnis tooling: [tools/environment/arnis](../../../tools/environment/arnis/README.md)
- Frozen Arnis fixture:
  `tests/scenario/fixtures/environment_substrate/arnis_bundle_v1/`

The dated reviews preserve their original evidence boundaries. They are not
permission to broaden capability claims or continue old dispatch queues.
