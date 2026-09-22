# 预览产物

这些 PNG/JSON 是在 2026-09-23 使用固定 Arnis v3.0.0 CMO patch、合成 OSM 输入和
`mapterhorn` 高程 provider 生成的离线预览。

- `continuous_field_overlay.png`：连续 DEM、分类地表覆盖和静态矢量叠加；
- `static_scene_preview.png`：道路/建筑/水系的静态几何推导；
- `continuous_field_metrics.json`：机器可读的来源与几何统计；
- `static_scene_geometry.json`：`cmo.static_scene_geometry.v1` 派生数据。
- `../field_acceptance.json`：平原/开放地表组成门槛；本报告通过不代表已释放
  通行性或视线 runtime。

预览标题中的 `NOT RUNTIME` 是有效边界：这些产物不提供碰撞、路径规划、通行性、
视线、掩体或战斗权威。完整 100% 原始 raster bundle 没有复制到仓库，原因是本次
导出的 1 m 栅格约 168 MiB；需要时可用同一 request 重建并通过 `verify` 校验。
