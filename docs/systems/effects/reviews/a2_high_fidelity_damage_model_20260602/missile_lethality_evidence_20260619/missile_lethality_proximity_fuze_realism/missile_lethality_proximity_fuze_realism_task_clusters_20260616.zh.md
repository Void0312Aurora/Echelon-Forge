# A2 导弹近炸引信真实性代理任务簇

状态：`2026-06-16` finite task cluster list，用于
[README.zh.md](README.zh.md)。PF-P5 验证已完成但保留残余；PF-P6 收口已同步。

英文辅文：
[missile_lethality_proximity_fuze_realism_task_clusters_20260616.md](missile_lethality_proximity_fuze_realism_task_clusters_20260616.md)。

## 边界决策

本子项目可以创建公开资料调研、当前 runtime gap audit、surrogate contract 设计、派发记录和验收标准。
不得把 runtime config、场景行为、训练 reward 或 authority claim 扩大到已明确接受的 PF-P4/PF-P5
surrogate evidence 切片之外。

本子项目也不得暗示真实武器引信参数、deterministic fuze authority、Pk、stock runtime authority
或具体弹种杀伤结论。

## 有限任务簇列表

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `PF-P0` | main thread | n/a | 创建符合 `docs/agent` 的 planning surface 和父级导航 | `docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_proximity_fuze_realism/**`；父 A2 README | runtime 修改、测试、reward 修改 | Markdown inspection、本地链接、`git diff --check` | 子项目可导航，并明确当前 implementation 边界 | 无依赖 | 1 | pass |
| `PF-P1` | main thread | high | 以高层机制方式准入公开资料事实 | `public_mechanism_source_note_20260616.md`；`public_mechanism_source_note_20260616.zh.md` | 真实引信阈值、具体弹种 target-detecting-device 参数、涉密逻辑 | 来源准入检查，无数字权威声明 | 来源被分成 admitted mechanism facts 和 rejected authority claims | `PF-P0` 后；可先于 runtime audit | 1 + 1 repair | pass |
| `PF-P2` | main thread | high | 用 admitted mechanism facts 审计当前 runtime 行为 | `current_runtime_gap_audit_20260616.md`；`current_runtime_gap_audit_20260616.zh.md` | 代码修改、行为修改 | 只读 `rg` / 文件检查、聚焦测试清单 | gap 表命名 proxy 假设和保留的 observed facts | `PF-P1` 后；和 `PF-P3` 串行 | 1 + 1 repair | pass |
| `PF-P3` | main thread | high | 设计后续 surrogate 事件和诊断合同 | `proximity_fuze_surrogate_contract_20260616.md`；`proximity_fuze_surrogate_contract_20260616.zh.md` | 未获批前实现字段或改事件 schema | contract review、link check、test-plan inspection | contract 区分 nearest approach、detection、trigger、detonation point 和 mechanism coverage | `PF-P2` 后 | 1 + 1 repair | pass |
| `PF-P4` | main thread | high | 只实现获批的 proximity-fuze surrogate | runtime contracts、damage system、Python bindings、diagnostics、focused tests | Pk、deterministic fuze、stock weapon truth、reward masking | `ef_py` build；聚焦 runtime、diagnostics、training、binding tests | runtime 行为匹配已接受 surrogate evidence contract | 明确继续后；串行 | 2 | pass |
| `PF-P5` | main thread | high | 实现后运行距离/初始偏置/高度机制对照 | `validation/pf_r5_proximity_fuze_validation.py`；最终 CSV/JSON/heatmap/summary 制品 | 训练 reward 展示、kill probability claim、完整校准 | 矩阵制品、聚焦 runtime 脚本、文档摘要 | 趋势可解释，残余已记录 | `PF-P4` 后；本轮串行 | 2 | pass_with_residuals |
| `PF-P6` | main thread | n/a | 决定 accepted 边界并同步文档/index/archive | README/status/acceptance；父 A2 README | 把 surrogate 证据标成真实引信或 Pk acceptance | Markdown link check、`git diff --check`、accepted validation commands 摘要 | acceptance 边界明确，过度声明仍被拒绝 | 最后；在 `PF-P5` 后 | 1 | pass |

## 派发规则

- 每个 worker packet 必须只对应上表一个任务簇。
- `PF-P1` 到 `PF-P3` 只做文档/设计，不得修改 runtime code、测试、配置、reward 或训练输出。
- `PF-P4` 和 `PF-P5` 已完成。后续工作必须打开新的有界 packet，不能静默扩展本矩阵。
- 不允许两个 worker 同时修改同一个规范表、状态行或验收章节。
- 任务簇超过 round cap 时，先停止并重划范围，不能追加无限 wave。
- 遵守
  [Subagent 使用规范](../../../../../../engineering/automation/standards/subagent_usage_policy.zh.md)。

## Worker Packet 要求

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
authority/overclaim check:
```

## 验证计划

```bash
git diff --check -- docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_proximity_fuze_realism docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/README.md docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/README.zh.md
```

实现验证已记录在
[proximity_fuze_runtime_implementation_20260616.zh.md](proximity_fuze_runtime_implementation_20260616.zh.md)。
PF-P5 验证已记录在
[validation/pf_r5_proximity_fuze_validation_20260616.zh.md](validation/pf_r5_proximity_fuze_validation_20260616.zh.md)。

## 验收标准

- planning surface 可从父 A2 README 导航。
- 公开资料事实保持机制级、无参数、非权威。
- 实现前已经记录当前 runtime gap。
- implementation 继续限制在 PF-P4 surrogate evidence 切片内。
- PF-P5 验证继续限制在 surrogate 门控和机制趋势内。
- 文档继续拒绝 Pk、deterministic fuze authority 和具体弹种杀伤。

## 残余地图

Immediate:

- 本子项目收口暂无 immediate 项。

Retained:

- live guidance 仍在链路内时，初始发射偏置对称性不是纯引信对称性测试。

Deferred:

- 真实武器校准。
- Pk。
- deterministic fuze authority。
- 轨迹/环境/导引头随机性。
- 飞行员/控制权限 kill-state coupling。
