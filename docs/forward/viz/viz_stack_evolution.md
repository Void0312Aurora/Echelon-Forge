# Visualization Stack Evolution (Operational/Strategic-Scale North Star)

> **Status**: Planning (foundation partially landed)
> **Last Updated**: 2026-07-21
> **Related branch**: `codex/viz-unified-scene-rendering`

## Executive Summary

The long-term target for visualization is to extend from the current
tactical layer (km-scale local scenes, platform-level entities) to the
**operational and strategic levels**: country-scale geography, echelon-
aggregated situation display, seamless cross-scale zoom. This document
records the evolution path and its ordering rationale. Core conclusions:

1. **The rewrite risk lives in data contracts, not the rendering engine.**
   The contract seeds are already planted (see "Foundation in place");
2. Large architecture items (state-stream v2, 2D WebGL migration) are
   **sequenced after their upstream dependencies**, not started early just
   because they are inevitable;
3. The ordering criterion is **whether the decision inputs exist**: work
   whose correct shape is determined today gets done immediately; work
   whose shape depends on undecided requirements waits for the upstream
   to settle.

## What Changes at Scale

Country-scale visualization is not "a bigger tactical map":

| Dimension | Tactical (today) | Operational/strategic (target) |
|-----------|------------------|-------------------------------|
| Coordinates | Local ENU plane (km-scale, flat approximation holds) | Global geodetic (curvature and projection distortion matter) |
| Entities | Platforms, all rendered | Echelon aggregates (battalion/brigade/division icons, front lines, supply axes) |
| Data | One-shot full payloads | Tiling / streaming / area-of-interest subscriptions |
| Time | Minute-scale episodes, frames discarded | Day/week spans; replay and event streams first-class |

## Foundation in Place (fait accompli)

| Commit | Content | Why it matters at scale |
|--------|---------|------------------------|
| `8c46e1f6` | Sun illumination parameterized: scenario `environment.illumination` -> engine `IEnvironmentModel` -> both viz views from one truth | Establishes the "display equals adjudication truth" pattern, replicable for wind/weather/visibility |
| `7bac7da3` | Four contract seeds: geodetic anchor, MIL-STD-2525 SIDC vocabulary, unit `echelon`, versioned wire contracts | Anchor = local scenes stay globe-placeable; SIDC/echelon = data precondition for aggregate rendering; versions = negotiable protocol migration |
| `6c3c1ea9` | eventlet retired for plain threading | Drops an unmaintained dependency; `socketio.sleep` delegation means a future ASGI switch needs no session-code edits |
| `e5374b92` | Buildless JSDoc typing (`types.js` + jsconfig + `@ts-check` core modules) | Wire contracts get machine-checked type mirrors; quality floor for AI/multi-person work |

Contract-test anchors: `tests/viz/test_strategic_scale_seeds.py`,
`tests/viz/test_frontend_typing.py`, `tests/viz/test_illumination_pipeline.py`.

## Ordering Principle

**Seed work** (correct shape fixed by existing standards: WGS84, 2525,
semantic versioning) -> do immediately; cheap now, expensive to retrofit.
Done.

**Architecture work** (correct shape depends on operational-level
requirements not yet settled) -> sequence after upstream. Doing it early
freezes today's shape and still gets rewritten at scale, now carrying
"already migrated" sunk cost.

## Evolution Items

### 1. State-stream v2 (delta + AOI + aggregation + binary)

- **Today**: 30 Hz full-state JSON frames (`examples.viz.state_frame.v1`),
  static fields resent every frame.
- **Why not "swap JSON for MessagePack"**: pure binary encoding only saves
  serialization CPU; the frame semantics stay identical — the shallowest
  win. The real v2 skeleton is delta frames (sync/recovery semantics), AOI
  subscriptions (server-side viewport filtering), and aggregate frames
  (strategic views receive echelon aggregates, not platforms).
- **Upstream**: operational-level data model (aggregation semantics, AOI).
- **Trigger**: hundreds of units, or the operational data model settles.
- **Shape-stable first step (safe anytime)**: frame-semantics cleanup —
  move static fields (`name`/`side`/`type`/`platform_type`/`echelon`) to a
  one-shot roster message; state frames carry dynamics only. Any v2 needs
  this, and it halves frame size today.

