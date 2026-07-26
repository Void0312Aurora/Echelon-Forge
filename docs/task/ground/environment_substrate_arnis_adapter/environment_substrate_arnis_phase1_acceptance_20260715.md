# Arnis Adapter Phase 1 Acceptance

Date: `2026-07-15`

Decision: `accepted`, scoped to static environment bundle export, verification,
CMO manifest import, and offline static-scene derivation/preview only.

## Accepted Facts

- Upstream is pinned to Arnis `v3.0.0` / commit
  `af521c99124b5e07ecba018ea54f2ac47b6441d5`.
- The continuous exporter patch is
  `0001-cmo-continuous-bundle-export-v1`, SHA-256
  `26536836d46aa7bc3e03da3449b4c52391f096527ab58f365d5dd4b96b9052ee`.
- The exporter rereads frozen OSM latitude/longitude and projects floating-point
  local ENU directly. It emits `arnis_cmo_bundle.v1` before block-coordinate OSM
  raster repair, map transformation, or any Minecraft writer.
- The phase-1 CLI requires a frozen OSM file, terrain, Web Mercator, scale 1,
  rotation 0, Overture disabled, and one exclusive actual elevation provider.
- Elevation provenance records `usgs_3dep: 2 source units` and
  `missing_source_units: 0`; any AWS tile fallback makes retained export fail
  closed.
- Elevation is written directly from the land-cover-aware postprocessed metre
  grid retained before `scale_to_minecraft()`; the bundle declares no
  Minecraft-Y transform or roundtrip.
- WorldCover is exported as a categorical metric grid for nearest-category
  sampling only.
- Polygon output requires closed source rings and uses continuous floating-point
  bbox clipping.
- Relation members are no longer duplicated as standalone buildings.
- Road/waterway widths and building heights come only from OSM metric tags,
  levels-based metric inference, or explicit metric semantic defaults, never
  from block ranges or counts.
- Roads, buildings, and hydrology carry fail-closed `elevation_anchor`
  components. Metric building bases resolve as rigid terrain anchors; ordinary
  zero-layer roads resolve as terrain-draped corridors. Missing roof, elevated,
  or subsurface profiles remain held instead of receiving guessed heights.
- The CMO importer validates path escape, SHA-256, raster dtype/shape/content,
  vector bounds, provenance, catalog admission, and held-capability boundaries.
  It also requires root, artifact, feature, and measurement continuous lineage
  plus an allowlisted patch SHA; the old block-derived bundle fails closed.

## Frozen Fixture

- bbox: `41.8865,-87.6355,41.8895,-87.6315`
- OSM SHA-256:
  `efe1b0d5045ae898b18fa5587df7e477849ef009eb2417c9437f7f2aa64bebd1`
- bundle.json SHA-256:
  `524064a993f83bd1c25c6b5b039ba2ee5c11fd5fae3a9a3cb9a8d617a609571d`
- local ENU extent: `331.116875 × 333.584780 m`
- CMO objects: `511`
  - elevation tile: `1`
  - land-cover tile: `1`
  - roads: `425`
  - buildings: `76`
  - hydrology: `8`

Two consecutive exports from the same input were byte-identical, and all seven
entries in `checksums.sha256` passed.

The offline `cmo.static_scene_geometry.v1` derivative covers `509` vector
objects: `403` resolved and `106` held. Resolved objects comprise `66`
buildings, `329` roads, and `8` hydrology features. Held objects comprise `10`
roof/building parts, `49` elevated road profiles, and `47` subsurface road
profiles. Fifty-four boundary roads are retained by clipping only derived
corridor polygons to the DEM extent; source centerlines remain unchanged.

## Verification

```bash
python tools/environment/arnis/cli.py verify \
  --bundle tests/scenario/fixtures/environment_substrate/arnis_bundle_v1/chicago_river_phase1/expected

python -m pytest -q \
  tests/scenario/test_environment_substrate_contracts.py \
  tests/scenario/test_environment_substrate_arnis_bundle.py \
  tests/scenario/test_environment_projection_contracts.py \
  tests/tools/test_arnis_environment_cli.py \
  tests/tools/test_arnis_continuous_bundle_visualize.py
```

The continuous preview reads only the CMO bundle and labels itself `NOT
RUNTIME`; it is neither a Minecraft render nor a claim that simulation-runtime
integration has been released. The CMO/Python acceptance set completed with
`97 passed`; the patched Arnis Rust suite completed with `362 passed`,
`3 ignored`, and `0 failed` under `--locked --no-default-features`.

## Held Items

- Runtime setup application, movement, passability, LOS, cover, fires, damage,
  hydrodynamics, and combat remain held.
- Long-term offline regeneration remains held until elevation and WorldCover
  source tiles are fully frozen.
- Multi-tile support, cross-tile objects, artifact deduplication, and first-class
  artifact references belong to later phases.
