from __future__ import annotations

from collections import defaultdict, deque
from typing import Any
import os

import numpy as np
from stable_baselines3.common.callbacks import BaseCallback


def _safe_mean(values):
    if values is None:
        return None
    arr = np.asarray(values, dtype=np.float64)
    if arr.size == 0:
        return None
    return float(arr.mean())


class CMODiagnosticsCallback(BaseCallback):
    """
    Lightweight TensorBoard diagnostics for debugging "no learning / unstable" training runs.

    Logs a few key scalars from observations/actions/infos at a fixed timestep interval.
    """

    TERMINAL_REWARD_KEYS = (
        "total",
        "crash_penalty",
        "failfast_penalty",
        "off_runway_terminate_penalty",
        "gear_collapse_penalty",
        "overload_penalty",
        "g_deviation_penalty",
        "waypoint_distance",
        "waypoint_cross_track",
        "waypoint_progress",
        "waypoint_success_bonus",
        "objective_bonus",
        "combat_win_bonus",
        "combat_loss_penalty",
        "combat_draw_reward",
    )

    LEADER_REWARD_KEYS = (
        "execution_reward",
        "command_change_penalty",
        "invalid_phase_penalty",
        "premature_approach_penalty",
        "baseline_deviation_penalty",
        "mode_change_penalty",
    )

    def __init__(self, log_every_timesteps: int = 50_000, preterm_window_steps: int = 32, verbose: int = 0):
        super().__init__(verbose=verbose)
        self.log_every_timesteps = int(log_every_timesteps)
        self.preterm_window_steps = max(4, int(preterm_window_steps))
        self._next_log_t = int(log_every_timesteps)
        self._histories: list[deque] = []
        self._episodes_window = 0
        self._term_counts_window: dict[str, int] = defaultdict(int)
        self._term_counts_total: dict[str, int] = defaultdict(int)
        self._failure_window = 0
        self._terminal_reward_window: dict[str, list[float]] = defaultdict(list)
        self._preterm_stats_window: dict[str, list[float]] = defaultdict(list)
        self._coop_world_done_window = 0
        self._coop_world_success_window = 0
        self._coop_shared_reset_window = 0
        self._coop_timeout_window = 0
        self._coop_role_episode_counts_window: dict[str, int] = defaultdict(int)
        self._coop_role_success_counts_window: dict[str, int] = defaultdict(int)
        self._coop_role_shared_reset_counts_window: dict[str, int] = defaultdict(int)
        self._coop_role_term_counts_window: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._coop_role_reward_window: dict[str, list[float]] = defaultdict(list)
        self._coop_role_length_window: dict[str, list[float]] = defaultdict(list)
        self._coop_role_waypoint_index_window: dict[str, list[float]] = defaultdict(list)
        self._coop_role_waypoint_progress_window: dict[str, list[float]] = defaultdict(list)
        self._coop_world_min_progress_window: list[float] = []
        self._coop_world_max_progress_window: list[float] = []
        self._coop_world_progress_gap_window: list[float] = []
        self._coop_world_slot_seen: dict[int, set[int]] = defaultdict(set)
        self._coop_world_slot_success: dict[int, bool] = defaultdict(bool)
        self._coop_world_slot_timeout: dict[int, bool] = defaultdict(bool)
        self._coop_world_slot_progress_values: dict[int, list[float]] = defaultdict(list)
        self._hmoe_param_stats_next_log_t = int(log_every_timesteps)

    def _on_training_start(self) -> None:
        n_envs = int(getattr(self.training_env, "num_envs", 1))
        self._histories = [deque(maxlen=self.preterm_window_steps) for _ in range(max(1, n_envs))]
        self._episodes_window = 0
        self._term_counts_window = defaultdict(int)
        self._term_counts_total = defaultdict(int)
        self._failure_window = 0
        self._terminal_reward_window = defaultdict(list)
        self._preterm_stats_window = defaultdict(list)
        self._coop_world_done_window = 0
        self._coop_world_success_window = 0
        self._coop_shared_reset_window = 0
        self._coop_timeout_window = 0
        self._coop_role_episode_counts_window = defaultdict(int)
        self._coop_role_success_counts_window = defaultdict(int)
        self._coop_role_shared_reset_counts_window = defaultdict(int)
        self._coop_role_term_counts_window = defaultdict(lambda: defaultdict(int))
        self._coop_role_reward_window = defaultdict(list)
        self._coop_role_length_window = defaultdict(list)
        self._coop_role_waypoint_index_window = defaultdict(list)
        self._coop_role_waypoint_progress_window = defaultdict(list)
        self._coop_world_min_progress_window = []
        self._coop_world_max_progress_window = []
        self._coop_world_progress_gap_window = []
        self._coop_world_slot_seen = defaultdict(set)
        self._coop_world_slot_success = defaultdict(bool)
        self._coop_world_slot_timeout = defaultdict(bool)
        self._coop_world_slot_progress_values = defaultdict(list)
        self._next_log_t = int(self.log_every_timesteps)
        self._hmoe_param_stats_next_log_t = int(self.log_every_timesteps)

    @staticmethod
    def _normalize_reason(reason: str) -> str:
        if not reason:
            return "unknown"
        out = []
        for ch in str(reason).strip().lower():
            if ("a" <= ch <= "z") or ("0" <= ch <= "9"):
                out.append(ch)
            else:
                out.append("_")
        s = "".join(out).strip("_")
        while "__" in s:
            s = s.replace("__", "_")
        return s if s else "unknown"

    @staticmethod
    def _is_failure_reason(reason: str) -> bool:
        if reason.startswith("success"):
            return False
        if reason == "combat_win":
            return False
        if reason in ("timeout", "running"):
            return False
        return True

    def _infer_termination_reason(self, info: dict) -> str:
        if not isinstance(info, dict):
            return "done_unknown"

        tr = info.get("termination_reason")
        if isinstance(tr, str) and tr.strip():
            return self._normalize_reason(tr)

        rt = info.get("reward_terms")
        if isinstance(rt, dict):
            try:
                if float(rt.get("nan_guard", 0.0)) > 0.0:
                    return "nan_guard"
            except Exception:
                pass
            if "waypoint_success_bonus" in rt:
                try:
                    if float(rt.get("waypoint_success_bonus", 0.0)) > 0.0:
                        return "success_waypoint"
                except Exception:
                    pass
            if "objective_bonus" in rt:
                try:
                    if float(rt.get("objective_bonus", 0.0)) > 0.0:
                        return "success_objective"
                except Exception:
                    pass
            if "off_runway_terminate_penalty" in rt:
                return "off_runway_terminate"
            if "gear_collapse_penalty" in rt:
                return "gear_collapse"
            if "failfast_penalty" in rt:
                return "failfast"
            if "crash_penalty" in rt:
                return "crash"

        ms = info.get("mission_status")
        if ms is not None:
            try:
                term = float(ms[3])
                if term > 0.5:
                    return "success"
                if term < -0.5:
                    return "failure_unknown"
            except Exception:
                pass

        if bool(info.get("TimeLimit.truncated", False)) or bool(info.get("truncated", False)):
            return "timeout"
        return "done_unknown"

    def _extract_terminal_inst(self, info: dict):
        if not isinstance(info, dict):
            return None
        term_obs = info.get("terminal_observation", None)
        if isinstance(term_obs, dict) and ("instruments" in term_obs):
            try:
                arr = np.asarray(term_obs["instruments"], dtype=np.float32).reshape(-1)
                if arr.size > 0:
                    return arr
            except Exception:
                return None
        return None

    def _make_snapshot(self, inst_row, action_row, reward_scalar):
        snap = {}
        if inst_row is not None:
            try:
                inst = np.asarray(inst_row, dtype=np.float32).reshape(-1)
            except Exception:
                inst = None
            if inst is not None and inst.size >= 11:
                snap["ias"] = float(inst[0])
                if inst.size > 3:
                    snap["alt_agl"] = float(inst[3])
                if inst.size > 5:
                    snap["aoa"] = float(inst[5])
                if inst.size > 6:
                    snap["beta"] = float(inst[6])
                if inst.size > 7:
                    snap["pitch"] = float(inst[7])
                if inst.size > 8:
                    snap["roll"] = float(inst[8])
                if inst.size > 10:
                    snap["g"] = float(inst[10])
                if inst.size > 14:
                    snap["yaw_rate"] = float(inst[14])

        if action_row is not None:
            try:
                a = np.asarray(action_row, dtype=np.float32).reshape(-1)
            except Exception:
                a = None
            if a is not None and a.size > 3:
                snap["throttle"] = float(a[3])
            if a is not None and a.size > 8:
                brake_raw = float(max(float(a[7]), float(a[8])))
                snap["brake"] = float(np.clip((brake_raw - 0.5) * 2.0, 0.0, 1.0))
            if a is not None and a.size > 16:
                snap["radar_active"] = float(a[9] > 0.5)
                snap["master_arm"] = float(a[13] > 0.5)
                snap["fire_weapon"] = float(a[14] > 0.5)
                snap["fire_gun"] = float(a[15] > 0.5)
                snap["weapon_select_id"] = float(int(np.clip(float(a[16]), 0.0, 1.0) * 7.0))

        if reward_scalar is not None:
            try:
                snap["reward"] = float(reward_scalar)
            except Exception:
                pass
        return snap if snap else None

    def _record_terminal_reward_terms(self, info: dict) -> None:
        if not isinstance(info, dict):
            return
        rt = info.get("reward_terms")
        if not isinstance(rt, dict):
            return
        for key in self.TERMINAL_REWARD_KEYS:
            if key not in rt:
                continue
            try:
                self._terminal_reward_window[key].append(float(rt[key]))
            except Exception:
                continue

    def _record_preterm_window(self, hist: deque) -> None:
        if not hist:
            return
        snap_list = list(hist)
        self._preterm_stats_window["window_len_steps"].append(float(len(snap_list)))

        def _values(name: str):
            vals = []
            for s in snap_list:
                if name in s:
                    try:
                        vals.append(float(s[name]))
                    except Exception:
                        continue
            return vals

        alt = _values("alt_agl")
        if alt:
            self._preterm_stats_window["min_alt_agl_m"].append(float(np.min(alt)))
            self._preterm_stats_window["final_alt_agl_m"].append(float(alt[-1]))

        roll = _values("roll")
        if roll:
            self._preterm_stats_window["max_abs_roll_deg"].append(float(np.max(np.abs(roll))))
        pitch = _values("pitch")
        if pitch:
            self._preterm_stats_window["max_abs_pitch_deg"].append(float(np.max(np.abs(pitch))))
        aoa = _values("aoa")
        if aoa:
            self._preterm_stats_window["max_abs_aoa_deg"].append(float(np.max(np.abs(aoa))))
        beta = _values("beta")
        if beta:
            self._preterm_stats_window["max_abs_beta_deg"].append(float(np.max(np.abs(beta))))
        yaw_rate = _values("yaw_rate")
        if yaw_rate:
            self._preterm_stats_window["max_abs_yaw_rate_deg_s"].append(float(np.max(np.abs(yaw_rate))))
        g_vals = _values("g")
        if g_vals:
            self._preterm_stats_window["max_abs_g"].append(float(np.max(np.abs(g_vals))))
        thr = _values("throttle")
        if thr:
            self._preterm_stats_window["mean_throttle"].append(float(np.mean(thr)))
        brk = _values("brake")
        if brk:
            self._preterm_stats_window["mean_brake"].append(float(np.mean(brk)))
        for switch_name in ("radar_active", "master_arm", "fire_weapon", "fire_gun"):
            vals = _values(switch_name)
            if vals:
                self._preterm_stats_window[f"mean_{switch_name}"].append(float(np.mean(vals)))
        weapon_select = _values("weapon_select_id")
        if weapon_select:
            self._preterm_stats_window["mean_weapon_select_id"].append(float(np.mean(weapon_select)))

    @staticmethod
    def _coop_role_name(info: dict) -> str | None:
        if not isinstance(info, dict):
            return None
        role = str(info.get("formation_role_id", "") or "").strip()
        entity = str(info.get("entity_name", "") or "").strip()
        if role:
            return role
        if entity:
            return entity
        return None

    def _record_cooperative_episode(self, info: dict, reason: str) -> None:
        if not isinstance(info, dict):
            return
        world_index = info.get("world_index", None)
        slot_index = info.get("slot_index", None)
        slots_per_world = info.get("slots_per_world", None)
        if world_index is None or slot_index is None:
            return
        try:
            world_idx = int(world_index)
            slot_idx = int(slot_index)
            expected_slots = max(1, int(slots_per_world)) if slots_per_world is not None else 1
        except Exception:
            return

        role_name = self._coop_role_name(info)
        if role_name:
            self._coop_role_episode_counts_window[role_name] += 1
            ep = info.get("episode", {})
            if isinstance(ep, dict):
                try:
                    self._coop_role_reward_window[role_name].append(float(ep.get("r", 0.0)))
                except Exception:
                    pass
                try:
                    self._coop_role_length_window[role_name].append(float(ep.get("l", 0.0)))
                except Exception:
                    pass
            ms = info.get("mission_status")
            if ms is not None:
                try:
                    arr = np.asarray(ms, dtype=np.float32).reshape(-1)
                except Exception:
                    arr = None
                if arr is not None:
                    if arr.size >= 2:
                        try:
                            self._coop_role_waypoint_index_window[role_name].append(float(arr[1]))
                        except Exception:
                            pass
                    if arr.size >= 3:
                        try:
                            waypoint_count = float(arr[2])
                            progress = float(arr[1]) / waypoint_count if waypoint_count > 0.5 else 0.0
                            self._coop_role_waypoint_progress_window[role_name].append(progress)
                        except Exception:
                            pass
            if bool(float(info.get("shared_world_reset", 0.0)) > 0.5):
                self._coop_role_shared_reset_counts_window[role_name] += 1
            if str(reason).strip():
                self._coop_role_term_counts_window[role_name][str(reason)] += 1

        success = False
        if ms is not None:
            try:
                arr = np.asarray(ms, dtype=np.float32).reshape(-1)
                if arr.size >= 4 and float(arr[3]) > 0.5:
                    success = True
            except Exception:
                success = False
            else:
                if arr.size >= 3:
                    try:
                        waypoint_count = float(arr[2])
                        progress = float(arr[1]) / waypoint_count if waypoint_count > 0.5 else 0.0
                        self._coop_world_slot_progress_values[world_idx].append(progress)
                    except Exception:
                        pass
        if role_name and success:
            self._coop_role_success_counts_window[role_name] += 1

        self._coop_world_slot_seen[world_idx].add(slot_idx)
        world_success_flag = bool(float(info.get("world_success", 0.0)) > 0.5) if isinstance(info, dict) else False
        self._coop_world_slot_success[world_idx] = bool(self._coop_world_slot_success[world_idx] or success)
        self._coop_world_slot_timeout[world_idx] = bool(
            self._coop_world_slot_timeout[world_idx] or str(reason) == "timeout"
        )
        if bool(float(info.get("shared_world_reset", 0.0)) > 0.5):
            self._coop_shared_reset_window += 1

        if bool(float(info.get("world_done", 0.0)) > 0.5) and len(self._coop_world_slot_seen[world_idx]) >= expected_slots:
            self._coop_world_done_window += 1
            if bool(world_success_flag):
                self._coop_world_success_window += 1
            if bool(self._coop_world_slot_timeout[world_idx]):
                self._coop_timeout_window += 1
            progress_vals = self._coop_world_slot_progress_values.get(world_idx, [])
            if progress_vals:
                min_progress = float(np.min(progress_vals))
                max_progress = float(np.max(progress_vals))
                self._coop_world_min_progress_window.append(min_progress)
                self._coop_world_max_progress_window.append(max_progress)
                self._coop_world_progress_gap_window.append(float(max_progress - min_progress))
            self._coop_world_slot_seen.pop(world_idx, None)
            self._coop_world_slot_success.pop(world_idx, None)
            self._coop_world_slot_timeout.pop(world_idx, None)
            self._coop_world_slot_progress_values.pop(world_idx, None)

    def _record_event_diagnostics(self) -> None:
        if self._episodes_window > 0:
            episodes = float(self._episodes_window)
            self.logger.record("diag/episodes_done_window", episodes)
            self.logger.record("diag/failure_frac_window", float(self._failure_window) / episodes)
            for reason in sorted(self._term_counts_window.keys()):
                cnt = float(self._term_counts_window[reason])
                self.logger.record(f"diag/term_frac_{reason}", cnt / episodes)
                self.logger.record(f"diag/term_count_total_{reason}", float(self._term_counts_total[reason]))

        for k, vals in self._terminal_reward_window.items():
            if vals:
                self.logger.record(f"diag/term_rew_{k}", float(np.mean(np.asarray(vals, dtype=np.float32))))

        for k, vals in self._preterm_stats_window.items():
            if vals:
                self.logger.record(f"diag/preterm_{k}", float(np.mean(np.asarray(vals, dtype=np.float32))))

        if self._coop_world_done_window > 0:
            worlds = float(self._coop_world_done_window)
            self.logger.record("coop_diag/world_episodes_done_window", worlds)
            self.logger.record("coop_diag/world_success_frac_window", float(self._coop_world_success_window) / worlds)
            self.logger.record("coop_diag/world_timeout_frac_window", float(self._coop_timeout_window) / worlds)
            self.logger.record(
                "coop_diag/shared_reset_per_world_mean",
                float(self._coop_shared_reset_window) / worlds,
            )
            if self._coop_world_min_progress_window:
                self.logger.record(
                    "coop_diag/world_min_waypoint_progress_frac_mean",
                    float(np.mean(np.asarray(self._coop_world_min_progress_window, dtype=np.float32))),
                )
            if self._coop_world_max_progress_window:
                self.logger.record(
                    "coop_diag/world_max_waypoint_progress_frac_mean",
                    float(np.mean(np.asarray(self._coop_world_max_progress_window, dtype=np.float32))),
                )
            if self._coop_world_progress_gap_window:
                self.logger.record(
                    "coop_diag/world_waypoint_progress_gap_frac_mean",
                    float(np.mean(np.asarray(self._coop_world_progress_gap_window, dtype=np.float32))),
                )
        total_role_eps = float(sum(self._coop_role_episode_counts_window.values()))
        if total_role_eps > 0.0:
            self.logger.record("coop_diag/slot_episodes_done_window", total_role_eps)
        for role_name in sorted(self._coop_role_episode_counts_window.keys()):
            episodes = float(self._coop_role_episode_counts_window[role_name])
            if episodes <= 0.0:
                continue
            role_key = self._normalize_reason(role_name)
            self.logger.record(
                f"coop_diag/role_{role_key}_success_frac_window",
                float(self._coop_role_success_counts_window[role_name]) / episodes,
            )
            self.logger.record(
                f"coop_diag/role_{role_key}_shared_reset_frac_window",
                float(self._coop_role_shared_reset_counts_window[role_name]) / episodes,
            )
            rewards = self._coop_role_reward_window.get(role_name, [])
            if rewards:
                self.logger.record(
                    f"coop_diag/role_{role_key}_reward_mean",
                    float(np.mean(np.asarray(rewards, dtype=np.float32))),
                )
            lengths = self._coop_role_length_window.get(role_name, [])
            if lengths:
                self.logger.record(
                    f"coop_diag/role_{role_key}_episode_len_mean",
                    float(np.mean(np.asarray(lengths, dtype=np.float32))),
                )
            waypoint_indices = self._coop_role_waypoint_index_window.get(role_name, [])
            if waypoint_indices:
                self.logger.record(
                    f"coop_diag/role_{role_key}_waypoint_index_mean",
                    float(np.mean(np.asarray(waypoint_indices, dtype=np.float32))),
                )
            waypoint_progress = self._coop_role_waypoint_progress_window.get(role_name, [])
            if waypoint_progress:
                self.logger.record(
                    f"coop_diag/role_{role_key}_waypoint_progress_frac_mean",
                    float(np.mean(np.asarray(waypoint_progress, dtype=np.float32))),
                )
            for reason, count in sorted(self._coop_role_term_counts_window[role_name].items()):
                self.logger.record(
                    f"coop_diag/role_{role_key}_term_frac_{reason}",
                    float(count) / episodes,
                )

        self._episodes_window = 0
        self._failure_window = 0
        self._term_counts_window = defaultdict(int)
        self._terminal_reward_window = defaultdict(list)
        self._preterm_stats_window = defaultdict(list)
        self._coop_world_done_window = 0
        self._coop_world_success_window = 0
        self._coop_shared_reset_window = 0
        self._coop_timeout_window = 0
        self._coop_role_episode_counts_window = defaultdict(int)
        self._coop_role_success_counts_window = defaultdict(int)
        self._coop_role_shared_reset_counts_window = defaultdict(int)
        self._coop_role_term_counts_window = defaultdict(lambda: defaultdict(int))
        self._coop_role_reward_window = defaultdict(list)
        self._coop_role_length_window = defaultdict(list)
        self._coop_role_waypoint_index_window = defaultdict(list)
        self._coop_role_waypoint_progress_window = defaultdict(list)
        self._coop_world_min_progress_window = []
        self._coop_world_max_progress_window = []
        self._coop_world_progress_gap_window = []
        self._coop_world_slot_seen = defaultdict(set)
        self._coop_world_slot_success = defaultdict(bool)
        self._coop_world_slot_timeout = defaultdict(bool)
        self._coop_world_slot_progress_values = defaultdict(list)

    @staticmethod
    def _mean_info_values(infos: list[dict], key: str) -> float | None:
        vals = []
        for info in infos:
            if not isinstance(info, dict) or key not in info:
                continue
            try:
                vals.append(float(info[key]))
            except Exception:
                continue
        return _safe_mean(vals)

    @staticmethod
    def _mean_reward_term_values(infos: list[dict], info_key: str, term_key: str) -> float | None:
        vals = []
        for info in infos:
            if not isinstance(info, dict):
                continue
            rt = info.get(info_key)
            if not isinstance(rt, dict) or term_key not in rt:
                continue
            try:
                vals.append(float(rt[term_key]))
            except Exception:
                continue
        return _safe_mean(vals)

    def _record_leader_diagnostics(self, obs, infos: list[dict]) -> None:
        if isinstance(obs, dict) and "ownship" in obs:
            try:
                own = np.asarray(obs["ownship"], dtype=np.float32)
                if own.ndim == 1:
                    own = own.reshape(1, -1)
                if own.ndim == 2 and own.shape[1] >= 12:
                    self.logger.record("leader_diag/ias_mean", float(own[:, 0].mean()))
                    self.logger.record("leader_diag/alt_agl_mean", float(own[:, 2].mean()))
                    self.logger.record("leader_diag/alt_baro_mean", float(own[:, 3].mean()))
                    self.logger.record("leader_diag/vvi_mean", float(own[:, 4].mean()))
                    self.logger.record("leader_diag/heading_mean", float(own[:, 5].mean()))
                    self.logger.record("leader_diag/roll_abs_mean", float(np.abs(own[:, 7]).mean()))
                    self.logger.record("leader_diag/pitch_abs_mean", float(np.abs(own[:, 8]).mean()))
                    self.logger.record("leader_diag/gear_mean", float(own[:, 11].mean()))
            except Exception:
                pass

        if isinstance(obs, dict) and "terminal" in obs:
            try:
                terminal = np.asarray(obs["terminal"], dtype=np.float32)
                if terminal.ndim == 1:
                    terminal = terminal.reshape(1, -1)
                if terminal.ndim == 2 and terminal.shape[1] >= 8:
                    self.logger.record("leader_diag/dme_mean_m", float(terminal[:, 0].mean()))
                    self.logger.record("leader_diag/loc_abs_mean", float(np.abs(terminal[:, 1]).mean()))
                    self.logger.record("leader_diag/gs_abs_mean", float(np.abs(terminal[:, 2]).mean()))
                    self.logger.record("leader_diag/runway_cross_abs_mean_m", float(np.abs(terminal[:, 4]).mean()))
                    self.logger.record("leader_diag/runway_heading_abs_mean_deg", float(np.abs(terminal[:, 5]).mean()))
                    self.logger.record("leader_diag/approach_phase_frac", float((terminal[:, 6] > 0.5).mean()))
                    self.logger.record("leader_diag/landing_cmd_frac", float((terminal[:, 7] > 0.5).mean()))
            except Exception:
                pass

        if not infos:
            return

        mean_guarded = self._mean_info_values(infos, "leader_phase_guarded")
        if mean_guarded is not None:
            self.logger.record("leader_diag/phase_guarded_frac", float(mean_guarded))
        mean_bias_guarded = self._mean_info_values(infos, "leader_bias_guarded")
        if mean_bias_guarded is not None:
            self.logger.record("leader_diag/bias_guarded_frac", float(mean_bias_guarded))
        mean_terminal_feasible = self._mean_info_values(infos, "leader_terminal_feasible")
        if mean_terminal_feasible is not None:
            self.logger.record("leader_diag/terminal_feasible_frac", float(mean_terminal_feasible))

        mode_counts: dict[str, int] = defaultdict(int)
        req_counts: dict[str, int] = defaultdict(int)
        reason_counts: dict[str, int] = defaultdict(int)
        bias_reason_counts: dict[str, int] = defaultdict(int)
        c2_task_counts: dict[str, int] = defaultdict(int)
        c2_transition_reason_counts: dict[str, int] = defaultdict(int)
        cmd_deltas = []
        for info in infos:
            if not isinstance(info, dict):
                continue
            mode = info.get("leader_phase_bucket")
            if isinstance(mode, str) and mode.strip():
                mode_counts[self._normalize_reason(mode)] += 1
            req = info.get("leader_requested_phase_bucket")
            if isinstance(req, str) and req.strip():
                req_counts[self._normalize_reason(req)] += 1
            reason = info.get("leader_phase_guard_reason")
            if isinstance(reason, str) and reason.strip():
                reason_counts[self._normalize_reason(reason)] += 1
            bias_reason = info.get("leader_bias_guard_reason")
            if isinstance(bias_reason, str) and bias_reason.strip():
                bias_reason_counts[self._normalize_reason(bias_reason)] += 1
            c2_task = info.get("leader_c2_task_name")
            if isinstance(c2_task, str) and c2_task.strip():
                c2_task_counts[self._normalize_reason(c2_task)] += 1
            c2_reason = info.get("leader_c2_transition_reason")
            if isinstance(c2_reason, str) and c2_reason.strip():
                c2_transition_reason_counts[self._normalize_reason(c2_reason)] += 1
            eff = info.get("leader_effective_command")
            base = info.get("leader_baseline_command")
            try:
                if eff is not None and base is not None:
                    eff_arr = np.asarray(eff, dtype=np.float32).reshape(-1)
                    base_arr = np.asarray(base, dtype=np.float32).reshape(-1)
                    if eff_arr.size >= 4 and base_arr.size >= 4:
                        cmd_deltas.append(
                            abs(float(eff_arr[0]) - float(base_arr[0]))
                            + abs(float(eff_arr[1]) - float(base_arr[1])) / 180.0
                            + abs(float(eff_arr[2]) - float(base_arr[2])) / max(1.0, abs(float(base_arr[2])) + 1.0)
                            + abs(float(eff_arr[3]) - float(base_arr[3])) / max(1.0, abs(float(base_arr[3])) + 1.0)
                        )
            except Exception:
                continue

        total = float(max(1, len(infos)))
        for mode, count in sorted(mode_counts.items()):
            self.logger.record(f"leader_diag/phase_frac_{mode}", float(count) / total)
        for req, count in sorted(req_counts.items()):
            self.logger.record(f"leader_diag/request_frac_{req}", float(count) / total)
        for reason, count in sorted(reason_counts.items()):
            self.logger.record(f"leader_diag/guard_reason_frac_{reason}", float(count) / total)
        for reason, count in sorted(bias_reason_counts.items()):
            self.logger.record(f"leader_diag/bias_guard_reason_frac_{reason}", float(count) / total)
        for task_name, count in sorted(c2_task_counts.items()):
            self.logger.record(f"leader_diag/c2_task_frac_{task_name}", float(count) / total)
        for reason, count in sorted(c2_transition_reason_counts.items()):
            self.logger.record(f"leader_diag/c2_transition_reason_frac_{reason}", float(count) / total)
        if cmd_deltas:
            self.logger.record(
                "leader_diag/cmd_vs_baseline_delta_mean",
                float(np.mean(np.asarray(cmd_deltas, dtype=np.float32))),
            )
        report_valid = self._mean_info_values(infos, "leader_report_valid")
        if report_valid is not None:
            self.logger.record("leader_diag/report_valid_frac", float(report_valid))
        c2_transitioned = self._mean_info_values(infos, "leader_c2_transitioned")
        if c2_transitioned is not None:
            self.logger.record("leader_diag/c2_transition_frac", float(c2_transitioned))

        for key in self.LEADER_REWARD_KEYS:
            mean_val = self._mean_reward_term_values(infos, "leader_reward_terms", key)
            if mean_val is not None:
                self.logger.record(f"leader_diag/reward_{key}", float(mean_val))

    def _on_step(self) -> bool:
        obs = self.locals.get("new_obs")
        actions = self.locals.get("clipped_actions", self.locals.get("actions"))
        rewards = self.locals.get("rewards")
        infos = self.locals.get("infos")
        dones = self.locals.get("dones")

        inst_arr = None
        if isinstance(obs, dict) and "instruments" in obs:
            try:
                inst_arr = np.asarray(obs["instruments"], dtype=np.float32)
                if inst_arr.ndim == 1:
                    inst_arr = inst_arr.reshape(1, -1)
            except Exception:
                inst_arr = None

        action_arr = None
        if actions is not None:
            try:
                action_arr = np.asarray(actions, dtype=np.float32)
                if action_arr.ndim == 1:
                    action_arr = action_arr.reshape(1, -1)
            except Exception:
                action_arr = None

        effective_action_arr = None
        if isinstance(infos, (list, tuple)) and infos:
            eff_rows = []
            for info in infos:
                if not isinstance(info, dict) or "effective_action" not in info:
                    eff_rows = []
                    break
                try:
                    eff_rows.append(np.asarray(info["effective_action"], dtype=np.float32).reshape(-1))
                except Exception:
                    eff_rows = []
                    break
            if eff_rows:
                try:
                    effective_action_arr = np.stack(eff_rows, axis=0)
                except Exception:
                    effective_action_arr = None

        reward_arr = None
        if rewards is not None:
            try:
                reward_arr = np.asarray(rewards, dtype=np.float32).reshape(-1)
            except Exception:
                reward_arr = None

        done_arr = None
        if dones is not None:
            try:
                done_arr = np.asarray(dones, dtype=bool).reshape(-1)
            except Exception:
                done_arr = None

        if not isinstance(infos, (list, tuple)):
            infos = []

        n_envs = len(self._histories)
        for i in range(n_envs):
            done_i = bool(done_arr[i]) if (done_arr is not None and i < done_arr.shape[0]) else False
            info_i = infos[i] if i < len(infos) and isinstance(infos[i], dict) else {}
            if effective_action_arr is not None and i < effective_action_arr.shape[0]:
                act_i = effective_action_arr[i]
            else:
                act_i = action_arr[i] if (action_arr is not None and i < action_arr.shape[0]) else None
            rew_i = float(reward_arr[i]) if (reward_arr is not None and i < reward_arr.shape[0]) else None

            if done_i:
                inst_term = self._extract_terminal_inst(info_i)
                if inst_term is None:
                    inst_term = inst_arr[i] if (inst_arr is not None and i < inst_arr.shape[0]) else None
                snap = self._make_snapshot(inst_term, act_i, rew_i)
                if snap is not None:
                    self._histories[i].append(snap)

                reason = self._infer_termination_reason(info_i)
                self._episodes_window += 1
                self._term_counts_window[reason] += 1
                self._term_counts_total[reason] += 1
                self._record_terminal_reward_terms(info_i)
                self._record_cooperative_episode(info_i, reason)
                if self._is_failure_reason(reason):
                    self._failure_window += 1
                    self._record_preterm_window(self._histories[i])
                self._histories[i].clear()
            else:
                inst_i = inst_arr[i] if (inst_arr is not None and i < inst_arr.shape[0]) else None
                snap = self._make_snapshot(inst_i, act_i, rew_i)
                if snap is not None:
                    self._histories[i].append(snap)

        if self.log_every_timesteps <= 0:
            return True
        if self.num_timesteps < self._next_log_t:
            return True
        self._next_log_t = int(self.num_timesteps) + int(self.log_every_timesteps)

        if rewards is not None:
            r_mean = _safe_mean(rewards)
            if r_mean is not None:
                self.logger.record("diag/reward_mean", r_mean)

        if isinstance(obs, dict) and "instruments" in obs:
            inst = np.asarray(obs["instruments"], dtype=np.float32)
            if inst.ndim == 2 and inst.shape[1] >= 10:
                self.logger.record("diag/ias_mean", float(inst[:, 0].mean()))
                self.logger.record("diag/alt_baro_mean", float(inst[:, 2].mean()))
                self.logger.record("diag/aoa_mean", float(inst[:, 5].mean()))
                self.logger.record("diag/pitch_mean", float(inst[:, 7].mean()))
                self.logger.record("diag/roll_mean", float(inst[:, 8].mean()))

                if inst.shape[1] >= 42:
                    ils = inst[:, -4:]
                    self.logger.record("diag/ils_valid_frac", float((ils[:, 0] > 0.5).mean()))
                    self.logger.record("diag/ils_loc_abs_mean", float(np.abs(ils[:, 1]).mean()))

        actions_for_log = effective_action_arr if effective_action_arr is not None else action_arr
        if actions_for_log is not None:
            a = np.asarray(actions_for_log, dtype=np.float32)
            if a.ndim == 2 and a.shape[1] >= 4:
                self.logger.record("diag/action_pitch_mean", float(a[:, 0].mean()))
                self.logger.record("diag/action_roll_mean", float(a[:, 1].mean()))
                self.logger.record("diag/action_rudder_mean", float(a[:, 2].mean()))
                self.logger.record("diag/action_throttle_mean", float(a[:, 3].mean()))
            if a.ndim == 2 and a.shape[1] >= 9:
                self.logger.record("diag/action_brake_any_frac", float((np.maximum(a[:, 7], a[:, 8]) > 0.5).mean()))
                brake_raw = np.maximum(a[:, 7], a[:, 8])
                brake_amt = np.clip((brake_raw - 0.5) * 2.0, 0.0, 1.0)
                self.logger.record("diag/action_brake_amt_mean", float(brake_amt.mean()))
            if a.ndim == 2 and a.shape[1] >= 17:
                self.logger.record("diag/action_radar_active_frac", float((a[:, 9] > 0.5).mean()))
                self.logger.record("diag/action_master_arm_frac", float((a[:, 13] > 0.5).mean()))
                self.logger.record("diag/action_fire_weapon_frac", float((a[:, 14] > 0.5).mean()))
                self.logger.record("diag/action_fire_gun_frac", float((a[:, 15] > 0.5).mean()))
                weapon_select_id = np.floor(np.clip(a[:, 16], 0.0, 1.0) * 7.0)
                self.logger.record("diag/action_weapon_select_id_mean", float(weapon_select_id.mean()))

        if isinstance(infos, (list, tuple)) and infos:
            reward_keys = [
                "total",
                "survival",
                "crash_penalty",
                "stall_penalty",
                "overload_penalty",
                "failfast_penalty",
                "off_runway_penalty",
                "off_runway_terminate_penalty",
                "gear_collapse_penalty",
                "altitude_progress",
                "speed_progress",
                "speed_regress",
                "heading_error_penalty",
                "heading_hold_bonus",
                "altitude_error_penalty",
                "speed_error_penalty",
                "roll_abs_penalty",
                "pitch_abs_penalty",
                "yaw_rate_abs_penalty",
                "beta_abs_penalty",
                "g_deviation_penalty",
                "alignment_reward",
                "waypoint_progress",
                "waypoint_distance",
                "waypoint_reached_bonus",
                "waypoint_success_bonus",
                "objective_bonus",
                "combat_win_bonus",
                "combat_loss_penalty",
                "combat_draw_reward",
                "untracked",
            ]
            for key in reward_keys:
                vals = []
                for info in infos:
                    if not isinstance(info, dict):
                        continue
                    rt = info.get("reward_terms")
                    if isinstance(rt, dict) and key in rt:
                        try:
                            vals.append(float(rt[key]))
                        except Exception:
                            pass
                if vals:
                    self.logger.record(f"diag/rew_{key}", float(np.asarray(vals, dtype=np.float32).mean()))

            on_runway = [info.get("on_runway") for info in infos if isinstance(info, dict) and "on_runway" in info]
            if on_runway:
                self.logger.record("diag/on_runway_frac", float(np.asarray(on_runway, dtype=np.float32).mean()))

            on_runway_geom = [
                info.get("on_runway_geom") for info in infos if isinstance(info, dict) and "on_runway_geom" in info
            ]
            if on_runway_geom:
                self.logger.record(
                    "diag/on_runway_geom_frac", float(np.asarray(on_runway_geom, dtype=np.float32).mean())
                )

            runway_cross = [
                info.get("runway_cross_m") for info in infos if isinstance(info, dict) and "runway_cross_m" in info
            ]
            if runway_cross:
                rc = np.asarray(runway_cross, dtype=np.float32)
                self.logger.record("diag/runway_cross_abs_mean_m", float(np.abs(rc).mean()))
                abs_rc = np.abs(rc)
                # Robust tail metrics help catch "edge-hugging" even when mean looks OK.
                try:
                    self.logger.record("diag/runway_cross_abs_p95_m", float(np.percentile(abs_rc, 95.0)))
                except Exception:
                    pass
                self.logger.record("diag/runway_cross_abs_max_m", float(abs_rc.max(initial=0.0)))

            gear_collapsed = [
                info.get("gear_collapsed") for info in infos if isinstance(info, dict) and "gear_collapsed" in info
            ]
            if gear_collapsed:
                self.logger.record("diag/gear_collapsed_frac", float(np.asarray(gear_collapsed, dtype=np.float32).mean()))

            gear_stress = [info.get("gear_stress") for info in infos if isinstance(info, dict) and "gear_stress" in info]
            if gear_stress:
                self.logger.record("diag/gear_stress_mean", float(np.asarray(gear_stress, dtype=np.float32).mean()))

            self._record_leader_diagnostics(obs, list(infos))

        policy = getattr(self.model, "policy", None)
        get_route_stats = getattr(policy, "get_hmoe_route_stats", None)
        if callable(get_route_stats):
            try:
                route_stats = get_route_stats()
            except Exception:
                route_stats = None
            if isinstance(route_stats, dict):
                for key, value in route_stats.items():
                    try:
                        self.logger.record(str(key), float(value))
                    except Exception:
                        continue
        get_param_stats = getattr(policy, "get_hmoe_parameter_stats", None)
        if callable(get_param_stats) and int(self.num_timesteps) >= int(self._hmoe_param_stats_next_log_t):
            try:
                param_stats = get_param_stats()
            except Exception:
                param_stats = None
            if isinstance(param_stats, dict):
                for key, value in param_stats.items():
                    try:
                        self.logger.record(str(key), float(value))
                    except Exception:
                        continue
            self._hmoe_param_stats_next_log_t = int(self.num_timesteps) + int(self.log_every_timesteps)

        self._record_event_diagnostics()
        return True


