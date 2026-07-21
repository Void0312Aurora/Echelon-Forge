# Agency 权限普查（2026-07-21）

语言：
- 英文规范版：[agency_authority_census_20260721.md](agency_authority_census_20260721.md)
- 中文伴随版：`agency_authority_census_20260721.zh.md`

文档类型：`reference`
生命周期：`maintained`
规范路径：`docs/plan/unified_architecture_program/agency_authority_census_20260721.md`
所有者：`unified architecture program workline`
最近核验：`2026-07-21`
基线提交：`8bd21d86`

状态：[统一架构计划](README.zh.md)的 T9（Agency 与条令架构）第一切片普查。
本文档是描述性普查登记（`reference` 参考记录），非独立评审：它枚举维护面上
散落的权限检查（“谁可指挥谁 / 谁可开火 / 谁可写什么”）站点，将每处归入一个或
多个权限维度，并记录钉住这些站点的注册式词汇与 ratchet 门禁。依据 T9 的关键
风险约束（C2 语义是研究主题，其改动需领域证据评审而非仅对等性），本切片实现
**零 C2 行为改动**：只产出普查、单一声明式词汇所有者与 ratchet 门禁；把散点
调用点收敛到词汇上的工作，留给后续带领域证据评审的切片。

本文为第一切片普查的**第二修复轮**（独立评审结论：needs-repair，两次）。第一轮
(1) 补全词汇对编译权威的镜像，(2) 重裁若干被“探测词→固定类别”刚性映射扭曲的站点
归类，(3) 堵住 ratchet 盲区。第二轮 (4) 让编译头提取器免受注释欺骗（提取枚举/scope
前先做引号感知的 C++ 注释剥离，故注释掉的“ghost”成员或块注释中的 `}` 不再能欺骗
它），(5) 在**词边界**匹配下真正 token 化同义词族，使扫描器咬住只用派生拼写的文件，
(6) 依源码证据将 A14 由 `arbitration` 重裁为 `gating`，(7) 对关键重裁站点钉死其
*精确*类别集。逐项改动在下文就地标注，并在 §8 汇总。

## 1. 范围与方法

维护权限面用 `rg` 普查了 `python/tasking_contracts/**`、`python/rl/tasking/**`、
`python/rl/profile/**` 以及与 C2/ROE 相关的 `gym_envs/**` 模块；`src/**` 仅只读
普查其编译权限契约。一处站点被计为权限检查散点的条件是：它裁决、委派、仲裁或
门控 *谁可指挥谁* 或 *谁可写哪个指令/ROE 字段*——区别于纯 DTO 字段搬运。

每处站点以逐文件的**探测词→出现次数**映射作指纹，探测词是一组稳定的、有辨识度
的权限标识符/短语，按**词边界**（`\bTOKEN\b`）匹配，故某 token 绝不会在更长的
标识符内部重复计数。已存在探测词的第二处出现会改变计数，从而使指纹漂移。词边界
匹配（第二轮）正是让此前未 token 化的同义词族得以无冲突 token 化的关键：裸
`commander_id` 局部（区别于 `ground_commander_id`）、snake_case 的
`command_relationship` 访问、`infer_command_relationship` 推断函数，以及 loader 委托
拼写 `_hierarchical_command_chain_active` 现均为一级 token，故只以派生拼写承载权限
逻辑的文件会被咬住而非漏过 ratchet。扫描器对 `code` 面探测词只在可执行代码中匹配
——先剥离注释、docstring 与 `import`/`__all__` 再导出壳，因此无辜 docstring 提及或
纯再导出不会误报——对 `prose` 面民俗短语只在 docstring/注释中匹配（这类约定本就存
于此）。

每处站点归入六个权限维度中的一个或多个（`role`、`scope`、`delegation`、
`arbitration`、`gating`、`doctrine`），另设 `undecided`（待裁定）桶用于语义尚未
裁定的站点。每个探测词在
`python/tasking_contracts/agency_registry.py:AUTHORITY_TOKEN_CATEGORIES` 中映射到
一个**候选类别集合**（而非单一固定类别）；站点声明的类别必须*落地*于（为其子集）
且*覆盖*（触及每一个）其钉住探测词的候选类别。逐文件指纹钉在
`tests/architecture/fixtures/agency_authority_census_20260721.json`。

