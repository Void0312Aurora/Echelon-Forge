export const DEFAULT_PROFILE = Object.freeze({
  profile_id: 'builtin.default_compatibility',
  profile_version: '1.0.0',
  request_id: 'default.experiment',
  request_version: '1.0.0',
  contract_versions: Object.freeze({
    composition: '1.0.0',
    content: '1.0.0',
    runtime: '1.0.0',
    stage: '1.0.0',
  }),
  intent: Object.freeze({
    evaluation_id: 'default.evaluation',
    policy_id: 'default.policy',
    simulation_id: 'default.simulation',
  }),
  required_capabilities: Object.freeze([
    'deterministic.step',
    'runtime.world_batch.cpu',
  ]),
  required_policies: Object.freeze([
    'native_step_authority',
    'no_mid_episode_truth_reconfiguration',
  ]),
  configuration: Object.freeze({
    seed: 42,
    time_step_ns: 16666667,
  }),
});
