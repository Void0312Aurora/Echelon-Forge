# A2 Target Geometry Dispatch Queue

Status: `2026-06-11` TG-P5-R1 complete / first dispatch queue. This records the
first-round progress; this round was completed by the main thread without a
worker dispatch.

Chinese canonical:
[missile_lethality_target_geometry_dispatch_queue_20260611.zh.md](missile_lethality_target_geometry_dispatch_queue_20260611.zh.md).

## Suggested First Round

| Packet | Cluster | Suggested Owner | Goal | Write set | Validation | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `TG-P1-R1` | `TG-P1` | main thread | Parse F-16 glTF and emit manifest plus scale/axis summary. | `tools/geometry/airframe_geometry_review.py`; `review_packets/f16c_20260611/manifest.json`; `tests/tools/test_airframe_geometry_review.py` | JSON parse; registry/glTF path existence; public-dimension check; `pytest -q tests/tools/test_airframe_geometry_review.py` | pass |
| `TG-P2-R1` | `TG-P2` | main thread | Generate first outer-region candidates from glTF bounds, position rules, and manual mapping. | `review_packets/f16c_20260611/f16c_geometry_mapping_candidate_20260611.json`; `top.svg`; `side.svg`; `front.svg`; focused tests | region schema; bounds check; SVG smoke; `pytest -q tests/tools/test_airframe_geometry_review.py` | pass |
| `TG-P3-R1` | `TG-P3` | main thread | Read current F-16 component boxes, bind regions, and flag anomalies. | `component_binding_report_20260611.json`; `component_binding_report_20260611.csv`; focused tests | every component has region or `needs_review`; `pytest -q tests/tools/test_airframe_geometry_review.py` | pass |
| `TG-P4-R1` | `TG-P4` | main thread | Generate first HTML/SVG review packet. | `review_packets/f16c_20260611/scene.html`; `top.svg`; `side.svg`; `front.svg` | local file existence; no external network dependency; `pytest -q tests/tools/test_airframe_geometry_review.py` | pass |
| `TG-P5-R1` | `TG-P5` | main thread | Emit distance diagnostics for nose 4 m / 6 m and related test points. | `review_point_diagnostics_20260611.json`; `review_point_diagnostics_20260611.csv`; focused tests | nearest outer/component distance and candidate count present; `pytest -q tests/tools/test_airframe_geometry_review.py` | pass |
| `TG-P6-R1` | `TG-P6` | main thread | Design the first finer-geometry proxy candidates. | `fine_geometry_proxy_design_20260611.zh.md`; `fine_geometry_proxy_design_20260611.md` | markdown links; `git diff --check` | pass as design draft; proxy JSON implementation remains queued |
| `TG-P6-R2` | `TG-P6` | main thread | Generate first fine-geometry proxy JSON and review overlay. | `fine_geometry_proxy_candidate_20260611.json`; optional SVG overlay; focused tests | proxy schema check; distance sanity; visual smoke | queued after `TG-P6-R1` |

## Main Thread Merge Checks

- Confirm workers did not store tokens, signed URLs, or Authorization headers.
- Confirm outputs do not claim true F-16 engineering structure or true weapon
  lethality.
- Confirm the review packet explains the 4 m nose case instead of only
  restating "not a direct hit."
- Confirm parent README status is synchronized only by the main thread.

## Held Items

- Runtime near-fuze projection integration: wait for `TG-P4`/`TG-P5`/`TG-P6`
  acceptance.
- MQ-9 geometry: wait until the F-16 toolchain is reusable.
- Structural breakup, debris/wreck, and Pk: later standalone subprojects.
