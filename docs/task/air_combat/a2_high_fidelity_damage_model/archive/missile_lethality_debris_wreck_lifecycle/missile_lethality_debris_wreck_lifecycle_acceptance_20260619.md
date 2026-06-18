# MLF-8 Debris And Wreck Lifecycle — Acceptance Record

Status: `2026-06-19` accepted / archived for the diagnostics-only MLF-8
lifecycle slice. P0 boundary, P1 inventory, P2 lifecycle contract, P3 runtime
representation, P4 diagnostics/facade exposure, P5 focused validation, P6
broader smoke, and P7 archive synchronization are complete.

Chinese companion:
[missile_lethality_debris_wreck_lifecycle_acceptance_20260619.zh.md](missile_lethality_debris_wreck_lifecycle_acceptance_20260619.zh.md).

## Acceptance Scope

This record accepts the bounded MLF-8 slice only. It records lifecycle facts
for detached structural parts and terminal wreck evidence in the maintained
engagement event stream. It does not create first-class debris/wreck entities,
debris physics, reward authority, calibrated lethality, or Pk.

`[x]` = met. `[~]` = intentionally held outside MLF-8.

## MLF-8A: Boundary And Index

- [x] README, task clusters, current status, dispatch queue, inventory,
  lifecycle contract, archive placeholder, and parent navigation exist.
- [x] Parent A2 README and archive registry route MLF-8 as an accepted archived
  diagnostics-only lifecycle evidence packet.
- [x] Air-combat README routes MLF-8 through the local A2 archive registry
  rather than an active planning path.
- [x] Forbidden claims remain listed and refused.

## MLF-8B: Lifecycle Contract

- [x] The base carrier is `LifecycleTransitionEvent`.
- [x] Detached-part lifecycle rows are diagnostics-only and chain-linked to the
  upstream structural event.
- [x] Terminal wreck lifecycle rows are diagnostics-only and require
  chain-linked missile structural/consequence evidence.
- [x] Plain non-missile ground crashes remain outside MLF-8 authority.
- [x] `wreck_entity` remains zero in the accepted base slice.

## MLF-8C: Runtime Representation

- [x] The engagement event recorder/store can record and sort lifecycle
  transition rows.
- [x] Structural breakup writes one bounded detached-part lifecycle row per
  accepted structural event, including multi-axis aggregate cases.
- [x] Terminal wreck helper writes a row only when chain-linked upstream
  structural/consequence evidence exists.
- [x] Repeated ticks do not duplicate already-emitted lifecycle rows.
- [x] No first-class debris or wreck ECS entities are spawned.

## MLF-8D: Diagnostics And Facade

- [x] Facade packets append and sort lifecycle rows with the rest of recent
  engagement evidence.
- [x] Python binding and contract tests include lifecycle transition fields.
- [x] Diagnostics probe rows and snapshots expose lifecycle rows and summaries.
- [x] Diagnostic schema version is updated for the lifecycle projection.

## MLF-8E: Reward And Visibility Boundary

- [x] All accepted MLF-8 lifecycle rows use diagnostics-only visibility.
- [x] Reward ignores diagnostics-only lifecycle rows and does not create a new
  MLF-8 reward term.
- [x] Existing terminal/reward behavior is not neutralized by diagnostics-only
  lifecycle evidence.

## MLF-8F: Validation Evidence

- [x] C++ structural lanes cover no-breakup, single detached part, multi-axis
  detached lifecycle, terminal wreck helper behavior, registered
  GroundContact-before-StructuralFailure same-tick impact/breakup ordering, and
  no duplicate rows.
- [x] Python runtime lanes cover facade, binding, engagement contract,
  diagnostics probe, continuous-rod integration, and reward non-leakage.
- [x] Geometry/edge-case smoke remains green after the MLF-8 branch-specific
  fuze expectation fix.
- [x] Full CTest and broad air-combat/engagement pytest smoke passed before
  archive.

## MLF-8G: Command Evidence

- [x] `ctest --test-dir build-workshop --output-on-failure` -> 6 passed.
- [x] `PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat/weapon_guidance_realism/test_geometry_and_edge_cases.py::GeometryAndEdgeCaseTests::test_live_controlled_geometry_varies_aspect_and_altitude_offset -vv`
  -> 1 passed.
- [x] `PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat/weapon_guidance_realism/test_geometry_and_edge_cases.py`
  -> 11 passed.
- [x] `PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat tests/runtime/engagement`
  -> 386 passed.
- [x] Local markdown-link check over touched MLF-8/A2/air-combat docs passed.
- [x] `git diff --check` passed.

## MLF-8H: Acceptance And Archive

- [x] Current status summarizes implementation evidence and residuals.
- [x] Task clusters and dispatch queue mark P7 complete.
- [x] Parent A2 README, A2 archive README, A2 archive registry, and air-combat
  README statuses are synchronized.
- [x] Physical archive movement completed under the parent A2 local archive.
- [x] The original active path contains only a lightweight pointer.
- [x] MLF-9/MLF-10 residuals remain named.

## Forbidden Claims

- [x] No real-world Pk or statistical lethality trend authority.
- [x] No calibrated debris throw, fragment range, casualty probability, or
  selected TP-21 output authority.
- [x] No weapon-specific or aircraft-specific debris calibration.
- [x] No first-class debris/wreck ECS entity model in the accepted base slice.
- [x] No debris-to-secondary-damage interaction.
- [x] No training reward authority from MLF-8 diagnostics.
- [x] No naval, ground, visual particle, or broader world-debris lifecycle
  authority.
