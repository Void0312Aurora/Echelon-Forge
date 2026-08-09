# 纯地图查看模式与 Profile 绑定后续项

状态：`2026-06-06`，已验收的 P1 visualization review。UI-only 纯地图查看切片
通过；profile/object binding 保持 held，归入单独 issue。

语言：

- 英文规范页：[README.md](README.md)
- 中文辅文：`README.zh.md`

Document kind: `review`
Lifecycle: `accepted`
Canonical: `docs/operations/visualization/reviews/map_only_viewer_mode_20260606/README.md`
Owner: `operations/visualization`
Last verified: `2026-08-08`

输入：

- 父级 owner：[Operations](../../../README.zh.md)
- 当前前端壳：
  [index.html](../../../../../examples/viz/web_viz/templates/index.html)
- 当前 profile loader：
  [profile_loader.py](../../../../../examples/viz/app/profile_loader.py)
- 已接受 P1 证据：
  [map_only_viewer_mode_p1_acceptance_20260606.zh.md](map_only_viewer_mode_p1_acceptance_20260606.zh.md)

## 目的

本 follow-on 为 `examples/viz` 增加直接的“纯地图”查看模式，让用户可以在不被 setup dock、
data dock、顶部 workspace/action bar 和底部 help overlay 干扰的情况下检查战术地图。

这个变化刻意保持 UI-only。它不改变 scenario schema、profile/session 所有权、environment data、
tactical payload 语义或 runtime 行为。

## 当前切片

`P1` 的已接受实现：

- 在现有顶部 action bar 增加显式 `MAP ONLY` 入口。
- 纯地图模式隐藏所有 chrome，但保留 tactical canvas、地图比例尺和小型 `EXIT MAP` 控件。
- `Escape` 可退出纯地图模式。
- 允许 profile `ui.map_only` 把默认 viewer posture 设为 UI 偏好。
- 如果在 `3D Inspect` 工作区请求纯地图模式，返回最近的地图工作区，避免出现空白 map-only 状态。

验收证据保留在
[map_only_viewer_mode_p1_acceptance_20260606.zh.md](map_only_viewer_mode_p1_acceptance_20260606.zh.md)。

## Held 后续项

Profile/object binding 不在本文实现。后续切片应把 visualization profile 中硬编码的 service/domain 假设改为对象绑定规则，例如：

- 将 focus 和 layer defaults 绑定到 scenario object IDs、object tags 或 asset registry capabilities；
- air/naval/ground 等 service 标签保留为元数据，而不是 profile 内的控制流分支；
- 保持 `profile` 与 `scenario` 边界：profile 选择查看姿态和对象绑定，scenario 拥有世界/内容语义。

## 验证

`P1` 已接受验证：

```bash
perl -0ne 'while (/<script\s+type="module"[^>]*>(.*?)<\/script>/sg) { print $1, "\n" }' examples/viz/web_viz/templates/index.html | node --input-type=module --check -
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/viz/test_tactical_map_workspace.py tests/viz/test_tactical_layer_model.py tests/viz/test_tactical_profile_ui_defaults.py tests/viz/test_tactical_map_only_mode.py
git diff --check -- docs/operations/visualization examples/viz tests/viz
```

浏览器 smoke 已验证 `MAP ONLY` 会隐藏 chrome、保留地图 canvas 交互，并能通过 `EXIT MAP`
和 `Escape` 退出；参见
[map_only_viewer_mode_p1_acceptance_20260606.zh.md](map_only_viewer_mode_p1_acceptance_20260606.zh.md)。

## 非声明

本 follow-on 不释放：

- 地形生成或生成场景 artifacts；
- runtime setup application；
- movement、LOS、cover、sensing、fires、damage、combat、reward 或 termination 行为；
- 除上方 held 设计说明以外的 profile object-binding 语义。
