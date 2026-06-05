# Environment Substrate G0-L Projection Preflight

状态：`2026-06-06` G0-L preflight 返回 `pass`；projection setup payload 与 strict
scenario compiler ingestion 已接受。Runtime setup application 继续 held。

语言：

- 英文主文：
  [environment_substrate_g0_projection_preflight_20260606.md](environment_substrate_g0_projection_preflight_20260606.md)
- 中文配套：
  `environment_substrate_g0_projection_preflight_20260606.zh.md`

输入：

- G0 package README：[README.zh.md](README.zh.md)
- 已接受 G0-J static contract：
  [environment_substrate_g0_static_manifest_contract_20260605.zh.md](environment_substrate_g0_static_manifest_contract_20260605.zh.md)
- 已接受 G0-K generator/catalog contract：
  [environment_substrate_g0_generator_catalog_20260605.zh.md](environment_substrate_g0_generator_catalog_20260605.zh.md)
- 当前 projection contract：
  [projection.py](../../../../python/scenario/environment_substrate/projection.py)
- 已接受 G0-L projection setup payload：
  [environment_substrate_g0_projection_setup_acceptance_20260606.zh.md](environment_substrate_g0_projection_setup_acceptance_20260606.zh.md)
- 已接受 G0-L-F scenario compiler ingestion：
  [environment_substrate_g0_scenario_ingestion_acceptance_20260606.zh.md](environment_substrate_g0_scenario_ingestion_acceptance_20260606.zh.md)
- Scenario/runtime source inventory：
  [environment_substrate_g0_source_inventory_20260605.zh.md](environment_substrate_g0_source_inventory_20260605.zh.md)

## 目的

G0-L 是 G0-K 之后的下一条 environment-substrate continuation。它要将已验证的
compatibility projection output 向当前 scenario/world setup surfaces 推进，同时不把
这件事误说成 terrain runtime behavior 已存在。

第一版唯一合理候选是面向矩形、surface-only objects 的有损
`world_zone_definition` projection，且这些 objects 必须已经通过 G0-J/G0-K validators。
A/B/C preflight packets 已返回 `pass`。已接受 G0-L 现在覆盖 inert projection setup
payload contract，以及把 accepted payloads 消费到 merged `environment.zones` 的 strict
compiler ingestion hook。它仍不 apply runtime setup。

## 当前状态

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| G0-J projection contract | accepted | [projection.py](../../../../python/scenario/environment_substrate/projection.py)、projection tests | 只输出 contract evidence；不 apply setup。 |
| G0-K generated manifest fixture | accepted | [G0-K acceptance](environment_substrate_g0_generator_catalog_acceptance_20260606.zh.md) | 只在内存中；不提交 generated artifacts。 |
| Projection setup payload contract | accepted implementation slice | [G0-L setup acceptance](environment_substrate_g0_projection_setup_acceptance_20260606.zh.md) | 只有 Python payload/evidence；不 apply setup。 |
| Scenario compiler ingestion | accepted implementation slice | [G0-L-F ingestion acceptance](environment_substrate_g0_scenario_ingestion_acceptance_20260606.zh.md) | 只做 strict data ingestion into merged scenario zones；不做 runtime setup application。 |
| Runtime setup application | held | 本文 | 需要单独 release package。 |
| C++ runtime behavior | held | G0 residual map | 不新增 runtime terrain ownership 或 behavior。 |
| Derived products | metadata-only G0-M accepted；runtime products held | [G0-M acceptance](environment_substrate_g0_derived_products_acceptance_20260606.zh.md) | 不做 road graph、movement-cost grid、passability mask、runtime LOS 或 cover product。 |

## 范围

G0-L preflight 范围内：

- 检查 Python scenario compiler/setup ingestion paths 是否支持 environment zones；
- 检查 C++ world setup 与 batch setup contracts 中的 `WorldZoneDefinition`；
- 定义 implementation 前所需的最小 projection request/evidence payload；
- 定义 focused tests 与 fail-closed projection integration reason codes；
- 判断是否能打开有限 G0-L implementation write set。

