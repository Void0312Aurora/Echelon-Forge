# Environment Runtime P2-A Contract

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/systems/environment/work/active/environment_runtime/environment_runtime_p2a_contract_20261124.md`
Owner: `systems/environment`
Last verified: `2026-11-24`

Status: authored contract and additive interface draft; owner review, coordinator
compilation, and native validation pending. This is not P2 acceptance or a P3
implementation. Language: English canonical only (Tier B work document).

Parent: [Environment Runtime](README.md). Evidence:
[P1 inventory](environment_runtime_p1_inventory_20261029.md), including its
2026-11-16 recheck; plan: [task clusters](environment_runtime_task_clusters_20260928.md).
No new runtime survey, external source admission, build, or test is claimed here.

## 1. Authority, frames, and unset data

One immutable environment snapshot is the authority for each simulation time.
Every admitted bundle declares the same scenario `horizontal_frame` and
`vertical_datum`, plus a source and stable snapshot/layer/tile identity. The datum
identifier must identify its reference surface, units, realization and conversion
version through scenario metadata; an empty string, unknown identifier, or
`source_provider_native_unspecified` is not an admitted datum. No automatic sea
level zero, ellipsoid/geoid substitution, or local-origin offset is permitted.
A source in another datum is converted explicitly before admission, with the
conversion and original datum recorded. Unconvertible layers are rejected.

All coordinates use metres. Elevations increase upward relative to this declared
datum: land elevation, bottom elevation, and water-surface elevation share it.
Water depth is a nonnegative difference `surface_elevation_m - bottom_elevation_m`,
not a second datum. A negative water surface is legal; negative depth is invalid.
Scenario Transform.z may be used as an absolute elevation only after its local
frame origin and datum have an explicit Geodetic Frame conversion.

`QueryContext` carries frame, datum, finite simulation time, and optional UTC
clock time. Missing/mismatched datum returns `InvalidDatum`; missing/mismatched
frame returns `InvalidFrame`; absent/out-of-validity time returns `InvalidTime`.
These checks precede coverage lookup. No admitted provider returns `Valid` with
empty frame, datum, source, snapshot identity or contributing tile identities.
Metadata contains the contributing resolution and validity interval; intervals
are half-open, and static layers declare validity over the scenario duration.
Nonfinite coordinates or malformed queries return `Unsupported`, never `Valid`.

`QueryStatus::Unavailable` means the provider has no implementation or admitted
layer. `OutOfCoverage` means no declared tile contains the query; `NoData` means
a declared covering tile has a gap or missing required value. `Unsupported`
means a requested mode cannot be evaluated. An empty optional is unknown, never
zero. Non-Valid observations must not carry authoritative payloads. `Valid`
means the particular query's required fields are available; optional attributes
may remain absent, with the source residual recorded. Domains decide how to
respond to missing truth; the environment does not decide passability.

## 2. Multi-tile and multi-layer terrain, bottom, and water

`get_environment_layers()` describes the ordered runtime layers through
`EnvironmentLayerDescriptor`. It returns no synthetic descriptors by default.
Each descriptor identifies its layer, snapshot, tile, frame/datum, resolution,
validity, priority and half-open bounds `[min_x,max_x) x [min_y,max_y)`.
Boundaries belong to the tile on their positive side. Global outer-edge coverage
must be declared explicitly rather than inferred by clamping.

Layers follow the substrate physical-base, surface, hydrology, atmosphere,
wind, illumination and maritime ordering. Within one layer, overlap is resolved
by descending explicit priority, then finer cell area, then lexicographic
layer/tile ID. Equal IDs with conflicting data are rejected. Elevation is
bilinearly sampled only from valid same-datum cells; categories use the containing
cell. No extrapolation, interpolation across nodata, or implicit cross-tile
blending is allowed. Adjacent tile sampling requires declared compatible edges;
otherwise the sample is `NoData`. Resampling/derived layers record provenance.

`query_terrain` is the atomic elevation-and-surface authority. `Valid` requires
both `elevation_m` and `surface`, from the same snapshot and compatible layer
coverage. `landcover_code` and physical slope are optional. Slope uses a bounded
valid window, including one-sided edge differences; gaps yield no slope. A slope
never combines raster elevation with an undeclared procedural fallback.

Outside every terrain tile, both elevation and surface are `OutOfCoverage` with
empty payloads. This resolves the P1 procedural hill versus `Obstacle` conflict.
A procedural hill or flat surface may be an explicitly admitted layer, with
coverage, datum and provenance, and then supplies both fields consistently.
`Obstacle` denotes an actual classified feature, never absence of data. Legacy
scalar/cell methods retain their old behavior during P2-A; their implementation
must converge on this authority in P3/P4 before consumers migrate.

`query_water_body` distinguishes sea, river, lake and reservoir by stable ID.
A valid wet observation requires kind, ID and surface elevation. Optional bottom
and depth are supplied only when measured/admitted; when both exist the depth
identity above must hold within a declared source tolerance. Unknown depth does
not imply deep or navigable water. Dry covered terrain returns `NoData` for this
wet-only query; it does not invent a water body. Flow is a vector toward motion
in the query frame; temperature is Celsius and salinity is PSU. No fording,
bridging, movement cost, or ship clearance policy is included.

`query_coastline` covers freshwater shorelines as well as sea coasts. A valid
result contains water-body ID/kind, nonnegative horizontal nearest distance,
nearest point and `wet_side`; exact shoreline distance is zero. Its nearest
point z is the declared water surface. Search must cover all competing shoreline
features or return incomplete coverage, rather than claim an unproved nearest
feature. Shoreline metadata and water truth must share snapshot and time.

`query_bathymetry_segment` reports the conservative minimum nonnegative depth
over the entire proposed horizontal segment at the supplied simulation time.
All crossed tiles and resolution changes count; endpoint-only sampling is
insufficient. Any uncovered, dry, nodata, frame, datum or time-invalid part
invalidates the whole observation. No partial minimum is `Valid`. P3 must state
the conservative sampling/error bound. The old `get_bathymetry_along_segment`
remains separate: its existing zero-water-surface and step-invariance constraints
are preserved. Nonzero tides are admitted only by the new timed seam after
consumer migration; P2-A does not relax the existing submarine policy.

## 3. Terrain visibility and Geodetic Frame boundary

`TerrainSightQuery` explicitly supplies each endpoint's `HeightReference`.
`AbsoluteDatum` means z is an elevation in the query datum. `AboveTerrain` means
z is a nonnegative offset added to the endpoint's valid `query_terrain`
elevation; mixed endpoint references are allowed. Unspecified references fail
closed. Endpoint heights are never inferred from platform type or z magnitude.
The query evaluates terrain occlusion along the whole segment, not just endpoint
clearance, and reports `Clear`, `Occluded`, or `Unknown`. A missing endpoint or
interior sample, unsupported curvature mode, or datum/frame failure gives a
non-Valid status and `Unknown`; `Clear` requires complete valid coverage.

The caller must explicitly select `LocalFlat` or `GeodeticEarth`; no automatic
range threshold silently changes the geometry. `LocalFlat` is the local Cartesian
segment without curvature and must be reported as such. `GeodeticEarth` delegates
earth shape, anchor, coordinate/datum conversion and chord geometry to
[Geodetic Frame](../../../../physics/work/active/geodetic_frame/README.md),
using the world's declared EarthModel. Environment samples the terrain against
that geometry; it does not add an independent fixed-radius earth bulge. A
provider without that capability returns `Unsupported`/`Unknown`. Atmospheric
refraction and sensor propagation stay with sensing.

The army branch's AGL raster LOS can be adapted with both heights explicitly
`AboveTerrain` and `LocalFlat`. Its existing Unknown boundary is retained until
multi-tile coverage exists. Do not replace sensor `check_line_of_sight` until
absolute heights, flat/procedural coverage, curvature, and Unknown policy have
regression evidence. P2-A adds `query_terrain_visibility`; it neither duplicates
that branch's implementation nor changes legacy boolean LOS behavior.

## 4. Seeded fields, maritime state, and illumination

`query_weather` samples atmosphere, wind toward motion (m/s in the query frame),
visibility (m), and precipitation (mm/hour). A Valid result carries at least one
available attribute; the other slots remain optional. `query_sea_state` supplies
an explicit total sea-state value and optional distinct wind-sea and swell
components: significant height (m), period (s), and propagation heading (NAV,
0 north, clockwise positive). Each present component must be complete and finite;
calm height may be zero. The legacy wave-heading convention requires an explicit
adapter; it is not assumed equivalent to this direction-toward convention.

Each varying field declares `VariationDescriptor`: Constant or SeededField,
algorithm version, parameters ID and seed; seeded fields also declare positive
space/time scales. Sampling is a pure function of scenario seed, layer identity,
position and simulation time, using declared interpolation and clock origin.
It must be independent of call order, thread count, stepping partition, GPU
scheduling and wall clock. Replay records descriptors, inputs, snapshot revision,
validity and source hashes. Unspecified variation cannot be treated as constant.
If wind and weather use separate descriptors, query provenance identifies their
combined immutable snapshot; incoherent field times are rejected.

An absent sea-state layer returns Unavailable, allowing a domain-owned legacy
platform fallback. An explicit calm value is Valid and overrides that fallback.
No partial legacy `MaritimeState` merge is introduced. P4-B replaces the three
P1 maritime fallback implementations with one shared observation plus explicit
consumer adapters, and carries `configured` through Python bindings. Loss of
`configured=false` must never become an environmental calm-sea override.

`query_illumination` declares `ScenarioFixed` or `ScenarioClock`. A valid result
contains a unit sun-direction-toward vector in the query frame and solar
elevation. Clock mode uses scenario UTC epoch plus simulation time and Geodetic
Frame location/anchor; a supplied UTC value must agree with that clock. Missing
clock/anchor/transform support is Unavailable or InvalidTime, never an invented
day/night result. Fixed mode remains explicitly authored and replayable. No
wall-clock sampling is allowed. Reference solar-geometry validation belongs to
P3-D; the legacy sun setter/getter remains authoritative for legacy consumers.

## 5. Ocean acoustic slots

`query_ocean_acoustics` supplies data at horizontal position and simulation time,
with depth samples positive downward from its declared water-surface elevation.
A valid result requires that surface and at least one supplied acoustic slot.
Profile depths are finite, nonnegative, increasing and within admitted water
depth where known. Each sample carries sound speed (m/s), or measured temperature
(Celsius) and salinity (PSU) for downstream conversion; absent values stay unset.
Mixed-layer depth is metres below surface, bottom class may be Unknown, and
ambient-noise pairs carry frequency in Hz and spectral level in dB re 1 uPa^2/Hz.
Empty profiles/noise vectors indicate absent data. No climatology, sound-speed
formula, ambient-noise constant, sonar propagation or detection policy is
fabricated. P3-E records per-source residuals and profile validity.

## 6. GPU parity and Ground migration

`gpu_visual_runtime` is a derived visual reader, never a second environment
authority. P1 found a hard-coded hill, missing Arnis elevation/wind/sun, and lost
step_x/step_y. A future snapshot must preserve layer/tile/source IDs, frame/datum,
coverage/nodata, both grid steps, categories, temporal validity, variation seed
and algorithm, sampled fields and illumination mode/time. CPU/GPU parity means
same coverage/status/categories and values within declared sampling tolerances
at the same time and revision. Unsupported visual layers are explicitly marked;
the renderer must not silently substitute a hill or feed approximation back into
physics, sensing or domain decisions. GPU parity is P3/P5 work, not delivered here.

P4-A starts from main. The shared authority keeps terrain loading/tiling,
physical elevation/surface/landcover/slope, water geometry and shorelines.
Ground takes GroundFieldSemanticObservation, GroundTransitionObservation,
get_ground_field_semantic_observation, get_ground_transition_observation,
load_arnis_field_overlay, field-overlay storage/readers and tree-line/settlement
policy, Water/Obstacle blocking, passability/transition costs, stance-dependent
multipliers, and corresponding kernel/binding adapters. These move to
src/systems/domains/ground or src/models/domains/ground. Generic vegetation or
built geometry may later be admitted as neutral layers, without Ground semantics.
The neutral slope API loses the Ground name during migration; the legacy method
stays until its callers move. No domain header is added in P2-A.

P4-A removes these legacy shared members only after all callers migrate and the
accepted Ground tests are rerun, with changed outcomes recorded, never retuned.
Source compatibility now is preserved by adding only nested types and virtual
methods with unavailable defaults: no old signature, enum value, caller, fake,
or DefaultEnvironmentModel implementation must change. Adding virtual members
requires recompilation; binary ABI compatibility with old objects is not claimed.

## 7. Coordinator validation and acceptance still required

The authoring worker runs no SSH, HEI build, CMake, CTest, C++ compilation or
runtime tests. Formatting and textual checks are authoring checks only.
The coordinator owns the prescribed HEI -j32 compilation/tests and owner review.
Required follow-up evidence includes mixed-resolution adjacent tiles, gaps and
procedural layers; unset/mismatched datum and nonzero water surfaces; whole-step
shoals and dry crossings; absolute/AGL/mixed LOS and curvature rejection; seed
replay under reordered queries; clock/fixed sun; acoustic missing slots;
CPU/GPU snapshot parity; Python configured preservation; and Ground acceptance.
Existing fakes must compile unchanged and every new default must be unavailable.
P3 runtime implementation and P4 migration remain planned until their gates pass.
