"""RL-independent scripted Air C2 manager.

This module owns C2 state, observation assessment, and transition orchestration.
Compiled report values and task-order DTO mutation are injected through ports;
no RL package, Gym environment, or native binding is imported here.
"""

from __future__ import annotations

from typing import Any

from python.angles import wrap_signed_deg
from python.tasking_contracts.common.bridge_views import (
    get_policy_agent_observation,
    get_policy_instrument_state,
)
from python.tasking_contracts.common.mission_defs import (
    COMMAND_CODE_LANDING,
    is_landing_command_code,
)
from python.tasking_contracts.air.tasking.c2_observation import (
    C2RecoveryReadinessInput,
    C2ReportTypeCodes,
    C2StationMetrics,
    assess_c2_report,
    compute_station_metrics,
    recovery_window_ready,
)
from python.tasking_contracts.air.tasking.c2_policy import (
    C2TransitionInput,
    C2TransitionPolicy,
    ScriptedC2TransitionPolicy,
)
from python.tasking_contracts.air.tasking.task_order_projection import C2TaskOrderProjection


class ScriptedC2TaskManager:
    """
    Scripted C2 task-state manager.

    The C2 layer is allowed to consume:
    - shared situation data (ownship state / recovery geometry / fuel)
    - leader pilot reports

    It is *not* allowed to directly author low-level mission commands. Those remain the
    responsibility of the leader layer.
    """

    TASK_IDLE = "TASK_IDLE"
    TASK_SCRAMBLE = "TASK_SCRAMBLE"
    TASK_CAP = "TASK_CAP"
    TASK_RTB = "TASK_RTB"
    TASK_RECOVER_LAND = "TASK_RECOVER_LAND"

    def __init__(
        self,
        *,
        scramble_complete_alt_agl_m: float = 120.0,
        scramble_complete_ground_speed_mps: float = 65.0,
        station_entry_radius_scale: float = 1.25,
        station_entry_altitude_slack_m: float = 250.0,
        station_entry_speed_slack_mps: float = 20.0,
        auto_rtb_on_station_complete: bool = True,
        recover_arm_dme_m: float = 18000.0,
        recover_arm_alt_agl_max_m: float = 1800.0,
        recover_arm_loc_abs_max: float = 0.8,
        recover_arm_gs_abs_max: float = 1.5,
        recover_arm_require_runway_frame: bool = True,
        recover_arm_along_min_m: float = -1000.0,
        recover_arm_cross_abs_max_m: float = 3500.0,
        recover_arm_heading_abs_max_deg: float = 85.0,
        transition_policy: C2TransitionPolicy | None = None,
        report_type_codes: C2ReportTypeCodes | None = None,
        task_order_projection: C2TaskOrderProjection | None = None,
    ):
        self.scramble_complete_alt_agl_m = float(scramble_complete_alt_agl_m)
        self.scramble_complete_ground_speed_mps = float(scramble_complete_ground_speed_mps)
        self.station_entry_radius_scale = float(station_entry_radius_scale)
        self.station_entry_altitude_slack_m = float(station_entry_altitude_slack_m)
        self.station_entry_speed_slack_mps = float(station_entry_speed_slack_mps)
        self.auto_rtb_on_station_complete = bool(auto_rtb_on_station_complete)
        self.recover_arm_dme_m = float(recover_arm_dme_m)
        self.recover_arm_alt_agl_max_m = float(recover_arm_alt_agl_max_m)
        self.recover_arm_loc_abs_max = float(recover_arm_loc_abs_max)
        self.recover_arm_gs_abs_max = float(recover_arm_gs_abs_max)
        self.recover_arm_require_runway_frame = bool(recover_arm_require_runway_frame)
        self.recover_arm_along_min_m = float(recover_arm_along_min_m)
        self.recover_arm_cross_abs_max_m = float(recover_arm_cross_abs_max_m)
        self.recover_arm_heading_abs_max_deg = float(recover_arm_heading_abs_max_deg)
        self.transition_policy = transition_policy or ScriptedC2TransitionPolicy()
        if not isinstance(self.transition_policy, C2TransitionPolicy):
            raise TypeError("transition_policy must implement C2TransitionPolicy")
        if not isinstance(report_type_codes, C2ReportTypeCodes):
            raise TypeError("report_type_codes must implement C2ReportTypeCodes")
        if not isinstance(task_order_projection, C2TaskOrderProjection):
            raise TypeError("task_order_projection must implement C2TaskOrderProjection")
        self.report_type_codes = report_type_codes
        self.task_order_projection = task_order_projection
        self.current_task_name = self.TASK_SCRAMBLE
        self.station_entry_time_s: float | None = None

    @staticmethod
    def task_name_to_id(task_name: str | None) -> int:
        mapping = {
            ScriptedC2TaskManager.TASK_IDLE: 0,
            ScriptedC2TaskManager.TASK_SCRAMBLE: 1,
            ScriptedC2TaskManager.TASK_CAP: 2,
            ScriptedC2TaskManager.TASK_RTB: 3,
            ScriptedC2TaskManager.TASK_RECOVER_LAND: 4,
        }
        return int(mapping.get(str(task_name or "").strip().upper(), 0))

    def _apply_loader_state(
        self,
        loader: Any,
        *,
        task_name: str,
        sim_time_s: float,
        transitioned: bool,
        transition_reason: str,
        report_valid: bool,
        report_reason: str,
    ) -> dict[str, Any]:
        loader.c2_task_name = str(task_name)
        loader.c2_task_id = int(self.task_name_to_id(task_name))
        loader.c2_transitioned = bool(transitioned)
        loader.c2_transition_reason = str(transition_reason)
        loader.c2_last_update_s = float(sim_time_s)
        loader.c2_report_valid = bool(report_valid)
        loader.c2_report_reason = str(report_reason)
        if self.station_entry_time_s is None:
            loader.c2_on_station_elapsed_s = 0.0
        else:
            loader.c2_on_station_elapsed_s = max(0.0, float(sim_time_s) - float(self.station_entry_time_s))
        return {
            "task_name": str(task_name),
            "task_id": int(self.task_name_to_id(task_name)),
            "transitioned": bool(transitioned),
            "transition_reason": str(transition_reason),
            "report_valid": bool(report_valid),
            "report_reason": str(report_reason),
            "on_station_elapsed_s": float(getattr(loader, "c2_on_station_elapsed_s", 0.0)),
        }

    def reset(self, loader: Any, sim_time_s: float = 0.0, *, truth: Any = None, inst: Any = None, sync_to_kernel: bool = True) -> dict[str, Any]:
        _ = (truth, inst, sync_to_kernel)
        scenario_data = getattr(loader, "scenario_data", {}) or {}
        meta = scenario_data.get("meta", {}) if isinstance(scenario_data, dict) else {}
        init_task = meta.get("initial_c2_task", self.TASK_SCRAMBLE) if isinstance(meta, dict) else self.TASK_SCRAMBLE
        self.current_task_name = str(init_task or self.TASK_SCRAMBLE).strip().upper()
        self.station_entry_time_s = None
        self.task_order_projection.retask_order(
            loader,
            task_name=self.current_task_name,
            sim_time_s=float(sim_time_s),
        )
        return self._apply_loader_state(
            loader,
            task_name=self.current_task_name,
            sim_time_s=float(sim_time_s),
            transitioned=False,
            transition_reason="reset",
            report_valid=False,
            report_reason="",
        )

    def _task_cfg(self, loader: Any) -> dict[str, Any]:
        scenario_data = getattr(loader, "scenario_data", {}) or {}
        cfg = scenario_data.get("c2_logic", {}) if isinstance(scenario_data, dict) else {}
        return cfg if isinstance(cfg, dict) else {}

    @staticmethod
    def _landing_post_transition_pending(loader: Any) -> bool:
        post = getattr(loader, "post_waypoint_transition", None)
        if not isinstance(post, dict) or not post:
            return False
        return bool(is_landing_command_code(post.get("command_code", COMMAND_CODE_LANDING)))

    def _route_exhausted_for_recovery(self, loader: Any) -> bool:
        if not self._landing_post_transition_pending(loader):
            return False
        waypoints = list(getattr(loader, "waypoints", []) or [])
        if not waypoints:
            return False
        waypoint_idx = int(getattr(loader, "waypoint_idx", 0) or 0)
        return waypoint_idx >= len(waypoints)

    def _fuel_margin_frac(self, loader: Any, *, inst: Any = None) -> tuple[float, float]:
        if inst is None:
            inst = get_policy_instrument_state(loader)
        fuel_total_kg = (
            float(max(0.0, getattr(inst, "fuel_internal", 0.0) + getattr(inst, "fuel_external", 0.0)))
            if inst is not None
            else 0.0
        )
        task = getattr(loader, "task_order", None)
        bingo_kg = float(max(0.0, getattr(task, "fuel_bingo_override_kg", 0.0) if task is not None else 0.0))
        if bingo_kg <= 1.0:
            return fuel_total_kg, 1.0
        return fuel_total_kg, float((fuel_total_kg - bingo_kg) / max(bingo_kg, 1.0))

    def _station_metrics(self, loader: Any, *, truth: Any = None, inst: Any = None) -> dict[str, float | bool]:
        task = getattr(loader, "task_order", None)
        if truth is None:
            truth = get_policy_agent_observation(loader)
        if inst is None:
            inst = get_policy_instrument_state(loader)
        metrics = compute_station_metrics(
            truth=truth,
            inst=inst,
            task=task,
            radius_scale=self.station_entry_radius_scale,
            altitude_slack_m=self.station_entry_altitude_slack_m,
            speed_slack_mps=self.station_entry_speed_slack_mps,
        )
        return {
            "near_station": bool(metrics.near_station),
            "anchor_dist_m": float(metrics.anchor_dist_m),
        }

    def _recovery_ready(self, loader: Any, *, truth: Any = None, inst: Any = None) -> bool:
        if truth is None:
            truth = get_policy_agent_observation(loader)
        if inst is None:
            inst = get_policy_instrument_state(loader)
        if truth is None or inst is None:
            return False
        try:
            ils = loader.get_ils_observation(
                float(getattr(truth, "x", 0.0)),
                float(getattr(truth, "y", 0.0)),
                float(getattr(inst, "alt_baro", 0.0)),
            )
        except Exception:
            return False
        ils_valid = float(ils[0]) > 0.5 if len(ils) >= 1 else False
        loc_abs = abs(float(ils[1])) if len(ils) >= 2 else float("inf")
        gs_abs = abs(float(ils[2])) if len(ils) >= 3 else float("inf")
        dme_m = float(ils[3]) if len(ils) >= 4 else float("inf")
        alt_agl_m = float(getattr(inst, "alt_radar", 0.0))
        cfg = self._task_cfg(loader)

        recover_arm_dme_m = float(cfg.get("recover_arm_dme_m", self.recover_arm_dme_m))
        recover_arm_alt_agl_max_m = float(cfg.get("recover_arm_alt_agl_max_m", self.recover_arm_alt_agl_max_m))
        recover_arm_loc_abs_max = float(cfg.get("recover_arm_loc_abs_max", self.recover_arm_loc_abs_max))
        recover_arm_gs_abs_max = float(cfg.get("recover_arm_gs_abs_max", self.recover_arm_gs_abs_max))
        recover_arm_require_runway_frame = bool(
            cfg.get("recover_arm_require_runway_frame", self.recover_arm_require_runway_frame)
        )
        recover_arm_along_min_m = float(cfg.get("recover_arm_along_min_m", self.recover_arm_along_min_m))
        recover_arm_cross_abs_max_m = float(cfg.get("recover_arm_cross_abs_max_m", self.recover_arm_cross_abs_max_m))
        recover_arm_heading_abs_max_deg = float(
            cfg.get("recover_arm_heading_abs_max_deg", self.recover_arm_heading_abs_max_deg)
        )

        valid_runway_frame = False
        along_m = 0.0
        cross_m = 0.0
        try:
            valid_runway_frame, along_m, cross_m, _rw_len, _rw_wid = loader.get_runway_local_frame(
                float(getattr(truth, "x", 0.0)),
                float(getattr(truth, "y", 0.0)),
            )
        except Exception:
            valid_runway_frame = False

        if recover_arm_require_runway_frame and not bool(valid_runway_frame):
            return False
        if bool(valid_runway_frame):
            if float(along_m) < recover_arm_along_min_m:
                return False
            if abs(float(cross_m)) > recover_arm_cross_abs_max_m:
                return False

        try:
            beacon = loader._nearest_ils_beacon(float(getattr(truth, "x", 0.0)), float(getattr(truth, "y", 0.0)))
        except Exception:
            beacon = None
        if beacon is None:
            return False
        runway_heading_err_deg = abs(
            wrap_signed_deg(float(getattr(inst, "heading", 0.0)) - float(beacon.get("heading", 0.0)))
        )
        return recovery_window_ready(
            C2RecoveryReadinessInput(
                ils_valid=bool(ils_valid),
                localizer_abs=float(loc_abs),
                glide_slope_abs=float(gs_abs),
                dme_m=float(dme_m),
                altitude_agl_m=float(alt_agl_m),
                runway_frame_valid=bool(valid_runway_frame),
                runway_along_m=float(along_m),
                runway_cross_m=float(cross_m),
                runway_heading_error_deg=float(runway_heading_err_deg),
                max_dme_m=float(recover_arm_dme_m),
                max_altitude_agl_m=float(recover_arm_alt_agl_max_m),
                max_localizer_abs=float(recover_arm_loc_abs_max),
                max_glide_slope_abs=float(recover_arm_gs_abs_max),
                require_runway_frame=bool(recover_arm_require_runway_frame),
                min_runway_along_m=float(recover_arm_along_min_m),
                max_runway_cross_abs_m=float(recover_arm_cross_abs_max_m),
                max_runway_heading_error_deg=float(recover_arm_heading_abs_max_deg),
            )
        )

    def _report_assessment(self, loader: Any, *, truth: Any = None, inst: Any = None) -> tuple[bool, str]:
        report = getattr(loader, "pilot_report", None)
        if report is None or not bool(getattr(report, "active", False)):
            return False, "no_report"
        report_codes = self.report_type_codes
        report_type = int(getattr(report, "report_type", report_codes.none))
        metrics = C2StationMetrics(False, float("inf"), False, False)
        if report_type == report_codes.on_station:
            if truth is None:
                truth = get_policy_agent_observation(loader)
            if inst is None:
                inst = get_policy_instrument_state(loader)
            metrics = compute_station_metrics(
                truth=truth,
                inst=inst,
                task=getattr(loader, "task_order", None),
                radius_scale=self.station_entry_radius_scale,
                altitude_slack_m=self.station_entry_altitude_slack_m,
                speed_slack_mps=self.station_entry_speed_slack_mps,
            )
        fuel_margin = 0.0
        if report_type == report_codes.bingo:
            _fuel_total_kg, fuel_margin = self._fuel_margin_frac(loader, inst=inst)
        assessment = assess_c2_report(
            report,
            report_codes=report_codes,
            station_metrics=metrics,
            fuel_margin_fraction=fuel_margin,
        )
        return bool(assessment.valid), str(assessment.reason)

    def update(self, loader: Any, sim_time_s: float = 0.0, *, truth: Any = None, inst: Any = None, sync_to_kernel: bool = True) -> dict[str, Any]:
        _ = sync_to_kernel
        cfg = self._task_cfg(loader)
        report_valid, report_reason = self._report_assessment(loader, truth=truth, inst=inst)
        report = getattr(loader, "pilot_report", None)
        report_type = (
            int(getattr(report, "report_type", self.report_type_codes.none))
            if report is not None
            else int(self.report_type_codes.none)
        )

        if inst is None:
            inst = get_policy_instrument_state(loader)
        alt_agl_m = float(getattr(inst, "alt_radar", 0.0)) if inst is not None else 0.0
        ground_speed_mps = float(getattr(inst, "ground_speed", 0.0)) if inst is not None else 0.0

        task = getattr(loader, "task_order", None)
        on_station_time_s = float(getattr(task, "on_station_time_s", 0.0) if task is not None else 0.0)
        current = str(self.current_task_name)
        metrics = self._station_metrics(loader, truth=truth, inst=inst)
        decision = self.transition_policy.decide(
            C2TransitionInput(
                current_task_name=current,
                sim_time_s=float(sim_time_s),
                altitude_agl_m=alt_agl_m,
                ground_speed_mps=ground_speed_mps,
                station_entry_time_s=self.station_entry_time_s,
                on_station_time_s=on_station_time_s,
                near_station=bool(metrics["near_station"]),
                report_type=report_type,
                report_valid=report_valid,
                report_reason=report_reason,
                rep_rtb_type=int(self.report_type_codes.rtb),
                warn_bingo_type=int(self.report_type_codes.bingo),
                rep_unable_type=int(self.report_type_codes.unable),
                route_exhausted=self._route_exhausted_for_recovery(loader),
                recovery_ready=self._recovery_ready(loader, truth=truth, inst=inst),
                scramble_complete_alt_agl_m=float(
                    cfg.get("scramble_complete_alt_agl_m", self.scramble_complete_alt_agl_m)
                ),
                scramble_complete_ground_speed_mps=float(
                    cfg.get("scramble_complete_ground_speed_mps", self.scramble_complete_ground_speed_mps)
                ),
                auto_rtb_on_station_complete=bool(
                    cfg.get("auto_rtb_on_station_complete", self.auto_rtb_on_station_complete)
                ),
            )
        )
        self.station_entry_time_s = decision.station_entry_time_s
        current = str(decision.task_name)

        self.current_task_name = str(current)
        self.task_order_projection.retask_order(
            loader,
            task_name=self.current_task_name,
            sim_time_s=float(sim_time_s),
        )
        return self._apply_loader_state(
            loader,
            task_name=self.current_task_name,
            sim_time_s=float(sim_time_s),
            transitioned=decision.transitioned,
            transition_reason=decision.reason or report_reason,
            report_valid=report_valid,
            report_reason=report_reason,
        )


__all__ = ["ScriptedC2TaskManager"]
