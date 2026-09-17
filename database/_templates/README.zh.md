# 模板区

Language:
- English canonical: [README.md](README.md)
- Chinese companion: `README.zh.md`

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/_templates/README.md`
Owner: `database/equipment-data`
Last verified: `not established`
Content status: provisional navigation scaffold；最终数据契约尚未建立。

## 职责

保存各类对象的结构模板；模板不表示已经收录具体装备。

## 不负责

本目录不定义 runtime 行为、来源 authority 或最终装备数据 schema。

## 当前权威

- [模板字段参考](FIELDS.md)：所有临时模板的字段含义、单位和当前边界；当前仅提供英文主文。
- [共享 Schema 定义](common.schema.json)：各类型 Schema 共用的 JSON Schema 定义。
- 类型 Schema：每个 `*.template.json` 在同目录都有对应的 `*.schema.json`。

## 层级

- 上级：`database//`
- 下级：`module/`、`platform/`、`source/`、`weapon/`

## 维护触发条件

当职责、下级结构或适用的数据契约发生变化时，更新本索引。
