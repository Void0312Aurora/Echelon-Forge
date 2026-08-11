# 发布工程

语言：英文规范页见 [README.md](README.md)；本页为中文配套。

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/engineering/release/README.md`
Owner: `engineering/release`
Last verified: `2026-08-07`

本区域负责全仓依赖与发布治理，包括依赖声明、项目版本一致性、发布门禁，以及第三方内容或
资产再分发检查。它不拥有各内容 owner 定义的版本语义、变更声明或验收证据。各 owner
提供其范围内的事实和产物，发布工程负责定义并执行跨仓门禁。

## 当前标准

- [发布与依赖政策](standards/release_and_dependency_policy.zh.md)：规定 release
  candidate 在依赖、版本、release notes、checklist、许可证和 provenance 方面的最低要求。

## 当前边界

- 上次核验时，`CMakeLists.txt` 与 `pyproject.toml` 均声明版本 `0.2.0`。每个
  release candidate 的门禁仍必须重新检查这两个版本面。
- 仓库尚无 canonical CHANGELOG 或专用 release-checklist 文档。在这些维护产物出现前，
  切 tag 前必须提供等价的 release-note 与 checklist packet。
- Smoke constraints 与 tool-local lock 产物的范围都窄于完整解析的仓库或训练环境，
  不得将其作为全环境可复现性的证明。
- 本索引及其政策定义治理要求，不表示仓库当前已经达到 release-ready 状态。
