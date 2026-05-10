# `src/runtime/facade` 边界

`runtime/facade` 是维护中的 C++ 应用层 API。它面向训练环境、Python 绑定和后续前端主线，提供 typed request/result，而不是暴露底层 world owner 的全部细节。

## 允许

- `RuntimeFacade`。
- facade request/result/capability 类型。
- 批量 reset、setup、step、command、tasking、episode 和 observation 操作。
- 对 `WorldBatchRuntime` 与 `ExecutionEpisodeController` 的受控包装。

## 禁止

- 实现 ECS system 或物理模型。
- 内联 Python 绑定逻辑。
- 把 `WorldBatchRuntime` 的所有低层 API 无选择复制为 facade API。
- 新增未设计 request/result 的主线入口。

## 逃逸口规则

`RuntimeFacade::runtime()` 是 compatibility / diagnostics 逃逸口。它可以服务旧测试、迁移期调试和底层能力验证，但新主线代码不应依赖它。

新增长期 API 时，应优先补充 facade request/result，并在 Python 层绑定 facade，而不是直接暴露新的底层 runtime 方法。
