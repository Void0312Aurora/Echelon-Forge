# 标准维护政策

语言：
- 英文主文：[standards_maintenance_policy.md](standards_maintenance_policy.md)
- 中文辅文：`standards_maintenance_policy.zh.md`

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/engineering/documentation/standards/standards_maintenance_policy.md`
Owner: `engineering/documentation-governance`
Last verified: `2026-08-07`

状态：`2026-08-07`，用于保持维护中标准与实现证据对齐的权威政策。

本政策定义 implementation、active work、test、scenario 或治理发生变化后，
各内容 owner 的维护中标准应如何更新。它补充
[文档工程总览](../README.zh.md)、迁移期
[标准化文档总览](../../../standards/README.zh.md)、
[文档对齐映射](../../../standards/overview/document_alignment_map.zh.md) 和
[双语文档政策](bilingual_documentation_policy.zh.md)。

## 目的

project、architecture、domain、system、learning、operations、engineering 与
research owner 所属的 standards 子树，共同定义仓库的命名、分层、军种/领域语义、
公开来源准入和治理规则。standards 子树不是任务板，但必须与实现保持足够接近，使
贡献者在修改代码、测试、场景或计划时可以信任它。

`docs/standards/` 仍是尚未迁往内容 owner 的维护中标准所使用的迁移期遗留表面。
临时位置不会赋予它更广权威；内容 owner 已存在时，新标准必须使用 owner-local 路由。

本维护政策防止两类失败：

- 标准落后于已经接受的 runtime/test 合同
- 标准文字过度声明实现成熟度，或把任务实验提升成项目级权威

## 权威规则

当标准和实现似乎不一致时，按以下顺序处理：

1. 当前代码、测试、场景、配置和 contract runner 决定事实上的实现状态。
2. 适用内容 owner 的维护中 `standards/` 入口决定命名、分层、所有权、公开来源
   准入和治理规则。
3. 适用 owner 的 `work/active/` 入口决定范围化工作状态、残余和验收证据。

仍位于遗留 `docs/standards/` 与 `docs/task/` 的维护入口在迁移前继续承担相应角色，
但这些根只是过渡路由，不是目标 ownership 模型。

如果可执行证据和标准页面不一致，不要静默选择其一。应打开或使用 review/task
治理通道，分类 drift，并通过明确的标准更新、实现更新或 held 决策收口。

## Drift 分类

| Drift 类型 | 含义 | 必需处理 |
| --- | --- | --- |
| 语义错配 | 标准和实现编码了互相矛盾的含义。 | 选择真实 owner，然后在同一 remediation 切片中更新代码或标准。 |
| 实现超前标准 | 代码、测试、场景或已接受任务证据新增了稳定合同，但标准尚未登记。 | 在宣称该合同 maintained 前，补充或更新标准 owner。 |
| 标准超前实现 | 标准页面描述了尚未实现的目标行为。 | 在证据存在前标记为 planning、held 或 non-runtime。 |
| 状态/日期陈旧 | 页面主体大体正确，但 header 或状态行无法告诉读者它反映哪一批证据。 | 刷新状态行和权威说明。 |
| 双语/索引 drift | 维护中 canonical 页面修改后，辅文、registry 或最近 README 索引未同步。 | 在关闭切片前更新 peer、registry 和索引。 |

## 准入门槛

新增或扩展 standards contract 必须说明：

- 内容 owner；适用时还要说明所属层，例如 `foundation`、`bridge`、`joint`、
  `services`、某个领域特化、`model` 或 `governance`
- 若页面描述当前行为，必须说明实现证据
- 若合同来自工作流稳定化，必须说明 task 或 review 证据
- 涉及 realism 或 doctrine 声明时，必须说明公开来源依据
- 状态类别：authoritative、specialization、planning supplement、held 或 archived
- 受影响表面的双语辅文预期

禁止空 owner 规则：

- 不要为了展示未来结构而创建 owner-local `standards/` 目录或
  `src/*/domains/<domain>` owner 空壳。
- 如果某一层尚未接受，应写明 held 或 planning，而不是添加看起来像生产路径的占位。
- 一个领域可以在 components、systems、models 三层拥有不同成熟度。缺失层应保持可见，
  不应被空目录或 dummy interface 隐藏。

## 必须更新的触发器

以下变化落地时，必须更新标准页面，或创建一个说明为何暂缓更新的 review gap：

- 新 DTO 字段、枚举值、mode、scenario contract、model contract 或 runtime
  workflow stage 进入 maintained
- 已接受任务改变了军种/领域所有权或能力声明
- runtime/test 合同退役了兼容路径或替换了旧 owner
- planning supplement 不再与当前源码布局对齐
- 维护中的治理规则改变了贡献者派发、翻译、验收、归档或验证工作的方式

不要只依赖带日期 review 文件作为当前权威。最近的维护 owner README 或 standards
入口必须指向当前解释。

## 状态与 Header 规则

维护中的 standards 页面应在顶部附近包含状态行：

```md
Status: `<YYYY-MM-DD>` <authority state> <short scope>.
```

使用精确 authority state：

- `authoritative`
- `authoritative foundation`
- `authoritative bridge`
- `authoritative model architecture`
- `specialization`
- `active planning supplement, not a current runtime contract`
- `held pending <evidence>`
- `archived`

不要用新日期暗示页面已经 accepted，尤其当正文仍包含 unresolved 或 planning-only
合同时。日期表示页面被检查或更新过；authority state 才说明页面能被怎样使用。

## Review 与收口通道

审计或实现工作发现的 standards drift，应在内容 owner 有边界的 `reviews/`、
`work/issues/` 或 `work/active/` 表面追踪，直到它被关闭、held 或归档。遗留
review/task 路由在迁移前继续有效。2026-06-10 的先例是已归档 accepted
[标准化文档治理](../../../task/review/archive/standards_documentation_governance/README.zh.md)
子项目。

参考路径：`docs/task/review/archive/standards_documentation_governance/README.md`。

一个 gap 只有在满足以下条件时才能关闭：

- owner 层已命名
- 宣称当前实现时，已引用 code/test/scenario 证据
- planning-only 或 held 行为被诚实标注
- 双语辅文和最近索引已同步
- 聚焦验证拥有通过/失败证据

## 验证

standards governance 切片使用以下检查：

```bash
python3 tools/maintenance/translate_docs_batch.py audit --root docs \
  --registry docs/engineering/documentation/reference/bilingual_document_clusters.json
python -m pytest -q tests/architecture/governance
git diff --check -- docs tools/maintenance tests/architecture/governance
```

如果 remediation 切片触及代码或 runtime 合同，必须补充受影响 runtime、architecture、
build 或 contract 测试。

## 相关文档

- [文档工程总览](../README.zh.md)
- [迁移期标准化文档总览](../../../standards/README.zh.md)
- [文档对齐映射](../../../standards/overview/document_alignment_map.zh.md)
- [双语文档政策](bilingual_documentation_policy.zh.md)
- [双语文档簇](../reference/bilingual_document_clusters.zh.md)
- [Subagent 使用规范](../../automation/standards/subagent_usage_policy.zh.md)
- [标准化文档治理](../../../task/review/archive/standards_documentation_governance/README.zh.md)
