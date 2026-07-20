# T6 残差台账（2026-07-20）

语言：
- 英文规范版：[t6_residual_ledger.md](t6_residual_ledger.md)
- 中文伴随版：`t6_residual_ledger.zh.md`

文档类型：`reference`
生命周期：`maintained`
规范路径：`docs/plan/unified_architecture_program/t6_residual_ledger.md`
所有者：`unified architecture program workline`
最近核验：`2026-07-20`
基线提交：`c2952d61`

状态：[统一架构计划](README.md) T6（测试基础设施合理化）残差索引。多轮已
验收迭代（I28、I31、I33）把非阻塞残差以自然语言散落登记在
`docs/plan/repository_consolidation/README.md` 各自的行内，未建立专门索引；
本文档即是这些登记行所指向、承诺补建的 T6 台账。按
[SCAL 一致性普查](scal_conformance_census_20260720.zh.md)先例，本文档是描
述性残差登记（`reference`），不是独立评审：它索引已经过评审的既有发现及
其出处迭代号，并加入本迭代（I36）的直接复核证据。本文档不作出新裁决，也
不关闭任何残差；某一行被"修复"仅代表其所属迭代已修复并如实记录，否则该行
仍由未来迭代持有。

## 1. I28：weapon_guidance_realism 的 xfail/expectedFailure 清单

I28 把 `tests/runtime/air_combat/weapon_guidance_realism` 下 45 个长期存在
的 junit 失败，裁定为跨六个漂移分组的 33 个唯一方法，逐方法治理（不使用
整批 skip）：25 个方法使用带机器可读 `reason=` 的
`pytest.mark.xfail(strict=True)`；另外 8 个方法改用纯 `unittest.expectedFailure`
（pytest 的 unittest 集成对这类方法只报告 `XFAIL`，**不带** reason 字符
串——原因是在 `xfail(strict=True)` 下，先通过的 subTest 会被判定为
`XPASS(strict)` 失败）。I28 自身的修复评审已指出这 8 个方法的理由只存在于
源码注释中，并要求本台账索引其中"混合通过"的那一半（另外 4 个是"全部子测
试失败"型，其 `expectedFailure` 折叠紧邻理由注释，审计成本更低）。

本迭代（I36）复核结果：

```
CMO_BUILD_DIR=<worktree>/build-local-win pytest -q tests/runtime/air_combat/weapon_guidance_realism -rx
-> 167 passed, 33 xfailed, 217 subtests passed
```

与 I28 落地时的计数完全一致。

### 1.1 四个纯 `expectedFailure` 节点 ID（混合通过型 subTest）

四者同属一个模块/类；每个方法都是**纯** `@unittest.expectedFailure`、未叠加
任何 `xfail` 标记（若用 strict xfail，pytest 9 会把其中通过的 subTest 判为
`XPASS(strict)`），治理理由只存在于紧邻的源码注释中，`-rx` 输出没有 reason
字符串——这正是 I28 要求本台账补齐的审计缺口。

| 节点 ID（模块/类见下方说明） | 分组 | 理由（取自源码注释） | 现状源码指针 |
| --- | --- | --- | --- |
| `test_phase3_power_and_data_link_dependencies_propagate_to_aircraft_overlay` | 主响应选择漂移 | E-3 宽带数据链命中现在把 `rotodome_radar_array` 报告为主组件 | `component_damage.py:982-989` |
| `test_phase2_named_control_components_derive_axis_specific_authority` | 主响应选择漂移 | F-16 前缘襟翼命中现在把 `flight_control_computer` 报告为主组件；集合用例还漂移进 `roll_control` | `aircraft_damage.py:435-442` |
| `test_phase2_avionics_and_crew_damage_derives_sensor_performance` | 跨子系统外溢 | 机翼飞控命中现在把传感器量程降到远低于 `>=0.9995` 不降级契约的水平 | `aircraft_damage.py:517-524` |
| `test_phase2_crew_consequences_distinguish_pilot_mission_and_command_roles` | 跨子系统外溢 | E-3 机组舱位命中现在外溢进用例标记为稳定的 `pilot`/`command_navigation` 角色 | `aircraft_damage.py:594-601` |

模块：`tests/runtime/air_combat/weapon_guidance_realism/test_warhead_and_component_damage.py`，
类 `WarheadAndComponentDamageTests`（该目录文档化的 wrapper 模式下，混入上
述 `AircraftDamageRuntimeMixin`/`ComponentDamageRuntimeMixin` 方法的 pytest
入口类）。完整节点 ID 为
`test_warhead_and_component_damage.py::WarheadAndComponentDamageTests::<方法名>`。

