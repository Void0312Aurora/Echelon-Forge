# CMO/EchelonForge 工程规范评估断言核验记录

- **核验日期：** 2026-06-03
- **仓库：** `/home/void0312/Workshop/CMO`
- **核验对象：** `docs/evaluation/engineering_discipline_review_20260603.md`
- **核验目标：** 确认工程纪律、行业规范、工具链和配置管理相关论述是否有当前仓库证据支持，并修正文档中过强或不可复现的断言。

## 0. 工作树与口径

当前工作树存在并行改动和未跟踪文件，尤其 `docs/evaluation/`、`python/rl/policy_algo/`、`python/rl/runtime/world_batch_vec_env.py`、`python/training_callbacks.py` 等位置。本轮只读核验并局部修正文档，不回滚、不覆盖这些改动。

默认口径：

- Git 指标：当前 HEAD 最近 50 次提交。
- Python 类型/异常/`hasattr` 指标：git 已跟踪的 `python/` 目录 `.py` 文件。
- CI/工具链指标：当前 `.github/workflows/ci-smoke.yml`、`CMakeLists.txt`、`pyproject.toml`、`.ruff.toml`、`.pre-commit-config.yaml` 等文件内容。
- 本轮没有创建新的会话线程；核验由当前主线程本地完成。

## 1. 总体核验结论

新增工程规范评估文档的主方向基本成立：

- CI 没有 lint 门控。
- CMake 没有显式 warning flag / sanitizer policy。
- `pyproject.toml` optional dependencies 没有版本下限。
- smoke constraints 文件存在，但 CI 仍直接 `pip install pytest numpy`。
- Ruff / clang-format / clang-tidy / pre-commit 已配置，但规则与 CI 强制程度仍处于初始阶段。
- 文档治理、任务包和 authority 边界记录确实明显强于常见轻量开源项目。

但原文有多处硬数字或绝对表述不成立，已在 `engineering_discipline_review_20260603.md` 中修正：

- 提交消息正文不是零。
- 最近 50 次提交平均文件数不是 42。
- 活跃度不是"3 天内 30 次提交"。
- README 当前为 373 行，不是 374 行。
- `.env` 当前没有 `DEEPSEEK_API_KEY` 条目，且 `.env` 被 `.gitignore` 排除、未被 git 跟踪。
- tracked `python/` 的类型注解、`__all__`、`except Exception`、`hasattr` 数字与原文不一致。
- Release "无优化标志"不能由当前 CMakeLists 推出，因为 CMake build type 通常提供默认 Release 优化；可确认的是没有显式 sanitizer policy。

## 2. Git 提交纪律断言

| 原断言 | 当前核验 | 判断 |
| --- | --- | --- |
| Conventional Commits 48%（24/50） | 最近 50 次提交中 24 个匹配常见 Conventional Commit 前缀 | **成立** |
| 提交消息正文为零 | 最近 50 次提交中 9 个有正文，41 个仅主题行 | **不成立，已修正** |
| GPG 签名为零 | 最近 50 次提交 `%G?` 均为 `N` | **成立** |
| 平均 42 文件，最大 624 文件 | `git diff-tree` 口径平均 36.38，最大 624；常见 `git show --name-only` 口径平均 30.02，最大 347 | **平均数不成立，最大数需注明口径** |
| 3 天内 30 次提交 | `--since='3 days ago'` 为 52；自 `2026-06-01 00:00:00` 为 49 | **不成立，已修正** |

复核命令核心口径：

```bash
git log -50 --pretty=%H
git show -s --format=%s <commit>
git show -s --format=%b <commit>
git show -s --format=%G? <commit>
git diff-tree --no-commit-id --name-only -r <commit>
git show --name-only --format= <commit>
git log --since='3 days ago' --oneline
```

## 3. 构建系统与 CI/CD 断言

| 原断言 | 当前核验 | 判断 |
| --- | --- | --- |
| 编译器警告标志零配置 | `CMakeLists.txt` / workflow 中未发现 `target_compile_options`、`add_compile_options`、`-Wall`、`-Wextra` 等 | **成立** |
| Debug sanitizer 不配置 | 未发现 `-fsanitize=address,undefined` 或等价 sanitizer policy | **成立** |
| Release 构建无优化标志 | CI 使用 `-DCMAKE_BUILD_TYPE=Release`，不能从仓库未显式写 `-O` 推出无优化 | **不成立，已改为未显式定义 sanitizer policy** |
| C++ 依赖版本钉到 tag | flecs v4.0.0、spdlog v1.13.0、nanobind v1.9.2、nlohmann_json v3.11.3、doctest v2.4.11 | **成立** |
| Python 依赖零下限约束 | `pyproject.toml` optional deps 是裸包名；但 `requirements/constraints-smoke.txt` 已约束 pytest/numpy smoke 依赖 | **需限定，已修正** |
| 版本号不一致 | `CMakeLists.txt` 为 0.1.0，`pyproject.toml` 为 0.2.0 | **成立** |
| CMakeLists 281 行 | 当前 281 行 | **成立** |
| CMake 提交 17 次、pyproject 6 次 | 当前 CMakeLists 17 次，pyproject 5 次 | **pyproject 数字不成立，已修正** |
| CI 单平台、Python 3.11、无 cache、无 lint、绕过 constraints | `.github/workflows/ci-smoke.yml` 与原断言一致 | **成立** |
| CI 演化 3 次提交 | workflow 文件历史为 3 次提交 | **成立** |

