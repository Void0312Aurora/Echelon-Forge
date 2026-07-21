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
其出处迭代号，并加入本迭代（I36）的直接复核证据，以及 I37 对第 2 节所登
记 xmacro helper 缺陷的后续修复与关闭。本文档本身不作出新裁决，也不独立
关闭任何残差；某一行被"修复"仅代表其所属迭代已修复并如实记录（见 2.1 节），否则该行
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

## 2. I33：xmacro 辅助函数换行吞噬缺陷 + 两处潜伏严格正则（已于 I37 修复）

**根因**（由 I33 登记；按本迭代自身指令写保护至 I35 落地，已于 I35 落地
后由 I37 修复——修复内容与完整复核见 2.1 节）：
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

**现状**：已于 I37 修复。下方 2.1 节记录修复内容、新增的 helper 级单元测
试、四处正则的统一、两处潜伏点的复核，以及完整验证门证据。

### 2.1 I37 修复与复核

**修复**：`tests/support/xmacro_text.py` 中的 `_INC_INCLUDE_RE` 不再吞掉
`#include` 行自身的结尾换行——`re.compile(r'#include "([^"]+\.inc)"\n?')`
改为 `re.compile(r'#include "([^"]+\.inc)"')`。`#include` 行自身的换行符
因此作为原样字面文本保留在周围源码中，使替换文本（本身仍不带结尾换行）
后面总会紧跟这个被保留下来的换行——一个完全由宏拥有字段的 struct，其模
拟出的 body 现在会在紧随其后的内容（通常是该 struct 自己的 `};`）前保留
换行，与手写风格逐字节一致。`expand_header_field_incs` 与
`expand_binding_field_incs` 共用这同一条正则，故这一行的修复同时覆盖两
侧调用点；`expand_binding_field_incs` 携带完全相同的潜伏缺陷（下方新增
的专项单元测试已确认），尽管台账登记的既有消费者均未依赖其粘连形态。

**新增 helper 级单元测试**（`tests/support/test_xmacro_text.py`；此前该
helper 无任何专属单元测试）：四个测试独立于任何生产头文件，围绕真实的
两字段 `runtime/contracts/detail/engagement_entity_ref.inc`（只读引用，
未新增任何 fixture 文件）构造"单宏组紧邻 `};`"的合成片段，直接验证修
复——

- `test_expand_header_field_incs_preserves_newline_before_closing_brace`
  ——严格 `\n\}};` 式（不带 `?`）可匹配全宏化 struct。
- `test_expand_header_field_incs_does_not_swallow_neighbouring_struct`
  ——紧随宏化 struct 之后放置的邻居 struct 不会被吞入前者的 body。
- `test_expand_header_field_incs_keeps_consecutive_include_lines_on_separate_lines`
  ——同一 struct 内两个连续的 `#include` 行，其共享边界处也保持换行分
  隔，不仅是收尾处。
- `test_expand_binding_field_incs_preserves_newline_before_following_code`
  ——绑定侧的姊妹函数获得同样的修复（共用正则）。

四个测试均先在修复前的 helper 上确认为红（临时 `git stash` 仅还原
`xmacro_text.py`），再在修复后确认为绿，证明它们确实命中缺陷本身，而非
假绿。

**四处正则统一为严格 `\n\}};` 式**（`\n?\}};` 放宽形态已在全仓退役）：
`test_engagement_contract_shape.py::_struct_body` 与
`test_runtime_dto_contracts.py::_struct_body` 的正则尾部由 `\n?\}};` 恢
复为严格 `\n\}};`。本迭代任务书标记为"可能需要微调"的第三处适配——I35
在 `test_dto_domain_shell_guard.py` 中改写的裸声明断言列表（如
`"shared_core_type shared_core;"` 而非 `"...shared_core{};"`）——实测无
需任何改动：该列表是针对 `_rendered_header_field` 另一条独立约定（"值初
始化默认值省略末尾 `{}`"）的纯子串包含检查，与本次修复恢复的换行正交，
故该列表逐字节保持不变且仍然通过。台账点名的两处潜伏点
（`test_typed_platform_spawn_contracts.py`、`test_policy_contract_shape.py`）
同样无需任何代码改动，且不再仅是"因头文件布局侥幸保绿"——helper 本体修
复后，无论其扫描的 struct 未来是否被完全宏化，其严格 `\n\}};` 式均恒正
确。

**全仓扫描**：搜索字面 `\n?\}};` 正则拼写，在 `.py` 文件内现已零命中。
仅剩的命中都是本台账与 `docs/plan/repository_consolidation/README.md`/
`.zh.md` 中 I33 登记行的历史叙述文字，二者均以过去时如实描述 I33 当年实
际做出的放宽；这些历史行刻意保持不变，未做编辑。

**验证**（本工作树，`CMO_BUILD_DIR=<worktree>/build-local-win`）：

