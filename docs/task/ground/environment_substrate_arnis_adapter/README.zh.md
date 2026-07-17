# Environment Substrate Arnis Adapter

状态：第一阶段已于 `2026-07-15` 实现并通过本地验收。

语言：

- 英文主文：[README.md](README.md)
- 中文配套：`README.zh.md`

本包是已闭合 environment-substrate G0 之后的独立 follow-on。它把 Arnis 用作真实
地理数据获取和语义处理前端，但不把 Minecraft world 或其方块坐标当作 CMO 地形
格式。数据链为：

```text
固定 OSM JSON + 固定 bbox + 固定 Arnis patch
  -> pre-render continuous metric arnis_cmo_bundle.v1
  -> CMO EnvironmentManifest + elevation-anchor admission
  -> offline cmo.static_scene_geometry.v1 derivation and preview
```

## 第一阶段交付

- 固定 Arnis `v3.0.0` / commit
  `af521c99124b5e07ecba018ea54f2ac47b6441d5` 与 CMO exporter patch；
- 独立 `arnis-cmo` 安装，不覆盖上游 `arnis`；
- 本地 ENU 连续米制 bundle：pre-Minecraft 高程、categorical WorldCover、
  浮点道路、建筑与水系；
- CMO fail-closed importer、专用 catalog、来源与校验和验证；
- root / artifact / feature / measurement 四层 continuous lineage 与 exporter
  patch SHA allowlist；
- 为刚性地面建筑、DEM 贴地道路、高架剖面、地下剖面和水面预览放置提供
  fail-closed `elevation_anchor` components；
- Chicago River 固定样本及逐文件 SHA-256；
- `prepare / export / verify` 统一工具入口，以及明确标记为非 runtime 的连续场和静态场景
  预览。

入口：

- 工具：[../../../../tools/environment/arnis/README.zh.md](../../../../tools/environment/arnis/README.zh.md)
- 导入器：`python/scenario/environment_substrate/importers/arnis_bundle.py`
- fixture：`tests/scenario/fixtures/environment_substrate/arnis_bundle_v1/chicago_river_phase1/`
- 验收：[environment_substrate_arnis_phase1_acceptance_20260715.zh.md](environment_substrate_arnis_phase1_acceptance_20260715.zh.md)

## 能力边界

第一阶段只接受静态环境数据。它没有释放 runtime setup application、movement、
passability、route graph、LOS、cover、concealment、fires、damage、hydrodynamics 或
combat。道路宽度、建筑高度和水系几何只是带来源语义的静态输入，不是战术效果。

高程栅格是 sampled heightfield，可由后续 runtime 以双线性方式连续重建；地表覆盖是
categorical field，只允许 nearest-category 采样。建筑、道路和水系保持独立矢量，不能
通过地形栅格插值。旧的 block-derived 草稿 bundle 已失效，新 importer 会 fail closed。

静态场景派生产物保持源 XY 不变。已解析建筑使用 DEM 样本与米制 base offset 确定单一
刚性基础平面；已解析道路使用带真实宽度的贴地 corridor polygon。缺少米制垂直剖面的
对象继续 held：Chicago 固定样本中包括 `10` 个屋顶/建筑分部、`49` 条高架道路剖面和
`47` 条地下道路剖面。该派生产物不是 collision、pathfinding、LOS、cover 或 damage
权威。

固定 OSM 输入与签入 bundle 可逐字节验证；USGS 3DEP 和 ESA WorldCover 的网络/缓存
来源尚未完整离线冻结，因此不能宣称未来从网络重新生成必然逐字节相同。