编译权限模型已作为参照目标存在：WP12 的 `AgentRole` /
`authorize_maintained_action_intent` / `authorize_maintained_coordination_intent`
契约位于 `src/runtime/contracts/policy_contracts.h` 与
`src/runtime/contracts/information_transform_contracts.h`，由
`tests/architecture/policy_execution/*` 门禁。Python 维护面尚未收敛到它，这项
收敛正是 T9 后续的工作。

## 2. 权限词汇（真源）

注册式词汇与架构权威（[仿真系统架构设计](../architecture/simulation_system_architecture_design.zh.md)
Agency 面）及编译契约对齐。ratchet 门禁解析枚举/scope 头文件，并对下述镜像与
编译值之间的任何漂移判红。以下均非自造。

- **AgentRole 五元 schema**（`simulation_system_architecture_design`）：
  `role`、`authority_scope`、`information_state_source`、`decision_model_ref`、
  `action_interface`。每个声明角色现携带全部五槽（见 §5）。
- **`AuthorityScope`**（`src/components/tasking/common/core_tasking_enums.h`）：
  `Unspecified`、`Strategic`、`Operational`、`Tactical`、`Execution`。
- **动作接口 scope**（`src/runtime/contracts/policy_contracts.h` 的
  `kAgentAuthorityScope*` / `is_known_agent_authority_scope`）：`platform_control`、
  `mission_command`、`formation_coordination`。（修复：首轮镜像缺 `mission_command`，
  现已补回。）
- **动作接口 kind**（`policy_contracts.h` 的
  `is_known_agent_action_interface_kind`）：`PilotActionAssignment`、
  `CommandChainAssignment`。
- **`CommandRelationship`**（`core_tasking_enums.h`）：`None`、`COCOM`、`OPCON`、
  `TACON`、`Support`、`ADCON`、`CoordinatingAuthority`、`DIRLAUTH`。
- **`CoordinationMode`**（`core_tasking_enums.h`）：`Unspecified`、`Independent`、
  `Attached`、`Follow`、`Support`、`Screen`、`Rejoin`、`Recover`、`Detached`。
- **`NavalWarfareRole`**（`src/components/domains/naval/tasking/naval_tasking_enums.h`）：
  `Unspecified`、`ScreenCommander`、`SurfaceActionCommander`、`AirDefenseCommander`、
  `SeaControlCommander`、`LogisticsCoordinator`。（修复：六项——含 `Unspecified`——
  现已按头文件全部声明。）
- **`merge_policy` 仲裁**（`simulation_system_architecture_design`）：
  `last_write_wins`、`priority_override`、`reject_on_conflict`、`merge_by_field`、
  `append_only`；来源优先级 `human > policy > scripted > diagnostic`
  （出处：`simulation_system_architecture_design`，Agency 面跨层合并/仲裁规则）。
- **使能/禁用门（`gating`）**：命令链激活门 `hierarchical_command_chain_active`
  （loader 委托拼写 `_hierarchical_command_chain_active`），判定 leader/命令链权限
  路径是否运行（A7/A9）；以及空战开火资格掩码
  `_air_combat_c2_roe_policy_fire_mask_open`（A14），判定策略*是否可开火*。两者皆为
  使能/禁用门，都不读 holder id 来选出胜者；此维度区别于 `arbitration`（多源竞争的
  冲突解决）。（第二轮：新增开火资格门作为第二个 gating 族。）
- **`DoctrineFamily`**（`simulation_system_architecture_design` 领域扩展模型）：
  任务模板、ROE、权限委派、交战策略——本切片仅声明为词汇占位（无机制）。

## 3. 权限散点登记表

