<!-- Machine-translated draft generated on 2026-05-18 from docs/task/viz/viz_unified_entry_session_profile_plan_20260516.zh.md. Review before treating this file as authoritative. -->

# Visual Unified Entry & Sessionization Refactoring Freeze Plan

Status: `2026-05-16` frozen design version.

Related files:

- [Current visualization main entry](../../../examples/viz/viz_runner.py)
- [Current web service skeleton](../../../examples/viz/web_viz/server.py)
- [Current frontend template](../../../examples/viz/web_viz/templates/index.html)
- [Existing legacy config example departure](../../../examples/viz/configs/departure.json)
- [Existing legacy config example landing](../../../examples/viz/configs/landing.json)
- [Current naval minimal scenario](../../../scenarios/naval/ddg51_take1_screen_contact_report_v1.json)
- [Naval realism layering checklist and next steps](../naval/naval_realism_layering_and_next_step_plan_20260516.zh.md)

Document positioning:

- This document is used to freeze a relatively large-scale refactoring plan around `examples/viz`.
- The goal of this round is not to continue stacking temporary buttons on the existing `viz_runner.py`, but to transform the visualization into a structure of "permanent application + replaceable sessions + configuration layering".
- This document only freezes the architecture, boundaries, configuration layers, and implementation order. It does not authorize extending new naval semantics or realism parameters directly in this round.

## 1. Problem Definition

The current visualization system can already undertake relatively rich presentation tasks, especially in naval scenarios:

1. Full-screen tactical 2D view;
2. 3D scene and tracking perspective;
3. Sensor rings, data links, tracks and other tactical overlays;
4. Loading of ship and aircraft models;
5. Continuous socket push of simulation state.

But its usage is still at the stage of "one command line corresponds to one simulation process".

The direct problems this brings are:

1. Changing scenarios, models, speed strategies, training configurations requires exiting and restarting the entire process;
2. The frontend already has strong UI capabilities, but the backend entry is still determined by the command line, causing the interaction center to be outside the application;
3. Visual rules such as model mapping, orientation correction, scale, waterline offset are hard-coded in frontend scripts, and subsequent ship type expansion will quickly spiral out of control;
4. The old `examples/viz/configs/*.json` only cover very narrow startup information and cannot fully assume the responsibility of complete visualization runtime configuration;
5. Visualization convenience configuration, simulation realism configuration, and training controller configuration currently lack clear boundaries.

Therefore, the real problem to be solved in this round is not "add another startup script", but:

**Evolve the current visualization system from a one-shot runner to a stable visualization application.**

## 2. Current Structure Assessment

Based on the current state of [viz_runner.py](../../../examples/viz/viz_runner.py) and [index.html](../../../examples/viz/web_viz/templates/index.html), the current structure has the following characteristics.

### 2.1 Current Frontend is Close to an Application Shell

The frontend already has:

1. Switching between full-screen tactical view and 3D view;
2. Unit list, focus unit, speed control, pause control;
3. Model loading, trajectory, tactical overlay drawing;
4. Wide-area scale display capability for naval scenarios.

This shows that the frontend is not the main bottleneck in this round; instead, it is already sufficient to take on the role of "UI shell after unified entry".

### 2.2 Current Backend Ties Multiple Responsibilities Together

`viz_runner.py` currently simultaneously takes on:

1. `argparse` command-line parsing;
2. Loading scenario, training configuration, controller;
3. env initialization;
4. Simulation loop;
5. Socket event handling;
6. Flask service startup;
7. Web page rendering.

This means switching a scenario essentially requires restarting the entire application.

### 2.3 Current Configuration Layer is Insufficient to Support Debugging Workflow

Existing `examples/viz/configs/departure.json` and `landing.json` are more like legacy demo configurations:

1. Can specify env module/class and model path;
2. Only cover very few viz settings;
3. Do not support asset mapping, default views, overlays, session behavior, and other more complete visualization configurations.

### 2.4 Current Asset Rules Are in the Wrong Layer

The current frontend already has hard-coded:

1. Ship platform identification;
2. Model file paths;
3. Orientation correction;
4. Scale;
5. Waterline offset;
6. Chase camera offset;
7. Semantic explanations for certain "substitute models".

Such rules essentially belong to an "asset registry" or "visualization profile" and should not continue to be scattered in frontend logic.

## 3. Goals

The goals of this refactoring round are:

