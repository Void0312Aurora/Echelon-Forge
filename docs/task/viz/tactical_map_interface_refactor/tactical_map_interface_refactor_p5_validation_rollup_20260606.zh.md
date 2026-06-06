# 战术地图界面重构 P5 验证汇总

状态：`2026-06-06`，`VIZ-TMAP-P5` 验证汇总已接受。后续 `P6` closure/archive 同步已由
[P6 closure/archive sync](tactical_map_interface_refactor_p6_closure_archive_sync_20260606.zh.md)
完成。

父项：[战术地图界面重构](README.zh.md)

英文规范页：
[tactical_map_interface_refactor_p5_validation_rollup_20260606.md](tactical_map_interface_refactor_p5_validation_rollup_20260606.md)

## 决策

`VIZ-TMAP-P5` 接受为当前战术地图界面重构的验证汇总。`P1` 到 `P4` 的证据，加上
下方新的代码面复核，已经足以在既定边界内接受第一版维护中的地图优先战术界面。

本汇总不新增 runtime 功能。它只把验收所需证据整理到文档中，使接受决策不依赖聊天历史。

## 证据矩阵

| 切片 | 接受范围 | 证据 | 不能证明什么 |
| --- | --- | --- | --- |
| `P0` 边界/参考 | 持久子项目权威、有限任务簇、状态和风格基线。 | [风格基线](tactical_map_interface_refactor_style_reference_baseline_20260606.zh.md)、[任务簇](tactical_map_interface_refactor_task_clusters_20260606.zh.md) | Runtime UI 实现或仿真行为。 |
| `P1` 壳布局 | 地图优先战术壳，以及可折叠 `SETUP` 和 `DATA` dock。 | [P1 壳布局验收](tactical_map_interface_refactor_p1_shell_layout_acceptance_20260606.zh.md) | 多地图工作区、图层分组、profile 默认值或新的仿真语义。 |
| `P2` 工作区模型 | Tabbed `COP`、`Environment`、`Tracks/Sensors` 和 `3D Inspect` 工作区。 | [P2 工作区验收](tactical_map_interface_refactor_p2_workspace_acceptance_20260606.zh.md)、[test_tactical_map_workspace.py](../../../../tests/viz/test_tactical_map_workspace.py) | Split-map 布局、scenario editor 行为或新的 payload 要求。 |
| `P3` 图层/符号模型 | 集中 tactical layer catalog、分组控制、绘制阶段和第一版样式。 | [P3 图层/符号验收](tactical_map_interface_refactor_p3_layer_symbology_acceptance_20260606.zh.md)、[test_tactical_layer_model.py](../../../../tests/viz/test_tactical_layer_model.py) | MIL-STD-2525/APP-6 合规或 tactical payload 语义变化。 |
| `P4` Profile UI 默认值 | Profile 选择 tactical workspace 和 layer defaults，作为 UI/runtime 偏好。 | [P4 profile-default 验收](tactical_map_interface_refactor_p4_profile_defaults_acceptance_20260606.zh.md)、[test_tactical_profile_ui_defaults.py](../../../../tests/viz/test_tactical_profile_ui_defaults.py) | Scenario schema 变化、真实性/世界参数变异或新的海军行为。 |

## 汇总验证

新的 `P5` 代码面复核：

```bash
perl -0ne 'while (/<script\s+type="module"[^>]*>(.*?)<\/script>/sg) { print $1, "\n" }' examples/viz/web_viz/templates/index.html | node --input-type=module --check -
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/viz/test_environment_overlays.py tests/viz/test_tactical_map_workspace.py tests/viz/test_tactical_layer_model.py tests/viz/test_tactical_profile_ui_defaults.py
python -m json.tool examples/viz/profiles/air_combat_1v1_stage0_forced_fire_debug.json >/dev/null
python -m json.tool examples/viz/profiles/naval_ddg51_contact_report_debug.json >/dev/null
python -m json.tool examples/viz/profiles/naval_ddg51_closing_contact_debug.json >/dev/null
```

`2026-06-06` 观察结果：module 语法检查通过；聚焦 viz 测试报告 `12 passed`；三个
profile JSON 均可正常解析。

浏览器证据保留在已接受切片文档中：

- `P1` 覆盖窄屏和桌面地图优先壳、直接陆军 scenario 加载、空战 profile 加载、
  3D toggle 行为，以及最终浏览器 console `Errors: 0`。
- `P2` 覆盖 `COP`、`ENVIRONMENT`、`TRACKS` 和 `3D INSPECT` 工作区切换、桌面和
  窄屏视口、非空地图像素，以及最终浏览器 console `Errors: 0`。
- `P3` 覆盖分组图层控制和 workspace/layer 行为，最终浏览器 console `Errors: 0`；
  截图路径：`output/playwright/tactical_map_p3_layer_groups_20260606.png`。
- `P4` 覆盖 naval contact-report profile 加载到 `READY`、`TRACKS` 工作区默认值、
  profile 选择的图层默认值，以及最终浏览器 console `Errors: 0`；截图路径：
  `output/playwright/tactical_map_p4_profile_defaults_20260606.png`。

`output/` 下的截图路径是本地 ignored 证据辅助，不是 tracked 项目交付物。`P5` 本身只改文档，
因此没有重新跑浏览器 smoke，而是引用 `P1` 到 `P4` 已接受的 runtime 证据。

## 已知非阻断噪音

- `P3` 和 `P4` 浏览器 smoke 报告的 WebGL `ReadPixels` 只是性能 warning，不是 console error。
- 部分浏览器 smoke 结束后的服务关闭阶段出现既有 nanobind leak warning。该 warning 发生在证据收集后，
  不归因于本 UI-only 战术地图重构。

## 已接受能力

本次 scoped 的第一版战术地图界面重构接受为：

- 保持 tactical canvas 为主表面的地图优先壳；
- tabbed 多表面工作区模型；
- 集中第一版绘制元数据的分组战术图层控制；
- 由 profile 驱动的 workspace/layer UI 默认值；
- 持续把 profile 默认值与 scenario/world 语义分开的文档边界。

## 残余与 held 声明

`P1` 到 `P4` 在本子项目内已经没有立即残余。以下内容仍保持 held 或 deferred，不属于本次收口：

- split-map 布局；
- 更丰富的地形、道路、建筑、植被、天气或其他环境 derived-product 渲染，直到对应环境基底工作线接受这些产品；
- 专门 tactical symbol registry 抽取，等待当前模板变得难以维护后再判定；
- scenario 编辑、地形生成器 UI、地形感知机动、可通行性、LOS、遮蔽/隐蔽、感知、火力、毁伤、奖励、终止或环境 runtime 行为；
- MIL-STD-2525、APP-6 或其他军用符号标准合规。

## 下一步

已由
[P6 closure/archive sync](tactical_map_interface_refactor_p6_closure_archive_sync_20260606.zh.md)
完成：同步 README/status/task-cluster/dispatch/archive 表面，并将本子项目标为 `closed`。
