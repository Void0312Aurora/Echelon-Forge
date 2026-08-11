# 环境系统

语言：[英文主文](README.md)；中文配套。

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/systems/environment/README.md`
Owner: `systems/environment`
Last verified: `2026-08-08`

本 owner 负责跨域环境 manifest、来源准入、生成器/catalog 合同、projection
payload、compiler ingestion 与环境派生产品。Ground 场景提供了第一批需求，但不拥有
共享 environment substrate。

## 当前权威入口

- [Environment Substrate G0 闭合记录](reviews/environment_substrate_g0_closure_20260606/README.zh.md)：
  static manifest、deterministic generator/catalog、inert projection payload、
  strict compiler ingestion 与 metadata-only derived products 的 accepted review。
- [Arnis Adapter 第一阶段](reviews/arnis_adapter_phase1_20260715/README.zh.md)：
  固定真实地理输入、连续米制导出、fail-closed CMO 导入和离线静态场景派生的
  accepted review。
- [Ground 特化](../../domains/ground/README.zh.md)：Ground task/status 语义及当前
  capability boundary 的 owner。

## G0 与 G1 边界

历史包中的同名阶段属于不同范围：

- Ground `G0/G1` 表示有限的 Ground task/status 与静态场景成熟度，不授予共享
  environment runtime 权威。
- Environment-substrate `G0` 是已接受的跨域数据合同线，到 runtime setup
  application、movement、passability、LOS、cover、fires、damage、hydrodynamics
  与 combat 之前停止。
- Arnis 第一阶段只提供带来源的静态输入和离线 preview，不构成 environment-runtime
  `G1` 发布。

这些 review 没有授权 environment-runtime `G1`。后续 runtime 包必须在
`systems/environment/work/active/` 下单独建立范围与验收证据。

## 当前实现入口

- Manifest 与 validators：`python/scenario/environment_substrate/`
- Scenario compiler ingestion：`python/scenario/compiler/`
- Arnis 工具：[tools/environment/arnis](../../../tools/environment/arnis/README.zh.md)
- 固定 Arnis fixture：
  `tests/scenario/fixtures/environment_substrate/arnis_bundle_v1/`

带日期 review 保留其原始证据边界，不授权扩大 capability claim，也不应继续旧
dispatch queue。
