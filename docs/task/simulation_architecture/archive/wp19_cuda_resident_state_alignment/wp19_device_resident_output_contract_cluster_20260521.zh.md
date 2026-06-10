# WP19-B Device-Resident Output Contract Pre-Gate

状态：`2026-05-21` pass / export-only DTO seam accepted。

语言版本：

- 英文主文：[wp19_device_resident_output_contract_cluster_20260521.md](wp19_device_resident_output_contract_cluster_20260521.md)
- 中文辅文：`wp19_device_resident_output_contract_cluster_20260521.zh.md`

输入：

- [WP19 主计划](cuda_resident_state_alignment_wp19_20260521.zh.md)
- [WP6 resident-state 边界规则](../wp6_backend_profile_policy/wp6_resident_state_boundary_rules_20260519.zh.md)
- [WP13 backend fidelity expansion](../wp13_backend_fidelity_expansion/backend_fidelity_expansion_wp13_20260520.zh.md)

## 目的

定义最小 facade/backend 契约面，使 device-resident outputs 可被描述，但不会被误解为
maintained resident-state ownership。

本轮 preflight 结论：

- 当前 maintained/export DTO 已经具备 host-visible snapshot 与 barrier
  identity，但并不携带 device-buffer metadata。
- `RuntimeCapabilities` 与 backend profile projection 已经对
  `supports_device_observation_view`、`supports_resident_state` 与 exact GPU
  support 保持 fail-closed。
- 因此 WP19-B 不应把 device-resident descriptor 直接塞进现有 maintained
  packet DTO。安全落点是 additive seam：把专门的 export-only/device-output
  descriptor 放在 maintained packet 真值路径旁边，而不是嵌进去。

## 范围

范围内：

- device output shape、dtype、element count、source snapshot、sync/export barrier、
  host-visible availability、diagnostics label 与 consumer constraints 的 metadata 要求；
- 没有 maintained profile 时请求 device-resident outputs 的 fail-closed 行为；
- DTO/binding 放置点的聚焦测试或 preflight notes。

范围外：

- maintained resident-state promotion；
- exact GPU execution；
- broad facade redesign。

## 基于源码的发现

| 来源 | 当前事实 | 对 WP19-B 的含义 |
|------|----------|------------------|
| `src/runtime/facade/runtime_facade_types.h` | `ObservationBatchPacket` 已暴露 `snapshot_version`、`barrier_id`、`source_time_s` 与 maintained `provenance`。`EngagementEventPacket` 已暴露 `snapshot_version`、`barrier_id`、`barrier_sequence`、`barrier_detail` 与 diagnostics provenance。 | maintained facade 已经有 host-visible export envelope 与 diagnostics ancestry vocabulary。若直接复用这些 packet 承载 device pointer 语义，会把 export truth 与 backend-local transport 混在一起。 |
| `src/interfaces/python/bindings_runtime.cpp` | Python bindings 只暴露 `ObservationBatchPacket` 与 `EngagementEventPacket` 的 host-visible packet 字段，没有任何 device-buffer descriptor。 | 第一版 device-resident contract 必须是 additive 且显式绑定，不能从现有 packet binding 中被静默推断。 |
| `src/runtime/facade/runtime_facade.cpp` | `RuntimeFacade::capabilities()` 将 `supports_device_observation_view = false`、`supports_resident_state = false`、`supports_exact_gpu_backend = false` 写死。 | device-output availability 不能投影成 maintained support。 |
| `src/runtime/contracts/backend_profile_contracts.h` | diagnostics-only 与 unmaintained profile 不能授权 exact GPU、resident-state、shadow 或 device observation support。 | device-resident output descriptor 在后续 maintained profile 显式提升前，必须保持 `export-only` / diagnostics-only。 |
| `WP6 resident-state boundary rules` | 没有被接受的 host-visible reconstruction/export rule 与 barrier 前，unsynced backend-local state 都是 diagnostics-only。 | 没有声明 export barrier 与 host-visible rule 的 device-resident buffer 不能被视为 maintained state 或 parity evidence。 |
| `WP13 backend fidelity expansion` | capability projection 是保守的 query surface，不是 transport/data-plane schema。 | WP19-B 不能把 per-output shape 或 buffer metadata 塞进 `RuntimeCapabilities`。 |

## 最小契约字段

最小可接受的 device-resident output descriptor 应包含：

