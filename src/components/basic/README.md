# `src/components/basic` 边界

`components/basic` 保存最底层、跨域共享的 ECS component 和标签。

## 允许

- identity、side、position、lifecycle tag 等基础状态。
- 环境数据中必须随实体存储的轻量 component。
- 被多个系统共同读取的稳定基础字段。

## 禁止

- 物理、战斗、传感器或任务专用状态。
- command/tasking DTO。
- runtime、system 或 binding 逻辑。

## 迁移备注

新增字段如果只服务单一业务域，应放到对应业务目录，而不是放进 `basic` 形成隐性全局杂物层。