1. Establish a unified and stable visualization startup entry;
2. Enable the web service to persist without needing a full restart when switching scenarios;
3. Decouple the simulation session from the application shell, supporting in-app loading, reloading, and resetting;
4. Establish an independent `viz profile` configuration layer;
5. Establish an independent asset registry layer for managing model mapping and correction parameters;
6. Keep "scenario realism" and "visualization convenience" layered, avoiding mixed writing.

## 4. Non-Goals

This round explicitly does not:

1. Promote new naval tactical semantics in this document;
2. Expand realistic implementations of weapons, damage, sinking, electronic warfare, etc. in this document;
3. Require full multi-session concurrency at this time;
4. Require hot-reloading of resources or editor-style scenario editing at this time;
5. Require a complete rewrite of the frontend into a new framework application.

This round allows:

1. Refactoring the entry and runtime structure of `examples/viz`;
2. Adding `viz app / viz session / viz profile / asset registry` modules;
3. Gradually migrating current frontend asset rules;
4. Establishing a stable foundation for future shared visualization shell for naval and air combat.

## 5. Recommended Architecture

This round recommends converging to a three-layer main structure, plus one configuration support layer.

### 5.1 Permanent Application Layer `viz_app`

Responsibilities:

1. Start Flask / SocketIO;
2. Provide unified web entry;
3. Provide configuration list and session control interface;
4. Hold a reference to the current active session.

It does not directly take on:

1. `argparse`-style runtime strategy distribution;
2. Long-term state logic for a specific scenario;
3. Platform asset identification and frontend geometry correction rules.

Suggested entry form:

```text
examples/viz/run_viz.py
```

Its responsibilities are:

1. Start the persistent viz app;
2. Open the unified browsing entry;
3. Let UI or profile trigger subsequent session loading.

### 5.2 Simulation Session Layer `viz_session`

Responsibilities:

1. Load scenario;
2. Load model or scripted controller;
3. Build env;
4. Manage sim loop;
5. Generate `map_setup / nav_setup / state_update`;
6. Support `start / pause / resume / reset / reload / stop`.

This layer is the core split point of this round.

The main content it needs to extract from the current `viz_runner.py` includes:

1. Training configuration loading;
2. env initialization and mode determination;
3. Simulation step loop;
4. mission / nav / tactical state extraction;
5. Termination reset strategy.

### 5.3 Visualization Configuration Layer `viz_profile`

`viz_profile` is responsible for describing:

1. Which scenario to start;
2. Whether to load model;
3. Whether to use scripted controller;
4. Default speed and default view mode;
5. Whether to auto-start, whether to pause at terminal;
6. Default overlay toggles;
7. Asset mapping scheme;
8. Optional focus unit, default zoom, and other UI preferences.

It is not responsible for describing:

1. Real displacement, speed, radar, etc., world parameters of ships;
2. Complete hyperparameters of training itself;
3. Scenario semantic ontology.

### 5.4 Asset Registry Layer `asset_registry`

This layer is responsible for mapping "platform semantics" to "visual models and correction parameters".

Recommended fields at least include:

1. Match keys:
   - `platform_type`
   - `name_patterns`
   - `service_profile`
   - `unit_type`
2. Asset fields:
   - `asset_path`
   - `label`
   - `substitute_for`
   - `realism_note`
3. Correction fields:
   - `scale`
   - `yaw_correction_deg`
   - `waterline_offset_m`
   - `chase_offset`
4. Optional controls:
   - `show_in_2d_as`
   - `show_sensor_ring`
   - `render_priority`

The value of this layer lies in:

1. Making model substitution relationships honestly visible;
2. Allowing ship type expansion without relying on frontend hard-coding;
3. Making orientation correction and scale correction configurable.

## 6. Configuration Layering Principles

This round recommends clearly splitting the visualization-related data sources into four layers:

1. `scenario`
   - World, entities, missions, realism parameters;
   - Source of simulation realism.

2. `train_config`
   - Controller training and inference information;
   - Source of model runtime constraints.

3. `viz_profile`
   - How this visualization starts, what default view to use;
   - Source of debugging workflow.

4. `asset_registry`
   - How platforms map to models and visual corrections;
   - Source of visual presentation.

The most important constraint here is:

**Do not stuff realism parameters into `viz_profile` for UI convenience, and do not write visual substitution rules back into scenario.**

## 7. UI Design Suggestions

