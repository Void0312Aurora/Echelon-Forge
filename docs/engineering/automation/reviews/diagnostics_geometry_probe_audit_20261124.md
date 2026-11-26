# Diagnostics and Geometry Probe Audit (#301)

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/engineering/automation/reviews/diagnostics_geometry_probe_audit_20261124.md`
Owner: `engineering/automation`
Last verified: `2026-11-24`

Addresses GitHub Issue `#301`: bounded, usage-led audit of `tools/diagnostics`
and `tools/geometry` (142 tracked Python files / 67,081 physical lines on
`main@6a9ce4eed`) and low-risk consolidation of genuinely duplicated utilities
without deleting or breaking historical evidence reproducers.

## 1. Top-20 Largest Script Inventory & Classification

Reference counts below reflect exact path/module/stem scans across `tests/`,
`tools/`, `.github/`, and `docs/` (excluding self-references). Note that
checkout LOC includes frozen historical evidence generators whose maintenance
cost is near zero when left untouched, whereas active maintenance burden comes
from scripts exercised by tests, `tools/diagnostics/README.md` entrypoints, or
shared helpers imported across multiple tools.

| # | LOC | Path | Refs (tests / tools / .github / docs) | Classification | Decision |
| --- | ---: | --- | --- | --- | --- |
| 1 | 4,173 | `tools/diagnostics/kill_chain_decoupling_probe.py` | 5 / 12 / 0 / 23 | `maintained shared helper` & `reproducible research probe` | **Retain** (heavy cross-tool & doc anchor) |
| 2 | 2,068 | `tools/diagnostics/fire_timing_fault_localization/window_position_sweep.py` | 1 / 3 / 0 / 4 | `reproducible research probe` | **Retain / freeze** (scientific review reproducer) |
| 3 | 1,437 | `tools/geometry/target_geometry_proxy_standoff_grid_probe.py` | 1 / 0 / 0 / 5 | `reproducible research probe` | **Freeze in place** (retained geometry evidence) |
| 4 | 1,399 | `tools/diagnostics/kill_chain_guidance_envelope_rebuild.py` | 2 / 2 / 0 / 1 | `reproducible research probe` | **Retain & deduplicate** (`_sha256` & CSV writer -> `common.py`) |
| 5 | 1,348 | `tools/diagnostics/kill_chain_guidance_scalar_calibration.py` | 1 / 1 / 0 / 1 | `reproducible research probe` | **Retain & deduplicate** (`_sha256` & CSV writer -> `common.py`) |
| 6 | 1,340 | `tools/diagnostics/kill_chain_guidance_calibration_visualize.py` | 1 / 0 / 0 / 2 | `reproducible research probe` | **Retain & deduplicate** (`_sha256` -> `common.py`) |
| 7 | 1,297 | `tools/geometry/airframe_review/constants.py` | 0 / 20 / 0 / 0 | `maintained shared helper` | **Retain** (airframe geometry review schema/data) |
| 8 | 1,252 | `tools/diagnostics/kill_chain_capture_structure_ablation.py` | 0 / 0 / 0 / 0 | `historical/one-off` | **Freeze in place** (zero active callers; CSV writer candidate if ever reopened) |
| 9 | 1,180 | `tools/geometry/target_geometry_lethality_matrix_probe.py` | 3 / 3 / 0 / 4 | `reproducible research probe` | **Retain / freeze** (referenced by tests, tools, composition closure) |
| 10 | 1,136 | `tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/lethality_chain.py` | 10 / 13 / 0 / 29 | `maintained shared helper` | **Retain** (active diagnostic probe backend) |
| 11 | 1,099 | `tools/diagnostics/event_credit_head/online_update.py` | 0 / 4 / 0 / 1 | `maintained shared helper` | **Retain** (called by maintained `event_credit_head_probe.py`) |
| 12 | 1,074 | `tools/diagnostics/kill_chain_maneuver_apn_admission.py` | 1 / 2 / 0 / 0 | `reproducible research probe` | **Freeze in place** (covered by `test_kill_chain_maneuver_apn_admission.py`) |
| 13 | 1,048 | `tools/geometry/airframe_review/report_writers.py` | 0 / 2 / 0 / 0 | `maintained shared helper` | **Retain** (used by `airframe_geometry_review.py`) |
| 14 | 1,045 | `tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/summarize.py` | 8 / 15 / 2 / 20 | `maintained shared helper` | **Retain** (active probe & workflow/test reference) |
| 15 | 990 | `tools/geometry/warhead_spatial_structural_admission.py` | 3 / 5 / 0 / 6 | `reproducible research probe` | **Freeze in place** (warhead spatial angular field admission evidence) |
| 16 | 932 | `tools/diagnostics/benchmarks/spatial_query.py` | 1 / 3 / 0 / 5 | `maintained entrypoint` (via `benchmark.py` / `benchmark_registry.py`) | **Retain** (active benchmark suite) |
| 17 | 889 | `tools/geometry/airframe_review/runtime_activation.py` | 3 / 7 / 0 / 18 | `maintained shared helper` | **Retain** (airframe review CLI/manifest fixture tests) |
| 18 | 881 | `tools/geometry/airframe_review/views/views_shape_placement.py` | 0 / 1 / 0 / 0 | `maintained shared helper` | **Retain** (view helper for `review_views.py`) |
| 19 | 839 | `tools/geometry/airframe_review/review_packet.py` | 3 / 31 / 0 / 118 | `maintained shared helper` | **Retain** (core packet builder for airframe/kill-chain reviews) |
| 20 | 809 | `tools/diagnostics/fire_timing_fault_localization/chain_breakpoint.py` | 1 / 3 / 0 / 15 | `maintained shared helper` | **Retain** (called by `fire_timing_fault_localization_probe.py`) |

