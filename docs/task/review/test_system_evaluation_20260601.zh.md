# 测试系统评估与意图矩阵

状态：`2026-06-01` 只读评估记录，基于本地抽样、既有命令结果和四路 subagent 分析。

落地注记：contract type、batch failure policy 与 `sim_kernel` gate/diagnostic 边界已开始在 `tests/README*` 和相关 contract README 中同步；首批测试治理矩阵与 focused suite 草案已落在 `tests/suites/`。

范围：`tests/`、`tests/contracts/`、`.github/workflows/`、`tools/runners/`、`python/testing/`、`docs/standards/`、`docs/task/`、`examples/config/training/`。

## 1. 总体结论

该项目的测试系统不是随机堆积，而是一个正在收敛中的多层测试体系。它已经具备清晰的设计意图：

- CI 只跑 `minimum smoke`，这是有意的仓库健康检查边界，不是完整测试矩阵。
- 业务回归主要落在 `tests/runtime/`、`tests/world_batch/`、`tests/training/`、`tests/eval/`、`tests/leader/` 和 JSON contracts。
- JSON contracts 已经形成独立执行体系，但当前更依赖路径约定和 README 语义，缺少机器可读的 `status / ci_tier / failure_policy / realism_gate` 元数据。
- `realism gate` 是项目明确采用的证据规则：只能声明已实现、运行时契约可见、并被证据覆盖的真实性等级。
- 当前主要短板不是“没有测试”，而是“测试资产、意图边界、CI 暴露、失败策略没有集中治理”。

因此，本评估给出的判断是：

| 维度 | 结论 |
| --- | --- |
| 完整性 | 对当前已声明的核心运行时、facade、world batch、naval N4、air-combat guard 有较强覆盖；对完整产品级、高保真、训练策略验收并不完整，且许多缺口是有意边界。 |
| 层次性 | 已具备 `CI smoke -> focused pytest -> JSON contract -> diagnostics/eval -> active/frozen training -> archive` 的层次，但缺少单一治理矩阵。 |
| 业务覆盖 | `runtime/facade`、`engagement`、`world_batch`、`naval N4` 和 `air_combat guard` 最成熟；`ground` 当前是 G0/G1 任务/静态语义边界；训练策略验收仍偏 entry/runtime gate。 |
| 可维护性 | 测试入口和 runner 可运行，但 build 解析、contract batch glob、契约语义状态之间有不一致。 |
| 主要风险 | 外部读者容易把 intentional boundary 误读为 test gap，或者把 diagnostics/supplemental contracts 当成 hard gating acceptance。 |

## 2. 评估方法

本次分析拆成四条只读支线：

| 支线 | 关注点 | 核心结论 |
| --- | --- | --- |
| CI / runner | GitHub workflow、suite runner、contract runner、build path | CI 明确只跑 smoke；runner 存在路径/语义不一致。 |
| contracts | JSON contract 类型、batch runner、gating/frozen/supplemental | 契约资产多且可运行，但分类主要靠路径和文档，缺 metadata。 |
| 业务域覆盖 | air_combat、naval、ground、runtime/facade、training、world_batch | 多数域有测试资产；是否进入 CI 和是否声明 realism level 需要矩阵化。 |
| 设计意图 | README、standards、task docs、active/frozen 配置 | realism gate、active/frozen、minimum smoke 都是明确设计，不应简单判为缺失。 |

辅助命令和已知结果：

- `source tools/maintenance/cmo_env.sh && cmo_env_validate && cmo_env_summary`：环境校验通过。
- `cmo_python tools/runners/run_pytest_suite.py --suite tests/smoke/ci_smoke_suite.json`：`182 passed`。
- `cmo_python -m pytest --collect-only -q tests`：收集约 `1333` 个测试项。
- `ctest --test-dir build-workshop -N`：`Total Tests: 0`，说明当前 C++ 侧没有独立 CTest 注册，C++ 行为主要通过 Python binding/runtime/facade 测试覆盖。
- `cmo_python tests/runners/test_contract_batches.py --default-group sim_kernel`：当前失败在 `tests/contracts/unit/kernel/pitch_hold_throttle_scan.json`。

关键证据索引：

