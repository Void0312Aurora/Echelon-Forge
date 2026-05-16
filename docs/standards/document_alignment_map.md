# 文档对齐映射

本文档用于明确“哪些文档是当前主依据、哪些文档是专用补充、哪些文档已经归档”。

## 1. 当前有效的主依据

### 1.1 Joint / Common Core

当前联合层主依据：

- [Joint 标准总览](/home/void0312/Workshop/CMO/docs/standards/joint/README.md)
- [Joint 指挥关系与建模基线](/home/void0312/Workshop/CMO/docs/standards/joint/command_and_modeling_baseline.md)

它们负责定义：

- 联合层 command relationship
- authority delegation
- task organization 的通用模板
- commander intent / order / report 的共通骨架

### 1.2 Service Profiles

当前军种 profile 主依据：

- [USAF Profile](/home/void0312/Workshop/CMO/docs/standards/services/air_force.md)
- [US Army Profile](/home/void0312/Workshop/CMO/docs/standards/services/army.md)
- [US Navy Profile](/home/void0312/Workshop/CMO/docs/standards/services/navy.md)
- [US Marine Corps Profile](/home/void0312/Workshop/CMO/docs/standards/services/marine_corps.md)

它们负责定义：

- 哪些层级适合进入 tight-loop runtime
- 哪些层级只应保留在 operation / scenario / campaign 层
- joint/common core 如何在各军种中具体落地

## 2. 当前仍有效但属于专用补充的文档

### 2.1 Air Platform/Task Specialization

以下文档仍有效，但不再作为全项目的共通标准：

- [Air 标准总览](/home/void0312/Workshop/CMO/docs/standards/air/README.md)
- [obs.md](/home/void0312/Workshop/CMO/docs/standards/air/obs.md)
- [act.md](/home/void0312/Workshop/CMO/docs/standards/air/act.md)
- [aim.md](/home/void0312/Workshop/CMO/docs/standards/air/aim.md)
- [rep.md](/home/void0312/Workshop/CMO/docs/standards/air/rep.md)

它们只负责：

- air platform 的观测、动作、命令、报告语义

它们不负责：

- 定义 joint/common core
- 统一海战或陆战的指挥链

## 3. 已归档文档

以下文档仅保留作历史参考：

- `docs/Archive/air_first_standards/com/*.md`
- `docs/Archive/air_first_standards/com/two_ship/*.md`
- `docs/Archive/architecture/*.md`
- `docs/Archive/architecture/layers/*.md`

这些文档之所以归档，不是因为它们完全错误，而是因为它们建立在
“air-first 再尝试泛化”的路径上，已经不适合作为当前主基线。

## 4. 对项目代码的直接对齐含义

从文档标准出发，代码层后续应按以下方向对齐：

### 4.1 应尽量上提到 common core 的概念

- `command relationship`
- `authority scope`
- `task_family`
- `service_profile`
- `tactical_unit_type`
- `role_code`
- `coordination_mode`
- `recovery_site_id`

这些概念在标准树中的归属应固定为：

- `joint/common core` 负责定义字段名、层级关系、最小语义边界
- runtime/standards bridge 只负责把现有代码对象对齐到这套共通骨架
- bridge 不应把某个军种当前好用的专用术语反向提升成全项目 core 命名

换句话说，bridge 层可以暂时兼容 air-first 历史字段，
但它的 ownership 应站在 `common/core` 侧，而不是站在 air task 侧。

### 4.2 应尽量下沉到 air specialization 的概念

- `CAP`
- `runway`
- `approach_type`
- `wingman`
- `element`
- `flight`

说明：

- 上面的 air-specific 词汇在空战实现里仍然有用
- 但它们不应继续主导 core 层命名与通用模板

### 4.3 runtime/standards bridge 的文档归属

如果某份文档要回答的是“现有 runtime 里的字段/对象应由哪一层拥有”，
应按下面规则写：

1. 先判断它是在说明 `joint/common core` 骨架，还是在说明某个 profile 的具体落地
2. 如果是在讲 `Task Order / Tactical Intent / Execution Command / Report` 的共通壳，
   文档应归到 `joint/` 或本对齐映射
3. 如果是在讲 `CAP`、`runway recovery`、`wingman`、`ILS approach`，
   文档应归到 `air/`
4. 如果是在讲未来海战 `task group / task unit / warfare commander / officer in tactical command`，
   文档应先归到 `services/navy.md`，未来再由 `naval/` 专用文档承接平台/任务细化

这条规则的目的不是限制实现，而是防止 runtime bridge 文档继续把
“当前 air 代码里已经存在的字段”误写成“全项目通用核心”。

### 4.4 未来 naval profile 的 landing points

从标准 ownership 角度看，未来 naval profile 的落点应是：

- `joint/common core`
  - `task_group_id`
  - `supported_node_id`
  - `supporting_node_id`
  - `coordination_mode`
  - `recovery_site_id`
- `services/navy`
  - `officer_in_tactical_command`
  - `warfare_role_code`
  - `task group / task unit` 级控制口径
- 未来 `naval/` 专用文档
  - 舰艇/编队几何
  - 回收/补给/舰面运行
  - 海战平台专用 execution command 语义

因此，WP0 文档阶段应先明确 ownership landing points，
而不是先在 common/core 文档里预写 air 以外域的执行参数细节。

## 5. 推荐维护方式

后续新增文档时，先判断其层级：

1. 如果是跨军种共通关系，放 `joint/`
2. 如果是军种组织与控制方式，放 `services/`
3. 如果是平台或任务专用语义，放 `air/` 或未来的 `naval/`、`land/`
4. 如果是历史设计与已废弃路线，显式标 `ARCHIVED`
