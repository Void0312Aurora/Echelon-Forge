// Shared frontend constants for the unified viz app.

// --- 3D scene ---
export const SCENE_BG = 0x060b11;
export const GRID_COLOR = 0x24455c;
export const GRID_COLOR_MINOR = 0x122334;
export const GRID_MIN_SIZE = 150000;
export const GRID_MAX_SIZE = 400000;
export const GRID_STEP = 50000;

// --- Trails / sampling ---
export const MAX_TRAIL_POINTS_PER_UNIT = 6000;
export const MAX_TACTICAL_TRAIL_POINTS_PER_UNIT = 360;
export const MAX_UNIT_VISUAL_SAMPLES = 8;

// --- Visual interpolation between state frames ---
export const VISUAL_INTERPOLATION_MIN_DELAY_MS = 45.0;
export const VISUAL_INTERPOLATION_MAX_DELAY_MS = 950.0;
export const VISUAL_INTERPOLATION_DELAY_MULT = 1.15;
export const VISUAL_EXTRAPOLATION_LIMIT_MS = 180.0;

// --- Render throttles ---
export const TACTICAL_RENDER_INTERVAL_MS = 1000.0 / 30.0;
// In MAP mode the 3D scene is only a faint underlay (opacity 0.16), so it is
// rendered every N animation frames instead of every frame.
export const MAP_MODE_3D_FRAME_INTERVAL = 3;

// --- Simulation speed steps ---
export const SPEED_STEPS = [0.05, 0.1, 0.25, 0.5, 1, 2, 4, 8, 16];