| 主题 | 证据 |
| --- | --- |
| 项目状态不是 polished product | `README.md:27-37` |
| 当前 minimum smoke 命令 | `README.md:91-99` |
| GitHub CI smoke 入口 | `.github/workflows/ci-smoke.yml:48-51` |
| smoke manifest 内容 | `tests/smoke/ci_smoke_suite.json:1-13` |
| tests 正在向 runner + JSON contracts 收敛 | `tests/README.md:3-9` |
| tests 目录结构和 diagnostics 边界 | `tests/README.md:11-39` |
| contract runner 使用方式 | `tests/README.md:73-116` |
| contract folder 语义 | `tests/README.md:140-195` |
| contract batch glob 分组 | `tests/runners/test_contract_batches.py:19-49` |
| contract batch hard-fail 执行 | `tests/runners/test_contract_batches.py:132-143` |
| contract dispatch 只看 `type` | `python/testing/contracts/__init__.py:14-30` |
| shell helper build artifact 选择 | `tools/maintenance/cmo_env.sh:8-31` |
| Python runtime build dir 选择 | `python/testing/runtime.py:22-49` |
| gradient realism 总规则 | `docs/standards/foundation/gradient_realism_principles.md:14-18` |
| 低 gate 不隐含高 gate | `docs/standards/foundation/gradient_realism_principles.md:52` |
| evidence 只需覆盖当前 claim | `docs/standards/foundation/gradient_realism_principles.md:160-173` |
| runtime workflow stable contracts | `docs/standards/bridge/runtime_workflow_and_contract_baseline.md:153-168` |
| task docs 深层文件是 supporting records | `docs/task/README.md:18-21` |
| training active/frozen taxonomy | `examples/config/training/README.md:5-17` |
| naval active entries 是 runtime gate | `examples/config/training/active/naval/README.md:14-21` |
| ground 当前 deferred 范围 | `docs/task/ground/ground_current_progress_20260524.md:31-36` |
| naval N4/N5/N6 边界 | `docs/task/naval/naval_current_progress_20260524.md:67-83` |
| frozen training gating vs supplemental | `tests/contracts/unit/training/frozen/README.md:5-15` |
| `pitch_hold_throttle_scan` 阈值 | `tests/contracts/unit/kernel/pitch_hold_throttle_scan.json:59-65` |
| ordered check hard-fail 逻辑 | `python/testing/contracts/unit/kernel.py:770-792` |

## 3. 当前分层模型

### 3.1 CI minimum smoke

权威入口：

- `.github/workflows/ci-smoke.yml`：workflow 名为 `ci-smoke`，构建 `ef_core` / `ef_py` 后运行 suite runner。
- `tests/smoke/ci_smoke_suite.json`：当前唯一 checked-in smoke manifest。
- `tools/runners/run_pytest_suite.py`：读取 manifest `paths`，检查路径存在，再执行 `python -m pytest -q`。

`ci_smoke_suite.json` 当前列出的入口会展开为 18 个 pytest 文件：

| manifest 项 | 作用 |
| --- | --- |
| `tests/architecture/test_runtime_facade_layering.py` | facade layering guard |
| `tests/architecture/test_wp5_design_boundary_gates.py` | design boundary gate |
| `tests/architecture/test_cmake_target_readiness.py` | CMake target readiness |
| `tests/runtime/core/test_env_config.py` | runtime env config |
| `tests/runtime/engagement` | engagement 目录整组 |
| `tests/runtime/facade/test_facade_step_evidence_gates.py` | facade evidence gates |
| `tests/runtime/facade/test_runtime_facade.py` | runtime facade |
| `tests/runtime/test_agent_shim.py` | agent shim |
| `tests/world_batch/test_world_batch_runtime.py` | world batch runtime |

判断：这是有意的最小健康检查层。它不代表完整业务覆盖，也不代表所有 maintained contracts 都是 PR gate。

### 3.2 Focused regression

实际资产分布在：

- `tests/runtime/`：按 capability domain 分组的运行时契约测试。
- `tests/world_batch/`：batch runtime、single-world、vec-env。
- `tests/training/`：训练入口、bootstrap、naval active entries。
- `tests/eval/`：维护的 eval CLI 级回归。
- `tests/leader/`：leader/tasking/profile 语义。
- `tests/scenario/`：scenario compiler/generation runtime。
- `tests/architecture/`：架构 gate、artifact gate、A2 retained evidence gate 等。

判断：focused regression 存在，但尚未以 checked-in suite manifest 形式公开为 `focused` 或 `full local` 层。

### 3.3 JSON contracts

当前 JSON contract 总量：