```
pytest -q tests/support/test_xmacro_text.py
-> 4 passed（新增；每条均已在修复前的 helper 上独立确认为红）

pytest -q tests/runtime/engagement/test_engagement_contract_shape.py
-> 6 passed

pytest -q tests/architecture/runtime_facade/test_runtime_dto_contracts.py
-> 7 passed（零红；本台账第 5 节所列的四处 test_wp22_* 红实际位于另一
   文件 test_runtime_escape_hatches.py，不在本文件内）

pytest -q tests/architecture/command_tasking/test_dto_domain_shell_guard.py
-> 11 passed

pytest -q tests/architecture/runtime_facade/test_tasking_batch_contract_boundaries.py
-> 2 passed, 1 failed——test_wp24_python_command_chain_business_writes_use_maintained_contracts
   在把 xmacro_text.py 还原至 I37 修复前状态时同样失败，即与本缺陷无关。
   I37 评审的谱系甄别（隔离干净检出）：48c86c4b（I33）绿、自 c2952d61
   （I34）起红——I34 落地把命令链写调用下沉到 _shared_ops.py，而该文本
   守护的合成文件集不扫描它（adapter.py 在三个提交都含 token；真正转空
   的是守护的 vec_env 合成文本与 cooperative 模块两处）。行为测试
   （test_world_batch_vec_env_command_chain.py，23/23）保持绿，故属守护
   适配缺失、非功能回归。已登记至下方第 6 节；修复方向：把 _shared_ops.py
   纳入守护扫描集。在本迭代写集之外，未做处理

pytest -q tests/architecture/platform_spawn/test_typed_platform_spawn_contracts.py
-> 5 passed

pytest -q tests/runtime/mission/test_policy_contract_shape.py
-> 8 passed

pytest -q tests/architecture/policy_execution/test_belief_and_read_side_boundaries.py
-> 13 passed

pytest -q tests/architecture/runtime_facade/test_runtime_facade_contract_boundaries.py
-> 8 passed

python tools/runners/run_pytest_suite.py --suite tests/smoke/ci_smoke_suite.json
-> 439 passed, 45 subtests passed（与本迭代起始基线一致；新增的
   tests/support/test_xmacro_text.py 未纳入 smoke 清单，未参与本次计数）

ruff check .        -> All checks passed!
git diff --check    -> 干净
```

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
| diagnostics 懒加载 `common.ef_py` 属性缺口 | `pytest tests/runtime/bindings/test_lazy_binding_resolution.py::LazyBindingResolutionTests::test_common_import_prefers_repo_build_ef_py` 失败：`AttributeError: module 'tools.diagnostics.common' has no attribute 'ef_py'. Did you mean: '_ef_py'?`（该模块只暴露私有的 `_ef_py()` 懒加载 helper）。**已于 I57 守卫适配到绿（见 8.5 节）。** | I31 登记行（"one pre-existing `common.ef_py` attribute gap"） |
| 4 处 `test_wp22_*` 红 | 按节点 ID 精确定位，均在 `tests/architecture/runtime_facade/test_runtime_escape_hatches.py`：`test_wp22_naval_screen_raw_unit_state_seam_stays_named_and_localized`、`test_wp22_tasking_bridge_quarantines_raw_mission_and_command_chain_sync_helpers`、`test_wp22_scripted_opponent_kernel_access_stays_named_and_localized`、`test_wp22_loading_world_layout_kernel_apply_stays_named_and_localized`；每条都断言一个本工作树 `python/rl/tasking/bridge.py` 尚不存在的重构后符号（如 `class LoaderOwnedScriptedOpponentKernelView:`）——这是相对于落地该 wp22 重构的分支的血缘差距，并非本迭代引入的回归。I35 评审的超集回归又暴露同族一处红：`test_wp12_runtime_facade_does_not_gain_a_second_maintained_injection_api`（同文件），经纯净基线工作树复现，于 I35 落地时补入本条。**四个 `test_wp22_*` 均已于 I57 守卫适配到绿（见 8.3 节）；那个 `test_wp12_*` 节点——实际位于 `tests/architecture/policy_execution/test_intent_injection_authority_guard.py`，而非本文件——亦于 I57 守卫适配到绿（见 8.4 节）。** | I33 登记行（"the four `test_wp22_*` directory reds"）；I35 评审 |
| `leader_phase_manager_approach_arm` 契约 | `python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/comm/leader_phase_manager_approach_arm.json` 失败：`expected approach-arm transition count mismatch: 0`。**已于 I57 分类（见 8.8 节）：lineage 分歧——契约脚手架 `FakeLoader` 落后于本谱系 `approach_arm_require_runway_frame` arming 门控；JSON/runner 未动。** | I34 登记行 |
| `tests/gpu` 的 `build-gpu` 缺失红 | `pytest tests/gpu/test_cuda_import_order.py::CudaImportOrderTests::test_world_batch_vec_env_import_after_torch_runtime_setup` 失败：其拉起的子进程报 `ModuleNotFoundError: No module named 'ef_py'`，因为本工作树只有 `build-local-win/`，没有 `build-gpu/`。**已于 I57 用条件 `skipUnless(build-gpu 存在)` 治理（见 8.7 节）。** | I34 登记行 |
| diagnostics 脚本治理红 | `tests/architecture/governance/test_tools_script_governance.py::test_diagnostics_top_level_entrypoints_are_governed_by_function`——I35 评审首次在干净 48c86c4b 检出上复现；I38 评审再次确认；于 I38 落地时补入。**已于 I57 用 `xfail(strict=True)` 治理（见 8.6 节）：该守卫强制的顶层收敛从未落地本谱系，且无法在不祝福其所禁止的散乱的前提下适配。** | I35/I38 评审 |
| 2 处空战校准漂移红 | `tests/runtime/air_combat/test_component_failure_probability_surface.py::test_mlf5c_direct_hit_load_floor_prevents_blast_tail_valley` 与 `tests/runtime/air_combat/test_live_detonation_event_surface.py::test_live_detonation_exports_standard_warhead_spatial_and_component_events`（签名 `'detonated_no_effect' == 'damage_applied'`）。I38 评审用 2026-07-18 改动前旧二进制直接复现两者——比同二进制 stash 对照更强的固有性证明——确证为与任何已落地迭代无关的本机产品/校准漂移，与 I28 裁定的漂移族同源。 | I38 评审 |
| `platform_spawn` 的 spdlog 采集错误 | `tests/architecture/platform_spawn/test_default_factory_spawn_plan_resolution.py` 收集期报 `Could not find include directory for CMake dependency 'spdlog'`——与上方 flecs 条目同家族但依赖不同、文件此前未列；I44 评审在写集完全无涉 CMake 依赖解析的前提下复现。于 I44 落地时补入。 | I44 评审 |
| `source_evidence_governance` 既有红 | `tests/architecture/damage_model/test_source_evidence_governance.py` 既有失败（单独跑 1 failed+5 errors；混跑 4 failed+5 errors——存在顺序敏感性）。根因链完全在任何已落地写集之外：`tools/maintenance/source_governance/rights_output_policy.py:107` 向 `re.sub` 传入 `None`。`test_source_admission_audit.py` 单独跑 6 passed。由 I44 评审超集扫描暴露；于 I44 落地时补入。**已于 I57 修复（见 8.2 节）：`_pdf_text_probe` 现捕获原始字节并做严格 UTF-8 解码（不可解码输出 fail-close、零声明命中），`_normalize_statement_text` 对 `None` fail-close；单独跑现为 22 passed。** | I44 评审 |

沿用 I34 独立复核并作为本迭代起始基线的门禁计数：维护 smoke
`436 passed, 45 subtests`；聚焦 `world_batch`+leader+facade 选集
`282 passed`、同样 5 条 flecs 红、`1 skipped`、`22 subtests`。

## 6. I34：命令链文本守护适配缺失（wp24）（已于 I39 修复）

于 I37 落地时依据 I37 评审的谱系甄别（逐提交隔离干净检出）登记：

| 项 | 详情 |
| --- | --- |
| 失败节点 | `tests/architecture/runtime_facade/test_tasking_batch_contract_boundaries.py::test_wp24_python_command_chain_business_writes_use_maintained_contracts` |
| 谱系 | `48c86c4b`（I33）绿；自 `c2952d61`（I34）起红；与 I35/I36/I37 写集无关 |
| 机理 | I34 把命令链写调用下沉到 `python/rl/runtime/world_batch/_shared_ops.py`；该守护的合成扫描集（adapter 加 vec_env 合成文本加 cooperative 模块）不含 `_shared_ops.py`，vec_env 合成与 cooperative 两处探针因此转空，而 `adapter.py` 自身 token 仍在 |
| 行为证据 | `test_world_batch_vec_env_command_chain.py` 在各提交均 23/23 绿——维护契约写路径功能完好；属守护适配缺失、非功能回归 |
| 修复方向 | 把 `_shared_ops.py` 纳入守护扫描集（守护意图不变）；归属：T6，记于 I34 名下 |

**姊妹缺口（于 I41 落地时登记，同为 I34 归因）：**
`tests/runtime/mission/test_ground_runtime_lifecycle_bridge.py::GroundRuntimeSourceBridgeTests::test_batch_envs_use_tasking_bridge_for_command_chain_sync`
——由 I41 聚焦回归暴露、经 I41 评审在隔离干净检出上谱系甄别（`48c86c4b`
绿、自 `c2952d61` 起红）：该守护仍断言 vec_env/cooperative 直接从
`bridge.py` 导入 `build_kernel_mission_command`，而 I34 下沉已把该调用移
入 `_shared_ops.py`；I39 修复只覆盖了 wp24 守护文件、未及此处。行为面不受
影响（与上方 wp24 条目同机理）。修复方向：与 I39 同款——把
`_shared_ops.py` 纳入该守护扫描集，守护意图不变。已于 I42 修复。

**现状**：已于 I39 修复。下方 6.1 节记录修复内容与复核。

### 6.1 I39 修复与复核

**修复**：`test_wp24_python_command_chain_business_writes_use_maintained_contracts`
（`tests/architecture/runtime_facade/test_tasking_batch_contract_boundaries.py`）
现在把 `python/rl/runtime/world_batch/_shared_ops.py` 的源码文本拼接进该测
试自身的本地扫描变量 `world_batch_vec_env`/`cooperative_vec_env`
（`world_batch_vec_env_source_text() + "\n" + shared_ops`；cooperative 一
侧则是该模块自身文本再拼接同一份 `shared_ops` 字符串），然后再执行随后
的正向 maintained-token 循环与禁用 legacy-token 循环。改动范围仅限于这一
个测试函数：`tests/architecture/runtime_facade/helpers.py` 中被共享的
`WORLD_BATCH_VEC_ENV_SOURCE_FILES` 元组（仅被另一个测试消费——
`test_scenario_setup_facade_boundary.py::test_wp24_public_vec_env_runtime_compatibility_flag_is_absent_from_maintained_adapters`）
未被触碰，因此没有任何其他守护的扫描集受到影响。新增的行内注释记录了原
因：I34 把两个 vec-env 消费者各自的逐实体命令链 diff 与批量提交调用，都
下沉到了共享的 `_shared_ops.py` 模块中（以
`diff_single_entity_command_chain`/`submit_command_chain_assignments` 形
式导入），因此两个消费者自身的源码文本都不再直接点名 maintained 赋值类/
setter——如今只有 `_shared_ops.py` 里还有。没有放松任何断言；这次修复只
是扩大了既有断言所扫描的文本范围，而且它让禁用 legacy-token 循环变得更
严格（而非更宽松），因为该循环现在也覆盖了两个消费者实际发起写调用的那
个模块。

**负向自证**（针对内存中的副本演练；工作树里的 `_shared_ops.py` 从未被
写入）：一个位于工作树之外的独立脚本导入了真实、未经修改的测试函数，用
`unittest.mock.patch.object` 只拦截 `_shared_ops.py` 这一个路径的
`pathlib.Path.read_text`，让它返回一份被破坏的副本——把
`runtime_adapter.set_pilot_reports_maintained_batch(report_assignments)`
还原为旧式的 `runtime_adapter.set_pilot_reports_batch(report_assignments)`
（其余所有路径的 `read_text` 均照常落到真实文件、不受影响），然后直接调
用该测试函数：