下表钉住每处维护门禁站点。`类别`为该站点裁定的权限维度（落地于并覆盖其探测词
候选类别）。`形态`记录检查当前的形状。逐文件探测词→出现次数指纹存于普查 JSON。

| # | 位置 | 探测词 | 类别 | 形态 | 语义 |
|---|------|--------|------|------|------|
| A1 | `python/rl/tasking/leader_tasking.py` | `allowed to directly author`（prose） | scope | 文档约定 | `ScriptedC2TaskManager` 民俗：C2 可消费态势+报告，但不得直接编写底层任务指令（leader 层权限）。 |
| A2 | `python/rl/tasking/common_core_profile.py` | `AuthorityScope`、`CommandRelationship`、`NavalWarfareRole`、`command_relationship`、`commander_id`、`ground_commander_id`、`infer_command_relationship`、`officer_in_tactical_command`、`warfare_role_code` | delegation, role, scope | 默认推断 | 跨 profile 权限默认：指挥关系+权限范围、OTC 委派、海军作战角色、地面/`commander_id` 角色、`infer_command_relationship` 分派。仅默认/身份推断，无冲突解决。**第二轮：钉住 snake_case/`commander_id`/`infer_` 同义词。** |
| A3 | `python/rl/profile/common_core_defaults.py` | `AuthorityScope`、`CommandRelationship` | delegation, scope | 默认提供 | 委派/范围枚举的叶子默认值提供者。（其 `command_relationship_default()` 函数名按词边界为复合排除；由 `CommandRelationship` 钉住。） |
| A4 | `python/rl/profile/air_profile.py` | `AuthorityScope`、`CommandRelationship`、`authorization_to_fire`、`command_relationship`、`engagement_authority_grantor_id`、`engagement_authority_holder_id`、`roe_state` | arbitration, delegation, doctrine, scope | 默认+优先级 | 空军默认 + 交战权限字段解析 + **leader 意图压过任务指令的开火权限优先级**。（`leader_authorization_to_fire` 局部按词边界排除；文件由裸字段钉住。） |
| A5 | `python/rl/profile/ground_profile.py` | `AuthorityScope`、`CommandRelationship`、`authorization_to_fire`、`command_relationship`、`ground_commander_id`、`infer_command_relationship`、`officer_in_tactical_command` | arbitration, delegation, role, scope | 默认+委派+优先级 | 地面默认 + OTC/地面指挥官委派 + **leader 意图 vs 任务指令的开火授权优先级**（`build_kernel_mission_command`，行 428-431）。**第一轮：补 arbitration**；**第二轮：钉住 `command_relationship`/`infer_command_relationship` 同义词并精确钉死类别集。** |
| A6 | `python/rl/profile/naval_profile.py` | `AuthorityScope`、`CommandRelationship`、`NavalWarfareRole`、`authorization_to_fire`、`command_relationship`、`engagement_authority_grantor_id`、`engagement_authority_holder_id`、`officer_in_tactical_command`、`roe_state`、`warfare_role_code` | arbitration, delegation, doctrine, role, scope | 默认+委派+优先级 | 单文件最密集面：作战角色、OTC、指挥关系、ROE、交战/开火权限 + leader 优先级。**第二轮：钉住 snake_case `command_relationship` token。** |
| A7 | `gym_envs/scenario_loader/core.py` | `_hierarchical_command_chain_active` | gating | 委托方法 | loader 对命令链**激活**门（使能/禁用）的委托。**第一轮：arbitration → gating**；**第二轮：以 loader 委托 token `_hierarchical_command_chain_active` 钉住**（词边界匹配不再把门名折进带下划线前缀的方法），并精确钉死类别集。 |
| A8 | `gym_envs/scenario_loader/runtime_state.py` | `authorization_to_fire`、`engagement_authority_grantor_id`、`engagement_authority_holder_id`、`ground_commander_id`、`roe_state` | delegation, doctrine, role | 状态投影 | 纯状态镜像：将任务指令权限/ROE 与地面指挥官字段投影进 runtime-state JSON 镜像；不作任何裁决。**第一轮：去掉 arbitration**（是镜像而非门；此处 `engagement_authority_holder_id` 为镜像身份）；**第二轮：精确钉死类别集**以防 arbitration 被静默加回。 |
| A9 | `gym_envs/scenario_loader/behavior_runtime/command_chain.py` | `hierarchical_command_chain_active` | gating | 激活门 | 命令链**激活**门的**定义站点**（依 task_order/leader_intent/pilot_report/c2_task_name 是否存在）。**第一轮：arbitration → gating**；**第二轮：精确钉死类别集**。 |
| A10 | `gym_envs/scenario_loader/behavior_runtime/post_waypoint_transition.py` | `authorization_to_fire` | delegation | 字段拷贝 | 在过渡时把开火权限委派传播到 `leader_intent`。 |
| A11 | `gym_envs/scenario_loader/reward_runtime/air_combat.py` | `authorization_to_fire`、`roe_state` | delegation, doctrine | 奖励门 | ROE `authorized_candidate` 门，条件化开火前奖励项（读取者，不编写指令）。 |
| A12 | `gym_envs/scenario_loader/reward_runtime/naval.py` | `authorization_to_fire`、`roe_state` | delegation, doctrine | 奖励门 | 开火前 ROE-hold 奖励 vs 授权惩罚门（读取者，不编写指令）。 |
| A13 | `gym_envs/universal_env_parts/air_combat_event_action.py` | `authorization_to_fire`、`engagement_authority_holder_id` | arbitration, delegation | 开火权限门 | **典范目标**：`holder_ok = (holder_id <= 0 或 == agent_id)`；`c2_authorized = authorization_to_fire 且 holder_ok`。谁可开火在调用点作为民俗存在。 |
| A14 | `gym_envs/scenario_loader/mission_observation.py` | `authorization_to_fire`、`engagement_authority_grantor_id`、`engagement_authority_holder_id`、`roe_state` | delegation, doctrine, gating | 观测投影+开火掩码 | 将 C2/ROE 权限字段投影进 `air_combat_c2_roe` 观测**并计算 `_air_combat_c2_roe_policy_fire_mask_open` 资格门**（`authorization_to_fire 且 wcs_state != 1 且 非 engage_hold 且 shot_policy_state > 0 且 shot_budget_remaining > 0 且 非 pending_assessment 且 target_contact_present`，行 281-300）。**第二轮（P1-3）：arbitration → gating**——掩码读 `authorization_to_fire`（+ wcs/engage/shot 状态）却**不**读 holder/grantor id（纯投影，行 405-406），故不解决谁可开火竞争（那是 A13 的职责）；类别集已精确钉定。**写排除**（I45 观测面）；只读普查。 |

