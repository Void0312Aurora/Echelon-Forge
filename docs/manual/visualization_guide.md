<!-- Machine-translated draft generated on 2026-05-18 from docs/manual/visualization_guide.zh.md. Review before treating this file as authoritative. -->

<!-- Machine-translated draft generated on 2026-05-18 from docs/manual/visualization_guide.md. Review before treating this file as authoritative. -->

# How to View Visualizations Remotely (Web Real-Time)

Since we run on a headless server, we need to use **SSH port forwarding** to forward the web visualization page from the server to your local browser.

## 1. Establish SSH Tunnel
Assume the server address is `server_ip`, run on **your local computer** terminal:

```bash
ssh -L 5000:127.0.0.1:5000 void0312@server_ip
```
*(If already connected via VSCode Remote, also add port 5000 forwarding)*

## 2. Start the Demo Script
Run on the server terminal:

```bash
# Activate environment (if not already activated)
source .venv/bin/activate
export PYTHONPATH=$PYTHONPATH:$(pwd)/build
# [Important] Resolve version conflict between Conda and system GCC libraries
export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libstdc++.so.6

# Run the script
python3 examples/viz/perception_viz.py
```

## 3. View Locally
Open a browser and visit:
*   **http://localhost:5000**

You will see real-time positions and sensor visualizations of the red and blue units.