作为对照，另外四个 `expectedFailure` 方法（全部子测试失败型，在
`@unittest.expectedFailure` 之上叠加了 `@pytest.mark.xfail(strict=True,
reason=...)`、reason 会出现在 `-rx` 输出中，不属于本次索引缺口）分别是
`test_live_missile_hit_against_non_f16_structured_target_produces_component_damage`
（`test_geometry_and_edge_cases.py::GeometryAndEdgeCaseTests`）、
`test_phase2_aircraft_damage_overlay_tracks_air_specific_subsystems`、
`test_phase2_aircraft_hitboxes_produce_distinct_subsystem_effects`（即 I28
登记行中点名的"G3 hitboxes"`mil_thrust_n` 案例）以及
`test_phase3_fighter_component_geometry_covers_nose_avionics_and_engine_runtime_identity`
（后三者均在 `test_warhead_and_component_damage.py::WarheadAndComponentDamageTests`）。

### 1.2 33 个方法的组映射概要

| 分组（沿用 I28 术语） | `xfail(strict)` | `expectedFailure` | 合计 |
| --- | --- | --- | --- |
| 主响应选择漂移 | 1 | 2 | 3 |
| 邻近投影扩散 | 2 | 1 | 3 |
| 跨子系统外溢 | 8 | 4 | 12 |
| 失效态升级/饱和 | 8 | 1 | 9 |
| 气动/引信响应漂移 | 3 | 0 | 3 |
| 机制标定漂移 | 3 | 0 | 3 |
| **合计** | **25** | **8** | **33** |

分组定义与实例（取自复核后的 `-rx` 输出与源码注释）：

- **主响应选择漂移**——某次命中报告的"主"组件/响应发生变化（如上表 AWACS
  宽带数据链、F-16 前缘襟翼两个案例）。
- **邻近投影扩散**——`projected_hitbox_count`/`component_hit_count` 在契约
  期望孤立命中的地方报告了非零扩散（如
  `test_dfm_p4_direct_component_hit_populates_primary_component_event_fields`）。
- **跨子系统外溢**——损伤外溢进用例标记为稳定的子系统/轴，包括登记行本身
  点名的例子
  `test_phase2_aircraft_hitboxes_produce_distinct_subsystem_effects`：某次
  hitbox 命中把 `mil_thrust_n` 从标定的 76310 变为 64510。
- **失效态升级/饱和**——某项 overlay/失效态判定越过了标定阈值（如飞控
  overlay 饱和至 0.0，或判定从 `combat_capable` 升级为 `mobility_kill`）。
- **气动/引信响应漂移**——气动或引信定时响应幅值漂出标定带（如侧滑角增量
  收缩至 0.29 度，对照 `>2.0 度` 契约）。
- **机制标定漂移**——战斗部机制标定不再复现参考幅值（如标定剖面下
  `component_failure_count` 不再 `> 0`）。

## 2. I33：xmacro 辅助函数换行吞噬缺陷 + 两处潜伏严格正则

**根因**（由 I33 登记，尚未修复；按本迭代指令写保护至 I35 落地前）：
`tests/support/xmacro_text.py::expand_header_field_incs` 使用
`_INC_INCLUDE_RE = re.compile(r'#include "([^"]+\.inc)"\n?')`，其结尾的
`\n?` 会选择性吞掉 `#include` 行自身的换行符。替换文本
（对展开字段声明做 `"\n".join(...)`）本身不带结尾换行，于是一个完全由宏
拥有字段的 struct，其模拟出的 body 会以最后一个字段直接粘连在紧随其后的
`};` 上，二者之间没有换行。

**后果**：任何用严格收尾正则定位 struct body 的源码文本边界测试

```python
pattern = rf"\bstruct\s+{re.escape(struct_name)}\b[^{{;]*\{{(?P<body>.*?)\n\}};"
```

都会跳过这个粘连的 `};`（因为它前面没有紧邻的 `\n`），并贪婪地越界匹配进
邻近 struct 的 body。I33 曾直接命中此缺陷：宏化两个 facade 类后，
`test_runtime_dto_contracts.py` 对 `RuntimeCapabilities` 的匹配从正确边界
扩张到 14,642 字符，吞掉了 `DeviceResidentOutputDescriptor` 及其禁用令牌
守卫。

