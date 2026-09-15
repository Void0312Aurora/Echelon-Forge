# 杀伤链证据留存

2026-09-15 杀伤链工作生成的逐运行 packet 属于生成证据，不属于仓库的
maintained authority，因此不再版本化到 `docs/**/review_packets/`。

本地复现输出统一放在被忽略的
`artifacts/kill_chain/20260915/raw_review_packets/`。CI 或 release 可以将
该目录作为外部 artifact 发布，但只有在记录生成提交、schema 版本、输入与
配置摘要、文件 SHA-256、留存责任人和检索方式后，才能将其认定为 admitted
evidence。

仓库只保留简洁结论、人类可读图像和小型 manifest。原始 packet 通过诊断工具
并显式指定 `--output-dir` 到上述 artifact 路径即可重建。

这遵循长周期治理规则：关闭后的 packet 离开 maintained authority，但其来源
和检索路径必须明确保留。
