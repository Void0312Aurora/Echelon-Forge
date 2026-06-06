# 战术地图界面重构 P1 壳布局验收

状态：`2026-06-06`，`VIZ-TMAP-P1` accepted slice。历史切片说明：在本检查点，
整个战术地图界面重构仍然 active；本文不接受 `P2` 地图工作区，也不接受后续图层/符号体系工作。
当前整体状态由
[P6 closure/archive sync](tactical_map_interface_refactor_p6_closure_archive_sync_20260606.zh.md)
取代。

父项：[战术地图界面重构](README.zh.md)

英文规范页：
[tactical_map_interface_refactor_p1_shell_layout_acceptance_20260606.md](tactical_map_interface_refactor_p1_shell_layout_acceptance_20260606.md)

## 决策

`VIZ-TMAP-P1` 作为地图优先壳布局切片接受。

已接受实现是
[index.html](../../../../../examples/viz/web_viz/templates/index.html) 中的单模板
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

- 历史说明：在 `P1` 检查点，`VIZ-TMAP-P2`、`VIZ-TMAP-P3` 和 `VIZ-TMAP-P4`
  仍为残余。当前状态由 [P2 工作区验收](tactical_map_interface_refactor_p2_workspace_acceptance_20260606.zh.md)、
  [P3 图层/符号验收](tactical_map_interface_refactor_p3_layer_symbology_acceptance_20260606.zh.md)
  和 [P4 profile-default 验收](tactical_map_interface_refactor_p4_profile_defaults_acceptance_20260606.zh.md) 覆盖。
- 历史说明：`P1` smoke 中观察到的 naval debug profile action-mode 不匹配，已由后续 `P4`
  profile-default 切片修复；naval viz profiles 现在对齐 `action_mode='naval_station3'`。
