<!-- Machine-translated draft generated on 2026-05-21 from docs/task/ground/g1_contract_skeleton/README.md. Review before treating this file as authoritative. -->

# G1 合约骨架

状态：`2026-05-21` G1-A 预检和 G1-B 狭窄 Python 配置文件实现已接受。

语言：

- 英文标准版：`README.md`
- 中文对照版：目前暂不需要；这是一个高频变动的任务片段。

输入：

- [地面标准概述](../../../standards/ground/README.md)
- [地面最小任务结构](../../../standards/ground/minimal_task_structure.md)
- [地面领域引导计划](../ground_domain_bootstrap_plan_20260521.md)
- [子智能体使用策略](../../../standards/governance/subagent_usage_policy.md)

## 目的

为 `ground` 任务配置文件创建最小的合约骨架，不添加运行时行为。

## 输出

- [G1 配置文件和 DTO 合约集群](g1_profile_dto_contract_cluster_20260521.md)
- [G1 配置文件和 DTO 预检](g1_profile_dto_preflight_20260521.md)

## 发布状态

- `G1-A`：仅预检，已返回 `implementation-ready`。
- `G1-B`：已接受仅用于 Python 配置文件实现。
- DTO 骨架：G1 中不需要。
- 推迟：C++ DTO、Python 绑定、运行时行为、场景加载器行为以及命令传递语义。
- 主线验证已通过，针对聚焦的 G1 套件和完整的 `tests/leader`。

## 范围

范围内：

- 为 `army`、`ground` 和 `land` 的配置文件解析
- 起始 `ground_profile` / 适配器骨架
- `TASK_MOVE`、`TASK_OCCUPY`、`TASK_SUPPORT` 的默认映射
- 在字段所有权确定后，可选为空或最小的 DTO 着陆点
- 聚焦于解析、默认值和兼容性的测试

范围外：

- 移动动力学
- 命令传递行为
- 观测导出
- 武器/效果行为

## 门控条件

当地面配置文件可以在不改变空中/海军行为的情况下被解析和规范化，并且聚焦测试证明了起始任务默认值有效时，G1 即可合并。
