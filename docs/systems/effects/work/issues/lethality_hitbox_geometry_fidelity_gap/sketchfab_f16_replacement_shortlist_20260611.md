# Sketchfab F-16 Replacement Shortlist

Status: `2026-06-11` replacement shortlist for replacing the FlightGear GPL v2 F-16 asset as the geometry-review candidate; same-day non-Sketchfab source research added.

Chinese companion: not maintained (English-only work surface); this English page is canonical.

## Conclusion

The FlightGear F-16 asset should not enter the mainline geometry-generation path. It remains only a historical provenance lead and local comparison asset, not an input for redistributable outer proxies, hitboxes, or component regions.

Sketchfab search did not find a suitable CC0 F-16. The usable pool is mostly CC BY 4.0. CC BY 4.0 allows copying, modification, and redistribution with attribution, license link, and change notice. This is easier to layer with the repository's Apache-2.0 mainline than GPL v2, but still requires attribution and provenance records.

Non-Sketchfab research found a Blend Swap CC0 F-16/F16 candidate. It has the cleanest license and should become the new first download candidate, but it is an old, small Blender file, so geometry quality must be reviewed after download. CGTrader, TurboSquid, 3DExport, Free3D, CadNav, MakerWorld, and similar sites mostly use royalty-free, non-commercial, standard digital file, paid, or mixed licensing, so they are not suitable open mainline geometry sources.

## Admission Rules

Replacement candidates must satisfy:

- Sketchfab API reports `isDownloadable: true`.
- License is `CC Attribution / CC BY 4.0` or broader.
- No `NC`, `ND`, `SA`, or GPL-like license for mainline geometry input.
- Description does not clearly indicate unclear provenance, game extraction, reposting, AI generation, or "not my model".
- After download, retain original archive hash, GLB/OBJ hash, author, UID, URL, publication time, license, and local conversion steps.
- Derived hitboxes or outer proxies must be marked `visual_reference_derived` or `review_geometry_candidate`, never real F-16C Block 50 engineering geometry.

## Priority Candidates

### Non-Sketchfab Priority Candidates

| Priority | Site | Model | URL | Author | License | Download / size | Assessment |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Blend Swap | `F16 jet fighter` | <https://blendswap.com/blend/16639> | `GreenMotion` | CC0 | Blender 2.7x / Cycles, `181 KB` | Cleanest license candidate. Page reports CC0, downloadable file, and author description as a self-made F16 jet fighter. It is small and over 10 years old, so inspect geometry quality, scale, stores, and material state after download. |
| 2 | Blend Swap | `F16 3D Model` | <https://blendswap.com/blend/4226> | `OKMP` | CC-BY | Blender 2.6x / Blender Internal, `575 KB` | Acceptable backup. Description says it was modeled for After Effects inflight CGI. Use only if the CC0 candidate is geometrically insufficient. |

### Sketchfab Priority Candidates

| Priority | Model | UID / URL | Author | License | Download | Geometry scale | Assessment |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 3 | `F16-C Falcon` | `4bc2ff75dc584af2afd0aa6bd8b79015` / <https://sketchfab.com/3d-models/f16-c-falcon-4bc2ff75dc584af2afd0aa6bd8b79015> | `Carlos.Maciel` | CC BY 4.0 | `isDownloadable: true`; downloaded on `2026-06-11`; the GLB runtime package is under `examples/viz/web_viz/static/assets/air/f16_c_falcon_carlos_maciel/`, and the glTF audit package is under `examples/viz/web_viz/static/assets/air/audit/f16_c_falcon_carlos_maciel/` | `4,504` faces / `2,563` vertices; locally parsed `4,504` triangles / `13,415` position-accessor vertices / raw span `9.5618 x 14.9752 x 4.62987`; post-node-transform world span about `5.833 x 2.824 x 9.136`, registry display scale `1.65` | Cleanest Sketchfab candidate: simple author chain, clear license, low face count, suitable for quick outer-review proxy generation; low detail means public-dimension scaling is still required. glTF audit package SHA256: `47388fb8646e704609712d55e0b53eb014571644b7344c7859276597fc63e248`; GLB runtime package SHA256: `243f164005c49bce0bb25202e449911fed99cbfa94e9bef25321dcbd7476d44f`. |
| 4 | `F-16 Fighter Jet` | `d84491f443384ee488593cc6f0f0839e` / <https://sketchfab.com/3d-models/f-16-fighter-jet-d84491f443384ee488593cc6f0f0839e> | `iedalton` | CC BY 4.0 | `isDownloadable: true` | `4,214` faces / `2,874` vertices | Low-poly backup, described as low-poly F-16 with weapons; useful for cross-checking candidate 3, not ideal as the only review basis. |
| 5 | `F16` | `4eecf423b8454c2ba2a371a7bfe9f157` / <https://sketchfab.com/3d-models/f16-4eecf423b8454c2ba2a371a7bfe9f157> | `manilov.ap` | CC BY 4.0 | `isDownloadable: true` | `29,226` faces / `15,240` vertices | Medium-detail candidate with older publication date; description is mostly generic encyclopedia text, so downloaded package contents still need review. |

## Held Candidates

