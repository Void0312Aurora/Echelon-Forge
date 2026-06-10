# 测试归档

`tests/archive/` 存放仅为追溯保留的历史测试资产。

这里的文件不属于维护中的 pytest 或 JSON contract surface。不要把新的活跃回归测试
放到这里。若要恢复某个已归档 contract，应先把它移回 `tests/contracts/`，再加入
contract surface matrix 或 suite，并验证对应 runner policy。
