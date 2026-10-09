"""Check the status observed by shell orchestration, including caught failures."""
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]


def run_entry(entry, *args):
    return subprocess.run([sys.executable, '-B', str(ROOT / entry), *map(str, args)],
                          cwd=ROOT, capture_output=True, text=True)


@pytest.mark.parametrize('entry', ['train.py', 'evaluate.py'])
def test_missing_scenario_fails(entry, tmp_path):
    args = ['--scenario', tmp_path / 'missing.json']
    if entry == 'evaluate.py':
        args += ['--model', 'missing.zip']
    result = run_entry(entry, *args)
    assert result.returncode != 0
    assert 'Scenario file not found' in result.stdout


@pytest.mark.parametrize('entry', ['train.py', 'evaluate.py'])
@pytest.mark.parametrize('config', ['missing', 'malformed'])
def test_bad_config_fails(entry, config, tmp_path):
    scenario = tmp_path / 'scenario.json'
    scenario.write_text('{}', encoding='utf-8')
    path = tmp_path / 'config.json'
    if config == 'malformed':
        path.write_text('{', encoding='utf-8')
    args = ['--scenario', scenario, '--train_config', path]
    if entry == 'evaluate.py':
        args += ['--model', 'missing.zip']
    assert run_entry(entry, *args).returncode != 0


@pytest.mark.parametrize('model_failure', [True, False])
def test_evaluation_load_failure_and_success_in_subprocess(model_failure, tmp_path):
    pytest.importorskip('stable_baselines3')
    scenario = tmp_path / 'scenario.json'
    scenario.write_text('{}', encoding='utf-8')
    # Keep this process-status test independent of native simulation. The maintained
    # train-entry smoke separately runs the real runtime and test-only checkpoint.
    script = '''
import sys, numpy as np, gymnasium as gym
import evaluate
class Env(gym.Env):
    observation_space = gym.spaces.Box(-1., 1., (1,), dtype=np.float32)
    action_space = observation_space
    def reset(self, **kwargs): return np.zeros(1, np.float32), {}
    def step(self, action): return np.zeros(1, np.float32), 1., True, False, {}
class Policy:
    def predict(self, obs, **kwargs): return np.zeros((1, 1)), None
def load(*args, **kwargs):
    if FAILURE: raise ValueError('broken checkpoint')
    return Policy()
evaluate._build_evaluation_env = lambda *a, **kw: Env()
evaluate.load_sb3_policy = load
sys.argv = ['evaluate.py', '--scenario', SCENARIO, '--model', 'broken.zip', '--episodes', '1']
raise SystemExit(evaluate.main())
'''.replace('FAILURE', repr(model_failure)).replace('SCENARIO', repr(str(scenario)))
    result = subprocess.run([sys.executable, '-B', '-c', script], cwd=ROOT,
                            capture_output=True, text=True)
    assert result.returncode == (1 if model_failure else 0), result.stdout + result.stderr
    assert ('Error loading model' if model_failure else 'EVALUATION SUMMARY') in result.stdout
