# 如何远程查看可视化 (Web 实时)

由于我们运行在无头服务器 (Headless Server) 上，需要使用 **SSH 端口转发** 将服务器上的 Web 可视化页面转发到你本地浏览器。

## 1. 建立 SSH 隧道
假设服务器地址为 `server_ip`，请在**你的本地电脑**终端执行：

```bash
ssh -L 5000:127.0.0.1:5000 void0312@server_ip
```
*(如果已经连接了 VSCode Remote，请同时添加 5000 端口转发)*

## 2. 启动演示脚本
在服务器终端运行：

```bash
# 激活环境 (如果没激活)
source .venv/bin/activate
export PYTHONPATH=$PYTHONPATH:$(pwd)/build
# [关键] 解决 Conda 与系统 GCC 库版本冲突
export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libstdc++.so.6

# 运行脚本
python3 examples/viz/perception_viz.py
```

## 3. 在本地观看
打开浏览器访问：
*   **http://localhost:5000**

你将看到红蓝单位的实时位置与传感器可视化。
