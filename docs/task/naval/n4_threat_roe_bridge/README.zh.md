# N4 威胁 / ROE 桥接场景

状态：`2026-05-24`，作为海军 MVP 之后第一个场景扩大化规划面打开。

语言：

- 英文规范版：[`README.md`](README.md)
- 中文伴随版：`README.zh.md`

输入：

- [海军当前进展追踪](../naval_current_progress_20260524.zh.md)
- [子代理使用政策](../../../standards/governance/subagent_usage_policy.zh.md)

## 目的

定义当前 DDG/T-AKE 屏护与接触 MVP 之后的下一个海军场景。该扩展应是
`N3 -> N4` 桥接，而不是直接进入交火：它先加入威胁分类、ROE 状态和目标
分配来源证明，再考虑武器交战或毁伤真实性。

候选场景：

- `ddg51_take1_screen_threat_roe_v1`

场景概念：

- `DDG-51` 屏护 `T-AKE-1` 高价值单位；
- 红方水面接触沿现有接触报告和共享航迹路径逼近；
- 蓝方在保持屏护几何的同时推进威胁与 ROE 状态；
- 场景可以到达开火前授权态，但不要求武器发射、命中评估或毁伤终止。

## 输出

- [N4 威胁 / ROE 桥接任务簇](naval_n4_threat_roe_bridge_cluster_20260524.zh.md)
- [N4 威胁 / ROE 分发队列](naval_n4_threat_roe_dispatch_queue_20260524.zh.md)

文档预算：

- 一对 README 用于导航；
- 一对任务簇文档用于记录有限工作包；
- owner 批准分发实现工作后，新增一对 dispatch queue；
- 在实现 packets 返回前，不新增 acceptance ledger。

## 范围

范围内：

- `N4` 受威胁机动与 ROE 的真实性边界；
- 后续场景、合同、runtime/facade 和 RL 预检工作的有限任务簇；
- 明确不声明 `N5` 武器交战和 `N6` 毁伤结果；
- 后续子代理分发的依赖关系与并行安全规则。

范围外：

- 在本规划片段中创建场景 JSON、合同、测试、binding 或 runtime 代码；
- 把武器开火作为任务目标；
- 命中概率、导弹飞行、CIWS 末端防御、毁伤传播、ASW、UNREP、舰载机运行或多舰队战术；
- 声称已经有 learned naval policy。

## 闭合门

本规划面完成时，任务簇文档应记录：

- 为什么 `ddg51_take1_screen_threat_roe_v1` 是下一个候选场景；
- 真实性声明是 `N3 -> N4`，而不是 `N5` 或 `N6`；
- 子代理政策要求的有限任务簇、目标、写入范围、非目标、验证命令、闭合门、
  依赖/并行关系、轮次上限和 model/reasoning 选择；
- RL 预检面，但不把它描述成已训练任务。

本文档片段的验证：

```bash
git diff --check -- docs/task/naval
```
