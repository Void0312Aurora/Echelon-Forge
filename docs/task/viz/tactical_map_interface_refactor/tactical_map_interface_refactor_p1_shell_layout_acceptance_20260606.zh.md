# 战术地图界面重构 P1 壳布局验收

状态：`2026-06-06`，`VIZ-TMAP-P1` accepted slice。整个战术地图界面重构仍然
active；本文不接受 `P2` 地图工作区，也不接受后续图层/符号体系工作。

父项：[战术地图界面重构](README.zh.md)

英文规范页：
[tactical_map_interface_refactor_p1_shell_layout_acceptance_20260606.md](tactical_map_interface_refactor_p1_shell_layout_acceptance_20260606.md)

## 决策

`VIZ-TMAP-P1` 作为地图优先壳布局切片接受。

已接受实现是
[index.html](../../../../examples/viz/web_viz/templates/index.html) 中的单模板
patch。它让 tactical canvas 保持第一视口主表面，把 session setup 放入可折叠左
dock，把 telemetry、mission、unit list 和 layer controls 放入可折叠右 dock，并保留既有
profile、scenario、asset、run control、layer control、telemetry 和 unit list DOM ID。

本切片还在直接从 scenario 加载会话时，给 profile 下拉增加
`Scenario only (no profile active)` 的 UI-only 占位。这只是澄清
profile/scenario 边界，不改变 profile 或 scenario schema。

## 证据

代码和回归检查：

```bash
perl -0ne 'while (/<script\s+type="module"[^>]*>(.*?)<\/script>/sg) { print $1, "\n" }' examples/viz/web_viz/templates/index.html | node --input-type=module --check -
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/viz/test_environment_overlays.py
```

观察结果：module 语法检查通过；`tests/viz/test_environment_overlays.py` 报告 `2 passed`。

浏览器 smoke 使用本地 viz 服务 `http://127.0.0.1:5064` 和项目 Playwright wrapper：

- `780x493` 窄屏初始壳：`layoutMode=narrow`，左右 dock 默认关闭，tactical canvas
  为 `780x493`，console errors 为 `0`。
- 窄屏交互壳：打开 `SETUP` 和 `DATA` 后，它们作为覆盖 dock 出现；地图 padding 保持
  narrow-overlay 形态，而不是把 canvas 顶到堆叠控件下方。
- 直接加载陆军 scenario：
  `scenarios/ground/ground_platoon_tasking_smoke_v1.json` 到达 `READY`，随后到达
  `RUNNING`；profile selector 显示 `Scenario only (no profile active)`；`ENV`
  仍保持 pressed；canvas 非空。
- `1440x900` 桌面陆军 smoke：`layoutMode=wide`，左右 dock 打开，tactical canvas 为
  `1440x900`，非背景像素采样为 `30 / 1852`；截图已更新到
  `output/playwright/tactical-map-p1-ground-desktop-20260606.png`。
- 窄屏截图已更新到
  `output/playwright/tactical-map-p1-ground-narrow-20260606.png`。
- 空军 profile smoke：
  `examples/viz/profiles/air_combat_1v1_stage0_forced_fire_debug.json` 到达 `READY`
  后可进入 `RUNNING`；unit list 包含 `Blue_Fighter`、`Red_Drone` 和 `Missile_584`；
  非背景像素采样为 `21 / 1852`。
- 3D 切换 smoke：`VIEW: 3D`，tactical panel display 为 `none`，renderer opacity 为
  `1`，renderer pointer events 为 `auto`，dock 保持打开。
- 最终浏览器 console 检查：`Errors: 0`。

截图路径是 `output/` 下的本地 ignored artifacts；它们是证据辅助，不是纳入版本控制的项目交付物。

## 已接受边界

- 不改变 scenario schema。
- 不改变 profile-loader contract。
- 不接受地形感知机动、可通行性、LOS、掩蔽/隐蔽、感知、火力、毁伤、奖励、终止、
  scenario 编辑器、地形生成器 UI 或 environment-runtime mutation。
- 不声明 MIL-STD-2525、APP-6 或其他军用符号标准合规。

## 残余

- `VIZ-TMAP-P2` 仍需定义维护中的地图工作区模型，包括第一版 `COP`、`Environment`、
  `Tracks/Sensors` 和 `3D Inspect` 表面行为。
- `VIZ-TMAP-P3` 仍需集中图层分组、绘制顺序和第一版符号样式。
- `VIZ-TMAP-P4` 继续 held，直到具体 workspace/layer 默认值需要通过 profile UI 默认值持久化。
- naval debug profiles 仍暴露一个既有 runtime action-mode 不匹配：naval tasking scenario
  需要 `action_mode='naval_station3'`，但当前 profile 路径在 reset 时解析为 `full`。
  该现象在 smoke 选择期间观察到，不由 `P1` 引入，也不由 `P1` 修复。
