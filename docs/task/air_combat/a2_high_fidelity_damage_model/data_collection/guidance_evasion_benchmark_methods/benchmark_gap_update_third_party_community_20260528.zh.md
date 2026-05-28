# Benchmark Gap Update：第三方、社区与开源 guidance / evasion 候选

状态：`2026-05-28 benchmark-gap / third-party-community / non-authoritative`。

本文档补充 [source_ledger.zh.md](source_ledger.zh.md)、[benchmark_gap_update_20260528.zh.md](benchmark_gap_update_20260528.zh.md) 与 guidance/miss-distance 第三方候选 pin：

- [guidance_miss_distance_public_methods/source_pin_update_third_party_community_20260528.zh.md](../guidance_miss_distance_public_methods/source_pin_update_third_party_community_20260528.zh.md)

它只定义第三方、社区和开源资料如何进入 benchmark design / gap register，不生成 artifact，不运行验证，不授予 Pk、真实制导性能、真实 AAM envelope、确定性引信或 runtime authority。

## Family gap update

| family | 第三方/社区/开源候选 | 可作为 | 仍缺内容 | 当前最高结论 | 禁止误用 |
|---|---|---|---|---|---|
| BVR engagement scale | `GMD-TPC-SRC-001/002` | `BVR_context_candidate`；historical/strategy-level range relevance and BVR scenario axes | CSBA/CSIS artifact hash, data provenance audit, scenario condition axes | 可以把 BVR benchmark 的 range bins 设为 broad public context，而非 single truth | 不得声明 modern BVR Pk、战术有效性或具体导弹 NEZ |
| Public AAM range sanity | `GMD-TPC-SRC-002/003/004/005` | `third_party_range_sanity`; contradictory estimate register | altitude/Mach/aspect/closure/loft, source date, variant mapping, official cross-check | 可发现数量级异常和 variant/source 冲突 | 不得把 AIM-120/R-77/AIM-9X range 写成 runtime envelope row |
| PN / 6DOF implementation scaffold | `GMD-OSC-SRC-001`; optional `GMD-OSC-SRC-005` after license reconciliation | `open_source_reproducibility_candidate`; implementation cross-check | commit/tag, license confirmation, dependency lock, parameter manifest, output hash | 可用于 self-generated toy benchmark 的 secondary implementation sanity | 不得当作 missile guidance validation 或真实 missile dynamics |
| BVR / terminal evasion scenario scaffold | `GMD-OSC-SRC-002`, `GMD-OSC-SRC-003`; old-scope `GEB-SRC-008/009/010/012/014/015` as primary method references | `open_source_config_candidate`; scenario axes and reward/terminal event audit | no release tag, GPL dependency review, JSBSim aircraft/missile config provenance, reward vs physics separation | 可设计 BVR/RL/evasion scenario manifest and failure-mode taxonomy | 不得使用 RL reward 或 game outcome as Pk / tactic truth |
| Seeker / filter / noise scaffold | `GMD-OSC-SRC-004` plus `GEB-SRC-004/007/016/017/021` | `reproducibility_candidate`; track/filter/noise benchmark scaffold | version pin, measurement model, noise distribution, covariance/proxy outputs, dropout/memory manifest | 可形成 seeker-filter toy benchmark with explicit synthetic noise | 不得声明 seeker ECCM/notch/clutter/decoy or acquisition truth |
| Community engineering estimate | `GMD-TPC-SRC-006` | `third_party_engineering_estimate_pending_rights`; residual discovery and sensitivity axes | rights/license, artifact hash, input provenance, CFD assumptions, DCS scope caveat | 可记录 "why public AIM-120C estimates are disputed" and test sensitivity ranges as synthetic | 不得 ingest coefficients, true thrust/drag, AIM-120C-5 envelope or Pk |
| Game / commercial simulation data | `GMD-TPC-REJ-001/002/003` | `community_sanity_check_only`; reject-list and balance-risk warning | none for authority; only retain source_ref and rejection reason | 可提醒 benchmark manifests avoid gameplay parameters and single numeric truth | 不得 enter dataset, criteria, descriptor, calibration or runtime rows |

## Benchmark package impact