### 3.1 交叉引用站点与扫描范围边界（不由 T9 门禁）

以下站点承载权限逻辑，但位于 T9 门禁扫描根之外；为完整性登记，刻意不作 ratchet
（修复：首轮 `### 2.1` 误编号已更正为 `### 3.1`）。

| # | 位置 | 语义 |
|---|------|------|
| R1 | `python/rl/runtime/world_batch/cooperative_director.py` | runtime/观测面：世界级 `is_leader` 角色/领队仲裁与编队角色元数据赋值。 |
| R2 | `python/rl/runtime/world_batch/adapter.py` | runtime/观测面：在 facade 指令路径上设置 `authorization_to_fire`。 |

其余刻意排除在外的面（登记以防该处新增权限文件被静默漏掉，并陈述统一口径）：

- **策略网络/算法面**（`python/rl/policy_algo/**`）：`policies.py`、
  `hmoe_routing.py`、`first_event_projection.py`、`_first_event_mixin.py` 将
  `authorization_to_fire` 任务列作为神经网络输入读取。它们是该权限字段的*消费者*，
  非 tasking 权限决策/委派/仲裁站点，故排除在 T9 扫描根之外。
- **再导出壳（统一口径）**：纯 `import` + `__all__` 再导出不是权限站点。
  `gym_envs/scenario_loader/behavior_runtime/__init__.py`（再导出
  `hierarchical_command_chain_active`）与 `python/rl/tasking/ground_adapter.py`
  （再导出 `infer_command_relationship`）同等处理——扫描器剥离 `import`/`__all__`
  语句，两者都不计入。权限逻辑钉在其定义/委托站点（A9 / A2）。（修复：首轮把
  `__init__.py` 再导出计入却未计 `ground_adapter.py`；现二者一致排除。）

