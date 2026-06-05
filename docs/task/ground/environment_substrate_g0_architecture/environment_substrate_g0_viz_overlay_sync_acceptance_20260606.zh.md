# Environment Substrate G0-Viz Overlay Sync Acceptance

状态：`2026-06-06` accepted implementation follow-on，用于在
`examples/viz` 中可视化已经接受的 G0 environment data。

## 决定

G0-Viz-A 接受为 visualization-only sync package。它不重新打开已经闭合的 G0
substrate 线，也不释放 runtime environment behavior。

本 slice 接受：

- 一个纯 Python 的 `examples/viz` overlay normalizer，用于整理 G0 environment
  data；
- 在既有 `map_setup.zones` 旁边增加向后兼容的
  `map_setup.environment_overlays` payload；
- 一个战术地图 `ENV` 图层，在 routes、tracks、weapons 与 units 之前绘制
  environment area overlays；
- 当 scenario 携带 G0-M bundle 时，metadata-only 的 `surface_zone_index` 与
  `occlusion_candidate_index` 可视化支持；
- 聚焦测试，确保 held derived products 不进入 viz overlay surface。

## 接受面

可视化层可以展示：

- 将 `environment.zones` 作为 surface-zone rectangles；
- 将 G0-M `surface_zone_index` entries 作为 surface-zone rectangles；
- 将 G0-M `occlusion_candidate_index` entries 作为 candidate footprints，支持
  `rect` 或 `aabb` geometry。

战术地图只能把这些 entries 用于 viewport bounds、drawing order、styling 与 labels。
payload 显式携带 no runtime setup application、no runtime consumer release、no
movement release 与 no LOS/cover release 证据标记。

## 明确非释放边界

G0-Viz-A 仍不释放：

- runtime setup application；
- scenario-producing terrain generator plugins 或 checked-in generated terrain
  artifacts；
- road graph、movement-cost grid、passability mask、runtime LOS occlusion、
  cover/concealment runtime products、tactical-area runtime graph；
- route following、speed updates、terrain-aware movement、sensing、fires、damage、
  combat、suppression、reward/termination binding、observation/export；
- weather simulation、hydrodynamics、hydrology effects 或 dynamic environment
  mutation。

## 证据

| Area | Evidence | Result |
| --- | --- | --- |
| Overlay normalizer | [environment_overlays.py](../../../../examples/viz/runtime/environment_overlays.py) | accepted |
| Viz map payload | [viz_session.py](../../../../examples/viz/runtime/viz_session.py) 在 `map_setup` 中 emit `environment_overlays` | accepted |
| Tactical map layer | [index.html](../../../../examples/viz/web_viz/templates/index.html) 增加 `ENV` 并绘制 `rect`/`aabb` overlays | accepted |
| Contract tests | [test_environment_overlays.py](../../../../tests/viz/test_environment_overlays.py) | accepted |

## 验证

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/viz/test_environment_overlays.py
# 2 passed
```

```bash
./.venv/bin/python -m py_compile examples/viz/runtime/environment_overlays.py examples/viz/runtime/viz_session.py
# clean
```

```bash
perl -0ne 'while (/<script\s+type="module"[^>]*>(.*?)<\/script>/sg) { print $1, "\n" }' examples/viz/web_viz/templates/index.html | node --input-type=module --check -
# clean
```

Browser smoke：

- 在 `http://localhost:5062` 启动 `examples/viz`；
- 加载 `scenarios/ground/ground_platoon_tasking_smoke_v1.json`；
- 观察到携带 `GroundTaskingSmokeArea` 与 1 个 environment overlay layer 的
  `map_setup`；
- 确认 `ENV` tactical layer button 出现，且切换时没有 console errors；
- 点击 `START` 后，canvas pixel probe 返回非空战术绘制，并检测到 environment
  风格像素：`nonBackground=5844`、`environmentLike=1130`；
- browser console 为 `0` errors。smoke 中出现的 WebGL readback warnings 与
  nanobind shutdown leak warnings 不是 overlay contract 引入的问题。

ground smoke scenario 仍使用当前 aircraft-compatible ground shell，短跑中出现了既有
failfast aircraft dynamics。该 runtime 行为不是 ground movement 或 terrain behavior
的证据。