| package | 新增候选 source_ids | 可新增检查 | 必须补齐后才能生成 artifact | 明确禁止 |
|---|---|---|---|---|
| `pn_classical_miss_distance_v1` | `GMD-OSC-SRC-001`, optional `GMD-OSC-SRC-005`; primary still `GEB-SRC-001/002/008/011/019` | compare A2 PN output sign convention and closest-approach interpolation against a pinned secondary implementation | exact commit/tag, license, dependency lock, scenario manifest, dt/integrator, output sha256 | adopting open-source default missile parameters as truth |
| `apn_target_accel_v1` | `GMD-OSC-SRC-004` for Kalman/Singer implementation scaffold; primary still `GEB-SRC-003/007/020/001` | filter state/covariance/proxy logging and target-acceleration estimator stress | noise model, target acceleration process, estimator state, reproducible seed/hash | naming biased PN as APN without estimator state |
| `terminal_evasion_sweep_v1` | `GMD-OSC-SRC-002/003`; context from `GMD-TPC-SRC-001` | BVR launch-distance bins, terminal break/jink/crank/notch scenario axes, reward/physics separation checklist | JSBSim/BVRGym commit, config provenance, old/simplified flag, target/missile energy state fields | declaring modern evasion tactic effectiveness or direct Pk multiplier |
| `seeker_filter_noise_v1` | `GMD-OSC-SRC-004` | Stone Soup/FilterPy pinned filter scaffold; bearings/range/elevation noise and dropout sanity | version pin, dependency lock, synthetic noise manifest, track output metrics, sha256 | ECM/ECCM/notch/clutter/decoy truth |
| `dynamic_flyout_vs_envelope_v1` | `GMD-TPC-SRC-002/003/004/005`, `GMD-TPC-SRC-006` only as public contradiction notes; primary still `GEB-SRC-011/005/018` | compare dynamic toy fly-out reason-for-miss against broad public range bins and show why single max range is insufficient | launch condition axes and public-source contradiction register | writing public third-party max range as static no-escape or guaranteed max envelope |
| `sixdof_module_boundary_v1` | `GMD-OSC-SRC-001/003`; primary still `GEB-SRC-005/006/013/018` | module-boundary checklist: seeker, filter, guidance, autopilot, airframe, actuator, propulsion, environment | code pin, module manifest, state vector, integrator, output metrics | weapon-specific aero/propulsion database claims |
| `a2_effects_bridge` | none admitted beyond context | add provenance warning that miss-distance inputs are generated/non-authoritative when derived from open-source scaffold | source_refs, generated artifact manifest, fuze/warhead evidence rows still separate | deterministic fuze trigger, lethal radius, final Pk shortcut |

## Public range admission rules

| rule_id | rule | applies to | reason |
|---|---|---|---|
| `TPC-RANGE-RULE-001` | Store public third-party AAM range as qualitative bin or contradiction note unless launch condition axes are explicit. | `GMD-TPC-SRC-002/003/004/005/006` | Public range claims rarely include altitude, speed, aspect, closure, loft or target maneuver. |
| `TPC-RANGE-RULE-002` | Do not merge "seeker range", "aerodynamic range", "maximum kinematic range", "effective range", "NEZ" or game "air max range" into one field. | `GMD-TPC-REJ-001`, `GMD-TPC-SRC-002/004/006` | Community/game DBs often expose distinct fields that look comparable but are not physically equivalent. |
| `TPC-RANGE-RULE-003` | Require at least one Tier A/B method source and one third-party sanity source before using a range bin in a benchmark scenario title. | all BVR range bins | Prevents a community number from becoming the benchmark's implied truth. |
| `TPC-RANGE-RULE-004` | Public BVR range context can set test-grid scale, but not acceptance thresholds. | `terminal_evasion_sweep_v1`, `dynamic_flyout_vs_envelope_v1` | Acceptance thresholds must come from generated toy benchmark manifest or validated data, not open-ended public estimates. |
| `TPC-RANGE-RULE-005` | Any source that is game/commercial-sim derived must be labeled `game_balance_risk=true` and excluded from numeric parameter ingestion. | `GMD-TPC-REJ-001/002/003` | Game data may be tuned for playability, scenario balance or patch policy. |

## Open-source scaffold admission checklist