## 4. 类别分布

| 类别 | 文件数 | 说明 |
|------|--------|------|
| scope | 6（A1-A6） | 权限梯次 + C2 读写范围民俗。 |
| role | 4（A2、A5、A6、A8） | 指挥节点身份（OTC、地面/`commander_id`、海军作战角色）。 |
| delegation | 11（A2-A6、A8、A10-A14） | 指挥关系（含 snake_case / `infer_` 同义词）、OTC/授予者转移、开火权限委派。 |
| arbitration | 4（A4、A5、A6、A13） | leader 压过任务指令的优先级 + 谁可开火 holder 门。（**第二轮**：A14 移出——其开火掩码是门而非冲突解决。） |
| gating | 3（A7、A9、A14） | 命令链激活（A7/A9）+ 空战开火资格掩码（A14）。 |
| doctrine | 6（A4、A6、A8、A11、A12、A14） | ROE-state / 武器控制模式字段。 |
| undecided | 0 | 本切片无未裁定站点。 |

门禁站点合计：14 个文件。交叉引用 / 范围外：R1、R2（runtime 面）加策略网络面
（`python/rl/policy_algo/**`）。

## 5. 注册式词汇设计

`python/tasking_contracts/agency_registry.py` 是权限词汇的单一声明式所有者
（G5“扩展即注册”）。它纯 stdlib、冻结、既不导入 `ef_py` 也不导入
`python.rl`/`gym_envs`，不接线任何东西，本切片不被任何运行时路径消费。

- `AGENT_ROLE_SCHEMA_FIELDS`——SCAL 五元 AgentRole schema 键序。
- `AUTHORITY_ROLES`——九个声明角色（autopilot_controller、flight_lead、
  scripted_c2、cooperative_director、officer_in_tactical_command、
  ground_commander、naval_warfare_commander、formation_member、
  engagement_authority_holder），各**现携带五元 schema**（`role`、
  `authority_scope`、`information_state_source`、`decision_model_ref`、
  `action_interface`）。取值按普查证据如实填；仅当站点是指挥节点身份/委派持有者
  而非编译式决策模型承载代理时，某槽标 `"unspecified"` 并注明（如 OTC、
  地面/海军指挥官、编队成员、交战持有者）。四个决策模型承载角色为：
  autopilot_controller（`platform_control` / `external_policy` /
  `PilotActionAssignment`）、flight_lead（`mission_command` / `rule_based` /
  `CommandChainAssignment`）、scripted_c2（`rule_based`；scope/interface 为
  `unspecified`，因 C2 任务状态层无编译动作接口且民俗禁止编写底层任务指令）、
  cooperative_director（`formation_coordination` / `CommandChainAssignment`；决策
  模型 `unspecified`，runtime 面拥有）。
- `AUTHORITY_SCOPE_LEVELS` + `ACTION_INTERFACE_SCOPES` + `ACTION_INTERFACE_KINDS`
  + `SCOPE_FOLKLORE_RULES`。
- `COMMAND_RELATIONSHIPS` + `COORDINATION_MODES` + `NAVAL_WARFARE_ROLES` +
  `DELEGATION_CARRIERS`。
- `MERGE_POLICIES` + `SOURCE_PRIORITY_ORDER` + `ARBITRATION_MECHANISMS` +
  `ACTIVATION_GATES` + `FIRE_ELIGIBILITY_GATES`（第二轮：空战开火掩码，使 `gating`
  维度的声明词汇覆盖 A14）+ `COMPILED_AUTHORIZATION_GATES`（可收敛到的编译式
  fail-closed 门）。
