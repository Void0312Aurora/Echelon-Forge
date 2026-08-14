# Hitbox Geometry Visual Review Tool Design

Status: `2026-06-11` proposed design for [README.md](README.md). This document designs the tool and data gates only; it does not replace runtime geometry.

Chinese companion: not maintained (English-only work surface); this English page is canonical.

## Goal

Build a small review tool that exports the visual GLB, public dimensions, outer regions, current component boxes, and scenario points into human-reviewable graphics or a scene. It should answer whether the geometry is reasonable, whether distance conventions are clear, and whether components sit in plausible regions before later lethality probability models consume those facts.

The first output is a geometry review packet, not a runtime replacement:

- a static HTML/Three.js scene for rotating the outer shape, regions, component boxes, and test points;
- top/side/front SVG projections for quick review;
- a JSON manifest recording source, hash, axes, scale, outer regions, component bindings, and review state;
- a diagnostics table for each review point: local coordinate, nearest outer-surface distance, nearest component distance, direct-hit state, and candidate component count.

## Current Asset Observation

Local F-16 asset:

- Current runtime GLB: [examples/viz/web_viz/static/assets/air/f16_c_falcon_carlos_maciel/f16_c_falcon_carlos_maciel.glb](../../../../../../examples/viz/web_viz/static/assets/air/f16_c_falcon_carlos_maciel/f16_c_falcon_carlos_maciel.glb)
- Current audit glTF scene: [examples/viz/web_viz/static/assets/air/audit/f16_c_falcon_carlos_maciel/gltf/scene.gltf](../../../../../../examples/viz/web_viz/static/assets/air/audit/f16_c_falcon_carlos_maciel/gltf/scene.gltf)
- Current audit glTF source archive: retired from the working tree on 2026-08-13 because it only re-packages the extracted `gltf/` scene above; recover it with `git show 5f95ee9d6544a7ede91be0474c76cf5ea045a708:examples/viz/web_viz/static/assets/air/audit/f16_c_falcon_carlos_maciel/4bc2ff75dc584af2afd0aa6bd8b79015_gltf.zip`
- Archived old FlightGear candidate: retired from the working tree on 2026-08-13; recover it with `git show 5f95ee9d6544a7ede91be0474c76cf5ea045a708:examples/viz/web_viz/static/assets/archive/f16_flightgear_gplv2_candidate_20260611/f16.glb`
- Retirement record for both, with sizes and SHA-256 digests: [examples/viz/web_viz/static/assets/audit_ledger.md](../../../../../../examples/viz/web_viz/static/assets/audit_ledger.md)
- Same file in the Godot archive: `archive/20260530_game_godot_local_archive/game/client/godot_project/assets/models/f16.glb` (local-only, untracked)
- Current replacement source: Sketchfab `F16-C Falcon`, UID `4bc2ff75dc584af2afd0aa6bd8b79015`, author `Carlos.Maciel`, license `CC-BY-4.0`.
- Current replacement source archive SHA256: `47388fb8646e704609712d55e0b53eb014571644b7344c7859276597fc63e248`.
- Current runtime GLB SHA256: `243f164005c49bce0bb25202e449911fed99cbfa94e9bef25321dcbd7476d44f`.
- Current replacement geometry scale: Sketchfab metadata `4,504` faces / `2,563` vertices; locally parsed `4,504` triangles / `13,415` position-accessor vertices; post-node-transform world span about `5.833 x 2.824 x 9.136`, registry display scale `1.65`.
- Useful replacement node names: `Canopy01_1`, `Eject_Seat_3`, `Pilot_4`, `ElevatorR01_7`, `AileronR01_8`, `AileronL01_9`, `VoletR01_14`, `VoletL01_15`, `EngineL01_17`, `RudderL01_18`.
- Old FlightGear candidate SHA256: `7c432edcaec14bc52a262d2ef311b19c525452e2614400c3c10f8e93da1b7ee0`.
- Old FlightGear candidate local filesystem timestamps: the previous `examples/viz` copy had birth `2026-01-20T00:35:49+08:00` and mtime `2026-01-20T00:35:50+08:00`; the Godot archive copy has birth/mtime `2026-05-15T17:43:08+08:00`.
- Old FlightGear candidate first Git introduction: `bf1597d45486f3f866ec523a9d572e84374799d3`, author/commit time `2026-01-21T14:21:10+08:00`, subject `1·21-14：21|更新v0.0.7`.
- Old FlightGear candidate GLB metadata: only `Khronos glTF Blender I/O v5.0.21`; no `source`, `author`, `license`, or Sketchfab UID.
- Old FlightGear candidate geometry scale: about `4,989` triangles; position accessor vertex count about `4,684`; accessor envelope about `15.65 x 9.59 x 5.17`.

