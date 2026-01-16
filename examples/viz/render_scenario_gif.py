import os
import sys

# Allow importing local utilities.
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(repo_root)

from python.scenario_visualizer import render_gif


def main():
    if len(sys.argv) < 3:
        print("Usage: python examples/viz/render_scenario_gif.py <log.jsonl> <out.gif>")
        sys.exit(1)

    log_path = sys.argv[1]
    output_path = sys.argv[2]

    if not os.path.isabs(log_path):
        log_path = os.path.join(repo_root, log_path)
    if not os.path.isabs(output_path):
        output_path = os.path.join(repo_root, output_path)

    render_gif(log_path, output_path)
    print(f"Saved GIF to {output_path}")


if __name__ == "__main__":
    main()