- `DOCTRINE_FAMILY`——`DoctrineFamilyPlaceholder`，命名该 family 及其组件
  （task_templates、roe、authority_delegation、engagement_policy）加既有 ROE
  模式字段（`roe_state`、`wcs_state`、`shot_policy_state`、`engage_order_state`、
  `authorization_to_fire`、`engagement_authority_holder_id`、
  `engagement_authority_grantor_id`）。状态：`vocabulary_placeholder`——本切片
  无机制。
- `AUTHORITY_TOKEN_CATEGORIES`（探测词 → 候选类别*集合*；第二轮新增同义词 token
  `commander_id` / `command_relationship` / `infer_command_relationship` 与 loader
  委托 `_hierarchical_command_chain_active`，并为 `authorization_to_fire` 的候选补入
  `gating` 以落地 A14 开火掩码）、`AUTHORITY_TOKEN_SURFACE`（探测词 → `code`/`prose`
  扫描面）与 `CATEGORY_VOCABULARY`（逐类别声明术语集）。

## 6. Ratchet 门禁设计

`tests/architecture/agency/test_authority_registry_gate.py` 遵循 I38
include-direction 允许清单先例（只减不增、大声失败），强制五件事：

1. **注册表 ↔ 普查一致性（候选集合模型）。** 每个普查文件声明的类别*落地*于
   （为其子集）且*覆盖*（触及每一个）其钉住探测词的候选类别；普查中出现的每个
   类别在注册表都有非空声明词汇；AgentRole 五元 schema 与 DoctrineFamily 占位
   如期声明。（修复：替换扭曲了 A5/A7/A8/A9 归类的“探测词→固定类别”刚性推导。）
2. **编译权威镜像。** 门禁解析 `core_tasking_enums.h`、`naval_tasking_enums.h`、
   `policy_contracts.h`（提取枚举成员与 `kAgentAuthorityScope*`），断言注册表镜像
   逐字复现 `CommandRelationship`、`AuthorityScope`、`CoordinationMode`、
   `NavalWarfareRole` 与动作接口 scope。头文件或镜像任一漂移即判红。（第一轮：新增，
   覆盖 P1-1。**第二轮**：提取器现在提取前先*引号感知*地剥离整个头文件的 C++ 注释，
   故注释掉的“ghost”成员与块注释中的 `}` 不再能欺骗它——字符串字面量 scope 如
   `kAgentAuthorityScope* = "..."` 因剥离器保留引号内内容而安然无恙。）
3. **指纹钉定（探测词 → 出现次数，词边界）。** 每个钉住文件必须仍复现其精确探测词
   *计数*；某文件被增删探测词——包括已存在探测词的*第二处*出现——都会令门禁变红，
   直到普查更新。探测词按**词边界**（`\bTOKEN\b`）匹配，故某 token 绝不会在更长
   标识符内部重复计数（`commander_id` 在 `ground_commander_id` 内）。（第一轮：从
   仅记 token 集合升级；取舍——相较“内容哈希 + token 集合”，token→count 对“同 token
   第二处权限检查”盲区更精准且对无关排版/注释改动稳定，而内容哈希会因任何空白改动
   抖动。**第二轮**：词边界匹配既修复子串重复计数，又解锁同义词族的 token 化。）
4. **对新散点的 ratchet。** 维护权限面扫描（目录递归扫描，故所属面内的新文件无法
   隐藏）不得含普查之外的文件；新的未登记权限检查站点会令门禁变红，须通过接入
   注册表或补一条署名普查项来解决。扫描器对 `code` 面探测词剥离注释、docstring 与
   `import`/`__all__` 壳，对 `prose` 民俗只在 docstring/注释中匹配。（第二轮：同义词
   token `commander_id` / `command_relationship` / `infer_command_relationship` 与
   loader 委托 `_hierarchical_command_chain_active` 闭合派生拼写盲区。）
