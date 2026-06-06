# 战术地图界面重构 P4 Profile Defaults 验收

状态：`2026-06-06`，`VIZ-TMAP-P4` 已作为切片接受。整体战术地图界面重构仍为活跃状态；
`P5` 验证汇总和 `P6` closure/archive 同步不由本文接受。

父项：[战术地图界面重构](README.zh.md)

英文规范页：
[tactical_map_interface_refactor_p4_profile_defaults_acceptance_20260606.md](tactical_map_interface_refactor_p4_profile_defaults_acceptance_20260606.md)

## 决策

`VIZ-TMAP-P4` 作为 profile UI 默认值切片接受。

已接受实现将 profile `ui` 默认值扩展为：

- `tactical_workspace`：规范化为 `cop`、`environment`、`tracks` 或 `inspect3d`。
- `tactical_layers`：局部或完整图层 map，规范化为前端图层键
  `environment`、`route`、`trails`、`tracks`、`sensorRings`、`datalinks` 和 `weapons`。

loader 会过滤未知 workspace、未知 layer 和非布尔 layer 值。浏览器把 profile layer defaults
作为所选 workspace 默认值之上的 UI 状态应用；它不会改写 scenario JSON、仿真 payload 语义或环境 runtime 状态。

## 证据

代码、JSON 和回归检查：

```bash
perl -0ne 'while (/<script\s+type="module"[^>]*>(.*?)<\/script>/sg) { print $1, "\n" }' examples/viz/web_viz/templates/index.html | node --input-type=module --check -
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/viz/test_environment_overlays.py tests/viz/test_tactical_map_workspace.py tests/viz/test_tactical_layer_model.py tests/viz/test_tactical_profile_ui_defaults.py
python -m json.tool examples/viz/profiles/air_combat_1v1_stage0_forced_fire_debug.json >/dev/null
python -m json.tool examples/viz/profiles/naval_ddg51_contact_report_debug.json >/dev/null
```

观察结果：module 语法检查通过；聚焦 viz 测试报告 `12 passed`；已编辑 profile JSON 文件解析干净。

浏览器 smoke 使用本地 viz 服务 `http://127.0.0.1:5064`：

- 从 profile selector 加载 `examples/viz/profiles/naval_ddg51_contact_report_debug.json`。
- profile 加载 `scenarios/naval/ddg51_take1_screen_contact_report_v1.json` 并达到 `READY`。
- session 以 `action_mode=naval_station3` 初始化，匹配当前维护中的海军动作面。
- profile 应用 `tactical_workspace=tracks`；顶栏和右侧 dock workspace 均显示 `TRACKS`。
- profile 图层默认值按下 `TRAIL`、`TRACK`、`RING` 和 `LINK`，而 `ENV`、`ROUTE`、`WEPN` 保持关闭。
- 浏览器 console 报告 `Errors: 0`；warnings 仅为 WebGL `ReadPixels` 性能提示。
- 截图：`output/playwright/tactical_map_p4_profile_defaults_20260606.png`。

smoke 结束后关闭服务时出现既有 nanobind leak warning。该警告发生在浏览器证据收集之后，
不归因于 profile UI-defaults 合同。

## 已接受边界

- 不改变 scenario schema。
- 不改变仿真 payload 语义。
- 不接受地形感知机动、可通行性、LOS、掩蔽/隐蔽、感知、火力、毁伤、奖励、终止、scenario 编辑器、地形生成器 UI 或环境 runtime 变异。
- 不声明 MIL-STD-2525、APP-6 或其他军用符号标准合规。
- 将 naval viz profiles 更新为 `action_mode=naval_station3` 只是在对齐已维护的海军 tasking 动作面；
  不声明新的海军行为释放。

## 残余

- `VIZ-TMAP-P5` 应汇总 `P1` 到 `P4` 的验证证据和残余。
- `VIZ-TMAP-P6` 应在验收决策后同步 closure/archive 指针。
- 未来 profile 默认值可以包含更多环境图层条目，但前提是这些环境产品已由所属环境基底工作线验收。
