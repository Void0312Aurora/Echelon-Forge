"""Shared HTML review helpers for airframe review views."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any, Iterable

from .views_fine_proxy import _fine_proxy_review_mini_svg


def _component_rows_by_name(
    component_report: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    return {row["component_name"]: row for row in component_report["rows"]}


def _triage_mini_view_grid(
    proxy: dict[str, Any],
    component_rows: list[dict[str, Any]],
    review_points: list[dict[str, Any]] | None = None,
) -> str:
    return (
        '<div class="mini-views">'
        + "".join(
            _fine_proxy_review_mini_svg(
                proxy,
                component_rows,
                view,
                review_points=review_points,
                component_labels_visible=True,
            )
            for view in ("top", "side", "front")
        )
        + "</div>"
    )


def _triage_list(items: Iterable[Any]) -> str:
    values = [str(item) for item in items if str(item)]
    if not values:
        return "<ul><li>none</li></ul>"
    return "<ul>" + "".join(f"<li>{html.escape(value)}</li>" for value in values) + "</ul>"


def _triage_card(
    *,
    title: str,
    subtitle: str,
    question: str,
    look_at: str,
    decision: str,
    details: list[str],
    proxy: dict[str, Any],
    component_rows: list[dict[str, Any]],
    severity: str,
    review_points: list[dict[str, Any]] | None = None,
) -> str:
    return f"""
    <article class="triage-card {html.escape(severity)}">
      <div class="triage-head">
        <h3>{html.escape(title)}</h3>
        <span>{html.escape(subtitle)}</span>
      </div>
      <div class="decision-box">
        <div><strong>Review question</strong><p>{html.escape(question)}</p></div>
        <div><strong>Look at</strong><p>{html.escape(look_at)}</p></div>
        <div><strong>Decision needed</strong><p>{html.escape(decision)}</p></div>
      </div>
      {_triage_list(details)}
      {_triage_mini_view_grid(proxy, component_rows, review_points=review_points)}
    </article>
  """


def _review_slug(value: str) -> str:
    cleaned = [char.lower() if char.isalnum() else "-" for char in value.replace("_", "-")]
    slug = "".join(cleaned).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "item"


def _relative_to(path: Path, parent: Path) -> str:
    return path.relative_to(parent).as_posix()


def _isolated_view_page(
    *,
    title: str,
    subtitle: str,
    question: str,
    look_at: str,
    decision: str,
    details: list[str],
    svg_filenames: dict[str, str],
    back_href: str,
    banner_html: str = "",
) -> str:
    banner_css = (
        """    .stale-banner {
      background: #fff7ed;
      border: 1px solid #fed7aa;
      border-left: 5px solid #ea580c;
      border-radius: 6px;
      color: #7c2d12;
      line-height: 1.4;
      margin-top: 14px;
      padding: 10px 12px;
    }
    .stale-banner a {
      color: #9a3412;
      font-weight: 700;
    }
"""
        if banner_html
        else ""
    )
    banner_section = f"{banner_html.rstrip()}\n" if banner_html else ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{html.escape(title)} isolated geometry view</title>
  <style>
    body {{
      margin: 0;
      background: #f6f7f9;
      color: #111827;
      font-family: Arial, sans-serif;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 24px;
    }}
    header, section {{
      background: #ffffff;
      border: 1px solid #d8dde6;
      border-radius: 6px;
      margin: 0 0 18px;
      padding: 18px;
    }}
    h1, h2 {{
      margin: 0;
    }}
    h1 {{
      font-size: 25px;
    }}
    .subtitle {{
      color: #475569;
      font-family: monospace;
      font-size: 13px;
      margin-top: 8px;
    }}
    .decision-box {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 10px;
      background: #f8fafc;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      padding: 10px;
      margin-top: 14px;
    }}
    .decision-box strong {{
      display: block;
      color: #0f172a;
      font-size: 12px;
      letter-spacing: 0;
      text-transform: uppercase;
    }}
    .decision-box p {{
      color: #1f2937;
      font-size: 13px;
      line-height: 1.35;
      margin: 4px 0 0;
    }}
{banner_css}    ul {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 5px 12px;
      margin: 0;
      padding-left: 20px;
      font-family: monospace;
      font-size: 12px;
      color: #334155;
    }}
    .views {{
      display: grid;
      gap: 18px;
    }}
    figure {{
      margin: 0;
      background: #ffffff;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      padding: 12px;
    }}
    figcaption {{
      color: #475569;
      font-family: monospace;
      font-size: 13px;
      margin-bottom: 8px;
    }}
    img {{
      display: block;
      width: 100%;
      height: auto;
    }}
    a {{
      color: #1d4ed8;
    }}
  </style>
</head>
<body>
<main>
  <header>
    <p><a href="{html.escape(back_href)}">Back to isolated review index</a></p>
    <h1>{html.escape(title)}</h1>
    <p class="subtitle">{html.escape(subtitle)}</p>
{banner_section}    <div class="decision-box">
      <div><strong>Review question</strong><p>{html.escape(question)}</p></div>
      <div><strong>Look at</strong><p>{html.escape(look_at)}</p></div>
      <div><strong>Decision needed</strong><p>{html.escape(decision)}</p></div>
    </div>
  </header>
  <section>
    <h2>Trace Details</h2>
    {_triage_list(details)}
  </section>
  <section class="views">
    {''.join(
      f'<figure><figcaption>{html.escape(view)} view</figcaption><img src="{html.escape(filename)}" alt="{html.escape(title)} {html.escape(view)} view"></figure>'
      for view, filename in svg_filenames.items()
    )}
  </section>
</main>
</body>
</html>
"""


def _write_isolated_review_entry(
    *,
    root_dir: Path,
    category: str,
    slug: str,
    title: str,
    subtitle: str,
    question: str,
    look_at: str,
    decision: str,
    details: list[str],
    proxy: dict[str, Any],
    component_rows: list[dict[str, Any]],
    review_points: list[dict[str, Any]] | None = None,
    priority: str,
    banner_html: str = "",
) -> dict[str, Any]:
    category_dir = root_dir / category
    category_dir.mkdir(parents=True, exist_ok=True)
    safe_slug = _review_slug(slug)
    svg_filenames: dict[str, str] = {}
    for view in ("top", "side", "front"):
        svg_filename = f"{safe_slug}_{view}.svg"
        svg_path = category_dir / svg_filename
        svg_path.write_text(
            _fine_proxy_review_mini_svg(
                proxy,
                component_rows,
                view,
                review_points=review_points,
                component_labels_visible=True,
                width=960,
                height=620,
            ),
            encoding="utf-8",
        )
        svg_filenames[view] = svg_filename
    html_path = category_dir / f"{safe_slug}.html"
    html_path.write_text(
        "\n".join(
            line.rstrip()
            for line in _isolated_view_page(
                title=title,
                subtitle=subtitle,
                question=question,
                look_at=look_at,
                decision=decision,
                details=details,
                svg_filenames=svg_filenames,
                back_href="../index.html",
                banner_html=banner_html,
            ).splitlines()
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "category": category,
        "slug": safe_slug,
        "title": title,
        "subtitle": subtitle,
        "priority": priority,
        "html": _relative_to(html_path, root_dir),
        "svg": {
            view: _relative_to(category_dir / filename, root_dir)
            for view, filename in svg_filenames.items()
        },
        "details": details,
        "component_names": [row["component_name"] for row in component_rows],
        "review_point_ids": [row["point_id"] for row in review_points or []],
        "source_region_id": proxy["source_region_id"],
        "review_question": question,
        "decision_needed": decision,
    }