关键证据：

```bash
rg -n 'target_compile_options|add_compile_options|Wall|Wextra|fsanitize' CMakeLists.txt .github/workflows
rg -n 'FetchContent_Declare|GIT_TAG' CMakeLists.txt
rg -n 'pip install|constraints-smoke|python-version|runs-on|cache|ruff|clang-format|clang-tidy' .github/workflows/ci-smoke.yml
git log --oneline -- CMakeLists.txt | wc -l
git log --oneline -- pyproject.toml | wc -l
git log --oneline -- .github/workflows/ci-smoke.yml | wc -l
```

## 4. 风格工具与文档治理断言

| 原断言 | 当前核验 | 判断 |
| --- | --- | --- |
| `.clang-format`、`.clang-tidy`、`.ruff.toml`、`.pre-commit-config.yaml`、`.editorconfig` 存在 | 文件均存在 | **成立** |
| Ruff 仅选择 `E9`、`F821`、`F822`、`F823` | `.ruff.toml` 与原断言一致 | **成立** |
| pre-commit 仅基础 hooks + ruff | `.pre-commit-config.yaml` 未含 clang-format / clang-tidy hooks | **成立** |
| 工程治理基线 2026-06-02 引入 | `d967e2e chore: add engineering governance baseline` 时间为 `2026-06-02 22:10:54 +0800` | **成立，但原"24 小时前"已改为绝对日期** |
| README 374 行 | `README.md` 当前 373 行 | **不成立，已修正** |
| 任务追踪达到"航空工程文档质量" | `docs/task` / `docs/plan` 确有证据表、禁止结论、authority 边界和验收记录；但"航空工程质量"不是仓库内可证明硬事实 | **方向成立，措辞已降级** |

## 5. 日志、配置与 secret 断言

| 原断言 | 当前核验 | 判断 |
| --- | --- | --- |
| Python 无集中 logging 设置 | `python`、`gym_envs`、`tools`、`train.py` 未发现 `logging.basicConfig`、`logging.config`、`getLogger` | **成立** |
| Python 日志仅 `self.logger.record()` | `self.logger.record` 约 187 处，但 `train.py` 和评估工具大量 `print()` | **需限定，已修正** |
| C++ 使用 spdlog 且有 `CMO_SIM_LOG_LEVEL` | `src/interfaces/python/python_module.cpp` 按环境变量设置 spdlog level，C++ 多处 `spdlog::*` | **成立** |
| 零 `DeprecationWarning` | 未发现 `DeprecationWarning`；存在 3 处普通 `warnings.warn` | **成立但需注意普通 warning 不等于弃用策略** |
| 环境变量最小且仅少数几个 | 当前还存在 `CMO_DEBUG_ZONES`、`CMO_FLIGHT_SHAPING_BACKEND`、`CMO_FBW_PROTECTION_MODE` 等 | **原"仅"不成立，已改为有限但分散** |
| `.env` 含 `DEEPSEEK_API_KEY` | `.env` 文件存在，但未发现该条目；`.env` 被 `.gitignore` 排除且未被 git 跟踪 | **不成立，已修正** |
| `env_config.py` 有配置合并和白名单校验 | `python/env_config.py` 明确实现 CLI args > JSON env > default 合并，并校验 action/runtime/info/backend/mode | **成立** |

复核命令注意：核验 `.env` 时只检查 key 是否存在，不输出 secret 值。

```bash
rg -n 'logging\.basicConfig|logging\.config|getLogger\(|import logging|from logging' python gym_envs tools train.py --glob '*.py'
rg -n 'self\.logger\.record' python gym_envs tools train.py --glob '*.py' | wc -l
rg -n 'DeprecationWarning|warnings\.warn' python gym_envs tools train.py --glob '*.py'
rg -n 'spdlog|CMO_SIM_LOG_LEVEL|std::getenv|getenv' src --glob '*.cpp' --glob '*.h'
test -f .env
rg -q '^DEEPSEEK_API_KEY=' .env
git check-ignore -v .env
git ls-files .env
```

## 6. 类型注解、异常与 Protocol 断言

