# CMO/EchelonForge 工程规范评估 — 2026-06-03

## 评估范围

从工程纪律和行业共识角度评估项目实现质量。覆盖：Git 提交纪律、构建系统、CI/CD、代码风格工具、文档质量、日志策略、配置管理、类型注解、依赖管理。

## 总体判断

**该项目在多个工程维度上表现出超出预期的纪律性，尤其是在文档治理、任务追踪和 authority 边界记录方面有明确结构性证据。P0 修复已接入第一道工具链门控，但构建系统质量保障（warning 债、CI lint 覆盖范围、依赖版本约束）仍需继续完善。** 整体呈现"外部文档治理强、代码工具链门控刚开始收口"的态势——这在单开发者研究项目中常见，但若计划扩大贡献者范围需继续补齐。

**复核口径**：除特别说明外，Git 指标按当前 HEAD 最近 50 次提交复算；Python 代码指标按 git 已跟踪的 `python/` 目录 `.py` 文件统计。当前工作树有并行改动和未跟踪 Python 文件，本评估不把未跟踪文件混入主指标。

**P0 修复更新**：`2026-06-03` 本地 P0 切口已将 CI smoke 安装改为使用 `requirements/constraints-smoke.txt`，加入 `ruff check` 与 changed-file `clang-format --dry-run -Werror` gate，将 CMake project version 对齐到 `0.2.0`，并为维护中的 C/C++ targets 添加非 fatal `-Wall -Wextra -Wpedantic` / `/W4` warning policy。本地 `ruff check`、CMake build 与 CTest smoke 已通过；remote CI 尚待实际运行。

---

## 逐维度评估

### 1. Git 提交纪律：中等（C+）

| 指标 | 结果 | 行业共识 |
|------|------|----------|
| Conventional Commits 合规率 | 48%（24/50） | 行业期望 ≥80% |
| 提交消息正文 | 9/50 有正文，41/50 仅主题行 | 复杂变更应有正文解释动机 |
| GPG 签名 | 0/50 | 安全敏感项目建议签名 |
| 分支策略 | 主干开发，单分支 `main` | 适合单开发者，但不适合多人协作 |
| 提交大小 | 平均 36.38 文件；最大 624 文件（`git diff-tree` 口径；`git show --name-only` 展示为 347） | 大提交含批量归档操作，非粒度变更 |
| 活跃度 | 最近 72 小时约 52 次提交；自 2026-06-01 00:00 起 49 次 | 持续活跃 |

**积极信号**：`docs`、`feat`、`fix`、`test`、`chore` 类型均有使用，非规范提交虽无前缀但描述清晰有意义。

**风险**：
- 无自动化 changelog 生成能力
- `git blame` 追溯困难（多数提交缺少正文解释复杂变更）
- 供应链安全缺口（无签名验证）

### 2. 构建系统：中等偏上（B-）

| 指标 | 结果 | 行业共识 |
|------|------|----------|
| **编译器警告标志** | P0 已为项目 targets 添加非 fatal `-Wall -Wextra -Wpedantic` / `/W4`；build 暴露多处 warning | ✅ 第一门已接入，warning cleanup 仍待做 |
| C++ 依赖版本 | 全部钉到精确 tag（flecs v4.0.0, spdlog v1.13.0 等） | ✅ 优秀 |
| CUDA 集成 | 通过 feature flag 门控，生成器表达式正确 | ✅ 优秀 |
| Python 依赖版本 | `pyproject.toml` optional dependencies 无下限约束；CI smoke/lint 已使用 `requirements/constraints-smoke.txt` | ⚠️ 部分合规 |
| CMake 目标组织 | 源码按子系统分组，静态库层次清晰 | ✅ 良好 |
| 构建系统演化 | 17 次 CMakeLists 提交，5 次 pyproject 提交 | ✅ 迭代演化 |
| 版本号一致性 | CMake 0.2.0 vs pyproject 0.2.0——已对齐 | ✅ 但仍非单源生成 |
| CMakeLists.txt 模块化 | 单体 319 行 | ⚠️ 可接受但可继续拆分 |

**积极信号**：源码分组已按子系统组织（core/engine、core/geometry、core/mission 等），GPU 实验通过 `EF_ENABLE_CUDA_EXPERIMENTS` 门控，`.editorconfig` 完整。

**严重缺口**：
- warning policy 已接入但仍是非 fatal，且已有 unused / signedness / third-party header warning 暴露出来
- 仓库未显式定义 sanitizer 策略（`-fsanitize=address,undefined`），CI 只跑 Release smoke；Release 优化通常由 CMake/build type 提供，不能据此称为"无优化"

