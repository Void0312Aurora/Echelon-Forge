# `src/components/naval` 边界

`components/naval` 保存舰艇、潜艇和舰载航空运作的静态/缓变平台状态组件。
这里放的是 naval 平台数据和甲板运作状态，不负责命令解释、tick 推进或
mission/runtime 编排。

## 允许

- 舰艇和潜艇平台性能、尺度、机动包线等纯数据字段。
- 舰载直升机/甲板运作所需的轻量状态组件。
- 可被 `systems/naval`、`models/`、`core/mission` 读取的 naval platform DTO。

## 禁止

- 舰艇/潜艇运动积分、海况推进或舰载机调度逻辑；这些属于 `systems/naval`。
- naval mission command、command link 或 tasking/C2 DTO。
- Python binding、facade request/result 或 env glue。
- 直接拥有 entity lifecycle 或 helo spawn/recovery runtime owner。

## 当前文件

- [ship_platform.h](ship_platform.h)
  - 水面舰艇平台参数，例如排水量、尺度、速度、转向、耐波与编制。
- [submarine_platform.h](submarine_platform.h)
  - 潜艇平台参数，例如水下航速、深度包线、隐身偏置与深度机动能力。
- [embarked_air_ops.h](embarked_air_ops.h)
  - 舰载航空运作状态，例如 active helo、发收舰偏移、OTH relay 相关标记。

## 依赖方向

本目录是数据层。`systems/naval`、`core/mission`、`runtime/facade` 和
`interfaces/python` 可以消费这些组件；本目录不应反向依赖这些上层。
