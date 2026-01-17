import argparse
import csv
import json
import os


def load_records(path):
    records = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def moving_average(values, window):
    if window <= 1:
        return values
    output = []
    running = 0.0
    for i, v in enumerate(values):
        running += v
        if i >= window:
            running -= values[i - window]
        denom = min(window, i + 1)
        output.append(running / denom)
    return output


def write_csv(path, records):
    fields = [
        "update",
        "avg_blue_return",
        "avg_red_return",
        "blue_win_rate",
        "red_win_rate",
        "draw_rate",
        "avg_steps",
        "avg_blue_fire",
        "avg_red_fire",
        "avg_blue_detection_steps",
        "avg_red_detection_steps",
        "history_opponent_rate",
    ]
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            row = {k: record.get(k) for k in fields}
            writer.writerow(row)


def plot_curves(records, output_path, window):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return False

    updates = [r.get("update", 0) for r in records]
    blue_ret = moving_average([r.get("avg_blue_return", 0.0) for r in records], window)
    red_ret = moving_average([r.get("avg_red_return", 0.0) for r in records], window)
    blue_win = moving_average([r.get("blue_win_rate", 0.0) for r in records], window)
    red_win = moving_average([r.get("red_win_rate", 0.0) for r in records], window)

    fig, axes = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    axes[0].plot(updates, blue_ret, label="blue_return")
    axes[0].plot(updates, red_ret, label="red_return")
    axes[0].set_ylabel("Return")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(updates, blue_win, label="blue_win_rate")
    axes[1].plot(updates, red_win, label="red_win_rate")
    axes[1].set_ylabel("Win rate")
    axes[1].set_xlabel("Update")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    fig.tight_layout()
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return True


def main():
    parser = argparse.ArgumentParser(description="Plot self-play training log.")
    parser.add_argument("--log", type=str, required=True, help="Path to train_log.jsonl")
    parser.add_argument("--csv", type=str, default="", help="CSV output path")
    parser.add_argument("--plot", type=str, default="", help="PNG output path")
    parser.add_argument("--window", type=int, default=10, help="Moving average window")
    args = parser.parse_args()

    records = load_records(args.log)
    if not records:
        raise SystemExit("No records found.")

    log_dir = os.path.dirname(os.path.abspath(args.log))
    csv_path = args.csv or os.path.join(log_dir, "train_log.csv")
    plot_path = args.plot or os.path.join(log_dir, "train_log.png")

    write_csv(csv_path, records)
    plotted = plot_curves(records, plot_path, args.window)

    print(f"Wrote CSV: {csv_path}")
    if plotted:
        print(f"Wrote plot: {plot_path}")
    else:
        print("Plot skipped (matplotlib not available).")


if __name__ == "__main__":
    main()
