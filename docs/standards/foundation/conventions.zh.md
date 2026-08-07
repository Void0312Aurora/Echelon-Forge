# 仿真约定

Language:
- English canonical: `foundation/conventions.md`
- Chinese companion: [conventions.zh.md](conventions.zh.md)

状态：`2026-05-18`，引擎中性基础约定权威版本。

本文档定义 runtime 真值载体、观测拼装与数值接口之间共享的最低层稳定约定。

它属于标准树的基础层，不负责：

- 军种画像层组织
- 联合指挥关系或 ROE 语义
- mission-observation mode 分类
- 空中或海上专属执行词汇

这些内容分别属于：

- [军种画像总览](../../domains/joint/service_profiles/README.md)
- [联合指挥与建模基线](../../domains/joint/standards/command_and_modeling_baseline.zh.md)
- [联合命令链与汇报基线](../../domains/joint/standards/command_link_and_reporting_baseline.zh.md)
- [运行时工作流与合同基线](../bridge/runtime_workflow_and_contract_baseline.md)
- [空中平台特化](../../domains/air/README.md)
- [海军特化](../naval/README.md)

## 坐标与单位约定

- 世界坐标系：`ENU`（East-North-Up）。
- 位置单位：米。
- 速度单位：米/秒。
- 高度、距离、航程剩余、横航偏差与偏移量字段统一使用米。
- `sim_time`、`time_since_update` 和各类 interval 字段统一使用秒。

这些约定应在 C++、Python 绑定、scenario-loader bridge 与可视化辅助层之间保持稳定。

## 角度约定

- 航向采用 NAV 度：`0 = North`，顺时针为正，归约到 `[0, 360)`。
- 相对方位与相对 bearing 采用 NAV 度，范围 `[-180, 180]`，顺时针为正。
- pitch 与 roll 使用度。
- `TrackData.azimuth` 与 `RWREvent.bearing` 使用同一套相对角度符号约定。

参考换算：

- 数学角度 `atan2(dy, dx)` 采用 `0 = East`，逆时针为正
- `nav_deg = 90 - math_deg`，再归约到 `[0, 360)`

## 真值载体与环境观测的区分

仓库里存在不止一种“观测”表面。这个边界在这里统一规定。

### `AgentObservation` 是真值/状态载体

C++ 的 `AgentObservation` 结构是 kernel 侧的低层状态载体，包含：

- `x/y/z`、`vx/vy/vz`、`heading/pitch/roll`、`speed` 等 own-state kinematics
- `health`、`missiles_remaining`、`can_fire`、`gear_state`、`throttle`、
  `total_reward` 等状态字段
- `contacts`、`rwr_warnings` 等接触与告警容器

它应被视为结构化真值/状态 DTO，而不是最终 RL observation schema。

### 环境观测是拼装后的产物

Python 环境会把观测拼成固定键：

- `instruments`
- `contacts`
- `rwr`
- `mission`
- 可选的 `proprio`

这些产物是由 truth、instrument、mission-command state 与 runtime products
共同拼装出来的 bridge-level arrays，不等同于原始 `AgentObservation` 布局。

## 传感器与航迹约定

### `TrackData`

当前维护中的中性解释如下：

- `id`：track identifier
- `range`：米
- `azimuth`：相对本机机头的 NAV 度
- `elevation`：相对本地地平线的角度
- `closing_speed`：米/秒，正值表示正在接近
- `time_since_update`：距离上次刷新经过的秒数
- `quality`、`confidence`、`classification_confidence`：`[0.0, 1.0]` 归一化评分

`source`、`classification`、`status`、`usability` 等字段目前保持为小型枚举码。
它们更细的条令含义应等待各领域传感器标准进一步稳定后再下沉定义。

### `RWREvent`

当前维护中的中性解释如下：

- `bearing`：相对 NAV 度
- `signal_strength`：无量纲信号强度值
- `is_lock`：是否表示跟踪/锁定
- `is_launch`：是否表示发射/制导

这些字段表达的是 warning semantics，而不是完整的 emitter-intelligence ontology。

## 数组拼装约定

环境在拼装数组观测时，当前维护路径统一遵守以下中性规则。

### 数值类型与形状稳定性

- 拼装后的数值观测数组应使用 `float32`
- `contacts` 形状为 `[max_contacts, 5]`
- `rwr` 形状为 `[max_rwr, 4]`
- `proprio` 若存在，则为与环境 action shape 对齐的一维向量

### 填充、截断与清洗

- 当可用条目少于配置上限时，contact 与 RWR 数组使用零填充
- 超出配置上限的条目在上限处截断
- 非有限数值统一清洗为 `0.0`
- instrument 向量在转成 `float32` 前，应裁剪到 `[-1e6, 1e6]`

这些规则是 runtime 稳定性规则，不是领域条令。

### Mission observation 向量仍是 mode-dependent

`mission` 数组是一个按 mode 变化的向量产物。本文档只负责以下事实：

- 它是固定顺序的数值向量
- 它通过 runtime workflow bridge 进行拼装
- 字段可见性随 mode 变化，而不是自由展开

真正的字段分类与 mode 名称，应继续由空中专属文档和 runtime workflow 文档负责。

## Action surface 约定

本文档不重写 `PilotAction` 的字段列表。那部分属于 [air/act.md](../../domains/air/standards/pilot_action_contract.md)。

真正属于这里的中性规则只有：

- 环境对外的 action arrays 应保持稳定数值顺序
- 当 action history 被复用为 `proprio` 时，应保留同一顺序
- `active` 这类有效性标记用于决定命令面或动作面是否处于激活状态

更细的 takeoff、formation、weapon、avionics 语义，继续由特化文档负责，而不是由基础层接管。

## 确定性与工作流边界

- command generation 与 command delivery 是不同概念
- pure-computation layer 的 runtime products 应是 prepared inputs 的确定性函数
- Python 侧的加载、归一化与 product application 属于 bridge stages，不应反过来重定义底层单位或数值语义

这些工作流边界会在
[运行时工作流与合同基线](../bridge/runtime_workflow_and_contract_baseline.md) 中进一步展开。

## 相关文档

- [标准概览](../README.md)
- [联合指挥与建模基线](../../domains/joint/standards/command_and_modeling_baseline.zh.md)
- [运行时工作流与合同基线](../bridge/runtime_workflow_and_contract_baseline.md)
- [空中平台特化](../../domains/air/README.md)
