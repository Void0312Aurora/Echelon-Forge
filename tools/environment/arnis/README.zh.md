# Arnis CMO 适配器

这里维护的是固定上游版本、固定补丁与单一 CLI；完整 Arnis 源码不会复制进 CMO。
当前 continuous patch SHA-256 为
`26536836d46aa7bc3e03da3449b4c52391f096527ab58f365d5dd4b96b9052ee`。

第一阶段只提供三件事：

- `prepare`：检出 Arnis `v3.0.0` 的固定 commit，验证并应用 CMO patch，以
  `--no-default-features` 构建独立的 `arnis-cmo`；
- `export`：读取固定 OSM 输入和固定 bbox 的 phase-1 request，在 Minecraft
  量化前导出连续米制 bundle；
- `verify`：验证 bundle 中每个文件的 SHA-256，并执行 CMO
  `EnvironmentManifest` / catalog admission。

安装不会覆盖上游 `arnis`。默认位置为：

```text
~/.cache/cmo/third_party/arnis/v3.0.0-af521c99124b-cmo5/
~/.local/opt/arnis-cmo/v3.0.0-cmo5/arnis-cmo
~/.local/bin/arnis-cmo
```

## 使用

```bash
python tools/environment/arnis/cli.py prepare

python tools/environment/arnis/cli.py export \
  --request tests/scenario/fixtures/environment_substrate/arnis_bundle_v1/chicago_river_phase1/request.json \
  --output-dir /tmp/arnis-cmo-phase1

python tools/environment/arnis/cli.py verify \
  --bundle tests/scenario/fixtures/environment_substrate/arnis_bundle_v1/chicago_river_phase1/expected

python tools/environment/arnis/visualize.py \
  --bundle tests/scenario/fixtures/environment_substrate/arnis_bundle_v1/chicago_river_phase1/expected \
  --output-dir /tmp/arnis-cmo-continuous-preview
```

可视化工具会同时写出连续场诊断与离线静态场景产物：

- `continuous_field_overlay.png` 与 `continuous_field_metrics.json`；
- 合同为 `cmo.static_scene_geometry.v1` 的 `static_scene_geometry.json`；
- 使用真实米制 Z 比例的 `static_scene_preview.png`。

已解析建筑生成刚性棱柱，源 XY footprint 不变；已解析零层道路按实际宽度生成 DEM
贴合走廊，派生边界面会裁到 DEM 范围，但源 centerline 不变。缺少米制剖面的屋顶、
桥梁、高层通道和地下道路保持显式 held，不猜测高度。

第一阶段强制 `--file`、terrain、`web_mercator`、scale 1、rotation 0、
Overture disabled，并校验实际高程 provider。输出仍只是一份静态环境数据包：不释放
runtime setup、movement、passability、LOS、cover、fires、damage 或 combat。

CMO 导出不会读取 Minecraft world，也不会使用 `ProcessedNode` 整数坐标、block
range 或 block count 作为权威几何。道路、建筑和水系直接从冻结 WGS84 源数据投影到
浮点 local ENU；高程直接来自 `scale_to_minecraft()` 前的 postprocessed metre
grid。地表覆盖是 categorical field，消费时使用 nearest-category；只有 DEM
heightfield 允许双线性连续重建，建筑等矢量对象不参与地形插值。

固定 OSM 输入使矢量来源可校验；已经生成并签入的 bundle 也是逐文件可校验的。但高程和
WorldCover 当前仍由网络/缓存 provider 供给，因此不能声称未来任意时间从网络重新生成仍
会逐字节相同。完全离线重生成属于后续阶段。
