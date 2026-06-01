# 海军领域执行面拆分验收门

状态：`2026-06-01`，gate 已定义；`P1-A/P1-B` 已作为第一切片验收，
但子项目整体尚未接受。

父项目：[海军领域执行面拆分](README.zh.md)

## Acceptance Decision

当前决定：`not accepted`。

原因：第一切片已经完成 inventory 与 guard tests，但当前代码库在 maintained naval path
上仍有已知 compatibility adapter / blocker：中性 `PilotAction` transport、flat
`MissionCommand` compatibility shell、Python-owned naval mission observation fallback，
以及 air-labeled environment backend knob。

## Interim Evidence Accepted

`P1-A/P1-B` 验收为 `accepted`，但只关闭第一切片：

- `P1-A` 已把 active naval path 上的 `PilotAction`、`MissionCommand`、
  `flight_shaping`、runway/takeoff/formation、gear/ILS、Python-owned observation
  fallback 与 `WorldPilotActionAssignment` 分类为 accepted shared infrastructure、
  compatibility adapter 或 blocker。
- `P1-B` 已增加 active naval config / eval guard，覆盖 `takeoff*` action mode、
  air mission-observation mode，以及 weapon/fire/damage/kill reward/action leakage。
- 本地主线程验收命令：

```bash
git diff --check -- docs/task/naval tests/training tests/eval

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/training/test_naval_active_training_entries.py \
  tests/training/test_naval_n4_closure_gate.py \
  tests/eval/test_eval_naval_n4_baseline.py \
  tests/runtime/naval/test_naval_n4_reward_surface.py
```

结果：`git diff --check` 无输出；pytest `39 passed, 48 subtests passed in 35.66s`。
整体 acceptance 仍保持 `not accepted`，直到 action/command/observation/config ownership
证据全部到位。

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
  tests/training/test_naval_active_training_entries.py \
  tests/training/test_naval_n4_closure_gate.py \
  tests/eval/test_eval_naval_n4_baseline.py \
  tests/runtime/naval/test_naval_n4_reward_surface.py
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
