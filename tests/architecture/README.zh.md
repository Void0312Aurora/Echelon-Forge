# 架构测试

`tests/architecture/` 存放源码、文档和治理护栏。它有意与
`tests/runtime/` 下的运行时行为测试、以及 `tests/contracts/` 下的数据驱动契约回归分开。

## 目录布局

`tests/architecture/` 下只使用一层语义目录：

- `build/`：构建系统和 target wiring readiness。
- `causal_runtime/`：stage manifest、replay/counterfactual envelope 和 worldline metadata。
- `command_tasking/`：command/tasking DTO shell 和 maintained tasking 边界。
- `compatibility_quarantine/`：明确容忍的遗留 escape hatch 与 allowlist。
- `damage_model/`：damage-model provenance、source admission、release 和 retained-artifact gate。
- `governance/`：任务、closure 和基础设施文档审计。
- `ground/`：ground domain architecture 和 realism-release 护栏。
- `platform_spawn/`：typed platform spawn、capability materialization 和 setup bridge。
- `policy_execution/`：policy、belief、role、intent 和 information-transformation 边界。
- `runtime_facade/`：facade layering 和 host-visible runtime DTO 契约。
- `runtime_profiles/`：backend、fidelity 和 parity-budget profile 契约。
- `runtime_spine/`：clock-domain、legacy-path 和 runtime-spine inventory gate。
- `structural_boundaries/`：C++/binding structural split 和 quarantine guard。

## 命名

文件名应从架构不变量出发，而不是从引入该检查的工作包编号出发。优先使用
`test_stage_node_manifest_registry.py` 或 `test_tasking_bridge_retirement.py`
这类名称，并放入对应的语义目录。

当确实需要追溯时，可在测试函数名、注释或任务文档中保留 `WP`、`A2` 等历史标签。
`RES`、`TP21`、`BECO`、`blastfrag` 等领域标签若本身属于被守护的契约，而不是项目管理标识，
可以保留在文件名中。