### 3. CI/CD：待改进（D）

| 指标 | 结果 | 行业共识 |
|------|------|----------|
| CI 平台 | GitHub Actions | ✅ |
| **Lint 门控** | P0 已加入 `ruff check .` 与 changed-file `clang-format --dry-run -Werror`；未加入 clang-tidy | ⚠️ 第一门已接入 |
| 构建矩阵 | 单平台（ubuntu），单 Python 版本（3.11） | ❌ 最小化 |
| 缓存 | 无 ccache/ pip 缓存 | ❌ 构建时间浪费 |
| 依赖安装 | `pip install -c requirements/constraints-smoke.txt pytest numpy ruff` | ✅ smoke/lint lane 可复现 |
| 合约测试执行 | ✅ 正确执行 pytest + 合约运行器 | ✅ |
| CI 演化 | 3 次提交 | 初期阶段 |

**关键问题**：P0 已阻止 undefined-name Python 问题和新改动 C/C++ 格式继续漂移，但 `.clang-tidy`、完整 Ruff 规则、全仓格式 baseline、sanitizer 和多平台矩阵仍未进入 CI。

### 4. 代码风格工具：初始阶段（C）

| 指标 | 结果 | 行业共识 |
|------|------|----------|
| C++ 格式化 | `.clang-format` 和 `.clang-tidy` 已配置 | ✅ |
| Python linting | `.ruff.toml` 已配置 | ✅ |
| Pre-commit hooks | 已配置但仅含基础检查 + ruff；CI 另有 Ruff + changed-file clang-format | ⚠️ |
| **Ruff 规则选择** | **仅 `E9` 和 `F821-F823`**——几乎不捕获任何问题 | **严重不足** |
| **引入时间** | 2026-06-02 工程治理基线提交集中引入 | **初始部署，未经调优** |
| `.editorconfig` | 完整，含格式特定覆盖 | ✅ |

**积极信号**：团队已意识到需要代码风格工具并在昨日引入——这是工程成熟的正确方向。

**不足**：Ruff 规则集过于最小（应至少含 `E, F, I, B, SIM`），pre-commit 缺少 `clang-format`/`clang-tidy` hooks；CI 的 clang-format 当前只检查 changed C/C++ files。

### 5. 文档质量：卓越（A+）

| 指标 | 结果 | 行业共识 |
|------|------|----------|
| README | 373 行实质性内容，含域成熟度矩阵 | ✅ 远超平均 |
| 双语（EN/ZH） | 完整 EN/ZH 对照，结构一致，并有 Tier A/B/C 维护政策 | ✅ 罕见的高质量 |
| **计划和标准文档** | **权威关系表、执行规则、归档边界**——治理基础设施 | **接近成熟商业项目的治理面** |
| **任务追踪** | **A1-A6 工作包，含证据表、禁止结论、"为什么不够"分析** | **高于常见开源任务文档** |
| 治理文件 | CODE_OF_CONDUCT、SECURITY、CONTRIBUTING、发布政策 | ✅ 完整 |
| **源码 docstring** | **核心入口稀疏**——`simulation_kernel.h` 无 Doxygen 注释，`train.py` 无模块 docstring（但有若干函数 docstring） | **与外部文档形成断层** |
| 文档维护性 | 每日更新（日期文件名 `_20260603.md`），双语迁移计划执行中 | ✅ 活跃维护 |

**关键发现**：该项目的 `docs/` 树有自己的治理结构、迁移计划、标准层次、层级系统和集群注册表。任务追踪文档（如 A5 约束事件-行动模型）包含精确证据指标、开放风险、"禁止结论"部分、验证计划和验收标准——这不是典型轻量 TODO，而是有结构化审查痕迹的工程记录。

**主要短板**：核心源码入口的 docstring / Doxygen 覆盖不足。项目以强外部文档补偿，但这对直接阅读代码的开发者形成障碍。

### 6. 日志策略：薄弱（D+）

| 指标 | 结果 | 行业共识 |
|------|------|----------|
| Python 日志 | **零集中设置**——无 `logging.basicConfig`、`getLogger`、`config` 调用 | ❌ 不合规 |
| Python 日志调用 | 主要通过外部训练框架的 `self.logger.record()` 记录训练指标；CLI/工具仍大量使用 `print()` | ⚠️ 非项目统一日志 |
| C++ 日志 | 使用 `spdlog`，有运行时级别控制（`CMO_SIM_LOG_LEVEL` 环境变量） | ✅ 但无 sink/格式/文件轮转配置 |
| 结构化日志 | 无 | ❌ |
| 弃用警告 | **零**使用 `DeprecationWarning` | ⚠️ 无弃用策略 |
| `print()` 调试 | `python/world_model/dreamer.py` 中初始化输出由 `verbose` 标志门控；训练入口和评估工具仍以 `print()` 为主 | ⚠️ 局部良好，整体仍非统一日志 |

