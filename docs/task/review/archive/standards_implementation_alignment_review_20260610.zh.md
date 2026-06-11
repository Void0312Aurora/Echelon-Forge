# 标准化-实现对齐审查

Language:
- 英文主文：[standards_implementation_alignment_review_20260610.md](standards_implementation_alignment_review_20260610.md)
- 中文辅文：`standards_implementation_alignment_review_20260610.zh.md`

状态：`2026-06-10`，`docs/standards/` 标准化文档与当前实现的对齐审查。

来源：对 `docs/standards/` 下全部维护中标准化文档 vs `src/`、`gym_envs/`、
`python/`、`tests/` 实现面的交叉审计。任务文档成熟度与验收状态不在本审查范围内，
除非标准明确冻结了具体的 runtime 合同。

## 1. 目的

本审查回答：

1. 当前实现是否遵循标准所有权层级（foundation → joint → services → air/naval/ground specialization → model）？
2. 标准中记录的字段级合同是否与 runtime/test 产物一致？
3. 哪些标准文档相对实现已滞后？
4. 标准与实现之间存在哪些语义错配需要解决？

## 2. 结论

**标准树与当前实现在架构和字段级合同上实质对齐。** 分层体系忠实地编码在
`src/components/` 目录结构中、`MissionCommand` owner-slice 拆分中、
`TaskOrder`/`LeaderIntent`/`PilotReport` 的 core-and-domain 分层中，
以及 service-profile 枚举词汇中。

共发现六处偏差。一处是语义错配（ground tasking），五处是文档滞后
（实现已超前标准）。没有任何偏差会阻止将标准树声明为项目的权威所有权地图。

## 3. 证据矩阵

### 3.1 分层体系 — 通过

| 标准层 | 标准引用 | 实现路径 | 状态 |
| --- | --- | --- | --- |
| Foundation | `docs/standards/foundation/conventions.md` | ENU 坐标、NAV 角度、米/秒单位在整个 C++ 和 Python 中使用 | 对齐 |
| Foundation | `docs/standards/foundation/gradient_realism_principles.zh.md` | G0–G7 标签在任务文档和场景配置中被引用 | 对齐 |
| Foundation | `docs/standards/foundation/realism_authority_boundary.zh.md` | Authority 字段门控 A2/M2/M3 的投放行为 | 对齐 |
| Joint | `docs/standards/joint/command_and_modeling_baseline.md` | `src/components/tasking/common/core_tasking_enums.h` — 7 个枚举全部存在 | 对齐 |
| Joint | `docs/standards/joint/command_link_and_reporting_baseline.md` | `src/components/command/common/mission_command_core.h` — 核心 DTO 存在 | 对齐 |
| Services | `docs/standards/services/` | 4 个军种画像已定义；`ServiceProfile` 枚举匹配 | 对齐 |
| Air | `docs/standards/air/` | `src/components/domains/air/` — command/tasking DTO + 测试 | 对齐 |
| Naval | `docs/standards/naval/` | `src/components/domains/naval/` — command/tasking DTO + 测试 | 对齐 |
| Ground | `docs/standards/ground/` | `src/components/domains/ground/` — command/tasking DTO + 测试 | 对齐 |
| Model | `docs/standards/model/policy_execution_architecture.md` | 18 组件实现映射已验证；全部文件存在 | 对齐 |
| Bridge | `docs/standards/bridge/` | 5 阶段 runtime 工作流与 `gym_envs/scenario_loader/` 吻合 | 对齐 |
| Governance | `docs/standards/governance/` | 双语文档、subagent 派发、WP closure 政策已登记 | 对齐 |

### 3.2 字段级合同 — 通过