| 范围 | 数量 |
| --- | ---: |
| `tests/contracts/**/*.json` | 103 |
| 活跃树，排除 `Archive` | 86 |
| `Archive` | 17 |

活跃 contract 类型统计：

| type | 数量 |
| --- | ---: |
| `unit_regression` | 51 |
| `env_regression` | 25 |
| `route_generator` | 7 |
| `scripted_bridge` | 2 |
| `loader_command_chain` | 1 |

执行机制：

- 顶层 dispatch 在 `python/testing/contracts/__init__.py`，按 `type` 选择 handler。
- `unit_regression` 再按 `check_kind` 进入 kernel、comm、leader、wrapper、training 等子 handler。
- `tests/runners/test_contract_batches.py` 按路径 glob 分组：`chain`、`env`、`unit`、`bridges`、`route_generator`、`same_process`、`sim_kernel`。
- `tools/runners/run_sim_kernel_contracts.py` 只是 `sim_kernel` 默认组的薄包装。

判断：contract 层已经可用，但 execution tier 和 semantic tier 还没有统一。

### 3.4 Diagnostics / eval / active experiment

`tests/README.md` 明确说明 `tests/diagnostics/` 不应托管稳定回归；一旦 deterministic，应迁回 `runtime/`、`world_batch/`、`scenario/`、`leader/` 或 `contracts/`。

`examples/config/training/active/` 和 `examples/config/training/frozen/` 区分 active experiment 与 frozen baseline。Naval active N4 entries 明确是 entry/runtime gate，不是 trained-policy acceptance。

判断：这些层是有意分开的。不能因为 active/eval/diagnostics 资产没有进 smoke CI，就直接判定缺失。

## 4. 业务覆盖矩阵

| 业务域 | 当前测试成熟度 | 已覆盖声明 | 显式非声明 / 有意边界 | CI 暴露 |
| --- | --- | --- | --- | --- |
| `runtime/facade` | 高 | facade layering、step evidence、fidelity admission、engagement export、unsupported provider fail-closed | exact GPU backend、resident state、shadow compare 仍 fail-closed | smoke |
| `engagement` | 高 | engagement packet/export、diagnostics trace、launch/damage adapter shape、trace replay gates | 完整武器毁伤真实性不由 engagement smoke 单独声明 | smoke，目录整组 |
| `world_batch` | 中高 | batch runtime、worker thread、command-chain maintained projection | vec env / single-world 资产未完全进入 CI smoke | 部分 smoke |
| `air_combat` | 中高 | flight dynamics guard、sensor P0、weapon guidance guard、A2 evidence scaffold | Pk、deterministic fuze、release-grade component probability 不由当前资产声明 | 未进 smoke |
| `naval` | 高于当前 N4 范围 | N1-N4 pre-fire bridge、station/order、contact/report、reward surface、active entry/eval gate | trained policy、weapon release、damage outcome、full naval combat 未声明 | 未进 smoke |
| `ground` | 低到中，符合当前边界 | G0/G1 tasking/status/static occupy/support、native schema identity | movement、terrain、sensing、fires、damage、suppression、G2+ 未声明 | 未进 smoke |
| `training/config` | 中 | train bootstrap、active naval entries、frozen leader contract mapping | active smoke/probe 不等于 learned-policy acceptance | 未进 smoke |
| `route_generator` | 中高 | route geometry、reachability、yaw/world-heading、多段 eval distribution | 不覆盖完整导航或策略成功 | 未进 smoke |
| `contracts/frozen training` | 中 | leader frozen baseline 与 supplemental matrix 有文档语义 | supplemental README 说未 promoted to frozen gating，但 runner glob 会 hard-fail 全部 unit contracts | 未进 CI |

## 5. Intentional boundary 与真实缺口

### 5.1 不应算作缺陷的边界

以下内容是项目设计边界，不应简单作为测试缺失：

- `README.md` 明确项目是 active research/engineering codebase，不是 polished product release。
- `docs/standards/foundation/gradient_realism_principles.md` 规定场景只能声明已实现、runtime contract 可见、证据覆盖的 realism level；低 gate 通过不代表高 gate 通过。
- `docs/task/ground/ground_current_progress_20260524.md` 明确 ground 当前是 tasking/planning baseline，不是 ground-combat runtime。
- `docs/task/naval/naval_current_progress_20260524.md` 明确 naval 当前主要在 N1-N4，N5/N6 weapon/damage 仍需 scenario-level gates。
- `examples/config/training/active/naval/README.md` 明确 active naval N4 entries 是 pre-fire entry/runtime gate，不是 weapon release、damage/kill reward 或 learned behavior claim。
- `tests/contracts/unit/training/frozen/README.md` 区分 frozen gating baseline 与 supplemental matrix。

