# `src/runtime` 边界

`runtime/` 保存维护中的应用层 C++ runtime contract。它把 `core/` 中较低层的 owner 和 API 组织成前端、训练环境和绑定层可长期依赖的接口。

## 允许

- 稳定 request/result 类型。
- facade、capability query、批量 runtime 操作入口。
- 对 `core/engine` 与 `core/mission` 的组合调用。

## 禁止

- ECS system 实现。
- Python/nanobind 绑定。
- 训练脚本、场景加载脚本或 CLI。
- GPU exact-step 语义替换。

## 子目录约定

- `contracts/`：facade、engine、binding 可共享的稳定 DTO，不能包含 runtime owner 或 engine headers。
- `facade/`：当前维护中的 typed runtime facade。

## 迁移备注

新增主线能力应先形成 facade request/result，再由 Python 或其他接口层绑定。不要让外部调用者继续扩大对 `WorldBatchRuntime` 或 `SimulationKernel` 的直接依赖。
