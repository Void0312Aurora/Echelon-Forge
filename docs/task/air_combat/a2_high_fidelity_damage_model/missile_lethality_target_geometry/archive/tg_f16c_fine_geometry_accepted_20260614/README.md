# A2 TG F-16C Fine-Geometry Proxy Accepted Package

Status: `2026-06-14` accepted / retained archive record. The F-16C outer-shape and component fine-geometry engineering proxy is closed against the geometry-only acceptance gate; default runtime replacement, training benefit, lethality probability, structural breakup, debris, and weapon-specific conclusions are out of scope for this package.

Language:

- English companion: `README.md`
- Chinese canonical: [README.zh.md](README.zh.md)

Entrypoints:

- Current subproject pointer: [../../README.md](../../README.md)
- Acceptance record: [target_geometry_acceptance_20260614.md](target_geometry_acceptance_20260614.md)
- Stable review packet: [../../review_packets/f16c_20260611/](../../review_packets/f16c_20260611/)
- Geometry review test: [../../../../../../../tests/tools/test_airframe_geometry_review.py](../../../../../../../tests/tools/test_airframe_geometry_review.py)

## Archive Decision

This package confirms that the F-16C fine-geometry modeling scope of `missile_lethality_target_geometry` is closed. The accepted object is an engineering proxy: source-traced, scale-checked, mesh-aligned, reviewable, externally constrained, and parse-ready where appropriate, while all forbidden higher-authority claims remain refused.

The review packet stays at the stable `review_packets/f16c_20260611/` path instead of being physically moved into this archive package. Maintained tools, focused tests, and opt-in training configs still reference that path; moving it now would turn a closeout audit into a broad path migration. This package records the accepted lifecycle state while the original packet remains a retained evidence surface.

## Accepted Scope

- F-16C source, license, hash, axis, and public-dimension audit.
- `14` outer regions and mesh-derived fine proxy silhouettes.
- `26/26` current component bindings with `0` geometry hard blockers.
- `10` review-point distance diagnostics across nose, tail, beam, above, and below aspects.
- `14` surface component candidates, `14` semantic shell-volume candidates, and `26` constrained internal receiver priors.
- Semantic parent-child layout, cross-region held segments, and `8` R22 split receiver candidates.
- Whole-airframe silhouette constraints and subcomponent placement repairs, with the later projected mesh contour diagnostic now recording `0` receiver-prior protrusions after the R22 thin-prism/frustum shape correction and still sitting outside the runtime acceptance path.

## Out Of Scope

- Default F-16 unit database or default near-fuze projection replacement.
- Policy/reward diagnostics, training benefit, learned weapon employment, or win/loss semantics.
- True F-16C Block 50 manufacturer engineering geometry or internal equipment boundary claims.
- Structural breakup, debris, Pk, or weapon-specific AIM-120C/MQ-9 lethality conclusions.
- MQ-9 or other-airframe reuse.

## Verification

Rechecked for acceptance:

```powershell
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests/tools/test_airframe_geometry_review.py
git diff --check -- docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry tools/geometry/airframe_geometry_review.py tests/tools/test_airframe_geometry_review.py
```

Result: geometry review tests `5 passed`; diff whitespace check produced no output.
