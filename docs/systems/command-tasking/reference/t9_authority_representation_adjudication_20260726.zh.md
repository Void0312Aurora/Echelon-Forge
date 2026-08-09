# T9 权限表示裁定（2026-07-26）

语言：
- 英文规范版：[t9_authority_representation_adjudication_20260726.md](t9_authority_representation_adjudication_20260726.md)
- 中文伴随版：`t9_authority_representation_adjudication_20260726.zh.md`

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/systems/command-tasking/reference/t9_authority_representation_adjudication_20260726.md`
Owner: `systems/command-tasking/authority-boundary`
Last verified: `2026-08-08`
Verification boundary: 已复核所有者路径、生命周期、no-mapping 裁定与命名一致性
门禁路由；逐路径引证仍只对记录的基线负责。
基线提交：`dd292f4b`

状态：维护中的所有者本地裁定。本文源自已完成统一架构计划的 T9（Agency
与条令架构）裁定切片。I68 的
A3 默认值名称归属搬迁（[Agency 权限普查](agency_authority_census_20260721.zh.md)
§9）带出一处前提纠正：编译端 `authorize_maintained_*` 门作用于 `AgentRole` /
`AgentAuthorityScope` 的 **action-interface**（动作接口）权限表示，而非
`CommandRelationship` / `AuthorityScope` 的**梯级（echelon）**枚举。该纠正暴露出
一条从未逐路径裁定过的表示边界：是否存在任一维护面代码路径，把一种表示的取值
映射、流入另一种表示，或与之比较？本文对每条相关的已普查路径（A2、A4、A5、A6、
A13）及反方向（action-interface 侧）逐一裁定该边界，附源码指针，并用一条承重的
一致性门禁（`tests/architecture/agency/test_authority_representation_boundary.py`）
钉住各判定。

依据 T9 的关键风险约束（C2 语义是研究主题，其改动需领域证据评审而非仅对等性），
本切片实现**零 C2 行为改动**：只读代码、记录判定，并新增一条只读结构门禁。
不修改任何 profile、loader、runtime 或编译文件。

## 1. 两种表示

**梯级权限**——指挥节点之间的条令性指挥梯级关系，以编译 C++ 枚举表示，作为
任务指令数据被携带：

| 项 | 来源 |
|----|------|
| `enum class CommandRelationship`（`None`、`COCOM`、`OPCON`、`TACON`、`Support`、`ADCON`、`CoordinatingAuthority`、`DIRLAUTH`） | `src/components/tasking/common/core_tasking_enums.h:31-40` |
| `enum class AuthorityScope`（`Unspecified`、`Strategic`、`Operational`、`Tactical`、`Execution`） | `src/components/tasking/common/core_tasking_enums.h:42-48` |
| 携带字段 `TaskOrderCore::command_relationship` / `::authority_scope` | `src/components/tasking/common/task_order_core.h:15-16` |
| pybind 导出（枚举；`TaskOrderCore` / `TaskOrder` 字段） | `src/interfaces/python/bindings_command.cpp:150-165, 493-494, 627-628` |

**Action-interface 权限**——被维护的 Agent *可以经由哪个接口做什么*，以编译端
字符串作用域契约表示，由 WP12 授权门强制执行：

| 项 | 来源 |
|----|------|
| `struct AgentAuthorityScope`（`scope` 字符串 + `world_index` / `entity_ids` / `roster_id` / `command_family`） | `src/runtime/contracts/policy_contracts.h:278-285` |
| 作用域取值 `platform_control` / `mission_command` / `formation_coordination` | `src/runtime/contracts/policy_contracts.h:41-46, 187-191` |
| `struct AgentRole`（五元 schema；`authority_scope` 成员） | `src/runtime/contracts/policy_contracts.h:319-325` |
| 形状 / 兼容 / 授权谓词（`agent_authority_scope_has_required_shape`、`agent_role_action_interface_matches_authority_scope`、`authorize_maintained_action_intent`、`authorize_maintained_coordination_intent`） | `src/runtime/contracts/policy_contracts.h:339-360, 397-416, 454-503` |
| pybind 导出 | `src/interfaces/python/bindings_runtime.cpp:399-406, 441-452, 638-645` |

**编译面互斥（承重事实）。** 在 `src/**` 全域，`CommandRelationship::` /
`AuthorityScope::` 的编译端使用仅有：枚举定义本身、`TaskOrderCore` 的默认成员
初始化、以及 pybind 值导出——**没有任何编译端决策逻辑读取梯级取值**
（`rg 'CommandRelationship::|AuthorityScope::' src/` 穷尽为
`core_tasking_enums.h`、`task_order_core.h:15-16`、`bindings_command.cpp`）。
反之，action-interface 族的定义头文件（`policy_contracts.h`、
`information_transform_contracts.h`、`counterfactual_replay_contract_types.h:96`）
从不命名任何梯级类型。在编译面上，梯级枚举是纯粹的被携带数据；action-interface
表示是唯一的编译端授权决策面。

**术语同形词（记录在案，非映射）。** 两个拼写横跨边界，但不跨界传值：

- `mission_command` 同时是：action-interface 作用域字符串
  `kAgentAuthorityScopeMissionCommand`（`policy_contracts.h:43-44`）、载荷类型
  `kActionInterfacePayloadMissionCommand`（`policy_contracts.h:37`）、场景数据
  dict 键（`gym_envs/scenario_loader/loading.py:113-117`）、以及编译端
  `MissionCommand` DTO 名。同一拼写，四种含义；没有代码把其中之一作为*权限取值*
  转换为另一个。
- snake_case 属性 `authority_scope` 同时命名梯级字段
  （`TaskOrderCore::authority_scope`，一个 `AuthorityScope` 枚举）与
  action-interface 成员（`AgentRole::authority_scope`，一个
  `AgentAuthorityScope` 结构体）。二者值域互斥（枚举整数 vs 字符串作用域结构体）；
  相撞的只是属性拼写。因此一致性门禁用类型/枚举/成员名做判别，而不用这个属性拼写。

## 2. 方法

对每条 A2/A4/A5/A6/A13 路径，被裁定的问题是：*是否存在梯级权限取值
（`CommandRelationship` / `AuthorityScope` 成员或其访问拼写）流入
action-interface 权限值（`AgentRole` / `AgentAuthorityScope`、scope 字符串、或
`authorize_maintained_*` 调用），或与之比较*——任一方向？证据为对维护面的 `rg`
普查加上对每处相关定义/调用点的通读；判定选项为 `mapped(证据)` /
`no-mapping(证据)` / `ambiguous(准确的待决问题)`。反方向（运行时面的
action-interface 授权路径）以同一标准对梯级词汇裁定。

以下多行共用的全面否定证据：action-interface 标识符（`AgentRole`、
`AgentAuthorityScope`、`authorize_maintained_*`、`agent_role_*`、
`is_known_agent_authority_scope`、`platform_control`、`formation_coordination`、
`PilotActionAssignment`、`CommandChainAssignment`）在 `python/rl/tasking/**`、
`python/rl/profile/**`、`gym_envs/**` 下**出现次数为零**——唯一例外是普查外标量
`NAVAL_STATION3_CARRIER_INTERFACE_KIND = "PilotActionAssignment"`
（`gym_envs/universal_env_parts/naval_actions.py:24`），普查（§3.2 普查外注记）
已登记的舰站元数据常量，不触及任何梯级取值。

## 3. 判定矩阵

| 路径 | 站点 | 判定 | 证据 |
|------|------|------|------|
| A2 | `python/rl/tasking/common_core_profile.py` | **no-mapping** | 纯梯级面：字段->枚举强制映射（`:191-192`）、未设置字段默认化（`:219-222`、`:256-259`）、spec 强制写入 `TaskOrder.command_relationship` / `.authority_scope`（`:630-640`）、推断分派 + 默认（`:792-804`）。所有产出值均为写入任务指令字段的 `ef_py.CommandRelationship` / `ef_py.AuthorityScope` 成员。`python/rl/tasking/**` 全域无任何 action-interface 标识符（§2 否定证据）；没有路径把产出的枚举送入 `AgentRole` 或与 scope 字符串比较。 |
| A4 | `python/rl/profile/air_profile.py` | **no-mapping** | 梯级默认（`:188-189`、`:211-214`、`:237-240`）与开火权限字段解析（含 leader 优先仲裁，`:604-622`）写入 `MissionCommand` 交战字段（`engagement_authority_holder_id` / `_grantor_id` / `authorization_to_fire`）与任务指令梯级字段。`MissionCommand` **不携带**任何梯级字段（`src/components/command/common/mission_command_core.h`：`authorization_to_fire` 在 `:23`；不存在 `command_relationship` / `authority_scope` 成员），且该文件不命名任何 action-interface 标识符（§2）。 |
| A5 | `python/rl/profile/ground_profile.py` | **no-mapping** | `infer_command_relationship` 返回 `Support` 或默认（`:24-25`、`:156-170`）；梯级默认（`:233-234`、`:254-257`、`:287-297`）；leader-vs-mission 开火授权优先（`:428-431`）；OTC 兜底取名（`:462`）。所有取值均为梯级枚举或任务式指挥（mission-command）DTO 字段；无 action-interface 标识符（§2）。`:428-431` 的优先级仲裁的是两个*梯级侧*生产者（`leader_intent` vs `mission_cmd`），并非两种表示之间。 |
| A6 | `python/rl/profile/naval_profile.py` | **no-mapping** | 梯级默认（`:206-207`、`:223-226`、`:246-249`）；warfare-role / OTC 推断（`:273-292`）；交战权限与 ROE 字段填充及 mission-config 重读（`:425-458`、`:505-552`）。与 A4/A5 同形：仅 `NavalWarfareRole` / `CommandRelationship` / `AuthorityScope` 成员与 DTO 字段；无 action-interface 标识符（§2）。（普查 A6 关于 `loader.mission_cmd` 与 `scenario_data["mission_command"]` 重绑定的待决问题属*梯级侧内部*的别名问题，不触及本边界。） |
| A13 | `gym_envs/universal_env_parts/air_combat_event_action.py` | **no-mapping** | 典范“谁可开火”门经 `cmd_view` 读任务式指挥（mission-command）DTO 字段：`holder_id = cmd_view.int_field("engagement_authority_holder_id", 0)`；`holder_ok = holder_id <= 0 or holder_id == agent_id`；`c2_authorized = authorization_to_fire AND holder_ok`（`:167-169`）。`agent_id` 是环境层的 agent/实体身份，不是对 `AgentAuthorityScope.entity_ids` 的读取——该文件（乃至 `gym_envs/**` 全域，§2）不命名任何 action-interface 标识符。如实记录的毗邻性：`engagement_authority_holder_id` 与 `AgentAuthorityScope.entity_ids` 指称同一整数 id 空间中的实体，但没有任何共享代码路径、转换或比较连接二者。 |
| 反向 | `python/rl/runtime/world_batch/adapter.py` | **no-mapping** | 运行时面的 `AgentRole` 构造**仅**由动作载荷类型推导 `authority_scope.scope`（载荷为任务式指挥（mission command）则 `"mission_command"` 否则 `"platform_control"`，`:481-488`），并在同一代码块从窗口请求填充 id；授权调用（`:639-642`）传入该 role 与 intent。文件中不出现任何梯级标识符（`CommandRelationship` / `AuthorityScope` / 成员名 / `command_relationship`）。即使被授权的 intent 携带 `MissionCommand`，授权谓词也只读 role 形状、scope<->interface 兼容性、以及包的 `action_interface` 描述符 + `has_pilot_action` / `has_mission_command` 标志（`policy_contracts.h:418-436, 454-476`）——从不读任何载荷字段，无论梯级与否。 |
| 反向 | `python/rl/runtime/agent_shim.py` | **no-mapping** | Python 侧 `AgentRole` 草图（`:215` 起）及其 `authority_scope` 映射只使用 action-interface 键（`scope` / `world_index` / `entity_ids` / `roster_id` / `command_family`，`:259-272`）；文件中不出现任何梯级标识符。 |

**汇总：正向 5/5 路径、反向 2/2 路径均判定 no-mapping；mapped 为 0；
ambiguous 为 0。** 在今日的维护面上，两种权限表示完全互斥：梯级取值生灭于
任务指令（task-order）/ 任务式指挥（mission-command）DTO 一侧；
action-interface 取值生灭于运行时授权一侧；仅有的接触点是拼写同形词（§1）。

## 4. 本判定说了什么、没说什么

- 它**说了**：把 A2/A4-A6/A13 收敛到编译端 `authorize_maintained_*` 门
  （普查 §7 推迟的语义收敛）不可能是机械的重指向——不存在可拓宽的既有桥梁。
  未来的收敛切片必须*设计*一个映射（或裁定不应存在映射），这正是 T9 推迟的
  领域证据决策。
- 它**没说**两种表示在*条令上*无关。梯级状态（如 `Tactical` 作用域下的
  `TACON`）是否*应当*蕴含 action-interface 授权（如对某编组的 `mission_command`
  作用域），是本切片刻意不裁决的 C2 设计问题。判定只关乎代码今日的行为，
  门禁钉住的是映射不能被悄悄引入。
- 注册表说明：`python/tasking_contracts/agency_registry.py` 并列声明两族词汇
  （梯级镜像 `COMMAND_RELATIONSHIPS` / `AUTHORITY_SCOPE_LEVELS`；
  action-interface 镜像 `ACTION_INTERFACE_SCOPES` / `ACTION_INTERFACE_KINDS` /
  `COMPILED_AUTHORIZATION_GATES`）。在冻结、无消费者的注册表里并列声明是
  文档记录，不是映射；注册表未把任一族映射到另一族。

## 5. 领域评审记录

**如实状态：本文是统一架构计划工作线（本轮迭代）完成的代码证据裁定。尚无任何
人类 C2 领域专家评审或签署这些判定。** 各判定是关于代码行为的结构性断言——
代码证据能够裁决的那类断言——且每行都可由所引行号证伪。代码证据无法裁决、
需人类领域评审者在任何映射切片落地前裁定的问题：

1. 梯级->action-interface 映射是否应当存在（例如对某单位持有 `TACON` /
   `Tactical` 是否在条令上蕴含对其的 `mission_command` action-interface
   权限），还是两种表示有意正交（梯级 = 指挥节点条令，action-interface =
   执行 Agent 能力）？
2. 若映射应当存在，归哪一侧所有（编译契约 vs Python 归一化层）？普查 A 路径中
   哪些必须经由它？
3. A13 的身份毗邻性（holder id 与 `entity_ids` 共享同一 id 空间）是
   “谁可开火”最终应查询 `AgentAuthorityScope.entity_ids` 的潜在需求，还是
   id 分配的巧合？

签署状态：`pending human domain review`（待评审发生时在此记录评审人、日期与
判定增量；在此之前，no-mapping 门禁钉住现状）。

### 5.1 签核记录（2026-07-27，受所有者委托代签）

**本记录的性质（诚实约束）。** 本记录是一次**受所有者委托的 Agent 代签裁定**：
仓库所有者（唯一维护者）已明确授权代表其记录本签核（“允许代签”，2026-07-27）。
它**不是**独立的人类 C2 领域专家评审，也绝不得被引用为后者。三个 §5 问题在
记录之前均已实质性裁定——对照所引代码路径、普查记录与仓库的 C2/条令前瞻
文档——每项判定列出所查证据。

**问题 1——梯级->action-interface 映射是否应当存在：不存在隐式映射；
no-mapping 判定作为维护契约成立。** 在本计划的条令模型中，于 `Tactical`
作用域持有 `TACON` 并不隐式蕴含 `mission_command` action-interface 权限：

- 仓库自身的条令参考把 C2 界定为围绕权限委派展开、且委派必须**显式**的
  任务式指挥问题（`docs/domains/joint/service_profiles/domains/air_force_profile.md`——AFDP 3-0.1 以
  指挥官为中心的职能与*显式权限委派*）；`docs/systems/command-tasking/work/issues/`（指挥链路
  路线图、操作层）中没有任何内容从梯级注记推导执行 Agent 能力。
- 梯级默认值是无处不在的被携带数据：A3 把**每一份**归一化任务指令默认为
  `TACON`/`Tactical`（普查 §9），且没有任何编译端决策逻辑读取梯级取值
  （§1）。若存在隐式蕴含，则默认情况下几乎每个 Agent 都会获得
  `mission_command` 接口权限——这将瓦解被携带的指挥节点条令数据与被强制
  执行的执行 Agent 能力之间的刻意区分。
- 因此两种表示被维护为**有意正交**（梯级 = 指挥节点条令注记；
  action-interface = 执行 Agent 能力契约）。任何未来映射必须以**显式注册
  结构**（G5“扩展即注册”）经由专门的领域证据切片到来——绝不得按名称
  相似引入（迭代队列 §5 红线）。

**问题 2——若引入映射归哪一侧所有：在问题 1 判定下悬置（moot）；注册表被
预先指定为声明所有者。** 若未来某个领域证据切片确要引入映射，
`python/tasking_contracts/agency_registry.py` 被预先指定为其声明所有者：
它已经是权限词汇的唯一声明式所有者，也是两族词汇唯一并列之处
（`CATEGORY_SCOPE` 在 `agency_registry.py:604` 共声明
`AUTHORITY_SCOPE_LEVELS + ACTION_INTERFACE_SCOPES`——已披露的共声明，非
映射），其 G5 纪律（冻结声明加漂移钉门禁）正是此类映射所需的形态。哪些
A 路径须经由它，留给该未来切片。

**问题 3——A13 身份毗邻性：id 分配的巧合，由门禁监控；不是潜在需求。**
`engagement_authority_holder_id` 与 `AgentAuthorityScope.entity_ids` 共享
同一整数 id 空间，是因为二者都指称世界实体、而所有实体引用都使用该空间——
共享值域是实体身份的固有属性，不是设计关联的证据。两个检查回答的是不同
问题（某实体按任务式指挥持有的交战权限 vs 某 Agent 对实体的接口能力）；
不存在任何交叉读取、转换或比较（§3 A13 行），且已落地的边界门禁
（`tests/architecture/agency/test_authority_representation_boundary.py`）会
使未来的交叉读取转红：在被钉文件内获取 action-interface 取值必须命名至少
一个判别标识符（`AgentRole` / `AgentAuthorityScope` /
`authorize_maintained_*`），而这正被门禁捕获。状态：**monitored-by-gate
（门禁监控中）**。若“谁可开火”未来被重设计为查询
`AgentAuthorityScope.entity_ids`，那属于问题 1 类的映射，须走同样的显式
注册路径。

**队列后果。** no-mapping 签核后，已排期的 T9 行为切片 **I86 按其自身行
逻辑以 held 关闭**（I72+ 迭代队列
`iteration_queue_i72_plus_20260726.zh.md`：“若 I77 结论为无映射，I86 改以
held 关闭”）。

签署状态：`adjudicated — owner-delegated（2026-07-27）`；上方的 pending 行
保留为已落地历史，本记录即其所要求的登记条目——但如实注明委托性质，而非
人类领域专家身份。

签核行：“Owner-delegated agent adjudication under explicit owner
authorization (2026-07-27); recorded by the unified architecture program
workline.”（受所有者明确授权的代签 Agent 裁定（2026-07-27）；由统一架构
计划工作线记录。）

## 6. 一致性门禁

`tests/architecture/agency/test_authority_representation_boundary.py` 使
no-mapping 判定成为承重结构：

1. **正向钉。** 每个 A2/A4/A5/A6/A13 文件的可执行代码面（剥离
   docstring/注释，丢弃 import/`__all__` 转口管道——复用普查门禁的扫描器，
   使两门对“代码”的定义一致；保留字符串字面量，因为 scope 取值以字面量形式
   travel）不得含任何 action-interface 判别符（`AgentRole`、
   `AgentAuthorityScope`、`AgentRoleAuthorizationResult`、
   `authorize_maintained_*`、`agent_role_*`、`is_known_agent_authority_scope`、
   `platform_control`、`formation_coordination`、`PilotActionAssignment`、
   `CommandChainAssignment`），按词边界匹配。
2. **反向钉。** `adapter.py` / `agent_shim.py` 不得含任何梯级判别符
   （`CommandRelationship`、`AuthorityScope`、`COCOM`、`OPCON`、`TACON`、
   `ADCON`、`DIRLAUTH`、`CoordinatingAuthority`、`command_relationship`、
   `infer_command_relationship`）。
3. **编译面互斥钉。** 每族定义头文件（剥注释后）不得命名另一族的类型；
   一条词边界回归测试证明 `AuthorityScope` 不会在 `AgentAuthorityScope` 内
   误触发。
4. **本族哨兵标记。** 每个被钉文件仍须携带*本族*标记，使被掏空或改作他用的
   文件响亮失败，而非让“不含对方”检查空洞通过。
5. **篡改自测。** 向 profile 注入 `ef_py.AgentRole()` + `"platform_control"`、
   向 adapter 注入 `ef_py.CommandRelationship.TACON`、以及一段合成的跨族比较
   均被检出；docstring/注释提及不构成误报。已用磁盘实测验证（向
   `ground_profile.py` 追加 `"platform_control"` 字面量使门禁转红，随后还原）。

同形词边界（刻意为之）：`mission_command` 与 snake_case 属性 `authority_scope`
不在判别符集合内（§1），故门禁不会误标其合法同形用法；若映射*只*借这些拼写
走私，则它要产生任何效果就必须命名至少一个真实的类型、成员或门标识符，而这些
正被判别符捕获。

该门禁已注册进 `tests/smoke/ci_smoke_suite.json`（实测成本：整个 agency 门禁
目录含本模块在三秒内跑完）。

## 7. 推迟 / 搁置

- **设计任何梯级<->action-interface 映射**（或正式裁定不应存在映射）——留给
  带领域证据评审的 T9 语义切片（§5 各问题）。本文只证明今日不存在映射。
- **普查 §7 的 A1-A14 语义收敛**——不变，继续推迟；本裁定收窄了其设计空间
  （§4）但未收敛任何东西。
- **A6 mission_cmd 别名待决问题**——不变（梯级侧内部；见普查 §3.2 A6 行）。

## 相关

- 历史来源：已完成统一架构计划的 T9 裁定；当前权威见下方仿真系统架构标准。
- [Agency 权限普查（2026-07-21）](agency_authority_census_20260721.zh.md)
  （A 路径登记；本裁定完成其 §9 的 I68 前提纠正）
- [仿真系统架构设计](../../../architecture/standards/simulation_system_architecture_design.zh.md)
  （Agency 面；AgentRole 五元 schema）
- `python/tasking_contracts/agency_registry.py`（两族词汇的声明式所有者）
- `tests/architecture/agency/test_authority_representation_boundary.py`
  （本裁定的一致性门禁）
- `tests/architecture/agency/test_authority_registry_gate.py`（普查 ratchet 门禁）
