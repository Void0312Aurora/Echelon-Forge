# Examples

Organized examples for demos, visualization, scenarios, and training helpers.

## Structure
- agents/: scripted agent helpers
- demos/: simple interactive demos (chase/evasion/missile/kinematics)
- gym/: gymnasium environments
- legacy/: older or known-bad demos kept for reference
- scenarios/: scenario runner utilities
- training/: training smoke tests
- viz/: visualization demos and web assets
  - web_viz/: Flask+SocketIO UI assets and server

## Usage
- Scenario runner: `python examples/scenarios/run_scenario.py <scenario.json>`
- Scenario runner (by id): `python examples/scenarios/run_scenario.py two_fighters`
- Web perception demo: `python examples/viz/perception_viz.py`
- Scenario GIF renderer: `python examples/viz/render_scenario_gif.py logs/two_fighters_YYYYMMDD_HHMMSS/log.jsonl logs/two_fighters_YYYYMMDD_HHMMSS/playback.gif`
- Logs default to `logs/<scenario>_<timestamp>/` when output config is set.
