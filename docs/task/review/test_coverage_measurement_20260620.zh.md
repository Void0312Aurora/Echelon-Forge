# 测试系统覆盖率实测与冗余分析

状态：`2026-06-20` 只读实测记录。本文是首次对测试系统做**机器实测覆盖率**的记录，与 [test_system_evaluation_20260601.zh.md](test_system_evaluation_20260601.zh.md)（基于抽样的意图矩阵）互补：前者回答"测试系统的设计意图与治理边界"，本文回答"测试实际覆盖了多少代码、覆盖是否冗余"。

工具：`coverage 7.14.1`（Python）、`gcovr 8.6`（C++，经 `--coverage -O0 -g` 插桩构建于 `build-coverage/`）。本次为项目首次配置覆盖率测量——此前 pytest、CMake、CI 均未接入任何覆盖率工具。

## 1. 总体结论

测试系统**治理纪律高、但形态低效、且此前无覆盖率度量**。"测试数量多（1872 函数）"不等于"覆盖好"：

- Python 行覆盖 **65%**，C++ 内核真实集成覆盖约 **52%**，属研究型代码库的中上水平。
- 真实缺口在 **C++ 直接单测**与**分支覆盖**（全程 <20%）：正常路径测得多，边界/异常分支测得少。
- 冗余的根源不是"测试太多"，而是**形态低效**：1872 个测试仅 1 个参数化，主体是手写复制的 unittest 类；25% 的测试完全不步进仿真。

## 2. 核心实测数据

| 维度 | 实测值 | 测量方式 |
| --- | --- | --- |
| 测试规模 | 1872 函数 / 210 文件 / 85892 行 | pytest 收集，0 collection error |
| Python 行覆盖率 | **65%**（漏 11869 / 34375 语句） | coverage 全量实测 |
| C++ 真实集成覆盖率 | **51.7%**（runtime+world_batch 子集经 `ef_py`） | 插桩 `ef_py` + Python 测试，189 gcda |
| 架构守卫测试 | 472 函数（约 25%），**零仿真步进** | `tests/architecture/` 全 61 文件无 `import ef_py` |
| 参数化使用 | 1872 测试仅 **1** 个 `@parametrize` | 全仓扫描 |
| 巨型测试文件 | 14 个 >1000 行（最大 1634 行） | 行数统计 |
| JSON 契约 | 59 个 | 文件计数 |
| 当前失败 | 20 个（全部不在 smoke gate 内） | coverage 全量；smoke 子集 338 全过 |

## 3. 关键纠正：C++ 覆盖率不是 19%

C++ 覆盖率极易被误读。只编译并运行 7 个 C++ doctest（`ef_test`）时，`gcovr` 报出 **19–20% 行覆盖**——但这个数字**严重误导**：

- `build-coverage/` 默认只构建了 `ef_test`，**未构建插桩 `ef_py`**。
- 因此 1872 个 Python 测试经 `ef_py` 执行到的全部 C++ 内核代码，**完全不计入** 19% 这个数字。
- 例如 `world_batch_runtime.cpp`（1850 行）在 doctest-only 报告里显示 0%，但它是 Python 批量运行时的核心，被大量 Python 测试间接执行。

把 `ef_py` 也用 `--coverage` 插桩重编后，仅 `tests/runtime/` + `tests/world_batch/` 子集单独就把 C++ 行覆盖打到 **51.7%**（gcda 从 137 升到 189）。**结论：C++ 内核主要靠 Python 集成测试间接覆盖，而非 C++ 单测。任何 C++ 覆盖率结论必须用插桩 `ef_py` 测量，否则会低估约 2.5 倍。**

复现要点：
1. `cmake -B build-coverage -DCMAKE_CXX_FLAGS="--coverage -O0 -g" -DCMAKE_C_FLAGS="--coverage -O0 -g"`
2. 构建 `ef_core ef_py ef_test`（**ef_py 必须包含**）。
3. `PYTHONPATH=build-coverage` 注入插桩模块跑 pytest。
4. `gcovr` 汇总 `build-coverage` 下的 gcda。

