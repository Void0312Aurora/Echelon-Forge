# 海军领域执行面拆分任务簇

状态：`2026-06-12`，`P1-A/P1-B/P2-A/P3-A/P3-B/P4-A` 已验收；面向
[海军领域执行面拆分](README.zh.md) 的有限任务簇计划。

accepted 行中的 model ID 保留历史派发记录，不是当前选择指引。任何 planned 或
reopened cluster 都必须按照
[Subagent 使用规范](../../../../../engineering/automation/standards/subagent_usage_policy.zh.md)
重新选择当前 capability/risk tier、可用模型和 reasoning budget。

## Boundary Decision

本子项目可以修改海军任务文档、active naval training-entry guard、command/action/
observation adapter，以及把 maintained naval execution 从 air-first compatibility
carrier 中拆出所需的聚焦测试。

本项目不得声明 N5 武器交战、N6 毁伤 authority、舰队 C2 成熟或 learned-policy 成功。
共享 runtime 基础设施可以复用，但 policy-visible naval 语义必须归 common 或 naval
surface 所有，不能归 air takeoff、runway、formation、gear 或 flight-control 字段所有。

## Finite Task Cluster List

| Cluster | Owner | 历史派发记录 / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `P0-A` | main thread | current | 创建子项目、状态、队列、验收和父级海军索引链接。 | `docs/domains/naval/work/active/naval_domain_surface_split/**`, `docs/domains/naval/README*` | runtime code、测试、能力提升声明 | `git diff --check -- docs/domains/naval` | 必需文件存在且父 README 链接本项目 | 第一个串行簇 | 1 | pass |
| `P1-A` | worker `Linnaeus` | `gpt-5.4-mini` / `xhigh` | 盘点 active naval policy/runtime 路径上仍存在的所有 air-first 依赖。 | `naval_domain_surface_split_current_status_20260601*.md`, optional diagnostics notes | 代码改动、重构 | 只读 `rg` inventory 加文件/行证据 | 每项依赖被分类为 accepted shared、compatibility adapter 或 blocker | `P0-A` 后；只读可单独运行 | 1 + 1 repair | accepted |
| `P1-B` | worker `Locke` | `gpt-5.4` / `high` | 增加 guard 测试，防止 active naval 入口回退到 air action 或 air mission-observation surface。 | `tests/training/**`, `tests/eval/**`, active naval config tests only | 新 packet 实现、N5 行为 | naval active entries 与 baseline eval 聚焦 pytest | `takeoff*`、air formation/takeoff mission mode、weapon/damage reward 泄漏会失败 | `P1-A` dispatch 后；可先于实现 | 1 + 1 repair | accepted |
| `P2-A` | worker `Locke` | `gpt-5.4` / `high` | 设计并实现 naval-owned action/intent assignment seam，或围绕当前 `PilotAction` carrier 建立显式 adapter。 | `src/runtime/contracts/**`, `gym_envs/universal_env_parts/**`, `python/rl/runtime/**`, focused tests | 完整 helm/autopilot doctrine、武器开关 | 若触及则跑 C++/binding build；聚焦 world-batch naval tests | maintained naval 路径不再把 `PilotAction` 语义当作 policy action truth | `P1-A/P1-B` 已验收；不与 `P2-B` 并行 | 2 + 1 repair | accepted |
| `P2-B` | future worker | n/a | 通过 shared-core 与 naval-owner projection 测试约束 `MissionCommand` compatibility 用法。 | `src/components/command/**`, `src/runtime/contracts/**`, `python/rl/profile/naval_profile.py`, command-chain tests | 重写所有 command consumer 为嵌套结构 | command roundtrip tests、world-batch command-chain tests | naval station/ROE/assigned-target 字段经 maintained naval slice 存活 | `P1-A` 后；若触及同一 contract 文件，不与 `P2-A` 并行 | 2 + 1 repair | planned |
| `P3-A` | main thread | current | 将 `naval_screen_station_v1` 推向 maintained naval observation packet。 | `python/mission_obs_taxonomy.py`, `gym_envs/scenario_loader/mission_observation.py`, observation runtime/batching, tests | weapon/damage observation、fleet C2 schema | mission observation taxonomy 与 naval reward/observation tests | policy-visible naval vector 不是 air takeoff/formation fallback | `P2-A` boundary accepted 后 | 2 + 1 repair | accepted |
| `P3-B` | worker `Linnaeus` | `gpt-5.4-mini` / `xhigh` | 当 air-labeled knob 阻塞 naval ownership 时增加 domain-neutral config alias。 | `python/env_config.py`, `train.py`, examples config docs, tests | 破坏既有 air config | env-config tests 与 naval training-entry bootstrap | naval entry 可使用中性名称，legacy air 名称仍兼容 | `P1-B` 已验收；与 `P2-A` 写集不重叠 | 1 + 1 repair | accepted |
| `P4-A` | main thread | current | 将 active naval config、eval gate 与 contract 接到已接受的拆分 surface。 | `examples/config/training/active/naval/**`, `tools/eval/**`, `tests/runtime/naval/**`, `tests/eval/**` | 正式训练、N5/N6 release | naval active pytest、eval CLI smoke、scenario contracts | active entry 在新 surface 上运行，仍禁止 airfield/weapon/damage term | `P2/P3` accepted 后 | 1 + 1 repair | accepted |
| `P5-A` | main thread | current | 通过 acceptance 与父级进展更新关闭或 hold 本子项目。 | `docs/domains/naval/work/active/naval_domain_surface_split/**`, `docs/domains/naval/README*`, optional current progress update | 后补实现 | `git diff --check -- docs/domains/naval` 加记录的测试结果 | acceptance doc 记录 pass/held residuals 且不越界声明 | 最终串行簇 | 1 | planned |