| 字段 | 必需语义 | 当前 host/export 来源 | 放置结论 |
|------|----------|----------------------|----------|
| `output_shape` | 导出 tensor/buffer 的逻辑 shape。 | 目前没有。 | 需要 additive DTO seam。 |
| `dtype` | 导出 buffer 的标量元素 dtype。 | 目前没有。 | 需要 additive DTO seam。 |
| `element_count` | shape 归一化后的逻辑元素总数。 | 目前没有。 | 需要 additive DTO seam。 |
| `source_snapshot` | 该 device buffer 所来源数据的归一化 snapshot identity。 | 已有 `snapshot_version` / `source_snapshot_version` vocabulary。 | 在 additive descriptor 中复用现有 snapshot vocabulary；不要替换 maintained packet 字段。 |
| `sync_or_export_barrier` | 该 descriptor 可被消费或导出的 barrier id；必要时还需 barrier detail/sequence。 | 已有 `barrier_id`、`barrier_detail`、`barrier_sequence`。 | 在 additive descriptor 中复用现有 barrier vocabulary。 |
| `host_visible_availability` | 当前是否已有 host-visible mirror/export、是否需要显式 readback、或者当前不可见。 | 目前没有独立 output contract。 | 需要 additive DTO seam。 |
| `diagnostics_label` | 显式标签，如 `diagnostics_only`、`export_only_candidate`，或以后某种 maintained classification。 | 已有 diagnostics-only vocabulary 与 maintained-status labels。 | 复用词汇，但按每个 output 放在 additive descriptor 中。 |
| `consumer_constraints` | 声明该 payload 仅允许 device-resident consumer、仅允许显式 host export/readback，或仅允许 diagnostics evidence。 | 目前没有。 | 需要 additive DTO seam。 |

归一化规则：

- `element_count` MUST 等于 `output_shape` 的乘积；标量输出必须归一化成显式
  one-element shape，或使用 producer/consumer 共享的单一文档化约定。

## DTO 放置决策

决策：

- 不要把 device-resident 字段直接加到 `ObservationBatchPacket`。
- 不要把 device-resident 字段直接加到 `EngagementEventPacket`。
- 不要把 per-output transport metadata 加到 `RuntimeCapabilities`。
- 应使用 additive DTO seam：把 export-only metadata 放在 maintained
  packet/result 旁边，并引用同一个 snapshot/barrier source。

为什么现有 DTO 不是合适的 seam：

1. `ObservationBatchPacket` 与 `EngagementEventPacket` 已是 host-visible
   maintained/export envelope。它们表示已经跨过 facade 边界的内容，而不是
   opaque backend-local transport。
2. 现有 bindings 与 tests 都假设这些 DTO 是 host-readable 的结构化 payload。
   如果把 device descriptor 回填进去，会让所有既有调用方在没有显式契约升级的
   情况下看起来像是“已经 device-aware”。
3. `RuntimeCapabilities` 是 maintained support projection，用来回答“支持什么”，
   不是回答“某个 barrier 上产出的 buffer 长什么样”。

安全的 additive 形态：

- 未来 DTO 可以是一个很小的 `DeviceResidentOutputDescriptor` 或
  `DeviceResidentExportDescriptor`。
- 它只应挂在 export-only/diagnostics 的 result seam 上，例如某个 result packet
  的可选 sibling collection，或某个专门的 diagnostics export result。
- 该 additive descriptor MUST 通过 `source_snapshot` 与
  `sync_or_export_barrier` 回指 maintained/export source；它 MUST NOT 变成第二条
  authoritative truth path。

## Fail-Closed 规则

WP19-B 要求以下 fail-closed 行为：

1. 缺少 `output_shape`、`dtype` 或 `element_count` 时，该 descriptor 无效，
   output 对 consumer 不可用。
2. `element_count` 与归一化后的 `output_shape` 不一致时，该 descriptor 无效。
   该 output MUST 被隔离为 diagnostics-only，且 MUST NOT 作为 parity 或
   maintained export claim 的依据。
3. 缺少 `source_snapshot` 或 `sync_or_export_barrier` 时，该 output 属于无来源
   输出。无来源输出 MUST 只能作为 backend-local diagnostics。
4. 如果 `host_visible_availability` 没有明确说明已有 host-visible export，
   调用方 MUST 假定 maintained facade surface 上不可直接 host-readback。
5. 缺少 `diagnostics_label` 时，默认是 diagnostics-only rejection，而不是静默提升。
6. 缺少 `consumer_constraints` 时，消费被阻断。调用方 MUST NOT 推断 host
   consumer、device consumer 与 diagnostics consumer 可以互换。
7. descriptor 的存在 MUST NOT 设置或暗示
   `supports_device_observation_view`、`supports_resident_state`、
   `supports_exact_gpu_backend` 或 `supports_shadow_compare`。