5. **关键重裁站点的精确类别钉定（第二轮，NB）。** 普通站点保留候选集合模型
   （落地 + 覆盖）以避免过度僵化，但本次评审重裁的站点——A5（保留 arbitration）、
   A7/A9（gating）、A8（去 arbitration）、A14（gating）——钉死其*精确*类别集，故任何
   静默重翻（删 A5 arbitration、给 A8 加回 arbitration、把 A7/A9 移出 gating、把 A14
   翻回 arbitration）都会令门禁变红，而非在子集自由度下蒙混过关。

负向自证证明门禁会咬住而非空过：
`test_gate_flags_an_injected_unregistered_scatter`（注入 token 文件被标记）、
`test_scanner_counts_repeated_tokens_in_the_same_file`（第二处出现使指纹漂移）、
`test_scanner_ignores_docstring_and_comment_mentions`（无辜 docstring 提及不误报）、
`test_scanner_ignores_reexport_import_plumbing`（纯再导出不计入，统一
`__init__.py`/`ground_adapter.py` 口径）、
`test_scanner_matches_prose_folklore_only_in_docstrings`（民俗仍在 prose 面被捕获）、
`test_enum_extractor_detects_registry_drift`（权威镜像提取器还原成员并检出被删成员），
以及第二轮新增：`test_enum_extractor_ignores_commented_ghost_members`（注释掉的
ghost 成员——`//` 或 `/* */`——不被还原）、
`test_enum_extractor_survives_brace_in_block_comment`（块注释中的 `}` 不截断枚举体）、
`test_comment_stripper_preserves_string_literal_comment_markers`（引号感知剥离保留
字符串字面量 scope）、`test_scanner_detects_synonym_only_file`（仅用 `commander_id` /
`command_relationship` 的文件被检测且未登记则标记）、
`test_scanner_word_boundary_excludes_substring`（`commander_id` 不命中
`ground_commander_id` 内部）、`test_key_readjudicated_sites_pin_exact_categories`
（关键站点钉死其精确类别集）、`test_pinned_key_site_check_bites_on_reflip`
（重翻 A5/A8/A14/A7 会破坏钉定）。

## 7. 推迟 / 暂缓

- **调用点收敛**（把 A1-A14 接入注册表 / 编译式 `authorize_maintained_*` 门）
  推迟到后续带领域证据评审的 T9 切片。本切片仅普查 + 词汇 + 门禁。
- **`DoctrineFamily` 机制**（真正的 ROE/交战策略行为）暂缓；只声明名字与词汇。
- **runtime 面站点 R1-R2** 与**策略网络面**（`python/rl/policy_algo/**`）由其他面
  拥有；T9 协调而非修改它们，并保持其排除在扫描根之外（登记边界）。
- **探测词覆盖边界。** 扫描器以**词边界**匹配注册探测词表。第二轮已将此前“登记但
  未 token 化”的同义词（`commander_id`、`command_relationship`、
  `infer_command_relationship`）与 loader 委托拼写（`_hierarchical_command_chain_active`）
  提升为一级 token，故评审否决的那个缺口已闭合。剩余的如实边界是那些内嵌基础 token
  但刻意不单独 token 化的**复合**标识符（因其文件已由基础 token 钉住）：
  `leader_authorization_to_fire`（空军）、`infer_warfare_role_code`（海军）、
  `command_relationship_default` / `_command_relationship_default` /
  `_support_command_relationship`，以及 `_hierarchical_command_chain_active_impl`
  导入别名。词边界匹配把它们逐一排除在基础 token 计数之外，同时保持文件被钉住。
- **`gym_envs/scenario_loader/mission_observation.py`（A14）** 写排除（I45）；
  只读普查，T9 不得修改。

## 8. 修复轮改动汇总

### 第一轮

- **P1-1 词汇镜像。** 动作接口 scope 补 `mission_command`；声明全部六项
  `NavalWarfareRole`；为每个 `AuthorityRole` 补齐五元 schema（`authority_scope`/
  `decision_model_ref`/`action_interface`，不确定处标 `"unspecified"`）。新增
  编译权威镜像门禁。
