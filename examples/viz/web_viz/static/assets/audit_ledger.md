# Visualization Asset Audit Ledger

Status: `2026-08-13`. This ledger is the retirement record for third-party
visualization source packages that were removed from the working tree. The
packages were intake evidence only; nothing in `examples/viz` loads them at
runtime, and every byte remains reachable in Git history.

Retirement commit pin: `5f95ee9d6544a7ede91be0474c76cf5ea045a708`
("Add audit-backed visualization assets", 2026-06-11). Every path below exists
at that commit, so any retired file can be recovered with:

```bash
git show 5f95ee9d6544a7ede91be0474c76cf5ea045a708:<path> > <local-copy>
```

Attribution obligations are unchanged by retirement. The per-directory
`ATTRIBUTION.md` files and `THIRD_PARTY_NOTICES.md` remain the credit records
for the runtime GLB assets that are still shipped.

## Still Live (Not Retired)

`examples/viz/web_viz/static/assets/air/audit/f16_c_falcon_carlos_maciel/gltf/`
is **not** evidence-only and must not be deleted. It is a parse input for
`tools/geometry/airframe_review` (`constants.DEFAULT_AUDIT_SCENE`) and is read
by `tests/tools/test_airframe_geometry_manifest.py`, which asserts triangle and
vertex counts read live from `scene.gltf` plus `scene.bin`. Only the redundant
`.zip` container of that same package was retired.

## Retired Packages

### F16-C Falcon — source archive only