### 7. 配置管理：良好（B+）

| 指标 | 结果 | 行业共识 |
|------|------|----------|
| 配置合并 | `env_config.py`：CLI args > JSON env > 默认值，带合并函数 | ✅ 良好模式 |
| 配置验证 | 每个键有已知有效值白名单，无效值引发 `ValueError` | ✅ |
| **环境变量分散** | 有限但分散——`CMO_BUILD_DIR`、`CMO_SIM_LOG_LEVEL`、`CMO_DEBUG_ZONES`、`CMO_FLIGHT_SHAPING_BACKEND`、线程控制与 `CMO_FBW_PROTECTION_MODE` 等 | ⚠️ 受控但需登记 |
| API 密钥 | 根目录存在 `.env`，已被 `.gitignore` 排除且未被 git 跟踪；本轮未发现 `DEEPSEEK_API_KEY` 条目 | ✅ 未见已跟踪 secret，但仍需保持 ignore/扫描 |
| 配置演化 | `runtime_compatibility_enabled` 门控用于遗留路径 | ✅ 迁移感知 |

### 8. 类型注解和代码约定：中等偏上（B）

| 指标 | 结果 | 行业共识 |
|------|------|----------|
| 函数返回类型注解 | **84.6%**（tracked `python/`：1,368 个函数中 1,157 个） | ✅ 良好 |
| 文件注解覆盖率 | **81.9%**（tracked `python/`：105 个文件中 86 个） | ✅ 良好 |
| 变量/字段类型注解 | 901 个 AST `AnnAssign`（tracked `python/` 口径） | ✅ 不稀疏，但需继续看语义质量 |
| `__all__` 使用 | 43 次 assignment（43 行 grep 命中） | ✅ 显式公共 API |
| `from __future__ import annotations` | 94 次（tracked `python/`） | ✅ 现代实践 |
| 裸 `except:` | **零** | ✅ |
| 宽泛 `except Exception` | **233 次**（tracked `python/`） | ❌ 见架构评审中的详细分析 |

---

## 工程规范综合评分

| 维度 | 评级 | 关键缺口 |
|------|------|----------|
| 文档治理 | **A+** | 源码 docstring 稀疏 |
| 配置管理 | **B+** | 环境变量登记与 secret 扫描仍可加强 |
| 类型注解 | **B** | 注解数量较好，但仍缺 Protocol 等接口合同 |
| 构建系统 | **B** | warning cleanup、Python optional dependency lower bounds、版本单源 |
| 代码风格工具 | **C+** | CI 第一门已接入，但规则最小且格式 baseline 未迁移 |
| Git 纪律 | **C+** | 无签名、多数提交无正文、48% 合规 |
| 日志策略 | **D+** | Python 端完全缺失统一日志 |
| CI/CD | **C-** | lint 第一门已接入，但单平台、无缓存、无 clang-tidy/sanitizer |

---

## 行业共识对照

| 行业实践 | 本项目状态 |
|----------|-----------|
| Conventional Commits | 48%——不达标 |
| GPG 签名提交 | 完全不使用 |
| CI lint 门控（pre-merge） | P0 已加入 Ruff + changed-file clang-format；覆盖仍不完整 |
| 编译器 `-Wall -Wextra` | P0 已为项目 targets 配置非 fatal warning flags |
| Debug 构建 sanitizer（ASan/UBSan） | 不配置 |
| 依赖版本下限约束 | C++ 钉版（好）；smoke/lint constraints 已进入 CI；`pyproject.toml` Python optional deps 仍无下限 |
| 结构化日志 | 不存在 |
| 弃用策略（`DeprecationWarning` + 迁移窗口） | 不存在 |
| `typing.Protocol` 接口合同 | tracked `python/` 存在 244 次 `hasattr(`，但零 Protocol reference——不达标 |
| 代码格式化自动执行 | changed-file C/C++ 格式已在 CI 强制；Python/full-repo 格式尚未强制 |
| 双语文档 | 卓越 |
| 治理文档（CoC、安全、贡献、发布政策） | 完整 |
| 架构决策记录（ADR） | 通过 `docs/plan/` 和 `docs/task/` 超额实现 |
| 版本号单源 | 数值已对齐为 0.2.0；仍不是单源生成 |

---

## 改进优先级（工程规范专用）

