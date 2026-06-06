# 战术地图界面重构 P2 工作区验收

状态：`2026-06-06`，`VIZ-TMAP-P2` 已作为切片接受。历史切片说明：在本检查点，
整体战术地图界面重构仍为活跃状态；`P3` 图层/符号分组和 `P4` profile 默认值持久化不由本文接受。
当前整体状态由
[P6 closure/archive sync](tactical_map_interface_refactor_p6_closure_archive_sync_20260606.zh.md)
取代。

父项：[战术地图界面重构](README.zh.md)

英文规范页：
[tactical_map_interface_refactor_p2_workspace_acceptance_20260606.md](tactical_map_interface_refactor_p2_workspace_acceptance_20260606.md)

## 决策

`VIZ-TMAP-P2` 作为第一版维护中的地图工作区模型切片接受。

本切片先选择 tabbed map surfaces，而不是 split-map 布局。已接受实现包括
[index.html](../../../../examples/viz/web_viz/templates/index.html) 中的单模板 patch，以及聚焦静态回归测试
[test_tactical_map_workspace.py](../../../../tests/viz/test_tactical_map_workspace.py)。

已接受表面：

| 表面 | 角色 | 默认视图 | 默认图层姿态 |
| --- | --- | --- | --- |
| `COP` | 共同态势图 | `MAP` | 默认打开环境、路线、航迹和武器；关闭 tracks/sensor rings/data links。 |
| `Environment` | 环境与区域查看 | `MAP` | 默认只打开环境；关闭路线、航迹、武器、tracks、sensor rings、data links。 |
| `Tracks` | 航迹、传感器和链路查看 | `MAP` | 默认打开航迹、tracks、sensor rings 和 data links；关闭环境、路线、武器。 |
| `3D Inspect` | 3D 模型查看 | `3D` | 复用既有 3D renderer 路径，并保持顶栏 workspace tabs 可回退。 |

这些 workspace tabs 只是 UI runtime 状态。它们不改变 scenario schema、profile schema、仿真 payload 语义或环境 runtime 行为。

## 证据

代码和回归检查：

```bash
perl -0ne 'while (/<script\s+type="module"[^>]*>(.*?)<\/script>/sg) { print $1, "\n" }' examples/viz/web_viz/templates/index.html | node --input-type=module --check -
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/viz/test_environment_overlays.py tests/viz/test_tactical_map_workspace.py
```

观察结果：module 语法检查通过；聚焦 viz 测试报告 `5 passed`。

浏览器 smoke 使用本地 viz 服务 `http://127.0.0.1:5064` 和
`scenarios/ground/ground_platoon_tasking_smoke_v1.json`：

- 初始 `READY` 状态在顶栏显示 `COP`、`ENVIRONMENT`、`TRACKS`、`3D INSPECT` workspace tabs。
- `ENVIRONMENT` 切到 `workspace=environment`，保持 `VIEW: MAP`，默认只启用 `ENV` 图层。
- `TRACKS` 切到 `workspace=tracks`，保持 `VIEW: MAP`，默认启用 trails、tracks、rings 和 links。
- `3D INSPECT` 切到 `workspace=inspect3d`，按钮变为 `VIEW: 3D`，隐藏战术地图 panel，3D renderer 保持
  `opacity=1` 且 pointer events 可用。
- 回到 `COP` 后恢复 `VIEW: MAP` 和地图 panel。
- `START` 后地图 canvas 像素采样得到 `53 / 1344` 个非背景样本。
- 桌面视口 `1440x900`：`layoutMode=wide`，`workspace=cop`，canvas
  `1440x900`，左右 docks 打开。截图：
  `output/playwright/tactical-map-p2-ground-desktop-20260606.png`。
- 窄屏视口 `780x493`：`layoutMode=narrow`，`workspace=cop`，canvas
  `780x493`，workspace tabs 宽度 `756`，左右 docks 关闭。截图：
  `output/playwright/tactical-map-p2-ground-narrow-20260606.png`。
- 最终浏览器 console 检查报告 `Errors: 0`。

截图路径是 `output/` 下的本地 ignored 辅助证据，不是 tracked 项目交付物。

## 已接受边界

- 不改变 scenario schema。
- 不改变 profile-loader contract。
- 本切片不接受 split-map workspace。
- 不接受地形感知机动、可通行性、LOS、掩蔽/隐蔽、感知、火力、毁伤、奖励、终止、scenario 编辑器、地形生成器 UI 或环境 runtime 变异。
- 不声明 MIL-STD-2525、APP-6 或其他军用符号标准合规。

## 残余

- 历史说明：在 `P2` 检查点，`VIZ-TMAP-P3` 和 `VIZ-TMAP-P4` 仍为残余。当前状态由
  [P3 图层/符号验收](tactical_map_interface_refactor_p3_layer_symbology_acceptance_20260606.zh.md)
  和 [P4 profile-default 验收](tactical_map_interface_refactor_p4_profile_defaults_acceptance_20260606.zh.md) 覆盖。
- split-map 布局继续推迟，除非后续需求证明它可以保留 `P1` 和本 P2 tabbed 切片已接受的地图优先人体工学。
