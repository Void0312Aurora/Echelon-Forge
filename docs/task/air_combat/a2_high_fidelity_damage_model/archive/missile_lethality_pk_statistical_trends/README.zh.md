# MLF-9 Pk / 统计趋势

状态：`2026-06-19` accepted / archived，用于有边界的 Pk / 统计趋势投影。
本子项目在 MLF-8 验收后关闭 simulation-trend 切片，且早于任何校准门工作。

语言：

- 英文主文：[README.md](README.md)
- 中文辅文：`README.zh.md`

输入：

- A2 父级索引：[../../README.zh.md](../../README.zh.md)
- MLF-5 部件失效证据：
  [../missile_lethality_component_failure/README.zh.md](../missile_lethality_component_failure/README.zh.md)
- MLF-6 结构失效证据：
  [../missile_lethality_structural_failure/README.zh.md](../missile_lethality_structural_failure/README.zh.md)
- MLF-7 后果桥接：
  [../missile_lethality_secondary_consequence_coupling/README.zh.md](../missile_lethality_secondary_consequence_coupling/README.zh.md)
- MLF-8 残骸 / 碎片生命周期：
  [../missile_lethality_debris_wreck_lifecycle/README.zh.md](../missile_lethality_debris_wreck_lifecycle/README.zh.md)
- 损伤后果奖励面：
  [../../damage_consequence_reward_surface/README.zh.md](../../damage_consequence_reward_surface/README.zh.md)
- 真实性权威边界：
  [../../../../../standards/foundation/realism_authority_boundary.zh.md](../../../../../standards/foundation/realism_authority_boundary.zh.md)

## 目的

MLF-9 把可回放的导弹杀伤链转成有边界的统计趋势证据。它应该回答的是：
“更近的起爆是否在仿真里倾向于更严重后果？”、“出现结构解体的链路，是否比未解体链路更常走向终端损失？”

它不应该回答：“真实 AIM-120C 对真实 F-16 或 MQ-9 的 Pk 是多少？”现实校准、
公开来源准入、具体弹种真值和具体目标真值都继续留给 MLF-10 或后续工作。

## 当前状态

| 区域 | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| 上游链路事实 | accepted inputs | 已归档 MLF-5 到 MLF-8 证据面 | 输入是可回放的仿真事实，不是校准后的现实数据 |
| 统计权威 | accepted / archived | 本 README、inventory、metric contract、trend/report integration results、validation record、acceptance record 和聚焦 diagnostics/tests | 当前没有任何校准 Pk 数值被验收 |
| 奖励 / 训练面 | retained adjacent work | 损伤后果奖励面仍独立维护 | MLF-9 不创建 reward 权威或训练收益声明 |
| 校准 | held | MLF-10 保留为校准门 | 不声明 stock weapon 或 target-specific truth |

## 范围

纳入：

- 定义 MLF-9 指标契约：回放行、事件 join、后果分桶、趋势摘要和不确定性字段。
- 只有契约明确后，才构建或扩展 diagnostics / replay 工具。
- 输出保持为 synthetic simulation trend report，除非后续校准门明确提升。
- 用受控 fixture 测试单调性和一致性，不把测试结果说成现实概率。
- 如果上游字段不足以诚实投影趋势，把缺口记录为 residual。

不纳入：

- 不声明真实弹种 Pk、真实目标杀伤率或 stock AIM-120C 效能。
- 不做 MLF-10 校准门、公开结果拟合或来源准入提升。
- 不做 reward shaping、实体删除、直接坠毁规则或碎片物理。
- 不修改已归档 MLF-1 到 MLF-9 包；除非只是修断链。

## 阶段计划

