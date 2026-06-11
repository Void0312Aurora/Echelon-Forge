# TG-P6 Fine Geometry Proxy Design

Status: `2026-06-11` TG-P6-R1 design draft. Chinese canonical:
[fine_geometry_proxy_design_20260611.zh.md](fine_geometry_proxy_design_20260611.zh.md).

## Purpose

TG-P1 through TG-P5 made the target-geometry problem reviewable, but the first
outer regions are still boxes. TG-P6 defines the next shape layer before any
runtime near-fuze, continuous-rod, or fragment projection consumes the new
geometry.

The goal is to move from review boxes to shape-closer proxies: oriented boxes,
thin prisms, convex hulls, and eventually simplified shell meshes.

## Boundaries

- Do not use the high-poly GLB as a per-frame collision mesh.
- Do not infer true internal equipment boundaries from the visual model.
- Do not claim true F-16 engineering geometry, true weapon lethality,
  structural breakup, or debris behavior.
- Do not hide left/right sign, oversized component, or placement issues behind
  a more complex shape.

## Proxy Layers

| Layer | Shape | Use | Runtime precondition |
| --- | --- | --- | --- |
| `review_aabb` | current boxes | First human review and gap finding | Review only |
| `obb` | oriented box | Fuselage, canopy, intake, engine sections | Center, axes, half extents, and SVG overlay |
| `thin_prism` | thin prism | Wings and tail surfaces | Must avoid counting large empty air as target body |
| `convex_hull` | point hull | Nose, wing roots, irregular transitions | Vertex source and simplification error recorded |
| `simplified_shell` | simplified outer mesh | Final distance and crossing candidate | Separate review and performance assessment |

## First Region Choices

- Nose: `convex_hull` or tapered `thin_prism`.
- Forward/center/aft fuselage: `obb`.
- Canopy and intake: independent `convex_hull` or small `obb`.
- Engine nozzle: short `obb`, later circular-section simplification.
- Wings and horizontal/vertical tails: `thin_prism`.
- Wing roots: `convex_hull` or two-side transition proxy.

## Runtime Use

- Near fuze: compute nearest outer distance and nearest outer region only; do
  not decide kill directly.
- Continuous rod: intersect the rod path or swept volume against outer proxies,
  then pass candidate regions/components to the existing damage chain.
- Fragments: intersect fragment paths with outer proxies, rank candidate
  components, and keep damage effects in the existing component chain.
- Flight outcome remains a result of component damage feeding existing flight
  dynamics, not a separate geometry-layer rule.

## First Implementation Order

1. Emit `fine_geometry_proxy_candidate_20260611.json` for the `14` F-16 outer
   regions.
2. Generate `thin_prism` for wings/tails, `obb` for fuselage sections, and
   review-required `convex_hull` candidates for nose/canopy/intake.
3. Overlay fine proxies against current boxes and output volume, envelope, and
   review-point distance deltas.
4. Resolve left/right coordinate signs before using wing proxies for path
   candidates.
5. Discuss runtime integration only in TG-P7, after TG-P6 review passes.

## Acceptance Criteria

- Every outer region has a finer proxy candidate or an explicit hold reason.
- Fine proxies cover less obvious empty air than the current boxes, especially
  wings, tails, nose, and intake.
- Nose, beam, above, and below review points report old-vs-new distance deltas.
- Left/right sign issues remain visible and are not silently corrected.
- Outputs remain review candidates and do not enter the runtime main path.
