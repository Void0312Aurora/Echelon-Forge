# Chicago River Arnis Bundle Phase 1 Fixture

This directory retains the first bounded, file-backed Arnis-to-CMO bundle
fixture. It is intended to validate bundle parsing, checksums, provenance, and
feature counts without contacting OpenStreetMap, USGS, ESA, or an Overpass
service during the test run.

## Frozen request

- WGS84 bounding box: `41.8865,-87.6355,41.8895,-87.6315`
- Frozen OSM input: `input/osm_extract_20260715.json`
- Arnis: `3.0.0` at commit
  `af521c99124b5e07ecba018ea54f2ac47b6441d5`
- Exporter: `cmo.phase1.v1`, continuous patch
  `0001-cmo-continuous-bundle-export-v1`
- Patch SHA-256:
  `26536836d46aa7bc3e03da3449b4c52391f096527ab58f365d5dd4b96b9052ee`
- Options: terrain enabled, Overture disabled, Web Mercator, scale `1`,
  rotation `0`
- Actual elevation provider: `usgs_3dep`
- Land-cover source: ESA WorldCover 2021 v200

The expected bundle contains:

- `425` road features across `402` source ways; continuous clipping may retain
  multiple in-bounds parts from one way;
- `76` building features after relation-member deduplication;
- `8` hydrology features across `7` source ways;
- one postprocessed, pre-Minecraft metric elevation raster; and
- one categorical land-cover raster exported before block-raster repair.

Vector geometry is projected directly from frozen WGS84 source coordinates as
floating-point local ENU metres. Road widths, building heights, and waterway
widths come from source metric tags or explicit metric semantic defaults; they
are not reconstructed from Minecraft block counts or ranges. The elevation
raster is written from the postprocessed metre grid retained before
`scale_to_minecraft()`.

All `509` vector objects carry fail-closed vertical-anchor semantics. `403` are
resolved for offline static-scene derivation and `106` remain held: `10`
roof/building parts without metric base offsets, `49` elevated road profiles,
and `47` subsurface road profiles. A visualizer-derived
`cmo.static_scene_geometry.v1` product may rigidly extrude the `66` resolved
buildings, drape the `329` resolved roads as width-bearing corridors, and place
all `8` hydrology features for preview. It is not retained as runtime authority.

The fixture is static environment data only. It does not release runtime setup,
terrain-aware movement, passability, line of sight, cover, fires, damage, or
combat capabilities.

## Verification

From this directory:

```bash
sha256sum input/osm_extract_20260715.json
(cd expected && sha256sum -c checksums.sha256)
```

The input digest must be
`efe1b0d5045ae898b18fa5587df7e477849ef009eb2417c9437f7f2aa64bebd1`.
The expected `bundle.json` digest must be
`524064a993f83bd1c25c6b5b039ba2ee5c11fd5fae3a9a3cb9a8d617a609571d`.

This fixture is reproducibly verifiable from the retained files. A fresh
network acquisition is not expected to remain byte-identical over multiple
years: OpenStreetMap contents, Overpass responses, provider datasets, and
upstream processing implementations may change. Regeneration must therefore
produce a newly reviewed fixture rather than silently replacing this baseline.

See [ATTRIBUTION.md](ATTRIBUTION.md) and
[`source_manifest.json`](source_manifest.json) for source and license details.
