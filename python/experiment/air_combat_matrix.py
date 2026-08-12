"""Typed Experiment ownership of the 24-file air-combat run-config matrix.

This module is the declarative single source for
``examples/config/training/active/air_combat/*.json``. Every checked-in run
configuration in that directory is a projection of one registered
:class:`~python.experiment.definition.Experiment`: a shared config base plus
a per-experiment delta, composed with the deterministic merge rules in
:mod:`python.experiment.composition` and serialized by
``tools/maintenance/experiment_matrix/generate.py``.

Byte parity with the checked-in files is a hard invariant (the config paths
are pinned by docs and tests). It is enforced by
``tests/architecture/governance/test_experiment_matrix_freshness.py``; edit
the base or a delta here, then run the generator with ``--write`` and
``--check``. Do not edit the generated JSON files directly.

Formatting facts this module pins (observed, not invented):

- ``CANONICAL_TRAILING_KEYS`` reproduces the matrix's canonical key layout
  (``hyperparameters`` serializes last, ``device``/``policy_kwargs`` close
  the hyperparameters block, and so on).
- Ten entries spell ``learning_rate`` as the plain decimal ``0.00003``
  instead of JSON's shortest form ``3e-05``; three entries expand scalar
  arrays one-element-per-line. Both dialects are recorded per entry as
  :class:`RenderStyle` so regeneration stays byte-identical.

Scenario pairings follow the directory README and
``tests/training/test_air_combat_training_entry_contracts.py``. Seed sets
are empty because no matrix entry pins seeds today (training bootstrap owns
the default); evaluation protocols are limited to the two intents the
matrix actually uses (``smoke``, ``probe``) per the registry-follows-usage
rule.
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
from python.experiment.matrix_projection import (
    SCALAR_ARRAY_LAYOUTS,
    MatrixEntryBase,
    RenderStyle,
)

__all__ = [
    "CONFIG_BASE",
    "CONFIG_BASE_ID",
    "MATRIX_DIR",
    "MATRIX_ENTRIES",
    "MatrixEntry",
    "REGISTRY",
    "RenderStyle",
    "SCALAR_ARRAY_LAYOUTS",
    "build_registry",
    "composed_config",
]

MATRIX_DIR = "examples/config/training/active/air_combat"
CONFIG_BASE_ID = "air_combat_1v1_hmoe_execution_v1"

# Canonical serialization order: these keys close their mapping, in this
# order, regardless of where a delta introduced sibling keys.
CANONICAL_TRAILING_KEYS: Mapping[tuple[str, ...], tuple[str, ...]] = MappingProxyType(
    {
        (): ("hyperparameters",),
        ("hyperparameters",): ("device", "policy_kwargs"),
        ("hyperparameters", "policy_kwargs"): ("log_std_init", "net_arch"),
        ("hyperparameters", "policy_kwargs", "features_extractor_kwargs"): (
            "use_amp",
            "amp_dtype",
            "use_checkpointing",
        ),
    }
)

@dataclass(frozen=True)
class MatrixEntry(MatrixEntryBase):
    """One registered air-combat experiment plus its pinned output projection."""

    MATRIX_DIR = "examples/config/training/active/air_combat"


# --- Scenario pairings (directory README + training entry contract tests) ---

_SCENARIO_HEADON_SMOKE = "scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json"
_SCENARIO_STAGE0 = "scenarios/air_combat/1v1/air_combat_1v1_stage0_drone_weapon_employment_v1.json"
_SCENARIO_STAGE1 = "scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json"
_SCENARIO_STAGE1_SHAPED = (
    "scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_training_shaped_v1.json"
)
_SCENARIO_STAGE1_C2_ROE = (
    "scenarios/air_combat/1v1/"
    "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json"
)
_SCENARIO_STAGE2_C2_ROE = (
    "scenarios/air_combat/1v1/air_combat_1v1_stage2_evasive_fighter_c2_roe_training_shaped_v1.json"
)

# --- Evaluation protocols actually used by this matrix ---

EVALUATION_PROTOCOLS = (
    EvaluationProtocol(
        "smoke",
        "Minimal bootstrap verification of the training chain (512-step budget).",
    ),
    EvaluationProtocol(
        "probe",
        "Short diagnostic training probe; produces evidence, not acceptance baselines.",
    ),
)

# --- Config base: the shared HMoE execution surface of all 24 entries ---

CONFIG_BASE: Mapping[str, Any] = {
    "agent_layer": "execution",
    "algo": "AdaptiveKLPPO",
    "policy": "HierarchicalMoEExecutionPolicy",
    "total_timesteps": 32768,
    "n_envs": 4,
    "save_freq": 8192,
    "runtime": {"torch_threads": 1},
    "env": {
        "include_proprio": True,
        "mission_obs_mode": "basic",
        "step_info_mode": "terminal",
        "execution_step_runtime_mode": "compiled",
        "flight_shaping_backend": "compiled",
        "action_mode": "air_combat_hybrid_v1",
    },
    "early_stop": {"enabled": False},
    "diagnostics": {
        "nonfinite_probe": True,
        "nonfinite_probe_report": "nonfinite_probe_report.json",
        "nonfinite_probe_history": 1024,
    },
    "hmoe": {"bootstrap_from_shared_action_head": "auto"},
    "hyperparameters": {
        "learning_rate": 3e-05,
        "n_steps": 256,
        "batch_size": 512,
        "n_epochs": 2,
        "gamma": 0.999,
        "gae_lambda": 0.97,
        "clip_range": 0.1,
        "clip_range_vf": 0.1,
        "normalize_advantage": True,
        "ent_coef": 0.0005,
        "vf_coef": 0.7,
        "max_grad_norm": 0.5,
        "target_kl": 0.02,
        "kl_penalty_coef": 0.05,
        "kl_adaptive": True,
        "kl_penalty_coef_min": 0.01,
        "kl_adapt_factor": 1.25,
        "lr_mult_max": 1.5,
        "low_kl_boost_patience": 6,
        "boost_lr_on_low_kl": False,
        "device": "cuda",
        "policy_kwargs": {
            "features_extractor_class": "TemporalTransformerExtractor",
            "features_extractor_kwargs": {
                "features_dim": 192,
                "n_heads": 4,
                "n_layers": 3,
                "use_amp": True,
                "amp_dtype": "bf16",
                "use_checkpointing": True,
            },
            "family_subexpert_counts": [3, 2, 3, 1],
            "hmoe_residual_scale": 0.18,
            "hmoe_head_lr_scale": 0.15,
            "hmoe_residual_warmup_fraction": 0.3,
            "hmoe_residual_start_factor": 0.0,
            "log_std_init": -2.0,
            "net_arch": {"pi": [192, 192], "vf": [192, 192]},
        },
    },
}

# --- Shared delta fragments (key order inside fragments is load-bearing) ---

_WORLD_BATCH_RUNTIME = {
    "world_batch_vec_env": True,
    "world_batch_threads": 4,
    "batch_observation_backend": "compiled",
    "batch_visual_backend": "compiled",
    "policy_observation_torch_bridge": True,
    "observation_return_mode": "copy",
}

_TG_P7_PROXY_DATABASE = (
    "docs/systems/effects/reviews/f16c_target_geometry_20260614/"
    "review_packets/f16c_20260611/target_geometry_training_proxy_database_20260613"
)

_TG_P7_PROXY_RUNTIME = {
    **_WORLD_BATCH_RUNTIME,
    "database_path": _TG_P7_PROXY_DATABASE,
    "target_geometry_proxy": {
        "feature_flag": "A2_TARGET_GEOMETRY_PROXY_F16C_R22",
        "target_unit": "F-16C_Block50",
        "activation_scope": "f16c_block50_initial_training_geometry_proxy",
        "source_manifest": _TG_P7_PROXY_DATABASE + ".json",
        "default_component_count": 26,
        "proxy_component_count": 32,
        "split_receiver_component_count": 8,
        "retired_parent_component_count": 2,
    },
}

_STABLE_FLIGHT_RESIDUAL_WRAPPERS = {
    "multi_timescale_action": {
        "enabled": True,
        "hold_steps": 1,
        "low_freq_indices": [],
        "snap_binary_indices": [],
        "binary_hysteresis_indices": [],
        "scripted_baseline_mode": "stable_flight",
        "scripted_residual_scale": 0.18,
        "scripted_blend_indices": [0, 1, 2, 3],
        "scripted_lock_indices": [],
    }
}

_C2_ROE_V1_ENV = {"mission_obs_mode": "air_combat_c2_roe_v1", "step_info_mode": "full"}
_C2_ROE_V1_TEMPORAL_ENV = {**_C2_ROE_V1_ENV, "temporal_history_len": 16}
_C2_ROE_V2_TEMPORAL_ENV = {
    "mission_obs_mode": "air_combat_c2_roe_v2",
    "step_info_mode": "full",
    "temporal_history_len": 16,
}

# Temporal window on top of the base extractor (stage-1 C2/ROE keeps n_layers=3;
# the early stage-0/stage-1 temporal probes drop to n_layers=2).
_TEMPORAL_STACK = {"temporal_n_heads": 4, "temporal_n_layers": 2}
_TEMPORAL_STACK_2L = {"n_layers": 2, **_TEMPORAL_STACK}

# Five-family HMoE route surface used by every C2/ROE entry (A4 decision).
_FIVE_FAMILY_POLICY = {
    "family_subexpert_counts": [3, 2, 3, 1, 3],
    "hmoe_head_lr_scale": 0.35,
    "hmoe_residual_start_factor": 0.25,
    "hybrid_action_spec": "air_combat_hybrid_v1",
}

_SHAPED_CURRICULUM_FIRST_EVENT = {
    "first_event_hazard_coef": 0.2,
    "first_event_curriculum_coef": 0.1,
    "first_event_curriculum_decay_fraction": 0.25,
}

_DEADLINE_FIRST_EVENT = {
    "first_event_hazard_coef": 0.3,
    "first_event_curriculum_coef": 0.0,
    "first_event_deadline_weight": 1.0,
    "first_event_deadline_min_window_age_steps": 64,
}

_EVENT_CREDIT_HYPERS = {
    "first_event_hazard_coef": 0.0,
    "first_event_curriculum_coef": 0.0,
    "first_event_deadline_weight": 0.0,
    "first_event_deadline_min_window_age_steps": 64,
    "first_event_launch_window_enabled": True,
    "first_event_launch_window_min_range_m": 8000.0,
    "first_event_launch_window_max_range_m": 30000.0,
    "first_event_launch_window_max_track_age_s": 5.0,
    "first_event_launch_window_min_window_age_steps": 32,
    "first_event_launch_window_prewindow_hold_weight": 0.0,
    "first_event_launch_window_early_accept_weight": 0.0,
    "event_credit_value_coef": 0.4,
    "event_credit_delta_align_coef": 0.0,
    "event_credit_delta_align_clip": 4.0,
    "event_credit_delta_align_positive_only": True,
    "event_credit_positive_mass_cap": 1.0,
    "event_credit_negative_mass_cap": 1.0,
    "event_credit_prewindow_hold_weight": 0.4,
    "event_credit_early_accept_weight": 1.0,
    "event_credit_curriculum_coef": 0.0,
    "event_credit_curriculum_min_window_age_steps": 32,
    "event_credit_censored_survival_weight": 0.0,
    "event_credit_deadline_weight": 1.0,
    "event_credit_deadline_min_window_age_steps": 64,
    "event_credit_shadow_quality_weight": 1.0,
    "event_credit_legal_open_quality_weight": 1.0,
    "event_credit_legal_open_quality_min_window_age_steps": 32,
    "event_credit_legal_projection_enabled": True,
    "event_credit_projection_value_coef": 0.4,
    "event_credit_projection_delta_align_coef": 0.0,
    "event_credit_separate_update_enabled": True,
    "event_credit_separate_update_max_grad_norm": 0.5,
    "event_policy_margin_coef": 0.35,
    "event_policy_margin": 2.0,
    "event_policy_projection_margin_coef": 0.15,
    "event_policy_separate_update_enabled": True,
    "event_policy_separate_update_max_grad_norm": 2.0,
    "event_policy_separate_update_steps": 4,
}

_FIRE_BOUNDARY_HYPERS = {
    "fire_boundary_coef": 20.0,
    "fire_boundary_negative_logit_ceiling_coef": 5.0,
    "fire_boundary_negative_logit_ceiling": -2.0,
    "fire_boundary_positive_logit_floor_coef": 5.0,
    "fire_boundary_positive_logit_floor": 2.0,
    "fire_boundary_separate_update_enabled": True,
    "fire_boundary_dedicated_optimizer_enabled": True,
    "fire_boundary_separate_update_steps": 32,
    "fire_boundary_max_grad_norm": 5.0,
    "fire_boundary_support_preserving_collect_enabled": True,
    "fire_boundary_support_preserving_hold_quality_enabled": True,
}

_GROUPED_STOPPING_HYPERS = {
    "grouped_stopping_coef": 1.0,
    "grouped_stopping_early_mass_coef": 1.0,
    "grouped_stopping_early_mass_budget": 0.05,
    "grouped_stopping_no_event_coef": 1.0,
    "grouped_stopping_boundary_threshold": 0.0,
    "grouped_stopping_detach_latent": False,
}

_EVENT_CREDIT_POLICY_HEADS = {
    "hybrid_event_head_lr_scale": 10.0,
    "hybrid_event_credit_head_lr_scale": 6.0,
}

_M3S2_EVENT_HEADS = {
    **_EVENT_CREDIT_POLICY_HEADS,
    "hybrid_event_use_stopping_head": False,
    "hybrid_event_use_window_classifier_head": False,
}

_SCRIPTED_RED_PROBE_HYPERS = {
    "n_steps": 128,
    "batch_size": 256,
    "ent_coef": 0.0002,
    "policy_kwargs": {"features_extractor_class": "TransformerExtractor", "log_std_init": -1.5},
}

_SCRIPTED_RED_SMOKE_HYPERS = {
    "n_steps": 64,
    "batch_size": 64,
    "ent_coef": 0.0002,
    "policy_kwargs": {"features_extractor_class": "TransformerExtractor", "log_std_init": -1.5},
}

# Ten entries keep the historical plain-decimal learning-rate spelling.
_LR_PLAIN_DECIMAL = {("hyperparameters", "learning_rate"): "0.00003"}

# --- Entry table: (experiment_id, scenario, protocol, delta, render style) ---

_ENTRY_SPECS: tuple[tuple[str, str, str, Mapping[str, Any], RenderStyle], ...] = (
    # Scripted-red F-16C smoke and probe ramp (headon sensor smoke scenario).
    (
        "air_combat_1v1_f16c_scripted_red_smoke_v1",
        _SCENARIO_HEADON_SMOKE,
        "smoke",
        {
            "total_timesteps": 512,
            "n_envs": 1,
            "save_freq": 256,
            "env": {"action_mode": "full"},
            "diagnostics": {"nonfinite_probe_history": 384},
            "hyperparameters": _SCRIPTED_RED_SMOKE_HYPERS,
        },
        RenderStyle(),
    ),
    (
        "air_combat_1v1_f16c_scripted_red_world_batch_smoke_v1",
        _SCENARIO_HEADON_SMOKE,
        "smoke",
        {
            "total_timesteps": 512,
            "n_envs": 1,
            "save_freq": 256,
            "runtime": {
                "world_batch_vec_env": True,
                "world_batch_threads": 1,
                "batch_observation_backend": "compiled",
                "batch_visual_backend": "compiled",
            },
            "env": {"action_mode": "full"},
            "diagnostics": {"nonfinite_probe_history": 384},
            "hyperparameters": _SCRIPTED_RED_SMOKE_HYPERS,
        },
        RenderStyle(),
    ),
    (
        "air_combat_1v1_f16c_scripted_red_world_batch_probe_8k_v1",
        _SCENARIO_HEADON_SMOKE,
        "probe",
        {
            "total_timesteps": 8192,
            "save_freq": 2048,
            "runtime": _WORLD_BATCH_RUNTIME,
            "env": {"action_mode": "full"},
            "diagnostics": {"nonfinite_probe_history": 768},
            "hyperparameters": _SCRIPTED_RED_PROBE_HYPERS,
        },
        RenderStyle(),
    ),
    (
        "air_combat_1v1_f16c_scripted_red_world_batch_probe_32k_v1",
        _SCENARIO_HEADON_SMOKE,
        "probe",
        {
            "runtime": _WORLD_BATCH_RUNTIME,
            "env": {"action_mode": "full"},
            "diagnostics": {"nonfinite_probe_history": 768},
            "hyperparameters": _SCRIPTED_RED_PROBE_HYPERS,
        },
        RenderStyle(),
    ),
    (
        "air_combat_1v1_f16c_scripted_red_tg_p7_target_geometry_proxy_world_batch_probe_v1",
        _SCENARIO_HEADON_SMOKE,
        "probe",
        {
            "total_timesteps": 8192,
            "save_freq": 2048,
            "runtime": _TG_P7_PROXY_RUNTIME,
            "env": {"action_mode": "full"},
            "diagnostics": {"nonfinite_probe_history": 768},
            "hyperparameters": _SCRIPTED_RED_PROBE_HYPERS,
        },
        RenderStyle(),
    ),
    (
        "air_combat_1v1_f16c_scripted_red_tg_p7_target_geometry_proxy_world_batch_probe_32k_v1",
        _SCENARIO_HEADON_SMOKE,
        "probe",
        {
            "runtime": _TG_P7_PROXY_RUNTIME,
            "env": {"action_mode": "full"},
            "diagnostics": {"nonfinite_probe_history": 768},
            "hyperparameters": _SCRIPTED_RED_PROBE_HYPERS,
        },
        RenderStyle(),
    ),
    # Stage 0: drone weapon-employment probes.
    (
        "air_combat_1v1_stage0_drone_weapon_employment_world_batch_probe_v1",
        _SCENARIO_STAGE0,
        "probe",
        {
            "total_timesteps": 4096,
            "save_freq": 1024,
            "runtime": _WORLD_BATCH_RUNTIME,
            "env": {"action_mode": "full"},
            "diagnostics": {"nonfinite_probe_history": 768},
            "hyperparameters": {
                "n_steps": 128,
                "batch_size": 256,
                "policy_kwargs": {
                    "features_extractor_class": "TransformerExtractor",
                    "log_std_init": -1.2,
                },
            },
        },
        RenderStyle(),
    ),
    (
        "air_combat_1v1_stage0_drone_weapon_employment_temporal_world_batch_probe_v1",
        _SCENARIO_STAGE0,
        "probe",
        {
            "total_timesteps": 4096,
            "save_freq": 1024,
            "runtime": _WORLD_BATCH_RUNTIME,
            "env": {"action_mode": "full", "temporal_history_len": 16},
            "diagnostics": {"nonfinite_probe_history": 768},
            "hyperparameters": {
                "n_steps": 128,
                "batch_size": 256,
                "policy_kwargs": {
                    "features_extractor_kwargs": _TEMPORAL_STACK_2L,
                    "log_std_init": -1.2,
                },
            },
        },
        RenderStyle(),
    ),
    # Stage 1: BVR non-maneuvering target, M1 interface/temporal ladder.
    (
        "air_combat_1v1_stage1_bvr_nonmaneuvering_target_world_batch_probe_v1",
        _SCENARIO_STAGE1,
        "probe",
        {
            "total_timesteps": 8192,
            "save_freq": 2048,
            "runtime": _WORLD_BATCH_RUNTIME,
            "env": {"action_mode": "full"},
            "hyperparameters": {
                "policy_kwargs": {
                    "features_extractor_class": "TransformerExtractor",
                    "log_std_init": -1.2,
                },
            },
        },
        RenderStyle(),
    ),
    (
        "air_combat_1v1_stage1_bvr_nonmaneuvering_target_temporal_world_batch_probe_v1",
        _SCENARIO_STAGE1,
        "probe",
        {
            "total_timesteps": 8192,
            "save_freq": 2048,
            "runtime": _WORLD_BATCH_RUNTIME,
            "env": {"action_mode": "full", "temporal_history_len": 16},
            "hyperparameters": {
                "policy_kwargs": {
                    "features_extractor_kwargs": _TEMPORAL_STACK_2L,
                    "log_std_init": -1.2,
                },
            },
        },
        RenderStyle(),
    ),
    (
        "air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_world_batch_probe_v1",
        _SCENARIO_STAGE1,
        "probe",
        {
            "total_timesteps": 8192,
            "save_freq": 2048,
            "runtime": _WORLD_BATCH_RUNTIME,
            "hyperparameters": {
                "policy_kwargs": {
                    "features_extractor_class": "TransformerExtractor",
                    "hybrid_action_spec": "air_combat_hybrid_v1",
                    "log_std_init": -1.2,
                },
            },
        },
        RenderStyle(),
    ),
    (
        "air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_temporal_world_batch_probe_v1",
        _SCENARIO_STAGE1,
        "probe",
        {
            "total_timesteps": 8192,
            "save_freq": 2048,
            "runtime": _WORLD_BATCH_RUNTIME,
            "env": {"temporal_history_len": 16},
            "hyperparameters": {
                "policy_kwargs": {
                    "features_extractor_kwargs": _TEMPORAL_STACK_2L,
                    "hybrid_action_spec": "air_combat_hybrid_v1",
                    "log_std_init": -1.2,
                },
            },
        },
        RenderStyle(),
    ),
    (
        "air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_shaped_world_batch_probe_v1",
        _SCENARIO_STAGE1_SHAPED,
        "probe",
        {
            "runtime": _WORLD_BATCH_RUNTIME,
            "wrappers": _STABLE_FLIGHT_RESIDUAL_WRAPPERS,
            "hyperparameters": {
                "policy_kwargs": {
                    "features_extractor_class": "TransformerExtractor",
                    "hybrid_action_spec": "air_combat_hybrid_v1",
                },
            },
        },
        RenderStyle(literal_overrides=_LR_PLAIN_DECIMAL),
    ),
    (
        "air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_temporal_shaped_world_batch_probe_v1",
        _SCENARIO_STAGE1_SHAPED,
        "probe",
        {
            "runtime": _WORLD_BATCH_RUNTIME,
            "env": {"temporal_history_len": 16},
            "wrappers": _STABLE_FLIGHT_RESIDUAL_WRAPPERS,
            "hyperparameters": {
                "policy_kwargs": {
                    "features_extractor_kwargs": _TEMPORAL_STACK,
                    "hybrid_action_spec": "air_combat_hybrid_v1",
                },
            },
        },
        RenderStyle(literal_overrides=_LR_PLAIN_DECIMAL),
    ),
    # Stage 1: A3/A4 C2-ROE shaped probes (five-family HMoE surface).
    (
        "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_shaped_world_batch_probe_v1",
        _SCENARIO_STAGE1_C2_ROE,
        "probe",
        {
            "runtime": _WORLD_BATCH_RUNTIME,
            "env": _C2_ROE_V1_ENV,
            "wrappers": _STABLE_FLIGHT_RESIDUAL_WRAPPERS,
            "hyperparameters": {
                **_SHAPED_CURRICULUM_FIRST_EVENT,
                "policy_kwargs": {
                    "features_extractor_class": "TransformerExtractor",
                    **_FIVE_FAMILY_POLICY,
                },
            },
        },
        RenderStyle(literal_overrides=_LR_PLAIN_DECIMAL),
    ),
    (
        "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_shaped_world_batch_probe_v1",
        _SCENARIO_STAGE1_C2_ROE,
        "probe",
        {
            "runtime": _WORLD_BATCH_RUNTIME,
            "env": _C2_ROE_V1_TEMPORAL_ENV,
            "wrappers": _STABLE_FLIGHT_RESIDUAL_WRAPPERS,
            "hyperparameters": {
                **_SHAPED_CURRICULUM_FIRST_EVENT,
                "policy_kwargs": {
                    "features_extractor_kwargs": _TEMPORAL_STACK,
                    **_FIVE_FAMILY_POLICY,
                },
            },
        },
        RenderStyle(literal_overrides=_LR_PLAIN_DECIMAL),
    ),
    (
        "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_shaped_world_batch_probe_v1",
        _SCENARIO_STAGE1_C2_ROE,
        "probe",
        {
            "runtime": _WORLD_BATCH_RUNTIME,
            "env": _C2_ROE_V1_TEMPORAL_ENV,
            "wrappers": _STABLE_FLIGHT_RESIDUAL_WRAPPERS,
            "hyperparameters": {
                **_DEADLINE_FIRST_EVENT,
                "policy_kwargs": {
                    "features_extractor_kwargs": _TEMPORAL_STACK,
                    **_FIVE_FAMILY_POLICY,
                },
            },
        },
        RenderStyle(literal_overrides=_LR_PLAIN_DECIMAL),
    ),
    (
        "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_shaped_world_batch_probe_v1",
        _SCENARIO_STAGE1_C2_ROE,
        "probe",
        {
            "runtime": _WORLD_BATCH_RUNTIME,
            "env": _C2_ROE_V1_TEMPORAL_ENV,
            "wrappers": _STABLE_FLIGHT_RESIDUAL_WRAPPERS,
            "hyperparameters": {
                **_DEADLINE_FIRST_EVENT,
                "policy_kwargs": {
                    "features_extractor_kwargs": _TEMPORAL_STACK,
                    **_FIVE_FAMILY_POLICY,
                    "hybrid_event_head_lr_scale": 10.0,
                },
            },
        },
        RenderStyle(literal_overrides=_LR_PLAIN_DECIMAL),
    ),
    (
        "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_launch_window_shaped_world_batch_probe_v1",
        _SCENARIO_STAGE1_C2_ROE,
        "probe",
        {
            "runtime": _WORLD_BATCH_RUNTIME,
            "env": _C2_ROE_V1_TEMPORAL_ENV,
            "wrappers": _STABLE_FLIGHT_RESIDUAL_WRAPPERS,
            "hyperparameters": {
                **_DEADLINE_FIRST_EVENT,
                "first_event_launch_window_enabled": True,
                "first_event_launch_window_min_range_m": 8000.0,
                "first_event_launch_window_max_range_m": 30000.0,
                "first_event_launch_window_max_track_age_s": 5.0,
                "first_event_launch_window_min_window_age_steps": 32,
                "first_event_launch_window_prewindow_hold_weight": 0.3,
                "first_event_launch_window_early_accept_weight": 1.0,
                "policy_kwargs": {
                    "features_extractor_kwargs": _TEMPORAL_STACK,
                    **_FIVE_FAMILY_POLICY,
                    "hybrid_event_head_lr_scale": 10.0,
                },
            },
        },
        RenderStyle(literal_overrides=_LR_PLAIN_DECIMAL),
    ),
    (
        "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_event_credit_launch_window_shaped_world_batch_probe_v1",
        _SCENARIO_STAGE1_C2_ROE,
        "probe",
        {
            "runtime": _WORLD_BATCH_RUNTIME,
            "env": _C2_ROE_V1_TEMPORAL_ENV,
            "wrappers": _STABLE_FLIGHT_RESIDUAL_WRAPPERS,
            "hyperparameters": {
                **_EVENT_CREDIT_HYPERS,
                "policy_kwargs": {
                    "features_extractor_kwargs": _TEMPORAL_STACK,
                    **_FIVE_FAMILY_POLICY,
                    **_EVENT_CREDIT_POLICY_HEADS,
                },
            },
        },
        RenderStyle(literal_overrides=_LR_PLAIN_DECIMAL),
    ),
    (
        "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_event_credit_launch_window_state_completed_world_batch_probe_v1",
        _SCENARIO_STAGE1_C2_ROE,
        "probe",
        {
            "runtime": _WORLD_BATCH_RUNTIME,
            "env": _C2_ROE_V2_TEMPORAL_ENV,
            "wrappers": _STABLE_FLIGHT_RESIDUAL_WRAPPERS,
            "hyperparameters": {
                **_EVENT_CREDIT_HYPERS,
                "policy_kwargs": {
                    "features_extractor_kwargs": _TEMPORAL_STACK,
                    **_FIVE_FAMILY_POLICY,
                    **_EVENT_CREDIT_POLICY_HEADS,
                },
            },
        },
        RenderStyle(literal_overrides=_LR_PLAIN_DECIMAL),
    ),
    (
        "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_grouped_stopping_state_completed_world_batch_probe_v1",
        _SCENARIO_STAGE1_C2_ROE,
        "probe",
        {
            "total_timesteps": 8192,
            "save_freq": 2048,
            "runtime": _WORLD_BATCH_RUNTIME,
            "env": _C2_ROE_V2_TEMPORAL_ENV,
            "wrappers": _STABLE_FLIGHT_RESIDUAL_WRAPPERS,
            "hyperparameters": {
                **_EVENT_CREDIT_HYPERS,
                **_GROUPED_STOPPING_HYPERS,
                "policy_kwargs": {
                    "features_extractor_kwargs": _TEMPORAL_STACK,
                    **_FIVE_FAMILY_POLICY,
                    **_EVENT_CREDIT_POLICY_HEADS,
                    "stopping_head_lr_scale": 5.0,
                },
            },
        },
        RenderStyle(scalar_array_layout="expanded"),
    ),
    (
        "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_event_window_state_completed_world_batch_probe_v1",
        _SCENARIO_STAGE1_C2_ROE,
        "probe",
        {
            "total_timesteps": 8192,
            "save_freq": 2048,
            "runtime": _WORLD_BATCH_RUNTIME,
            "env": _C2_ROE_V2_TEMPORAL_ENV,
            "wrappers": _STABLE_FLIGHT_RESIDUAL_WRAPPERS,
            "hyperparameters": {
                **_EVENT_CREDIT_HYPERS,
                **_FIRE_BOUNDARY_HYPERS,
                "policy_kwargs": {
                    "features_extractor_kwargs": _TEMPORAL_STACK,
                    **_FIVE_FAMILY_POLICY,
                    **_M3S2_EVENT_HEADS,
                },
            },
        },
        RenderStyle(scalar_array_layout="expanded"),
    ),
    # Stage 2: evasive-fighter continuation of the M3-S2 fire-boundary owner.
    (
        "air_combat_1v1_stage2_evasive_fighter_c2_roe_hybrid_temporal_event_window_state_completed_world_batch_probe_v1",
        _SCENARIO_STAGE2_C2_ROE,
        "probe",
        {
            "total_timesteps": 8192,
            "save_freq": 2048,
            "runtime": {**_WORLD_BATCH_RUNTIME, "observation_return_mode": "view"},
            "env": _C2_ROE_V2_TEMPORAL_ENV,
            "wrappers": _STABLE_FLIGHT_RESIDUAL_WRAPPERS,
            "hyperparameters": {
                **_EVENT_CREDIT_HYPERS,
                **_FIRE_BOUNDARY_HYPERS,
                "policy_kwargs": {
                    "features_extractor_kwargs": {**_TEMPORAL_STACK, "use_checkpointing": False},
                    **_FIVE_FAMILY_POLICY,
                    **_M3S2_EVENT_HEADS,
                },
            },
        },
        RenderStyle(scalar_array_layout="expanded", literal_overrides=_LR_PLAIN_DECIMAL),
    ),
)


def build_registry() -> ExperimentRegistry:
    """Build a fresh, fully validated registry of the air-combat matrix."""
    registry = ExperimentRegistry()
    registry.register_config_base(CONFIG_BASE_ID, CONFIG_BASE)
    for protocol in EVALUATION_PROTOCOLS:
        registry.register_evaluation_protocol(protocol)
    for experiment_id, scenario, protocol_name, delta, _ in _ENTRY_SPECS:
        registry.register_experiment(
            Experiment(
                experiment_id=experiment_id,
                scenario=ScenarioRef(scenario),
                config=ConfigComposition(CONFIG_BASE_ID, delta),
                seeds=SeedSpec(),
                evaluation_protocol=protocol_name,
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
