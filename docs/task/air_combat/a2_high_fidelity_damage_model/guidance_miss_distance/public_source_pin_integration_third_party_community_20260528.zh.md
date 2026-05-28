# Public Source Pin Integration：third-party / community / open-source guidance update

状态：`2026-05-28 integration-note / third-party-community / evidence-route-only / non-authoritative`。

本文档把 guidance / miss-distance / evasion 的第三方、社区和开源候选接入 evidence route。它不修改 runtime，不生成 benchmark，不放行 deterministic fuze，不声明真实 Pk、真实制导性能或真实 AIM-120/R-77/AIM-9X envelope。

## 新增文档入口

| 文档 | 角色 | 最高用途 |
|---|---|---|
| [guidance_miss_distance_public_methods/source_pin_update_third_party_community_20260528.zh.md](../data_collection/guidance_miss_distance_public_methods/source_pin_update_third_party_community_20260528.zh.md) | 登记第三方 BVR/context/range sanity、开源 PN/6DOF/filter scaffold、游戏/商业仿真拒绝项 | `third_party_range_sanity`、`open_source_reproducibility_candidate`、`community_sanity_check_only` |
| [guidance_evasion_benchmark_methods/benchmark_gap_update_third_party_community_20260528.zh.md](../data_collection/guidance_evasion_benchmark_methods/benchmark_gap_update_third_party_community_20260528.zh.md) | 把第三方/社区/开源来源映射到 benchmark gap 和 manifest checklist | generated benchmark planning only |
| [public_source_pin_integration_20260528.zh.md](public_source_pin_integration_20260528.zh.md) | 上一轮官方/公开方法 source pin 接入口 | method / criteria / benchmark design references |
| [public_source_pin_integration_guidance_20260528.zh.md](public_source_pin_integration_guidance_20260528.zh.md) | guidance benchmark update 接入口 | source acquisition posture and runtime gate posture |

## Evidence-route 接入

| evidence-route area | 第三方/社区/开源可接入 | 必须保留的限制 |
|---|---|---|
| BVR range scale | `GMD-TPC-SRC-001/002/003/004/005` may define broad public-context bins and contradiction notes. | Treat as qualitative test-grid scale only; no true NEZ, max envelope, acceptance threshold or Pk. |
| PN / miss-distance implementation | `GMD-OSC-SRC-001` and, after license reconciliation, `GMD-OSC-SRC-005` may cross-check sign convention and generated toy outputs. | Pin commit/tag/license/dependencies and mark all outputs synthetic or open-source scaffold. |
| Terminal evasion / BVR scenario axes | `GMD-OSC-SRC-002/003` may suggest launch-decision, missile-evade, terminal break/jink/crank/notch and reward-vs-physics audit fields. | GPL/JSBSim/config provenance must be explicit; RL reward and game outcome are not physical evidence. |
| Seeker / filter / noise | `GMD-OSC-SRC-004` may support Stone Soup/FilterPy track/filter scaffold with synthetic noise. | No ECCM/notch/clutter/decoy/seeker acquisition truth. |
| Community engineering estimate | `GMD-TPC-SRC-006` may appear in residual and sensitivity-axis notes. | Do not ingest coefficients, curves, tables or AIM-120C-5 envelope values; rights and artifact hash are pending. |
| Game/commercial sim records | `GMD-TPC-REJ-001/002/003` may appear only in rejected-source or sanity-warning sections. | They are excluded from source inputs, benchmark acceptance and runtime descriptors. |

## Source acquisition posture

| status | Meaning | Affected groups |
|---|---|---|
| `source_ref_pinned` | Stable public URL/repo/page exists and is useful for citation. | CSBA, CSIS Missile Threat articles, Designation-Systems, GlobalSecurity, Air & Space Forces Magazine, C4DYNAMICS, BVRGym, JSBSim, Stone Soup, FilterPy, community/game rejection records |
| `repo_ref_pinned` | `git ls-remote` captured current branch/tag commits, but no local artifact or output hash exists. | C4DYNAMICS, BVRGym, JSBSim, small PN repos, FilterPy |
| `rights_partial` | Page-level copyright or repo license identified, but body artifact/license copy not retained here. | CSBA/CSIS/GlobalSecurity/Designation/Air & Space Forces/C4DYNAMICS |
| `pending_rights_or_license` | License unknown or inconsistent; source cannot be used as benchmark input. | AIM-120C-5 community PDF, `iwishiwasaneagle/proportional_navigation`, `gedeschaines/propNav` |
| `rejected_as_truth` | Source may be mentioned only to prevent accidental future use as truth. | CMO-DB viewer, DCS forum/mod ecosystem, War Thunder wiki/forum/community data, anonymous spreadsheets/mirrors |

