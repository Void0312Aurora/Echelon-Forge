#!/bin/bash

# Ensure we are in the project root
cd "$(dirname "$0")"

# Activate venv
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "Virtual environment not found in .venv/"
    exit 1
fi

# Set PYTHONPATH to include build artifacts
export PYTHONPATH=$PYTHONPATH:$(pwd)/build

# CRITICAL: Force system libstdc++ to avoid Conda conflict
export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libstdc++.so.6

echo "Generating Data..."
python3 examples/visualized_demo.py

echo "---------------------------------------------------"
echo "Starting Rerun File Server..."
echo "Ensure you have forwarded port 9090:"
echo "  ssh -L 9090:localhost:9090 ..."
echo "Then visit http://localhost:9090"
echo "---------------------------------------------------"

# Run serve-web on the specific file. 
# Explicitly use 9090 for web listener.
# Note: 0.0.0.0 allows external connection if needed, but localhost is safer safely via tunnel.
rerun --serve-web --web-viewer-port 9090 demo.rrd
