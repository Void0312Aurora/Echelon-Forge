# Environment Substrate Arnis Adapter

Status: phase 1 implemented and locally accepted on `2026-07-15`.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

This package is a separate follow-on to the closed environment-substrate G0
line. Arnis is used as the real-geography acquisition and semantic-processing
frontend; neither a Minecraft world nor its block coordinates are treated as
the CMO terrain format. The data path is:

```text
frozen OSM JSON + fixed bbox + pinned Arnis patch
  -> pre-render continuous metric arnis_cmo_bundle.v1
  -> CMO EnvironmentManifest + elevation-anchor admission
  -> offline cmo.static_scene_geometry.v1 derivation and preview
```

## Phase 1 Deliverables

- pinned Arnis `v3.0.0` / commit
  `af521c99124b5e07ecba018ea54f2ac47b6441d5` plus the CMO exporter patch;
- a separate `arnis-cmo` install that does not replace upstream `arnis`;
- a local-ENU continuous metric bundle containing pre-Minecraft elevation,
  categorical WorldCover, and floating-point roads, buildings, and hydrology;
- a fail-closed CMO importer with dedicated catalogs, provenance, and checksum
  validation;
- root/artifact/feature/measurement continuous lineage plus an exporter patch
  SHA allowlist;
- fail-closed `elevation_anchor` components for rigid terrain-based buildings,
  DEM-draped roads, elevated profiles, subsurface profiles, and water-surface
  preview placement;
- a frozen Chicago River fixture with per-file SHA-256 values;
- one maintained `prepare / export / verify` tool entrypoint plus an explicitly
  non-runtime continuous-field and static-scene preview.

Entry points:

- tool: [../../../../tools/environment/arnis/README.md](../../../../tools/environment/arnis/README.md)
- importer: `python/scenario/environment_substrate/importers/arnis_bundle.py`
- fixture: `tests/scenario/fixtures/environment_substrate/arnis_bundle_v1/chicago_river_phase1/`
- acceptance: [environment_substrate_arnis_phase1_acceptance_20260715.md](environment_substrate_arnis_phase1_acceptance_20260715.md)

## Capability Boundary

Phase 1 accepts static environment data only. It does not release runtime setup
application, movement, passability, route graphs, LOS, cover, concealment,
fires, damage, hydrodynamics, or combat. Road widths, building heights, and
hydrology geometries are provenance-bearing static inputs, not tactical effects.

The elevation raster is a sampled heightfield that a later runtime may
reconstruct bilinearly. Land cover is categorical and permits only
nearest-category sampling. Buildings, roads, and hydrology remain separate
vector geometry and must not be interpolated through the terrain raster. The
old block-derived draft bundle is invalid and now fails closed at import.

The static-scene derivative preserves source XY. Resolved buildings use one
rigid foundation plane from DEM samples plus a metric base offset. Resolved
roads use width-bearing terrain-conforming corridor polygons. Objects lacking a
metric vertical profile remain held: in the retained Chicago fixture this is
`10` roof/building parts, `49` elevated road profiles, and `47` subsurface road
profiles. The derived product is not collision, pathfinding, LOS, cover, or
damage authority.

The frozen OSM input and checked-in bundle are byte-verifiable. USGS 3DEP and
ESA WorldCover network/cache sources are not yet fully frozen for offline
regeneration, so future network regeneration is not claimed to be byte-identical.