Local source records:

- `Temp/Model/resource.md` (local-only, untracked) records DDG, Patuxent, and low-poly missile sources, but not F-16.
- [examples/viz/web_viz/static/assets/missiles/ATTRIBUTION.md](../../../../../../examples/viz/web_viz/static/assets/missiles/ATTRIBUTION.md) and [uav/ATTRIBUTION.md](../../../../../../examples/viz/web_viz/static/assets/uav/ATTRIBUTION.md) already attribute missiles/MQ-9; there is no equivalent F-16 attribution record.

FlightGear provenance lead:

- The user-provided download record points to [FlightGear Aircraft-2018 f16.zip](https://mirrors.ibiblio.org/flightgear/ftp/Aircraft-2018/f16.zip). The server reports `Last-Modified: Fri, 29 May 2020 00:16:42 GMT` and `Content-Length: 312425093`.
- The archive contains a `f16/` FlightGear F-16 package with `1215` entries, including `f16/LICENSE`, `f16/README.md`, `f16/authors.txt`, `f16/Models/f16.ac`, and `f16/Models/F-16.xml`.
- Key archive timestamps: `f16/LICENSE` is `2018-10-13T21:07:10`, `f16/authors.txt` is `2020-05-09T04:15:28`, `f16/Models/f16.ac` is `2020-05-09T04:15:22`, `f16/Models/F-16.xml` is `2020-05-29T00:15:10`, and `f16/README.md` is `2020-05-29T00:15:14`.
- `LICENSE` is GNU GPL v2. `README.md` identifies the package as the FlightGear F-16 Fighting Falcon, and `authors.txt` lists contributors including Erik Hofman, Nikolai V. Chr., J Maverick 16, Richard Harrison, and Justin Nicholson.
- Existing A2 data collection already pinned [FlightGear `NikolaiVChr/f16`](https://github.com/NikolaiVChr/f16), commit `190a699c77bd3c2c7da1e3bb4bffc7a6013bc8f5`, as an open-source community simulation candidate for shape/name sanity only.
- GitHub `master` currently still resolves to `190a699c77bd3c2c7da1e3bb4bffc7a6013bc8f5`, matching the existing source pin.
- The local GLB strongly matches FlightGear `f16/Models/f16.ac` by object names: all `117` local node/mesh names were found in `f16.ac` named objects, including `AirIntake`, `RadarDomeTop`, `CanopyBackInside`, `LeftUpperAileron`, `RightUpperAileron`, `LeftUpperFlap`, `RightUpperFlap`, `Rudder`, `Tail`, `VentralFins`, `LWStation1`, and `RWStation1`.
- Geometry counts are not identical: the local GLB has about `4,989` triangles and `4,684` position-accessor vertices, while FlightGear `f16.ac` is `1,706,737` bytes with `124` named objects, `10,470` total `numvert`, and a rough triangulated floor of about `17,722` faces. This suggests Blender conversion, merging, pruning, or retriangulation. The object-name match supports a strong source candidate, but not a vertex-for-vertex reproduction proof.
- The user-provided `blob:https://github.com/70ccc3e5-b369-4d7d-b88d-0dce6c4ea77f` is a browser-local blob URL. It only indicates that the object was created under the GitHub origin; it is not a fetchable GitHub file path and cannot prove source by itself.

Initial online candidates:

- Sketchfab has `F16-C Falcon` by Carlos.Maciel, downloadable for free, but the current local GLB lacks a verifiable UID and the FlightGear object-name match is stronger. This lead is now secondary.
- The `F16-C Falcon` candidate's Sketchfab API record says UID `4bc2ff75dc584af2afd0aa6bd8b79015`, createdAt `2022-02-28T12:38:47.839845`, publishedAt `2022-02-28T12:46:12.308593`, author `Carlos.Maciel`, license `CC Attribution / CC BY 4.0`, and faceCount `4504`. That face count is close to but not identical to the locally parsed about `4,989` triangles, so it is only a candidate lead, not match proof.
- Sketchfab also has several other free F-16 models, including `F-16 Fighting Falcon - Fighter Jet - Free`, `F-16 Fighting Falcon Jet Fighter Aircraft`, and `Low-Poly F-16 Fighting Falcon`; their triangle counts or license terms do not clearly match the current local file.

Conclusion: the current F-16 GLB is a strong FlightGear GPL v2 source candidate, but it should not enter the mainline geometry-derived path. It remains only a historical provenance lead and local comparison asset. Follow-up mainline geometry candidates should restart from the [Sketchfab F-16 Replacement Shortlist](sketchfab_f16_replacement_shortlist_20260611.md), prioritizing downloadable CC BY 4.0 or broader assets.

## Source Admission Gate

The geometry tool must emit `asset_source_status`:

| Status | Meaning | Allowed use |
| --- | --- | --- |
| `verified_redistributable` | source, author, license, and hash are recorded; license allows derived geometry to be redistributed with the repo | generated outer proxies and review packets may be committed |
| `matched_flightgear_gplv2_candidate` | FlightGear source, authors, GPL v2 license, and object-name match evidence are recorded; still a community simulation asset, not official geometry | local review, three-view overlays, and coarse region drafts; derived geometry needs an explicit GPL v2 acceptance policy before mainline use |
| `rejected_for_mainline_license` | source is traceable, but the license would add unnecessary relicensing obligations to mainline geometry data | historical lead or local comparison only; no mainline derived geometry |
| `verified_review_only` | source and license are recorded, but terms restrict usage to local/non-commercial/non-authoritative review | local review only; derived geometry cannot become mainline fact |
| `source_unverified` | only file and hash exist, source/license are not closed; if the FlightGear match is later rejected, F-16 falls back to this state | local candidate review only; not authoritative geometry |
| `rejected` | provenance or license is unsuitable, or model does not fit the aircraft | excluded from the geometry pipeline |

The existing FlightGear F-16 asset should be treated as `rejected_for_mainline_license`. Follow-up should:

- retain FlightGear attribution and match evidence to avoid repeated provenance work; and
- replace it with a source-clear Sketchfab GLB whose license is better suited for derived geometry distribution.

## Data Layers

### 1. Visual Asset Layer

Example:

```json
{
  "asset_id": "f16c_visual_candidate_20260611",
  "runtime_visual_path": "examples/viz/web_viz/static/assets/air/f16_c_falcon_carlos_maciel/f16_c_falcon_carlos_maciel.glb",
  "audit_scene_path": "examples/viz/web_viz/static/assets/air/audit/f16_c_falcon_carlos_maciel/gltf/scene.gltf",
  "source_status": "visual_reference_derived",
  "source_ref": "Sketchfab F16-C Falcon / UID 4bc2ff75dc584af2afd0aa6bd8b79015",
  "source_license": "CC-BY-4.0",
  "visual_glb_sha256": "243f164005c49bce0bb25202e449911fed99cbfa94e9bef25321dcbd7476d44f",
  "archive_sha256": "47388fb8646e704609712d55e0b53eb014571644b7344c7859276597fc63e248",
  "asset_bounds_m": [5.833, 2.824, 9.136],
  "axis_map": {
    "asset_x": "sim_right",
    "asset_y": "sim_up",
    "asset_z_negative": "sim_forward"
  }
}
```

### 2. Outer Region Layer

Outer regions come from GLB nodes, node-name rules, and manual correction:

```json
{
  "outer_regions": [
    {"id": "nose_radome", "source_nodes": ["RadarDomeTop"], "role": "outer_skin"},
    {"id": "canopy", "source_nodes": ["CanopyBackInside", "CanopyForwardOutside"], "role": "outer_skin"},
    {"id": "air_intake", "source_nodes": ["AirIntake"], "role": "outer_skin"},
    {"id": "left_wing", "source_nodes": ["LeftUpperAileron", "LeftUpperFlap", "LWStation1"], "role": "lifting_surface"},
    {"id": "right_wing", "source_nodes": ["RightUpperAileron", "RightUpperFlap", "RWStation1"], "role": "lifting_surface"},
    {"id": "tail", "source_nodes": ["Tail", "Rudder", "VentralFins"], "role": "tail_surface"}
  ]
}
```

Each region can export:

- `aabb`: cheapest first-round review proxy;
- `obb`: better local fit;
- `convex_hull`: useful for path and outer-shell approximation;
- `simplified_mesh`: final candidate for outer-surface distance and crossing tests.

### 3. Component Vulnerability Layer

Components still come from database `damage_model.components`, but must bind to outer regions:

```json
{
  "component_bindings": [
    {
      "component_name": "apg68_radar_array",
      "expected_outer_region": "nose_radome",
      "current_box": {"center": [6.6, 0.0, 0.0], "size": [1.2, 0.8, 0.6]},
      "review_status": "needs_visual_check"
    }
  ]
}
```

Human review checks:

- whether the component sits inside its expected outer region;
- whether the box protrudes too far outside the outer shape;
- whether the box is too large and causes false damage, or too small and misses close-to-skin proximity;
- whether legacy hitboxes diverge badly from the GLB outer shell.

### 4. Review Point Layer

Each heatmap/probe point should be exported as a visible object:

```json
{
  "review_points": [
    {
      "id": "mlf5_continuous_rod_nose_x4",
      "local_point": [4.0, 0.0, 0.0],
      "warhead_family": "continuous_rod",
      "expected_question": "0.2m close-to-skin should not silently produce zero component candidates"
    }
  ]
}
```

The tool should calculate and display:

- nearest outer region;
- nearest outer-surface distance;
- nearest component;
- nearest component distance;
- whether the point is inside the outer shape;
- whether the point is inside a component box;
- candidate component count;
- actual component trigger count from the current model.

## Tool Design

Suggested entry point:

```bash
python tools/geometry/airframe_geometry_review.py \
  --aircraft examples/config/database/aircraft/units/f16c_block50.json \
  --asset examples/viz/web_viz/static/assets/air/audit/f16_c_falcon_carlos_maciel/gltf/scene.gltf \
  --mapping docs/systems/effects/reviews/f16c_target_geometry_20260614/review_packets/f16c_20260611/f16c_geometry_mapping_candidate_20260611.json \
  --review-points <review_points.json> \
  --out docs/systems/effects/reviews/f16c_target_geometry_20260614/review_packets/f16c_20260611
```

Outputs:

```text
review_packets/f16c_20260611/
  manifest.json
  geometry_summary.md
  scene.html
  top.svg
  side.svg
  front.svg
  review_points.csv
  component_binding_report.csv
```

`scene.html` should open offline and show:

- original GLB;
- simplified outer regions;
- current large hitboxes;
- current component boxes;
- heatmap review points;
- lines from each point to the nearest outer shape and nearest component;
- toggles for outer shape, damage regions, components, review points, and legacy boxes.

## Implementation Order

1. **Asset audit**
   - Parse GLB metadata, hash, node names, envelope dimensions, and triangle count.
   - Read local attribution; if absent, mark the attribution gap.
   - Record the FlightGear zip/GitHub commit, GPL v2 license, authors, key file timestamps, and object-name match evidence.
   - Mark FlightGear as `rejected_for_mainline_license`, retaining it only as a historical lead and local comparison.
   - Select a CC BY 4.0 or broader replacement from the Sketchfab shortlist and record UID, author, hash, and download time.

2. **F-16 read-only review packet**
   - Build rough regions from GLB node names.
   - Overlay current F-16 hitbox/component boxes.
   - Export three-view SVG and static HTML.
   - Do not change runtime.

3. **Manual mapping file**
   - Manually confirm node-to-region mapping.
   - Manually confirm which outer region owns each component.
   - Mark obviously wrong boxes: low height, hard boundary cliff, component outside shape.

4. **Geometry fact diagnostics**
   - For MLF-5 heatmap points, output nearest outer distance, nearest component distance, and candidate component count.
   - Recheck whether `x=4.0` nose continuous-rod proximity is identified as close-to-skin.

5. **Runtime design review**
   - Decide whether first runtime slice consumes outer-proxy distance.
   - Decide whether continuous rod uses sweep/path intersection against outer regions.
   - Decide whether legacy hitboxes remain as fallback.

## Acceptance

- The tool can generate an F-16 review packet without changing runtime.
- The registry uses single-file GLB for runtime visualization; review tooling uses glTF/source packages for source audit and geometry checks.
- The packet shows audit-model outer shape, current large hitboxes, current component boxes, and test points together.
- The manifest clearly marks the FlightGear F-16 as `rejected_for_mainline_license`; any replacement model records Sketchfab UID, author, CC BY 4.0 license, hash, and download time.
- The `x=4.0` nose point shows nearest outer-surface distance and nearest component distance, rather than only "non-direct hit".
- At least one top view and one side view make the legacy hitbox height deficiency obvious.

## Non-Goals

- Do not use high-poly GLB meshes directly for per-frame runtime collision in the first slice.
- Do not hide geometry gaps by simply raising probabilities.
- Do not commit derived geometry from FlightGear community simulation assets as authoritative F-16C Block 50 mainline data.
- Do not silently mix GPL v2 derived geometry into mainline data before the project accepts that license path.
- Do not claim crash, structural breakup, wreck/debris, or real weapon Pk from this tool.