Additional #21–#25 sampled scripts with direct consolidation relevance:
- `tools/diagnostics/kill_chain_guidance_exact_mechanism_ablation.py` (764 LOC, refactored below)
- `tools/diagnostics/kill_chain_guidance_mechanism_ablation.py` (634 LOC, covered by tests, refactored below)

## 2. Demonstrated Redundancies Consolidated

1. **Chunked SHA-256 artifact digest helper (`tools.diagnostics.common.file_sha256`)**:
   - Identical 6-line chunked `hashlib.sha256` readers (`_sha256(path)`) were duplicated in:
     - `tools/diagnostics/kill_chain_guidance_envelope_rebuild.py`
     - `tools/diagnostics/kill_chain_guidance_scalar_calibration.py`
     - `tools/diagnostics/kill_chain_guidance_calibration_visualize.py`
   - Consolidated onto `tools.diagnostics.common.file_sha256` (re-bound as `_sha256` where existing tests inspect `module._sha256`), preserving exact byte hashing including empty files.
2. **Sorted-union CSV writer (`tools.diagnostics.common.write_csv_rows`)**:
   - Identical `csv.DictWriter(..., fieldnames=sorted(...), lineterminator="\n")` loops (`_write_csv(path, rows)`) with per-script `_csv_value` serialization were duplicated in:
     - `tools/diagnostics/kill_chain_guidance_envelope_rebuild.py`
     - `tools/diagnostics/kill_chain_guidance_scalar_calibration.py`
     - `tools/diagnostics/kill_chain_guidance_exact_mechanism_ablation.py`
     - `tools/diagnostics/kill_chain_guidance_mechanism_ablation.py`
   - Consolidated onto `tools.diagnostics.common.write_csv_rows(path, rows, value_transform=_csv_value)`. Note: `exact_mechanism_ablation` and `mechanism_ablation` encode nested `list`/`dict` with `ensure_ascii=True`, whereas `envelope_rebuild` and `scalar_calibration` use `ensure_ascii=False` (and `allow_nan=False` in `scalar_calibration`), so parameterizing `value_transform` preserves 100% output-schema and byte parity while removing the duplicated `csv.DictWriter` boilerplate.
3. **Net LOC impact**:
   - Added 35 lines (including spacing/docstrings) of shared helpers in `tools/diagnostics/common.py` (`file_sha256`, `write_csv_rows`) plus 10 import lines across the 5 callers (`+45` insertions).
   - Removed 59 duplicated lines across the 5 kill-chain guidance scripts (net `-14` LOC across `tools/diagnostics/`, plus parity coverage in `tests/tools/test_diagnostics_common_consolidation.py`).
   - Remaining similar `_sha256` / `_write_csv` copies in frozen one-off/admission probes (`kill_chain_p10_apn_null_band_followup.py`, `kill_chain_p11_expectation_rebaseline.py`, `kill_chain_p11_terminal_track_sensitivity.py`, `kill_chain_maneuver_apn_admission.py`, `kill_chain_integrated_admission.py`, `kill_chain_capture_structure_ablation.py`) are left frozen in place until touched for functional changes, per Issue #301's low-risk scope.
