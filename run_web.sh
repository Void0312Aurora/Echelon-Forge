#!/bin/bash
cd "$(dirname "$0")"

# Activate venv
source .venv/bin/activate
export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libstdc++.so.6

echo "Starting Web Visualization..."
echo "Please forward port 5000: ssh -L 5000:localhost:5000 ..."
echo "Then visit http://localhost:5000"

python3 examples/perception_viz.py
