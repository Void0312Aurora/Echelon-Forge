# Runtime Providers

`src/runtime/providers` 是已准入 provider catalog 与 composition-root adapter
的原生集成边界，将具体 engine/model implementation 绑定到
`src/runtime/composition` 的 host-neutral lifecycle kernel。

该层可以依赖 native engine owner、抽象 model interface、components、models 与
runtime contracts，但不得定义第二套 manifest resolver、绕过 native admission，
或把 provider callback 放入仿真 step hot path。Cordis 与 Node adapter 保持为独立
host-side 层，并降低到同一个 native composition 边界。