| 阶段 | 目标 | 入口条件 | 退出条件 | 状态 |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | 建立子项目并冻结禁止声明。 | MLF-8 已验收 / 归档。 | 父级索引链接本项目，任务簇存在。 | pass |
| `P1 Evidence Inventory` | 盘点可回放上游字段和缺失 join。 | P0 文档存在。 | inventory 命名 accepted inputs、缺失字段和安全写集。 | pass |
| `P2 Metric Contract` | 定义行、分母、分桶和不确定性标签。 | P1 完成。 | 契约可实现且不暗示校准。 | initial pass |
| `P3 Trend Harness` | 产出确定性的回放 / 统计摘要。 | P2 contract available。 | 聚焦测试覆盖受控 fixture 趋势。 | initial pass |
| `P4 Integration` | 通过 diagnostics 或 retained artifact 暴露报告。 | P3 trend harness available。 | 报告可消费且不泄漏到 reward / training。 | initial pass |
| `P5 Validation` | 执行聚焦验证和 smoke。 | P4 report integration available。 | 验证能区分趋势证据和真实 Pk。 | pass |
| `P6 Closure` | 验收、hold 或重划 MLF-9，并同步索引。 | P5 证据存在。 | README/status/acceptance、指针路径和 archive registry 一致。 | pass |

## 任务簇

- 任务簇计划：
  [missile_lethality_pk_statistical_trends_task_clusters_20260619.zh.md](missile_lethality_pk_statistical_trends_task_clusters_20260619.zh.md)
- 派发队列：
  [missile_lethality_pk_statistical_trends_dispatch_queue_20260619.zh.md](missile_lethality_pk_statistical_trends_dispatch_queue_20260619.zh.md)
- 证据盘点：
  [missile_lethality_pk_statistical_trends_inventory_20260619.zh.md](missile_lethality_pk_statistical_trends_inventory_20260619.zh.md)
- 指标契约：
  [missile_lethality_pk_statistical_trends_metric_contract_20260619.zh.md](missile_lethality_pk_statistical_trends_metric_contract_20260619.zh.md)
- 趋势工具结果：
  [missile_lethality_pk_statistical_trends_trend_harness_20260619.zh.md](missile_lethality_pk_statistical_trends_trend_harness_20260619.zh.md)
- 报告集成结果：
  [missile_lethality_pk_statistical_trends_report_integration_20260619.zh.md](missile_lethality_pk_statistical_trends_report_integration_20260619.zh.md)
- 聚焦验证：
  [missile_lethality_pk_statistical_trends_validation_20260619.zh.md](missile_lethality_pk_statistical_trends_validation_20260619.zh.md)
- 验收记录：
  [missile_lethality_pk_statistical_trends_acceptance_20260619.zh.md](missile_lethality_pk_statistical_trends_acceptance_20260619.zh.md)

## 输出和证据

- MLF-9 planning surface 和父级索引入口。
- P1 证据盘点，覆盖 MLF-5 到 MLF-8 输入和 diagnostics 输出。
- P2 初始 metric contract，定义 replay rows、denominators、outcome buckets 和不确定性标签。
- Diagnostics process-probe row-surface 更新，暴露 `structural_breakup` rows 和 snapshot fields。
- 基于显式 row fixtures 的确定性 MLF-9 trend harness：
  `tools/diagnostics/mlf9_statistical_trends.py` 和
  `tests/tools/test_mlf9_statistical_trends.py`。
- 通过 `mlf9_statistical_trends` payload 和可选 `--mlf9_report_json_out` 暴露的
  process-probe retained report integration。
- P5 focused validation 报告 `50 passed`、diff whitespace clean，以及 MLF-9/A2 docs
  集合本地 Markdown 链接 0 缺失。
- P6 acceptance record 将 deterministic simulation-trend/report 切片标记为
  accepted / archived，并继续 hold real-world Pk/calibration。

## 验收门

本子项目只有在以下条件满足后才能标记 accepted：

- MLF-9 报告来自显式回放行或受控 fixture。
- 测试证明趋势摘要是确定的、有边界的，并且不会泄漏到 reward、实体删除或校准权威。
- 每个趋势报告都写清分母、样本来源、不确定性标签和禁止声明。
- 真实弹种 Pk 和校准声明继续拒绝。

## 残余和下一步

- 立即工作：已验收的 simulation-trend/report 切片不需要继续实现。
- 推迟项：MLF-10 校准门、公开来源结果准入、特定武器 / 目标校准。

## Archive

MLF-9 已物理归档到父级 A2 本地 archive。旧 active 路径现在只保留轻量兼容指针。