## Dispatch Rules

- 每个 worker packet 必须精确映射到上表一个 cluster。
- 不允许两个 worker 并发编辑同一规范表、public API、scenario contract 或 status line。
- 触及 `src/runtime/contracts/**` 的 command/action contract 工作保持串行。
- acceptance 和父级 README closure 保持串行。
- 如果 cluster 超过 round cap，先停止并重新划分范围，不能直接加下一波。
- 遵循 [Subagent 使用规范](../../../../../engineering/automation/standards/subagent_usage_policy.zh.md)。

## Worker Packet Requirements

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

Worker packet 还必须说明剩余的 `PilotAction`、`MissionCommand`、`flight_shaping`、
runway、takeoff、formation、gear 或 ILS 依赖分别属于 accepted shared infrastructure、
compatibility adapter 还是 blocker。

## Validation Plan

文档-only 切片的基线验证：

```bash
git diff --check -- docs/domains/naval
```

实现验收前预期的聚焦 runtime 验证：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/training/test_naval_training_entry_contracts.py \
  tests/training/test_naval_training_entry_contracts.py \
  tests/eval/test_evaluation_cli_contracts.py \
  tests/runtime/mission/test_mission_obs_taxonomy.py \
  tests/runtime/naval/test_naval_station_policy_surface.py
```

触及 `src/`、`python/rl/runtime`、`gym_envs`、active config 或 scenario contract 时，
worker packet 必须补充更窄的 build、binding 或 contract 命令。

## Acceptance Criteria

- Active maintained naval 入口不使用 air takeoff action 或 air formation/takeoff
  mission-observation 语义。
- naval-owned action/intent path，或显式限定的 compatibility adapter，取代 maintained naval
  入口的 policy-visible `PilotAction` truth。
- `MissionCommand` compatibility shell 被测试为 projection transport，而不是 naval 语义 owner。
- Naval observation 字段以海军字段命名并被测试。
- Config alias 或 wrapper 不再把 naval ownership 暴露成 air `flight_shaping` 行为。
- N4 contract 保持绿色，N5/N6 声明保持阻塞。

## Residual Map

Immediate:

- `P1-A/P1-B` 已完成 active air-first 依赖盘点与回归 guard；
- `P2-A` 已建立 `naval_station_command` policy family 与 `PilotAction`
  compatibility-only transport adapter；
- `P3-B` 已让 active naval config 使用 domain-neutral `shaping_backend` alias；
- `P3-A` 已将 `naval_screen_station_v1` 收束为 maintained Python observation
  adapter，`basic` 仅作为 compiled batch fallback；
- `P4-A` 已增加 active/eval `surface_gate`，覆盖 action command surface、
  legacy transport adapter 与 naval observation adapter；
- 下一步聚焦 `P2-B` command projection，并继续避免 `src/runtime/contracts/**` 写集并发。

Follow-on:

- action/command ownership 接受后再打开 N5 launch/reject package；
- observation、reward 和 eval gate 成熟后再做正式训练证据。

Deferred:

- 完整 helm/autopilot doctrine；
- 高保真毁伤与 kill authority；
- fleet C2 或多舰艇 learned tactics。