### 5.2 真实治理缺口

| ID | 缺口 | 影响 | 建议 |
| --- | --- | --- | --- |
| G-001 | 没有单一 test-system matrix | 外部读者无法判断什么是 CI gate、manual gate、diagnostic、archive | 新增 machine-readable matrix 或 suite registry |
| G-002 | contract JSON 缺少 metadata | `status`、`owner`、`ci_tier`、`realism_gate`、`failure_policy` 只能靠路径推断 | 加 metadata schema，并让 runner 消费 |
| G-003 | `unit/**/*.json` glob 混合 hard gate / supplemental / diagnostic | supplemental/frozen/diagnostic 被同一 failure policy 处理 | 改成 manifest 或 metadata filtering |
| G-004 | `sim_kernel` 当前语义不清 | realism scan 失败会被操作上 hard fail，但语义更像 diagnostic/supplemental | 拆 `sim_kernel_gate` 与 `sim_kernel_diagnostic` |
| G-005 | runner build path 不完全一致 | 从 shell helper、pytest suite、contract batch 直接运行时可能选择不同 build dir | 统一 `python/testing/runtime.py` 与 `cmo_env.sh` |
| G-006 | `tests/README.md` contract type 清单漏 `env_regression` | 文档与实际 handler 不一致 | 补全文档 |
| G-007 | focused/full/local gate 没有 manifest | “有大量测试但不在 CI”容易被误判 | 新增 `tests/suites/` 或扩展 `tests/smoke/` |
| G-008 | CTest 未注册测试 | C++ 侧测试入口对新读者不可见 | 若需要 CTest gate，应注册；否则 README 说明 C++ 行为由 Python/facade 回归覆盖 |

## 6. 当前 `sim_kernel` 失败分类

失败文件：`tests/contracts/unit/kernel/pitch_hold_throttle_scan.json`

失败检查：

- `check_kind = kernel_flight_parameter_scan`
- `ordered_field_checks` 要求 `ias_mps` 按 throttle 0.2 -> 0.6 -> 1.0 increasing，且 `min_delta = 10.0`
- 实际本地结果：
  - throttle `0.2`: `ias_mps = 163.689`
  - throttle `0.6`: `ias_mps = 168.734`
  - throttle `1.0`: `ias_mps = 194.244`
  - 0.2 -> 0.6 只增加 `5.045`，低于 `10.0`

操作分类：当前 runner 会把它作为 hard failure，因为 `sim_kernel` 分组和默认 `unit` glob 都会 fail-fast。

语义分类：更接近 `supplemental realism diagnostic`，不是 frozen acceptance gate。它确实保护了飞行动力学相对趋势，但阈值、duration、初始状态和控制律应由 realism owner 明确校准后再决定是否成为 PR gate。

建议短期处理：

```json
{
  "metadata": {
    "status": "active",
    "ci_tier": "diagnostic",
    "realism_gate": true,
    "failure_policy": "report",
    "rationale": "Throttle response trend guard pending threshold calibration."
  }
}
```

如果项目决定它必须阻塞 PR，则应显式改为：

```json
{
  "metadata": {
    "status": "active",
    "ci_tier": "pr",
    "realism_gate": true,
    "failure_policy": "hard_fail",
    "owner": "flight_dynamics"
  }
}
```

关键点：不要继续让路径位置隐式决定 failure policy。

## 7. 建议的机器可读矩阵

建议新增一份测试治理矩阵，例如：

- `tests/suites/test_system_matrix.json`
- 或 `tests/suites/contracts_matrix.json` + `tests/suites/pytest_matrix.json`

推荐字段：

