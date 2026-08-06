# Engineering Governance P0

状态：`2026-06-03` local-pass remediation slice，用于落实工程规范评估中的 P0 修复；remote CI 执行仍待实际运行。

语言：

- 英文规范页：`README.md`
- 中文辅文：`README.zh.md`

输入：

- [Review task area](../README.zh.md)
- [Engineering discipline review](../../../evaluation/engineering_discipline_review_20260603.md)
- [Engineering discipline claim verification](../../../evaluation/engineering_discipline_claim_verification_20260603.zh.md)
- [Agent subproject standard](../../../engineering/automation/rules/subproject_creation_standard.zh.md)
- [Subagent usage policy](../../../standards/governance/subagent_usage_policy.zh.md)

## Purpose

本子项目实现工程规范评估中优先级最高的一段修复：CI lint gate、可复现 smoke
依赖安装、C++ warning policy，以及版本号对齐。

范围刻意保持很窄。本子项目不扩大 Ruff 规则集、不把 C++ warning 变成 fatal，
也不声明 release readiness。

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| CI lint gate | local-pass | `.github/workflows/ci-smoke.yml`；`ruff check .` 通过 | 只接入当前 Ruff 规则和 changed-file clang-format。 |
| Dependency constraints | local-pass | `requirements/constraints-smoke.txt`；pip dry-run 可解析 | smoke/lint constraints 不是完整训练 lockfile。 |
| C++ warning policy | local-pass | `CMakeLists.txt`；CMake build 通过且 warning 可见 | warning 为非 fatal，且不直接作用于第三方 FetchContent target。 |
| Version alignment | local-pass | `CMakeLists.txt`, `pyproject.toml` 均为 `0.2.0` | 本切口只对齐数值，不引入完整版本生成系统。 |

## Scope

In scope:

- 通过 `requirements/constraints-smoke.txt` 安装 smoke 和 lint Python 依赖。
- 在 CI 中添加 `ruff check` 和 changed-file `clang-format --dry-run -Werror`。
- 为维护中的 C/C++ target 添加非 fatal warning flags。
- 让 CMake project version 与 `pyproject.toml` 对齐。
- 记录验证证据和残余风险。

Out of scope:

- 把 Ruff 规则从当前 `E9` / `F821-F823` 扩大到更完整规则集。
- 把 C++ warning 变成 fatal。
- 把 clang-tidy 加入 CI gate。
- 引入完整 release lockfile、版本生成系统或多平台 CI matrix。
- 仅为了未来更严格 lint policy 而重构源码。

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | 冻结窄工具链切口。 | 工程评估已核验。 | 任务簇和非目标已记录。 | pass |
| `P1 Implementation` | 应用 CI、constraints、CMake 和版本改动。 | 边界已记录。 | 文件已编辑并可检查。 | pass |
| `P2 Validation` | 运行聚焦本地检查。 | 实现已存在。 | CI-equivalent checks 本地通过；remote CI 待运行。 | pass |
| `P3 Closure` | 同步状态和残余。 | 验证完成。 | README/task cluster status 与证据一致。 | pass |

## Task Clusters

- Task cluster plan: `engineering_governance_p0_task_clusters_20260603.md`

## Outputs And Evidence

- `.github/workflows/ci-smoke.yml`
- `CMakeLists.txt`
- `requirements/constraints-smoke.txt`
- `requirements/README.md`
- 本任务子项目和父级 review 索引入口。

验证证据：

- `./.venv/bin/python -m ruff check .` 通过。
- changed-file clang-format gate 在本 P0 diff 中没有 C/C++ 文件需要检查。
- `pip install --dry-run -c requirements/constraints-smoke.txt pytest numpy ruff` 可解析。
- `cmake -S . -B build-workshop -DCMAKE_BUILD_TYPE=Release` 通过。
- `cmake --build build-workshop --target ef_core ef_py ef_test -j2` 通过。
- `ctest --test-dir build-workshop -R ef_test_all --output-on-failure` 通过。
- touched P0 files 的 `git diff --check` 通过。

## Acceptance Gate

本子项目只有在以下条件满足时才能标为 accepted：

- CI 通过 constraints 文件安装 smoke/lint 依赖。
- CI 有显式 Ruff 和 clang-format gate。
- 维护中的 C/C++ targets 得到 warning flags，且第三方 dependency target 不受影响。
- `CMakeLists.txt` 与 `pyproject.toml` 版本号一致。
- 聚焦本地验证命令和任何 blocker 已记录。

## Residuals And Next Steps

- 当前 baseline 稳定后，另开切口扩大 Ruff 规则。
- 后续切口添加 clang-tidy 和 sanitizer lanes。
- 简单版本对齐接受后，再考虑版本单源机制。
- 清理 warning policy 现在暴露出的非 fatal C++ warnings。
- 决定是做 whole-repo Python/C++ formatting 迁移，还是长期维持 changed-file gates。

## Archive

只有在存在替代 current-status 表面后，历史或被取代的 remediation 记录才移动到
`archive/README.md`。