## Gate posture update

| gate | 当前状态 | 原因 |
|---|---|---|
| `source_ref` | improved for third-party/community search space | Candidate and rejection source refs are now explicitly named with IDs. |
| `rights` | partial / blocked for several sources | Page-level citation is safe, but body reuse, code execution artifacts and community PDFs need license/hash manifests. |
| `scope` | documented as coarse / open-source scaffold / game-balance-risk | Sources are not official calibration data and often lack launch conditions or physical provenance. |
| `artifact_sha256` | missing | No source PDFs/HTML snapshots/repos or generated outputs are retained as canonical artifacts in this note. |
| `validation_manifest` | missing | No acceptance criteria, reviewer notes or output hashes are frozen. |
| `runtime authority` | closed | No external calibration dataset or validated physics surrogate exists; all entries remain `authority=none`. |

## Integration rules

- Future benchmark manifests must cite `GMD-TPC-*` or `GMD-OSC-*` source IDs when using this line, and must carry their residual IDs forward.
- BVR range bins derived from third-party public sources must be named as coarse scenario scales, not as weapon performance rows.
- Open-source scaffolds may be used only after commit/tag, license, dependency lock, scenario manifest, seed and output hash are recorded.
- Game/commercial-sim records must stay in `rejected_sources` or `community_sanity_check_notes`; they cannot appear in `inputs`, `calibration_sources` or `descriptor_rows`.
- Any guidance output feeding the fuze/effects bridge must still pass the separate source, warhead, fuze, target vulnerability and residual gates; this integration note changes none of those gates.

## Most useful candidates

| candidate | why useful | boundary |
|---|---|---|
| `GMD-OSC-SRC-001` C4DYNAMICS | Best open-source PN/6DOF/seeker/filter scaffold found in this line; has docs, GitHub route and tag/commit candidates. | Reproducibility scaffold only; no AAM truth. |
| `GMD-OSC-SRC-004` Stone Soup / FilterPy | Good filter/noise/Singer/Kalman implementation cross-check for seeker-filter toy benchmark. | Synthetic tracking proxy only. |
| `GMD-OSC-SRC-002/003` BVRGym + JSBSim | Useful for BVR scenario axes and evasion-environment structure. | Reward/game-environment behavior is not physical validation. |
| `GMD-TPC-SRC-001/002` CSBA / CSIS | Good public BVR context and AMRAAM range order-of-magnitude sanity. | Policy/reporting context; no envelope or Pk. |
| `GMD-TPC-SRC-003/004/005` Designation-Systems / GlobalSecurity / Air & Space Forces | Useful contradiction register for public AAM ranges and variant ambiguity. | Tier C/B sanity only. |

## Rejection summary

| rejected class | record ids | reason |
|---|---|---|
| game/commercial sim data as truth | `GMD-TPC-REJ-001/002/003` | Gameplay balance, patch churn, commercial DB design and no public provenance. |
| rights-unclear mirrors and anonymous claims | `GMD-TPC-REJ-004` | Fails source_ref/provenance/rights/scope gates. |
| unknown-license code as input | `GMD-OSC-SRC-006` and any unreconciled small PN repo | Cannot be copied, vendored or used to retain generated artifacts before license review. |
| community engineering coefficients as calibration | `GMD-TPC-SRC-006` until rights/provenance/validation close | Even after rights close, it remains sensitivity/residual material without independent validation. |

## Still-open gaps

| gap | next closeout |
|---|---|
| Third-party public range launch conditions | Add altitude, Mach, aspect, closure, target maneuver and loft axes or keep ranges qualitative. |
| Open-source artifact manifests | Record exact license files, source tarball/repo hashes, dependency locks, commands, seeds and output sha256. |
| Benchmark independence | Split unit consistency, cross-implementation agreement and external validation; no authority from self-generated outputs alone. |
| Community/game contamination | Add review grep around descriptor and benchmark manifests for `DCS`, `War Thunder`, `CMO-DB`, `cmano-db`, `game_balance_risk`, `Pk`, `lethal radius`, `fuse radius`. |
| AIM-120C-5 community PDF | Decide whether to close rights/hash for residual-only use or keep as rejected/pending-rights search lead. |
