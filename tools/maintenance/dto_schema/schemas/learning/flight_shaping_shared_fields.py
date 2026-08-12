"""Declarative DTO schema parsed from src/core/mission/runtime/detail/flight_shaping_shared_fields.inc."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
  '// X-macro list of the config-static flight-shaping fields shared between\n'
  '// FlightShapingRuntimeInputs (core/mission/runtime/reward_runtime.h) and\n'
  '// StepEvaluationBatchConfig (core/mission/episode/execution_episode_batch_prepare.h).\n'
  '//\n'
  '// Consumers define EF_FLIGHT_SHAPING_FIELD(type, name, default_value) before\n'
  "// including this file; the macro is #undef'd here after expansion. Expansion\n"
  '// sites: both struct definitions, the batch-prepare config->inputs copy, and\n'
  '// the FlightShapingRuntimeInputs Python bindings.\n'
  '//\n'
  '// Field order is load-bearing: it fixes the member layout of both structs.\n'
  '// target_altitude_m / target_speed_mps also exist on both structs but live in\n'
  '// the mission-dynamic block of FlightShapingRuntimeInputs, so they stay\n'
  '// hand-written to preserve member order.\n'
  '\n'
)
FILE_FOOTER = (
  '\n'
  '#undef EF_FLIGHT_SHAPING_FIELD\n'
)


SCHEMA = DtoSchema(
  name='flight_shaping_shared_fields',
  output_path='src/core/mission/runtime/detail/flight_shaping_shared_fields.inc',
  file_header=FILE_HEADER,
  fields=(
    Field(name='altitude_progress_weight', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='speed_progress_weight', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='speed_progress_negative_weight', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='stationary_penalty', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='stationary_grace_steps', cpp_type='int', default='20', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='stationary_speed_threshold_mps', cpp_type='double', default='5.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='stationary_alt_threshold_m', cpp_type='double', default='5.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='liftoff_bonus', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='liftoff_speed_threshold_mps', cpp_type='double', default='80.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='liftoff_alt_threshold_m', cpp_type='double', default='5.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='rotation_reward_weight', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='rotation_speed_threshold_mps', cpp_type='double', default='80.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='rotation_alt_threshold_m', cpp_type='double', default='5.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='rotation_pitch_cap_deg', cpp_type='double', default='15.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='rotation_overpitch_penalty_weight', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='gear_up_bonus', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='gear_up_bonus_min_alt_agl_m', cpp_type='double', default='50.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='roll_stability_weight', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='heading_error_weight', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='heading_hold_deadband_deg', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='heading_hold_bonus', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='waypoint_turn_heading_relief_max', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='altitude_error_weight', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='altitude_error_min_alt_m', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='altitude_error_target_m', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='altitude_error_deadband_m', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='altitude_error_norm_m', cpp_type='double', default='100.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='altitude_error_power', cpp_type='double', default='1.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='altitude_error_clip', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='altitude_hold_bonus', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='speed_error_weight', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='speed_error_min_ias_mps', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='speed_error_target_mps', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='speed_error_deadband_mps', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='speed_error_norm_mps', cpp_type='double', default='30.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='speed_error_power', cpp_type='double', default='1.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='speed_error_clip', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='speed_hold_bonus', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='roll_abs_weight', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='roll_abs_deadband_deg', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='roll_abs_norm_deg', cpp_type='double', default='30.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='roll_abs_power', cpp_type='double', default='1.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='pitch_abs_weight', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='pitch_abs_deadband_deg', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='pitch_abs_norm_deg', cpp_type='double', default='20.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='pitch_abs_power', cpp_type='double', default='1.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='yaw_rate_abs_weight', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='yaw_rate_abs_deadband_deg_s', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='yaw_rate_abs_norm_deg_s', cpp_type='double', default='10.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='yaw_rate_abs_power', cpp_type='double', default='1.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='beta_abs_weight', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='beta_abs_deadband_deg', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='beta_abs_norm_deg', cpp_type='double', default='10.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='beta_abs_power', cpp_type='double', default='1.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='g_deviation_weight', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='g_deviation_deadband', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='g_deviation_norm', cpp_type='double', default='0.5', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='g_deviation_power', cpp_type='double', default='1.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='g_deviation_min_alt_agl_m', cpp_type='double', default='5.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='speed_reward_weight', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='runway_centerline_penalty_min_ias_mps', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='runway_centerline_penalty_max_ias_mps', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='runway_centerline_m_penalty_weight', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='runway_centerline_m_deadband_m', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='runway_centerline_m_norm_m', cpp_type='double', default='5.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='runway_centerline_m_power', cpp_type='double', default='2.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='runway_centerline_m_clip', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='runway_centerline_penalty_weight', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='runway_centerline_safe_frac', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='runway_centerline_penalty_power', cpp_type='double', default='2.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='runway_centerline_barrier_weight', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='runway_centerline_barrier_clip_frac', cpp_type='double', default='0.995', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='departure_centerline_max_alt_agl_m', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='departure_centerline_m_penalty_weight', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='departure_centerline_m_deadband_m', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='departure_centerline_m_norm_m', cpp_type='double', default='20.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='departure_centerline_m_power', cpp_type='double', default='2.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='departure_centerline_m_clip', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='departure_centerline_reward_weight', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='departure_centerline_reward_band_m', cpp_type='double', default='1.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='departure_track_error_weight', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='departure_track_error_deadband_deg', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='departure_track_error_norm_deg', cpp_type='double', default='10.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='departure_track_error_power', cpp_type='double', default='2.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='departure_track_error_clip', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='departure_track_reward_weight', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='departure_track_reward_band_deg', cpp_type='double', default='10.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='alignment_reward_weight', cpp_type='double', default='0.0', group='EF_FLIGHT_SHAPING_FIELD'),
    Field(name='mission_alignment_min_alt_m', cpp_type='double', default='120.0', group='EF_FLIGHT_SHAPING_FIELD'),
  ),
  file_footer=FILE_FOOTER,
)
