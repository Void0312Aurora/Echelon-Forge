# A2 Target Geometry Task Clusters

Status: `2026-06-11` finite task-cluster plan for [README.md](README.md).

Chinese canonical:
[missile_lethality_target_geometry_task_clusters_20260611.zh.md](missile_lethality_target_geometry_task_clusters_20260611.zh.md).

## Boundary Decision

This subproject turns F-16 outer shape, component regions, and test-point
distances into reviewable facts. The first round must not change the maintained
near-fuze projection path, tune probabilities to hide geometry errors, or claim
true F-16 engineering geometry, true weapon lethality, structural breakup, or
debris/wreck behavior.

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `TG-P0` | main thread | n/a | Create subproject entry, status, and dispatch queue. | `docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry/**`; parent A2 README; issue pointer | No tool implementation; no runtime change | markdown links, `git diff --check` | Docs are navigable from parent and issue | none | 1 | pass |
| `TG-P1` | main thread | high | Parse F-16 glTF and generate source/axis/scale manifest. | `tools/geometry/airframe_geometry_review.py`; `.../review_packets/f16c_20260611/manifest.json`; `tests/tools/test_airframe_geometry_review.py` | No runtime collision mesh | JSON parse, path existence, public-dimension error check, focused pytest | Manifest records GLB/glTF roles, hashes, axes, and scale | after `TG-P0` | 2 | pass |
| `TG-P2` | main thread | high | Generate low-fidelity outer regions from the audit model. | `review_packets/f16c_20260611/f16c_geometry_mapping_candidate_20260611.json`; `top.svg`; `side.svg`; `front.svg`; focused tests | Do not treat node names as true components | region count check, bounds inside scaled envelope, SVG smoke | Major regions are visible in top/side/front views | depends on `TG-P1` | 2 | pass |
| `TG-P3` | main thread | high | Bind current component boxes to outer regions and flag anomalies. | `component_binding_report_20260611.json`; `component_binding_report_20260611.csv`; focused tests | No vulnerability-probability rewrite | schema check, out-of-envelope report check, focused pytest | Every current component has a region or explicit `needs_review` | depends on `TG-P2` | 2 | pass |
| `TG-P4` | main thread | medium | Generate static HTML/SVG review packet. | `review_packets/f16c_20260611/scene.html`; SVG; README summary | No web app runtime integration | file existence, no network dependency, basic HTML asset checks | Packet can be opened offline and shows outer shape, legacy boxes, components, and test points | depends on `TG-P2`/`TG-P3`; completed with `TG-P5` | 2 | pass |
| `TG-P5` | main thread | high | Emit outer/component distance diagnostics for MLF-5 test points. | review point JSON/CSV; focused tests | No real-weapon Pk rerun | CSV rows include nearest outer distance, nearest component distance, candidate count | 4 m nose case has concrete geometry evidence | depends on `TG-P2`; completed with `TG-P4` | 2 | pass |
| `TG-P6` | main thread | high | Design finer geometry proxies: oriented boxes, convex hulls, or simplified shell meshes. | mapping refinement JSON; proxy review notes; optional SVG overlay | No high-poly GLB as per-frame collision mesh | proxy schema check, distance sanity, visual overlay smoke | Error, fit boundary, and manual-review items from coarse boxes to finer proxies are recorded | depends on `TG-P4`/`TG-P5` | 2 | planned |
| `TG-P7` | main thread | high | Decide runtime-interface boundary and close as accepted or held. | README/status/acceptance docs; optional design note | No unreviewed proxy in the main path | doc audit, targeted tests if runtime design is accepted | accepted or held decision records next work | depends on `TG-P6` | 1 | planned |

## Dispatch Rules

- Every worker packet must map to exactly one cluster above.
- `TG-P1` through `TG-P6` must not edit the parent README status line; parent
  synchronization is main-thread work.
- Do not let two workers edit the same mapping JSON, manifest, or status doc at
  the same time.
- Any source or license supplement must record source, license, hash, and
  retrieval date; never store tokens, signed URLs, or Authorization headers.
- Any runtime integration discussion waits for `TG-P4`, `TG-P5`, and `TG-P6`
  acceptance.

## Worker Packet Requirements

Each worker returns:

- changed file list;
- key assumptions;
- validation commands and results;
- unresolved risks;
- whether any forbidden claim was touched;
- whether main-thread merge or human review is needed.

## Validation Plan

- `git diff --check -- docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry`
- JSON/schema parse for generated manifest, mapping, and review-point files.
- F-16 registry/runtime asset path existence check.
- glTF audit asset path existence check.
- Offline packet smoke: generated HTML/SVG/CSV files exist and reference local
  assets only.
- Targeted runtime tests only after a later runtime-interface decision.

## Acceptance Criteria

- The F-16 review packet shows outer shape, legacy hitboxes, component boxes,
  and test points together.
- Diagnostics separate local coordinates, outer-surface distance,
  component-surface distance, direct-hit state, and candidate-component count.
- The 4 m nose close-to-shape case is no longer explained only as "not direct,
  therefore no damage."
- Docs continue to reject true engineering geometry, structural breakup,
  debris/wreck, Pk, and weapon-specific kill claims.

## Residual Map

- MQ-9 geometry: later reuse target, not in the first F-16 acceptance.
- Structural breakup and debris/wreck: later standalone subprojects.
- Pk and real-weapon calibration: later standalone subprojects.
- Main runtime-path replacement: depends on human review packet and diagnostics
  acceptance.
- Finer geometry proxy: first round is F-16 only and does not commit MQ-9 or
  other aircraft.
