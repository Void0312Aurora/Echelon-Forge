# WP19 Subagent Dispatch Queue

状态：`2026-05-21` closed / accepted。

语言版本：

- 英文主文：[wp19_subagent_dispatch_queue_20260521.md](wp19_subagent_dispatch_queue_20260521.md)
- 中文辅文：`wp19_subagent_dispatch_queue_20260521.zh.md`

派发 subagents 时使用该队列。主线程负责 integration 与 final acceptance。

## 第一轮

| Stream | Agent type | 模型 / 思考预算 | 任务 | 写入范围 |
|--------|------------|-----------------|------|----------|
| `WP19-A` | worker | `gpt-5.4-mini`, xhigh | 核验 CUDA/resident-state facts、helper/probe surfaces、support flags 与 first-slice candidates。 | 仅 WP19-A ledger docs 与 read-only inventory notes；不改 runtime behavior。 |
| `WP19-B` | worker | `gpt-5.4`, high | 预检 device-resident output contract，并识别 DTO/test placement，不晋级 support。 | Contract/DTO preflight notes 与安全时的聚焦测试；不编辑 CUDA helpers。 |
| `WP19-C` | worker | `gpt-5.4`, high | 收紧或预检 GPU helper/probe diagnostics boundary 与 non-promotion tests。 | GPU helper binding/architecture tests 或 notes；不编辑 sync/shard semantics。 |
| `WP19-D` | worker | `gpt-5.4`, xhigh | 构建映射到当前 runtime evidence 的 resident-state sync/shard preflight。 | Sync/shard contract docs/tests only；不编辑 CUDA helper implementations。 |

## 暂缓流

| Stream | 释放条件 |
|--------|----------|
| `WP19-E` | A-D 返回安全 bounded helper/output slice 后释放。 |
| `WP19-F` | A-E 返回 mergeable 或 blocked packets 后释放。 |

## 第一轮返回状态

| Stream | Agent | Return status | Planning consequence |
|--------|-------|---------------|----------------------|
| `WP19-A` | Turing | `preflight-only / pass` | CUDA helper、probe、capability 与 `WorldBatchRuntime` facts 已冻结到 WP19-A ledger。除非选出 bounded host-owned helper slice，否则 WP19-E 仍保持 preflight。 |
| `WP19-B` | Singer | `preflight-only / pass` | additive device-resident descriptor seam 已成立，但不得嵌入 `ObservationBatchPacket`、`EngagementEventPacket` 或 `RuntimeCapabilities`。 |
| `WP19-C` | Descartes | `pass after standard-env revalidation` | helper/probe diagnostics guards 与 tests 已收紧。初始 blocker 是裸 `python` 加载全局旧 `ef_py`；使用 `bash tools/maintenance/cmo_env.sh` 后 suite 通过。 |
| `WP19-D` | Ramanujan | `preflight-only / pass` | resident-state shard/barrier/ownership baseline 已映射到当前 runtime evidence。不支持 resident-state promotion。 |

第一轮后的主线程验证：

- `git diff --check` 通过。
- `python -m py_compile tests/architecture/runtime_facade/test_layering.py tests/test_gpu_runtime_bindings.py tests/architecture/runtime_facade/test_dto_contracts_batch1.py` 通过。
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/runtime_facade/test_layering.py` 通过：`22 passed`。
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/test_gpu_runtime_bindings.py` 通过：`12 passed`。
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/runtime_facade/test_dto_contracts_batch1.py -k "device_resident or packet"` 通过：`2 passed, 4 deselected`。
- `python3 tools/maintenance/wp_doc_closure_audit.py --wp WP19 --summary` 通过。

## 第二轮

| Stream | Agent type | 模型 / 思考预算 | 任务 | 写入范围 |
|--------|------------|-----------------|------|----------|
| `WP19-B2` | worker | `gpt-5.4`, high | 实现 additive export-only `DeviceResidentOutputDescriptor` seam，补 bindings 与 tests，但不挂到 maintained packets 或 capability projection。 | `src/runtime/facade/runtime_facade_types.h`、`src/interfaces/python/bindings_runtime.cpp`、聚焦 binding/architecture tests 与 WP19-B docs。不要编辑 CUDA helper implementations 或 `WorldBatchRuntime`。 |
| `WP19-E1` | worker | `gpt-5.4`, xhigh | 选择并且仅在安全时实现一条 host-owned broadphase candidate-list alignment slice，显式保留 host post-filter evidence。 | `src/core/engine/world_batch_runtime.*`、`tests/world_batch/test_world_batch_runtime.py` 与 WP19-E docs。不要编辑 facade DTO/bindings 或 support flags。 |

## 第二轮返回状态

| Stream | Agent | Return status | Integration consequence |
|--------|-------|---------------|-------------------------|
| `WP19-B2` | Laplace | `pass` | `DeviceResidentOutputDescriptor` 已作为 standalone export-only DTO 实现，带 binding 与 focused tests。它没有挂到 maintained packets 或 capability projection。 |
| `WP19-E1` | Carver | `pass / evidence-only` | 现有 `WorldBatchRuntime` broadphase candidate-list path 已满足 selected host-owned helper boundary；focused tests 证明 `use_gpu=True` 保持 host filtering semantics 与 fail-closed capabilities。 |

第二轮后的主线程验证：

- `git diff --check` 通过。
- `cmake --build build-workshop --target ef_py -j4` 通过。
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py` 通过：`20 passed`。
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/runtime_facade/test_dto_contracts_batch1.py -k "device_resident or packet"` 通过：`3 passed, 4 deselected`。
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/world_batch/test_world_batch_runtime.py -k "candidate or gpu or broadphase or visual or comm or sensor"` 通过：`4 passed, 17 deselected`。
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/test_gpu_runtime_bindings.py` 通过：`12 passed`。
- `python3 tools/maintenance/wp_doc_closure_audit.py --wp WP19 --summary` 通过。

## 收口轮

| Stream | Agent type | 模型 / 思考预算 | 任务 | 写入范围 |
|--------|------------|-----------------|------|----------|
| `WP19-F` | worker | `gpt-5.4-mini`, xhigh | 集成 A-E/B2/E1 结果，记录 validation rollup 与 residuals，同步 README/review indexes、bilingual closure docs 与 acceptance review。 | 仅 WP19-F docs、WP19 dispatch queue、README/review indexes、acceptance review 与 bilingual companions。不要编辑 runtime implementation。 |

## Required Worker Return Packet

```md
Stream:
Status: pass | fail | blocked | preflight-only
Touched files:
Commands run:
Evidence:
Residuals:
Integration notes:
Closure impact:
```

Worker reminder：

- 你不是独自在代码库中工作；不要 revert unrelated edits 或其他 worker 的 edits。
- 保持写入范围互不重叠。
- 遇到 blocker 时停在命名 blocker 上，不要扩展到 WP20/WP21 或 exact GPU promotion。
