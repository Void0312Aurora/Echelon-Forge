# Arnis CMO Adapter

This directory maintains one pinned upstream revision, one patch, and one CLI;
the full Arnis source tree is not copied into CMO.
The current continuous patch SHA-256 is
`26536836d46aa7bc3e03da3449b4c52391f096527ab58f365d5dd4b96b9052ee`.

Phase 1 provides only:

- `prepare`: checkout the fixed Arnis `v3.0.0` commit, verify/apply the CMO
  patch, and build a separate `arnis-cmo` with `--no-default-features`;
- `export`: consume a frozen OSM input and fixed-bbox phase-1 request and emit a
  continuous metric bundle before Minecraft quantization;
- `verify`: validate every bundle SHA-256 and run CMO manifest/catalog admission.

The install does not replace the upstream `arnis` command. Default locations:

```text
~/.cache/cmo/third_party/arnis/v3.0.0-af521c99124b-cmo5/
~/.local/opt/arnis-cmo/v3.0.0-cmo5/arnis-cmo
~/.local/bin/arnis-cmo
```

## Usage

```bash
python tools/environment/arnis/cli.py prepare

python tools/environment/arnis/cli.py export \
  --request tests/scenario/fixtures/environment_substrate/arnis_bundle_v1/chicago_river_phase1/request.json \
  --output-dir /tmp/arnis-cmo-phase1

python tools/environment/arnis/cli.py verify \
  --bundle tests/scenario/fixtures/environment_substrate/arnis_bundle_v1/chicago_river_phase1/expected

python tools/environment/arnis/visualize.py \
  --bundle tests/scenario/fixtures/environment_substrate/arnis_bundle_v1/chicago_river_phase1/expected \
  --output-dir /tmp/arnis-cmo-continuous-preview
```

The visualizer writes both the continuous-field diagnostic and an offline
static-scene product:

- `continuous_field_overlay.png` and `continuous_field_metrics.json`;
- `static_scene_geometry.json`, contract `cmo.static_scene_geometry.v1`;
- `static_scene_preview.png`, rendered at true metre Z scale.

Resolved buildings become rigid prisms without changing their source XY
footprints. Resolved zero-layer roads become width-bearing DEM-draped
corridors; derived boundary polygons are clipped to the DEM extent while source
centerlines remain unchanged. Bridges (`bridge=true`, positive layer, linear
centerline) resolve to `abutment_interpolated_deck` corridors: the two
centerline endpoints are sampled from the DEM as abutment anchors and the deck
elevation is interpolated linearly along the arc length. No measured deck
elevation is claimed; `deck_profile.deck_elevation_measured` stays `false` and
decks whose abutments fall outside the finite DEM remain held. Roofs,
non-bridge elevated passages, and subsurface roads without metric profiles
remain explicit held objects rather than receiving guessed heights.

Phase 1 requires a frozen `--file`, terrain, `web_mercator`, scale 1, rotation
0, Overture disabled, and an admitted actual elevation provider. The output is
static environment data only; it does not release runtime setup, movement,
passability, LOS, cover, fires, damage, or combat.

CMO export does not read a Minecraft world and does not treat integer
`ProcessedNode` coordinates, block ranges, or block counts as authoritative
geometry. Roads, buildings, and hydrology are projected directly from the
frozen WGS84 source into floating-point local ENU. Elevation is written from
the postprocessed metre grid retained before `scale_to_minecraft()`. Land cover
is a categorical field consumed with nearest-category sampling; only the DEM
heightfield permits bilinear continuous reconstruction, while vector buildings
and other structures remain separate geometry.

The frozen OSM input and checked-in bundle are byte-verifiable. Elevation and
WorldCover are still supplied by network/cache providers, so future network
regeneration is not guaranteed to remain byte-identical. Fully offline source
freezing belongs to a later phase.
