# A2 Target Geometry Dispatch Queue

Status: `2026-06-12` TG-P6-R4 complete / human review dashboard generated.
This records the first-round progress plus the TG-P6 continuation; these
rounds were completed by the main thread without a worker dispatch.

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
| `TG-P6-R1` | `TG-P6` | main thread | Design the first finer-geometry proxy candidates. | `fine_geometry_proxy_design_20260611.zh.md`; `fine_geometry_proxy_design_20260611.md` | markdown links; `git diff --check` | pass as design draft |
| `TG-P6-R2` | `TG-P6` | main thread | Generate first fine-geometry proxy JSON and review overlay. | `fine_geometry_proxy_candidate_20260611.json`; `fine_proxy_top.svg`; `fine_proxy_side.svg`; `fine_proxy_front.svg`; focused tests | proxy schema check; distance sanity; visual smoke; `pytest -q tests/tools/test_airframe_geometry_review.py` | pass as review-only candidate; human review still required before `TG-P7` |
| `TG-P6-R3` | `TG-P6` | main thread | Replace rectangle-only fine overlay with mesh-derived top/side/front silhouettes from audit glTF vertices. | `tools/geometry/airframe_geometry_review.py`; `fine_geometry_proxy_candidate_20260611.json`; `fine_proxy_*.svg`; focused tests | mesh silhouette schema check; inflated fallback visibility; visual smoke; `pytest -q tests/tools/test_airframe_geometry_review.py` | pass as review-only silhouette candidate; `6` inflated-bound fallbacks require review before `TG-P7` |
| `TG-P6-R4` | `TG-P6` | main thread | Generate a human review dashboard with per-region zoom panels and flags. | `fine_proxy_review_dashboard.html`; `scene.html`; focused tests | dashboard smoke; candidate/review/hold status visible; component overlays visible; `pytest -q tests/tools/test_airframe_geometry_review.py` | pass as human review aid; still not runtime geometry |

## Main Thread Merge Checks

- Confirm workers did not store tokens, signed URLs, or Authorization headers.
- Confirm outputs do not claim true F-16 engineering structure or true weapon
  lethality.
- Confirm the review packet explains the 4 m nose case instead of only
  restating "not a direct hit."
- Confirm fine proxy outputs stay review-only and keep left/right sign review
  visible instead of silently correcting wing or tail proxies.
- Confirm inflated-bound fallback silhouettes remain visible and do not get
  treated as precise engineering geometry.
- Confirm parent README status is synchronized only by the main thread.

## Held Items

- Runtime near-fuze projection integration: wait for `TG-P4`/`TG-P5`/`TG-P6`
  acceptance.
- MQ-9 geometry: wait until the F-16 toolchain is reusable.
- Structural breakup, debris/wreck, and Pk: later standalone subprojects.