**I33 已修复**（将 `\n\}};` 放宽为 `\n?\}};`）：
`tests/runtime/engagement/test_engagement_contract_shape.py`、
`tests/architecture/runtime_facade/test_runtime_dto_contracts.py`（上述阻塞性
回归触发的评审驱动修复）。

**两处仍处于严格 `\n\}};` 形式的潜伏点**（目前为绿仅因为它们扫描的 struct
尚未通过 `.inc` include 完全宏化；未来任何经此模式迁移的字段族都会重现同
样的静默越界匹配）：

| 位置 | 指针 | 扫描的 struct |
| --- | --- | --- |
| `tests/architecture/platform_spawn/test_typed_platform_spawn_contracts.py` | `_struct_body`，第 54 行 | `TypedPlatformSpawnAdmission`、`TypedPlatformSpawnResult`、`BatchWorldSetupResult` |
| `tests/runtime/mission/test_policy_contract_shape.py` | `_struct_body`，第 16 行 | `ActionHoldPolicy`、`ActionIntentPacket`、`CoordinationIntentPacket`、`AgentRole`、`DecisionBelief`、`AgentRoleAuthorizationResult` |

**现状**：待 I35 落地后统一修复。按本迭代指令，`tests/support/xmacro_text.py`
与上述两个文件均在本迭代写集之外，未做任何改动；本行仅为指针登记。

## 3. 任务 B 修复（本迭代 I36）：retained 存档重写副作用

**根因**：`tests/architecture/damage_model/test_release_signoff_gate.py::test_release_signoff_gate_cli_writes_default_artifacts`
是该文件中唯一未使用 `tmp_path` 的测试；它在不传 `--output-dir`/`--report`
的情况下调用
`tools/maintenance/damage_model.py release-governance source-release-signoff`，
于是 CLI 的 argparse 默认值（`DEFAULT_OUTPUT_DIR`/`DEFAULT_REPORT_PATH`）
把写入目标直接指向真实的 retained 存档位置：
`docs/task/air_combat/archive/a2_high_fidelity_damage_model/calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/retained_artifacts/res001_release_signoff_20260531/{manifest.json,res001_release_signoff_gate.json}`
及同级报告
`validation_res001_release_signoff_gate_20260531.zh.md`。重新生成会基于磁
盘上源 payload 的字节重算若干 `sha256` 字段；在本 CRLF checkout 下，重算出
的 `gate_sha256` 与已落盘值不同（实测：落盘值 `822c496d...` vs 重算值
`809dfe67...`），于是每次运行都会重写全部三个文件——这违反了 retained 存
档的不可变政策，且已两次造成"工作树污染"的误报。
`tools/maintenance/release_governance/source_release_signoff.py` 的 Windows
`\r\n` 写文本行为是 I19 登记在案、有意保留的既有约定，本迭代正确地未触
碰它；本迭代写集只包含该测试文件本身。

**修复**：改为通过 CLI 自带的 `--output-dir`/`--report` 参数把写入重定向到
`tmp_path`（与同文件另外四个测试保持一致，它们均已使用 `tmp_path`），并另
加一条不产生任何 IO 的静态断言，钉住
`DEFAULT_OUTPUT_DIR`/`DEFAULT_REPORT_PATH` 两个默认值本身，使默认参数的接
线仍受回归保护，但绝不会再写向真实位置。

**验证**：目标测试文件连续单跑两次——两次运行前后 `git status` 均报告三个
retained 文件零改动；三个文件与 HEAD 始终字节一致。

## 4. 已 held 与移交中的 DTO 残差

### 4.1 I31：`ExecutionBatchStepResult` held（预处理器逗号）

`ExecutionBatchStepResult`（15 字段）保持完全手写，未纳入
`tools/maintenance/dto_schema` 单一来源治理：其
`std::vector<std::array<double, 4>>` 字段包含一个尖括号内的逗号，X-macro
预处理器会把它误拆成额外的宏参数（预处理器只按括号配对，不识别尖括号）；
若改用类型别名规避，又会破坏与手写声明逐 token 相同的类型等价性。本行未
指派目标迭代，留作指针，等待未来某个 DTO 族迁移迭代找到不破坏 token 等价
性的编码方式（例如在 schema 的扩展位中注册专用别名）。

### 4.2 I33：`RecentEngagementEvents` 移交（I35 处理中）