| Model | UID / URL | Author | License | Geometry scale | Hold reason |
| --- | --- | --- | --- | --- | --- |
| `F-16` | `d898c99707324305bc53b4d224f52602` / <https://sketchfab.com/3d-models/f-16-d898c99707324305bc53b4d224f52602> | `Cxyber` | CC BY 4.0 | `129,861` faces / `77,912` vertices | Good detail, but the description says `Model made by codeata, texture fixes cyber`; author chain needs extra confirmation. |
| `F-16 Fighting Falcon | GameReady` | `0793379abcf742aa881c319155c61220` / <https://sketchfab.com/3d-models/f-16-fighting-falcon-gameready-0793379abcf742aa881c319155c61220> | `Pan_Ar4ik` | CC BY 4.0 | `114,684` faces / `58,685` vertices | High face count and includes weapons/textures; useful for visual reference, but mainline geometry needs author-chain confirmation and pylon/store cleanup. |
| `F 16 High Poly (Subdive Ready)` | `eb37548347bf408eb4d5547ee7b67322` / <https://sketchfab.com/3d-models/f-16-high-poly-subdive-ready-eb37548347bf408eb4d5547ee7b67322> | `Andante` | CC BY 4.0 | `300,480` faces / `150,497` vertices | Too heavy and lacks clear modeling-source notes; visual reference only, not first-round proxy input. |
| `Lowpoly F16 Block 70` | `52c6f5ad114c48adad7a3205a53a56ab` / <https://sketchfab.com/3d-models/lowpoly-f16-block-70-52c6f5ad114c48adad7a3205a53a56ab> | `SIpriv` | CC BY 4.0 | `8,133` faces / `4,218` vertices | Description points to an ArtStation image, so external dependency needs review; Block 70 is not preferred for F-16C Block 50 review. |

## Other-Site Research

| Site | Finding | License / download state | Decision |
| --- | --- | --- | --- |
| Blend Swap | `F16 jet fighter` by `GreenMotion`; page reports CC0, Blender 2.7x / Cycles, `181 KB`, uploaded over 10 years ago. | CC0, broadest license. | New first priority; download and inspect geometry quality and scale. |
| Blend Swap | `F16 3D Model` by `OKMP`; page reports CC-BY, Blender 2.6x, `575 KB`, modeled for After Effects inflight CGI. | CC-BY. | Acceptable backup with attribution. |
| BlenderKit | `Low Poly F-16` by `chroma 3D`; page reports low-poly F-16, `205.9 KiB`, `2,789` polygons. | Fetched page did not expose clear license text, and shows mixed `Full Plan` / `Free` entry points. | Hold pending login/plugin or license-page verification. |
| Meshy AI | F16 tag page claims free CC0 downloads in STL/OBJ/FBX/GLB, but examples are AI-generated and include wording like "inspired by an f-16 or f-22 or f-15". | CC0 claim is friendly, but AI and mixed-aircraft provenance risk is high. | Do not use as F-16 shape constraint; UI placeholder only. |
| Thingiverse | Search results show `F-16 Fighting Falcon by Knerdler` as CC BY; other F-16 print models also exist. | Current environment could not reliably open pages; mostly STL/printing models. | Hold; even under CC BY, not a first-choice outer-shape source. |
| CGTrader | Free F-16/F16 entries exist, including `F-16 Fighting Falcon` and `F16 Fighter Plane`; pages show `Royalty Free License (no AI)`. | Royalty-free marketplace license, not an open content license. | Not a mainline open geometry source; local visual reference only. |
| TurboSquid | Free/low-poly F-16 search pages exist and describe royalty-free / extended usage. | Royalty-free marketplace. | Not a mainline open geometry source; local visual reference only. |
| 3DExport | F16 search page lists royalty-free F16 models, mixed free/paid. | Royalty-free marketplace. | Not a mainline open geometry source. |
| CadNav | `F-16 Fighting Falcon 3D Model` page reports `.3ds/.max`, `6415` polygons, `6567` vertices. | Explicit `License: Non-commercial`. | Reject for mainline use. |
| Free3D | F-16 results are mostly paid models; no open license found. | Paid/royalty-free marketplace. | Not a mainline open geometry source. |
| MakerWorld | F-16 print model pages use a `Standard Digital File License`. | Non-open, print-ecosystem license. | Reject for mainline use. |

## Follow-Up Intake Steps

1. Download the Blend Swap `F16 jet fighter` original package first and record download time, archive hash, file inventory, and license metadata/screenshot.
2. If the Blend Swap CC0 model is geometrically insufficient, download Sketchfab `F16-C Falcon` as the backup; keep GLB for runtime and glTF/source packages for audit and geometry checks, recording Sketchfab UID, URL, author, CC BY 4.0, publication time, download time, and conversion steps.
3. Parse model bounds, triangle count, node names, and axes.
4. Scale against public length, wingspan, and height; do not treat raw model scale as fact.
5. Generate a read-only review packet with three views, outer proxy, legacy hitbox overlay, and MLF-5 test points.
6. After human confirmation of outer regions, decide whether a simplified proxy can enter mainline as `review_geometry_candidate`.

## Excluded

- FlightGear GPL v2 F-16: no longer a mainline geometry-derived input.
- CC BY-SA / GPL / ODbL and similar share-alike licenses: avoid unnecessary relicensing obligations for mainline data.
- CC BY-NC / CC BY-ND: unsuitable for mainline derived geometry.
- Unclear provenance, suspected game extraction, paid-package reposts, forum attachments, or cloud-drive models.