```
--- sanity: guard passes against the REAL (unsabotaged) _shared_ops.py ---
OK: real worktree state is green, as expected.

--- negative self-proof: guard against a SABOTAGED in-memory copy ---
GUARD WENT RED AS EXPECTED. Traceback:
  File ".../test_tasking_batch_contract_boundaries.py", line 295, in
    test_wp24_python_command_chain_business_writes_use_maintained_contracts
    assert "set_pilot_reports_maintained_batch" in source
AssertionError

--- post-check: worktree _shared_ops.py is untouched on disk ---
OK: worktree _shared_ops.py byte-identical to before the rehearsal.
```

**验证**（本工作树，`CMO_BUILD_DIR=<worktree>/build-local-win`）：

```
pytest -q tests/architecture/runtime_facade/test_tasking_batch_contract_boundaries.py
-> 3 passed（此前为 2 passed, 1 failed）

pytest -q tests/architecture/runtime_facade
-> 67 passed, 4 failed——与本台账第 5 节已登记的四个 test_wp22_* 节点完全
   相同（均在 test_runtime_escape_hatches.py 内）；未新增红

pytest -q tests/architecture/policy_execution/test_intent_injection_authority_guard.py
-> 4 passed, 1 failed——与本台账第 5 节已登记的 test_wp12_* 节点相同；不受
   本次修复影响（不同文件，在本次修复写集之外）

python tools/runners/run_pytest_suite.py --suite tests/smoke/ci_smoke_suite.json
-> 439 passed, 45 subtests passed——测于本台账编辑之前。I39 评审对最终
   写集实测为 438 passed / 1 failed（该红即本台账编辑触发的双语注册表
   标记，其哈希刷新按迭代任务书属落地方职责）；已由 I39 落地时的
   registry 刷新解决，落地树复验绿

ruff check tests/architecture/runtime_facade/test_tasking_batch_contract_boundaries.py
-> All checks passed!

git diff --check    -> 干净
```

本次修复的写集：`tests/architecture/runtime_facade/test_tasking_batch_contract_boundaries.py`
（仅守护适配）以及本台账自身的登记（本节）。未改动任何
`python/rl/runtime/world_batch/**` 生产代码——这属于守护适配缺失，不是功
能缺陷。

### 6.2 I42 修复与复核（姊妹缺口）

**修复**：`test_batch_envs_use_tasking_bridge_for_command_chain_sync`
（`tests/runtime/mission/test_ground_runtime_lifecycle_bridge.py`，
`GroundRuntimeSourceBridgeTests`）现在把
`python/rl/runtime/world_batch/_shared_ops.py` 的源码文本读取一次，用
`"\n"` 拼接到两个逐文件扫描文本各自末尾（`vec_env.py`与
`cooperative_world_batch_vec_env.py`各自 `read_text()` 的结果），再执行
该测试原有的那九条 `assertIn`/`assertNotIn` 断言。改动范围仅限于这一个
测试函数：本文件内的其它测试、以及套件中的任何其它守护，都未被触碰。新
增的行内注释（`NOTE(I42)`）记录了原因，采用与 I39 的 wp24 守护修复（上方
6.1 节，`tests/architecture/runtime_facade/test_tasking_batch_contract_boundaries.py`）
相同的本地拼接模式：I34 把两个 vec-env 消费者各自的逐实体命令链 diff 与
批量提交调用——包括本守护要盯防的那次 `build_kernel_mission_command` 调
用——都下沉到了共享的 `_shared_ops.py` 模块中（以
`diff_single_entity_command_chain`/`submit_command_chain_assignments` 形
式导入），因此两个消费者自身的源码文本都不再直接点名
`build_kernel_mission_command` 或 maintained 批量 setter——如今只有
`_shared_ops.py` 里还有。注释同时指出：本守护原有的"vec_env/cooperative
直接从 `bridge.py` 导入"表述，如今是经由两者共享的 `_shared_ops.py` 依赖
满足的，不再是同文件内导入——已按事实更新表述，但没有放松或删除任何断
言：每条正向检查仍要求真实 token 出现在下沉后的调用链某处（`_shared_ops.py`
携带了守护要求的全部五个正向 token、且四个禁用 legacy token 均缺席，修复
前已逐一核对确认——I42 评审另实跑子串检查证明各 maintained 名均不含
legacy 名），每条禁用
legacy-token 检查也变得更严格而非更宽松，因为它现在同样覆盖了实际发起
写调用的那个模块。

**负向自证**（针对内存中的副本演练；工作树里的 `_shared_ops.py` 从未被
写入）：一个位于工作树之外的独立脚本导入了真实、未经修改的
`GroundRuntimeSourceBridgeTests` 测试用例，用
`unittest.mock.patch.object` 只拦截 `_shared_ops.py` 这一个路径的
`pathlib.Path.read_text`，让它返回一份被破坏的内存副本——把其中每一处
`build_kernel_mission_command` 都改名为
`renamed_kernel_mission_command_symbol`（其余所有路径的 `read_text` 均照
常落到真实文件、不受影响），然后通过 `TestCase.debug()` 直接运行该测试
用例：

```
--- sanity: guard passes against the REAL (unsabotaged) _shared_ops.py ---
OK: real worktree state is green, as expected.

--- negative self-proof: guard against a SABOTAGED in-memory copy ---
GUARD WENT RED AS EXPECTED. Traceback:
  File ".../test_ground_runtime_lifecycle_bridge.py", line 129, in
    test_batch_envs_use_tasking_bridge_for_command_chain_sync
    self.assertIn("from python.rl.tasking.bridge import build_kernel_mission_command", text)
AssertionError: 'from python.rl.tasking.bridge import build_kernel_mission_command'
not found in '...renamed_kernel_mission_command_symbol...'

--- post-check: worktree _shared_ops.py is untouched on disk ---
OK: worktree _shared_ops.py byte-identical to before the rehearsal.
```

**验证**（本工作树，`CMO_BUILD_DIR=<worktree>/build-local-win`）：