The current naval visualization already clearly prioritizes tactical view, so the new unified entry UI should not be designed as a traditional admin panel. Instead, it should maintain the structure where "the main screen is the tactical map".

Suggested layout:

1. **Full-screen tactical view**
   - As the default main view;
   - When opening the app, first see the map, not a form page.

2. **Lightweight startup/session control bar**
   - For selecting profile, scenario, asset set;
   - Provide `Start / Reload / Reset / Stop`;
   - Display current session status.

3. **Collapsible information area**
   - For displaying unit list, focus information, model substitution notes, debug status.

4. **3D view switch**
   - Keep as auxiliary view;
   - Must not replace the tactical main view.

## 8. Backend Interface Suggestions

Currently exists:

1. `start_sim`
2. `pause_sim`
3. `resume_sim`
4. `set_speed`

After unified entry, it is recommended to complete into two categories.

### 8.1 Listing Interfaces

1. `list_profiles`
2. `list_scenarios`
3. `list_asset_sets`
4. `get_session_status`

### 8.2 Session Control Interfaces

1. `load_profile`
2. `start_session`
3. `pause_session`
4. `resume_session`
5. `reset_session`
6. `reload_session`
7. `stop_session`

This way, after frontend starts, it can first get the lists, then choose to load, instead of being bound to a scenario that was fixed at startup when entering the page.

## 9. Suggested Directory Structure

It is recommended to gradually evolve under `examples/viz` to a structure like:

```text
examples/viz/
  run_viz.py
  app/
    server.py
    session_manager.py
    routes.py
    socket_handlers.py
  runtime/
    viz_session.py
    session_factory.py
    state_extractors.py
  profiles/
    naval_debug_minimal.json
    air_departure_debug.json
  assets/
    registry/
      naval_surface.json
      air_fixedwing.json
  web_viz/
    templates/
    static/
```

The key point here is not that directory names must be exactly the same, but that structural boundaries are clear:

1. `app/` manages the application shell;
2. `runtime/` manages simulation sessions;
3. `profiles/` manages viz profiles;
4. `assets/registry/` manages model mapping and corrections;
5. `web_viz/` still mainly hosts web resources.

## 10. Phased Implementation Suggestions

This round recommends proceeding in the following order to avoid rework while editing.

### WP-V1: Extract Session Layer

Goal:

1. Extract `VizSession` from `viz_runner.py`;
2. Make the "simulation loop" no longer directly depend on `main()`;
3. First achieve in-app creation, destruction, and reset.

Freeze scope:

- [examples/viz/viz_runner.py](../../../examples/viz/viz_runner.py)
- New `runtime/viz_session.py`

Not done at this time:

1. Do not require the frontend UI to immediately complete all switching controls;
2. Do not require asset registry to be fully migrated at the same time.

### WP-V2: Establish Permanent Application Entry

Goal:

1. Add unified entry `run_viz.py`;
2. Web service persists;
3. First page open does not strongly depend on a CLI scenario.

Freeze scope:

- New `app/` layer
- Adjust startup logic

### WP-V3: Introduce `viz_profile`

Goal:

1. Establish stable configuration for startup selection;
2. Replace the workflow of "manually typing a string of commands each time";
3. Support different default views and debug preferences for naval and air combat.

Freeze scope:

- New `profiles/*.json`
- Add profile loader

Current progress (`2026-05-16` already implemented):

1. First `viz_profile` loader added:
   - [examples/viz/app/profile_loader.py](../../../examples/viz/app/profile_loader.py)
2. First batch of naval profiles added:
   - [examples/viz/profiles/naval_ddg51_contact_report_debug.json](../../../examples/viz/profiles/naval_ddg51_contact_report_debug.json)
   - [examples/viz/profiles/naval_ddg51_closing_contact_debug.json](../../../examples/viz/profiles/naval_ddg51_closing_contact_debug.json)
3. Unified entry now supports:
   - CLI preload `--profile`
   - HTTP `GET /api/viz/profiles`
   - HTTP `POST /api/viz/load_profile`
   - Socket `viz_load_profile`
   - `RELOAD` under profile session
4. Frontend lightweight control bar now supports:
   - Profile dropdown
   - `LOAD PROFILE`
   - Current session / scenario / profile status display
   - Profile-driven default UI preferences: `presentation_mode` / `camera_mode` / `tactical_zoom`

Still explicitly not done in this phase:

