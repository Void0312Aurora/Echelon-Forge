"""Typed Experiment ownership of the cooperative flight-shaping config matrix.

This module is the declarative single source for the twelve run-config files
at the active-training root, ``examples/config/training/active/*.json``: the
cooperative flight lane (cruise formation, interval takeoff, the
takeoff-to-cruise bridge with its HMoE and fair-control counterparts, and the
closed-loop takeoff-cruise-landing line) plus the P4b cruise-to-landing
reopen lane that shares the same flight-shaping wrapper machinery. Every
checked-in file in that directory is a projection of one registered
:class:`~python.experiment.definition.Experiment`: a config base plus a
per-experiment delta, composed with the deterministic merge rules in
:mod:`python.experiment.composition` and serialized by
``tools/maintenance/experiment_matrix/generate.py --matrix cooperative_flight``.

Unlike the single-base air-combat matrix, this matrix registers two config
bases, because base+delta composition has no key-deletion semantics and the
two lanes disagree on which top-level keys exist at all:

- ``cooperative_flight_shaping_v1`` carries the nine ``cooperative_*``
  entries (dual-ship cooperative execution: ``agent_layer`` /
  ``cooperative_execution`` blocks, world-batch-free compiled runtime, the
  takeoff-then-stable-flight shaping wrapper).
- ``p4b_cruise_to_landing_v1`` carries the three ``p4b_*`` entries (the
  earlier single-policy cruise-to-landing bridge: no cooperative blocks, a
  visual extractor, and its own curriculum ramp).

Byte parity with the checked-in files is a hard invariant (the config paths
are pinned by docs and tests). It is enforced by
``tests/architecture/governance/test_cooperative_flight_matrix_freshness.py``;
edit a base or a delta here, then run the generator with
``--matrix cooperative_flight --write`` and ``--check``. Do not edit the
generated JSON files directly.

Formatting facts this module pins (observed, not invented):

- ``CANONICAL_TRAILING_KEYS`` reproduces the canonical key layout shared by
  both lanes (``wrappers``/``curriculum``/``hyperparameters`` close the
  document, ``device``/``policy_kwargs`` close the hyperparameters block,
  the ``scripted_blend/lock/rate`` trio closes the shaping wrapper, and
  ``use_checkpointing`` closes the extractor kwargs).
- Every cooperative entry spells the shaping wrapper's
  ``scripted_residual_alt_scales`` with trailing-zero decimals
  (``0.10 ... 0.30``) and the landing entries spell the ``landing_ils`` mode
  scale as ``0.20``; the two P4b reopen entries spell ``learning_rate`` as
  the plain decimal ``0.00003``. All are recorded per entry as
  :class:`RenderStyle` literal overrides so regeneration stays
  byte-identical.

Scenario pairings follow the directory README
(``examples/config/training/active/README.md``). Seed sets are empty because
no entry pins seeds today (training bootstrap owns the default); the single
``training_line`` evaluation protocol mirrors the README's status for the
whole directory ("current forward-moving training lines, not a frozen
acceptance set") per the registry-follows-usage rule.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from python.experiment.composition import compose_config, normalize_trailing_keys
from python.experiment.definition import (
    ConfigComposition,
    EvaluationProtocol,
    Experiment,
    ExperimentRegistry,
    ScenarioRef,
    SeedSpec,
)
from python.experiment.matrix_projection import MatrixEntryBase, RenderStyle

__all__ = [
    "CONFIG_BASES",
    "COOPERATIVE_CONFIG_BASE_ID",
    "MATRIX_DIR",
    "MATRIX_ENTRIES",
    "MatrixEntry",
    "P4B_CONFIG_BASE_ID",
    "REGISTRY",
    "build_registry",
    "composed_config",
]

MATRIX_DIR = "examples/config/training/active"
COOPERATIVE_CONFIG_BASE_ID = "cooperative_flight_shaping_v1"
P4B_CONFIG_BASE_ID = "p4b_cruise_to_landing_v1"

# Canonical serialization order: these keys close their mapping, in this
# order, regardless of where a delta introduced sibling keys. The map is
# shared by both bases; every declared key already closes its mapping in the
# P4b base order, so normalization is the identity there.
CANONICAL_TRAILING_KEYS: Mapping[tuple[str, ...], tuple[str, ...]] = MappingProxyType(
    {
        (): ("wrappers", "curriculum", "hyperparameters"),
        ("wrappers", "multi_timescale_action"): (
            "scripted_blend_indices",
            "scripted_lock_indices",
            "action_rate_penalty_coef",
        ),
        ("hyperparameters",): ("device", "policy_kwargs"),
        ("hyperparameters", "policy_kwargs"): ("log_std_init", "net_arch"),
        ("hyperparameters", "policy_kwargs", "features_extractor_kwargs"): (
            "use_checkpointing",
        ),
    }
)


@dataclass(frozen=True)
class MatrixEntry(MatrixEntryBase):
    """One registered active-root experiment plus its pinned output projection."""

    MATRIX_DIR = "examples/config/training/active"


# --- Scenario pairings (directory README) ----------------------------------

_SCENARIO_CRUISE_FORMATION = (
    "scenarios/cruise/cooperative_cruise_waypoints_paramroute_navv2_formation_train_v1.json"
)
_SCENARIO_INTERVAL_TAKEOFF = (
    "scenarios/takeoff/cooperative_interval_takeoff_departure_navv2_train_v1.json"
)
_SCENARIO_TAKEOFF_TO_CRUISE = (
    "scenarios/combined/cooperative_takeoff_to_cruise_paramroute_navv2_train_v1.json"
)
_SCENARIO_TAKEOFF_CRUISE_LANDING = (
    "scenarios/combined/cooperative_takeoff_to_cruise_landing_continuous_train_v1.json"
)
_SCENARIO_P4B_CRUISE_TO_LANDING = (
    "scenarios/combined/cruise_to_landing_continuous_train_v1.json"
)

# --- Evaluation protocols actually used by this matrix ---------------------

EVALUATION_PROTOCOLS = (
    EvaluationProtocol(
        "training_line",
        "Forward-moving active training line; produces checkpoints and "
        "evidence, not a frozen acceptance baseline.",
    ),
)

# --- Config base A: the shared cooperative flight-shaping surface ----------

# Curriculum randomization ramp shared by the nav-v1 baseline stages and the
# earlier-cut cruise/interval stages (same three randomization blocks, only
# the stage boundaries differ).
_NAV_RANDOMIZATION_RAMP = (
    {
        "world_yaw_range": [0.0, 0.0],
        "rotate_mission_heading_with_world": True,
        "wind_headwind_range": [0.0, 4.0],
        "wind_crosswind_range": [-2.0, 2.0],
        "wind_tailwind_max_mps": 0.0,
        "wind_shear_range": [0.0, 1.5],
    },
    {
        "world_yaw_range": [0.0, 180.0],
        "rotate_mission_heading_with_world": True,
        "wind_headwind_range": [0.0, 8.0],
        "wind_crosswind_range": [-4.0, 4.0],
        "wind_tailwind_max_mps": 1.0,
        "wind_shear_range": [0.0, 3.0],
    },
    {
        "world_yaw_range": [0.0, 360.0],
        "rotate_mission_heading_with_world": True,
        "wind_headwind_range": [0.0, 12.0],
        "wind_crosswind_range": [-6.0, 6.0],
        "wind_tailwind_max_mps": 2.0,
        "wind_shear_range": [0.0, 6.0],
    },
)


def _staged_curriculum(
    boundaries: tuple[int | None, ...],
    ramp: tuple[Mapping[str, Any], ...],
) -> list[dict[str, Any]]:
    if len(boundaries) != len(ramp):
        raise ValueError(
            f"curriculum needs one boundary per randomization block: "
            f"{len(boundaries)} vs {len(ramp)}"
        )
    return [
        {"until_timesteps": until, "randomization": dict(randomization)}
        for until, randomization in zip(boundaries, ramp)
    ]


COOPERATIVE_CONFIG_BASE: Mapping[str, Any] = {
    "agent_layer": "cooperative_execution",
    "algo": "AdaptiveKLPPO",
    "policy": "SquashedMultiInputPolicy",
    "total_timesteps": 131072,
    "n_envs": 4,
    "save_freq": 16384,
    "runtime": {
        "batch_observation_backend": "compiled",
        "batch_visual_backend": "compiled",
    },
    "cooperative_execution": {"policy_route": "shared_execution"},
    "env": {
        "include_proprio": True,
        "mission_obs_mode": "nav_v2_cooperative_takeoff_v1",
        "step_info_mode": "terminal",
        "visual_downsample": 1,
        "visual_update_interval": 1,
        "action_mode": "full",
    },
    "early_stop": {"enabled": False},
    "wrappers": {
        "multi_timescale_action": {
            "enabled": True,
            "hold_steps": 4,
            "low_freq_indices": [4, 5, 6, 9, 12, 13, 14, 15, 16],
            "snap_binary_indices": [],
            "binary_hysteresis_indices": [4, 9, 12, 13, 14, 15],
            "binary_on_threshold": 0.75,
            "binary_off_threshold": 0.25,
            "binary_initial_values": {
                "4": 1.0,
                "9": 0.0,
                "12": 0.0,
                "13": 0.0,
                "14": 0.0,
                "15": 0.0,
            },
            "center_deadband_indices": [5, 6, 7, 8],
            "center_deadband_center": 0.5,
            "center_deadband_half_width": 0.18,
            "scripted_baseline_mode": "takeoff_then_stable_flight",
            "scripted_transition_alt_agl_m": 160.0,
            "scripted_residual_scale": 0.16,
            "scripted_residual_alt_breakpoints_m": [0.0, 20.0, 160.0, 500.0, 1500.0],
            "scripted_residual_alt_scales": [0.10, 0.10, 0.16, 0.24, 0.30],
            # Mode scales stay per-entry: the lines disagree on which modes
            # exist and on their serialization order, and composition cannot
            # delete a base key.
            "scripted_residual_mode_scales": {},
            "scripted_blend_indices": [0, 1, 2, 3],
            "scripted_lock_indices": [4, 5, 6, 7, 8],
            "action_rate_penalty_coef": 0.00015,
        }
    },
    "curriculum": {
        "check_freq": 16384,
        "stages": _staged_curriculum((32768, 65536, None), _NAV_RANDOMIZATION_RAMP),
    },
    "hyperparameters": {
        "learning_rate": 3e-05,
        "n_steps": 128,
        "batch_size": 256,
        "n_epochs": 4,
        "gamma": 0.999,
        "gae_lambda": 0.97,
        "clip_range": 0.1,
        "clip_range_vf": 0.1,
        "normalize_advantage": True,
        "ent_coef": 0.0002,
        "vf_coef": 0.7,
        "max_grad_norm": 0.5,
        "target_kl": 0.02,
        "kl_penalty_coef": 0.05,
        "kl_adaptive": True,
        "device": "cuda",
        "policy_kwargs": {
            "features_extractor_class": "TransformerExtractor",
            "features_extractor_kwargs": {
                "features_dim": 192,
                "n_heads": 4,
                "n_layers": 3,
                "use_amp": True,
                "use_checkpointing": True,
            },
            "log_std_init": -1.5,
            "net_arch": {"pi": [192, 192], "vf": [192, 192]},
        },
    },
}

# --- Config base B: the P4b cruise-to-landing reopen surface ---------------

_P4B_RANDOMIZATION_RAMP = (
    {
        "world_yaw_range": [0.0, 90.0],
        "rotate_mission_heading_with_world": True,
        "wind_headwind_range": [0.0, 8.0],
        "wind_crosswind_range": [-3.0, 3.0],
        "wind_tailwind_max_mps": 1.0,
        "wind_shear_range": [0.0, 2.0],
    },
    {
        "world_yaw_range": [0.0, 180.0],
        "rotate_mission_heading_with_world": True,
        "wind_headwind_range": [0.0, 10.0],
        "wind_crosswind_range": [-5.0, 5.0],
        "wind_tailwind_max_mps": 2.0,
        "wind_shear_range": [0.0, 4.0],
    },
    {
        "world_yaw_range": [0.0, 360.0],
        "rotate_mission_heading_with_world": True,
        "wind_headwind_range": [0.0, 16.0],
        "wind_crosswind_range": [-8.0, 8.0],
        "wind_tailwind_max_mps": 3.0,
        "wind_shear_range": [0.0, 6.0],
    },
)

P4B_CONFIG_BASE: Mapping[str, Any] = {
    "algo": "AdaptiveKLPPO",
    "policy": "HierarchicalMoEExecutionPolicy",
    "total_timesteps": 32768,
    "n_envs": 4,
    "save_freq": 8192,
    "env": {
        "include_proprio": True,
        "mission_obs_mode": "nav_v2",
        "step_info_mode": "terminal",
        "visual_downsample": 2,
        "visual_update_interval": 2,
        "action_mode": "full",
    },
    "early_stop": {"enabled": False},
    "wrappers": {
        "multi_timescale_action": {
            "enabled": True,
            "hold_steps": 4,
            "low_freq_indices": [4, 5, 6, 9, 12, 13, 14, 15, 16],
            "snap_binary_indices": [],
            "binary_hysteresis_indices": [4, 9, 12, 13, 14, 15],
            "binary_on_threshold": 0.75,
            "binary_off_threshold": 0.25,
            "binary_initial_values": {
                "4": 1.0,
                "9": 0.0,
                "12": 0.0,
                "13": 0.0,
                "14": 0.0,
                "15": 0.0,
            },
            "center_deadband_indices": [5, 6, 7, 8],
            "center_deadband_center": 0.5,
            "center_deadband_half_width": 0.18,
            "scripted_baseline_mode": "takeoff_cruise_landing",
            "scripted_transition_alt_agl_m": 140.0,
            "scripted_residual_scale": 0.18,
            "scripted_residual_alt_breakpoints_m": [0.0, 20.0, 140.0, 500.0],
            "scripted_residual_alt_scales": [0.0, 0.0, 0.12, 0.22],
            "scripted_residual_mode_scales": {
                "takeoff": 0.0,
                "stable_flight": 0.18,
                "landing_ils": 0.25,
            },
            "scripted_residual_terminal_waypoint_count": 3,
            "scripted_residual_terminal_scale": 0.0,
            "scripted_residual_phaseout_target_speed_max": 130.0,
            "scripted_residual_phaseout_target_altitude_max": 900.0,
            "scripted_residual_phaseout_scale": 0.15,
            "scripted_blend_indices": [0, 1, 2, 3],
            "scripted_lock_indices": [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
            "action_rate_penalty_coef": 0.00015,
        }
    },
    "curriculum": {
        "check_freq": 8192,
        "stages": _staged_curriculum((12288, 24576, None), _P4B_RANDOMIZATION_RAMP),
    },
    "hyperparameters": {
        "learning_rate": 3e-05,
        "n_steps": 128,
        "batch_size": 256,
        "n_epochs": 4,
        "gamma": 0.999,
        "gae_lambda": 0.97,
        "clip_range": 0.1,
        "clip_range_vf": 0.1,
        "normalize_advantage": True,
        "ent_coef": 0.0002,
        "vf_coef": 0.7,
        "max_grad_norm": 0.5,
        "target_kl": 0.02,
        "kl_penalty_coef": 0.05,
        "kl_adaptive": True,
        "device": "cuda",
        "policy_kwargs": {
            "features_extractor_class": "TransformerVisualExtractor",
            "features_extractor_kwargs": {
                "features_dim": 256,
                "n_heads": 4,
                "n_layers": 4,
                "visual_cnn_channels": 64,
                "use_amp": False,
                "use_checkpointing": True,
            },
            "log_std_init": -1.5,
            "net_arch": {"pi": [256, 256], "vf": [256, 256]},
        },
    },
}

CONFIG_BASES: Mapping[str, Mapping[str, Any]] = MappingProxyType(
    {
        COOPERATIVE_CONFIG_BASE_ID: COOPERATIVE_CONFIG_BASE,
        P4B_CONFIG_BASE_ID: P4B_CONFIG_BASE,
    }
)

# --- Shared delta fragments (key order inside fragments is load-bearing) ---

# The four takeoff-line entries share the two-mode residual scale table; the
# three landing entries extend it with the ILS segment.
_TAKEOFF_MODE_SCALES = {"takeoff": 0.12, "stable_flight": 0.16}

_LANDING_WRAPPER = {
    "multi_timescale_action": {
        "scripted_baseline_mode": "takeoff_cruise_landing",
        "scripted_residual_mode_scales": {
            "takeoff": 0.12,
            "stable_flight": 0.16,
            "landing_ils": 0.20,
        },
        "scripted_residual_terminal_waypoint_count": 3,
        "scripted_residual_terminal_scale": 0.0,
        "scripted_residual_phaseout_target_speed_max": 130.0,
        "scripted_residual_phaseout_target_altitude_max": 900.0,
        "scripted_residual_phaseout_scale": 0.12,
        "scripted_lock_indices": [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
    }
}

_TAKEOFF_MODE_WRAPPER = {
    "multi_timescale_action": {"scripted_residual_mode_scales": _TAKEOFF_MODE_SCALES}
}

_NONFINITE_DIAGNOSTICS = {
    "nonfinite_probe": True,
    "nonfinite_probe_report": "nonfinite_probe_report.json",
    "nonfinite_probe_history": 384,
}

_HMOE_BOOTSTRAP = {"bootstrap_from_shared_action_head": "auto"}

# Optimizer-side adaptive-KL schedule shared by the HMoE lines and their
# fair-control shared baseline (replaces the base's plain penalty).
_ADAPTIVE_KL_SCHEDULE = {
    "kl_penalty_coef_min": 0.01,
    "kl_adapt_factor": 1.25,
    "lr_mult_max": 1.5,
    "low_kl_boost_patience": 6,
    "boost_lr_on_low_kl": False,
}

_HMOE_ROUTE_KWARGS = {
    "family_subexpert_counts": [3, 2, 3, 1],
    "hmoe_residual_scale": 0.18,
    "hmoe_head_lr_scale": 0.15,
}

_HMOE_POLICY_KWARGS = {
    **_HMOE_ROUTE_KWARGS,
    "hmoe_residual_warmup_fraction": 0.3,
    "hmoe_residual_start_factor": 0.0,
}

_LANDING_HMOE_POLICY_KWARGS = {
    "features_extractor_kwargs": {"amp_dtype": "bf16"},
    **_HMOE_ROUTE_KWARGS,
    "hmoe_residual_warmup_fraction": 0.1,
    "hmoe_residual_start_factor": 0.2,
}

_LANDING_RANDOMIZATION_RAMP = (
    {
        "world_yaw_range": [0.0, 45.0],
        "rotate_mission_heading_with_world": True,
        "wind_headwind_range": [0.0, 6.0],
        "wind_crosswind_range": [-2.0, 2.0],
        "wind_tailwind_max_mps": 0.5,
        "wind_shear_range": [0.0, 2.0],
    },
    {
        "world_yaw_range": [0.0, 150.0],
        "rotate_mission_heading_with_world": True,
        "wind_headwind_range": [0.0, 10.0],
        "wind_crosswind_range": [-4.0, 4.0],
        "wind_tailwind_max_mps": 1.5,
        "wind_shear_range": [0.0, 4.0],
    },
    {
        "world_yaw_range": [0.0, 360.0],
        "rotate_mission_heading_with_world": True,
        "wind_headwind_range": [0.0, 16.0],
        "wind_crosswind_range": [-8.0, 8.0],
        "wind_tailwind_max_mps": 3.0,
        "wind_shear_range": [0.0, 6.0],
    },
)

# The cruise/interval first-stage lines cut the same randomization ramp at
# earlier boundaries; stage lists replace wholesale (list semantics), so each
# variant is a complete delta value.
_EARLY_STAGE_CURRICULUM = {
    "stages": _staged_curriculum((16384, 32768, None), _NAV_RANDOMIZATION_RAMP)
}
_LANDING_CURRICULUM = {
    "stages": _staged_curriculum((32768, 81920, None), _LANDING_RANDOMIZATION_RAMP)
}

# Plain (non-adaptive) KL penalty used by the shared-policy baselines.
_PLAIN_KL = {"kl_penalty_coef": 0.0}

# --- Literal spellings required for byte parity -----------------------------

_ALT_SCALES_PATH = (
    "wrappers",
    "multi_timescale_action",
    "scripted_residual_alt_scales",
)
_LANDING_ILS_PATH = (
    "wrappers",
    "multi_timescale_action",
    "scripted_residual_mode_scales",
    "landing_ils",
)

# Every cooperative entry keeps the historical trailing-zero spelling of the
# altitude-scale table; the landing entries also keep "0.20" for the ILS
# residual scale, and the P4b reopen entries keep the plain-decimal
# learning rate.
_COOP_ALT_SCALES_LITERAL = {_ALT_SCALES_PATH: "[0.10, 0.10, 0.16, 0.24, 0.30]"}
_CRUISE_ALT_SCALES_LITERAL = {_ALT_SCALES_PATH: "[0.10, 0.10, 0.15, 0.22, 0.30]"}
_LANDING_LITERALS = {**_COOP_ALT_SCALES_LITERAL, _LANDING_ILS_PATH: "0.20"}
_LR_PLAIN_DECIMAL = {("hyperparameters", "learning_rate"): "0.00003"}

_COOP_RENDER = RenderStyle(literal_overrides=_COOP_ALT_SCALES_LITERAL)
_LANDING_RENDER = RenderStyle(literal_overrides=_LANDING_LITERALS)

# --- Entry table: (experiment_id, scenario, base, delta, render style) -----

_ENTRY_SPECS: tuple[
    tuple[str, str, str, Mapping[str, Any], RenderStyle], ...
] = (
    # Cooperative cruise line (P8 cooperative-execution formation baseline).
    (
        "cooperative_cruise_nav_v2_formation_v1",
        _SCENARIO_CRUISE_FORMATION,
        COOPERATIVE_CONFIG_BASE_ID,
        {
            "total_timesteps": 65536,
            "env": {"mission_obs_mode": "nav_v2_formation_role_v1"},
            "wrappers": {
                "multi_timescale_action": {
                    "scripted_baseline_mode": "stable_flight",
                    "scripted_transition_alt_agl_m": 140.0,
                    "scripted_residual_scale": 0.15,
                    "scripted_residual_alt_breakpoints_m": [0.0, 60.0, 140.0, 400.0, 1500.0],
                    "scripted_residual_alt_scales": [0.10, 0.10, 0.15, 0.22, 0.30],
                    "scripted_residual_mode_scales": {"stable_flight": 0.15},
                }
            },
            "curriculum": _EARLY_STAGE_CURRICULUM,
            "hyperparameters": _PLAIN_KL,
        },
        RenderStyle(literal_overrides=_CRUISE_ALT_SCALES_LITERAL),
    ),
    # Cooperative takeoff line: interval takeoff/departure first stage.
    (
        "cooperative_interval_takeoff_departure_nav_v1",
        _SCENARIO_INTERVAL_TAKEOFF,
        COOPERATIVE_CONFIG_BASE_ID,
        {
            "total_timesteps": 65536,
            "wrappers": _TAKEOFF_MODE_WRAPPER,
            "curriculum": _EARLY_STAGE_CURRICULUM,
            "hyperparameters": _PLAIN_KL,
        },
        _COOP_RENDER,
    ),
    # Takeoff-to-cruise bridge: shared baseline, HMoE, and the fair pair.
    (
        "cooperative_takeoff_to_cruise_nav_v1",
        _SCENARIO_TAKEOFF_TO_CRUISE,
        COOPERATIVE_CONFIG_BASE_ID,
        {
            "diagnostics": _NONFINITE_DIAGNOSTICS,
            "wrappers": _TAKEOFF_MODE_WRAPPER,
            "hyperparameters": _PLAIN_KL,
        },
        _COOP_RENDER,
    ),
    (
        "cooperative_takeoff_to_cruise_nav_hmoe_v1",
        _SCENARIO_TAKEOFF_TO_CRUISE,
        COOPERATIVE_CONFIG_BASE_ID,
        {
            "policy": "HierarchicalMoEExecutionPolicy",
            "diagnostics": _NONFINITE_DIAGNOSTICS,
            "hmoe": _HMOE_BOOTSTRAP,
            "wrappers": _TAKEOFF_MODE_WRAPPER,
            "hyperparameters": {
                **_ADAPTIVE_KL_SCHEDULE,
                "policy_kwargs": _HMOE_POLICY_KWARGS,
            },
        },
        _COOP_RENDER,
    ),
    (
        "cooperative_takeoff_to_cruise_nav_shared_fair_v1",
        _SCENARIO_TAKEOFF_TO_CRUISE,
        COOPERATIVE_CONFIG_BASE_ID,
        {
            "diagnostics": _NONFINITE_DIAGNOSTICS,
            "wrappers": _TAKEOFF_MODE_WRAPPER,
            "hyperparameters": _ADAPTIVE_KL_SCHEDULE,
        },
        _COOP_RENDER,
    ),
    (
        "cooperative_takeoff_to_cruise_nav_hmoe_fair_v1",
        _SCENARIO_TAKEOFF_TO_CRUISE,
        COOPERATIVE_CONFIG_BASE_ID,
        {
            "policy": "HierarchicalMoEExecutionPolicy",
            "diagnostics": _NONFINITE_DIAGNOSTICS,
            "hmoe": _HMOE_BOOTSTRAP,
            "wrappers": _TAKEOFF_MODE_WRAPPER,
            "hyperparameters": {
                **_ADAPTIVE_KL_SCHEDULE,
                "policy_kwargs": _HMOE_POLICY_KWARGS,
            },
        },
        _COOP_RENDER,
    ),
    # Closed-loop takeoff-cruise-landing line.
    (
        "cooperative_takeoff_to_cruise_landing_nav_v1",
        _SCENARIO_TAKEOFF_CRUISE_LANDING,
        COOPERATIVE_CONFIG_BASE_ID,
        {
            "diagnostics": _NONFINITE_DIAGNOSTICS,
            "wrappers": _LANDING_WRAPPER,
            "curriculum": _LANDING_CURRICULUM,
            "hyperparameters": _PLAIN_KL,
        },
        _LANDING_RENDER,
    ),
    (
        "cooperative_takeoff_to_cruise_landing_hmoe_v1",
        _SCENARIO_TAKEOFF_CRUISE_LANDING,
        COOPERATIVE_CONFIG_BASE_ID,
        {
            "policy": "HierarchicalMoEExecutionPolicy",
            "diagnostics": _NONFINITE_DIAGNOSTICS,
            "hmoe": _HMOE_BOOTSTRAP,
            "wrappers": _LANDING_WRAPPER,
            "curriculum": _LANDING_CURRICULUM,
            "hyperparameters": {
                **_ADAPTIVE_KL_SCHEDULE,
                "policy_kwargs": _LANDING_HMOE_POLICY_KWARGS,
            },
        },
        _LANDING_RENDER,
    ),
    (
        "cooperative_takeoff_to_cruise_landing_hmoe_v1_resume_128k_from_32768",
        _SCENARIO_TAKEOFF_CRUISE_LANDING,
        COOPERATIVE_CONFIG_BASE_ID,
        {
            "policy": "HierarchicalMoEExecutionPolicy",
            "total_timesteps": 98304,
            "diagnostics": _NONFINITE_DIAGNOSTICS,
            "hmoe": _HMOE_BOOTSTRAP,
            "wrappers": _LANDING_WRAPPER,
            "curriculum": _LANDING_CURRICULUM,
            "hyperparameters": {
                **_ADAPTIVE_KL_SCHEDULE,
                "policy_kwargs": _LANDING_HMOE_POLICY_KWARGS,
            },
        },
        _LANDING_RENDER,
    ),
    # P4b cruise-to-landing reopen lane (second config base).
    (
        "p4b_cruise_to_landing_shared_reopen_v1",
        _SCENARIO_P4B_CRUISE_TO_LANDING,
        P4B_CONFIG_BASE_ID,
        {
            "policy": "SquashedMultiInputPolicy",
            "hyperparameters": _PLAIN_KL,
        },
        RenderStyle(literal_overrides=_LR_PLAIN_DECIMAL),
    ),
    (
        "p4b_cruise_to_landing_hmoe_v1",
        _SCENARIO_P4B_CRUISE_TO_LANDING,
        P4B_CONFIG_BASE_ID,
        {
            "hmoe": _HMOE_BOOTSTRAP,
            "hyperparameters": {
                **_ADAPTIVE_KL_SCHEDULE,
                "policy_kwargs": _HMOE_POLICY_KWARGS,
            },
        },
        RenderStyle(),
    ),
    (
        "p4b_cruise_to_landing_hmoe_reopen_v1",
        _SCENARIO_P4B_CRUISE_TO_LANDING,
        P4B_CONFIG_BASE_ID,
        {
            "hmoe": _HMOE_BOOTSTRAP,
            "hyperparameters": {
                **_ADAPTIVE_KL_SCHEDULE,
                "policy_kwargs": _HMOE_POLICY_KWARGS,
            },
        },
        RenderStyle(literal_overrides=_LR_PLAIN_DECIMAL),
    ),
)


def build_registry() -> ExperimentRegistry:
    """Build a fresh, fully validated registry of the cooperative matrix."""
    registry = ExperimentRegistry()
    for base_id, base in CONFIG_BASES.items():
        registry.register_config_base(base_id, base)
    for protocol in EVALUATION_PROTOCOLS:
        registry.register_evaluation_protocol(protocol)
    for experiment_id, scenario, base_id, delta, _ in _ENTRY_SPECS:
        registry.register_experiment(
            Experiment(
                experiment_id=experiment_id,
                scenario=ScenarioRef(scenario),
                config=ConfigComposition(base_id, delta),
                seeds=SeedSpec(),
                evaluation_protocol="training_line",
            )
        )
    return registry


REGISTRY = build_registry()

MATRIX_ENTRIES: tuple[MatrixEntry, ...] = tuple(
    MatrixEntry(
        experiment=REGISTRY.experiment(experiment_id),
        output_path=f"{MATRIX_DIR}/{experiment_id}.json",
        render=render,
    )
    for experiment_id, _, _, _, render in _ENTRY_SPECS
)


def composed_config(entry: MatrixEntry) -> dict[str, Any]:
    """Expand one matrix entry into its canonical run-config mapping."""
    merged = compose_config(
        REGISTRY.config_base(entry.experiment.config.base_id),
        entry.experiment.config.delta,
    )
    return normalize_trailing_keys(merged, CANONICAL_TRAILING_KEYS)