```
pytest -q tests/runtime/mission/test_ground_runtime_lifecycle_bridge.py
-> 4 passed（此前为 3 passed, 1 failed——本节修复的节点）

pytest -q tests/runtime/mission
-> 90 passed, 8 subtests passed（此前为 1 failed, 89 passed, 8 subtests
   passed——被修复的节点是本目录唯一的红；未见其它节点变化）

python tools/runners/run_pytest_suite.py --suite tests/smoke/ci_smoke_suite.json
-> 446 passed, 45 subtests passed——测于本台账编辑之前。
   `tests/runtime/mission/test_ground_runtime_lifecycle_bridge.py` 不是
   smoke 清单成员（`tests/smoke/ci_smoke_suite.json` 列了另外五个
   `tests/runtime/mission/*` 文件，但没有这一个），因此本守护的红/绿状态
   不会左右这一计数。
   445 passed, 1 failed, 45 subtests passed——测于本台账编辑（本文件及其
   `.zh.md` 对应版本）之后：新增的这一处红即本次编辑自身触发的双语注册表
   哈希标记（`test_document_link_audit.py::test_repository_bilingual_registry_matches_the_maintained_surface`），
   与 I39/I41 落地时同一机理；其 `clusters --write` 刷新按迭代任务书属落
   地方职责，不在本次修复写集之内。`python tools/maintenance/translate_docs_batch.py audit`
   （未带 `--write`，只读比对注册表）确认 `pair_count: 80`、
   `synced: 79`、`diverged: 1`，且
   `plan/unified_architecture_program/t6_residual_ledger`（即本文档对）
   是唯一那条 diverged 条目。

ruff check tests/runtime/mission/test_ground_runtime_lifecycle_bridge.py
-> All checks passed!

git diff --check    -> 干净
```

本次修复的写集：`tests/runtime/mission/test_ground_runtime_lifecycle_bridge.py`
（仅守护适配）以及本台账自身的登记（本节，双语）。未改动任何
`python/rl/runtime/world_batch/**` 生产代码——这属于守护适配缺失、不是功
能缺陷，与本节上级条目所交叉引用的 wp24 姊妹条目同源。

## 7. I41：T3 第二切片——六条 include 方向违规的评估矩阵（1 条收敛，5 条缓办）

I38 把六条既有的 include 方向违规 ratchet 进
`tests/architecture/fixtures/cpp_include_direction_allowlist_20260720.json`
（见 I38 登记行）。I41（T3 第二切片）针对每一条重新评估"本轮可安全收敛"
与"确属结构/设计缺口、应缓办"这一问题，逐条做了完整的消费者/绑定面普查，
并实施了普查后确认低风险的那一条。本节即允许清单自身修订说明所指向的评
估矩阵与处置记录；允许清单各条目也已在自己的 `reason` 字段内联记录了同
样的结论（见 I41 修订后的各条目）。

| 序号 | 边（`from_group` -> `to_group`） | 裁决 | 一句话理由 |
| --- | --- | --- | --- |
| a | `components/combat/common/weapon_common.h:12` -> `models/weapons/kalman_seeker.h` | **收敛** | `SeekerEkfState`/`SeekerEkfParams` 恰好只有四个触点（定义处、一处按值持有、一处数学函数调用、一处直接 include 的测试），且零 Python 绑定；把两个结构体迁移到 components 自有叶子即可用逐字节等价的类型搬移关闭该边。 |
| b | `core/engine/world_batch_runtime.cpp:9` -> `gpu/gpu_interaction_broadphase_runtime.h` | 缓办 | interaction-broadphase 路径内有四处直接调用 `gpu::` 打包类型/函数；关闭此边需要 GPU/engine 集成缝本身，而非类型搬移。 |
| c | `core/engine/world_batch_runtime.h:12` -> `core/mission/episode/execution_episode_controller.h` | 缓办 | `ExecutionEpisodeController` 的批量所有权被 `WorldBatchRuntime` 的九个方法读写；迁移所有权是一项 WP4 热路径设计决策（即 I38 `next_gate` 所指的 facade/mission 自有批量包装器），不是类型搬移。 |
| d | `core/engine/world_batch_runtime.h:13` -> `gpu/gpu_visual_runtime.h` | 缓办 | `WorldBatchVisualBindingCompatibilityScene` 是两个公开 `WorldBatchRuntime` 批量方法的返回/参数类型；与 (b) 同属一个 GPU/engine 集成缝。 |
| e | `core/engine/world_batch_visual_binding_compatibility_helper.h:9` -> `gpu/gpu_visual_runtime.h` | 缓办 | 该 helper 存在的全部意义就是桥接四个 `gpu::render_visual_*` 入口；与 (b)/(d) 同一集成缝，并非偶发 include。 |
| f | `runtime/contracts/world_batch_contracts.h:16` -> `core/mission/episode/execution_episode_batch_prepare.h` | 缓办 | `StepEvaluationBatchConfig`/`StepEvaluationBatchEnvState` 被 `core/mission/episode` 与 `core/mission/runtime` 全线消费，在 `bindings_episode.cpp` 中逐字段单独绑定，且 `EnvState` 本身还按值嵌入另外十个 mission 自有的聚合类型；原样搬移只会反转违规方向，独立定义 contracts 自有镜像类型又需要复制整张嵌套类型图——这是 T1 DTO 族收尾量级的迁移，不是机械搬移。 |

### 7.1 (a) 已收敛：`missile_seeker` 的 EKF 状态迁至 components 叶子

**普查**（`missile_seeker::SeekerEkfState`/`SeekerEkfParams` 及
`missile_seeker::` 自由函数在全仓的所有触点）：`src/models/weapons/kalman_seeker.h`
（定义处，以及操作这两个结构体的 EKF 数学函数）、`src/components/combat/common/weapon_common.h`
（`Missile` 在第 221-222 行按值持有 `ekf_state`/`ekf_params`）、
`src/models/weapons/default_guidance_model.cpp`（调用
`missile_seeker::ekf_init/ekf_predict/ekf_update/ekf_filtered_*/ekf_closing_speed_mps`，
但此前是*经由*
`core/interfaces/guidance_model.h` -> `weapon_common.h` -> `kalman_seeker.h`
这条传递链拿到这些自由函数，自身并未直接 include）、以及
`src/tests/test_kalman_seeker.cpp`（直接 include `kalman_seeker.h`；属于
豁免的 `tests` 组，不受方向策略约束）。两个结构体、以及 `Missile` 本身，
从未经由 `nb::class_<...>` 绑定——对 `src/interfaces/python/*.cpp` 搜索
`Missile`/`ekf` 只命中内部 ECS 的 `.get<Missile>()` 调用，没有任何绑定。
`tools/maintenance/dto_schema` 对两个结构体零引用，故此次搬移不触及
schema/生成器治理面。

**修复**：新增叶子头文件 `src/components/combat/common/missile_seeker_state.h`，
持有 `namespace missile_seeker { struct SeekerEkfState {...}; struct
SeekerEkfParams {...}; }`，与此前 `kalman_seeker.h` 内联定义逐字节等价
（字段名、类型、顺序、默认值均不变——纯粹的文本搬移，非重新设计，因此两
个结构体以及 `Missile` 的 C++ 布局/ABI 在构造上即不受影响，不仅仅是靠测
试证据推断）。`kalman_seeker.h` 现在反向 `#include` 这个叶子（`models ->
components`，策略已允许），不再自行定义两个结构体。`weapon_common.h` 原
本对 `models/weapons/kalman_seeker.h` 的 include 换成对新叶子的 include
（`components -> components`，同组，永远允许）。`default_guidance_model.cpp`
新增了一条直接的 `#include "models/weapons/kalman_seeker.h"`（该文件本就
属于 `models` 组，故不构成新的方向边）——原因是切断 `weapon_common.h` 对
`kalman_seeker.h` 的 include，同时也切断了此前把 EKF 数学函数传递给它的
那条传递链，这是本次搬移必须连带做的"按实际使用补 include"修复，不是可
选项。共触及 4 个文件（1 新增、3 修改）；零 CMake 改动（头文件通过
`ef_core` 的公共 include 目录被发现，未被逐一列举）。

### 7.2 (b)/(c)/(d)/(e) 缓办：GPU/engine 与 mission 批量所有权的设计缺口是真实的，不是机械问题

四者都落在 I38 `next_gate` 文本已经点名的 WP4 热路径/GPU 集成缝上。I41
在缓办前逐一复核确认了这是多处功能耦合，而非偶发 include：(b) 的
`gpu::InteractionBroadphaseConfig`/`InteractionEntityPacked`/`InteractionQueryPacked`
与 `gpu::build_interaction_broadphase_*_batch` 在 `world_batch_runtime.cpp`
的 interaction-broadphase 路径内被四处调用；(c) 的
`std::vector<ExecutionEpisodeController> execution_episode_controllers_`
被 `clear_execution_episode_controller_batch`、
`prime_execution_episode_controller_batch`、
`execution_episode_controller_ready`、
`export_execution_episode_states_batch`、`evaluate_execution_episode_batch`、
`step_execution_episode_batch`、`step_execution_episode_results_batch`，以
及两个私有的 `checked_execution_episode_controller` 重载读写——是九个方
法，不是一个字段；(d) 的 `WorldBatchVisualBindingCompatibilityScene` 是
`collect_visual_binding_compatibility_scenes_from_candidate_ids_batch` 与
`collect_visual_binding_compatibility_scenes_batch` 两个公开批量方法的返
回/参数类型；(e) 的 helper（`world_batch_visual_binding_compatibility_helper.h`）
存在的目的就是构建 `gpu::VisualRenderRequest`/`VisibleObjectPacked` 值并
在 `gpu::render_visual_experiment(_batch_export)` 与
`gpu::render_visual_reference_cpu(_batch)` 之间分支——gpu 依赖就是这个
helper 存在的全部理由。四者都无法靠搬移类型关闭；各自需要的是 GPU/engine
集成缝本身（b/d/e）或 facade/mission 自有的批量包装器（c）——I38
`next_gate` 文本已点名，这是属于 T4（精确运行时对齐，其自身关键风险恰
恰就是这一 WP4 双重所有权过渡期）或下一个 T3 物理拆分切片的架构决策。
本轮维持原状缓办；允许清单各条目的 `reason` 字段已内联记录本次 I41 复核
结论（见允许清单修订说明）。

### 7.3 (f) 缓办：mission/contracts 这对 DTO 是 T1 量级迁移，不是机械搬移

裁决前的完整消费者/绑定面普查：`StepEvaluationBatchConfig`/`StepEvaluationBatchEnvState`
（`core/mission/episode/execution_episode_batch_prepare.h`）被
`core/mission/episode/execution_episode_controller.h`/`.cpp`（`WorldBatchRuntime`
经 `WorldExecutionEpisodeStepRequest.config`/`.env_state` 调用的
`evaluate`/`step`/`step_result` 方法）、
`core/mission/episode/detail/episode_transition_runtime.h`/`.cpp`、以及
`core/mission/runtime/reward_runtime.h` 消费；两个类型都在
`interfaces/python/bindings_episode.cpp` 中被逐字段单独绑定
（`nb::class_<StepEvaluationBatchConfig>`/`<StepEvaluationBatchEnvState>`，
合计 57 次 `def_rw` 调用）；`StepEvaluationBatchEnvState` 本身还按值嵌入
另外十个 mission 自有的聚合类型（`ExecutionEpisodeState`、
`MissionObservationInputs`、`StepInfoInputs`、`SafetyRuntimeInputs`、
`WaypointRewardInputs`、`ApproachRewardInputs`、`ConditionalObjectiveSpec`、
`ConditionalObjectiveInputs`、`ObjectiveShapingConfig`、
`FlightShapingRuntimeInputs`），每个也都单独被绑定，并被四处
`python/rl/runtime/world_batch/**` 调用点消费（`vec_env.py`、
`_observation_mixin.py`、`cooperative_world_batch_vec_env.py`、
`_execution_episode_mixin.py`）。

这份普查把任务书提出的两条备选补救路径都堵死了。若把任一结构体的物理归
属原样迁入 `runtime/contracts`，新的 contracts 头文件就必须
`#include` 它仍按值嵌入的十个 mission 自有嵌套类型中的一个或多个——而
`runtime_contracts` 策略允许的目标集合仅有 `{components}`（见
`tools/architecture/cpp_include_graph.FINE_GROUP_ALLOWED_TARGETS`），因此
这只会把违规反转为一条或多条
`runtime_contracts -> core_mission_runtime`/`core_mission_episode` 的边，
且每一条都比现在这一条更难自证正当（是整个聚合类型按值嵌入，不是两个扁
平的 config/state 结构体）。改为定义一个独立的 contracts 自有传输态类型
虽能避免反转边的方向，但代价是把同一张十类型嵌套图复制一份到第二个名字
下，此后还要手工维持两者同步——用"治理门违规"换成了"静默漂移风险"，而且
这个改动的体量（十个聚合类型、跨两个 Python 绑定文件合计 57+ 个已绑定字
段）与 T1 DTO 族收尾这条主线相当（按 I31/I33/I35 的既有线索，这正是上文
第 4 节已索引的下一个自然的单一来源迁移候选），不是 T3 第二切片量级的机
械搬移。`python/rl/runtime/world_batch/**` 也在本迭代写集边界之外（按本
迭代任务书，I40 正在姊妹工作树中并发使用它）——即便 C++ 侧其他方面均安
全，这一条也独立地排除了本轮触碰 Python 可见绑定形状的可能性。本条缓办；
允许清单条目的 `reason` 字段已内联记录这份完整普查。

### 7.4 验证（本工作树，`CMO_BUILD_DIR=<worktree>/build-local-win`，基线 `b618971f`）

```
cmake --build build-local-win --target ef_core ef_py -j4
-> 成功（增量；仅有第三方 spdlog/nanobind 模板既有警告，与本迭代改动无关）

pytest -q tests/architecture/governance/test_cpp_include_direction.py
-> 7 passed（允许清单条目 6 -> 5；在编辑允许清单之前，门禁已正确把 (a)
   的指纹标记为过期，证明门禁确实检测到了修复本身，而非该修复未经校验）

tools/maintenance/dto_schema/generate.py --check -> 全部产物 up-to-date

ctest（build-local-win） -> 8/8 passed

ef_test.exe --source-file="*test_kalman_seeker*" -> 3 个测试用例、17423
条断言，0 失败（同一套 EKF 数学运算现在作用于搬移后的结构体上）

pytest -q tests/world_batch tests/architecture/runtime_facade
  tests/runtime/bindings tests/runtime/mission tests/runtime/engagement
  tests/architecture/damage_model/test_release_signoff_gate.py
-> 471 passed, 6 failed, 1 skipped, 28 subtests。六个失败经 `git stash`
   核实，在改动前的基线上逐一等同复现：上文第 5 节已登记的四个
   `test_wp22_*` 节点与懒加载 `common.ef_py` 缺口，外加一个此前未登记
   的——`tests/runtime/mission/test_ground_runtime_lifecycle_bridge.py::GroundRuntimeSourceBridgeTests::test_batch_envs_use_tasking_bridge_for_command_chain_sync`
   （断言 `vec_env.py`/`cooperative_world_batch_vec_env.py` 仍从
   `python.rl.tasking.bridge` 导入 `build_kernel_mission_command`；两者
   现在都改经 `_shared_ops.py` 做命令链同步，与第 6 节已登记的 I34 下沉
   同源——看起来是另一个测试文件里的姊妹级守护缺口，第 6 节的 I39 修复
   未覆盖到它）。已确认与本迭代改动无关（stash 掉本迭代改动后依然复现
   为红）且在本迭代写集边界之外（该测试与 `vec_env.py`/`bridge.py` 均未
   被本迭代触碰）；此处仅如实记录以便可见，本节不对其做裁决或修复。

python tools/runners/run_pytest_suite.py --suite tests/smoke/ci_smoke_suite.json
-> 446 passed, 45 subtests passed（与本迭代起始的 I38/I39 基线一致，无
   变化）

跨构建 parity：(b)-(f) 各边所涉类型在别处确有 Python 绑定
（`gpu::InteractionBroadphaseConfig`/packed 视图在 `bindings_gpu.cpp`、
`ExecutionEpisodeController` 在 `bindings_episode.cpp`、
`StepEvaluationBatchConfig`/`EnvState` 如第 7.3 节所引为逐字段绑定），但
这五条边本轮零触碰、其绑定面按构造不受影响；本轮唯一实施的搬移 (a) 仅涉
`Missile`/`SeekerEkfState`/`SeekerEkfParams`，三者从未被绑定——对
`src/interfaces/python/*.cpp` 搜索找不到任何 `nb::class_<Missile>` 或以
`ekf` 命名的绑定调用。（措辞于 I41 落地时按评审更正：原"六条边类型零绑
定"的说法与第 7.3 节自引的 (f) 绑定相矛盾。）既然本迭代唯一实施的这一次搬移实际影响的 Python
绑定类数量为零，"受影响类"这一 parity 集合按构造即为空集；作为方法学自
证与构建健康检查，另外抓取了两个哨兵 contracts 类
（`WorldEntityRef`、`TypedPlatformSpawnRequest`）在旧构建产物
`D:\workshop\Research\Echelon-Forge\build-local-win`（2026-07-18）与本工
作树重建后的 `ef_py` 之间的 `dir()` 及深度 4 递归默认值快照：两个字段
（`dir_public`、`default_value_snapshot`）在两个类上均逐字节一致，证明
对拍方法本身可靠，且本工作树的重建未引入任何偶发的 Python 侧表面漂移。

ruff check .        -> All checks passed!
git diff --check    -> 干净
```

本节已收敛修复的写集：`src/components/combat/common/missile_seeker_state.h`
（新增）、`src/components/combat/common/weapon_common.h`、
`src/models/weapons/kalman_seeker.h`、
`src/models/weapons/default_guidance_model.cpp`（共 4 个文件），外加允许
清单 fixture（删除 1 条、修订余下 5 条）与本台账小节。未触碰任何
`python/**` 或 `examples/**`；无 CMake 目标改动。

## 8. I57：T6 第二清偿包（七条处置）

基线提交 `fae17eb8`；在本工作树上针对只读共享 CPU 快照核验
（`CMO_BUILD_DIR=D:\workshop\Research\EF-w2-training\build-local-win`；未触发
任何 CMake/构建，写集为纯 Python/JSON/文档）。本迭代逐条复现了第 5 节所追踪
的七个可治理红，逐条从源码定根因（不照抄第 5 节既有假设），并按性质处置。
值得注意的是：第 5 节曾将三条红初判为"重构落在别的谱系、从未进本分支"，但
直接检查发现它们其实是"重构**确已**落地本分支、只是守卫扫了搬移前的位置/写
法"——故按 I39/I42 先例做**守卫适配到绿**，而非上 xfail。只有一条 lineage 红
（第 7 条）确实无法适配，用 `xfail(strict=True)` 治理。

### 8.1 处置汇总

| 序号 | 节点/目标 | 复现的红 | 根因（源码证据） | 处置 |
| --- | --- | --- | --- | --- |
| 6 | `test_source_evidence_governance.py`（整文件） | 单独跑 `1 failed, 16 passed, 5 errors` | `rights_output_policy.py` 把 `None` 的 `result.stdout` 传入 `re.sub`（第 107 行）：`text=True` 用本机 Windows 控制台编码（GBK）解码 pdftotext 的合法 UTF-8 输出；reader 线程在 UTF-8 连字符序列（`e2 80 93`，其 `0x93` 字节处）中途崩溃，`result.stdout` 变为 `None` | **真缺陷修复→绿**（8.2） |
| 1 | `runtime_facade/test_runtime_escape_hatches.py` 的四个 `test_wp22_*` | `4 failed` | 每个都只在"定义位于 `bridge.py`"这条断言失败；I24 已把 loader-owned 接缝类/函数搬入 `python/tasking_contracts/bridge_views.py`（bridge.py 现在 re-export 同一批对象）——rg 确认全部定义在此、且各消费端文件早已使用命名接缝 | **守卫适配→绿**（8.3） |
| 2 | `policy_execution/test_intent_injection_authority_guard.py::test_wp12_runtime_facade_does_not_gain_a_second_maintained_injection_api` | `1 failed` | `run_window` API 存在（`runtime_facade.h:116`），coordinator 携带全部被断言 token；唯一差异是 C++ `&` 绑定风格（`const RuntimeWindowRequest &request` vs 守卫的 `RuntimeWindowRequest& request`） | **守卫适配→绿**（8.4） |
| 3 | `runtime/bindings/test_lazy_binding_resolution.py::...::test_common_import_prefers_repo_build_ef_py` | `AttributeError: ... has no attribute 'ef_py'` | 本谱系经私有懒加载 `_ef_py()` 解析 ef_py（无模块级 `ef_py` 属性；rg 全仓零生产消费者引用 `common.ef_py`） | **守卫适配→绿**（8.5） |
| 7 | `governance/test_tools_script_governance.py::test_diagnostics_top_level_entrypoints_are_governed_by_function` | `1 failed`（多出 11 个顶层脚本） | diagnostics"按功能治理"的顶层收敛（收敛到 15 项批准集）从未落地本谱系；扩允许清单会祝福该守卫本要禁止的散乱 | **`xfail(strict=True)`**（8.6） |
| 5 | `gpu/test_cuda_import_order.py::...::test_world_batch_vec_env_import_after_torch_runtime_setup` | `1 failed`（`ModuleNotFoundError: ef_py`） | 测试硬编码了 CPU-only 工作树永不生成的 `build-gpu/` GPU CUDA 构建树 | **条件 skip**（8.7） |
| 4 | `run_scenario_contract.py --spec .../leader_phase_manager_approach_arm.json` | `expected approach-arm transition count mismatch: 0` | 纯 Python 相位管理器分歧：本谱系 `RuleBasedLeaderPhaseManager` 以 `approach_arm_require_runway_frame=True` 经 `loader.get_runway_local_frame(...)` 门控 arming，而契约脚手架 `FakeLoader` 从未实现它（其 `_activate_post_waypoint_transition(self)` 也早于当前 `sync_to_kernel=` 调用约定） | **分类（lineage；脚手架落后）**（8.8） |

### 8.2 第 6 条——真缺陷修复：源权 PDF 探针 None/locale 解码

**根因**：`tools/maintenance/source_governance/rights_output_policy.py::_pdf_text_probe`
运行 `subprocess.run(["pdftotext", ...], capture_output=True, text=True)`。
`text=True` 用控制台 locale 编码解码子进程 stdout，本机 Windows 为 GBK。
pdftotext（MiKTeX）把 retained DENIX PDF 的页文本输出为**合法 UTF-8**
（事实于 I57 评审轮更正、本迭代已直接复核：对两个 retained PDF 的原始探针
字节做严格 UTF-8 解码均成功——TP-20 14,413 字节、TP-21 14,204 字节；GBK
报错 `'gbk' codec can't decode byte 0x93 in position 70` 点名的 `0x93` 字节
位于偏移 70 处的 UTF-8 连字符 `e2 80 93` 内（`b"r \xe2\x80\x93 Op"`），并非
本节最初所称的 cp1252 智能引号）；GBK reader 线程在该多字节序列中途抛
`UnicodeDecodeError`，于是 `result.stdout` 变为 `None`。
`_public_distribution_statement(None)` 随后走到
`_normalize_statement_text`（第 107 行）调用 `re.sub(r"\s+", " ", None)`
→ `TypeError: expected string or bytes-like object, got 'NoneType'`。整文件跑
为 `1 failed, 16 passed, 5 errors`（module 级 `source_rights_policy_bundle`
fixture 在 setup 崩溃，连累五个消费者 error；CLI 测试经子进程同样崩溃）——且
该文件的权利清单断言还要求 PDF 声明被真正识别
（TP-20 的 `statement_id == "distribution_statement_a_public_release_unlimited"`、
TP-21 的 `"public_release_distribution_unlimited"`），故仅做 None→fail-closed
的补丁不足以让文件转绿。

**修复**（生产，纯 Python；于 I57 评审轮加固）：`_pdf_text_probe` 现改为捕获
原始字节（去掉 `text=True`）并做**严格** UTF-8 解码；遇 `UnicodeDecodeError`
时返回专用的 fail-closed 形态
（`extraction_status="pdf_text_probe_decode_error_fail_closed"`、全部声明标志
`False`、保留 `statement_locator`），沿用 `pdftotext_missing`/`timeout` 分支的
既有约定——不可解码的输出永远不可能产生权利声明命中。I57 首版补丁曾用
`errors="ignore"` 解码；独立评审证明其**失败开放**——伪造字节流在权利短语内
夹入畸形字节（`b"RE\xffLEASE"`）时该字节被静默删除、短语被拼回 `"RELEASE"`，
误命中 `statement_id="public_release_distribution_unlimited"`（本轮已在进程内
复现）——且该有损解码也无必要，因为真实 payload 输出本就是合法 UTF-8（见上
方更正后的根因）；有损解码已在本迭代内替换为"严格解码、失败即 fail-closed"。
`_normalize_statement_text` 保留 `None`/空值守卫，fail-close 到 `""`（把调用
方契约的"无可提取声明"情形钉到与 `pdftotext_missing`/`timeout` 分支相同的判
定）。用修复后的探针端到端跑真实 retained payload（真实 pdftotext）确认严格
路径成功：TP-20 识别为 `distribution_statement_a_public_release_unlimited`、
TP-21 识别为 `public_release_distribution_unlimited`。

**聚焦单测**（新增 `tests/architecture/damage_model/test_rights_output_policy_probe.py`，
9 个测试，密闭——monkeypatch `subprocess.run`，无需真实 pdftotext/payload）。
伪 `subprocess.run` 桩自身锁定捕获模式：断言探针传了 `capture_output=True`、
且从不传 `text=True`/`universal_newlines=`/`encoding=`/`errors=`（评审修复：
首版桩忽略 kwargs、无论如何都返回 bytes，未来若有人加回 `text=True`，测试
仍绿而真实路径崩）。覆盖面：`None`/空值归一化；`None` 声明评估 fail-closed；
合法多字节 UTF-8 的严格解码（镜像真实 TP-20 内容的连字符 payload）识别出正
确 `statement_id`；TP-21 式 id；评审的伪造畸形字节流 fail-closed 且零命中；
`stdout=None` 不崩溃且零命中；缺二进制分支。测试性质口径（更正本节最初
"每条测试修复前均红"的说法——评审证实其中三条在基线即绿）：**六条**为新行
为钉扎、对修复前模块为红（`..._tolerates_missing_text`、
`..._none_is_fail_closed`（声明）、`..._decodes_utf8_multibyte_text`、
`..._public_release_without_statement_a`、`..._malformed_bytes_fail_closed`、
`..._none_stdout_is_fail_closed`）；**三条**为回归守卫、修复前即绿、钉住不变
行为（`..._collapses_whitespace_and_uppercases`、`..._detects_statement_a`、
`..._missing_binary_is_fail_closed`）。评审场景的红→绿（进程内演示）：对临时
`errors="ignore"` 逻辑，伪造流得 `statement_detected=True` /
`statement_id='public_release_distribution_unlimited'`（失败开放）；对严格解
码修复，同一流在探针内抛
`UnicodeDecodeError: ... can't decode byte 0xff in position 22`，fail-close
零命中（新增 `test_pdf_text_probe_malformed_bytes_fail_closed` 钉住的正是这
一行为）。原 `None` 路径红证据仍成立：修复前的
`_normalize_statement_text`/`_public_distribution_statement(None)` 抛出完全
相同的 `TypeError: expected string or bytes-like object, got 'NoneType'`。

**验证**：

```
pytest -q tests/architecture/damage_model/test_rights_output_policy_probe.py
-> 9 passed（6 条新行为钉扎修复前红；3 条回归守卫修复前绿）

pytest -q tests/architecture/damage_model/test_source_evidence_governance.py
-> 22 passed   （此前 1 failed, 16 passed, 5 errors；严格解码加固后复验）
```

混跑（顺序敏感性）在 8.10 的整 `damage_model` 扫描中复验。

### 8.3 第 1 条——守卫适配：四个 wp22 loader-owned 接缝守卫

**根因（源码证据）**：`tests/architecture/runtime_facade/test_runtime_escape_hatches.py`
中的四个 `test_wp22_*` 守卫全部只在"某接缝**定义**位于
`python/rl/tasking/bridge.py`"这条断言失败（如 `class LoaderOwnedRuntimeView:`、
`class LoaderOwnedScriptedOpponentKernelView:`、
`def apply_loader_owned_world_layout_to_kernel(...)`）。bridge.py 自身头部注释
记载 I24 已把这些 loader-owned 运行时视图与 profile-无关的命令链/任务命令接缝
helper 搬入中立的 `python/tasking_contracts/bridge_views.py`；bridge.py 现在导入
并 re-export 同一批对象。rg 确认每一处被断言的定义（类在 bridge_views.py:88/177、
`get_unit_position/velocity`/`is_unit_active` 在 140/143/146、
`loader_owned_runtime_view`/`loader_owned_scripted_opponent_kernel_view`/
`apply_loader_owned_world_layout_to_kernel` 在 233/237/241、四个
`sync_task_order/leader_intent/pilot_report/mission_command` 方法在 124-136、
`sync_loader_mission_command`/`sync_loader_command_chain_reentrant` 在 312/335）
都在 bridge_views.py，而每个被断言缺席的 forbidden/legacy token
（`loader_owned_raw_sim_compat`、`LoaderOwnedRawSimCompatibilityFacade`、
`*_compat`、`loader.sim.set_*`）在两文件均零命中。消费端断言（naval_screen.py/
scripted_opponents.py/loading.py 早已使用命名接缝、无 raw `loader.sim.*`）本就通过。

**处置（守卫适配，I39/I42 先例，不减弱任何断言）**：
`tests/architecture/runtime_facade/helpers.py` 新增 `TASKING_BRIDGE_VIEWS` 常量与
`_tasking_bridge_source()` helper，返回 bridge.py 文本拼接 bridge_views.py 文本；
四个守卫的 `bridge_text`/`text` 改从它读取。每个正向 token 仍要求出现在合并接缝
文本中；每个 forbidden token 现在要求在**两个**文件均缺席，负向检查因此增强而非
放松。这与 I39/I42 对 `_shared_ops.py` 命令链下沉所做的"写调用搬到姊妹模块、扩
扫描集"完全同款。

结果：`test_runtime_escape_hatches.py` `4 failed -> 0 failed`。

### 8.4 第 2 条——守卫适配：wp12 facade run_window 签名

**根因（源码证据）**：RuntimeWindow 机制在本谱系完整存在。`runtime_facade.h:116`
声明 `RuntimeWindowResult run_window(const RuntimeWindowRequest &request);`；
`runtime_window_coordinator.h` 携带 `classify_runtime_window_inputs`（第 55 行）、
`"source_layer is required"`（77）、`"input_snapshot_version is required"`（82）；
同文件三个 wp12 的 C++ 编译测试通过；facade 头也不含任何 forbidden 的"第二注入
API"token。守卫唯一失败的断言与源码仅差 C++ 引用绑定风格：它期望
`RuntimeWindowRequest& request`（`&` 贴类型），本谱系风格为
`RuntimeWindowRequest &request`（`&` 贴变量名）——同一声明。

**处置（守卫适配，不减弱断言）**：那一条 `run_window` 断言现在对 needle 与头文件
都折叠引用参数间的空格（`" &"`/`"& "` → `"&"`）后再比较。守卫仍要求
`RuntimeWindowResult run_window(const RuntimeWindowRequest&)` 这一声明确切存在——
只容忍语义无关的 `&` 绑定风格。未触碰 C++（守红线）。结果：守卫通过。
（更正第 5 节 I35 备注：该 `test_wp12_*` 节点位于
`tests/architecture/policy_execution/test_intent_injection_authority_guard.py`，
而非 `test_runtime_escape_hatches.py`。）

### 8.5 第 3 条——守卫适配：diagnostics common ef_py 解析

**根因（源码证据）**：`tools/diagnostics/common.py` 经私有 `_ef_py()` helper 懒加载
ef_py（函数内 `ensure_repo_imports()` 后 `import ef_py`）；不暴露任何 eager 的模块级
`ef_py` 属性，故 `common.ef_py` 抛 `AttributeError`。rg 全仓发现 `common.ef_py`
只被该测试与本台账引用——零生产消费者。这与该文件自身的懒绑定主题一致（同模块的
姊妹测试正是验证各模块把 ef_py 绑定推迟到运行时使用）。

**处置（守卫适配，意图保留）**：断言改为 `self.assertEqual(common._ef_py(), ef_py)`
——即本谱系实际暴露的解析 API。这保留了原意（"common 优先用 repo-build 的 ef_py"）
而不减弱它；周边检查（模块路径位于 `build_dir` 下、`ConditionalObjectiveProperty`/
`WorldBatchRuntime` 存在）保持不变。结果：该节点通过。

### 8.6 第 7 条——xfail(strict)：diagnostics 顶层收敛缺口

**根因（源码证据）**：`test_diagnostics_top_level_entrypoints_are_governed_by_function`
断言顶层 `tools/diagnostics/*.py` 集合等于 15 项的 `APPROVED_DIAGNOSTICS_TOP_LEVEL`。
实际集合多出 11 个未治理脚本（`kill_chain_decoupling_probe`、
`kill_chain_expectation_harness`/`_response_diagnosis`/`_stage_attribution`/`_visualize`、
`kill_chain_guidance_mechanism_ablation`/`_exact_mechanism_ablation`、
`lethality_chain_contract`、`mlf9_statistical_trends`、`structural_breakup_export`、
`calibration_admission_audit`）：该守卫所强制的"按功能治理"顶层收敛从未落地本谱系。

**处置（`xfail(strict=True)`，I28 先例，不删测试）**：这是唯一无法适配到绿的
lineage 红——把这 11 个额外脚本扩进允许清单会祝福该守卫本要禁止的顶层散乱（其中
`kill_chain_expectation_stage_attribution` 还会命中守卫自身的 `stage` 禁名部件检查），
故守卫意图在此确实未被满足、而非仅被搬移。测试带
`@pytest.mark.xfail(strict=True, reason=...)`，reason 机器可读、点名缺失的收敛重构
并指向本台账。strict 意味着未来某次 diagnostics 收敛会把它翻为 `XPASS(strict)` 失败，
提示移除该标记。该文件另外三个治理测试保持绿。

### 8.7 第 5 条——条件 skip：tests/gpu build-gpu 缺失

**根因**：`test_world_batch_vec_env_import_after_torch_runtime_setup` 把 `build-gpu/`
硬编码进 `PYTHONPATH` 并起子进程导入 `world_batch_vec_env`（进而 `ef_py`）。CPU-only
工作树（本树把 `CMO_BUILD_DIR` 指向共享 `build-local-win` CPU 快照）从不生成
`build-gpu/`，故子进程抛 `ModuleNotFoundError: No module named 'ef_py'`。

**处置（条件 skip，非无条件）**：该方法现带
`@unittest.skipUnless(os.path.isdir(_BUILD_GPU), reason=...)`，reason 机器可读、指向
本台账的 build-gpu 缺失环境条目。在 GPU 构建树上检查照常运行；在 CPU-only 树上报
`SKIPPED` 而非误红。

### 8.8 第 4 条——分类：leader_phase_manager_approach_arm 契约

**根因（源码证据）**：该检查为纯 Python。其处理器
（`python/testing/contracts/unit/leader.py::leader_phase_manager_approach_arm`）构造
`FakeLoader`，在 `RuleBasedLeaderPhaseManager.reset()` 后断言
`loader.transition_calls == 1`。`transition_calls` 仅当管理器调用
`loader._activate_post_waypoint_transition(...)` 时递增，而这由 `_should_arm_approach(...)`
门控。本谱系（`python/rl/tasking/leader_tasking.py`）该门控默认
`approach_arm_require_runway_frame=True`（第 315 行），并在 `loader.get_runway_local_frame(...)`
不产出有效帧时返回 `False`（第 702 行）——而脚手架 `FakeLoader` 从未实现
`get_runway_local_frame`（`try/except` 令 `valid_runway_frame=False`），故 arming 从不
触发、`transition_calls` 恒为 `0`。另外，管理器现在调用
`_activate_post_waypoint_transition(sync_to_kernel=...)`，这一 kwarg 是脚手架的
`_activate_post_waypoint_transition(self)` 不接受的——即便 arming 触发脚手架也会抛。
两点都表明契约脚手架（spec + `FakeLoader`）建模的是比本谱系相位管理器更旧的 leader
协议。

**处置（分类；JSON/runner/脚手架/生产均不动）**：这是契约脚手架与生产相位管理器逻辑
之间的谱系分歧，既非校准漂移、非 C++/二进制行为，也非明显零风险的 spec 缺陷（要转绿
需在脚手架里伪造 runway-frame 几何并更新下沉签名——既非零风险、也不在"spec 明显缺陷"
修复通道内，而改动相位管理器生产逻辑按红线属越界）。按契约红指引，此处带证据登记、
保持不动。由于这是独立的契约 runner 检查（非 pytest 节点），无法用 xfail 治理；它作为
已归因、已登记的 lineage 红保留，直至未来某轮把契约脚手架与 runway-frame arming 协议
重新对齐（修复方向：给 `FakeLoader` 补 `get_runway_local_frame`、令
`_activate_post_waypoint_transition` 接受 `sync_to_kernel=`，再提供满足
`approach_arm_along_min_m`/`approach_arm_cross_abs_max_m` 的 runway 几何）。

### 8.9 全目录扫描新暴露的环境红

跑整个 `tests/architecture/damage_model` 目录（此前门禁只跑定向文件）暴露了一个在七条
范围之外的双成员红家族：
`test_candidate_artifact_contracts.py::test_candidate_retained_artifact_pack_writes_retained_files`
（第 611 行）与
`test_component_probability_artifacts.py::test_component_probability_retained_artifact_pack_writes_retained_files`
（第 655 行）都断言 `loaded["manifest_relative_path"].endswith("retained_pack/manifest.json")`，
但在 Windows 上该值以 `retained_pack\manifest.json`（反斜杠分隔符）结尾，故 POSIX 斜杠
后缀检查失败。（对该目录 `rg '\.endswith\("[^"]*/[^"]*"\)'` 确认这两条即完整家族。）
这是测试断言里的 Windows 路径分隔符（OS 条件）红，与任何已落地写集及本迭代改动无关
（它们走 `retained_pack`/`component_probability` 生成器，而非源权治理模块）。归为环境类
（与 flecs/spdlog/校准红同属"只分类"家族）；本迭代不触碰。

