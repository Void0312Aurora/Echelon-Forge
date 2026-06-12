# 海军领域执行面拆分验收门

状态：`2026-06-12`，gate 刷新；`P1-A/P1-B/P2-A/P3-A/P3-B/P4-A`
已作为切片验收，但子项目整体尚未接受。

父项目：[海军领域执行面拆分](README.zh.md)

## Acceptance Decision

当前决定：`not accepted`。

原因：已接受切片现在覆盖 inventory、guard tests、action command surface、
bounded maintained naval observation adapter、domain-neutral config alias，以及
active/eval surface gates。但当前代码库仍保留 flat `MissionCommand`
compatibility shell，以及尚未全局退休的 `PilotAction` carrier /
`WorldPilotActionAssignment` transport path。

## Interim Evidence Accepted

`P1-A/P1-B/P2-A/P3-A/P3-B/P4-A` 验收为 `accepted`，但只关闭已分发切片：

- `P1-A` 已把 active naval path 上的 `PilotAction`、`MissionCommand`、
  `flight_shaping`、runway/takeoff/formation、gear/ILS、原 Python-owned observation
  fallback 与 `WorldPilotActionAssignment` 分类为 accepted shared infrastructure、
  compatibility adapter 或 blocker。
- `P1-B` 已增加 active naval config / eval guard，覆盖 `takeoff*` action mode、
  air mission-observation mode，以及 weapon/fire/damage/kill reward/action leakage。
- `P2-A` 已建立 `naval_station_command` action family，并把剩余 `PilotAction`
  标记为 compatibility-only transport adapter；未触及 `src/runtime/contracts/**`，
  因此不需要 binding rebuild。
- `P3-B` 已增加 domain-neutral `shaping_backend` alias，并保持 canonical
  `flight_shaping_backend` 与 CLI / canonical override 优先级兼容。
- `P3-A` 已把 `naval_screen_station_v1` 收束为 maintained Python observation
  adapter，`basic` 只作为 compiled batch fallback，不作为 policy-visible vector。
- `P4-A` 已增加 active/eval `surface_gate` 证据，覆盖 action command surface、
  legacy transport adapter 与 maintained naval observation adapter。
- 本地主线程验收命令：

```bash
git diff --check -- docs/task/naval examples/config/training/active/naval \
  gym_envs/universal_env.py gym_envs/universal_env_parts python/env_config.py \
  python/rl/runtime tests/eval/test_evaluation_cli_contracts.py \
  tests/runtime/core/test_env_config.py tests/runtime/naval/test_naval_station_policy_surface.py \
  tests/training/test_naval_training_entry_contracts.py tests/world_batch/test_world_batch_vec_env.py

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/runtime/core/test_env_config.py \
  tests/training/test_naval_training_entry_contracts.py \
  tests/eval/test_evaluation_cli_contracts.py \
  tests/runtime/naval/test_naval_station_policy_surface.py

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/runtime/naval/test_naval_station_policy_surface.py \
  tests/world_batch/test_world_batch_vec_env.py \
  -k "transport_adapter or naval_action_family or naval_station3 or maintained_window"
```

结果：`git diff --check` 无输出；pytest 分别为
`45 passed, 45 subtests passed in 34.50s` 与
`13 passed, 74 deselected in 3.44s`。整体 acceptance 仍保持 `not accepted`，
直到 `P2-B` command projection 证据到位。

P3/P4 刷新命令：

```bash
pytest -q tests/runtime/mission/test_mission_obs_taxonomy.py
# 5 passed

pytest -q tests/runtime/naval/test_naval_station_policy_surface.py
# 19 passed

pytest -q tests/eval/test_evaluation_cli_contracts.py -k "NavalStationPolicyEvalTests"
# 8 passed, 5 deselected
```

本次刷新后，observation 证据已通过 bounded adapter 路径到位。整体 acceptance
仍保持 `not accepted`，直到 `P2-B` command projection 实现，或以替代条件显式 held。

## Required Evidence

只有具备以下全部证据，本子项目才能 accepted：

1. Action/intent ownership：
   active maintained naval 入口不再把 `PilotAction` 语义作为 policy-visible action truth，
   或任何剩余 carrier 都被明确文档化并测试为 compatibility-only。
2. Command ownership：
   naval stationing、ROE、assigned-target provenance 和后续 fire-control intent 被 maintained
   shared-core 与 naval-owner projection 测试保护，而不是依赖宽泛 air owner slice 行为。
3. Observation ownership：
   `naval_screen_station_v1` 拥有 maintained packet 或正式边界的 maintained adapter，并且
   测试证明它不把 air takeoff、runway、gear、ILS 或 formation-role 语义暴露为 naval
   policy truth。
4. Config ownership：
   naval 入口可以使用 domain-neutral config name 选择 runtime/control backend，同时既有
   air 名称保持兼容。
5. Regression safety：
   N4 contract 和 active naval training-entry gate 保持绿色。
6. Capability boundary：
   weapon release、hit/intercept、damage、kill、fleet C2 和 learned-policy success 仍在范围外，
   除非另有独立 accepted package 覆盖。

## Expected Validation

至少运行：

```bash
git diff --check -- docs/task/naval

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/training/test_naval_training_entry_contracts.py \
  tests/training/test_naval_training_entry_contracts.py \
  tests/eval/test_evaluation_cli_contracts.py \
  tests/runtime/naval/test_naval_station_policy_surface.py
```

如果实现触及 C++ contract、nanobind binding、active config、eval tool 或 scenario contract，
必须记录额外 build、binding、contract 或 CLI smoke 命令。

## Fail-Closed Rules

- 如果实现仍要求 active naval 入口使用 `takeoff*` action mode，标记 failed。
- 如果实现把 air formation/takeoff mission observation 重新引入 active naval policy input，
  标记 failed。
- 如果实现把 weapon/damage reward term 变成 N4 验收的一部分，标记 failed。
- 如果实现无法解释每个剩余 air-first dependency 是 accepted shared infrastructure、
  compatibility adapter 还是 blocker，最多标记 partial。