| 字段 | 含义 |
| --- | --- |
| `id` | 稳定编号 |
| `domain` | `runtime_facade` / `engagement` / `air_combat` / `naval` / `ground` / `training_config` / `world_batch` / `route_generator` |
| `capability_surface` | 被保护的能力面 |
| `realism_level` | `G0`、`G1`、`N4_pre_fire`、`P0_sensor`、`diagnostic_only` 等 |
| `committed_claim` | 当前测试实际承诺的行为 |
| `explicit_non_claims` | 明确不声明的能力 |
| `test_assets` | pytest 文件、contract JSON、eval CLI、docs gate |
| `runner` | `pytest_suite`、`contract_batch`、`eval_cli`、manual |
| `ci_tier` | `smoke`、`focused`、`nightly`、`manual`、`archive` |
| `failure_policy` | `hard_fail`、`soft_fail`、`report`、`skip_allowed` |
| `dependencies` | `ef_py`、`gymnasium`、CUDA、external artifact、database fixture |
| `determinism` | seeded、fixture-only、diagnostic、known-flaky |
| `owner` | capability owner 或 gate group |
| `promotion_rule` | 从 diagnostic/supplemental 提升到 gating 的条件 |

示例：

```json
{
  "id": "contract.sim_kernel.pitch_hold_throttle_scan",
  "domain": "air_combat",
  "capability_surface": "flight_dynamics.throttle_pitch_hold_response",
  "realism_level": "G1_parameter_scan",
  "committed_claim": "Increasing throttle should produce monotonic airspeed and climb trends under a pitch-hold controller.",
  "explicit_non_claims": [
    "full F-16 performance calibration",
    "combat maneuver validity",
    "trained-policy acceptance"
  ],
  "test_assets": [
    "tests/contracts/unit/kernel/pitch_hold_throttle_scan.json"
  ],
  "runner": "contract_batch:sim_kernel",
  "ci_tier": "diagnostic",
  "failure_policy": "report",
  "dependencies": ["ef_py", "scenario:test_aero"],
  "determinism": "seeded",
  "owner": "flight_dynamics",
  "promotion_rule": "Promote to hard_fail only after threshold and initial-condition calibration are recorded."
}
```

## 8. 推荐实施顺序

### P0：只做文档和索引

目标：先让读者知道现有测试体系的意图。

- 保留 `ci_smoke_suite.json` 为 minimum smoke。
- 在 README / tests README 中说明 smoke 不是完整 acceptance。
- 补充本评估作为 test-system 意图入口。

### P1：加 suite / contract governance matrix

目标：不扩大 CI 成本，先把已有资产分层。

- 新增 `tests/suites/test_system_matrix.json`。
- 新增 `focused_runtime_suite.json` 或等价 manifest。
- contract batch 从路径 glob 过渡到 manifest 或 metadata filtering。

### P2：统一 runner 环境

目标：避免本地 runner 与 CI helper 选择不同 build artifact。

- 统一 `python/testing/runtime.py` 与 `tools/maintenance/cmo_env.sh` 的 build dir 策略。
- `tools/runners/run_scenario_contract.py` 调用 `ensure_repo_imports()`。
- `tests/runners/test_contract_batches.py` 不再把硬编码 `build` 放在 `PYTHONPATH` 最前。

### P3：拆分 contract failure policy

目标：让 hard gate、supplemental、diagnostic 不再混在一个 glob 里。

- 拆 `sim_kernel_gate` / `sim_kernel_diagnostic`。
- training frozen 的 gating baseline 与 supplemental matrix 分别建 manifest。
- `env_regression` 补进 `tests/README.md` 的 Contract Types。

### P4：选择性扩大 CI

目标：在成本可控前提下提高业务覆盖。

候选优先级：

1. route_generator contracts：低依赖、确定性强。
2. ground G0/G1 tasking contracts：低成本，能防止 boundary 回退。
3. naval N4 closure gate 的轻量 entry/config 检查：不跑训练，只验配置/契约对齐。
4. world_batch vec/single 的最小 smoke：在 runtime/facade 之后补齐 batch surface。

不建议第一步就把所有 contracts 或所有 runtime tests 放进 PR CI。这个项目的现实情况更适合先把 tier 和 failure policy 固化，再扩大 CI。

## 9. 最终判断

当前测试系统“有层次、有业务覆盖、有设计意图”，但还没有形成完整的机器可治理测试系统。它最像一个成熟研究工程项目的中期状态：重要路径已经有 guard 和 contracts，边界纪律也很强；缺的是把这些资产转成稳定的 suite、metadata、failure policy 和 CI tier。

下一步不应直接追求“全量 CI”，而应先落地测试治理矩阵。这样既能保留当前 minimum smoke 的速度，也能防止 active experiment、diagnostic realism scan、frozen baseline、supplemental matrix、archive provenance 在执行语义上继续混淆。
