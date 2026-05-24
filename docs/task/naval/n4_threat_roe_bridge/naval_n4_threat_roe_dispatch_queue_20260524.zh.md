# 海军 N4 威胁 / ROE 分发队列

状态：`2026-05-24`，在 owner 批准展开分发工作后打开的活跃分发队列。

语言：

- 英文规范版：[`naval_n4_threat_roe_dispatch_queue_20260524.md`](naval_n4_threat_roe_dispatch_queue_20260524.md)
- 中文伴随版：`naval_n4_threat_roe_dispatch_queue_20260524.zh.md`

输入：

- [N4 威胁 / ROE 桥接 README](README.zh.md)
- [N4 威胁 / ROE 桥接任务簇](naval_n4_threat_roe_bridge_cluster_20260524.zh.md)
- [子代理使用政策](../../../standards/governance/subagent_usage_policy.zh.md)

## 范围边界

本队列激活任务簇文档中的有限簇计划。它不会把 N4 桥接扩大成武器交战或毁伤。

第一批分发：

- `N4-B0 Threat / ROE Source Inventory`：归属于 `N4-B` 的只读诊断。它可以
  帮助后续收窄 N4-B/N4-C 写入范围，但不解锁闭合。
- `N4-A1 Scenario / Contract Boundary`：第一个实现 worker，负责
  `ddg51_take1_screen_threat_roe_v1` 的场景与合同边界。

门控工作：

- `N4-B1 Threat / ROE Semantics` 等待 N4-A 边界和 B0 source inventory。
- `N4-C1 Runtime / Facade Evidence` 等待 N4-A 和收窄后的写入范围。
- `N4-D1 RL Task Surface Preflight` 等待 N4-A/B 语义被接受。
- `N4-E1 Integration / Acceptance` 在实现 packets 之后串行执行。

## 队列

| Dispatch | Cluster | 状态 | Model / reasoning | Owner type | 写入范围 | 并行安全 | 预期 packet |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `N4-B0 threat/ROE source inventory` | `N4-B Threat / ROE Semantics` | pass / 只读 | inherited parent model，medium | diagnostics explorer | 只读 source/test/docs inspection | 是；不编辑文件且不解锁闭合 | 已返回字段 inventory、source anchors、最小写入范围建议、架构风险 |
| `N4-A1 scenario contract boundary` | `N4-A Scenario / Contract Boundary` | pass / 已接受 | `gpt-5.4`，high | implementation worker | `scenarios/naval/ddg51_take1_screen_threat_roe_v1.json`；`tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json`；`python/testing/contracts/unit/comm.py`；仅在需要时触及 `tests/runtime/naval/` 聚焦测试 | 否；这是第一个阻塞实现边界 | 已返回 pass packet；主线程已重跑合同和 naval screen tests |
| `N4-B1 threat/ROE semantics` | `N4-B Threat / ROE Semantics` | pass / 已接受 | `gpt-5.4`，high | implementation worker | 在 `N4-A1` 和 `N4-B0` 后收窄；预期文件族为 command shared-core、naval profile、loader runtime-state fallback、command bindings 和聚焦 mission/binding tests | 本轮不并行；接受前阻塞 N4-C | 已返回 pass packet；主线程已重跑构建、聚焦测试和 N4/N3 合同 |
| `N4-C1 facade/world-batch evidence` | `N4-C Runtime / Facade Evidence` | 门控 | `gpt-5.4`，high | implementation worker | 在 `N4-A1` 后收窄；预期文件族为 world-batch command-chain cache、vec-env tests、facade guards | 可能，仅在与 N4-B 写入范围不重叠后 | maintained projection 证据和 guard 结果 |
| `N4-D1 RL preflight surface` | `N4-D RL Task Surface Preflight` | 门控 | `gpt-5.4`，medium | docs / design worker | 本子项目 docs 或后续明确命名的 RL task doc | N4-A/B 语义接受后可并行 | observation/action/reward/termination 草案，不声明 learned policy |
| `N4-E1 integration and acceptance` | `N4-E Integration / Acceptance` | 门控 / 串行 | `gpt-5.4`，high | integration owner | 仅分发时命名的 naval docs 和 acceptance/status 文件 | 否 | 验证汇总、README/current-progress 同步、残留登记、N5 打开/阻塞决策 |

## 活跃 Worker Packet

### N4-B0 Threat / ROE Source Inventory

状态：pass / 只读诊断已完成。没有修改文件。

Packet：

```md
Cluster: N4-B Threat / ROE Semantics
Dispatch: N4-B0 threat/ROE source inventory
Model / reasoning: inherited parent model, medium
Round cap: 1 diagnostics round
Goal: inventory existing threat state, ROE / engagement authority, assigned
target, and track-provenance surfaces.
Write scope: none; read-only.
Non-goals: implementation, scenario edits, contract edits, facade changes.
Validation: source anchors and test/doc paths only.
Closure gate: return field inventory, minimal N4-B/N4-C write-scope
recommendation, and architecture risks. This does not unlock N4-E closure.
Parallel/dependency: parallel-safe with N4-A1 because it is read-only.
```

返回 inventory 摘要：

- 现有 maintained ROE/authority/target 字段已经存在于 `MissionCommand`
  shared core、`LeaderIntentCore`、Python bindings、naval profile、episode JSON
  roundtrip 和 world-batch maintained contracts。
- 尚无专用 `threat_state` 字段。最接近的输入是 track 的 `classification`、
  `source`、`quality/confidence`、`source_time_s`、`update_age_s` 和
  `snapshot_version`。
