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

## 2. Start the Visualization Service
Run on the server terminal:

```bash
# Activate environment (if not already activated)
source .venv/bin/activate
export PYTHONPATH=$PYTHONPATH:$(pwd)/build
# [Important] Resolve version conflict between Conda and system GCC libraries
export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libstdc++.so.6

# Run the maintained visualization entrypoint
python3 examples/viz/run_viz.py --scenario <path-to-scenario.json>
```

If you want the legacy single-session runner instead of the session manager UI,
you can also use:

```bash
python3 examples/viz/viz_runner.py --scenario <path-to-scenario.json>
```

Both entrypoints serve the web UI on port `5000` by default. `run_viz.py` is
the preferred maintained entrypoint because it routes through the current
unified visualization app and can load scenarios or profiles at startup.

## 3. View Locally
Open a browser and visit:
*   **http://localhost:5000**

You will see the current web visualization UI, including real-time platform
state and sensor/track overlays for the loaded scenario.
