# Terrain Point Query Candidate

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/systems/environment/work/active/environment_runtime/terrain_point_query_candidate.md`
Owner: `systems/environment`
Last verified: `2026-11-16`

Language: English canonical only; candidate contract work surface.

Parent: [Environment Runtime](README.md).

Status: candidate API and single-raster implementation. This slice does not
accept the full Environment Runtime P2 contract or release a consumer migration.

## API and fields

`IEnvironmentModel::get_terrain_point_observation(x, y)` is additive. The default
virtual implementation returns `Unavailable`; it does not derive a sample from
legacy scalar methods. The default provider implements it for its loaded Arnis
elevation/landcover pair. Flat and procedural profiles return `Unavailable`.

The candidate field meanings are fixed for this slice:

| Field | Meaning |
| --- | --- |
| `availability` | `Available`: both source elevation and a recognized source surface class exist at the same raster cell. `OutOfCoverage`: outside that raster. `InvalidInput`: non-finite query coordinate. `NoData`: an in-coverage cell cannot supply the pair. `Unavailable`: no implementation or active raster. |
| `source` | `ArnisMetricRaster` identifies the adapter, not a promise of measured or calibrated source data. `None` supplies no raster observation. Synthetic test bundles also use the adapter tag; their source metadata identifies them as fixtures. |
| `elevation_m`, `surface` | Paired source-cell height and `TerrainSurfaceClass`. Every non-`Available` observation has non-finite elevation and no surface, rather than a hill or obstacle fallback. |
| `landcover_code` | Optional raw source byte, including nodata or unsupported codes when the cell is present but the pair is `NoData`. |
| `horizontal_frame` | Verbatim bundle `coordinate_frame`, empty if undeclared or null. Existing bundles declare `local_enu_m`; that declaration does not assert alignment with a scenario's geodetic frame. |
| `vertical_datum` | Verbatim elevation metadata. Missing, null or empty stays empty; `source_provider_native_unspecified` remains that string. Availability is independent of datum compatibility. |
| `elevation_source`, `surface_source` | Verbatim elevation `source_provider` and landcover `classification_scheme`, respectively; empty if undeclared. |
| `tile_id` | Verbatim bundle `tile_scheme.tile_id`, empty if undeclared. No multi-tile selection occurs. |
| `grid_step_x_m`, `grid_step_y_m` | Signed metric steps from the raster pair. Their magnitudes give the separate per-axis resolutions. No interpolation or resampling is implied. |

The adapter reads elevation and landcover with one cell index. It uses the
existing point registration and nearest-centre convention: last cell centres
are covered, as are points strictly less than half a cell beyond them. The
outer half-cell ties round outside. Coverage is bounded before integer rounding,
including for huge finite coordinates. Covered cells with WorldCover nodata or
unsupported classes report `NoData`; so do cells without the supported
`ESA_WorldCover_2021_v200` classification declaration. The raw byte and scheme
remain available as provenance, without guessing their surface meaning or
treating them as environmental obstacles.
Input finiteness checks precede provider/coverage checks. Out-of-coverage
and nodata observations retain the active raster's provenance and resolution.

## Source boundary and compatibility

This is a raw raster query. It reports WorldCover classes, including water,
built-up and vegetation, without passability, friction or movement cost.
Scenario zones and bridge/river vector policies continue through the existing
compatibility queries; they do not override this source observation.

Metadata is loaded transactionally with the raster. Failed replacements leave
the active sample and provenance intact. Optional string metadata accepts an
undeclared or null value; a non-string declared value rejects the replacement.
No vertical conversion, datum compatibility decision or source admission is
inferred. Consumers combining heights must establish compatible frames and
datums in a later owner contract.

`get_terrain_elevation`, `get_terrain_at` and their consumers retain their
existing behavior, including legacy off-raster fallbacks. This slice changes no
Ground, sensor, GPU, LOS, hit-volume or route consumer and adds no binding,
component or system. Army LOS and raster-edge slope work remains separate and
is not reimplemented here. The loaded-content checkpoint guard belongs to the
native branch owner and must be preserved when integrating this additive query.

## Validation and remaining decisions

The focused native target `ef_environment_terrain_point_test` compiles the real
default provider, this interface and `test_environment_terrain_point.cpp`, with
doctest and JSON only. It is registered as CTest `environment_terrain_point`.
It covers cell/edge pairing, absent providers, invalid and huge coordinates,
signed non-square steps, a single cell, surface/nodata classes, frame/datum metadata,
overlay separation and failed-load preservation. It does not qualify kernel,
Python, GPU or replay consumers.

P2 still needs multi-tile precedence and gap rules, common-datum admission,
water-body composition, and explicit LOS height/curvature semantics. Migrating
legacy scalar consumers is a separate packet; this candidate does not close
their off-raster inconsistency.
