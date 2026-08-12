# A2 近炸引信真实性代理当前状态

状态：`2026-06-16` PF-R5 聚焦矩阵验证完成但保留残余。本子项目已有机制说明、gap audit、
surrogate contract、runtime 解释性实现和最终验证制品。

英文辅文：
[missile_lethality_proximity_fuze_realism_current_status_20260616.md](missile_lethality_proximity_fuze_realism_current_status_20260616.md)。

## 相比上一个 checkpoint 的变化

此前没有 checkpoint。本文现在记录完整 surrogate pass：PF-R1 公开机制说明、PF-R2 只读 runtime
gap audit、PF-R3 surrogate contract、PF-R4 聚焦 runtime 实现和 PF-R5 矩阵验证。

## 成熟度矩阵

| 区域 | 成熟度 | 证据 | 下一步 | 禁止过度声明 |
| --- | --- | --- | --- | --- |
| 子项目边界 | active / validation checkpoint | [README.zh.md](README.zh.md) | 保持 PF-R6 收口同步 | runtime 修改限于已记录的 surrogate 切片。 |
| 公开机制资料 | pass / non-authoritative | [public_mechanism_source_note_20260616.zh.md](public_mechanism_source_note_20260616.zh.md) | 实现前复核 | 公开来源不给具体弹种引信真值。 |
| Runtime gap audit | pass / read-only | [current_runtime_gap_audit_20260616.zh.md](current_runtime_gap_audit_20260616.zh.md) | 实现前复核 | 当前 proxy 不是真实引信模型。 |
| Surrogate contract | pass / implemented design | [proximity_fuze_surrogate_contract_20260616.zh.md](proximity_fuze_surrogate_contract_20260616.zh.md) | 保持 authority 边界附着 | 不释放真实引信或 Pk authority。 |
| Implementation | pass / 聚焦 runtime evidence | [proximity_fuze_runtime_implementation_20260616.zh.md](proximity_fuze_runtime_implementation_20260616.zh.md) | 保持范围冻结 | 不释放 deterministic fuze authority 或 Pk。 |
| Validation | pass_with_residuals / 聚焦矩阵证据 | [validation/pf_r5_proximity_fuze_validation_20260616.zh.md](validation/pf_r5_proximity_fuze_validation_20260616.zh.md) | 只保留最终制品 | 不声明 kill probability 或 stock lethality。 |

## 证据链接

- A2 父入口：[../README.zh.md](../README.zh.md)
- MLF-2 几何/引信指针：
  [../missile_lethality_geometry_fuze/README.zh.md](../missile_lethality_geometry_fuze/README.zh.md)
- 当前实现面：
  [../../../../../src/systems/combat/damage_system_common.h](../../../../../../../src/systems/combat/damage_system_common.h)
- 当前聚焦测试入口：
  [../../../../../tests/runtime/air_combat/weapon_guidance_realism/test_launch_guidance_and_dynamics.py](../../../../../../../tests/runtime/air_combat/weapon_guidance_realism/test_launch_guidance_and_dynamics.py)
- 真实性 authority 边界：
  ../../../../standards/foundation/realism_authority_boundary.zh.md（`git show e8dc0b29~1:docs/standards/foundation/realism_authority_boundary.zh.md`）
- 公开机制说明：
  [public_mechanism_source_note_20260616.zh.md](public_mechanism_source_note_20260616.zh.md)
- Runtime gap audit：
  [current_runtime_gap_audit_20260616.zh.md](current_runtime_gap_audit_20260616.zh.md)
- Surrogate contract：
  [proximity_fuze_surrogate_contract_20260616.zh.md](proximity_fuze_surrogate_contract_20260616.zh.md)
- Runtime 实现结果：
  [proximity_fuze_runtime_implementation_20260616.zh.md](proximity_fuze_runtime_implementation_20260616.zh.md)
- PF-R5 验证摘要：
  [validation/pf_r5_proximity_fuze_validation_20260616.zh.md](validation/pf_r5_proximity_fuze_validation_20260616.zh.md)
- PF-R5 最终热图：
  [validation/pf_r5_proximity_fuze_validation_heatmaps_20260616.png](validation/pf_r5_proximity_fuze_validation_heatmaps_20260616.png)

## 残余登记

| Residual | 状态 | Owner | 解决路径 |
| --- | --- | --- | --- |
| 缺公开资料机制说明 | closed | main thread | 已由 `PF-P1` 关闭。 |
| 缺当前 runtime gap audit | closed | main thread | 已由 `PF-P2` 关闭。 |
| 缺后续 surrogate contract | closed | main thread | 已由 `PF-P3` 关闭。 |
| 缺实现确认 | closed | user/main thread | 已由明确继续 `PF-P4` 关闭。 |
| 验证矩阵未定义 | closed_with_residuals | main thread | 已由 PF-R5 CSV/JSON/heatmap/summary 制品关闭。 |
| 初始偏置对称性不是纯测试 | retained residual | future fixed-point harness | live guidance 仍在链路内，所以初始发射偏置不是纯起爆点对称性测试。 |
| 真实 fuze/Pk authority 缺失 | deferred | future authority package | 另建 source-admission 与 validation package。 |

## 推荐下一步

1. 保留 PF-R5 最终 CSV、JSON、热图和摘要作为标准验证制品。
2. 将初始偏置不对称视为 live-guidance 残余，而不是纯引信对称性失败。
3. 本轮验证继续排除 reward、Pk 和真实武器校准。

## 明确拒绝的声明

- 真实 AIM-120C 或 AIM-120C-class deterministic fuze 行为。
- 真实 Pk、具体弹种杀伤或 stock runtime authority。
- 校准后的 target-detecting-device 阈值。
- 把 PF-R4/PF-R5 surrogate 证据冒充完整杀伤接受。
- 用 reward 或 terminal-state 调参替代引信链真实性。
