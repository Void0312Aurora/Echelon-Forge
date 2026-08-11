# 如何远程查看可视化 (Web 实时)

由于我们运行在无头服务器 (Headless Server) 上，需要使用 **SSH 端口转发** 将服务器上的 Web 可视化页面转发到你本地浏览器。

## 1. 建立 SSH 隧道
假设服务器地址为 `server_ip`，请在**你的本地电脑**终端执行：

```bash
ssh -L 5000:127.0.0.1:5000 void0312@server_ip
```
*(如果已经连接了 VSCode Remote，请同时添加 5000 端口转发)*

## 2. 启动可视化服务
在服务器终端运行：

```bash
# 激活环境 (如果没激活)
source .venv/bin/activate
export PYTHONPATH=$PYTHONPATH:$(pwd)/build
# [关键] 解决 Conda 与系统 GCC 库版本冲突
export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libstdc++.so.6

# 运行当前维护中的可视化入口
python3 examples/viz/run_viz.py --scenario <scenario.json 路径>
```

如果你想直接使用 legacy 的单会话 runner，而不是 session manager UI，
也可以运行：

```bash
python3 examples/viz/viz_runner.py --scenario <scenario.json 路径>
```

这两个入口默认都会在 `5000` 端口启动 Web UI。当前优先推荐
`run_viz.py`，因为它接入了统一可视化应用，支持在启动时直接加载
scenario 或 profile。

## 3. 在本地观看
打开浏览器访问：
*   **http://localhost:5000**

你将看到当前的 Web 可视化界面，包括已加载场景中的平台实时状态以及
传感器/目标轨迹叠加信息。