### 立即（本周内）
1. **清理新暴露的 C++ warnings**：unused variables/functions、signedness、nanobind third-party header `-Wpedantic` 噪声
2. **扩展 `.ruff.toml` 规则**：至少 `["E", "F", "I", "B", "SIM"]`，分阶段处理
3. **决定格式 baseline 策略**：whole-repo migration，或长期 changed-file gates
4. **补 sanitizer lane 设计**：先手动或 nightly，再决定是否进入每次 CI

### 短期（本月内）
5. **Python 依赖加版本下限**：`"numpy>=1.24"`、`"torch>=2.0"` 等
6. **版本号单源化**：在已对齐 `0.2.0` 的基础上，决定是否引入生成/检查机制
7. **CI 构建矩阵**：多 Python 版本 + macOS
8. **添加 ccache/pip 缓存** 到 CI
9. **Debug 构建添加 sanitizer**：`-fsanitize=address,undefined`

### 中期（下季度）
10. **建立 Python 日志策略**：统一 `logging.getLogger(__name__)` 模式
11. **添加 GPG 签名** 到提交流程
12. **定义 `typing.Protocol`** 替换关键 `hasattr` 检查
13. **提升源码 docstring 覆盖率**
14. **拆分单体 CMakeLists.txt** 为子目录 CMakeLists

---

## P0 修复跟进（2026-06-03 执行）

本轮评估完成后，`2026-06-03` P0 工程治理切口已改变部分原始缺口状态：

### 已修复

| 项目 | 修复内容 | 验证 |
|------|----------|------|
| CI smoke 依赖安装 | 改为通过 `requirements/constraints-smoke.txt` 安装 `pytest numpy ruff` | `pip install --dry-run -c requirements/constraints-smoke.txt pytest numpy ruff` ✅ |
| CI lint gate | 加入 `ruff check .` 与 changed-file `clang-format --dry-run -Werror` | `ruff check .` ✅；changed-file `clang-format` local gate ✅ |
| CMake 版本对齐 | project version 从 `0.1.0` 对齐为 `0.2.0`，与 `pyproject.toml` 一致 | 双文件确认 `0.2.0` ✅ |
| CMake warning policy | 项目 targets 添加非 fatal warning flags：GNU/Clang/AppleClang `-Wall -Wextra -Wpedantic`，MSVC `/W4` | CMake build 通过，non-fatal warnings 可见 ✅ |
| Ruff baseline | tracked Python 最小 Ruff baseline 本地通过；修正少量 F821 undefined-name 问题 | `ruff check .` pass ✅ |
| CTest smoke | `ef_test_all` C++ smoke | `100% tests passed, 0 tests failed out of 1` ✅ |

### 仍未解决

| 项目 | 状态 |
|------|------|
| Remote GitHub Actions | 尚未实际运行（仅本地验证） |
| CI 多平台/多 Python 版本/缓存 | 仍是单平台 ubuntu、单 Python 3.11、无 cache |
| Ruff 规则扩展 | 仍停留在最小 `E9, F821-F823` baseline |
| clang-format 全仓 | 只检查 changed C/C++ files，whole-repo formatting baseline 仍有大量既有债 |
| C++ warning cleanup | warnings 已可见但未清理，未升级为 warnings-as-errors |
| clang-tidy / sanitizer lanes | 仍未接入 CI |

### 关键可复现命令口径

以下命令用于核验本评估中的量化指标，建议固化为维护脚本以避免每次手工复算导致口径漂移：

```bash
# Git 提交指标
git log -50 --pretty=%H
git show -s --format=%s <commit>
git show -s --format=%b <commit>
git diff-tree --no-commit-id --name-only -r <commit>

# Python 代码指标（tracked python/ 口径）
git ls-files | rg '^python/.*\.py$' | xargs rg -n 'except Exception' | wc -l
git ls-files | rg '^python/.*\.py$' | xargs rg -n '\bhasattr\(' | wc -l
git ls-files | rg '^python/.*\.py$' | xargs rg -n 'from __future__ import annotations' | wc -l

# C++ 指标
git grep -n -E '\b(CHECK|CHECK_FALSE|REQUIRE|REQUIRE_FALSE|ASSERT|EXPECT)[A-Za-z_]*[[:space:]]*\(' -- '*.cpp' '*.h' | wc -l

# 大文件检测
git ls-files -z '*.py' '*.cpp' '*.h' '*.json' | xargs -0 wc -l | awk '$1 > 3000 {print}'
```

---

*由工程规范评估会话生成，2026-06-03。P0 修复跟进于同日完成。*
*所有数据来自实际 git log、文件阅读和 grep 分析。*
