# 发布与依赖政策

语言：英文规范页见 [release_and_dependency_policy.md](release_and_dependency_policy.md)；
本页为中文配套。

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/engineering/release/standards/release_and_dependency_policy.md`
Owner: `engineering/release`
Last verified: `2026-08-07`

状态：已核验的依赖与发布治理基线。

本政策定义 Echelon Forge 最小发布治理面。由于仓库当前还没有覆盖整个仓库或
训练环境的 lockfile，本政策刻意保持轻量。个别工具或导入资源可以拥有局部 lock
产物，但它们不能证明整个项目环境已经得到完整解析。

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

`requirements/constraints-smoke.txt` 是 CI/smoke 可复现性的入口。constraints 文件及
使用它的 CI workflow 是权威 package inventory；正文不得另行维护
范围更窄的重复清单。截至 `2026-08-07` 的核验，受约束表面包括
`pytest`、`numpy`、`ruff`、`gymnasium`、`coverage`、`gcovr` 等直接
smoke/lint/coverage 依赖，以及专门测试 package build/install 时使用的 Python
构建前端/后端包。

它不应膨胀成隐藏的训练 lockfile。除非消费它的 CI lane 确有需要，或单独批准训练
锁政策，否则不要为 `torch`、`stable-baselines3`、`tensorboard` 或类似可选
训练/实验包添加硬 pin。当前为 smoke 与 coverage lane 约束 `gymnasium`，只证明
该接口依赖边界，不表示训练环境已经被解析或锁定。

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

截至 `2026-08-07` 的核验，`CMakeLists.txt` 与 `pyproject.toml` 当前都声明
`0.2.0`。这项观察不构成永久豁免：每次 release checklist 都必须重新读取两个文件，
在切 release tag 前确认版本同步，或记录已批准的例外。

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
- 每个 lockfile 都是有独立范围的治理 artifact，必须有明确 ownership；不得从
  tool-local lock 推断全仓可复现性。
- 当 CI 依赖安装、发布打包或第三方资产处理方式变化时，更新本政策。
- 除非解析后的环境和 artifact provenance 已记录，否则不要把一次本地训练成功视为发布依赖证据。
