#!/usr/bin/env python3
"""Render the retained warhead spatial evidence as an inline SVG heatmap fragment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PACKET = (
  REPO_ROOT
  / "docs"
  / "systems"
  / "effects"
  / "reviews"
  / "warhead_spatial_angular_field_admission_20260914"
  / "review_packets"
  / "warhead_spatial_angular_field_admission_20260914.json"
)
DEFAULT_OUTPUT = DEFAULT_PACKET.parent.parent / "warhead-spatial-evidence.html"
DIRECTIONS = ("front", "back", "right", "left", "up", "down")
HEADINGS = (0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0)
STANDOFFS = (0.5, 2.0, 6.0, 10.0)
FAMILIES = ("blast_fragmentation", "continuous_rod")


def _close(left: float, right: float) -> bool:
  return abs(float(left) - float(right)) <= 1.0e-9


def _matrix(rows: list[dict], family: str, standoff: float, field: str) -> list[list[float]]:
  lookup = {
    (
      str(row["direction"]),
      float(row["detonation_attitude_deg"][0]),
    ): float(row["event"][field])
    for row in rows
    if str(row["warhead_family"]) == family
    and _close(float(row["standoff_m"]), standoff)
  }
  return [
    [lookup[(direction, heading)] for heading in HEADINGS]
    for direction in DIRECTIONS
  ]


def _build_payload(packet: dict) -> dict:
  rows = list(packet["rows"])
  effect_heatmaps = [
    {
      "family": family,
      "standoff_m": standoff,
      "values": _matrix(rows, family, standoff, "spatial_projection_effect_scale"),
    }
    for family in FAMILIES
    for standoff in STANDOFFS
  ]
  angular_heatmaps = [
    {
      "family": "blast_fragmentation",
      "standoff_m": standoff,
      "values": _matrix(rows, "blast_fragmentation", standoff, "fragment_angular_density"),
      "signed_polar_cosine": _matrix(
        rows, "blast_fragmentation", standoff, "fragment_angular_signed_polar_cosine"
      ),
    }
    for standoff in STANDOFFS
  ]
  metrics = packet["metrics"]
  decision = packet["admission_decision"]
  return {
    "directions": list(DIRECTIONS),
    "headings": list(HEADINGS),
    "effect_heatmaps": effect_heatmaps,
    "angular_heatmaps": angular_heatmaps,
    "summary": {
      "row_count": int(packet["matrix"]["case_count"]),
      "trace_valid_count": int(metrics["trace_valid_count"]),
      "trace_closure_failures": int(
        metrics["post_closure_failure_count"]
        + metrics["preclamp_decomposition_failure_count"]
        + metrics["candidate_aggregate_mismatch_count"]
        + metrics["flag_closure_failure_count"]
      ),
      "floor_applied_count": int(metrics["near_field_floor_applied_count"]),
      "clamped_count": int(metrics["effect_scale_clamped_count"]),
      "sign_collapse_count": int(metrics["orientation_sign_collapse_count"]),
      "axial_sign_collapse_count": int(metrics["axial_orientation_sign_collapse_count"]),
      "rod_baseline_mismatch_count": int(packet["continuous_rod_baseline_regression"]["mismatch_count"]),
      "fragmentation_admission": str(decision["fragmentation_angular_field_admission"]),
      "overall_admission": str(decision["warhead_spatial_field_admission"]),
    },
  }


FRAGMENT_TEMPLATE = r'''<div id="warhead-spatial-evidence-20260914" class="warhead-spatial-evidence" role="region" aria-labelledby="warhead-spatial-evidence-title">
  <h1 id="warhead-spatial-evidence-title">Warhead spatial evidence</h1>
  <p class="warhead-spatial-caption">384 rows · six directions · four standoffs · eight headings · shared scales within each section</p>
  <div class="warhead-spatial-legend" aria-label="Heatmap legend">
    <span><i class="legend-swatch legend-effect" aria-hidden="true"></i>effect scale</span>
    <span><i class="legend-swatch legend-angular" aria-hidden="true"></i>fragment angular density</span>
    <span><i class="legend-swatch legend-residual" aria-hidden="true"></i>reported residual</span>
  </div>
  <h2>Projected effect scale</h2>
  <div id="warhead-effect-grid" class="warhead-heatmap-grid" aria-label="Effect scale heatmaps"></div>
  <h2>Fragment angular density</h2>
  <div id="warhead-angular-grid" class="warhead-heatmap-grid" aria-label="Fragment angular density heatmaps"></div>
  <h2>Admission and residuals</h2>
  <svg id="warhead-diagnostic-strip" class="warhead-diagnostic-strip" role="img" aria-label="Admission and residual counts"></svg>
  <p class="warhead-spatial-footnote">Axial sign collapse is the front/back check; non-axial equatorial symmetry remains visible in the residual count. Overall spatial-field admission is held by the continuous-rod geometry boundary.</p>
  <noscript>Enable JavaScript to view the evidence heatmaps.</noscript>
  <style>
    #warhead-spatial-evidence-20260914 { color: var(--foreground); font-size: var(--font-size-base); width: 100%; }
    #warhead-spatial-evidence-20260914 h1 { margin: 0 0 0.35rem; }
    #warhead-spatial-evidence-20260914 h2 { margin: 1.2rem 0 0.35rem; }
    #warhead-spatial-evidence-20260914 .warhead-spatial-caption,
    #warhead-spatial-evidence-20260914 .warhead-spatial-footnote { color: var(--muted-foreground); margin: 0.2rem 0 0.6rem; }
    #warhead-spatial-evidence-20260914 .warhead-spatial-caption { font-size: var(--font-size-small); }
    #warhead-spatial-evidence-20260914 .warhead-spatial-footnote { font-size: var(--font-size-small); }
    #warhead-spatial-evidence-20260914 .warhead-spatial-legend { display: flex; flex-wrap: wrap; gap: 0.8rem 1.2rem; margin: 0.5rem 0 0.3rem; color: var(--muted-foreground); font-size: var(--font-size-small); }
    #warhead-spatial-evidence-20260914 .legend-swatch { display: inline-block; width: 0.75rem; height: 0.75rem; margin-right: 0.3rem; vertical-align: -0.08rem; }
    #warhead-spatial-evidence-20260914 .legend-effect { background: var(--viz-series-1); }
    #warhead-spatial-evidence-20260914 .legend-angular { background: var(--viz-series-3); }
    #warhead-spatial-evidence-20260914 .legend-residual { background: var(--destructive); }
    #warhead-spatial-evidence-20260914 .warhead-heatmap-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 240px), 1fr)); gap: 0.45rem 0.8rem; }
    #warhead-spatial-evidence-20260914 .warhead-heatmap { min-width: 0; }
    #warhead-spatial-evidence-20260914 .warhead-heatmap-title { margin: 0.15rem 0 0; color: var(--foreground); font-size: var(--font-size-small); font-weight: 500; }
    #warhead-spatial-evidence-20260914 svg { display: block; width: 100%; overflow: visible; }
    #warhead-spatial-evidence-20260914 .warhead-heatmap-svg { aspect-ratio: 1.48; }
    #warhead-spatial-evidence-20260914 .warhead-diagnostic-strip { height: 10rem; }
    #warhead-spatial-evidence-20260914 .chart-frame { fill: none; stroke: var(--border); stroke-width: 1; }
    #warhead-spatial-evidence-20260914 .grid-line { stroke: var(--border); stroke-width: 1; opacity: 0.7; }
    #warhead-spatial-evidence-20260914 .axis-label,
    #warhead-spatial-evidence-20260914 .axis-title,
    #warhead-spatial-evidence-20260914 .cell-label,
    #warhead-spatial-evidence-20260914 .bar-label,
    #warhead-spatial-evidence-20260914 .bar-value { fill: var(--foreground); font-size: var(--font-size-small); }
    #warhead-spatial-evidence-20260914 .axis-title { font-weight: 500; }
    #warhead-spatial-evidence-20260914 .bar-track { fill: var(--muted); }
    #warhead-spatial-evidence-20260914 .bar { fill: var(--viz-series-3); }
    #warhead-spatial-evidence-20260914 .bar.residual { fill: var(--destructive); }
    #warhead-spatial-evidence-20260914 .bar.held { fill: var(--viz-series-2); }
    @media (max-width: 420px) {
      #warhead-spatial-evidence-20260914 .warhead-heatmap-svg { aspect-ratio: 1.35; }
      #warhead-spatial-evidence-20260914 .warhead-spatial-legend { gap: 0.45rem 0.8rem; }
    }
  </style>
  <script>
    (() => {
      const DATA = __DATA__;
      const ROOT = document.getElementById("warhead-spatial-evidence-20260914");
      const SVG_NS = "http://www.w3.org/2000/svg";
      const DIRECTIONS = DATA.directions;
      const HEADINGS = DATA.headings;
      const createSvg = (tag, attrs = {}) => {
        const node = document.createElementNS(SVG_NS, tag);
        Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, String(value)));
        return node;
      };
      const appendText = (parent, text, attrs = {}) => {
        const node = createSvg("text", attrs);
        node.textContent = text;
        parent.appendChild(node);
        return node;
      };
      const flatten = (values) => values.flatMap((row) => row);
      const extent = (values) => {
        const flat = flatten(values);
        return [Math.min(...flat), Math.max(...flat)];
      };
      const colorMix = (value, domain, token) => {
        const span = domain[1] - domain[0] || 1;
        const ratio = Math.max(0, Math.min(1, (value - domain[0]) / span));
        const percentage = Math.round(12 + ratio * 78);
        return `color-mix(in srgb, var(${token}) ${percentage}%, var(--background))`;
      };
      const appendHeatmap = (host, item, domain, token, valueLabel) => {
        const panel = document.createElement("div");
        panel.className = "warhead-heatmap";
        const title = document.createElement("p");
        title.className = "warhead-heatmap-title";
        title.textContent = `${item.family === "blast_fragmentation" ? "blast fragmentation" : "continuous rod"} · ${item.standoff_m} m`;
        panel.appendChild(title);
        const svg = createSvg("svg", { class: "warhead-heatmap-svg", role: "img", "aria-label": title.textContent });
        panel.appendChild(svg);
        host.appendChild(panel);
        const draw = () => {
          const width = Math.max(240, Math.floor(svg.getBoundingClientRect().width || 240));
          const height = Math.max(170, Math.round(width / 1.48));
          const margin = { top: 28, right: 6, bottom: 42, left: 62 };
          const plotWidth = width - margin.left - margin.right;
          const plotHeight = height - margin.top - margin.bottom;
          const cellWidth = plotWidth / HEADINGS.length;
          const cellHeight = plotHeight / DIRECTIONS.length;
          svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
          svg.replaceChildren();
          svg.appendChild(createSvg("title")).textContent = title.textContent;
          svg.appendChild(createSvg("rect", { class: "chart-frame", "data-chart-frame": "true", x: margin.left, y: margin.top, width: plotWidth, height: plotHeight }));
          HEADINGS.forEach((heading, column) => appendText(svg, `${heading}°`, { class: "axis-label", x: margin.left + cellWidth * (column + 0.5), y: margin.top - 9, "text-anchor": "middle" }));
          DIRECTIONS.forEach((direction, rowIndex) => appendText(svg, direction, { class: "axis-label", x: margin.left - 8, y: margin.top + cellHeight * (rowIndex + 0.5) + 4, "text-anchor": "end" }));
          appendText(svg, "heading (deg)", { class: "axis-title", "data-axis": "x", x: margin.left + plotWidth / 2, y: height - 5, "text-anchor": "middle" });
          const yTitle = appendText(svg, "direction", { class: "axis-title", "data-axis": "y", x: 12, y: margin.top + plotHeight / 2, "text-anchor": "middle" });
          yTitle.setAttribute("transform", `rotate(-90 12 ${margin.top + plotHeight / 2})`);
          item.values.forEach((row, rowIndex) => row.forEach((value, column) => {
            const rect = createSvg("rect", { x: margin.left + column * cellWidth + 0.5, y: margin.top + rowIndex * cellHeight + 0.5, width: Math.max(0, cellWidth - 1), height: Math.max(0, cellHeight - 1), fill: colorMix(value, domain, token), "data-chart-hit": "true", "data-tooltip": `${item.family}, ${item.standoff_m} m, ${DIRECTIONS[rowIndex]}, ${HEADINGS[column]}°: ${valueLabel(value)}` });
            const tooltip = createSvg("title");
            tooltip.textContent = `${DIRECTIONS[rowIndex]} ${HEADINGS[column]}° · ${valueLabel(value)}`;
            rect.appendChild(tooltip);
            svg.appendChild(rect);
            appendText(svg, valueLabel(value), { class: "cell-label", x: margin.left + column * cellWidth + cellWidth / 2, y: margin.top + rowIndex * cellHeight + cellHeight / 2 + 4, "text-anchor": "middle" });
          }));
        };
        draw();
        if (typeof ResizeObserver !== "undefined") new ResizeObserver(draw).observe(svg);
      };
      const effectValues = DATA.effect_heatmaps.map((item) => item.values);
      const angularValues = DATA.angular_heatmaps.map((item) => item.values);
      const effectDomain = extent(effectValues);
      const angularDomain = extent(angularValues);
      DATA.effect_heatmaps.forEach((item) => appendHeatmap(document.getElementById("warhead-effect-grid"), item, effectDomain, item.family === "blast_fragmentation" ? "--viz-series-1" : "--viz-series-2", (value) => value.toFixed(2)));
      DATA.angular_heatmaps.forEach((item) => appendHeatmap(document.getElementById("warhead-angular-grid"), item, angularDomain, "--viz-series-3", (value) => value.toFixed(2)));
      const drawDiagnostics = () => {
        const svg = document.getElementById("warhead-diagnostic-strip");
        const width = Math.max(320, Math.floor(svg.getBoundingClientRect().width || 320));
        const height = 160;
        const margin = { top: 12, right: 8, bottom: 34, left: 12 };
        const values = [
          ["trace valid", DATA.summary.trace_valid_count, DATA.summary.row_count, "bar"],
          ["closure failures", DATA.summary.trace_closure_failures, DATA.summary.row_count, "bar"],
          ["rod baseline Δ", DATA.summary.rod_baseline_mismatch_count, DATA.summary.row_count, "bar"],
          ["sign residuals", DATA.summary.sign_collapse_count, DATA.summary.row_count, "bar residual"],
          ["axial residuals", DATA.summary.axial_sign_collapse_count, DATA.summary.row_count, "bar residual"],
        ];
        const maxValue = Math.max(DATA.summary.row_count, ...values.map((entry) => entry[1]), 1);
        const plotWidth = width - margin.left - margin.right;
        const slot = plotWidth / values.length;
        const barWidth = Math.min(74, slot * 0.62);
        svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
        svg.replaceChildren();
        svg.appendChild(createSvg("title")).textContent = "Admission and residual counts";
        values.forEach(([label, value, , className], index) => {
          const x = margin.left + slot * index + (slot - barWidth) / 2;
          const trackHeight = height - margin.top - margin.bottom;
          const barHeight = trackHeight * (value / maxValue);
          const y = height - margin.bottom - barHeight;
          svg.appendChild(createSvg("rect", { class: "bar-track", x, y: margin.top, width: barWidth, height: trackHeight }));
          svg.appendChild(createSvg("rect", { class: className, x, y, width: barWidth, height: barHeight, "data-chart-hit": "true", "data-tooltip": `${label}: ${value}` }));
          appendText(svg, String(value), { class: "bar-value", x: x + barWidth / 2, y: Math.max(margin.top + 12, y - 5), "text-anchor": "middle" });
          appendText(svg, label, { class: "bar-label", x: x + barWidth / 2, y: height - 13, "text-anchor": "middle" });
        });
      };
      drawDiagnostics();
      if (typeof ResizeObserver !== "undefined") new ResizeObserver(drawDiagnostics).observe(document.getElementById("warhead-diagnostic-strip"));
    })();
  </script>
</div>
'''


def render(packet_path: Path, output_path: Path) -> None:
  packet = json.loads(packet_path.read_text(encoding="utf-8"))
  payload = json.dumps(_build_payload(packet), ensure_ascii=True, separators=(",", ":"))
  fragment = FRAGMENT_TEMPLATE.replace("__DATA__", payload).replace('\\"', '"')
  output_path.parent.mkdir(parents=True, exist_ok=True)
  output_path.write_text(fragment, encoding="utf-8", newline="\n")


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--packet", type=Path, default=DEFAULT_PACKET)
  parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
  args = parser.parse_args()
  render(args.packet, args.output)
  print(args.output)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
