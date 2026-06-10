# `src/components/domains` 边界

`components/domains` 持有具体执行域专属的 component slice。它把后续新增域收束在 `components/` 根目录之下的统一入口里，同时继续遵守 component 层规则：这里只保存数据与 DTO，不保存 runtime 或 system 逻辑。

## 布局

- `air/`：空域平台、战斗、command 与 tasking component。
- `naval/`：海域平台、战斗、command 与 tasking component。
- `ground/`：陆域 combat、command 与 tasking owner slice。当前仍限定在已接受的 bootstrap/static-tasking surface。

每个域内部优先按 `platform/`、`combat/`、`command/`、`tasking/` 这类能力子目录组织。新增域应沿用这个形态，而不是继续增加 `components/` 顶层目录。

## 依赖方向

域 component slice 可以依赖 `components/basic`、`components/combat/common`、`components/command/common`、`components/tasking/common` 等共享 component foundation。它们不得依赖兄弟域、`systems/`、`models/`、`core/`、`runtime/` 或 `interfaces/`。
