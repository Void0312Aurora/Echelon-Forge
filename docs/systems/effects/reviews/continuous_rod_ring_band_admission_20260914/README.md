# Continuous-Rod Expanding Ring-Band Admission (2026-09-14)

## Decision

The P6 explicit continuous-rod expanding ring/band geometry passes its independent geometry admission. Across the complete 192-case matrix, 120 cases intersect maintained hitbox/component AABBs and 72 are rejected by geometry. Intersection state, model-owned trace state, sampled angular coverage, and zero/non-zero effect state close without residuals.

This does not admit the complete Warhead Spatial Field or integrated kill chain. The ±6° band is synthetic, default weapon profiles retain `legacy_side_sweep`, and all 24 surviving 10 m intersections are clamped to the projection minimum of `0.05`. P7 floor/clamp admission therefore remains open.

## Model semantics

The opt-in `expanding_ring_band` model samples azimuth around the warhead forward axis and polar layers across the band thickness. Finite rays are intersected with actual target AABBs. An azimuth segment counts once if any polar ray intersects, and `rod_count × angular_coverage` drives the rod hit estimate. A non-intersection rejects the projection candidate before any floor or clamp can create a synthetic hit. The legacy axis/orientation scalar pair is not applied again on the explicit path.

The default remains compatibility-safe: the new path activates only when a profile explicitly selects `continuous_rod_spatial_model = "expanding_ring_band"`.

## Evidence

The matrix covers six envelope-face directions, `0.5 / 2 / 6 / 10 m` face-referenced standoff, and eight headings at 45° intervals. The admitted configuration uses 720 azimuth samples, 5 polar layers, and a ±6° band.

![Continuous-rod ring-band structural evidence](continuous-rod-ring-band-evidence.png)

Hard-gate results:

- 192/192 rows present; 120 intersections and 72 geometric rejections.
- Zero geometry-closure, 180° symmetry, left/right mirror, distance-topology, distance-monotonicity, or axial-rejection residuals.
- 288→720 azimuth refinement: zero classification changes, maximum coverage delta `0.0034722`, maximum effect delta `0.0043464`.
- 720-sample half-step phase shift: zero classification changes, maximum coverage delta `0.0027778`, maximum effect delta `0.0037111`.
- 5→9 polar refinement: zero classification changes, maximum coverage delta `0.0041667`, maximum effect delta `0.0032000`.
- Legacy/default comparison: 192 rows, zero mismatches, and zero explicit-ring activations.

## Boundary and next gate

This packet establishes explicit geometric topology only. It does not establish physical rod breakup dynamics, calibrated material/rod parameters, component failure probability, real-weapon Pk, or integrated guidance/fuze authority.

The next batch is P7: paired projection-minimum ablation and component-load propagation at the 10 m boundary. P8 Component Load Admission and any default-profile promotion follow separately.

Reproduce with:

```powershell
$env:CMO_BUILD_DIR = 'D:\workshop\Research\Echelon-Forge\build-warhead-spatial-admission-vs'
python tools/geometry/continuous_rod_ring_band_admission.py
python tools/geometry/render_continuous_rod_ring_band_evidence.py
```

The machine-readable packet is `review_packets/continuous_rod_ring_band_admission_20260914.json`.