范围外：

- preflight packets 返回前编辑 scenario compiler/runtime code；
- C++ runtime edits 或新的 world-query ownership；
- generated scenario files 或 checked-in generated environment artifacts；
- 将 non-rect geometry、buildings、vegetation、roads、hydrology effects、weather
  cells、wind/maritime behavior、dynamic state 或 derived products 投影成 runtime
  behavior；
- movement、passability、route following、LOS、cover、fires、damage、combat 或
  observation/export。

## 阶段计划

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `G0-L-A Scenario Compiler Surface Preflight` | 检查 Python scenario compiler/setup surfaces，并识别 projected world zones 是否有 maintained ingestion path。 | G0-K accepted。 | packet 返回 accepted candidates、blockers 与 held risks。 | pass |
| `G0-L-B Runtime Setup Surface Preflight` | 检查 C++ batch/world setup contracts 对 `WorldZoneDefinition` 的兼容性和 runtime side effects。 | G0-K accepted。 | packet 返回 accepted candidates、blockers 与 held risks。 | pass |
| `G0-L-C Test And Validator Gate Preflight` | 定义 G0-L implementation 前所需 focused tests、reason codes 与 fail-closed gates。 | G0-K accepted。 | packet 返回 required tests 与 reason codes。 | pass |
| `G0-L-D Integration Decision` | 整合 A/B/C packets，并决定是否能打开 implementation。 | A/B/C returned。 | 接受有限 projection setup payload write set；compiler ingestion 通过 G0-L-F 续接；runtime application 继续 held。 | pass |
| `G0-L-E Projection Setup Payload Contract` | 为已接受 world-zone projections 实现 inert payload/evidence conversion。 | G0-L-D pass。 | focused tests 通过，且不 apply runtime setup。 | accepted |
| `G0-L-F Scenario Compiler Ingestion` | 将 accepted projection setup payloads 接入 scenario compiler ingestion。 | G0-L-E accepted 加 closure continuation。 | strict compiler data ingestion 已接受且有 focused tests；runtime setup application 继续 held。 | accepted |

## 任务簇

- Task cluster plan：
  [environment_substrate_g0_projection_preflight_cluster_20260606.zh.md](environment_substrate_g0_projection_preflight_cluster_20260606.zh.md)

## 派发规则

- 只复用现有 agents；不得创建新的会话线程。
- diagnostics workers 只读，不得编辑、stage、commit 或重排格式。
- 每个 worker packet 必须精确映射到一个 G0-L-A/B/C cluster。
- 不把同一 normative table 拆给多个 worker。
- G0-L-D 接受有限 write set 前不得实现 projection integration。
- G0-L projection 必须与 G0-M derived products 以及单独 ground route-move
  release votes 分离。

## 验收门

G0-L projection 接受至 scenario compiler ingestion，因为：

- G0-L-A/B/C 返回 `pass`；
- candidate projection target 限于已接受 compatibility setup fields，第一版只考虑
  `world_zone_definition`；
- 已接受 write set 有限且只在 Python；
- projection evidence 保留 source manifest/object/catalog/provenance IDs；
- 对 unknown profiles、unsupported targets、non-rect geometry、dropped rich
  attributes、branch/catalog mismatch 和 held runtime claims 定义 fail-closed 行为；
- scenario compiler ingestion 是 strict、namespaced、provenance-preserving，且能在
  layout metadata 默认 invalid surfaces 前 fail closed；
- movement、LOS、cover、fires、damage、combat、weather simulation、hydrodynamics、
  hydrology effects、dynamic mutation 与 runtime derived-product consumer claims
  全部继续 held。

## Residuals

- Runtime setup application 继续 held。
- G0-M metadata-only derived products 已单独接受。
- Ground route movement 仍由单独 G6-D3/G6-F release path 管辖。