- Source: <https://sketchfab.com/3d-models/f16-c-falcon-4bc2ff75dc584af2afd0aa6bd8b79015>
- Author: `Carlos.Maciel` (<https://sketchfab.com/Carlos.Maciel>)
- License: CC-BY-4.0, <http://creativecommons.org/licenses/by/4.0/>
- Sketchfab UID: `4bc2ff75dc584af2afd0aa6bd8b79015`
- Retired: `air/audit/f16_c_falcon_carlos_maciel/4bc2ff75dc584af2afd0aa6bd8b79015_gltf.zip`
  — `4,282,583` bytes, SHA-256 `47388fb8646e704609712d55e0b53eb014571644b7344c7859276597fc63e248`
- Reason: the archive only re-packages `gltf/license.txt`, `gltf/scene.bin`,
  `gltf/scene.gltf`, and the three `gltf/textures/*` files, all of which stay
  on disk because the geometry review tooling parses them.

### Shahed 136

- Source: <https://sketchfab.com/3d-models/shahed-136-bc8754128c9d48c48baadeff1db8f0c7>
- Author: `faintastic18` (<https://sketchfab.com/faintastic>)
- License: CC Attribution (CC BY), <http://creativecommons.org/licenses/by/4.0/>
- Sketchfab UID: `bc8754128c9d48c48baadeff1db8f0c7`
- Downloaded: `2026-06-11 Asia/Shanghai`
- Runtime asset kept: `uav/shahed_136_faintastic18.glb`
- Retired `uav/audit/shahed_136_faintastic18/`, `3,585,438` bytes total:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `bc8754128c9d48c48baadeff1db8f0c7_gltf.zip` | 1,075,939 | `6922d2712cf6468788abaa373cd86cbe97a623610c77208571a175f9ecaabf32` |
| `intake_metadata.json` | 1,268 | `3602334375b7938a6c52ab702f92b8f520a27a812c570b9a5d785705f5950d4f` |
| `gltf/license.txt` | 678 | `79630b53acb79ba0549fef9c8d54224518a2c4dfc6996ede37d4062893d1e323` |
| `gltf/scene.bin` | 2,474,904 | `9c8a8d923d19657b9d52a411675f81da67c4f4bc75e84cfad3ebbf986f22e6fe` |
| `gltf/scene.gltf` | 32,649 | `55a9157ec57b71fc82400230700e6080e8767c69f610b7e8ae1e9ec45577d249` |

### MQ-9 Reaper Drone — Game Ready Military Asset

- Source: <https://sketchfab.com/3d-models/mq-9-reaper-drone-game-ready-military-asset-a02057e7401a4f4ea130cb75cc73d8cb>
- Author: `The Aesthetic Modeler` (<https://sketchfab.com/racingrevved>)
- License: CC Attribution (CC BY), <http://creativecommons.org/licenses/by/4.0/>
- Sketchfab UID: `a02057e7401a4f4ea130cb75cc73d8cb`
- Downloaded: `2026-06-11 Asia/Shanghai`
- Runtime asset kept: `uav/mq9_reaper_game_ready_aesthetic_modeler.glb`
- Retired `uav/audit/mq9_reaper_game_ready_aesthetic_modeler/`, `992,392` bytes total:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `a02057e7401a4f4ea130cb75cc73d8cb_gltf.zip` | 312,432 | `bbb08b4b1c78812cd26f082d748f3e425303af9074ed3f8edc2006cb1c9cda32` |
| `intake_metadata.json` | 1,379 | `43782f9f93d442e6483feae608d10727145970854db7bf61435e99081f80481c` |
| `gltf/license.txt` | 844 | `a327c681bd4dbb5ea94cfef36702a4cd392fe8019a50dec755a30d061a065d60` |
| `gltf/scene.bin` | 631,444 | `a54b8d5e4093fecb737e088ef089bc6c7e3139dc8845c26167ad7fd750f5ece9` |
| `gltf/scene.gltf` | 46,293 | `624456025f202ec89f26d4dd5d2a4606cd650fe68bba7bde82df5ba52641d365` |

### AIM-120 AMRAAM missile

- Source: <https://sketchfab.com/3d-models/aim-120-amraam-missile-e52d37a110004e1480465bc6b0943ebc>
- Author: `RickSlash` (<https://sketchfab.com/rickslash>)
- License: CC-BY-4.0, <http://creativecommons.org/licenses/by/4.0/>
- Sketchfab UID: `e52d37a110004e1480465bc6b0943ebc`
- Downloaded: `2026-06-11 Asia/Shanghai`
- Runtime asset kept: `missiles/aim120_amraam_rickslash.glb`
- Retired `missiles/audit/aim120_amraam_rickslash/`, `603,206` bytes total:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `e52d37a110004e1480465bc6b0943ebc_gltf.zip` | 234,049 | `9eb2584e5b0bf8d280b79a8ff12b24e980cc6ca15e992b093413636984a00518` |
| `intake_metadata.json` | 1,578 | `20c6b221ccac2276314ad668ca1542d8ae0657e7cc3f4621ae8b70269e7bbd44` |
| `gltf/license.txt` | 722 | `22996be527e5faa044f4177aa7db102b99fd3d722e7f0e447d8af0cbd64e7d63` |
| `gltf/scene.bin` | 71,088 | `83487659a32636683ec864cb832a581f420be80a4ba45644d313a9df4a99408a` |
| `gltf/scene.gltf` | 38,109 | `57e0c39593cd48930fee8b9db0334f6043656f6f3005037778a5137f9bd85f10` |
| `gltf/textures/lambert1_baseColor.jpeg` | 165,227 | `cea97e039dd59dd52c73478b234fe287d2696f25f67bf3d7715fac764692de89` |
| `gltf/textures/lambert1_metallicRoughness.png` | 38,847 | `727d77a50043dc962958ff7f9d1deb1a1439f3be872920926ec43793dbb452b7` |
| `gltf/textures/lambert1_normal.png` | 53,586 | `187874443648c48abe3d60871c4373a9fe0e333fdf5800a1bfa64a853dad5982` |

### Game Ready Low Poly R-77

- Source: <https://sketchfab.com/3d-models/game-ready-low-poly-r-77-0da27c5b53f24542843a4a423c59b96a>
- Author: `Mustafa.Garip` (<https://sketchfab.com/MustafaGarip>)
- License: CC-BY-4.0, <http://creativecommons.org/licenses/by/4.0/>
- Sketchfab UID: `0da27c5b53f24542843a4a423c59b96a`
- Downloaded: `2026-06-11 Asia/Shanghai`
- Runtime asset kept: `missiles/r77_mustafa_garip.glb`
- Retired `missiles/audit/r77_mustafa_garip/`, `916,348` bytes total:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `0da27c5b53f24542843a4a423c59b96a_gltf.zip` | 363,982 | `477bb65da8dc90d29d7f918a83a381813a21bfb1d02851f6b53381fffaf7f1c0` |
| `intake_metadata.json` | 1,592 | `492b19cc858975fa243d7d9ee4cb2389749359cdae3d90bf829b81f3bdc90cb7` |
| `gltf/license.txt` | 746 | `ab6d3347e21798338d83cdf6d907dd64c7e3dc590b8e3714610f66f2c8907186` |
| `gltf/scene.bin` | 268,200 | `3d8a3bc67d2acd2df272e52b00daea8685dae484729c229789ef518dda89f42b` |
| `gltf/scene.gltf` | 5,974 | `131adbd9bbe854e6ea160019310b4e5fde022a1d937de767e64964b26e4064b1` |
| `gltf/textures/R-77_material_baseColor.png` | 102,682 | `970a0079d07081bec988aa9c0fbdd98b07f7da533060889436c748f01204b0a9` |
| `gltf/textures/R-77_material_metallicRoughness.png` | 155,250 | `dcf1945db55558b820b7f4ab2fcccfffbfad3c9937b92733654170c2c9a96e82` |
| `gltf/textures/R-77_material_normal.png` | 17,922 | `668027b46d8a93a22d75e54ac1c4370b53df43575f7e2eb894f98bef9eb9a9af` |

### Archived F-16 FlightGear GPLv2 candidate

- Provenance lead: FlightGear `NikolaiVChr/f16`, <https://github.com/NikolaiVChr/f16>
- Package: <https://mirrors.ibiblio.org/flightgear/ftp/Aircraft-2018/f16.zip>
- Pinned commit observed in A2 source records: `190a699c77bd3c2c7da1e3bb4bffc7a6013bc8f5`
- License: GPL v2
- Retired `archive/f16_flightgear_gplv2_candidate_20260611/`, `287,827` bytes total:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `f16.glb` | 286,528 | `7c432edcaec14bc52a262d2ef311b19c525452e2614400c3c10f8e93da1b7ee0` |
| `README.md` | 1,299 | `8eb5be9cb9db527d4ae659500ca5a022353cd3166db9c65ef37f1774de334a41` |

This candidate was rejected for mainline geometry derivation before retirement:
object-name comparison matched all 117 local node/mesh names against FlightGear
`f16/Models/f16.ac`, making GPLv2 the likely upstream license. It must not be
treated as repository-level Apache-2.0 content, and no mainline hitbox, outer
proxy, or component-region fact may be derived from it. Retiring it from the
working tree removes the risk of accidental reuse; the provenance record above
preserves the review conclusion.

## Totals

| Group | Files | Bytes | MB |
| --- | ---: | ---: | ---: |
| F16-C Falcon source archive | 1 | 4,282,583 | 4.08 |
| Shahed 136 | 5 | 3,585,438 | 3.42 |
| MQ-9 Reaper | 5 | 992,392 | 0.95 |
| AIM-120 AMRAAM | 8 | 603,206 | 0.58 |
| R-77 | 8 | 916,348 | 0.87 |
| F-16 FlightGear candidate | 2 | 287,827 | 0.27 |
| **Total retired** | **29** | **10,667,794** | **10.17** |
