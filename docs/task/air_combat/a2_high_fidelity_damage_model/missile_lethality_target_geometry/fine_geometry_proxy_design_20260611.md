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
4. Generate review-only surface component candidates for each outer region and
   list the current internal components or missing links they may hand off to.
5. Resolve left/right coordinate signs before using wing proxies for path
   candidates.
6. Discuss runtime integration only in TG-P7, after TG-P6 review passes.

## Acceptance Criteria

- Every outer region has a finer proxy candidate or an explicit hold reason.
- Fine proxies cover less obvious empty air than the current boxes, especially
  wings, tails, nose, and intake.
- Nose, beam, above, and below review points report old-vs-new distance deltas.
- Left/right sign issues remain visible and are not silently corrected.
- Candidate links from outer regions to surface components and from surface
  components to current internal components are reviewable.
- Outputs remain review candidates and do not enter the runtime main path.

## TG-P6-R3 Implementation Note

`2026-06-12`: the mesh-derived review layer now filters audit glTF vertices by
each source region and an explicit audit-node whitelist, generates top/side/front
2D convex hull silhouettes, and overlays those polygons in `fine_proxy_*.svg`.
The previous bounds-expansion fallback has been removed; if the node whitelist
and region bounds cannot produce a closed silhouette, the region must fail into
manual review. These silhouettes are still review-only and remain held from
runtime use until `TG-P7`.

## TG-P6-R5 Implementation Note

`2026-06-12`: `surface_component_candidate_20260611.json` and CSV now turn the
`14` outer regions into review-only surface components. Each surface component
records likely surface damage, linked current internal components, old
component-box drift, left/right sign review, and missing explicit runtime
component links. This answers "which part should this outer hit hand off to"
without claiming true internal structure or changing the runtime near-fuze,
continuous-rod, or fragment paths.

## TG-P6-R6 Implementation Note

`2026-06-12`: `human_review_triage.html` now groups the manual-review queue into
visual cards for coordinate-sign, component-placement, surface-handoff, and
review-point sanity issues. Each card carries local top/side/front overlays, so
human review can start from the geometry picture instead of trying to infer the
problem from CSV rows.

## TG-P6-R7 Visual Findings Note

`2026-06-12`: `human_review_findings_20260612.zh.md` and its English companion
now record the first actual visual findings. At that R7 snapshot, TG-P6
artifacts remained valid as review-only evidence, but side-sign convention,
nose radar/IFF, engine/nozzle, missing runtime surface components, and
`wing_spar_center` cross-region semantics blocked `TG-P7`; that blocker set was
later refined by R9/R10 and superseded by the R11 repair note below.

## TG-P6-R8 Isolated View Note

`2026-06-12`: `component_review_views/` now generates a separate page and
top/side/front SVGs for each current component, each surface-to-single-component
or missing-link handoff, and each review-point candidate component. The manifest
currently records `75` review-only isolated pages after R11 regeneration, so reviewers do not have to
infer individual relationships from crowded overview cards.

## TG-P6-R9 Independent Review Note

`2026-06-12`: `subagent_independent_review_findings_20260612.zh.md` and its
English companion summarize five read-only subagent reviews. The review refines
coarse earlier judgments: `engine_core` and `wing_spar_center` should first be
handled as cross-region semantics. At that R9 snapshot, side-sign, radar/IFF,
afterburner/nozzle, and missing runtime relations were still hard blockers.

## TG-P6-R10 Subagent Correction Note

`2026-06-12`: `subagent_correction_results_20260612.zh.md` and its English
companion record the first write-scoped correction pass. `apg68_radar_array`,
`iff_interrogator`, and `afterburner_nozzle` now bind cleanly to their target
regions; `engine_core` and `wing_spar_center` are represented as review-only
cross-region semantics. At the R10 snapshot, `TG-P7` remained held for side-sign
and missing runtime receiver work; that blocker set is superseded by R11.

## TG-P6-R11 Geometry Repair Note

`2026-06-12`: `geometry_repair_results_20260612.zh.md` and its English
companion record the main-thread repair pass after R10. Left/right wing,
wing-root, and horizontal-tail region mapping now matches the component-side
convention; wing and wing-root component boxes are placed on the mesh-derived
surfaces; canopy, intake, and horizontal-tail receiver components exist in the
F-16 damage model. The regenerated packet has `0` component `needs_review`, `0`
surface `needs_review`, `0` side-sign blockers, and `0` missing runtime receiver
relations. `TG-P7` remains held only for explicit ownership of the
`engine_core` and `wing_spar_center` cross-region semantics.