## 4. 覆盖度判断（回答"是否真覆盖系统"）

**部分覆盖，分布不均。**

- **Python 层 65% 行覆盖**：核心 RL / scenario / runtime 路径基本被打到。
- **C++ 内核真实约 52%**：靠 Python 集成测试间接覆盖。
- **最弱项是 C++ 直测与分支覆盖**：6 万行内核仅 7 个 doctest 文件。以下核心模块**无任何 C++ 单测**，一旦 Python 路径未覆盖到某分支即裸奔：
  - `src/core/engine/world_batch_runtime.cpp`（1850 行）
  - `src/models/weapons/detail/default_effects_*_detail.inc`（合计约 2400 行）
  - `src/runtime/facade/runtime_facade_counterfactual.cpp`、`runtime_facade_packet.cpp`
- **分支覆盖全程 <20%**：印证"正常路径测得多、边界/异常分支测得少"。

## 5. 冗余判断（回答"覆盖是否冗余"）

**有明确冗余信号，但不是"测试太多"，是"测试形态低效"。**

1. **几乎零参数化**：1872 个测试只有 1 个 `@parametrize`，主体是 124 个 unittest 类。大量结构相同、仅改输入值的用例靠手写复制——这是冗余根源。参数化重构可降数量而不降覆盖。
2. **巨型文件**：14 个超千行测试文件，重复 setup/断言密集。
3. **25% 是非行为测试**：472 个架构守卫测试只读源码/扫路径/跑 cmake 查合规，完全不验证系统行为。它们有价值（防架构腐化，见 [architecture_test_system_governance_closeout_20260610.zh.md](architecture_test_system_governance_closeout_20260610.zh.md)），但让"测试数量"虚高。

**冗余不等于无用**：参数化重构减数量不减覆盖；架构守卫应保留。该治理的是**形态**，不是删测试。

## 6. 20 个当前失败的归因

**不是测试系统缺陷，是其他在途工作的副产品。** 20 个失败中 12 个聚于 `tests/runtime/air_combat/weapon_guidance_realism/`。`git log` 显示 air_combat 域刚被大改（`a9 mach-indexed missile aero tables`、`MLF-8 debris lifecycle`、`aircraft damage consequences calibration`）。典型报错 `beta_delta_deg 0.188 vs 期望 >2.0`——物理模型已更新、断言阈值未跟进。全部不在 smoke gate 内（smoke 338 全过），属 air_combat 工作收尾的校准任务，非测试系统问题。

## 7. 治理建议（按性价比排序）

1. **建立覆盖率基线（最高价值，当前完全缺失）**：把 `coverage`（Python）+ `gcovr`（C++ via 插桩 `ef_py`）接进 CI 并设阈值门禁。这是回答"覆盖够不够"的唯一可持续办法；一次性测量会随代码漂移失效。
2. **参数化重构**：把高重复 unittest 类改 `pytest.mark.parametrize`，优先 14 个巨型文件。
3. **补 C++ 直测分支**：给 0 直测的核心模块（`world_batch_runtime`、weapon effects detail）加 doctest，专攻边界/异常分支。
4. **校准漂移失败**：把 12 个 `weapon_guidance_realism` 阈值与新物理模型对齐（归 air_combat 工作线）。

## 8. 本次未完成 / 留待后续

- 全量 Python 测试（非子集）经插桩 `ef_py` 的完整 C++ 覆盖率：叠加运行因 `PYTHONPATH` 未生效而退化（gcda 回落到 137、binding 显示 0%），未重跑。可信数字以第 3 节的 51.7% 子集实测为准。
- 逐模块 Python 漏行清单。
- 上述建议均为只读评估结论，未改动任何测试或 CI 配置。