| checklist_id | required field | Why it matters |
|---|---|---|
| `TPC-OSC-REQ-001 source_ref` | repo URL plus exact commit/tag and release route | GitHub main branches drift. |
| `TPC-OSC-REQ-002 rights` | license file, package metadata and any asset/config license | Some repos have license conflicts or bundled configs. |
| `TPC-OSC-REQ-003 dependency_lock` | Python/package/JSBSim/FlightGear versions, OS assumptions | Numeric outputs can change across versions. |
| `TPC-OSC-REQ-004 scenario_manifest` | initial geometry, target maneuver, missile model, guidance law, sensor/noise, dt/integrator | The scaffold is not useful without all physics assumptions visible. |
| `TPC-OSC-REQ-005 generated_output_hash` | metrics, output path, sha256, random seed | Needed to cite artifact rather than local transient output. |
| `TPC-OSC-REQ-006 no_truth_labels` | explicit `synthetic`, `toy`, `old_scope`, or `open_source_scaffold` label | Prevents generated data from being mistaken for external calibration. |

## Gap register update

| `gap_id` | 影响范围 | 当前状态 | 关闭条件 |
|---|---|---|---|
| `GEB-TPC-GAP-001 third-party-range-conditions` | BVR / public AAM range sanity | Range claims collected but launch-condition axes absent. | Each range bin has altitude/Mach/aspect/closure/loft/target-maneuver caveat or stays qualitative. |
| `GEB-TPC-GAP-002 open-source-license-pin` | C4DYNAMICS/BVRGym/JSBSim/FilterPy/Stone Soup/small PN repos | Git refs recorded; some licenses from page metadata only; one license conflict and one unknown-license repo noted. | Fetch or record official license text, reconcile conflicts, exclude unknown-license repos. |
| `GEB-TPC-GAP-003 open-source-parameter-provenance` | PN/6DOF/BVRGym/JSBSim configs | Default parameters may be tutorial, public approximation or gameplay scope. | Manifest lists every non-synthetic parameter source and marks unverified defaults as synthetic. |
| `GEB-TPC-GAP-004 game-balance-contamination` | DCS/War Thunder/CMO community data | Game DBs and forum/mod data look precise but fail authority gates. | Keep as rejected/sanity-only and add automated review grep before descriptor generation. |
| `GEB-TPC-GAP-005 validation-independence` | All scaffold-derived benchmarks | Cross-implementation agreement does not prove real-world validity. | Validation report distinguishes unit consistency, method cross-check and external calibration; no authority without independent data. |
| `GEB-TPC-GAP-006 AIM120C5-community-rights` | `GMD-TPC-SRC-006` | Public routes known, but license/canonical artifact/hash not closed. | Rights and artifact manifest complete; even then values remain sensitivity/scaffold unless independently validated. |

## Rejected source classes for benchmark manifests

| rejection class | Examples | Manifest handling |
|---|---|---|
| `game_database_parameter_truth` | CMO-DB viewer, DCS data files/mods, War Thunder wiki tables | May appear only in `rejected_sources` or `community_sanity_check_notes`, never in `inputs`. |
| `forum_single_point_claim` | forum posts with one max range, one Pk, one fuze/lethal radius | Reject unless traceable to official/publisher/DOI/source artifact. |
| `mirror_pdf_body_use` | Scribd, Studylib, PDFCoffee, random web mirrors, unofficial copies of books/papers/manuals | Use DOI/publisher/official handle only; body content requires legal source artifact. |
| `rights_unknown_code` | GitHub repos without license or with conflicting package metadata | Do not vendor, execute for retained artifact, or cite generated outputs until rights clear. |
| `controlled_tool_output` | JMEM/JWS/J-ACE/AJEM/COVART/FASTGEN/Endgame Manager and derivatives | Rejected; do not summarize or derive benchmark data. |

## Matrix revision note

- The third-party range pool can help choose broad scenario scales, e.g. WVR/short-range, medium BVR, long BVR, but every bin must remain a non-authoritative test-grid label.
- Open-source scaffold can reduce implementation mistakes in PN/filter/noise benchmarks, but source kind remains `reproducibility_candidate` or `sanity_check_only` until generated artifacts have manifests and hashes.
- Community engineering estimates may inform residual questions and sensitivity sweeps; their coefficients and envelope curves are not data inputs.
- Game/commercial-sim records are useful mainly as "sharp-looking numbers to distrust"; they are intentionally captured so later work does not accidentally promote them.
