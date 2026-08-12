# Arnis Adapter 第一阶段验收

日期：`2026-07-15`

结论：`accepted`，范围仅限静态 environment bundle 导出、校验、CMO manifest
导入，以及离线静态场景派生/预览。

## 已验收事实

- 上游固定为 Arnis `v3.0.0` / commit
  `af521c99124b5e07ecba018ea54f2ac47b6441d5`；
- continuous exporter patch 为
  `0001-cmo-continuous-bundle-export-v1`，SHA-256
  `26536836d46aa7bc3e03da3449b4c52391f096527ab58f365d5dd4b96b9052ee`；
- exporter 直接重读冻结 OSM 经纬度并投影为浮点 local ENU，在基于 block coordinate
  的 OSM raster repair、map transform 和 Minecraft writer 之前输出
  `arnis_cmo_bundle.v1`；
- phase-1 CLI 强制固定 OSM 文件、terrain、Web Mercator、scale 1、rotation 0、
  Overture disabled 与唯一实际高程 provider；
- 高程来源记录为 `usgs_3dep: 2 source units`、`missing_source_units: 0`，任何
  AWS tile fallback 都会使 retained export fail closed；
- 高程直接写自 land-cover-aware postprocess 后、`scale_to_minecraft()` 前的米制
  grid；bundle 明确声明没有 Minecraft-Y transform 或 roundtrip；
- WorldCover 作为 categorical metric grid 输出，后续只允许 nearest-category
  sampling；
- polygon 只接受闭合源环，并用连续浮点 bbox clipping 处理边界；
- relation member 不再与 standalone building 重复；
- 道路/水道宽度与建筑高度只来自 OSM 米制标签、levels-based metric inference 或
  明确的 metric semantic defaults，不来自 block range/count；
- 道路、建筑和水文携带 fail-closed `elevation_anchor` components：米制建筑基底作为
  刚性 terrain anchor，普通零层道路作为 terrain-draped corridor；缺少屋顶、高架或
  地下剖面的对象保持 held，不猜测高度；
- CMO importer 验证路径逃逸、SHA-256、栅格 dtype/shape/content、矢量范围、
  provenance、catalog admission 与 held capability 边界；同时强制 root、artifact、
  feature、measurement 四层 continuous lineage 和 patch SHA allowlist，旧 block-derived
  bundle fail closed。

## 固定样本

- bbox：`41.8865,-87.6355,41.8895,-87.6315`
- OSM SHA-256：
  `efe1b0d5045ae898b18fa5587df7e477849ef009eb2417c9437f7f2aa64bebd1`
- bundle.json SHA-256：
  `524064a993f83bd1c25c6b5b039ba2ee5c11fd5fae3a9a3cb9a8d617a609571d`
- local ENU extent：`331.116875 × 333.584780 m`
- CMO 对象：`511`
  - elevation tile：`1`
  - landcover tile：`1`
  - roads：`425`
  - buildings：`76`
  - hydrology：`8`

同一输入连续两次导出的目录逐字节一致，`checksums.sha256` 七项全部通过。

离线 `cmo.static_scene_geometry.v1` 派生产物覆盖 `509` 个矢量对象，其中 `403`
resolved、`106` held。Resolved 包括 `66` 个建筑、`329` 条道路和 `8` 个水文对象；
held 包括 `10` 个屋顶/建筑分部、`49` 条高架道路剖面与 `47` 条地下道路剖面。另有
`54` 条边界道路只对派生 corridor polygon 做 DEM 范围裁剪，源 centerline 保持不变。

## 验证

```bash
python tools/environment/arnis/cli.py verify \
  --bundle tests/scenario/fixtures/environment_substrate/arnis_bundle_v1/chicago_river_phase1/expected

python -m pytest -q \
  tests/scenario/test_environment_substrate_contracts.py \
  tests/scenario/test_environment_substrate_arnis_bundle.py \
  tests/scenario/test_environment_projection_contracts.py \
  tests/tools/test_arnis_environment_cli.py \
  tests/tools/test_arnis_continuous_bundle_visualize.py
```

连续预览只读取 CMO bundle，并在图上显式标记 `NOT RUNTIME`；它不是 Minecraft
渲染，也不冒充已释放的仿真运行时。CMO/Python 验收集结果为 `97 passed`；打补丁后的
Arnis Rust 测试集在 `--locked --no-default-features` 下结果为 `362 passed`、
`3 ignored`、`0 failed`。

## 保留项

- runtime setup application、movement、passability、LOS、cover、fires、damage、
  hydrodynamics 和 combat 继续 held；
- elevation / WorldCover 上游 tile 尚未完整签入，长期离线重生成保证继续 held；
- 多 tile、跨 tile object、artifact 去重和第一类 artifact refs 属于后续阶段。