| 原断言 | 当前核验 | 判断 |
| --- | --- | --- |
| 函数返回类型注解 71%（981/1,383） | tracked `python/` 当前为 84.6%（1,157/1,368） | **不成立，已修正** |
| 文件注解覆盖率 78%（83/107） | tracked `python/` 当前为 81.9%（86/105）；filesystem `python/` 当前为 107，其中 2 个未跟踪 | **不成立/口径混杂，已修正** |
| 变量类型注解 88 个 | AST `AnnAssign` 口径为 901 | **不成立，已修正** |
| `__all__` 45 次 | tracked `python/` AST assignment 为 43，grep 命中 43 行 | **不成立，已修正** |
| `from __future__ import annotations` 多处 | tracked `python/` 为 94 次 | **成立，已补数字** |
| 裸 `except:` 为零 | tracked `python/` 为 0；all tracked `.py` 也为 0 | **成立** |
| 宽泛 `except Exception` 221 次 | tracked `python/` 为 233；all tracked `.py` 为 604 | **不成立，已修正** |
| `hasattr` 231 次、零 Protocol | tracked `python/` 为 244 次 `hasattr(`，Protocol reference 为 0 | **方向成立，数字已修正** |

可复现命令/脚本口径：

```bash
git ls-files | rg '^python/.*\.py$' | wc -l
find python -name '*.py' -type f | wc -l
git ls-files | rg '^python/.*\.py$' | xargs rg -n 'except Exception' | wc -l
git ls-files | rg '^python/.*\.py$' | xargs rg -n '\bhasattr\(' | wc -l
git ls-files | rg '^python/.*\.py$' | xargs rg -n 'from __future__ import annotations' | wc -l
git ls-files | rg '^python/.*\.py$' | xargs rg -n '__all__' | wc -l
```

AST 统计脚本用于函数返回注解、文件注解覆盖、`AnnAssign`、裸 `except`、Protocol reference 等，避免只靠文本匹配。

## 7. 修订结果

已修订 `docs/evaluation/engineering_discipline_review_20260603.md`：

- 添加复核口径说明。
- 修正 Git 提交正文、平均提交大小、活跃度、README 行数、pyproject 提交次数。
- 限定最大提交文件数的 `diff-tree` / `git show` 口径差异。
- 修正 CMake Release 优化相关误判。
- 修正 `.env` / `DEEPSEEK_API_KEY` 断言。
- 修正 tracked `python/` 类型注解、`__all__`、`except Exception`、`hasattr` 指标。
- 将"航空工程文档质量"、"文档世界级"等不可由仓库单独证明的措辞降级为可由结构证据支持的工程判断。

## 8. 结论

`engineering_discipline_review_20260603.md` 经过修订后，可以作为当前工程纪律审阅材料引用。它的核心结论可信：项目不是随意堆功能，文档治理和任务机制有结构性实现；但工程工具链门控仍明显落后于一般多人协作项目的行业预期。

后续若要把它升级为正式治理基线，建议把本记录中的命令固化为维护脚本，避免每次评审手工复算导致口径漂移。

## 9. P0 修复跟进

本记录完成后，`2026-06-03` P0 工程治理切口已改变部分原始缺口状态：

- `.github/workflows/ci-smoke.yml` 已改为通过 `requirements/constraints-smoke.txt` 安装 `pytest numpy ruff`。
- CI 已加入 `ruff check .` 与 changed-file `clang-format --dry-run -Werror` gate。
- `CMakeLists.txt` project version 已从 `0.1.0` 对齐为 `0.2.0`。
- `CMakeLists.txt` 已为项目 targets 添加非 fatal warning policy：GNU/Clang/AppleClang 使用 `-Wall -Wextra -Wpedantic`，MSVC 使用 `/W4`。
- tracked Python 的最小 Ruff baseline 已本地通过；为此修正了少量 F821 undefined-name 问题。

本轮验证结果：

```text
ruff check .: pass
changed-file clang-format local gate: pass, no C/C++ files in this P0 diff
pip install --dry-run -c requirements/constraints-smoke.txt pytest numpy ruff: pass
cmake -S . -B build-workshop -DCMAKE_BUILD_TYPE=Release: pass
cmake --build build-workshop --target ef_core ef_py ef_test -j2: pass, non-fatal warnings visible
ctest --test-dir build-workshop -R ef_test_all --output-on-failure: pass
git diff --check for touched P0 files: pass
```

仍未解决：

- Remote GitHub Actions 尚未实际运行。
- CI 仍是单平台、单 Python 版本、无 cache。
- Ruff 规则仍停留在最小 undefined-name baseline。
- clang-format 只检查 changed C/C++ files，whole-repo C++ formatting baseline 仍有大量既有债。
- C++ warnings 已可见但未清理，也未升级为 warnings-as-errors。
- clang-tidy 与 sanitizer lanes 仍未接入。
