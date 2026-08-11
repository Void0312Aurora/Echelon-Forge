# MLF-9 当前状态

状态：`2026-06-19` accepted / archived。MLF-9 在 MLF-8 验收后关闭有边界的
Pk / 统计趋势 simulation-report 切片。

英文主文：
[missile_lethality_pk_statistical_trends_current_status_20260619.md](missile_lethality_pk_statistical_trends_current_status_20260619.md)。

## 摘要

已验收切片创建持久 MLF-9 工作面，盘点 accepted inputs，定义 metric contract，对齐
diagnostics rows，使 `structural_breakup` 能和 component damage、consequence、lifecycle
阶段放在同一张表中观察，新增确定性行级 trend harness，通过 process probe 将 trend payload
作为 retained diagnostics artifact 暴露，并记录 focused validation 和 acceptance。输出仍然是基于可回放链路事实的仿真趋势报告，
不是校准后的现实杀伤概率。

## 成熟度矩阵

| 区域 | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| 子项目表面 | P0 pass | README、任务簇、派发队列、当前状态、archive 占位；docs diff 和链接检查通过 | setup 本身不证明 runtime trend harness |
| 上游事实 | accepted inputs | MLF-5 部件失效、MLF-6 结构失效、MLF-7 后果、MLF-8 生命周期 | 输入是已验收仿真事实，不是 Pk 校准 |
| 证据盘点 | P1 pass | Inventory doc 命名 reusable rows、gaps 和 safe write sets | 盘点本身不是趋势证据 |
| Metric contract | P2 initial pass | Metric contract 定义 row source、denominators、buckets、grouping fields 和 uncertainty labels | 契约仍拒绝校准 Pk |
| Structural row surface | P2 initial pass | Process probe row contract 现在暴露 `structural_breakup`；聚焦 diagnostics tests 通过 | Row exposure 不改变 damage physics |
| 趋势提取 | P3 initial pass | `tools/diagnostics/mlf9_statistical_trends.py`、`tests/tools/test_mlf9_statistical_trends.py`、trend harness result doc | 仅做 row summarization；不提升 runtime physics 或 calibration |
| 报告集成 | P4 initial pass | Process probe 嵌入 `mlf9_statistical_trends`，并可写出 `--mlf9_report_json_out`；report integration result doc | 仅为 diagnostics/report artifact；不进入 reward/training/calibration consumer |
| 验证 | P5 pass | Focused validation 报告 `53 passed`、`git diff --check` clean、本地 Markdown 链接 0 缺失 | 验证只覆盖 simulation/report behavior，不覆盖现实 Pk |
| 收口 | P6 pass | Acceptance record 和父级索引将切片标记为 accepted / archived | 旧 active 路径是兼容指针 |
| 校准 | held | MLF-10 保留 | 不声明真实武器或具体目标概率 |

## 推荐行动顺序

1. 使用已归档证据包作为 MLF-9 canonical record。
2. 只有 calibration gates、public-source outcome admission 或具体武器/目标概率讨论才开启 MLF-10。
3. 继续 hold Pk 校准、公开结果拟合、reward shaping 和 entity deletion。

## 拒绝声明

- 真实 AIM-120C、F-16、MQ-9 或 stock platform Pk。
- 公开结果校准或验证。
- Reward shaping 或训练收益。
- 实体删除、直接坠毁规则或碎片物理。
