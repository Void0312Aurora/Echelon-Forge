# Ground Arnis 原生地形 v1

语言：[英文规范页](README.md)；本页为中文配套。

Document kind: `work-package`
Lifecycle: `active`
Canonical: `docs/domains/ground/work/active/ground_arnis_native_terrain_v1/README.md`
Owner: `domains/ground`
Accepted: `2026-09-24`

## 目的

让现有 Arnis 东部平原测试包服务于维护中的原生陆战单兵移动切片，同时不把
fixture 元数据悄悄冒充成运行时真值。

## 已准入合同

- `SimulationKernel.load_arnis_terrain_bundle(bundle_root)` 是显式 provider 入口。
- provider 只接受声明 `no_held_capability_release=true` 的
  `arnis_cmo_bundle.v1` bundle。
- 高程和地表覆盖 artifact 必须有匹配且为正的 shape、匹配的有限原点/步长元数据、
  安全的子路径、精确字节长度以及有限的小端 float 高程。
- 原生 environment 直接按带符号米制网格采样。永久水面和未知/nodata 单元会让当前
  有界单兵移动停下；农地/草地/树覆盖目前共用软土移动代价。
- `SimulationKernel.get_ground_terrain_observation(x, y)` 向训练侧 adapter 和诊断暴露
  原生采样，字段为 `(elevation, surface_type, friction, roughness, vegetation_density)`。
- 加载具有事务性：候选包无效时返回 `false`，不替换当前 provider 栅格。

## 明确的非目标

本包不消费 Arnis 矢量要素，不从水文要素推断桥梁，不提供路线/通行性或视线查询，
也不把 RL 训练接到原生 reset/step/replay；同样不宣称自动 runtime setup 或完整地形物理。

## 证据

- `tests/runtime/ground/test_ground_infantry_native_unit.py`
- `tests/training/test_ground_infantry_contracts.py`
- `src/models/environment/default_environment_model.cpp`
- `src/core/engine/simulation_kernel.cpp`

2026-09-24 批次使用固定的 Windows 依赖完成构建。Arnis 移动测试和陆战训练契约测试
通过（`5 passed`）。矢量语义、通行性、桥梁、观测和 RL 门仍明确开放。