8. device pointer、CUDA helper success、benchmark speedup 或 GPU build success
   都 MUST NOT 替代 `source_snapshot`、barrier metadata 或 maintained profile
   acceptance。

## Consumer Constraint 分类

WP19-B 区分三类 consumer：

| Consumer 模式 | 允许的契约 | 禁止的推断 |
|---------------|------------|------------|
| `host_readback` | Consumer 收到一个 maintained/export packet，或在声明的 barrier 上收到显式 host-visible mirror。 | MUST NOT 仅凭 device-local descriptor 就推断其可 host-read。 |
| `device_resident_consumer` | Consumer 只有在接受 descriptor 的 `dtype`、shape、barrier 与 diagnostics/export label 时才能读取该 device-resident output。 | MUST NOT 推导出 maintained resident-state ownership 或 device observation support。 |
| `diagnostics_only` | Output 可以作为 report-only evidence 被记录、profile 或比较。 | MUST NOT 驱动 committed state、fallback 选择、capability promotion 或 parity acceptance。 |

## 聚焦测试切片

本轮 preflight 添加的安全 guard：

- `tests/architecture/runtime_facade/test_runtime_dto_contracts.py` 现在断言
  `ObservationBatchPacket` 与 `EngagementEventPacket` 保持其 host-visible
  metadata surface，且不会静默长出 device-resident descriptor 字段。这样可以保护
  additive seam 决策，而不改变 runtime 行为。

WP19-B2 的实现更新：

- `src/runtime/facade/runtime_facade_types.h` 现在定义了一个 additive、
  export-only 的 `DeviceResidentOutputDescriptor`，携带
  `output_shape`、`dtype`、`element_count`、`source_snapshot`、
  `sync_or_export_barrier`、`host_visible_availability`、
  `diagnostics_label` 与 `consumer_constraints`。
- `src/interfaces/python/bindings_runtime.cpp` 现在把该 descriptor 作为独立 DTO
  暴露到 Python，并保持 fail-closed 默认值。
- `ObservationBatchPacket`、`EngagementEventPacket` 与
  `RuntimeCapabilities` 保持原状，继续作为 host-visible packet/support surface；
  descriptor 不会被内联进去，也不会提升任何 support flags。

本轮仍故意不加的测试或行为：

- 不加 CUDA helper implementation tests。
- 不新增 support-flag promotion tests；现有 `RuntimeFacade::capabilities()` 与
  backend-profile contract coverage 已足够保守。
- 不把 descriptor 挂到 maintained packet DTO 或 capability projection 上。

## 任务项

| ID | 任务 | 验收 |
|----|------|------|
| `B1` | Contract fields | 完成。最小字段被拆分为可复用的 snapshot/barrier vocabulary，以及必须 additive 引入的 shape/dtype/count/availability/consumer metadata。 |
| `B2` | Fail-closed projection | 完成。preflight 保证 device output descriptor 不会暗示 `supports_resident_state`、`supports_device_observation_view` 或 exact GPU support。 |
| `B3` | Consumer constraints | 完成。Host-readback、device-resident 与 diagnostics-only consumer 已被明确区分。 |
| `B4` | Test plan or tests | 按 implementation 标准完成。聚焦 binding 与 architecture guard 证明了独立 descriptor 的字段、fail-closed 默认值、可赋值性，以及 packet/capability 边界未被内联突破。 |

## 建议验证

```bash
git diff --check
python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "capab or backend or profile"
python -m pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py
python -m pytest -q tests/architecture/runtime_facade/test_runtime_dto_contracts.py -k "device_resident or packet"
```

## Residuals

- 当前 descriptor 仍只是 export-only metadata；runtime 结果面尚未发布任何
  descriptor collection。
- 目前还没有 maintained profile 声明 device-resident consumer contract、
  host reconstruction rule 或 resident-state promotion gate。
- 后续若要超出 export-only diagnostics，仍需等待 WP19-D 正式收敛
  shard/barrier ownership 语言。

## 交付

返回 contract fields、touched files、tests run、blockers，以及该 stream 是否
implementation-ready 或 preflight-only。

WP19-B2 完成后的当前建议返回：

- Status: `pass`
- Implementation readiness: additive DTO seam 已作为独立 export-only
  descriptor 落地，但后续集成仍必须保证它不进入 maintained packet DTO、
  capability projection 或 support-flag promotion 路径。

## Closure Outcome

WP19-B 在 WP19 范围内以 additive export-only descriptor seam 通过验收。它尚不从
runtime result packet 发布 descriptor collections，也不晋级 exact GPU、
device-observation 或 maintained resident-state support。
