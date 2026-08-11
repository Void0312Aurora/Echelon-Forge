# Fuze Authority Gap Update - Third-Party and Community Sources

状态：`2026-05-28 / authority gap update / third-party-community / not_admitted / non-authoritative`
关联来源更新：[AIM-120C-class third-party/community source pin](../data_collection/aim120c_warhead_fuze/source_pin_update_third_party_community_20260528.zh.md)
写入边界：本文只说明第三方/社区候选对 P4 fuze authority gap 的影响；不授予 runtime authority，不创建 fuze manifest，不允许移除现有非权威 fallback。

## 本轮新增材料对 gate 的最高用途

| source_id / group | source role | 最高用途 | 对 fuze authority 的影响 | 仍阻塞的 gate |
|---|---|---|---|---|
| `AIM120-TPC-001` | Designation-Systems AMRAAM page | `third_party_candidate` for WDU/FZU/TDD search terms and warhead mass-claim cluster | 可帮助列出需要验证的 candidate fields；不能证明任何 field。 | No official/public engineering provenance per field; no trigger threshold, delay, reliability, safe-arm or replay evidence. |
| `AIM120-TPC-002` | Air Force Armament Museum Foundation artifact page | `third_party_candidate` for C-5 40 lb / WDU-41 and public TDD/QTDD claim cluster | 可增加 C-class warhead/fuze residual 的可审计性；不能闭合 TDD/QTDD admission。 | No source chain, variant scope uncertainty, no threshold/false-trigger criteria or validation artifact. |
| `AIM120-TPC-003/004/005/006/007` | magazine/enthusiast/defense-media/missile encyclopedia pages | `community_sanity_check` and `non-authoritative_estimate` | 可用于 sanity check 18-23 kg / 40-50 lb 量级、blast-fragmentation family and active-radar/proximity terminology。 | No source can support C-variant fuze trigger model, lethal footprint, warhead fragment cloud or deterministic replay. |
| `AIM120-TPC-008` | FAS mirror of generic fuzing/warhead teaching material | `method_reference` / terminology sanity only | 可帮助定义 generic `TDD`, proximity mode, fuze safety/arming and fragmentation vocabulary。 | Not AIM-120-specific; mirror rights/provenance are weaker than official source; no runtime evidence. |
| `AIM120-TPC-REJ-001..005` | DCS/War Thunder/forum/game/inaccessible leads | rejected for data use | No positive gate contribution; documents what must not seed fuze radius, damage or Pk behavior。 | Rights/provenance/game-balance/leak risk; values rejected before source gate. |

## P4 gate impact

| gate | 第三方/社区材料能做什么 | 当前不能做什么 |
|---|---|---|
| source gate | Record traceable non-official claims, source URLs, access status, rights caveats, reasonableness and cross-validation residuals. | Cannot replace official/source-cleared evidence for trigger thresholds, delay, reliability, safety/arming, target signature or burst-point logic. |
| evidence gate | Provide search terms such as WDU-33/B, WDU-41/B, FZU-49/B, TDD, QTDD, proximity/impact fuze and blast-fragmentation. | Cannot prove component identity, fuze implementation, false/missed trigger criteria, or variant-specific field values. |
| validation gate | Help define what future surrogate or replay tests must explicitly reject or bracket. | Cannot supply scope-matched validation artifacts, metrics, reviewer record, or residual closeout. |
| replay gate | No direct replay input. Community/game configs can be used only as anti-import checks. | Cannot seed event hashes, admission matrix, trigger-radius profile, detonation timing or reliability behavior. |
| dependency gate | Adds weak candidate clusters for AIM-120C-class warhead/fuze residuals. | Does not close target signature, contact surface, timestep, warhead/fuze profile, or backend dependency bundles. |

## Fuze type gap after third-party/community review

| fuze type | 本轮可记录 | 仍缺的 admission evidence |
|---|---|---|
| `radar_proximity` | TDD/proximity/fuze terms are cross-mentioned by official Federal Register terminology, third-party AMRAAM pages, museum-foundation page and generic fuzing material. | Target RCS/aspect/signal evidence; receiver/threshold evidence; burst-point logic; delay; reliability; false/missed trigger criteria; scope-matched validation and executed replay matrix. |
| `contact` / `impact` | Some third-party pages mention impact fuze as part of public AMRAAM descriptions. | Contact surface accuracy, impact normal/angle/velocity evidence, arming/dud policy, material scope, timestep tunneling validation and replay results. |
| `timed` | No useful timed-fuze evidence. | Setting source, clock/drift evidence, safety/arming linkage, no-target policy, validation and replay evidence. |
| `laser_proximity` | No AIM-120-relevant laser evidence. | Reflectance/projected signature evidence, threshold, environmental scope, validation and replay evidence. |

## Rejected influence controls

| rejected source class | enforced boundary |
|---|---|
| DCS Lua datamine / simulator config | Do not import any warhead, explosive, proximity radius, fuse radius, damage, fragment, reliability or Pk-like field. Public GitHub reachability does not clear DCS data rights or engineering provenance. |
| War Thunder wiki/forum/game tables | Treat as game/community fields only. Do not copy numeric game values into source ledger, benchmark config or runtime profile. |
| Forum posts with attachments, screenshots, or possible leaked/controlled references | Stop at rejection record. Do not summarize sensitive details, do not follow them into parameter extraction, and do not use them as cross-validation. |
| Personal/tabletop game stat pages | Reject numeric rows and scenario/game mechanics. They may only be logged as examples of non-engineering sources that must not drive damage behavior. |
| Inaccessible third-party leads | No facts admitted until stable public artifact, rights, provenance and scope are acquired. |

## Authority gap statement

The third-party/community review improves auditability but does not close P4. The current status remains `deterministic_fuze_authority = not_admitted / deferred`.

Still missing before any admission:

- admitted `a2.fuze_authority.v1` manifest with scope and dependency refs;
- public/source-cleared trigger threshold, burst-point logic, delay, reliability and safety/arming evidence;
- target signature/contact-surface dependency bundle;
- validated surrogate or external dataset with artifact checksum, metrics, acceptance criteria and residual closeout;
- executed replay/admission matrix with event hashes and failed-case review;
- explicit rejection filters preventing DCS/War Thunder/forum/game values from entering runtime or benchmark calibration.

No third-party or community source in this update supports AIM-120C deterministic fuze behavior, trigger radius, lethal radius, component failure probability, Pk, or calibrated runtime damage behavior.
