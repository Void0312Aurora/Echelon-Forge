# Eastern Plain Infantry Training v1

Document kind: `work-package`
Lifecycle: `active`
Owner: `domains/ground` with `systems/environment` input
Status: `contract-and-source-fixture`

This work package introduces a fictionalized agricultural-plain map profile and a
single dismounted infantry schema. It is deliberately a movement and environment
observation slice; it does not introduce weapon employment, targeting, or a combat
runtime.

## Scope

The map profile is a small eastern-European-plain analogue composed of broad fields,
three narrow tree belts, two small settlements, a river, a bridge, and farm tracks.
It uses a flat, non-conflict US central-plains elevation/landcover analogue; the
geometry is synthetic and does not point to a real battlefield. Arnis phase 1 is
used for the frozen continuous metric source (DEM, landcover, roads, buildings, and
hydrology). A companion metadata overlay carries the source tags that the current
Arnis CMO exporter does not promote to vector feature classes: farmland, tree line,
settlement anchors, and crossing intent.

The companion overlay is not a navigation graph. It is not collision, passability,
line-of-sight, cover, concealment, fire-control, or damage authority. Those products
must be derived by their own owners and consumed only after a fail-closed contract is
accepted.

## Current artifacts

- Frozen Arnis request and synthetic OSM input:
  `tests/scenario/fixtures/environment_substrate/arnis_bundle_v1/eastern_plain_infantry_phase1/`.
- Native individual unit schema:
  `examples/config/database/ground/units/ground_infantry_soldier_mvp.json`.
- Training contract (not yet a train.py entry point):
  `examples/config/training/active/ground/eastern_plain_infantry_single_v1.contract.json`.
- Metadata-only semantic overlay builder:
  `tools/environment/arnis/field_overlay.py`.
- Offline composition gate:
  `tools/environment/arnis/field_acceptance.py`. The sample must pass slope,
  open-landcover, tree-cover, and semantic-count thresholds before passability
  derivation is considered.
- Deterministic contract/proxy scaffold:
  `python/rl/ground/infantry_proxy.py`. It is explicitly engineering-proxy-only
  and is not a native Ground runtime or RL training entry point.
- Gymnasium contract harness:
  `python/rl/ground/proxy_env.py` (`GroundInfantryProxyEnv`). It exercises the
  RL reset/step/observation/reward/termination/trace boundary only; its
  authority remains `engineering_proxy_only`.
- Maintained command projection:
  `python/rl/ground/command.py`. It carries the representable heading/speed
  and existing Ground static-task slice through the batch contract, while
  rejecting stance/route fields that the current native command shape cannot
  represent.

The proxy observation now includes explicit tree-line and settlement distance/
bearing values plus river/bridge flags. These remain replayable engineering
products. The native provider now admits continuous Arnis elevation/landcover
sampling and exposes a bounded terrain observation tuple; vector semantic and
track observation export remain held.

The `expected/` bundle has now been generated and verified with the pinned Arnis
v3.0.0 CMO patch, and the preview plus `field_acceptance.json` are retained. The
elevation and landcover providers remain network/cache backed, so this is a verified
evidence snapshot rather than a promise that any future network re-run will be
byte-identical.

## Single-soldier curriculum

1. **S0 contract/reset** — one named soldier, fixed seed, byte-equivalent initial
   observation and replay trace.
2. **S1 flat waypoint** — deterministic step and route progress on a simple surface;
   no crossing or held semantic is silently traversable.
3. **S2 terrain cost** — slope, landcover, farm track, river, and bridge passability
   become explicit products with owners and provenance.
4. **S3 observation** — tree-line and settlement observations are reported with
   unknown values preserved; no weapon behavior is introduced.
5. **S4 team transition** — only after the single-agent gates pass, add squad/command
   relationships and then revisit the existing ground damage slice.

The first runtime implementation should be a scripted controller and a deterministic
step/replay harness. Reinforcement learning is downstream of reset, action,
observation, reward, termination, and replay contracts; it must not be used to hide
missing terrain semantics.

The current native-runtime measurement and residuals are recorded in
[`native_runtime_blockers.md`](native_runtime_blockers.md). The native slice now
covers one deterministic `MoveStatic` step with surface/slope cost plus explicit
Arnis raster loading and terrain observation; the substitute still keeps vector
semantic and curriculum work moving without releasing a passability claim.

## Explicit held items

- automatic Arnis runtime setup and vector semantic map-provider consumption;
- route graph and passability mask;
- slope/wet-ground/river crossing policy;
- line-of-sight, cover, concealment, and exposure model;
- ground track/sensor observation export (terrain sampling is admitted separately);
- fatigue, medical, logistics, fires, suppression, and combat integration.