同一次扫描还暴露了一条范围外的红：
`test_component_fragility_validation.py::test_fragility_benchmark_compares_candidate_to_synthetic_sigmoid`：
其 `synthetic_sigmoid_probability` 行来自 `component_fragility_benchmark._comparison_rows`
的 `baseline["baseline_component_failure_probability"]`，即二进制计算的组件失效概率面，现读作
~0.170-0.173，对照测试硬编码的 `0.35168` 参考（最大相对差 1.07）。这是与第 5 节已追踪的两条
空战校准漂移红（`test_component_failure_probability_surface.py` 等）同族的、二进制驱动的组件失效
概率产品/校准漂移，而非路径/逻辑问题——归为环境类（校准），保持不动。合计：
`tests/architecture/damage_model` 收尾为 `3 failed, 263 passed`（评审轮严格解码加固后重跑；
比首轮多 1 passed，因探针文件由 8 条增至 9 条），三条失败全为环境类（两条 Windows
路径分隔符 + 一条校准漂移）；第 6 条的 `test_source_evidence_governance.py`（22）与新增
`test_rights_output_policy_probe.py`（9）在本次混跑中皆绿（第 5 节所标的顺序敏感性已消解）。

### 8.10 验证（本工作树，`CMO_BUILD_DIR=<共享 CPU 快照>`）