- **P1-2 重裁。** A5 补 `arbitration`（leader-vs-mission 开火优先级）；A8 去
  `arbitration`（纯状态镜像）；A7/A9 由 `arbitration` 移至新的 `gating` 维度
  （激活而非冲突解决）；A14 语义补全以记录 `fire_mask_open` 策略门。
- **P1-3 ratchet 盲区。** 指纹升级为 token→count；扫描器现忽略注释/docstring 与
  `import`/`__all__` 再导出壳（统一再导出口径）同时仍捕获 prose 民俗；扫描根扩至
  整目录；同义词覆盖边界登记。

### 第二轮（本轮）

- **P1-1 提取器不再被注释欺骗。** 编译头枚举/scope 提取器现在于正则运行前先剥离
  整个头文件的 C++ 注释（引号感知：`//` + `/* */`，保留字符串/字符字面量），且枚举体
  以其真实闭合花括号（`{[^}]*}`）为界。这同时修复了注释掉的“ghost”成员被还原、以及
  块注释中的 `}` 截断枚举体两个问题。新增两个负向自证
  （`test_enum_extractor_ignores_commented_ghost_members`、
  `test_enum_extractor_survives_brace_in_block_comment`），外加引号感知证明
  （`test_comment_stripper_preserves_string_literal_comment_markers`）。
- **P1-2 同义词盲区真正修复。** 扫描器改为**词边界**匹配，并 token 化同义词族：
  `commander_id`、`command_relationship`、`infer_command_relationship`，以及 loader
  委托拼写 `_hierarchical_command_chain_active`（必要，因为词边界匹配——正确地——不再
  把门名折进带下划线前缀的方法，否则会漏掉 A7）。仅用同义词的文件现被检测
  （`test_scanner_detects_synonym_only_file`），词边界不碰撞得到证明
  （`test_scanner_word_boundary_excludes_substring`）。全部 14 个逐文件指纹以新扫描器
  重生（词边界剔除复合标识符子串，如 `leader_authorization_to_fire`、
  `infer_warfare_role_code`、`air_combat_c2_roe_state_from_*`，见 §7）。
- **P1-3 A14 依源码证据重裁。** `fire_mask_open`
  （`_air_combat_c2_roe_policy_fire_mask_open`）读 `authorization_to_fire` 及武器/交战/
  射击状态，却**不**读 `engagement_authority_holder_id` / `engagement_authority_grantor_id`
  （纯观测投影，行 405-406），故它裁的是策略*是否可开火*（门），而非*哪个 producer
  胜出*（仲裁）。A14 由 `arbitration → gating`（保留 delegation / doctrine）。对比 A13：
  它*确实*读 holder id 来解决谁可开火，故保持 `arbitration`。`gating` 词汇新增
  `FIRE_ELIGIBILITY_GATES` 以声明该开火掩码。
- **NB 候选集合门禁现钉住重裁结论。** 关键重裁站点（A5、A7、A8、A9、A14）钉死其
  *精确*类别集，故任何静默重翻都令门禁变红
  （`test_key_readjudicated_sites_pin_exact_categories`、
  `test_pinned_key_site_check_bites_on_reflip`）；普通站点保留候选集合模型以避免
  过度僵化。

## 相关

- [统一架构计划](README.zh.md)（T9 轨道定义）
- [仿真系统架构设计](../architecture/simulation_system_architecture_design.zh.md)
  （Agency 面；AgentRole schema；DoctrineFamily；合并/来源优先级规则）
- [SCAL 一致性普查（2026-07-20）](scal_conformance_census_20260720.zh.md)
  （同类 `reference` 登记；结构先例）
- `python/tasking_contracts/agency_registry.py`（注册式词汇所有者）
- `tests/architecture/agency/test_authority_registry_gate.py` 与
  `tests/architecture/fixtures/agency_authority_census_20260721.json`
  （ratchet 门禁 + 指纹钉定）
- `tests/architecture/policy_execution/*`（编译 WP12 AgentRole 权限门——收敛目标）
