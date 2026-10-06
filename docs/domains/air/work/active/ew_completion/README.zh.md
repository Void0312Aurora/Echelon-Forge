# Air EW 完善工作包

状态：`2026-10-07` active；E1 与有限范围的 E2 本地验收通过。E1 Stack 审阅和 #104 被取消的 CUDA 工具链检查仍未闭合。

Document kind: plan
Lifecycle: active
Canonical: `docs/domains/air/work/active/ew_completion/README.md`
Owner: domains/air
Last verified: 2026-10-07

Language:

- 英文规范：[README.md](README.md)
- 中文入口：本文件。高频任务簇文档采用英文规范。

Inputs:

- [Air 主入口](../../../README.zh.md)
- [任务簇](ew_completion_task_clusters_20261006.md)

## Purpose

按依赖顺序完善 EW，并拆分为可审阅的 PR Stack。

## Current State

诱饵与基础干扰机制已在主分支；RF/ESM 数据、确认与过期、被动观测，以及 E2 的频段门控、发射预算和有符号 DRFM 距离偏移已通过本地验收。

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

E2 的完整 Jammer/雷达 RF 契约才允许按频段重叠干扰；旧式配置保留现有带宽代理。
发射 EIRP 仍只用于发射观测，干扰 burn-through 使用独立的 `power_watts` 标定。
可选预算必须同时配置突发上限与冷却时间；缺省仍为无限时长。DRFM 的正负偏移
仅改写同一目标的报告距离，不生成独立虚假航迹。

## Acceptance Gate

以最后一次编译的代码执行负面用例、状态往返、EW 回归及 Python 内容/投影验证；
创建 PR 不等于通过审阅，E1 不等于取得可玩性验收。

## Residuals And Next Steps

外部/支援干扰机组合尚未实现；当前频段、burn-through 和平台效果仍是工程代理，
没有校准 J/S，也不生成虚假航迹生命周期。#104 CUDA 检查在安装工具链时被取消，
不能视为通过。当前导弹雷达分类仍是粗粒度发射机代理。旧版传感器字段已提供受限
转换，完整跨修订状态一致性仍需独立证据。详见英文规范的具体边界。

## Archive

完成声明的验收、残余项归属、审阅与入口同步后再归档。