逐条红→绿（或已治理）证据见 8.2-8.8 内联。合并门禁：

```
pytest -q tests/architecture/runtime_facade tests/architecture/policy_execution
       tests/runtime/bindings tests/architecture/governance
-> 233 passed, 1 xfailed, 1 failed。xfail 是第 7 条。那一条失败是
   test_document_link_audit.py::test_repository_bilingual_registry_matches_the_maintained_surface
   ——本次台账编辑自身触发的双语注册表哈希标记（按迭代任务书属落地方
   `clusters --write` 职责，非修复回归）。第 1/2/3 条皆绿；无其它红。

pytest -q tests/architecture/damage_model
-> 3 failed, 263 passed（评审轮严格解码加固后重跑；探针文件 8 -> 9 条）。
   三条失败全为环境类、且在七条范围之外（见 8.9 节）：两条 Windows 路径
   分隔符红 + 一条组件脆性校准漂移红。第 6 条的
   test_source_evidence_governance.py（22）与新增
   test_rights_output_policy_probe.py（9）在本次混跑中皆绿。

pytest -q tests/gpu/test_cuda_import_order.py
-> 1 skipped   （第 5 条条件 skip）

ruff check .        -> All checks passed!
git diff --check    -> 干净
python tools/maintenance/translate_docs_batch.py audit   （只读）
-> pair_count 86, synced 85, diverged 1（本台账对为唯一 diverged 条目）
```

