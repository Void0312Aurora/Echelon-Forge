# Environment Substrate G0-K Generator Catalog

状态：`2026-06-06` 已接受 G0-K generator/catalog contract 子阶段。本文起初是
`2026-06-05` preflight dispatch；现在记录已返回 diagnostics、有限实现切片和验收边界。

语言：

- 英文主文：
  [environment_substrate_g0_generator_catalog_20260605.md](environment_substrate_g0_generator_catalog_20260605.md)
- 中文配套：
  `environment_substrate_g0_generator_catalog_20260605.zh.md`

输入：

- G0 package README：[README.zh.md](README.zh.md)
- G0 architecture plan：
  [environment_substrate_g0_architecture_plan_20260605.zh.md](environment_substrate_g0_architecture_plan_20260605.zh.md)
- G0 terrain-system architecture：
  [environment_substrate_g0_terrain_system_architecture_20260605.zh.md](environment_substrate_g0_terrain_system_architecture_20260605.zh.md)
- 已接受 G0-J static contract：
  [environment_substrate_g0_static_manifest_contract_20260605.zh.md](environment_substrate_g0_static_manifest_contract_20260605.zh.md)
- G0-K 验收：
  [environment_substrate_g0_generator_catalog_acceptance_20260606.zh.md](environment_substrate_g0_generator_catalog_acceptance_20260606.zh.md)
- Subagent 使用规范：
  [../../../standards/governance/subagent_usage_policy.zh.md](../../../standards/governance/subagent_usage_policy.zh.md)

## 目的

G0-K 是 G0-J 之后的 environment-substrate 子阶段。它把 static manifest contract
推进为 deterministic generator/catalog contract，但不声明 runtime behavior。preflight
workers 已返回 `pass`，主线程接受一个有限实现：request/tile/seed/provenance data、
catalog descriptors/admission rules，以及 deterministic in-memory manifest fixture
generation。

第一版有效 generator target 不是 ground 私有 schema，而是 shared
environment-substrate generator contract。它后续应能生成 terrain、buildings、
vegetation、infrastructure、tactical areas、weather/wind/maritime context 与
hydrology objects，并以 catalog-composed `EnvironmentObject` records 输出。

## 当前状态

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| G0 architecture | accepted | [README.zh.md](README.zh.md) | shared design only；不释放 runtime。 |
| G0-J static contract | accepted | [G0-J acceptance](environment_substrate_g0_static_manifest_contract_acceptance_20260605.zh.md) | 只有 static manifest、validators、fixture 与 contract projection tests。 |
| G0-K request/tile/seed contract | accepted | [generator.py](../../../../python/scenario/environment_substrate/generator.py)、focused tests | 只有 Python contract；不做 scenario compiler/runtime integration。 |
| G0-K catalog admission rules | accepted | [catalog.py](../../../../python/scenario/environment_substrate/catalog.py)、focused tests | Catalog labels 仍是 recipes；不释放 movement/LOS/cover/fires/damage/combat semantics。 |
| G0-K deterministic fixture | accepted | [test_environment_substrate_contracts.py](../../../../tests/scenario/test_environment_substrate_contracts.py) | 只生成内存 manifest；不提交 generated artifact。 |
| Runtime projection and derived products | outside G0-K | G0 residual map 与后续 closure records | G0-L/G0-M 已单独接受；runtime setup 与 consumers 继续 held。 |

## 范围

G0-K 已接受范围：

- 定义并验证 deterministic generator request fields；
- 定义 tile/extent/seed partitioning 与 provenance rules；
- 定义 catalog descriptor 与 catalog admission rules；
- 定义 deterministic fixture output expectations；
- 添加 focused validation 与 determinism tests；
- terrain 作为第一条细化 branch，但 non-terrain branches 仍保留在同一
  environment root 下。

范围外：

- scenario compiler/runtime integration；
- C++ runtime ownership；
- checked-in generated scenario/environment artifacts；
- road graph、movement-cost grid、passability mask、LOS index、cover index 或
  tactical-area graph 等 derived products；
- movement、passability、LOS、cover、fires、damage、combat、weather simulation、
  hydrodynamics、hydrology effects 或 mutable environment state；
- 创建新的会话线程。

## 阶段计划

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `G0-K-A Request/Tiling Preflight` | 定义 deterministic request、tile、seed 与 provenance contract。 | G0-J accepted。 | worker packet 返回 inspected files、required fields 与 rejected shortcuts。 | pass |
| `G0-K-B Catalog Admission Preflight` | 定义 generic catalog descriptors 与 admission rules。 | G0-J accepted。 | worker packet 将 road/building/vegetation/infrastructure/tactical/weather objects 映射到 components，且不 hardcode schema。 | pass |
| `G0-K-C Determinism And Validator Preflight` | 定义 implementation 所需 fixture 与 validation gates。 | G0-J accepted。 | worker packet 命名 focused tests 与 fail-closed rejection cases。 | pass |
| `G0-K-D Integration Map` | 整合 worker packets 为有限 implementation plan。 | G0-K-A/B/C returned。 | 主线程命名有限 implementation write set 与 residuals。 | pass |
| `G0-K-E Implementation` | 实现 request/tile/catalog contracts 与 deterministic fixture。 | integrated preflight evidence。 | focused tests 通过且 runtime claims 继续 held。 | pass |
| `G0-K-F Acceptance` | 记录 accepted scope 并同步父级状态。 | focused tests 通过。 | G0-K 只接受 Python contract 与 fixture generation。 | accepted |

## 任务簇

- Task cluster plan：
  [environment_substrate_g0_generator_catalog_cluster_20260605.zh.md](environment_substrate_g0_generator_catalog_cluster_20260605.zh.md)

## 输出与证据

已接受输出：

- G0-K-A/B/C read-only worker packets 已整合进 cluster plan；
- [catalog.py](../../../../python/scenario/environment_substrate/catalog.py)；
- [generator.py](../../../../python/scenario/environment_substrate/generator.py)；
- [package exports](../../../../python/scenario/environment_substrate/__init__.py)；
- [focused generator/catalog tests](../../../../tests/scenario/test_environment_substrate_contracts.py)；
- [G0-K acceptance record](environment_substrate_g0_generator_catalog_acceptance_20260606.zh.md)。

## 验收门

G0-K 被接受，是因为：

- G0-K-A/B/C 均返回 `pass` 并已整合；
- implementation write set 有限，并与 runtime projection 分离；
- deterministic seed/tile/catalog behavior 有 focused tests；
- validators 会拒绝 omitted 或 mismatched request/catalog fields、unsupported
  schema roots、branch mismatches 与 held runtime claims；
- 父级 G0 docs 继续把 G0-K implementation 与 G0-L projection、G0-M derived
  products 分开。

## 残余与下一步

- G0-K 只接受 Python request/tile/catalog contracts 与 deterministic in-memory
  fixture generation。
- G0-K 历史 residual 中的 G0-L 已由 accepted G0-L projection setup plus compiler
  data ingestion 取代；runtime setup application 继续 held。
- G0-K 历史 residual 中的 G0-M 已由 accepted metadata-only derived products
  取代；runtime consumers 继续 held。
- Ground movement 与 combat 仍由单独 ground release gates 管辖。

## Archive

本文是当前 G0-K record。被取代的 G0-K dispatch notes 只有在未来 maintained
README/status 或 acceptance surface 指向替代入口后，才移入本地 `archive/`。
