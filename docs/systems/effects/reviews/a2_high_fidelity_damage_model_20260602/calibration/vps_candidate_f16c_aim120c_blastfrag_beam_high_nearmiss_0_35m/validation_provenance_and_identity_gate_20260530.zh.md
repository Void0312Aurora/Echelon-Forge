# Validation Provenance And Identity Gate

状态：`blocked / candidate / non-authoritative / shared_package_surface_only`。

本文档记录当前 A2 窄域候选包的第一版 shared provenance / surrogate identity gate。它来自
[damage_model.py](../../../../../../../tools/maintenance/damage_model.py) `release-governance package-provenance-identity`，
目标不是放行 authority，而是把 `RES-001 source provenance` 与 `RES-002 surrogate identity`
的共享阻塞面机器化固定下来，供 Stage B 与 Stage C 共用。

本文档不创建 runtime descriptor，不授予 authority，也不把 author-side retained chain 误写成 release-grade identity。

## 1. 元数据

| 字段 | 值 |
|---|---|
| `package_id` | `a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_beam_high_near_miss_0_35m_v0` |
| `schema_version` | `a2.package_provenance_identity_gate.v1` |
| `review_target` | `shared_provenance_and_surrogate_identity_surface` |
| `readiness_level` | `author_side_pin_and_identity_surface_present_but_not_release_grade` |
| `gate_status` | `blocked_non_authoritative_package_provenance_identity_candidate` |

## 2. 当前已满足条件

| `condition_id` | residual | 含义 |
|---|---|---|
| `READY-PI-001` | `RES-001`, `RES-002` | provenance / identity 文档面当前没有 placeholder hits。 |
| `READY-PI-002` | `RES-001` | artifact pin manifest 已冻结到 author-side candidate review surface。 |
| `READY-PI-003` | `RES-002` | surrogate identity manifest 已固定 model/version/repo anchor surface。 |
| `READY-PI-004` | `RES-002` | canonical retained Stage B author-side artifacts 已存在。 |
| `READY-PI-005` | `RES-002` | canonical retained Stage C author-side artifacts 已存在。 |

## 3. 当前阻塞项

| `blocker_id` | residual | 当前阻塞原因 |
|---|---|---|
| `BLOCK-PI-001` | `RES-001` | DENIX official public artifacts 虽已 externally verified 并固定 sha256，但 package provenance 仍未达到 release-grade closeout：canonical retention、allowed-output policy 和 benchmark-consumption 仍 open。 |
| `BLOCK-PI-002` | `RES-002` | surrogate identity 仍是 author-side；repo 还不处于 clean release-grade identity state。 |
| `BLOCK-PI-003` | `RES-002` | author-side retained artifact packs 已存在，但它们只证明候选证据被保留，不关闭 release-grade surrogate identity。 |
| `BLOCK-PI-004` | `RES-013/014-boundary` | 本 shared gate 不授予 stock runtime authority、Pk authority 或 deterministic fuze authority。 |

## 4. RES-001 / RES-002 条件追踪

| residual | satisfied condition ids | blocking condition ids | gate result |
|---|---|---|---|
| `RES-001` | `READY-PI-001`, `READY-PI-002` | `BLOCK-PI-001` | `blocked` |
| `RES-002` | `READY-PI-001`, `READY-PI-003`, `READY-PI-004`, `READY-PI-005` | `BLOCK-PI-002`, `BLOCK-PI-003` | `blocked` |

补充 fail-closed 规则：

- 如果 provenance / identity 文档重新出现 placeholder，则 `BLOCK-PI-000` 会同时阻塞 `RES-001/002`；
- 即使有人把 `package_provenance_status` 改成 `release_grade_closed`，只要 pin surface 仍有 `verified_candidate_artifact`、`sanity_only` 或 `pending_acquisition` 条目，`RES-001` 仍保持 blocking；
- 即使 repo 状态未来变成 clean，只要 retained pack 仍是 `present_author_side_non_authoritative`，`RES-002` 仍保持 blocking。

## 5. 当前 gate 结论

这份 gate 当前只允许支持以下结论：

- 当前 package 已经具备统一的 artifact-pin、surrogate-identity、Stage B retained 和 Stage C retained surface；
- DENIX public artifacts 当前已在 candidate 侧完成 external verification 和 checksum pin，但还没有进入 retained benchmark input 或 release-grade provenance closeout；
- 当前 package 还没有达到 release-grade provenance / surrogate identity closeout；
- retained chain 当前只说明 author-side candidate evidence 已保存，不等于独立审阅、clean release identity 或 authority release 已完成。

## 6. 当前不允许的叙述

- “pin manifest 已经等于 release-grade provenance”
- “有 retained pack 就等于 surrogate identity 已关闭”
- “shared provenance / identity gate 已经放行 stock authority”

## 7. 当前判定

当前判定为：

> `the package now has a shared author-side provenance and surrogate-identity surface; DENIX public artifacts are externally verified and checksummed, but release-grade provenance and identity remain blocked by open retention/consumption closeout and the current dirty release-state`.
