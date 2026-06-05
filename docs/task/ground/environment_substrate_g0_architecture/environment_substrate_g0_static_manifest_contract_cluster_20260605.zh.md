# Environment Substrate G0 Static Manifest Contract 任务簇

状态：`2026-06-05` 面向
[environment_substrate_g0_static_manifest_contract_20260605.zh.md](environment_substrate_g0_static_manifest_contract_20260605.zh.md)
的 accepted finite G0-J implementation substage。

## 边界决策

`G0-J` 只实现 static shared environment manifest contract、default registries、
validators、deterministic fixture 与 contract-level compatibility projection tests。
它不得实现 terrain generation、scenario/runtime integration、C++ runtime ownership、
movement、LOS、cover、fires、damage、combat、weather simulation、hydrodynamics、
hydrology effects 或 dynamic environment mutation。

## 有限任务簇

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `G0-J-A Static Schema` | main thread | n/a | 新增 shared manifest、branch membership、component、geometry、extent、generation 与 projection-profile data structures。 | `python/scenario/environment_substrate/manifest.py`、package `__init__.py` | 不做 runtime setup、generator 或 C++ code。 | Import 与 deterministic metadata tests。 | Fixture deterministic serialize。 | G0 architecture acceptance 后启动。 | 1 | pass |
| `G0-J-B Registry And Validation` | main thread | n/a | 新增 default branch/component/layer registries 与 fail-closed validation。 | `python/scenario/environment_substrate/components.py`、`validation.py` | 不释放 runtime capability。 | missing branch、missing component attrs、untyped behavior 与 held claims reject。 | Validation 返回 stable reason codes。 | 依赖 G0-J-A。 | 1 | pass |
| `G0-J-C Projection Contract` | main thread | n/a | 新增 contract-only `world_zone_definition` projection evidence，并 fail closed 拒绝 unsupported rich features。 | `python/scenario/environment_substrate/projection.py`、`tests/scenario/test_environment_substrate_projection.py` | 不做 compiler/runtime integration 或 actual world setup application。 | Focused projection tests。 | Projection 输出 evidence，并拒绝 dropped rich components、misspelled surface fields、non-rect geometry 与 unsupported targets。 | 依赖 G0-J-A/B。 | 1 | pass |
| `G0-J-D Documentation Sync` | main thread | n/a | 记录 G0-J acceptance evidence 与 parent docs status。 | `docs/task/ground/environment_substrate_g0_architecture/*.md`、ground 父 README/progress/queue docs | 不 archive，不做 generator implementation。 | touched docs 的 `git diff --check`。 | 父级 docs 在 G0-J closeout 时标记 G0-J accepted 与 G0-K held；当前 G0-K acceptance 已取代该 residual。 | tests 后串行。 | 1 | pass |

## 派发规则

- 即使 task package 由 ground lane 索引，也必须保持为 shared
  `environment_substrate` infrastructure。
- G0-J 不编辑 C++ runtime code。
- G0-J 不把 projection 接进 scenario compiler/runtime setup。
- G0-J 不添加 generator plugins、derived products、movement、LOS、cover、fires、
  damage 或 combat behavior。
- 不把 compatibility projection evidence 当作 runtime release。

## Worker Packet 要求

该窄范围 main-thread implementation 不需要 subagent packet。未来任何 G0-K delegated
packet 必须返回 files inspected、implementation scope、validation outcome、
rejected alternatives 与 explicit held capability claims。

## 验证计划

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/scenario/test_environment_substrate_manifest.py tests/scenario/test_environment_substrate_projection.py
```

结果：`10 passed`。

## 验收标准

G0-J 已接受，因为：

- shared package namespace 已落在 `python/scenario/environment_substrate/`；
- static manifests deterministic serialize；
- branch registry 包含 terrain 加 atmosphere/weather、wind、illumination、
  maritime/ocean、hydrology 与 dynamic environment；
- validators 用 stable reason codes fail closed；
- projection tests 证明 unsupported rich terrain semantics 会被拒绝，而不是默默落进
  当前 setup defaults；
- 不声明或释放 runtime behavior。

## Residual Map

- G0-K generator/catalog work 在 G0-J closeout 时保持 held；当前已由已接受的
  G0-K generator/catalog contract 取代。
- G0-J 原本关于 G0-L/G0-M 的 residual 已由 accepted G0-L projection setup plus
  compiler data ingestion 与 accepted G0-M metadata-only derived products 取代。
- Runtime setup application 与 runtime derived-product consumers 继续 held。
- Ground route movement 与 terrain-aware realism 仍在单独 release votes 之后。