`RecentEngagementEvents`（`src/core/engine/engagement_event_types.h`，14
字段，按 I33 普查为"形状同样干净"）位于 I33 声明写集边界之外，被登记为下
一个自然候选的 DTO 单一来源迁移对象。按本迭代（I36）任务书所述，I35 正在
处理该迁移——其"下一轮候选"的记载见 I33 自身的登记行
（`docs/plan/repository_consolidation/README.md`）；截至本台账落笔时，I35
自身的迁移登记行尚未出现（进行中，未落地）。本台账仅作指针登记，不重复或
抢跑该迁移。

## 5. 本机环境红清单（截至 c2952d61）

以下五类属于机器/工作树本地的既有环境红，已在 I31、I33、I34 的隔离基线核
查中独立复现过。本迭代在这一具体工作树上
（`CMO_BUILD_DIR=<worktree>/build-local-win`）逐类直接复核；对能收敛为可枚
举小集合的类别，直接点出精确节点 ID。

| 项目 | I36 直接复核结果 | 登记出处 |
| --- | --- | --- |
| 5 条 flecs 静态库链接签名红 | 复现了该失败类别：`tests/architecture/compatibility_quarantine/test_guard_enforcement.py` 与 `tests/architecture/runtime_spine/test_clock_domain_enforcement.py` 在收集阶段均报 `AssertionError: Could not find include directory for CMake dependency 'flecs'`（针对本工作树的 `build-local-win` 快照）。 | I31/I33/I34 登记行（每次均在隔离基线上独立复现；I34："same 5 flecs reds"） |
| diagnostics 懒加载 `common.ef_py` 属性缺口 | `pytest tests/runtime/bindings/test_lazy_binding_resolution.py::LazyBindingResolutionTests::test_common_import_prefers_repo_build_ef_py` 失败：`AttributeError: module 'tools.diagnostics.common' has no attribute 'ef_py'. Did you mean: '_ef_py'?`（该模块只暴露私有的 `_ef_py()` 懒加载 helper）。 | I31 登记行（"one pre-existing `common.ef_py` attribute gap"） |
| 4 处 `test_wp22_*` 红 | 按节点 ID 精确定位，均在 `tests/architecture/runtime_facade/test_runtime_escape_hatches.py`：`test_wp22_naval_screen_raw_unit_state_seam_stays_named_and_localized`、`test_wp22_tasking_bridge_quarantines_raw_mission_and_command_chain_sync_helpers`、`test_wp22_scripted_opponent_kernel_access_stays_named_and_localized`、`test_wp22_loading_world_layout_kernel_apply_stays_named_and_localized`；每条都断言一个本工作树 `python/rl/tasking/bridge.py` 尚不存在的重构后符号（如 `class LoaderOwnedScriptedOpponentKernelView:`）——这是相对于落地该 wp22 重构的分支的血缘差距，并非本迭代引入的回归。I35 评审的超集回归又暴露同族一处红：`test_wp12_runtime_facade_does_not_gain_a_second_maintained_injection_api`（同文件），经纯净基线工作树复现，于 I35 落地时补入本条。 | I33 登记行（"the four `test_wp22_*` directory reds"）；I35 评审 |
| `leader_phase_manager_approach_arm` 契约 | `python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/comm/leader_phase_manager_approach_arm.json` 失败：`expected approach-arm transition count mismatch: 0`。 | I34 登记行 |
| `tests/gpu` 的 `build-gpu` 缺失红 | `pytest tests/gpu/test_cuda_import_order.py::CudaImportOrderTests::test_world_batch_vec_env_import_after_torch_runtime_setup` 失败：其拉起的子进程报 `ModuleNotFoundError: No module named 'ef_py'`，因为本工作树只有 `build-local-win/`，没有 `build-gpu/`。 | I34 登记行 |

沿用 I34 独立复核并作为本迭代起始基线的门禁计数：维护 smoke
`436 passed, 45 subtests`；聚焦 `world_batch`+leader+facade 选集
`282 passed`、同样 5 条 flecs 红、`1 skipped`、`22 subtests`。

## 相关

- [仓库整合计划](../repository_consolidation/README.zh.md)（上文引用的
  I28、I31、I33、I34 登记行）
- [SCAL 一致性普查（2026-07-20）](scal_conformance_census_20260720.zh.md)
  （同为 `reference` 类型的登记文档；本文档的结构先例）
- `tests/runtime/air_combat/weapon_guidance_realism/README.md`（第 1 节引
  用的 wrapper/mixin 收集契约）