| 合同 | 标准文档 | 代码位置 | 字段匹配 | 备注 |
| --- | --- | --- | --- | --- |
| `MissionCommandCore` | `joint/command_link_and_reporting_baseline.md` §3 | `src/components/command/common/mission_command_core.h` | 11/11 核心字段存在 | 4 个额外字段未入标准：`threat_state`、`assigned_target_track_id`、`assigned_target_source_id`、`assigned_target_snapshot_time_s` |
| `MissionCommandAir` | `joint/command_link_and_reporting_baseline.md` §3 | `src/components/domains/air/command/mission_command_air.h` | 11/11 air 字段存在 | 使用类型化枚举而非 raw int——较标准更优 |
| `MissionCommandNaval` | `joint/command_link_and_reporting_baseline.md` §3 | `src/components/domains/naval/command/mission_command_naval.h` | 7/7 naval 字段存在 | 在标准基线之上增加了结构化 directive |
| `PilotAction` | `air/act.md` | `src/components/command/pilot_action.h` | 19/19 字段存在 | 头文件显式引用 `act.md` |
| `TaskOrderCore` | `joint/command_and_modeling_baseline.md` §5 | `src/components/tasking/common/task_order_core.h` | 全部 13 个 common-core 字段存在 | — |
| `PilotReportCore` | `air/rep.md` | `src/components/tasking/common/pilot_report_core.h` | 全部 17 个核心字段存在 | — |
| `air_combat_hybrid_v1` | `air/act.md` §A5 | `gym_envs/universal_env_parts/air_combat_event_action.py` | 12 维 transport 匹配 | A5 event-action FSM runtime 已实现并测试 |
| Mission obs modes | `air/obs.md` | `python/mission_obs_taxonomy.py` | 6/6 air mode 存在 | 自标准撰写后新增 3 个 mode：`naval_screen_station_v1`、`air_combat_c2_roe_v1`、`air_combat_c2_roe_v2` |

### 3.3 双语文档合规 — 通过

`docs/standards/` 下全部 25 份标准文档均配备 `.zh.md` 辅文。
无孤立的 canonical 文件。符合
`docs/standards/governance/bilingual_documentation_policy.zh.md`。

### 3.4 模型架构实现映射 — 通过

`docs/standards/model/policy_execution_architecture.md` §Current Implementation Map
中列出的全部 18 个实现面均在声明的路径存在：

- `python/mission_obs_taxonomy.py` — 存在
- `gym_envs/scenario_loader/mission_observation.py` — 存在
- `python/models/transformer.py` — 存在（`TransformerExtractor`、`TemporalTransformerExtractor`）
- `python/rl/policy_algo/policies.py` — 存在（`HierarchicalMoEExecutionPolicy`、`_HybridActionDistribution` 等）
- `python/rl/policy_algo/hmoe_routing.py` — 存在
- `gym_envs/universal_env_parts/air_combat_event_action.py` — 存在
- `python/rl/policy_algo/first_event_hazard.py` — 存在
- `python/rl/policy_algo/first_event_rollout_buffer.py` — 存在
- `python/rl/policy_algo/ppo_adaptive_kl.py` — 存在
- `tools/diagnostics/` 下全部 probe/diagnostic 路径 — 存在

## 4. 缺口清单

### GAP-001：Ground Tasking 语义错配 — `TASK_MOVE` ≠ `HoldStatic`

| 字段 | 值 |
| --- | --- |
| 严重度 | **中** |
| 标准 | `docs/standards/ground/minimal_task_structure.zh.md` — `TASK_MOVE` 含义为"让以 platoon 为中心的单位向 route、phase line 或 objective reference 机动" |
| 实现 | `src/components/domains/ground/tasking/ground_tasking_enums.h` — `GroundTaskMode::HoldStatic = 1` |
| 影响 | 唯一编码 `TASK_MOVE` 意图的方式是 `HoldStatic`，但"固守"与"机动"语义矛盾。`OccupyStatic` ↔ `TASK_OCCUPY` 和 `SupportStatic` ↔ `TASK_SUPPORT` 语义一致。 |
| 建议 | 要么将 `HoldStatic` 重命名为 `MoveStatic`（保留 G0 静态限制），要么新增 `MoveDynamic` 枚举值并标记为延后。若 G0 范围确实被有意收窄为 static-only tasking，则更新标准。 |
| 引用 | `ground_tasking_enums.h:3-8`、`minimal_task_structure.zh.md:66-74` |

### GAP-002：Mission Observation Mode 已超出标准范围

| 字段 | 值 |
| --- | --- |
| 严重度 | **低** |
| 标准 | `docs/standards/air/obs.md` — 记录 6 个 air-specific mode（`basic` 到 `nav_v2_cooperative_takeoff_v1`） |
| 实现 | `python/mission_obs_taxonomy.py` — 9 个 mode；新增 `naval_screen_station_v1`、`air_combat_c2_roe_v1`、`air_combat_c2_roe_v2` |
| 影响 | 3 个新 mode 已在 runtime 和测试中活跃使用，但没有标准层所有权声明。`naval_screen_station_v1` 应归 naval specialization；`air_combat_c2_roe_v1/v2` 应归 air specialization。 |
| 建议 | 更新 `air/obs.md` 注册 `air_combat_c2_roe_v1` 和 `air_combat_c2_roe_v2`。创建或更新 naval observation contract 注册 `naval_screen_station_v1`。记录新 mode 的字段列表。 |
| 引用 | `mission_obs_taxonomy.py:9-11`、`obs.md:35-42` |

