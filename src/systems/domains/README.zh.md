# `src/systems/domains` 边界

`systems/domains` 持有具体执行域专属的 per-tick ECS runtime system。它把新增域 runtime owner 收束在统一入口下，避免继续摊到 `systems/` 根目录，同时保留 system 层规则：这里可以注册或运行 ECS system，但不拥有 world lifecycle、facade、binding 或 scenario 编排。

## 布局

- `air/`：air-domain flight control、aero state、aerodynamic force/moment 与 propulsion system。
- `naval/`：naval ship/submarine motion、embarked-air token runtime、naval logistics 与 naval weapon-release bridge system。

当前没有 `ground/` runtime owner。ground-contact primitive 仍保留在 `systems/physics`，直到 land movement、sensing、fires、damage 与 terrain runtime ownership 被接受。

## 依赖方向

域 system 可以消费共享 `components/`、`components/domains` 下的域 component、model interface 与可替换 `models/`。它们不得为了方便依赖兄弟域，也不得依赖 `runtime/facade`、`interfaces/python` 或 training/scenario glue。
