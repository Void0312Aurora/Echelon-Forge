// Responsive shell layout: dock visibility, CSS variable insets, and the
// tactical-map padding derived from the current chrome measurements.

import { dom } from './dom.js';
import { vizState } from './store.js';
import { drawTacticalView } from './tactical-map.js';
import { saveUiPrefs } from './storage.js';

function applyResponsiveDockDefaults() {
    if (vizState.dockUserTouched) return;
    vizState.dockState.left = window.innerWidth >= 960;
    vizState.dockState.right = window.innerWidth >= 1180;
}

function measureLayoutPanels() {
    const measure = (element, fallbackWidth = 0, fallbackHeight = 0) => {
        if (!element) return { width: fallbackWidth, height: fallbackHeight };
        const rect = element.getBoundingClientRect();
        return {
            width: Math.max(fallbackWidth, Math.round(rect.width || element.offsetWidth || 0)),
            height: Math.max(fallbackHeight, Math.round(rect.height || element.offsetHeight || 0)),
        };
    };
    const leftDockBox = measure(dom.leftDockPanel, 348, 0);
    const rightDockBox = measure(dom.rightDockPanel, 324, 0);
    const controlsHelpBox = measure(dom.controlsHelpPanel, 340, 0);
    const uiControlsBox = measure(dom.uiControlsPanel, 220, 0);
    const topbarHeight = vizState.mapOnlyMode ? 0 : (dom.vizMenubar?.offsetHeight || 50);
    return {
        viewportWidth: window.innerWidth,
        viewportHeight: window.innerHeight,
        gutter: 12,
        topOffset: topbarHeight + 12,
        leftDockWidth: leftDockBox.width,
        leftDockHeight: leftDockBox.height,
        rightDockWidth: rightDockBox.width,
        rightDockHeight: rightDockBox.height,
        controlsHelpWidth: controlsHelpBox.width,
        controlsHelpHeight: controlsHelpBox.height,
        uiControlsWidth: uiControlsBox.width,
        uiControlsHeight: uiControlsBox.height,
    };
}

function resolveLayoutMode(measurements) {
    if (measurements.viewportWidth < 860 || measurements.viewportHeight < 560) return 'narrow';
    if (measurements.viewportWidth < 1180) return 'compact';
    return 'wide';
}