### GAP-003：`MissionCommandCore` 含有未文档化字段

| 字段 | 值 |
| --- | --- |
| 严重度 | **低** |
| 标准 | `joint/command_link_and_reporting_baseline.md` §2–3 — 列出已知核心字段 |
| 实现 | `src/components/command/common/mission_command_core.h` — 新增 `threat_state`、`assigned_target_track_id`、`assigned_target_source_id`、`assigned_target_snapshot_time_s` |
| 影响 | 这些字段已在活跃 runtime contract 中（`mission_command_codec.cpp` 序列化它们），但其所有权（joint、sensor/track 或 engagement）未在标准中定义。 |
| 建议 | 将这些字段补充到 `joint/command_link_and_reporting_baseline.md` §2，并注明所有权分类。若横切 sensor/track 关注点，引用待定 sensor/track 标准。 |
| 引用 | `mission_command_core.h:19-22`、`command_link_and_reporting_baseline.md:27-45` |

### GAP-004：标准文档日期陈旧

| 字段 | 值 |
| --- | --- |
| 严重度 | **低** |
| 范围 | 多份 authoritative 标准携带的日期早于它们所描述的最新实现变更： |

| 文档 | 标准日期 | 最后实现变更 | 漂移 |
| --- | --- | --- | --- |
| `air/act.md` | 2026-06-02 | 2026-06-08（A5 event-action runtime 验收） | 6 天 |
| `air/obs.md` | 2026-05-18 | 2026-06-04（C2/ROE mode 新增） | 17 天 |
| `bridge/runtime_workflow_and_contract_baseline.md` | 2026-05-18 | 2026-06-08 | 21 天 |
| `joint/command_and_modeling_baseline.md` | 无日期 | — | 未标注 |
| `naval/minimal_task_structure.md` | 无日期 | — | 未标注 |

| 影响 | 读者无法仅从标准判断它是否反映当前 runtime contract。 |
| 建议 | 为 `joint/command_and_modeling_baseline.md`、`joint/command_link_and_reporting_baseline.md`、`naval/minimal_task_structure.md` 和 `air/obs.md` 添加或刷新日期戳。`air/act.md` 日期较近但应在状态行中确认 A5。 |
| 引用 | 各标准文件头部 |

### GAP-005：模块化规划与实际 `src/` 布局不一致

| 字段 | 值 |
| --- | --- |
| 严重度 | **低**（文档自标注"活跃规划，不是当前 runtime 合同"） |
| 标准 | `docs/standards/planning/modularization_plan.md` — 目标 `core/` → `systems/` → `interfaces/` 单向依赖 |
| 实现 | `src/components/` 是主导组织层；`systems/` 填充度低于规划；`core/` 职责分布在 `core/engine/`、`core/mission/` 和 `runtime/facade/` |
| 影响 | 该计划可能让期待它描述当前代码的读者困惑。 |
| 建议 | 要么 (a) 更新计划，反映实际 `components/domains/{air,naval,ground}/` 三域拆分作为已实现目标，要么 (b) 若项目方向已转移则归档并添加前向指针。 |
| 引用 | `modularization_plan.md:53-59` |

### GAP-006：新增 MLF-3 测试文件无对应标准入口

| 字段 | 值 |
| --- | --- |
| 严重度 | **低**（属任务文档层问题，非标准缺陷） |
| 观察 | `tests/runtime/air_combat/test_warhead_spatial_component_projection.py` 为新增（未跟踪）。warhead effects 空间投影合同未在 `docs/standards/` 下任何 weapons/damage specialization 标准中捕获。 |
| 影响 | 若空间投影合同稳定化，需要标准层所有权槽位。当前 foundation 层 `realism_authority_boundary.zh.md` 提供 authority 门控，但不提供字段级合同文档。 |
| 建议 | 当 MLF-3 warhead effects 工作达到验收时，在 `docs/standards/air/` 下新增 weapon-effects specialization 条目，或在 `docs/standards/weapons/` 新目录。不要让合同仅存在于任务文档和测试文件中。 |
| 引用 | `tests/runtime/air_combat/test_warhead_spatial_component_projection.py`、`docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_warhead_effects/` |

