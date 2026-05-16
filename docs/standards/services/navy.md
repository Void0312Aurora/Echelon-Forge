# US Navy Profile

本文档定义项目在海战/海上行动建模时采用的 US Navy profile。

## 1. 官方现实基础

Navy 公开资料显示，海军战术组织比陆军更“任务编组化”，并且在战术控制上广泛采用
`Task Force` 与 `Composite Warfare Commander (CWC)` 体系。

当前公开官方依据：

- [U.S. 7th Fleet, CTF 71 establishment](https://www.c7f.navy.mil/Media/News/Display/Article/2641477/ctf-71-establishment-enhances-readiness-in-7th-fleet/)
- [TTGP Warfare Commanders Conference I](https://www.ttgp.navy.mil/OFRP-Syllabus/Warfare-Commanders-Conference-I/)
- [NAVIFOR, IW Has a Seat at the Table](https://www.navifor.usff.navy.mil/Press-Room/News-Stories/Article/2395110/iw-has-a-seat-at-the-table/)
- [COMPHIBRON 5 About](https://www.surfpac.navy.mil/Ships/Amphibious-Squadron-COMPHIBRON-5/About/)

从这些官方页面可以确认：

- `Task Force` 是实际任务组织单元
- sea combat / amphibious / information warfare 等能力会围绕 `CWC table`
  与 warfare commanders 组织
- `Officer in Tactical Command` 与 `Composite Warfare Commander` 在舰队/编队场景中是现实存在的角色

## 2. 建模结论

### 2.1 不应进入 tight-loop runtime 的层

- numbered fleet
- major theater maritime component

这些更适合作为：

- operation-level command nodes
- scenario tasking and force packaging nodes

### 2.2 更适合进入 tight-loop runtime 的层

海战 tight-loop runtime 更适合放在：

- `task group / task unit` 级 tactical grouping
- `warfare commander` 级角色协同
- `single ship / ship section`

说明：

- Navy profile 的关键不是“像空军一样分 element”，而是
  `task organization + warfare commander role`

## 3. 对项目通用模板的影响

如果项目后续扩海战，joint/core 层必须能表达：

- `task_group_id`
- `warfare_role_code`
- `supported/supporting relation`
- `officer_in_tactical_command`

而不能把核心协同对象预设成：

- `lead / wingman`

那只适合空战 sortie 级编组，不适合舰队/编队控制。

## 4. 对 upcoming naval module 的直接约束

若后续把当前 `tasking / command` 继续拆为 `common + air + naval`，Navy profile 应按下面方式落位：

### 4.1 应继续留在 `common` 的对象

- `service_profile`
- `task_family`
- `tactical_unit_type`
- `command_relationship`
- `authority_scope`
- `coordination_mode`
- `task_group_id`
- `supported_node_id / supporting_node_id`
- `recovery_site_id`

这些字段在 Navy 里仍然成立，但含义应由 Navy profile 解释，而不是改成 air 词汇。

### 4.2 应进入 `naval` 的对象

- `warfare_role_code`
- `officer_in_tactical_command`
- naval `task force / task group / task unit` 组织层级解释
- formation / station / screen / support 的舰队语义
- 舰艇 section、surface action group、amphibious group 等专用 tasking 语义

### 4.3 不应从 air 直接照搬到 naval core 的对象

- `lead / wingman`
- `element lead`
- `runway`
- `approach type`
- `takeoff clearance`
- air sortie phase 驱动的 `LeaderPhase`

如果 naval 也需要“谁跟谁走、谁守哪个站位”，应优先建模为 naval role / station / warfare commander 语义，
而不是把 air 两机编队词汇泛化成通用模板。

## 5. 对文档与代码协同的建议

为 upcoming module work，Navy 侧建议按下面顺序推进：

1. 先在 `common` 固定 joint 字段和 DTO 骨架。
2. 再由 Navy profile 明确这些字段在 naval runtime 中对应的组织层级与角色口径。
3. 最后才在 `naval` 专用文档里增加 tight-loop station / screen / support / recovery 语义。

这样可以避免在 `common` 层过早写入 air-first 的编队与回收假设。

## 6. 对 runtime/standards bridge 的 ownership 含义

本 profile 对 bridge 文档的要求是：

- `services/navy.md` 负责说明 Navy profile 希望 core 保留哪些共通挂点
- 它不负责定义 naval platform 的具体执行命令字段
- 它也不应把 air 已有的 `route / landing / wingman` 语义直接当成 Navy 的默认模板

对未来模块边界的文档落点，可先按下面理解：

- `joint/common core`：
  - `task_group_id`
  - `supported/supporting relation`
  - `recovery_site_id`
  - `coordination_mode`
- `services/navy`：
  - `officer_in_tactical_command`
  - `warfare_role_code`
  - `task group / task unit` 级 tactical ownership
- 未来 `naval/` 专用层：
  - 舰艇/编队任务语义
  - 舰面回收、补给、站位、海上编队几何
  - naval execution command / reporting specialization

因此，runtime/standards bridge 在 Navy 方向上的首要工作，
应是把 core 骨架留给联合层，把海军组织与控制口径挂到 profile 层，
而不是把 air-specific command 词汇继续扩写成“通用 core”。