function applyAutoLayout(mode, measurements) {
    const layoutState = vizState.layoutState;
    const dockState = vizState.dockState;
    const rootStyle = document.documentElement.style;
    const gutter = measurements.gutter;
    if (vizState.mapOnlyMode) {
        const topOffset = 0;
        const inset = 16;
        rootStyle.setProperty('--viz-top-offset', `${topOffset}px`);
        rootStyle.setProperty('--left-dock-width', `${measurements.leftDockWidth || 348}px`);
        rootStyle.setProperty('--right-dock-width', `${measurements.rightDockWidth || 324}px`);
        rootStyle.setProperty('--map-left-inset', `${inset}px`);
        rootStyle.setProperty('--map-right-inset', `${inset}px`);
        rootStyle.setProperty('--map-bottom-inset', `${inset}px`);
        rootStyle.setProperty('--controls-help-bottom', `${inset}px`);
        document.documentElement.dataset.layoutMode = 'map-only';
        document.documentElement.dataset.leftDock = 'closed';
        document.documentElement.dataset.rightDock = 'closed';

        for (const toggle of [dom.btnToggleLeft, dom.btnToggleRight]) {
            toggle?.classList.remove('active');
            toggle?.setAttribute('aria-pressed', 'false');
        }
        if (dom.leftDockPanel) {
            dom.leftDockPanel.setAttribute('aria-hidden', 'true');
            dom.leftDockPanel.inert = true;
        }
        if (dom.rightDockPanel) {
            dom.rightDockPanel.setAttribute('aria-hidden', 'true');
            dom.rightDockPanel.inert = true;
        }

        layoutState.mode = 'map-only';
        layoutState.measurements = {
            ...measurements,
            leftInset: inset,
            rightInset: inset,
            bottomInset: inset,
            topOffset,
        };
        return;
    }
    const topOffset = measurements.topOffset;
    const overlayDockMode = mode === 'narrow';
    const leftDockWidth = Math.max(300, Math.min(380, measurements.leftDockWidth || 348));
    const rightDockWidth = Math.max(280, Math.min(360, measurements.rightDockWidth || 324));
    const leftInset = (!overlayDockMode && dockState.left) ? leftDockWidth + gutter * 2 : gutter + 12;
    const rightInset = (!overlayDockMode && dockState.right) ? rightDockWidth + gutter * 2 : gutter + 12;
    const controlsHelpBottom = mode === 'narrow' ? 10 : gutter;
    const controlsHeight = dom.controlsHelpPanel && getComputedStyle(dom.controlsHelpPanel).display !== 'none'
        ? Math.max(0, measurements.controlsHelpHeight || 0)
        : 0;
    const bottomInset = Math.max(56, controlsHeight + controlsHelpBottom + gutter);

    rootStyle.setProperty('--viz-top-offset', `${topOffset}px`);
    rootStyle.setProperty('--left-dock-width', `${leftDockWidth}px`);
    rootStyle.setProperty('--right-dock-width', `${rightDockWidth}px`);
    rootStyle.setProperty('--map-left-inset', `${leftInset}px`);
    rootStyle.setProperty('--map-right-inset', `${rightInset}px`);
    rootStyle.setProperty('--map-bottom-inset', `${bottomInset}px`);
    rootStyle.setProperty('--controls-help-bottom', `${controlsHelpBottom}px`);
    document.documentElement.dataset.layoutMode = mode;
    document.documentElement.dataset.leftDock = dockState.left ? 'open' : 'closed';
    document.documentElement.dataset.rightDock = dockState.right ? 'open' : 'closed';

    dom.btnToggleLeft?.classList.toggle('active', dockState.left);
    dom.btnToggleRight?.classList.toggle('active', dockState.right);
    dom.btnToggleLeft?.setAttribute('aria-pressed', dockState.left ? 'true' : 'false');
    dom.btnToggleRight?.setAttribute('aria-pressed', dockState.right ? 'true' : 'false');
    if (dom.leftDockPanel) {
        dom.leftDockPanel.setAttribute('aria-hidden', dockState.left ? 'false' : 'true');
        dom.leftDockPanel.inert = !dockState.left;
    }
    if (dom.rightDockPanel) {
        dom.rightDockPanel.setAttribute('aria-hidden', dockState.right ? 'false' : 'true');
        dom.rightDockPanel.inert = !dockState.right;
    }

    layoutState.mode = mode;
    layoutState.measurements = {
        ...measurements,
        leftDockWidth,
        rightDockWidth,
        leftInset,
        rightInset,
        bottomInset,
        topOffset,
    };
}

function computeTacticalPaddingFromLayout() {
    if (vizState.mapOnlyMode) {
        return { left: 16, right: 16, top: 44, bottom: 16 };
    }
    const measurements = vizState.layoutState.measurements || {};
    const gutter = measurements.gutter || 20;
    return {
        left: Math.max(24, measurements.leftInset || gutter + 12),
        right: Math.max(24, measurements.rightInset || gutter + 12),
        top: Math.max(82, (measurements.topOffset || 62) + 42),
        bottom: Math.max(56, measurements.bottomInset || 56),
    };
}

export function refreshAutoLayout(options = {}) {
    const layoutState = vizState.layoutState;
    if (layoutState.applying) return;
    layoutState.applying = true;
    applyResponsiveDockDefaults();
    const measurements = measureLayoutPanels();
    const mode = resolveLayoutMode(measurements);
    applyAutoLayout(mode, measurements);
    layoutState.tacticalPadding = computeTacticalPaddingFromLayout();
    layoutState.topInset = layoutState.tacticalPadding.top;
    layoutState.leftInset = layoutState.tacticalPadding.left;
    layoutState.rightInset = layoutState.tacticalPadding.right;
    layoutState.bottomInset = layoutState.tacticalPadding.bottom;
    layoutState.applying = false;
    if (options.redraw && vizState.lastTacticalState && vizState.presentationMode === 'MAP') {
        drawTacticalView(vizState.lastTacticalState);
    }
}

window.toggleVizDock = function (side) {
    if (!Object.prototype.hasOwnProperty.call(vizState.dockState, side)) return;
    if (vizState.mapOnlyMode) window.toggleMapOnlyMode(false);
    vizState.dockUserTouched = true;
    vizState.dockState[side] = !vizState.dockState[side];
    saveUiPrefs({ dockState: { left: vizState.dockState.left, right: vizState.dockState.right } });
    refreshAutoLayout({ redraw: true });
};
