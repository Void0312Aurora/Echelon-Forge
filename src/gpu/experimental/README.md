# `src/gpu/experimental` 边界

`gpu/experimental` 保存尚未进入维护主线的 GPU 探针、验证代码和临时实验。这里的代码不能被默认为 production truth path。

## 允许

- 性能探针。
- parity prototype。
- 未冻结的 GPU backend 实验。

## 禁止

- 默认 runtime backend。
- 被 facade 或训练主线无条件依赖。
- 没有说明的行为替换。

## 迁移备注

实验代码进入 `gpu/` 主目录前，必须有冻结计划、parity 边界和维护 API。
