"""On-demand data visualisation — live Statistics Estonia (stat.ee) figures.

The LLM calls ``make_chart`` with a dataset key; we pull the series from the
Statistics Estonia PxWeb open API (andmed.stat.ee, keyless, CC BY-SA 4.0),
build a Plotly figure server-side, and return it as an ``__ARTIFACT__`` payload
(kind="chart"). The chat streaming endpoint already forwards ``__ARTIFACT__``
blocks to the browser as an ``artifact_show`` event, where chat.js renders the
figure with ``Plotly.newPlot`` in the right-hand results panel.

Each builder returns a plain ``{"data": [...], "layout": {...}}`` dict
(``json.loads(fig.to_json())``) — the same shape Plotly.js consumes directly.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Literal

import httpx
import plotly.graph_objects as go
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)

# PxWeb open API. Data is queried with POST (JSON-stat2); the tree path encodes
# language / database / table. See https://andmed.stat.ee/help/api-manual.pdf
API_BASE = "https://andmed.stat.ee/api/v1/en/stat/"

# Brand palette (eesti.chat blue + a red accent for second series).
BLUE = "#0030DE"
RED = "#E10600"
INK = "#111827"
GRID = "rgba(17,24,39,0.08)"

# -- Dataset catalogue -------------------------------------------------------
# Every entry is a verified stat.ee table reduced to a single annual series
# (non-year dimensions are fixed to one value so the JSON-stat value array
# aligns 1:1 with the year axis). ``year`` is the year dimension's code.
DATASETS: dict[str, dict] = {
    "budget_balance": {
        "path": "majandus/rahandus/valitsemissektori-rahandus/"
                "valitsemissektori-tulud-kulud/RR061.PX",
        "year": "Aasta",
        "title": "Estonia — general government debt & balance (% of GDP)",
        "source": "Statistics Estonia, table RR061",
        "unit": "% of GDP",
        # Two series from the "Näitaja" (indicator) dimension.
        "series": [
            {"label": "Government debt", "fixed": {"Näitaja": ["2"]}, "color": BLUE},
            {"label": "Surplus / deficit", "fixed": {"Näitaja": ["4"]}, "color": RED},
        ],
    },
    "gdp": {
        "path": "majandus/rahvamajanduse-arvepidamine/sisemajanduse-koguprodukt-(skp)/"
                "pehilised-rahvamajanduse-arvepidamise-naitajad/RAA0013.PX",
        "year": "Aasta",
        "title": "Estonia — GDP per capita (current prices)",
        "source": "Statistics Estonia, table RAA0013",
        "unit": "EUR per capita",
        "series": [
            {"label": "GDP per capita", "fixed": {"Näitaja": ["1"]}, "color": BLUE},
        ],
    },
    "inflation": {
        "path": "majandus/hinnad/IA001.PX",
        "year": "Aasta",
        "title": "Estonia — consumer price inflation (annual change)",
        "source": "Statistics Estonia, table IA001",
        "unit": "% change on previous year",
        "series": [
            {"label": "CPI change", "fixed": {"Kaubagrupp": ["1"]}, "color": BLUE},
        ],
    },
    "population": {
        "path": "rahvastik/rahvastikunaitajad-ja-koosseis/"
                "rahvaarv-ja-rahvastiku-koosseis/RV021.PX",
        "year": "Aasta",
        "title": "Estonia — population, 1 January",
        "source": "Statistics Estonia, table RV021",
        "unit": "persons",
        "recent": 35,  # long history; keep the most recent N years for legibility
        "series": [
            {"label": "Population", "fixed": {"Sugu": ["1"], "Vanuserühm": ["1"]}, "color": BLUE},
        ],
    },
    "unemployment": {
        "path": "sotsiaalelu/tooturg/tooturu-uldandmed/aastastatistika/TT0151.px",
        "year": "Vaatlusperiood",
        "title": "Estonia — unemployment rate (ages 15–74)",
        "source": "Statistics Estonia, table TT0151",
        "unit": "% of labour force",
        "series": [
            {"label": "Unemployment rate",
             "fixed": {"Näitaja": ["UNEMP_RATE"], "Sugu": ["T"], "Vanuserühm": ["Y15-74"]},
             "color": BLUE},
        ],
    },
}

# Simple in-process cache so repeated questions don't re-hit stat.ee.
_CACHE: dict[str, tuple[float, list, list]] = {}
_TTL = 6 * 3600  # 6 hours


def _fetch_series(path: str, year_code: str, fixed: dict[str, list[str]]):
    """POST a single-series JSON-stat2 query and return (years, values)."""
    cache_key = path + "|" + json.dumps(fixed, sort_keys=True, ensure_ascii=False)
    hit = _CACHE.get(cache_key)
    if hit and (time.time() - hit[0]) < _TTL:
        return hit[1], hit[2]

    body = {
        "query": [{"code": code, "selection": {"filter": "item", "values": vals}}
                  for code, vals in fixed.items()],
        "response": {"format": "json-stat2"},
    }
    r = httpx.post(API_BASE + path, json=body, timeout=25.0)
    r.raise_for_status()
    data = r.json()

    index = data["dimension"][year_code]["category"]["index"]  # year-code -> position
    years = sorted(index, key=lambda k: index[k])
    values = data["value"]
    # All non-year dimensions are fixed to a single value, so the linear
    # JSON-stat index of each cell reduces to the year's own position.
    series = [values[index[y]] for y in years]

    _CACHE[cache_key] = (time.time(), years, series)
    return years, series


def _layout(title: str, unit: str) -> dict:
    return dict(
        title=dict(text=title, font=dict(size=15, color=INK)),
        height=380,
        margin=dict(l=56, r=20, t=52, b=44),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Inter, system-ui, sans-serif", size=12, color=INK),
        xaxis=dict(showgrid=False, tickfont=dict(size=11)),
        yaxis=dict(title=dict(text=unit, font=dict(size=11)),
                   showgrid=True, gridcolor=GRID, zeroline=True, zerolinecolor=GRID),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        hovermode="x unified",
    )


def _build(dataset: str) -> tuple[dict, str]:
    """Return (figure_dict, short_data_summary) for a dataset key."""
    cfg = DATASETS[dataset]
    fig = go.Figure()
    recent = cfg.get("recent")
    summary_bits: list[str] = []

    for s in cfg["series"]:
        years, values = _fetch_series(cfg["path"], cfg["year"], s["fixed"])
        if recent:
            years, values = years[-recent:], values[-recent:]
        fig.add_trace(go.Scatter(
            x=years, y=values, mode="lines+markers", name=s["label"],
            line=dict(color=s["color"], width=2.4), marker=dict(size=5, color=s["color"]),
            hovertemplate="%{x}: %{y}<extra>" + s["label"] + "</extra>",
        ))
        # Compact summary: first + latest non-null point for the model to narrate.
        pts = [(y, v) for y, v in zip(years, values) if v is not None]
        if pts:
            (fy, fv), (ly, lv) = pts[0], pts[-1]
            summary_bits.append(f"{s['label']}: {fy}={fv}, {ly}={lv}")

    fig.update_layout(_layout(cfg["title"], cfg["unit"]))
    figure = json.loads(fig.to_json())
    summary = (f"{cfg['title']} ({cfg['unit']}). " + "; ".join(summary_bits)
               + f". Source: {cfg['source']}.")
    return figure, summary


class ChartArgs(BaseModel):
    dataset: Literal["budget_balance", "gdp", "inflation", "population", "unemployment"] = Field(
        description=(
            "Which official Statistics Estonia series to visualise:\n"
            "- 'budget_balance': general government debt and surplus/deficit as % of GDP "
            "(use for state budget / balancing the budget / fiscal / debt / deficit questions)\n"
            "- 'gdp': GDP per capita at current prices\n"
            "- 'inflation': consumer price index annual change\n"
            "- 'population': total population (1 January)\n"
            "- 'unemployment': unemployment rate, ages 15–74"
        )
    )


def _make_chart(dataset: str) -> str:
    try:
        figure, summary = _build(dataset)
    except Exception as e:  # noqa: BLE001 — never 500 the chat over a data hiccup
        log.warning("make_chart failed for %s: %s", dataset, e)
        return (f"Could not load the '{dataset}' data from Statistics Estonia right now. "
                "Answer from official sources in words and suggest the user try again.")
    cfg = DATASETS[dataset]
    payload = {"kind": "chart", "title": cfg["title"], "subtitle": cfg["source"],
               "figure": figure}
    # The chat endpoint strips everything from __ARTIFACT__ onward and streams it
    # to the results panel; the text before it is the model-facing confirmation.
    return (
        f"Chart rendered in the results panel — {summary} "
        "Describe the trend in a sentence or two and cite the Statistics Estonia "
        "source; do NOT print the raw numbers or JSON.\n\n"
        "__ARTIFACT__" + json.dumps(payload, ensure_ascii=False, default=str)
    )


make_chart = StructuredTool.from_function(
    func=_make_chart,
    name="make_chart",
    description=(
        "Render an interactive chart of official Estonian statistics in the results "
        "panel, using live data from Statistics Estonia (stat.ee). Call this when the "
        "user asks to see, show, visualise, plot, or graph a trend — especially about "
        "the state budget / balancing the budget (debt and deficit), GDP, inflation, "
        "population, or unemployment — or when a chart would make a fiscal or economic "
        "point clearer. After calling it, briefly describe the trend in words and cite "
        "the source; the chart itself appears automatically."
    ),
    args_schema=ChartArgs,
)
