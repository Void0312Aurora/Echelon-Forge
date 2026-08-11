# TG-P6-R13 Internal Component Prior Geometry Constraints

Status: `2026-06-12` applied / review-only prior candidate / active runtime
activation still held. Chinese canonical:
[internal_component_prior_results_20260612.zh.md](internal_component_prior_results_20260612.zh.md).

This slice adds the mechanism where semantic shell regions act as parent
components and current internal/system receivers get simple constrained prior
geometry. It does not infer true internal structure from the shell mesh. It
generates low-fidelity sphere, cylinder, capsule, and ellipsoid candidates from
the current receiver boxes, then constrains them inside the parent shell support
bounds so receiver geometry no longer protrudes outside the airframe review
shell.

## Implemented

| Slice | Implementation | Boundary |
| --- | --- | --- |
| Receiver priors | Generates `sphere`, `cylinder`, `capsule`, and `ellipsoid` priors for all `26` current receivers, with recorded shape, axis, role, and rationale. | Priors are synthetic engineering review aids, not true F-16 internal layout. |
| Shell constraints | Each prior starts from the old component AABB center/scale, then is shifted or shrunk into semantic shell `support_bounds`. | Constraints use review support bounds, not closed physical bays. |
| Cross-region held | `engine_core` is constrained by the intake / aft engine bay / nozzle union; `wing_spar_center` is constrained by the center fuselage / wings / wing roots union and remains held. | This proves a non-protruding candidate can be generated; it does not accept ownership. |
| Review artifacts | Adds [internal_component_prior_candidate_20260611.json](review_packets/f16c_20260611/internal_component_prior_candidate_20260611.json), [CSV](review_packets/f16c_20260611/internal_component_prior_candidate_20260611.csv), and retired intermediate isolated views. | `runtime_active_component_count=0`; runtime behavior is unchanged. |

## Packet Summary

- Internal receiver priors: `26`.
- Shape coverage: `capsule=13`, `cylinder=4`, `ellipsoid=4`, `sphere=5`.
- Post-constraint protrusions: `0`.
- Cross-region held priors: `2`, namely `engine_core` and `wing_spar_center`.
- Active runtime priors: `0`.

## Preview Entrypoints

- Isolated pages: retired from the current final-result surface.
- View manifest: retired from the current final-result surface.

Layer meanings:

- Blue: source semantic mesh silhouette.
- Gray: shell constraint bounds.
- Purple: old receiver AABB.
- Cyan: constrained prior envelope.
- Red text: cross-region ownership held.

## Remaining Boundary

- R13 is not true internal bay modeling. It converts old receiver AABBs into
  better review-only prior shapes and constrains them within semantic shell
  bounds.
- `sphere`, `cylinder`, `capsule`, and `ellipsoid` are recorded as candidate
  primitives. Runtime activation still needs explicit tests and acceptance.
- `engine_core` and `wing_spar_center` are still not owned by a single shell
  region; they must be split or explicitly accepted as cross-region receivers.

## Verification

```bash
python -m py_compile tools/geometry/airframe_geometry_review.py
pytest -q tests/tools/test_airframe_geometry_review.py
python tools/geometry/airframe_geometry_review.py --out docs/systems/effects/reviews/f16c_target_geometry_20260614/review_packets/f16c_20260611
```

Focused result: `tests/tools/test_airframe_geometry_review.py` reports
`2 passed`; regenerated packet reports `internal_component_prior_count=26` and
`internal_component_prior_post_constraint_outside_count=0`.