1. `asset_registry` not yet introduced;
2. Profile does not carry realism world parameters;
3. Profile currently only covers session startup and a few UI defaults, not full overlay toggles or model registration.

### WP-V4: Introduce `asset_registry`

Goal:

1. Migrate hard-coded model mapping and correction parameters from frontend;
2. Give honest annotations for temporary substitute models;
3. Provide maintainable path for future ship type expansion.

Freeze scope:

- Asset judgment logic in `index.html`
- New asset registry JSON or Python loader

Current progress (`2026-05-16` first version already implemented):

1. First asset registry loader added:
   - [examples/viz/app/asset_registry.py](../../../examples/viz/app/asset_registry.py)
2. First registry data file added:
   - [examples/viz/assets/registry/default.json](../../../examples/viz/assets/registry/default.json)
3. Current registry covers:
   - Basic visualization assets for `F-16`
   - `DDG-51` destroyer assets with orientation/tracking corrections
   - Temporary `USNS Patuxent` substitute asset for `T-AKE-1` with honest annotation
4. Unified entry currently:
   - Loads `default` registry by default
   - Profile can explicitly specify `asset_registry`
   - Distributes current registry to frontend via state flow
5. Frontend now changed to:
   - Use registry for unit matching, model path, yaw correction, scale, waterline offset, chase offset
   - Display substitute model annotations in unit list instead of burying this semantics in comments
   - Determine unit 2D symbol type and sensor ring display in tactical map according to registry

Still explicitly not done in this phase:

1. Current registry only covers verified minimal naval/air assets, not a complete ship library;
2. No finer-grained layer toggle editor yet;
3. `show_in_2d_as` currently only covers unified entry tactical map, not all future views.

### WP-V5: Integrate UI Internal Loader

Goal:

1. Select profile / scenario / asset set within the application;
2. Support reload / reset / stop;
3. Keep tactical map as the main working interface.

Freeze scope:

- [examples/viz/web_viz/templates/index.html](../../../examples/viz/web_viz/templates/index.html)
- New listing and session control events

Current progress (`2026-05-16` already implemented):

1. Unified entry now supports in-app selection and loading of:
   - `profile`
   - `scenario`
   - `asset set`
2. Currently integrated control events include:
   - `viz_load_profile`
   - `viz_load_session`
   - `viz_load_asset_registry`
   - `viz_reload_session`
   - `viz_stop_session`
3. Currently integrated listing interfaces include:
   - `GET /api/viz/profiles`
   - `GET /api/viz/scenarios`
   - `GET /api/viz/asset_registries`
   - `GET /api/viz/assets`
4. After `STOP`, unified entry retains the current profile / asset set selection semantics for repeated debugging, instead of forcibly clearing the entire working context.
5. Unified entry has been fully verified through:
   - `UNLOADED -> LOAD PROFILE -> READY -> LOAD ASSET SET -> START -> RUNNING -> STOP -> UNLOADED`

Phase closing assessment:

1. `WP-V4` completed first usable closure;
2. `WP-V5` completed first unified entry workflow closure;
3. Subsequent new work should default to either "extend registry content" or "clean up runtime exit path noise", rather than reverting to frontend hard-coded asset logic.

## 11. Realism and Engineering Boundaries

There is one principle that must be adhered to in this round:

**The refactoring of the visualization system is for more honest and efficient observation of simulations, not for using UI configuration to cover up realism gaps.**

Therefore:

1. `scenario` remains the primary source of realism parameters;
2. Temporary substitute models must be explicitly annotated through `asset_registry`;
3. Tactical map overlays, radar circles, shared links, etc. in naval combat should continue to be understood as "observation presentation layer", not automatically equivalent to "higher fidelity world modeling".

This boundary is especially important for subsequent naval combat progress.

## 12. Current Freeze Conclusion

The correct direction for refactoring the current visualization system is not to continue adding switches to `viz_runner.py`, but to:

1. Split it into "permanent application layer + replaceable session layer";
2. Introduce independent `viz_profile`;
3. Introduce independent `asset_registry`;
4. Keep the tactical 2D main view as the center of naval debugging;
5. Replace the workflow of "restarting the entire process to switch scenarios" with "reload session within application".

Before entering implementation, the next step should default to proceeding in the order of `WP-V1 -> WP-V2 -> WP-V3 -> WP-V4 -> WP-V5`, rather than making big parallel changes across all layers.
