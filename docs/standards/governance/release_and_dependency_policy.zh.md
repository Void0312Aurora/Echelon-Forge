# 发布与依赖政策

语言版本：

- 英文主文：[release_and_dependency_policy.md](release_and_dependency_policy.md)
- 中文辅文：`release_and_dependency_policy.zh.md`

状态：`2026-06-02`，依赖与发布治理基线。

本政策定义 Echelon Forge 最小发布治理面。由于仓库当前还没有完整
lockfile，本政策刻意保持轻量。

## 适用范围

本政策适用于：

- 依赖声明与 smoke constraints；
- release candidate 准备；
- 准备对外分发的源码包、wheel、二进制包、文档、场景、模型与留存产物包；
- 第三方源码、包与资产许可证检查。

本政策不会把 optional dependency groups 变成可复现环境锁，也不会授权在
smoke constraints 中硬性固定完整训练栈。

## 依赖治理

`pyproject.toml` 的 optional dependency groups 是能力声明。它们说明某个工作流能力
可能需要哪些包，例如 test、RL、training、world-model 或 dev convenience。它们不能证明
一个精确解析后的环境。

`requirements/constraints-smoke.txt` 是 CI/smoke 可复现性的入口。它可以约束：

- 当前 CI smoke lane 直接安装的包，目前是 `pytest` 与 `numpy`；
- 当专门测试包构建/安装 smoke 时相关的 Python 构建前端/后端包，目前是 `pip`、
  `scikit-build-core` 与 `nanobind`。

它不应膨胀成隐藏的训练 lockfile。除非单独批准训练锁政策，否则不要为 `torch`、
`stable-baselines3`、`gymnasium`、`tensorboard` 或类似可选训练/实验包添加硬 pin。

在专用 lockfile 出现前，训练和实验可复现性必须随 run artifact 记录解析后的环境。至少记录：

- Python 版本与平台；
- `python -m pip freeze --all` 输出；
- 相关 CUDA、加速器、驱动或编译器信息；
- 场景/config 标识与 run artifact 校验和。

## 版本治理

release candidate 必须审查两个项目版本面：

- CMake：`CMakeLists.txt` 中的 `project(EchelonForge VERSION ...)`；
- Python distribution：`pyproject.toml` 中的 `[project].version`。

对于 release tag，CMake 项目版本和 Python distribution 版本必须一致；如果有意不同，
release notes 中必须给出明确例外说明，解释为什么 native artifact 与 Python artifact
需要不同版本。

截至本政策基线，仓库存在已知版本同步缺口：`CMakeLists.txt` 声明 `0.1.0`，
`pyproject.toml` 声明 `0.2.0`。release checklist 必须在切 tag 前关闭或明确豁免
这个不一致。

## 发布门禁

release candidate 发布前，release owner 必须记录：

- 版本同步结果，或已批准的版本不一致例外；
- 使用维护中的 smoke dependency entry point 完成的 smoke 验证；
- CHANGELOG 或 release notes，覆盖用户可见变更、依赖政策变更、兼容性破坏和已知残留；
- release checklist 结果，写明精确 commit、artifact set、验证命令和未解决风险；
- 第三方包、源码、模型、媒体、场景和留存产物许可证审查；
- 对再分发文件的资产 provenance 审查，包括生成、下载、转换或解包资产。

仓库当前缺少 canonical `CHANGELOG` 和专用 release checklist 文档。这是发布治理缺口，
不是跳过 release notes 的理由。在这些文件出现前，release owner 必须先创建等价的
release-note 与 checklist packet，再切 tag。

## 第三方与资产门禁

发布前，检查以下内容的许可证与再分发状态：

- 仓库许可证与 `THIRD_PARTY_NOTICES.md`；
- CMake `FetchContent` 依赖与任何 vendored source；
- 发布 artifact 或 smoke/install path 使用的 Python 依赖；
- model、media、scenario、data、calibration 与 retained evidence artifacts；
- 生成或转换资产，因为原始来源许可证仍可能适用。

release artifact 不得包含 provenance 未知、再分发条款不兼容、缺少署名或生成/转换所有权不清的资产。
如果某个资产仅对本地研究必要但 release 不安全，应将其排除在 release bundle 之外，并记录排除原因。

## 维护规则

- smoke constraints 保持小而明确，只服务 smoke lane。
- 新 lockfile 视为单独治理 artifact，必须有明确 ownership。
- 当 CI 依赖安装、发布打包或第三方资产处理方式变化时，更新本政策。
- 除非解析后的环境和 artifact provenance 已记录，否则不要把一次本地训练成功视为发布依赖证据。
