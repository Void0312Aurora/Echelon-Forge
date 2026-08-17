# Cordis 仿真组合合同 — 2026-08-17

状态：`2026-08-17` P1-B contract baseline 与 P2-A 原生 realization/identity 修复已实现并
验证；production provider migration 仍属于 P2-B。

语言：

- 英文规范页：[cordis_simulation_composition_contract_20260817.md](cordis_simulation_composition_contract_20260817.md)
- 中文配套页：`cordis_simulation_composition_contract_20260817.zh.md`

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/cordis_simulation_composition_kernel/cordis_simulation_composition_contract_20260817.md`
Owner: `architecture/runtime-composition`
Last verified: `2026-08-17`

父项目：[Cordis 仿真组合内核](README.zh.md)

## 决策

P1-B 冻结 host-neutral requested manifest 与 deterministic resolved envelope。
Cordis、native static profile、Python tooling 或未来 Node host 均可生成 requested JSON
shape。Native code 继续负责 revalidation、capability/stage admission、provider
construction、scope transaction、executable graph realization 与 evidence export。

Contract 有五类 artifact：

| Artifact | 权威与用途 |
| --- | --- |
| [`simulation_composition_contract.py`](../../../../../tools/maintenance/simulation_composition_contract.py) | executable schema source、normalization rule、stable diagnostics、deterministic graph ordering 与 compatibility-fixture generator |
| [`simulation_composition_manifest.v1.schema.json`](../../../../../src/runtime/contracts/composition/simulation_composition_manifest.v1.schema.json) | 生成的 host-neutral transport schema |
| [`resolved_simulation_composition.v1.schema.json`](../../../../../src/runtime/contracts/composition/resolved_simulation_composition.v1.schema.json) | 生成的 closed resolved-envelope transport schema |
| [`simulation_composition_contract.h`](../../../../../src/runtime/contracts/simulation_composition_contract.h) | 与 JSON library 无关的 C++ value contract、stable service key、scope、version 与 error code |
| default requested/resolved fixture | 冻结的 cross-implementation conformance 与 migration baseline |

Python executable specification 不是 runtime owner。Native resolver/validator 现会针对这些
fixture 重算相同的 requested/resolved SHA-256，并在构造任何 provider 前证明
diagnostic-code 与 ordering parity。

## 版本化 Envelope

Requested manifest schema：

```text
echelon_forge.simulation_composition_manifest.v1
```

Resolved envelope schema：

```text
echelon_forge.resolved_simulation_composition.v1
```

Resolver contract：

```text
echelon_forge.simulation_composition_resolver.v1
```

Requested manifest 不包含 self-hash。Resolved envelope 携带：

- normalized requested manifest；
- requested-manifest SHA-256；
- dependency-safe provider construction order；
- deterministic system registration order；
- resolver contract version；
- resolved-manifest SHA-256。

Resolved SHA-256 preimage 只省略 `resolved_manifest_sha256` 字段。这避免未定义的
self-referential hash，同时覆盖所有其他 identity-bearing field。

## Requested Manifest 字段

| 字段 | 规则 |
| --- | --- |
| `schema_version` | 精确支持的 schema ID；未知版本在 resolution 前失败 |
| `composition_id` | 与 host/discovery order 无关的 stable lower-case semantic ID |
| `contract_versions` | composition、runtime、content、stage contract version |
| `requested_profile` | profile ID/version；选择 profile 本身不授予 capability |
| `plugins[]` | implementation/version、host support、determinism class、artifact identity、requirement、conflict 与 canonical configuration |
| `providers[]` | scope、offered/required service、capability requirement、conflict、restart/teardown policy 与显式 ordering dependency |
| `service_bindings[]` | 精确 consumer/service/provider edge；禁止 implicit last-registration-wins |
| `component_contributions[]` | stable component identity 与 registration identity |
| `system_contributions[]` | registration factory、domain、service/component requirement、stage join、state shard、barrier、capability、conflict 与 graph edge |
| `backend_request` | requested backend profile 与提供 `runtime.world_batch_backend` 的 provider |
| `scope_policies[]` | 完整 application/backend/batch/world/episode hierarchy |
| `reconfiguration_policy` | truth-affecting change 重建 scope generation，active episode 内禁止 |
| `evidence_policy` | mandatory canonicalization、SHA-256、provider-version、graph-hash、scope-generation evidence |
| `compatibility_claims[]` | 显式临时 migration claim；不能成为 implicit fallback authority |

Object 默认关闭：未知字段被拒绝。这强制通过 schema versioning 演进，避免 host 添加私有
authority-bearing field。

## Canonicalization

Canonicalization ID：

```text
echelon_forge.sorted_utf8_json.v1
```

规则：

1. 所有 string 与 object key 规范为 Unicode NFC；
2. object key 按 Unicode 升序序列化；
3. JSON 使用 UTF-8，无非必要空白，不使用 ASCII-only escaping；
4. boolean 与 `null` 使用标准 JSON literal；
5. numeric value 只允许 signed 64-bit integer；
6. v1 configuration 禁止 floating-point；物理小数必须使用 schema-owned integer unit
   或 normalized decimal string；
7. entity array 按 stable semantic ID 排序；
8. set-like array 唯一化并按 UTF-8 byte order 排序；
9. provider/system execution order 由 stable topological sort 推导，只用 semantic ID
   作为 tie-breaker；
10. source-file order、plugin discovery order、map insertion order、filesystem path、PID、
    timestamp、object address 不进入 hash input。

禁止浮点是有意决策，用于避免基础 contract 的跨语言数字渲染歧义。后续版本可引入单独
测试的 numeric canonicalization standard，但不能静默改变 v1 hash。

## Scope 与 Binding 规则

固定 scope order：

```text
application -> backend -> batch -> world -> episode
```

Provider 可以向同 scope 或 descendant 提供 service。Parent consumer 不能持有 child
provider。v1 中每个 required provider/system service 必须有且只有一个 explicit binding。
Collection、reducer、chain、fallback、priority semantic 需要后续显式 contract；v1 不推断。

冻结的 service-key set 覆盖：

- environment、unit factory、effects、sensor、acoustic、control、guidance；
- engagement event recorder；
- weapon-release damage bridge 与 release service；
- world-batch backend；
- composition evidence sink。

这些 key 命名 semantic service，不暴露 C++ pointer、Flecs singleton、Cordis object
identity 或 binding-language object。

## Resolution 与失败语义

P1-B executable specification 执行确定性、无资源的 resolution 部分：

1. 拒绝 unsupported schema/contract version 与 malformed ID；
2. 拒绝 duplicate plugin/provider/component/system ID 与 duplicate set entry；
3. 验证 plugin/provider ownership 与 stable service key；
4. 每个 required service 必须有且只有一个 explicit binding；
5. 验证 selected provider 确实提供 bound service；
6. 拒绝 child-to-parent scope capture；
7. 拒绝 selected provider/system conflict；
8. 从 service binding 与 explicit `after_provider_ids` 构造 provider dependency edge；
9. 从 `after`/`before` 构造 system dependency edge；
10. 以 stable diagnostic code 拒绝 dependency cycle；
11. backend provider 必须提供 semantic backend SPI；
12. 验证完整 scope hierarchy 与 immutable-episode policy；
13. normalize、topologically order、serialize、hash 结果。

Capability admission、semantic-stage ownership、domain maturity、backend promotion、artifact
authenticity、runtime resource construction 不由该 resolver 授予。P2/P3/P4 必须连接既有
owner contract，并在 realization 前 fail closed。

Stable diagnostic code 在 C++ 与 executable specification 中镜像，包括 duplicate ID、
missing/ambiguous binding、unknown service、scope capture、provider/system conflict/cycle、
backend mismatch、invalid policy 与 noncanonical number。

## 默认 Compatibility Profile

生成的 default fixture 冻结迁移前 composition inventory：

| 表面 | 冻结数量 |
| --- | ---: |
| built-in plugin descriptor | 1 |
| 包含 CPU backend 的 provider | 11 |
| kernel model/factory provider | 7 |
| kernel service/event provider | 3 |
| component contribution | 82 |
| system contribution | 34 |
| scope policy | 5 |

34 个 system contribution 通过 dependency chain 复现当前 registration order。存在当前
exact descriptor 时附加 exact-stage name。空 semantic-stage/read-write/barrier field 是显式
compatibility gap，不证明这些 system 无需 contract。P3 必须连接 stage/domain owner 后才能
移除中央 registration list。

Requested fixture 使用 repository-source artifact identity，artifact SHA-256 为 null，因为
P1-B 不构建或签名 distributable artifact。外部 package acceptance 前，resolved runtime
evidence 必须替换为 admitted artifact provenance。

## Conformance Evidence

P1-B architecture suite 证明：

- generated schema 与 requested/resolved fixture freshness；
- schema object closed 且 host-neutral；
- C++ version、scope、service key、error code 与 executable specification 一致；
- default fixture 精确跟踪 `simulation_kernel_systems.cpp` 中 82 个 component 与 34 个
  system call；
- 每个 required service 有唯一 scope-safe binding；
- 32 种 input permutation 生成相同 byte、hash 与 order；
- resolved self-hash exclusion 精确；
- 10-case invalid-manifest matrix 对 version、duplicate、missing/ambiguous binding、scope
  capture、conflict、cycle、backend、number violation fail closed；
- Draft 2020-12 schema validation 接受 default fixture；
- C++ value header 通过 MSVC C++20 syntax check。

## P1-B Closure 与 P2 入口

P1-B 在 contract boundary 通过。它不声明 native runtime resolver、provider construction、
rollback、generation-checked handle、system graph realization、Cordis package、Node host 或
behavior parity。

P2-A 随后在隔离的 `ef_composition` library 中实现以下约束：

- native parsing/validation 必须复现冻结 fixture 与 stable diagnostic code；
- complete manifest/graph admission 前不得创建 runtime resource；
- scope construction 必须 transactional，disposal 反向遍历 realized dependency graph；
- handle 携带 scope generation，并拒绝 stale access；
- successful native realization 按冻结 canonical field rule 重算并导出 requested/resolved
  hash，既不信任 producer claim，也不创建私有 identity；
- replacement rebuild 接受新验证的 manifest/catalog，失败时保留旧 identity，并要求
  token/generation-safe effect handover；
- Python executable specification 只作为 conformance oracle，绝不进入 maintained simulation
  step path。

该实现 checkpoint 不修改 P1-B hash 语义；它加入 native canonical-byte/hash 重算、生成的
resolved-envelope schema、typed-scope fail-closed validation 与 Python/schema/native parity
修复。Cordis producer 逐字节 conformance、Unicode 多实现一致性、artifact provenance、
production provider construction 与 behavior parity 仍是 P2-B/P6 起的后续 gate。
