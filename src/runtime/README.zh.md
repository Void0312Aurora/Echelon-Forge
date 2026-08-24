# `src/runtime` 边界

`runtime/` 保存维护中的应用层 C++ runtime contract。它把 `core/` 中较低层的 owner 和 API 组织成前端、训练环境和绑定层可长期依赖的接口。

当前 runtime 文档应使用 multi-domain/common-first 口径：air execution 是成熟路径，naval tasking/engagement evidence 通过维护中的 contract 与 facade packet 暴露，ground 仅 setup/evidence-aware。在下层 owner 与 schema 存在前，不应在这里描述 full ground runtime。

## 允许

- 稳定 request/result 类型。
- step path 外的 host-neutral composition ingestion、validation、scoped lifecycle ownership
  与 deterministic rollback/teardown。
- facade、capability query、批量 runtime 操作入口。
- 对 `core/engine` 与 `core/mission` 的组合调用。
- common command/tasking contract、air/naval maintained slice、ground-bootstrap setup evidence 和 engagement evidence export。

## 禁止

- ECS system 实现。
- Python/nanobind 绑定。
- 训练脚本、场景加载脚本或 CLI。
- GPU exact-step 语义替换。
- ground movement、sensing、fires、damage 或 full ground-domain runtime 行为。

## 子目录约定

- `contracts/`：facade、engine、binding 可共享的稳定 DTO，不能包含 runtime owner 或 engine headers。
- `composition/`：隔离的原生 composition ingestion、provider catalog、transaction、scope
  generation、typed handle 与 teardown owner。
- `facade/`：当前维护中的 typed runtime facade。

## 当前阅读入口

- [contracts/README.md](contracts/README.md)
- [composition/README.md](composition/README.zh.md)
- [facade/README.md](facade/README.md)

## 当前文件落点

- `contracts/`
  - `world_batch_contracts.h`, `engagement_contracts.h`, `platform_capability_contracts.h`
- `composition/`
  - `composition_json.h`, `provider_catalog.h`, `composition_runtime.h`
- `facade/`
  - `runtime_facade.h`, `runtime_facade.cpp`, `runtime_facade_types.h`

## 迁移备注

新增主线能力应先形成 facade request/result，再由 Python 或其他接口层绑定。不要让外部调用者继续扩大对 `WorldBatchRuntime` 或 `SimulationKernel` 的直接依赖。