class ScenarioCurriculumCallback(BaseCallback):
    """
    Time-based curriculum for scenario randomization.

    Applies `ScenarioLoader.set_randomization_overrides()` (via `env_method`) according to staged schedule:
      stages = [{"until_timesteps": 200000, "randomization": {...}, "leader_env_overrides": {...}}, {..., "until_timesteps": null, ...}]
    """

    def __init__(self, stages: list[dict[str, Any]], check_freq: int = 10_000, verbose: int = 0):
        super().__init__(verbose=verbose)
        if not isinstance(stages, list) or not stages:
            raise ValueError("ScenarioCurriculumCallback requires a non-empty `stages` list")
        self.stages = stages
        self.check_freq = int(check_freq)
        self._next_check = 0
        self._active_stage_idx: int | None = None

    def _select_stage(self, t: int) -> int:
        for idx, st in enumerate(self.stages):
            until = st.get("until_timesteps", None)
            if until is None:
                return idx
            if t < int(until):
                return idx
        return len(self.stages) - 1

    def _apply_stage(self, idx: int) -> None:
        st = self.stages[idx]
        overrides = st.get("randomization_overrides", st.get("randomization", {}))
        if overrides is None:
            overrides = {}
        if not isinstance(overrides, dict):
            raise TypeError(f"curriculum stage randomization overrides must be a dict, got {type(overrides)}")

        # Broadcast to all parallel envs (works for DummyVecEnv/SubprocVecEnv).
        try:
            self.training_env.env_method("set_randomization_overrides", overrides)  # type: ignore[union-attr]
        except Exception as e:
            if self.verbose > 0:
                print(f"[WARN] curriculum stage {idx} apply failed: {e}")

        leader_overrides = st.get("leader_env_overrides", {})
        if leader_overrides is None:
            leader_overrides = {}
        if not isinstance(leader_overrides, dict):
            raise TypeError(
                f"curriculum stage leader_env_overrides must be a dict, got {type(leader_overrides)}"
            )
        if leader_overrides:
            try:
                self.training_env.env_method("set_leader_overrides", leader_overrides)  # type: ignore[union-attr]
            except Exception as e:
                if self.verbose > 0:
                    print(f"[WARN] curriculum leader stage {idx} apply failed: {e}")

        self._active_stage_idx = int(idx)
        self.logger.record("curriculum/stage", int(idx))

    def _on_training_start(self) -> None:
        self._next_check = 0
        self._active_stage_idx = None
        self._apply_stage(self._select_stage(int(self.num_timesteps)))

    def _on_step(self) -> bool:
        if self.check_freq <= 0:
            return True
        if self.num_timesteps < self._next_check:
            return True
        self._next_check = int(self.num_timesteps) + int(self.check_freq)

        idx = self._select_stage(int(self.num_timesteps))
        if self._active_stage_idx != idx:
            self._apply_stage(idx)
        return True