- 尚无专用 assigned-target provenance 字段。最接近的 maintained 证据是
  `TrackPacket` 的 source/timing/snapshot 数据，以及 facade packet
  provenance。
- N4-B 应增加显式 maintained threat state 与 assigned-target provenance
  语义，而不是把 loose scenario JSON 或 raw whole-shell mission command 当成
  owner。
- N4-C 应证明这些字段能通过 maintained facade/world-batch projection 存活。
- 已知风险：`gym_envs/scenario_loader/runtime_state.py` 在没有 canonical
  mission-command JSON 的 fallback 路径中可能丢失 `roe_state` 和
  `engagement_authority_*`。

### N4-A1 Scenario / Contract Boundary

状态：pass / 已接受。主线程已本地重跑验证命令。

Packet：

```md
Cluster: N4-A Scenario / Contract Boundary
Dispatch: N4-A1 scenario contract boundary
Model / reasoning: gpt-5.4, high
Round cap: 2 implementation rounds before re-scope
Goal: implement the first N4 bridge boundary for
ddg51_take1_screen_threat_roe_v1.
Write scope:
- scenarios/naval/ddg51_take1_screen_threat_roe_v1.json
- tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json
- python/testing/contracts/unit/comm.py
- tests/runtime/naval/test_naval_screen_scenario.py only if focused runtime
  assertions are required
Non-goals:
- no weapon release as a required objective
- no hit/intercept/damage/kill assertions
- no broad mission-command or facade refactor
- no RL trainer/reward implementation
Validation:
- PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json
- PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_contact_report_geometry.json
- PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_closing_contact_geometry.json
- PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/naval/test_naval_screen_scenario.py
Closure gate:
- new scenario loads through ScenarioLoader;
- existing N3 screen/contact gates still pass;
- N4 contract asserts threat/ROE pre-fire state from valid shared/local track
  evidence or records a concrete blocker if the maintained surface is missing;
- docs and tests continue to forbid N5/N6 claims.
Parallel/dependency:
- depends on N4-0 planning surface;
- blocks N4-B1, N4-C1, and N4-D1 implementation;
- may run in parallel with N4-B0 diagnostics because N4-B0 is read-only.
```

返回证据：

- 新增 `scenarios/naval/ddg51_take1_screen_threat_roe_v1.json`。
- 新增 `tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json`。
- 在 `python/testing/contracts/unit/comm.py` 中增加窄的
  `naval_screen_threat_roe` 处理，同时保留现有 `naval_screen_contact_report`
  行为。
- 证明开火前 `MissionCommand` ROE/authority/assigned-target 可见，并证明合同窗口内
  weapon inventory、health、damage 没有变化。
- 尚未证明独立 `threat_state` 或 assigned-target provenance。

主线程验证：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json
# PASS

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_contact_report_geometry.json
# PASS

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_closing_contact_geometry.json
# PASS

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/naval/test_naval_screen_scenario.py
# 8 passed
```

### N4-B1 Threat / ROE Maintained Semantics

状态：pass / 已接受。主线程已本地重跑构建、聚焦测试和场景合同。

Packet：

```md
Cluster: N4-B Threat / ROE Semantics
Dispatch: N4-B1 threat/ROE maintained semantics
Model / reasoning: gpt-5.4, high
Round cap: 2 implementation rounds before re-scope
Goal: add the minimal maintained semantics for independent pre-fire threat
state and assigned-target provenance.
Write scope:
- command shared-core / mission-command / leader-intent core files, only for
  N4 threat/provenance fields
- mission-command episode JSON codec
- command Python bindings
- python/rl/profile/naval_profile.py
- gym_envs/scenario_loader/runtime_state.py
- focused mission/binding tests
Non-goals:
- no weapon-release, hit/intercept, damage, or kill semantics
- no facade/world-batch projection work
- no RL trainer/reward implementation
Validation:
- focused mission-command ROE tests
- command binding surface tests
- N4 scenario contract smoke
Closure gate:
- maintained state exposes threat state and assigned-target provenance fields;
- Python profile and runtime-state fallback do not silently drop those fields;
- N4-A contract still passes.
Parallel/dependency:
- depends on N4-A1 and N4-B0;
- blocks N4-C1 until accepted.
```

返回证据：

- 新增 maintained shared-core 字段：`threat_state`、
  `assigned_target_track_id`、`assigned_target_source_id` 和
  `assigned_target_snapshot_time_s`。
- 这些字段已通过 mission-command JSON roundtrip、command bindings、naval
  profile mission-command 构造，以及 loader runtime-state fallback 保留。
- 增加聚焦 mission/binding 测试，覆盖 binding 暴露、naval profile 映射、
  episode JSON roundtrip 和 runtime-state fallback preservation。
- facade/world-batch projection 保留给 `N4-C1`，未在本簇触及。

主线程验证：

```bash
cmake --build build-workshop --target ef_py -j2
# passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/mission/test_mission_command_roe_fields.py tests/runtime/mission/test_naval_mission_command_mapping.py
# 10 passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/bindings/test_bindings_command_surface.py
# 5 passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json
# PASS

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_contact_report_geometry.json tests/contracts/unit/naval/naval_screen_closing_contact_geometry.json
# PASS / PASS
```

## Worker Return Packet

每个 worker 必须返回：

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## 停止规则

- 如果 N4 contract 只能通过发明 raw compatibility path 来断言 ROE/authority/assignment，停止。
- 如果场景需要成功武器发射才能通过，停止。
- 如果 worker 需要编辑其分发写入范围之外的宽 facade/world-batch surface，停止。
- 到达轮次上限后停止并重新划分范围，不追加临时 follow-up。