## 5. 非缺口（已验证对齐）

以下领域经核查无需操作：

| 领域 | 检查 | 结果 |
| --- | --- | --- |
| `CommandRelationship` 枚举 | 与 `joint/command_and_modeling_baseline.md` §2 匹配（COCOM、OPCON、TACON、ADCON、support、coordinating authority、DIRLAUTH） | 全部 7 个值存在 |
| `CoordinationMode` 枚举 | 与 joint 标准 §5 匹配 | 全部 8 个值存在 |
| `ServiceProfile` 枚举 | 与 `services/` 四个画像匹配 | AirForce、Army、Navy、MarineCorps |
| `MissionCommand` owner-slice 模式 | Air/Naval/Ground 均有 `OwnerSlice` typedef + `kMissionCommand*OwnedDomainSlice` constexpr | 跨领域一致 |
| `PilotReportCore` 字段 | 与 `air/rep.md` §核心报告字段匹配 | 全部 17 个字段存在 |
| `PilotReportAir` 字段 | 与 `air/rep.md` §Air 报告扩展字段匹配 | 全部 7 个字段存在 |
| C++ roundtrip 测试 | 标准要求 air/naval/ground 命令字段 roundtrip 保持 | 三个领域均有测试 |
| `air_combat_hybrid_v1` event-action FSM | `air/act.md` §A5 定义 engagement state machine | `air_combat_event_action.py` 实现完整 FSM |
| `CommandLink` 和 `DataLink` | `joint/command_link_and_reporting_baseline.md` §4–5 | 头文件存在：`command_link.h`、`command_link_qos.h`、`data_link.h` |
| `fidelity_profile_contracts.h` | Foundation 梯度真实性原则 | 6 个标签已定义，`exact_evaluation` 已准入 |

## 6. 建议行动顺序

| 优先级 | 缺口 ID | 行动 | 工作量 |
| --- | --- | --- | --- |
| 1 | GAP-001 | 解决 ground `TASK_MOVE` ↔ `HoldStatic` 错配（重命名枚举或更新标准） | 小 |
| 2 | GAP-002 | 在 observation 标准中注册 `air_combat_c2_roe_v1/v2` 和 `naval_screen_station_v1` | 小 |
| 3 | GAP-003 | 在 joint 标准中补充 `threat_state`、`assigned_target_track_id`、`assigned_target_source_id`、`assigned_target_snapshot_time_s` | 小 |
| 4 | GAP-004 | 刷新陈旧标准文档的日期戳 | 极小 |
| 5 | GAP-005 | 决定 modularization plan 的去向（更新或归档） | 中 |
| 6 | GAP-006 | MLF-3 达到验收时创建 weapon-effects 标准条目 | 中 |

## 7. 验证说明

对齐通过以下方式验证：

- `find` 遍历 `src/components/`，对比目录结构与标准所有权层级
- `MissionCommand*`、`TaskOrder*`、`PilotReport*`、`PilotAction` 头文件逐字段对比标准字段列表
- 枚举值对比（`core_tasking_enums.h`、`ground_tasking_enums.h`、`naval_tasking_enums.h`、`air_tasking_enums.h`）vs 标准词汇表
- `python/mission_obs_taxonomy.py` mode 列表对比 `air/obs.md` mode 表
- 模型架构实现映射文件存在性检查（18 路径，全部存在）
- 双语辅文存在性检查（25 对，全部存在）

## 8. 相关文档

- [标准化文档总览](../../standards/README.zh.md)
- [文档对齐映射](../../standards/overview/document_alignment_map.zh.md)
- [联合指挥与建模基线](../../standards/joint/command_and_modeling_baseline.md)
- [联合命令链与汇报基线](../../standards/joint/command_link_and_reporting_baseline.md)
- [运行时工作流与合同基线](../../standards/bridge/runtime_workflow_and_contract_baseline.md)
- [空中平台特化总览](../../standards/air/README.md)
- [海军标准总览](../../standards/naval/README.md)
- [Ground 标准总览](../../standards/ground/README.zh.md)
- [模型架构基线](../../standards/model/policy_execution_architecture.md)
- [文档系统就绪度审查](documentation_system_readiness_review_20260601.zh.md)