class RewardPlateauEarlyStopCallback(BaseCallback):
    """
    Stop training when episode-reward EMA no longer improves.

    This remains lightweight and does not require a separate eval env, but it should
    track the same scale as SB3's `rollout/ep_rew_mean` rather than instantaneous
    step rewards.
    """

    def __init__(
        self,
        min_timesteps: int = 200_000,
        check_every_timesteps: int = 20_000,
        patience_checks: int = 6,
        min_improvement: float = 0.5,
        ema_alpha: float = 0.05,
        best_model_path: str | None = None,
        verbose: int = 0,
    ):
        super().__init__(verbose=verbose)
        self.min_timesteps = int(min_timesteps)
        self.check_every_timesteps = int(check_every_timesteps)
        self.patience_checks = int(patience_checks)
        self.min_improvement = float(min_improvement)
        self.ema_alpha = float(ema_alpha)
        self.best_model_path = best_model_path

        self._next_check = 0
        self._ema_reward = None
        self._best_ema = None
        self._stale_checks = 0
        self._best_saved = False

    def _save_best_model(self) -> None:
        if not self.best_model_path:
            return
        try:
            d = os.path.dirname(self.best_model_path)
            if d:
                os.makedirs(d, exist_ok=True)
            self.model.save(self.best_model_path)
            self._best_saved = True
        except Exception:
            pass

    def _on_training_start(self) -> None:
        self._next_check = int(self.check_every_timesteps)
        self._ema_reward = None
        self._best_ema = None
        self._stale_checks = 0
        self._best_saved = False

    def _current_reward_metric(self):
        ep_buf = getattr(self.model, "ep_info_buffer", None)
        if ep_buf:
            vals = []
            for ep in ep_buf:
                if not isinstance(ep, dict):
                    continue
                try:
                    vals.append(float(ep.get("r")))
                except Exception:
                    continue
            if vals:
                return float(np.mean(np.asarray(vals, dtype=np.float32)))

        rewards = self.locals.get("rewards")
        if rewards is not None:
            r_mean = _safe_mean(rewards)
            if r_mean is not None:
                return float(r_mean)
        return None

    def _on_step(self) -> bool:
        if self.num_timesteps < self._next_check:
            return True
        self._next_check = int(self.num_timesteps) + int(self.check_every_timesteps)

        metric = self._current_reward_metric()
        if metric is None:
            return True
        self.logger.record("early_stop/reward_metric", float(metric))

        if self._ema_reward is None:
            self._ema_reward = float(metric)
        else:
            a = self.ema_alpha
            self._ema_reward = float((1.0 - a) * self._ema_reward + a * float(metric))

        self.logger.record("early_stop/ema_reward", float(self._ema_reward))

        if self.num_timesteps < self.min_timesteps:
            if self._best_ema is None or self._ema_reward > self._best_ema:
                self._best_ema = float(self._ema_reward)
                self._save_best_model()
            return True

        if self._best_ema is None:
            self._best_ema = float(self._ema_reward)
            self._save_best_model()
            return True

        improvement = float(self._ema_reward - self._best_ema)
        self.logger.record("early_stop/improvement", improvement)
        self.logger.record("early_stop/stale_checks", int(self._stale_checks))

        if improvement > self.min_improvement:
            self._best_ema = float(self._ema_reward)
            self._stale_checks = 0
            self._save_best_model()
            return True

        self._stale_checks += 1
        if self._stale_checks >= self.patience_checks:
            if self.verbose > 0:
                print(
                    "[EARLY STOP] reward EMA plateau detected: "
                    f"ema={self._ema_reward:.3f}, best={self._best_ema:.3f}, "
                    f"checks={self._stale_checks}/{self.patience_checks}"
                )
            return False

        return True
