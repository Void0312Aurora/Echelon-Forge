# `src/runtime/composition` 边界

状态：`2026-08-17` P2-A 原生 lifecycle baseline 与独立审阅修复批次已实现并通过聚焦
测试；不声明已迁移 engine、provider family、system、backend facade、binding 或 Cordis。

语言：

- 英文规范页：[README.md](README.md)
- 中文配套页：`README.zh.md`

## 目的

本目录将 [`runtime/contracts`](../contracts/README.zh.md) 中 host-neutral composition
value 实现为隔离的原生 lifecycle library。它解析 closed JSON envelope，重算
requested/resolved identity，验证 graph 与稳定顺序，冻结 provider catalog，事务式构造 scoped provider
instance，只在 commit 时发布 staged lifecycle effect，并按 realized dependency 的逆序
teardown。

目标为 `ef_composition`。它有意不链接 `ef_core`、`ef_facade`、Flecs、nanobind、Node
或 Cordis；唯一 implementation-only dependency 是原生 JSON ingestion boundary 使用的
`nlohmann_json`。

## Lifecycle 模型

1. 解析 closed requested/resolved JSON envelope。missing/extra field、错误类型、浮点配置
   值与未知 scope 在 factory lookup 前失败。
2. 冻结 `ProviderCatalog`；freeze 后拒绝继续注册。
3. 重新计算并验证 requested/resolved SHA-256、稳定 provider/system order、service
   binding、scope capture、conflict/cycle、backend、policy 与不可变 factory metadata 规则。
4. 按已验证 dependency order 构造 provider。factory 必须立即通过 `ILifecycleEffect`
   登记全部外部副作用。
5. 只有全部 provider 存在后才 commit staged effect。任何 construction/effect-commit
   失败都会逆序销毁 candidate instance 并 rollback effect，不发布 runnable runtime。
6. 冻结 runtime，并暴露带 generation check 的 `ServiceHandle<T>`。
7. 将一个 scope 及全部 descendant 构造成 candidate generation，并可输入新验证的 resolved
   manifest/catalog。失败时旧 generation 与 identity 保持 live；成功后无分配交换 record/plan、
   使旧 handle 失效并逆序 dispose retired provider。
8. stop 幂等，先使 handle 失效、逆转 external effect，再按 provider 逆序销毁 instance。

## Handle 与 Barrier 合同

`ServiceHandle<T>` 不拥有资源。consumer 保留 handle，而不是保留 `try_get()` 返回的
pointer。lifecycle rebuild/stop 只能发生在既有治理下已经 quiescent 的 barrier，不能与
active simulation-stage access 并发。这与父架构一致：影响 truth 的 reconfiguration 只在
`pre_run`、`world_rebuild` 或 `episode_end` 发生，不能 mid-step。

handle control block 携带 provider ID、scope、generation 与 atomic active bit，并在成功
rebuild/stop 后拒绝访问。它无法让 caller 私自保留的 raw pointer 变安全；这种保留仍是
禁止的 consumer 行为，必须在 provider migration 时消除。
Native runtime 会串行化 lifecycle control operation。runtime 只允许 move construction，
明确禁止 move assignment，避免 callback 通过隐式 move assignment 销毁当前实现。

## Effect 合同

`ILifecycleEffect` 表示 provider instance 内普通 C++ RAII 无法单独逆转的外部发布：

- `commit()` 发布 staged effect，可以失败；
- `rollback()` 逆转 staged 或 committed 状态，且幂等；
- `dispose()` 执行正常 committed teardown，且幂等；
- old/new generation 都发布外部状态时必须通过 `supports_replacement_handover()`，其 opt-in
  承诺 cleanup 只作用于 effect 自有 token/generation；
- 两个 terminal method 都是 `noexcept`，保证 unwind 必定完成。

factory 在 `construct()` 中必须 stage 外部状态，而不能进行不可逆发布。无法满足此规则的
provider 不得进入本 lifecycle kernel，除非另行验收 handover 设计。

## Public Surface

- `composition_json.h`：将 closed native JSON 解析为 P1-B value type；
- `composition_identity.h`：共享 manifest/resolved canonical-byte SHA-256；
- `provider_catalog.h`：factory catalog、provider/effect interface、带 generation check 的
  typed handle 与 construction context；
- `composition_runtime.h`：原生 validation、realization、service lookup、replacement-aware
  scoped rebuild、immutable identity/generation query 与 deterministic stop；
- `composition_error.h`：稳定 native lifecycle error code 与 result value。

## 当前证据与残余

聚焦 C++ suite 解析并验证冻结的 11-provider/82-component/34-system fixture，并测试 catalog
freeze、hash tamper、非法 typed scope、自依赖 cycle、不可变 plugin/factory identity、稳定
service ABI、typed service lookup、失败清理顺序、lifecycle 重入、并发 rebuild 串行化、
effect-commit failure、完整 rollback、replacement-aware scope rebuild、handover admission、
stale-handle rejection 与 reverse teardown。聚焦 executable 在普通 MSVC build 与
RelWithDebInfo MSVC AddressSanitizer build 中均通过 14 个 test case、381 个 assertion；
architecture contract suite 为 20 passed、1 个 toolchain-dependent skip。

本 baseline 使用同一冻结 fixture/canonical field rule 重算并公开 P1-B requested/resolved
identity，不创建私有 runtime identity。Artifact provenance/signature 与 Cordis producer 的逐字节
conformance 仍是后续 admission gate。默认 model 构造与全部 simulation behavior 继续走既有
路径，直到后续 migration cluster 提供 parity evidence。

canonical contract 的长期语义仍是 Unicode NFC。当前原生 v1 admission profile 只接受
ASCII string 与 object key；ASCII 是 NFC-safe 子集。在 Python producer 与原生 runtime
共享同一个 normalization implementation 之前，非 ASCII manifest 将 fail closed。
