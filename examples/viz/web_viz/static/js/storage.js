// Local persistence for display-only UI preferences (language, docks,
// workspace, and per-workspace layer toggles). Session/scenario state is
// never persisted here; profiles remain the authoritative startup source
// and simply overwrite these values when applied.

const STORAGE_KEY = 'ef-viz-ui-v1';

export function loadUiPrefs() {
    try {
        const raw = window.localStorage.getItem(STORAGE_KEY);
        const parsed = raw ? JSON.parse(raw) : null;
        return parsed && typeof parsed === 'object' ? parsed : {};
    } catch (err) {
        // Private mode / disabled storage: behave as if nothing was saved.
        return {};
    }
}

export function saveUiPrefs(patch) {
    if (!patch || typeof patch !== 'object') return;
    try {
        const merged = { ...loadUiPrefs(), ...patch };
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(merged));
    } catch (err) {
        // Ignore quota/privacy errors; persistence is best-effort.
    }
}
