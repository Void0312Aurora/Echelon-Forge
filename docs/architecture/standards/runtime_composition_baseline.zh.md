# Runtime Composition 基线

状态：`2026-08-23` maintained architecture standard，由已接受的有界 Cordis
仿真组合计划提升而来。

语言：

- 英文规范页：[runtime_composition_baseline.md](runtime_composition_baseline.md)
- 中文配套页：`runtime_composition_baseline.zh.md`

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/architecture/standards/runtime_composition_baseline.md`
Owner: `architecture/runtime-composition`
Last verified: `2026-08-23`

相关权威：

- [仿真系统架构设计](simulation_system_architecture_design.zh.md)
- [Runtime workflow 与 contract 基线](runtime_workflow_and_contract_baseline.zh.md)
- [已归档 Cordis composition 计划](../work/archive/cordis_simulation_composition_kernel/README.zh.md)

## 已接受边界

维护中基线只接受仓库自有 `builtin.default_compatibility` profile 与
`cpu_exact.reference` backend。Experiment intent 由仓库 Cordis producer lowering，
与 owner admission join，生成 canonical requested/resolved artifact，再由原生 C++
重新校验并仅由原生 runtime 执行。Python 是该原生 runtime 的已接受 caller，不是第二个
仿真 owner。

本标准不准入更多 profile/provider、CUDA parity、Node host、外部 plugin distribution
或 state-complete replay。

## 权威链

维护中的方向只有一条：

1. Experiment Face 拥有实验意图。
2. `@echelon-forge/cordis-runtime` 拥有已准入默认 profile 的高层 lowering 与仓库
   package/provenance layer。
3. 各 category owner 把 descriptor 准入版本化 catalog lock。Cordis 不能发明或私自
   准入 model、system、backend、domain、evidence 或 security implementation。
4. requested/resolved 低层 manifest 是 producer/native 交换面；原生代码重新解析、
   校验 identity 和 owner join。
5. `build_default_simulation_composition` 是唯一准入的 production entry，
   `build_default_simulation_composition_impl` 是唯一原生 model/service realization function；
   已记录的 test-only publication-failure wrapper 委托该 realizer。
   `materialize_default_world_batch_backend` 是维护中的 backend-provider materializer。
6. `SimulationKernel::step` 与原生 stage/runtime owner 继续是唯一确定性执行权威。
   Cordis 与 binding 不执行 semantic stage callback。

## 构造与兼容规则

- `SimulationKernel(std::string resolved_manifest_json)` 是显式原生 manifest bridge。
- `SimulationKernel()` 为既有 C++/Python diagnostics 与 compatibility caller 保留，但必须
  把生成的默认 resolved artifact 显式交给同一个原生 builder。空输入不得表示“选择隐藏
  default”。
- `WorldBatchRuntime` 是内部 native-backend wrapper。维护中的 host 代码通过
  `RuntimeFacade` 进入，concrete backend 只能由已准入 backend-provider catalog 选择。
- constructor、setter、binding、package 或环境变量不得成为另一条 model/service/system/
  backend composition truth source。
- test-only publication-failure seam 必须使用 generated 默认 artifact 与共享 native realizer；
  它只能注入具名 staged publication failure，不能成为 runtime configuration surface。
- 已退场 model replacement setter 必须保持不存在。未来 replacement protocol 需要
  owner 批准的 lifecycle/rebuild contract；禁止重新引入临时 setter。

## Graph、Lifecycle 与 Evidence 规则

- owner-derived contribution registry 与 admitted catalog lock 拥有 component/system/provider
  membership；文件发现和 Cordis package discovery 不授予 admission。
- realization 必须确定、transactional、generation-checked 且逆序 disposal；失败构造不得
  发布部分 service。
- truth-affecting rebuild 只能在声明 barrier 执行；raw-world exposure 或 world mutation 后，
  按原生 lifecycle contract fail closed。
- 维护中 evidence 绑定 request、catalog lock、profile projection、requested/resolved
  manifest、provider version、executable graph、backend、world/scope 与原生执行 owner；
  replay/comparison 对无法解释的 mismatch fail closed。
- host parity 用冻结 semantics 和独立批准的 performance budget 比较 native-direct 与本地
  Python caller；caller language 不改变 execution ownership。

## Security 与 Extension 规则

已接受 security 边界是仓库构建且由 owner 准入的代码与封存 package provenance。
本基线不准入外部 native artifact。签名、distribution、ABI trust、sandbox、remote catalog
与 marketplace policy 需要独立批准的 security program。

## Held 残余

| 残余 | Owner | 激活 gate |
| --- | --- | --- |
| Node host adapter | `interfaces/node` | 明确批准的 host use case 与 P6-B dispatch |
| 更广 profile/provider | `architecture/runtime-composition` 加 category owner | owner admission 与 profile/provider parity evidence |
| CUDA backend parity | `runtime/backend` | 独立 exact-runtime CUDA admission 与 parity gate |
| 外部 plugin distribution/signing | `owner.security` | authenticity、ABI、distribution 与 trust policy |
| 完整 state replay | `runtime/evidence` | 超出 composition compatibility 的 state-complete replay contract |

held 残余不得削弱默认 producer/native 路径，也不会因未来使用“plugin”或“Cordis”字样而
被隐式接受。

## 可执行治理

P8 closure record 是
[`default_runtime_composition_migration_closure.v1.json`](../../../tests/architecture/composition/fixtures/default_runtime_composition_migration_closure.v1.json)，
由
[`runtime_composition_migration_closure.py`](../../../tools/maintenance/runtime_composition_migration_closure.py)
生成和校验。guard 清点维护中 caller，绑定已接受 authority hash，证明退场 surface 不存在，
并拒绝重新封存的 authority、caller、setter、residual owner 或 Node-admission forgery。

修改本基线需要相关 owner、重生成 closure evidence、Cordis/native vertical conformance、
聚焦 native/Python test 与 documentation/link validation。