### 2. 2D Tactical Map WebGL Migration

- **Today**: single immediate-mode Canvas 2D full redraw; no pressure at
  current scale (tens of entities, 1 km² vectors).
- **Why deferred**: the pipeline skeleton depends on operational-level
  rendering needs — aggregate symbols (atlas + instancing), control
  measures (front lines/sectors/axes style pipeline), wide-area basemaps
  (tiling). Built against tactical needs first, it gets rebuilt at scale.
- **Upstream**: consumption shape of the SIDC/echelon seeds, control-
  measure graphics set.
- **Trigger**: significant vector-layer growth (contours/sensor coverage/
  dense symbology) or aggregate-rendering requirements.
- **Design rule (when it happens)**: keep layers projection-agnostic; the
  world-to-screen transform stays single-point (current `toCanvas`
  closure habit), so the same layers can later hang under a geographic
  projection.
- **Shape-stable first step (safe anytime)**: hybrid rendering of static
  vectors — roads/buildings/water into WebGL (orthographic three.js view
  reusing existing 3D geometry), dynamic layers stay Canvas 2D on top.

### 3. ASGI Migration (Flask/Werkzeug -> FastAPI/uvicorn or similar)

- **Motivation**: dev server is not a long-term host; native WebSocket
  pairs better with binary frames.
- **Scheduling**: same batch as state-stream v2 (change protocol and
  server together; avoid migrating twice).
- **Already prepared**: session code goes through `socketio.sleep` /
  `start_background_task`; task draining supports multiple async models.

### 4. Dual-Engine Layering (geo engine + tactical three.js)

- **Predicted shape**: strategic/operational layers on a geo engine
  (Cesium or deck.gl globe) for aggregate situations and global basemaps;
  tactical layer keeps the three.js local high-fidelity scene; the two
  join via the `geodetic_anchor` contract and share SIDC semantics.
- **Why no Cesium now**: the data contract is local ENU (`local_enu_m`);
  Cesium's core value (ellipsoid, terrain streaming, imagery) is unused
  while its geodetic complexity taxes everything.
- **Trigger**: data contract upgrade to a global CRS (multi-theater or
  real-basemap requirements).

### 5. 2D Hillshade on GPU

- **Today**: sun-angle changes rebuild the terrain bitmap on CPU
  (hundreds of ms) — acceptable for one-shot changes.
- **Trigger**: time-of-day progression (environment Phase B, sun moving
  with sim time) makes high-frequency rebuilds infeasible; then move 2D
  shading to GPU (falls out of the WebGL migration) or precompute sun-
  angle bins. The 3D side is already live-lit.

### 6. Store Subscription Mechanism

- **Today**: `vizState` is plain mutable state; changes fan out manually
  at call sites (e.g. `applyIllumination` calls both refreshers).
- **Trigger**: before environment parameter fan-out grows (time/weather/
  wind/sensor-coverage parameterization). A few dozen lines of subscribe;
  no framework.

### 7. Incremental `@ts-check` Rollout

- **Order**: `layers` -> `asset-registry` -> `scene-geometry` -> (large
  modules) `session`/`ui-shell`/`tactical-map`/`scene3d`.
- **Check command**:
  `npx -y -p typescript tsc --noEmit -p examples/viz/web_viz/jsconfig.json`.

## Non-Goals (explicitly not doing)

- No binary encoding of the current frame shape before frame semantics
  are cleaned up;
- No 2D pipeline rewrite against tactical-only requirements;
- No Cesium/globe engine while the data contract is local ENU;
- Frontend stays buildless (no bundler); type checking remains editor /
  on-demand tsc.

## Cross-References

- Contract-seed tests: `tests/viz/test_strategic_scale_seeds.py`
- Typing foundation: `examples/viz/web_viz/static/js/types.js`,
  `examples/viz/web_viz/jsconfig.json`
- Illumination truth chain: `examples/viz/runtime/illumination.py`,
  `examples/viz/web_viz/static/js/illumination.js`
- Scene-geometry contract (anchor): `examples/viz/runtime/scene_geometry.py`
- Echelon inference: `examples/viz/runtime/unit_semantics.py`
- SIDC vocabulary: `examples/viz/web_viz/static/js/symbology.js`
