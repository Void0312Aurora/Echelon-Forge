import json
import os


def _load_log(log_path):
    ticks = []
    entities = None

    with open(log_path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if record.get("type") == "meta":
                entities = record.get("data", {}).get("entities")
                continue
            if record.get("type") != "tick":
                continue
            if entities is None:
                entities = list(record.get("entities", {}).keys())
            ticks.append(record)

    return entities or [], ticks


def _pick_color(name):
    lname = name.lower()
    if "blue" in lname:
        return "tab:blue"
    if "red" in lname:
        return "tab:red"
    return "tab:gray"


def render_gif(log_path, output_path, fps=20, max_frames=600):
    try:
        import matplotlib.pyplot as plt
        from matplotlib.animation import FuncAnimation, PillowWriter
    except ImportError as exc:
        raise RuntimeError(
            "matplotlib (and Pillow) are required to render GIF output."
        ) from exc

    entities, ticks = _load_log(log_path)
    if not ticks:
        raise RuntimeError("No tick records found in log.")

    frames = ticks
    if max_frames and len(frames) > max_frames:
        stride = max(1, len(frames) // max_frames)
        frames = frames[::stride]

    # Compute bounds
    xs = []
    ys = []
    for record in frames:
        for pos in record["entities"].values():
            xs.append(pos[0])
            ys.append(pos[1])

    if not xs or not ys:
        raise RuntimeError("No positions available to render.")

    padding = 1000.0
    min_x, max_x = min(xs) - padding, max(xs) + padding
    min_y, max_y = min(ys) - padding, max(ys) + padding

    fig, ax = plt.subplots()
    ax.set_xlim(min_x, max_x)
    ax.set_ylim(min_y, max_y)
    ax.set_aspect("equal")
    ax.set_xlabel("East (m)")
    ax.set_ylabel("North (m)")
    ax.set_title("Scenario Playback (2D)")

    lines = {}
    dots = {}
    trails = {name: [] for name in entities}
    for name in entities:
        color = _pick_color(name)
        line, = ax.plot([], [], color=color, linewidth=1.0, alpha=0.7)
        dot, = ax.plot([], [], marker="o", color=color, markersize=4)
        lines[name] = line
        dots[name] = dot

    def update(frame):
        positions = frame["entities"]
        for name in entities:
            pos = positions.get(name)
            if pos is None:
                continue
            trails[name].append((pos[0], pos[1]))
            xs_local = [p[0] for p in trails[name]]
            ys_local = [p[1] for p in trails[name]]
            lines[name].set_data(xs_local, ys_local)
            dots[name].set_data([pos[0]], [pos[1]])
        return list(lines.values()) + list(dots.values())

    anim = FuncAnimation(fig, update, frames=frames, interval=1000 / fps, blit=True)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    anim.save(output_path, writer=PillowWriter(fps=fps))
    plt.close(fig)
