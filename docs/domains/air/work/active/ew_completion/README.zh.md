# Air EW 完善工作包

状态：`2026-10-06` active；E1 本地验收通过，待发布 Stack 并完成远端检查与审阅。

Document kind: plan
Lifecycle: active
Canonical: `docs/domains/air/work/active/ew_completion/README.md`
Owner: domains/air
Last verified: 2026-10-06

Language:

- 英文规范：[README.md](README.md)
- 中文入口：本文件。高频任务簇文档采用英文规范。

Inputs:

- [Air 主入口](../../../README.zh.md)
- [任务簇](ew_completion_task_clusters_20261006.md)

## Purpose

按依赖顺序完善 EW，并拆分为可审阅的 PR Stack。

## Current State

诱饵与基础干扰机制已在主分支；RF/ESM 数据、确认与过期、被动观测已通过本地验收。

## Scope

范围包括 ESM、干扰效果与资源、时序、协同、动作准入和命名终局场景。
具体装备的 RF 校准、发射机库、旁瓣与虚假航迹需要独立的来源和验收。

## Phase Plan

E1 RF/ESM → E2 干扰与资源 → E3 时序 → E4 协同 → E5 动作准入 → E6 终局验收。

## Task Clusters

每簇一次实现与最多两次证据驱动的修复。扩大范围时单独登记后续簇。

## Outputs And Evidence

E1 分成数据契约与运行时观测两个 PR。接收功率使用自由空间参考；置信度表示
所需独立扫描的完成比例；相邻有效观测的间隔超过记忆时限后重新计数，
它不表示滑动窗口计数或探测概率。旧内容和默认观测键保持兼容。

## Acceptance Gate

以最后一次编译的代码执行负面用例、状态往返、EW 回归及 Python 内容/投影验证；
创建 PR 不等于通过审阅，E1 不等于取得可玩性验收。

## Residuals And Next Steps

E2-E6 仍需逐项实现。当前导弹雷达分类是粗粒度发射机代理，基础 DRFM
只修改同一目标的距离。旧版传感器字段已提供受限转换，完整跨修订状态一致性仍需独立证据。详见英文规范的具体边界。

## Archive

完成声明的验收、残余项归属、审阅与入口同步后再归档。