全量 smoke（`tools/runners/run_pytest_suite.py --suite tests/smoke/ci_smoke_suite.json`）：
`1 failed, 458 passed, 45 subtests passed`。smoke 清单有意保持不变（被适配的守卫均非 smoke
成员，新增聚焦探针测试也刻意不纳入——以匹配该套件既有的"不含源权治理测试"惯例与速度预算）。
那一条失败——以及 `458` 相对 `459`-passed 基线——正是本次台账编辑触发的双语注册表哈希标记
（`test_document_link_audit.py::test_repository_bilingual_registry_matches_the_maintained_surface`），
其 `clusters --write` 刷新按迭代任务书属落地方职责。

### 8.11 写集（本迭代）

- `tools/maintenance/source_governance/rights_output_policy.py`（第 6 条生产修复）
- `tests/architecture/damage_model/test_rights_output_policy_probe.py`（第 6 条聚焦单测，新增）
- `tests/architecture/runtime_facade/helpers.py`（第 1 条扩扫描集：`TASKING_BRIDGE_VIEWS` + `_tasking_bridge_source()`）
- `tests/architecture/runtime_facade/test_runtime_escape_hatches.py`（第 1 条守卫适配）
- `tests/architecture/policy_execution/test_intent_injection_authority_guard.py`（第 2 条守卫适配）
- `tests/runtime/bindings/test_lazy_binding_resolution.py`（第 3 条守卫适配）
- `tests/architecture/governance/test_tools_script_governance.py`（第 7 条 xfail-strict）
- `tests/gpu/test_cuda_import_order.py`（第 5 条条件 skip）
- `docs/plan/unified_architecture_program/t6_residual_ledger.md` / `.zh.md`（本节 + 第 5 节状态更新）

未触碰 C++、`examples/**`、`docs/plan/repository_consolidation/**`、契约 JSON 或契约 runner；
未触发 CMake/构建。

## 相关

- [仓库整合计划](../repository_consolidation/README.zh.md)（上文引用的
  I28、I31、I33、I34 登记行）
- [SCAL 一致性普查（2026-07-20）](scal_conformance_census_20260720.zh.md)
  （同为 `reference` 类型的登记文档；本文档的结构先例）
- `tests/runtime/air_combat/weapon_guidance_realism/README.md`（第 1 节引
  用的 wrapper/mixin 收集契约）
- `tests/architecture/fixtures/cpp_include_direction_allowlist_20260720.json`
  （I38/I41 ratchet 允许清单；上文第 7 节即本台账对 I41 修订的记录）
