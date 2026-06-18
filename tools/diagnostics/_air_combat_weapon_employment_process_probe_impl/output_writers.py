"""CSV, JSON, and plot writers for the process probe."""

from __future__ import annotations

import csv
import json
import os
from typing import Any

import numpy as np


def write_csv(path: str, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    out_path = os.path.abspath(path)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: str, payload: dict[str, Any]) -> None:
    out_path = os.path.abspath(path)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=True)
        f.write("\n")


def plot_rows(rows: list[dict[str, Any]], path: str) -> None:
    try:
        import matplotlib.pyplot as plt
    except Exception as exc:
        raise RuntimeError("plotting requires matplotlib") from exc
    first_episode = min(int(row["episode"]) for row in rows)
    ep_rows = [row for row in rows if int(row["episode"]) == first_episode]
    x = np.asarray([float(row["sim_time_s"]) for row in ep_rows], dtype=np.float32)
    target_health = np.asarray([float(row["target_health"]) for row in ep_rows], dtype=np.float32)
    missiles = np.asarray([float(row["missiles_remaining"]) for row in ep_rows], dtype=np.float32)
    range_km = np.asarray(
        [float(row["target_range_geom_m"]) / 1000.0 for row in ep_rows], dtype=np.float32
    )
    radar = np.asarray(
        [float(row.get("action_radar_on", 0.0)) for row in ep_rows], dtype=np.float32
    )
    master = np.asarray(
        [float(row.get("action_master_arm_on", 0.0)) for row in ep_rows], dtype=np.float32
    )
    fire = np.asarray(
        [float(row.get("action_fire_weapon_on", 0.0)) for row in ep_rows], dtype=np.float32
    )

    fig, axes = plt.subplots(3, 1, figsize=(11, 7), sharex=True)
    axes[0].plot(x, target_health, label="target health")
    axes[0].plot(x, missiles * 25.0, label="blue missiles x25")
    axes[0].set_ylabel("health / ammo")
    axes[0].legend(loc="best")
    axes[1].plot(x, range_km, label="target range km", color="tab:green")
    axes[1].set_ylabel("range km")
    axes[1].legend(loc="best")
    axes[2].step(x, radar, where="post", label="radar")
    axes[2].step(x, master + 1.2, where="post", label="master arm")
    axes[2].step(x, fire + 2.4, where="post", label="fire weapon")
    axes[2].set_yticks([0.5, 1.7, 2.9])
    axes[2].set_yticklabels(["radar", "master", "fire"])
    axes[2].set_xlabel("sim time s")
    axes[2].legend(loc="best")
    fig.tight_layout()
    out_path = os.path.abspath(path)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
