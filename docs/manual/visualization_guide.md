# 如何远程查看可视化 (Rerun Visualization)

由于我们运行在无头服务器 (Headless Server) 上，需要使用 **SSH 端口转发** 将服务器上的可视化数据流传到你本地的浏览器观看。

## 1. 建立 SSH 隧道
假设服务器地址为 `server_ip`，请在**你的本地电脑**终端执行：

```bash
ssh -L 9090:127.0.0.1:9090 -L 9876:127.0.0.1:9876 void0312@server_ip
```
*(如果已经连接了 VSCode Remote，请同时添加 9090 和 9876 端口转发)*

## 2. 启动演示脚本
在服务器终端运行：

```bash
# 激活环境 (如果没激活)
source .venv/bin/activate
export PYTHONPATH=$PYTHONPATH:$(pwd)/build
# [关键] 解决 Conda 与系统 GCC 库版本冲突
export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH

# 运行脚本
python3 examples/visualized_demo.py
```

## 3. 在本地观看
打开你可以访问互联网的浏览器（推荐 Chrome/Edge），访问：
*   **[http://localhost:9090](http://localhost:9090)**
*   这会打开由服务器托管的 Rerun Web 版查看器。

你将看到红蓝两个点在三维空间中运动。
