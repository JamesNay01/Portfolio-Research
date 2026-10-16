#!/usr/bin/env python3
"""
generate_site.py — builds the deployable static site from data/portfolio.json.

Usage: python3 generate_site.py
Output: site/index.html, site/research/index.html, site/research/<ticker>.html,
        site/assets/styles.css

Why a build script instead of hand-written HTML: the portfolio changes
every time a trade happens. This script is the single place that turns
data/portfolio.json into every page, so updating a holding, adding a new
one, or writing a thesis means editing the JSON (or asking Claude to) and
re-running this script — never hand-editing 15 HTML files.
"""
import json
import math
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
DATA = json.loads((ROOT / "data" / "portfolio.json").read_text())
PERF_PATH = ROOT / "data" / "performance.json"
PERF = json.loads(PERF_PATH.read_text()) if PERF_PATH.exists() else {"benchmarkName": "S&P 500", "dates": [], "portfolioReturns": [], "benchmarkReturns": []}
SITE = ROOT / "site"

PALETTE = [
    "#2f6b4f", "#8a6d3b", "#3d7ea6", "#a23b2e", "#6b5b95",
    "#4f8a5b", "#c98a2b", "#4a6a8a", "#8a4a4a", "#5b7a6b",
    "#a68a3d", "#3d5a8a", "#7a4a6a", "#5a8a4a",
]

def fmt_usd(v, decimals=2):
    sign = "-" if v < 0 else ""
    return f"{sign}${abs(v):,.{decimals}f}"

def fmt_pct(v, decimals=2):
    sign = "+" if v >= 0 else ""
    return f"{sign}{v*100:.{decimals}f}%"

def gain_class(v):
    return "gain" if v >= 0 else "loss"

TAB_ICONS = {
    "portfolio": '<svg viewBox="0 0 16 16" fill="currentColor"><rect x="1" y="1" width="6" height="6" rx="1.2"/><rect x="9" y="1" width="6" height="6" rx="1.2"/><rect x="1" y="9" width="6" height="6" rx="1.2"/><rect x="9" y="9" width="6" height="6" rx="1.2"/></svg>',
    "research": '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><rect x="3" y="1.5" width="10" height="13" rx="1.5"/><line x1="5.5" y1="5" x2="10.5" y2="5"/><line x1="5.5" y1="8" x2="10.5" y2="8"/><line x1="5.5" y1="11" x2="8.5" y2="11"/></svg>',
    "allocation": '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="8" cy="8" r="6.3"/><path d="M8 1.7 A6.3 6.3 0 0 1 14.3 8 L8 8 Z" fill="currentColor" stroke="none"/></svg>',
    "performance": '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="1.5,12 6,7 9,10 14.5,3.5"/><polyline points="10.5,3.5 14.5,3.5 14.5,7.5"/></svg>',
    "about": '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="5.2" r="2.7"/><path d="M2.3 14c0-2.9 2.5-5 5.7-5s5.7 2.1 5.7 5"/></svg>',
}

TABS = [
    ("portfolio", "Portfolio", "index.html"),
    ("research", "Research", "research/index.html"),
    ("allocation", "Allocation", "allocation.html"),
    ("performance", "Performance", "performance.html"),
    ("about", "About", "about.html"),
]

def nav(prefix="", active=""):
    links = "".join(
        f'<a href="{prefix}{href}"{" class=\"active\"" if key == active else ""}>{TAB_ICONS[key]}{label}</a>'
        for key, label, href in TABS
    )
    return f"""
  <header class="site-header">
    <div class="top-row">
      <div class="wordmark"><a href="{prefix}index.html">{DATA['accountName']}</a></div>
    </div>
    <nav class="tab-bar">{links}</nav>
  </header>"""

def page(title, body, prefix="", active="", extra_class=""):
    description = f"Independent equity research and an active portfolio track record — {DATA['accountName']}."
    canonical_title = title
    favicon = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='16' fill='%2314201c'/%3E%3Cpath d='M22 68 L38 44 L52 56 L78 26' stroke='%232f6b4f' stroke-width='7' fill='none' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{title}</title>
<meta name="description" content="{description}" />
<link rel="icon" href="{favicon}" />

<meta property="og:type" content="website" />
<meta property="og:site_name" content="{DATA['accountName']}" />
<meta property="og:title" content="{canonical_title}" />
<meta property="og:description" content="{description}" />
<meta name="twitter:card" content="summary" />
<meta name="twitter:title" content="{canonical_title}" />
<meta name="twitter:description" content="{description}" />

<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:wght@500;600;700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap">
<link rel="stylesheet" href="{prefix}assets/styles.css">
<script src="{prefix}assets/performance-chart.js"></script>
</head>
<body class="{extra_class}">
{nav(prefix, active)}
{body}
  <footer class="site-footer">
    Paper-trading portfolio (Investopedia Stock Simulator) for educational and research-demonstration purposes.
    Not a real brokerage account and not investment advice. Data as of {DATA['asOf']}.
  </footer>
</body>
</html>
"""

def build_index():
    acct = DATA["account"]
    hs = DATA["holdingsSummary"]
    stats = f"""
  <div class="hero">
    <div class="hero-inner">
      <h1>{DATA['accountName']}</h1>
      <p class="tagline">Independent research and an active paper-trading portfolio, updated as positions change with the reasoning behind each move.</p>
    </div>
  </div>
  <div class="stat-row">
    <div class="stat"><div class="label">Account value</div><div class="value">{fmt_usd(acct['accountValue'], 2)}</div>
      <div class="sub {gain_class(acct['todaysChange'])}">{fmt_usd(acct['todaysChange'])} ({fmt_pct(acct['todaysChangePct'])}) today</div></div>
    <div class="stat"><div class="label">Annual return</div><div class="value pos">{fmt_pct(acct['annualReturn'], 2)}</div></div>
    <div class="stat"><div class="label">Total gain / loss</div><div class="value {gain_class(hs['totalGainLoss'])}">{fmt_usd(hs['totalGainLoss'], 2)}</div>
      <div class="sub {gain_class(hs['totalGainLossPct'])}">{fmt_pct(hs['totalGainLossPct'])} overall</div></div>
  </div>
"""
    rows = ""
    for h in sorted(DATA["holdings"], key=lambda x: -x["totalValue"]):
        rows += f"""
      <tr>
        <td><a class="ticker-link" href="research/{h['ticker'].lower()}.html">{h['ticker']}</a></td>
        <td>{h['name']}</td>
        <td class="num">{fmt_usd(h['currentPrice'])}</td>
        <td class="num {gain_class(h['todaysChange'])}">{fmt_usd(h['todaysChange'])} ({fmt_pct(h['todaysChangePct'])})</td>
        <td class="num">{fmt_usd(h['purchasePrice'])}</td>
        <td class="num">{h['qty']:,}</td>
        <td class="num">{fmt_usd(h['totalValue'])}</td>
        <td class="num {gain_class(h['totalGainLoss'])}">{fmt_usd(h['totalGainLoss'])} ({fmt_pct(h['totalGainLossPct'])})</td>
      </tr>"""
    holdings_section = f"""
  <div class="section">
    <h2 class="section-title">Current holdings</h2>
    <p class="section-sub">Every ticker links to the research and reasoning behind that position.</p>
    <div class="table-wrap">
    <table>
      <thead><tr><th>Ticker</th><th>Company</th><th class="num">Price</th><th class="num">Today</th><th class="num">Cost basis</th><th class="num">Qty</th><th class="num">Value</th><th class="num">Total gain/loss</th></tr></thead>
      <tbody>{rows}
      </tbody>
    </table>
    </div>
  </div>
"""
    return page(f"{DATA['accountName']} — Portfolio", stats + holdings_section, active="portfolio")

def build_research_index():
    cards = ""
    for h in sorted(DATA["holdings"], key=lambda x: -x["totalGainLossPct"]):
        cards += f"""
      <a class="research-card" href="{h['ticker'].lower()}.html">
        <div class="ticker">{h['ticker']}</div>
        <div class="name">{h['name']}</div>
        <div class="gainline {gain_class(h['totalGainLossPct'])}">{fmt_pct(h['totalGainLossPct'])} since purchase</div>
      </a>"""
    body = f"""
  <div class="hero">
    <div class="hero-inner">
      <h1>Research</h1>
      <p class="tagline">The thinking behind every position in the portfolio.</p>
    </div>
  </div>
  <div class="section">
    <div class="research-index">{cards}
    </div>
  </div>
"""
    return page("Research — " + DATA["accountName"], body, prefix="../", active="research")

def build_research_page(h):
    thesis = h.get("thesis", "").strip()
    if thesis and "---UPDATE---" in thesis:
        first, second = [s.strip() for s in thesis.split("---UPDATE---", 1)]
        thesis_html = (f'<div class="thesis-part">{first}</div>'
                       '<div class="thesis-divider"><span>Update: where it stands now</span></div>'
                       f'<div class="thesis-part">{second}</div>')
    elif thesis:
        thesis_html = thesis
    else:
        thesis_html = "No writeup yet for this position. Tell Claude the reasoning behind this trade and it'll go here."
    thesis_class = "thesis-box" if thesis else "thesis-box placeholder"
    body = f"""
  <div class="hero research-page">
    <div class="hero-inner">
      <p class="back-link"><a href="index.html">← Research</a></p>
      <h1>{h['ticker']} — {h['name']}</h1>
    </div>
  </div>
  <div class="section">
    <div class="trade-facts">
      <div class="cell"><div class="label">Purchase price</div><div class="value">{fmt_usd(h['purchasePrice'])}</div></div>
      <div class="cell"><div class="label">Current price</div><div class="value">{fmt_usd(h['currentPrice'])}</div></div>
      <div class="cell"><div class="label">Quantity</div><div class="value">{h['qty']:,}</div></div>
      <div class="cell"><div class="label">Position value</div><div class="value">{fmt_usd(h['totalValue'])}</div></div>
      <div class="cell"><div class="label">Total gain/loss</div><div class="value {gain_class(h['totalGainLoss'])}">{fmt_usd(h['totalGainLoss'])}</div></div>
      <div class="cell"><div class="label">Return</div><div class="value {gain_class(h['totalGainLossPct'])}">{fmt_pct(h['totalGainLossPct'])}</div></div>
    </div>
    <h2 class="section-title">Thesis</h2>
    <div class="{thesis_class}">{thesis_html}</div>
  </div>

"""
    return page(f"{h['ticker']} research — {DATA['accountName']}", body, prefix="../", active="research")

# ---------------------------------------------------------------- allocation

def donut_point(cx, cy, r, angle_deg):
    rad = math.radians(angle_deg)
    return cx + r * math.sin(rad), cy - r * math.cos(rad)

def donut_svg(slices, size=320):
    cx = cy = size / 2
    outer_r = size / 2 - 10
    inner_r = outer_r * 0.58
    cum = 0.0
    paths = []
    for ticker, value, pct, color in slices:
        start_angle = cum * 360
        cum += pct
        end_angle = cum * 360
        large_arc = 1 if (end_angle - start_angle) > 180 else 0
        x1, y1 = donut_point(cx, cy, outer_r, start_angle)
        x2, y2 = donut_point(cx, cy, outer_r, end_angle)
        x3, y3 = donut_point(cx, cy, inner_r, end_angle)
        x4, y4 = donut_point(cx, cy, inner_r, start_angle)
        d = (f"M{x1:.2f},{y1:.2f} A{outer_r:.2f},{outer_r:.2f} 0 {large_arc} 1 {x2:.2f},{y2:.2f} "
             f"L{x3:.2f},{y3:.2f} A{inner_r:.2f},{inner_r:.2f} 0 {large_arc} 0 {x4:.2f},{y4:.2f} Z")
        paths.append(f'<path d="{d}" fill="{color}"><title>{ticker}: {pct*100:.1f}%</title></path>')
    slices_svg = "\n      ".join(paths)
    return f"""<svg viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">
      {slices_svg}
    </svg>"""

def build_allocation():
    total = sum(h["totalValue"] for h in DATA["holdings"])
    ranked = sorted(DATA["holdings"], key=lambda x: -x["totalValue"])
    slices = [(h["ticker"], h["totalValue"], h["totalValue"] / total, PALETTE[i % len(PALETTE)]) for i, h in enumerate(ranked)]

    legend_rows = "".join(
        f"""<tr>
          <td><span class="swatch" style="background:{color}"></span><span class="tk">{ticker}</span></td>
          <td class="pct">{pct*100:.1f}%</td>
          <td class="pct">{fmt_usd(value)}</td>
        </tr>"""
        for ticker, value, pct, color in slices
    )

    body = f"""
  <div class="hero">
    <div class="hero-inner">
      <h1>Allocation</h1>
      <p class="tagline">How the portfolio's {fmt_usd(total)} of invested value is weighted across positions.</p>
    </div>
  </div>
  <div class="section">
    <div class="allocation-layout">
      <div class="donut-wrap">{donut_svg(slices)}</div>
      <div class="table-wrap">
      <table class="legend">
        <thead><tr><th style="text-align:left;">Position</th><th class="pct" style="text-align:right;">Weight</th><th class="pct" style="text-align:right;">Value</th></tr></thead>
        <tbody>{legend_rows}</tbody>
      </table>
      </div>
    </div>
  </div>
"""
    return page("Allocation — " + DATA["accountName"], body, active="allocation")

# ---------------------------------------------------------------- performance

def line_chart_svg(dates, series, width=860, height=340):
    pad_l, pad_r, pad_t, pad_b = 50, 20, 20, 30
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b
    all_vals = [v for s in series for v in s["values"]]
    vmin, vmax = min(all_vals), max(all_vals)
    vrange = (vmax - vmin) or 1
    n = len(dates)

    def xy(i, v):
        x = pad_l + (i / (n - 1)) * plot_w if n > 1 else pad_l
        y = pad_t + plot_h - ((v - vmin) / vrange) * plot_h
        return x, y

    gridlines = ""
    for frac in (0, 0.25, 0.5, 0.75, 1.0):
        y = pad_t + plot_h * (1 - frac)
        val = vmin + vrange * frac
        gridlines += f'<line x1="{pad_l}" y1="{y:.1f}" x2="{width-pad_r}" y2="{y:.1f}" stroke="#dce1db" stroke-width="1"/>'
        gridlines += f'<text x="4" y="{y+4:.1f}" font-size="10" fill="#5b6b62" font-family="IBM Plex Mono, monospace">{val:+.0f}%</text>'

    lines = ""
    for s in series:
        pts = " ".join(f"{xy(i, v)[0]:.1f},{xy(i, v)[1]:.1f}" for i, v in enumerate(s["values"]))
        lines += f'<polyline points="{pts}" fill="none" stroke="{s["color"]}" stroke-width="2.5"/>'

    return f"""<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
      {gridlines}
      {lines}
    </svg>"""

def build_yearly_chart():
    years = PERF.get("yearlyReturns", [])
    if not years:
        return ""
    width, height = 860, 300
    pad_l, pad_r, pad_t, pad_b = 50, 20, 20, 34
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b
    all_vals = [y["portfolio"] for y in years] + [y["benchmark"] for y in years]
    vmax = max(max(all_vals), 0)
    vmin = min(min(all_vals), 0)
    vrange = (vmax - vmin) or 1
    zero_y = pad_t + plot_h - ((0 - vmin) / vrange) * plot_h

    n = len(years)
    slot_w = plot_w / n
    bar_w = slot_w * 0.28
    gap = slot_w * 0.06

    def y_for(v):
        return pad_t + plot_h - ((v - vmin) / vrange) * plot_h

    bars = ""
    labels = ""
    gridlines = ""
    for frac in (0, 0.25, 0.5, 0.75, 1.0):
        gy = pad_t + plot_h * (1 - frac)
        gval = vmin + vrange * frac
        gridlines += f'<line x1="{pad_l}" y1="{gy:.1f}" x2="{width-pad_r}" y2="{gy:.1f}" stroke="#dce1db" stroke-width="1"/>'
        gridlines += f'<text x="4" y="{gy+4:.1f}" font-size="10" fill="#5b6b62" font-family="IBM Plex Mono, monospace">{gval:+.0f}%</text>'

    for i, y in enumerate(years):
        slot_x = pad_l + i * slot_w
        px = slot_x + slot_w / 2 - gap / 2 - bar_w
        bx = slot_x + slot_w / 2 + gap / 2
        p_top, p_bot = sorted([y_for(y["portfolio"]), zero_y])
        b_top, b_bot = sorted([y_for(y["benchmark"]), zero_y])
        bars += f'<rect x="{px:.1f}" y="{p_top:.1f}" width="{bar_w:.1f}" height="{max(p_bot-p_top,1):.1f}" fill="#2f6b4f"/>'
        bars += f'<rect x="{bx:.1f}" y="{b_top:.1f}" width="{bar_w:.1f}" height="{max(b_bot-b_top,1):.1f}" fill="#8a6d3b"/>'
        p_label_y = p_top - 5 if y["portfolio"] >= 0 else p_bot + 12
        b_label_y = b_top - 5 if y["benchmark"] >= 0 else b_bot + 12
        bars += f'<text x="{px+bar_w/2:.1f}" y="{p_label_y:.1f}" font-size="10.5" text-anchor="middle" fill="#2f6b4f" font-family="IBM Plex Mono, monospace" font-weight="600">{y["portfolio"]:+.1f}%</text>'
        bars += f'<text x="{bx+bar_w/2:.1f}" y="{b_label_y:.1f}" font-size="10.5" text-anchor="middle" fill="#8a6d3b" font-family="IBM Plex Mono, monospace" font-weight="600">{y["benchmark"]:+.1f}%</text>'
        labels += f'<text x="{slot_x+slot_w/2:.1f}" y="{height-10}" font-size="11.5" text-anchor="middle" fill="#1a1d1f" font-family="Inter, sans-serif">{y["year"]}</text>'

    svg = f"""<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
      {gridlines}
      <line x1="{pad_l}" y1="{zero_y:.1f}" x2="{width-pad_r}" y2="{zero_y:.1f}" stroke="#b9c2b6" stroke-width="1.5"/>
      {bars}
      {labels}
    </svg>"""

    notes = [y.get("note") for y in years if y.get("note")]
    note_text = " · ".join(notes) if notes else ""

    return f"""
    <h2 class="section-title" style="margin-top:8px;">Year by year vs. the market</h2>
    <p class="section-sub">Portfolio return compared to {PERF.get('benchmarkName', 'S&P 500')} for each calendar year, calculated from real account values at each year's boundary.</p>
    <div class="yearly-chart-wrap">{svg}
      <div class="chart-legend">
        <div class="item"><span class="line-swatch" style="background:#2f6b4f"></span>{DATA['accountName']}</div>
        <div class="item"><span class="line-swatch" style="background:#8a6d3b"></span>{PERF.get('benchmarkName', 'S&P 500')}</div>
      </div>
    </div>
    <p class="yearly-note">{note_text}</p>
"""

def build_position_bar(top_pct):
    """A bar spanning the top 50% down to top 0.01%, since a full 0-100
    linear scale would put a top-0.28% marker indistinguishable from the
    very edge. Zooming into the range that's actually meaningful here is
    what makes the visual honest rather than gimmicky."""
    lo, hi = 50.0, 0.01  # left = less exclusive, right = most exclusive
    frac = (lo - top_pct) / (lo - hi)
    frac = max(0.0, min(1.0, frac))
    width, height = 760, 90
    pad = 24
    track_y = 44
    track_h = 10
    x0, x1 = pad, width - pad
    marker_x = x0 + frac * (x1 - x0)
    fill_w = marker_x - x0
    label_anchor = "end" if marker_x > (x0 + x1) / 2 else "start"
    label_x = marker_x - 8 if label_anchor == "end" else marker_x + 8

    return f"""<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
      <rect x="{x0}" y="{track_y}" width="{x1-x0}" height="{track_h}" rx="{track_h/2}" fill="#e8eae6"/>
      <rect x="{x0}" y="{track_y}" width="{fill_w:.1f}" height="{track_h}" rx="{track_h/2}" fill="#8a6d3b"/>
      <line x1="{marker_x:.1f}" y1="{track_y-10}" x2="{marker_x:.1f}" y2="{track_y+track_h+10}" stroke="#12181f" stroke-width="2"/>
      <circle cx="{marker_x:.1f}" cy="{track_y+track_h/2}" r="6" fill="#12181f"/>
      <text x="{label_x:.1f}" y="{track_y-16}" text-anchor="{label_anchor}" font-family="IBM Plex Mono, monospace" font-size="12" font-weight="600" fill="#12181f">James's Portfolio — Top {top_pct:.2f}%</text>
      <text x="{x0}" y="{track_y+track_h+28}" font-family="Inter, sans-serif" font-size="11" fill="#5b6b62">Top 50%</text>
      <text x="{x1}" y="{track_y+track_h+28}" text-anchor="end" font-family="Inter, sans-serif" font-size="11" fill="#5b6b62">Top 0.01%</text>
    </svg>"""

def build_standing_section():
    acct = DATA["account"]
    top_pct = acct.get("topPercent")
    band = acct.get("topRankBand")
    if not top_pct or not band:
        return ""
    bar_svg = build_position_bar(top_pct)
    return f"""
    <h2 class="section-title">Simulator standing</h2>
    <p class="section-sub">Where this portfolio ranks among all Investopedia Simulator accounts. Rankings change often, so this is shown as a range.</p>
    <div class="standing-hero">
      <div class="big-stat">Top <span class="accent">{top_pct:.2f}%</span></div>
      <div class="sub">In the top {band:,} of over 3 million Investopedia Simulator users</div>
    </div>
    <div class="position-bar-wrap">{bar_svg}</div>
    <p class="position-bar-caption">Position among the top 50% of all users, zoomed in since the full user base is too large to show a meaningful marker on a linear scale.</p>
    <div class="standing-stats">
      <div class="stat"><div class="label">Rank</div><div class="value">Top {band:,}</div></div>
      <div class="stat"><div class="label">Total users</div><div class="value">3M+</div></div>
      <div class="stat"><div class="label">Percentile</div><div class="value pos">Top {top_pct:.2f}%</div></div>
    </div>
"""

def build_performance():
    dates = PERF.get("dates", [])
    if not dates:
        body = f"""
  <div class="hero">
    <div class="hero-inner">
      <h1>Performance</h1>
      <p class="tagline">Portfolio return vs. {PERF.get('benchmarkName', 'the market')} over time.</p>
    </div>
  </div>
  <div class="section">
    <div class="empty-state">
      No performance history loaded yet. This page compares real account value over
      time against a benchmark — nothing here is estimated or filled in.<br><br>
      To populate it: connect Claude for Chrome to your logged-in Investopedia tab
      and ask Claude to pull your performance history, or export it from
      Investopedia's <strong>Performance History</strong> button and share the file.
      That data goes into <code>data/performance.json</code>, and this chart
      builds itself from it.
    </div>
  </div>
"""
        return page("Performance — " + DATA["accountName"], body, active="performance")

    payload = json.dumps({
        "dates": PERF["dates"],
        "portfolioReturns": PERF["portfolioReturns"],
        "benchmarkReturns": PERF["benchmarkReturns"],
        "portfolioLabel": DATA["accountName"],
        "benchmarkLabel": PERF.get("benchmarkName", "S&P 500"),
    })

    body = f"""
  <div class="hero">
    <div class="hero-inner">
      <h1>Performance</h1>
      <p class="tagline">Portfolio return vs. {PERF.get('benchmarkName', 'the market')}. Drag across the chart for exact values; filter the timeframe below.</p>
    </div>
  </div>
  <div class="section">
    <div class="chart-controls" id="perfControls">
      <button data-range="3m">3M</button>
      <button data-range="6m">6M</button>
      <button data-range="1y">1Y</button>
      <button data-range="2y">2Y</button>
      <button data-range="all" class="active">All</button>
    </div>
    <div class="chart-wrap">
      <svg id="perfSvg" viewBox="0 0 860 340" xmlns="http://www.w3.org/2000/svg"></svg>
      <div class="chart-tooltip" id="perfTooltip"></div>
    </div>
    <div class="chart-legend">
      <div class="item"><span class="line-swatch" style="background:#2f6b4f"></span>{DATA['accountName']}</div>
      <div class="item"><span class="line-swatch" style="background:#8a6d3b"></span>{PERF.get('benchmarkName', 'S&P 500')}</div>
    </div>
    <p class="chart-resolution-note">Portfolio values are from real daily account history. The {PERF.get('benchmarkName', 'S&P 500')} comparison is monthly resolution — so 3M/6M views show a handful of real monthly points rather than a smooth daily line. Each timeframe is re-indexed to 0% at its own starting point.</p>

    {build_yearly_chart()}
  </div>
  <div class="section">
    {build_standing_section()}
  </div>
  <script id="perfData" type="application/json">{payload}</script>
  <script>
  (function() {{
    const DATA = JSON.parse(document.getElementById('perfData').textContent);
    const svg = document.getElementById('perfSvg');
    const tooltip = document.getElementById('perfTooltip');
    const chartWrap = svg.closest('.chart-wrap');
    const svgNS = 'http://www.w3.org/2000/svg';
    const W = 860, H = 340, padL = 50, padR = 20, padT = 20, padB = 30;
    const plotW = W - padL - padR, plotH = H - padT - padB;
    let current = null;

    function el(tag, attrs) {{
      const e = document.createElementNS(svgNS, tag);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      return e;
    }}

    function xAt(i, n) {{ return n > 1 ? padL + (i / (n - 1)) * plotW : padL; }}
    function yAt(v, vmin, vrange) {{ return padT + plotH - ((v - vmin) / vrange) * plotH; }}

    function pickLabelIndices(n) {{
      if (n <= 6) return [...Array(n).keys()];
      const idxs = new Set([0, n - 1]);
      const step = (n - 1) / 5;
      for (let k = 1; k < 5; k++) idxs.add(Math.round(k * step));
      return [...idxs].sort((a, b) => a - b);
    }}

    function render(rangeKey) {{
      current = PerformanceChart.filterRange(DATA.dates, DATA.portfolioReturns, DATA.benchmarkReturns, rangeKey);
      const {{ dates, portfolio, benchmark }} = current;
      const n = dates.length;
      const all = portfolio.concat(benchmark);
      const vmin = Math.min(...all), vmax = Math.max(...all);
      const vrange = (vmax - vmin) || 1;

      svg.innerHTML = '';
      const g = el('g', {{}});

      [0, 0.25, 0.5, 0.75, 1].forEach((f) => {{
        const y = padT + plotH * (1 - f);
        const val = vmin + vrange * f;
        g.appendChild(el('line', {{ x1: padL, y1: y.toFixed(1), x2: W - padR, y2: y.toFixed(1), stroke: '#dce1db', 'stroke-width': 1 }}));
        const t = el('text', {{ x: 4, y: (y + 4).toFixed(1), class: 'axis-label' }});
        t.textContent = (val >= 0 ? '+' : '') + val.toFixed(0) + '%';
        g.appendChild(t);
      }});

      pickLabelIndices(n).forEach((i) => {{
        const t = el('text', {{ x: xAt(i, n).toFixed(1), y: H - 8, class: 'axis-label', 'text-anchor': 'middle' }});
        t.textContent = dates[i];
        g.appendChild(t);
      }});

      function linePoints(values) {{
        return values.map((v, i) => xAt(i, n).toFixed(1) + ',' + yAt(v, vmin, vrange).toFixed(1)).join(' ');
      }}
      g.appendChild(el('polyline', {{ points: linePoints(portfolio), fill: 'none', stroke: '#2f6b4f', 'stroke-width': 2.5 }}));
      g.appendChild(el('polyline', {{ points: linePoints(benchmark), fill: 'none', stroke: '#8a6d3b', 'stroke-width': 2.5 }}));

      const guideLine = el('line', {{ x1: 0, y1: padT, x2: 0, y2: H - padB, stroke: '#b9c2b6', 'stroke-width': 1, style: 'display:none' }});
      const dotP = el('circle', {{ r: 4, fill: '#2f6b4f', style: 'display:none' }});
      const dotB = el('circle', {{ r: 4, fill: '#8a6d3b', style: 'display:none' }});
      g.appendChild(guideLine); g.appendChild(dotP); g.appendChild(dotB);
      svg.appendChild(g);

      function onMove(clientX, clientY) {{
        const rect = svg.getBoundingClientRect();
        const viewBoxX = ((clientX - rect.left) / rect.width) * W;
        const fracInPlot = (viewBoxX - padL) / plotW;
        const idx = PerformanceChart.nearestIndex(fracInPlot, n);
        const px = xAt(idx, n), pyP = yAt(portfolio[idx], vmin, vrange), pyB = yAt(benchmark[idx], vmin, vrange);
        guideLine.setAttribute('x1', px); guideLine.setAttribute('x2', px); guideLine.style.display = '';
        dotP.setAttribute('cx', px); dotP.setAttribute('cy', pyP); dotP.style.display = '';
        dotB.setAttribute('cx', px); dotB.setAttribute('cy', pyB); dotB.style.display = '';

        const wrapRect = chartWrap.getBoundingClientRect();
        const pxPixels = (px / W) * rect.width + (rect.left - wrapRect.left);
        tooltip.style.display = 'block';
        tooltip.innerHTML = '<div class="date">' + dates[idx] + '</div>' +
          DATA.portfolioLabel + ': ' + (portfolio[idx] >= 0 ? '+' : '') + portfolio[idx].toFixed(2) + '%<br>' +
          DATA.benchmarkLabel + ': ' + (benchmark[idx] >= 0 ? '+' : '') + benchmark[idx].toFixed(2) + '%';
        const tw = tooltip.offsetWidth || 140;
        let left = pxPixels + 14;
        if (left + tw > wrapRect.width) left = pxPixels - tw - 14;
        tooltip.style.left = left + 'px';
        tooltip.style.top = '14px';
      }}

      svg.addEventListener('mousemove', (e) => onMove(e.clientX, e.clientY));
      svg.addEventListener('touchmove', (e) => {{ if (e.touches[0]) onMove(e.touches[0].clientX, e.touches[0].clientY); }}, {{ passive: true }});
      svg.addEventListener('mouseleave', () => {{
        guideLine.style.display = 'none'; dotP.style.display = 'none'; dotB.style.display = 'none'; tooltip.style.display = 'none';
      }});
    }}

    document.querySelectorAll('#perfControls button').forEach((btn) => {{
      btn.addEventListener('click', () => {{
        document.querySelectorAll('#perfControls button').forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
        render(btn.dataset.range);
      }});
    }});

    render('all');
  }})();
  </script>
"""
    return page("Performance — " + DATA["accountName"], body, active="performance")

def build_about():
    bio = (
        "I'm James, a Freshman at Wake Forest University with a long-running interest "
        "in business and investing. I started this portfolio in October 2022 on Investopedia's "
        "trading simulator to build real research and decision-making experience without "
        "capital risk, still sizing positions deliberately, writing down my thesis in a stock "
        "before buying, and holding through volatility rather than trading the headlines. This "
        "site is where I track that portfolio and publish the reasoning behind it, including the "
        "calls that haven't worked, along with those that have."
    )

    principles = [
        {
            "title": "Paying for good companies",
            "body": "When a business has a durable, specific competitive advantage, I'm willing to pay a higher multiple for it rather than wait for a discount that may never come.",
            "examples": [("NVDA", "CUDA's software lock-in"), ("CDNS", "one of only two EDA providers"), ("VRTX", "a genetic monopoly on cystic fibrosis treatment")],
        },
        {
            "title": "Buy value when the fear is temporary and sector-wide",
            "body": "My best value plays share a pattern: the market panicking about something macro or sector-wide rather than a company-specific problem that's actually getting fixed.",
            "examples": [("C", "turnaround already underway, not just hoped for"), ("XOM", "spending discipline the market didn't believe yet"), ("SCHW", "a brokerage mispriced as a regional bank")],
        },
        {
            "title": "Hold through volatility instead of trading the news",
            "body": "Almost every position states explicitly that I'm holding through short-term moves rather than trying to time entries and exits around quarterly results or headlines.",
            "examples": [("BAC", "\"trading around every rate headline\""), ("QSR", "holding through the slow stretches of a turnaround")],
        },
        {
            "title": "Size positions for how much uncertainty I'm expecting",
            "body": "Low-volatility compounders are used as a stable part of the portfolio, while positions with a wider range of possible outcomes are sized and reviewed more carefully.",
            "examples": [("NEE", "steady, unexciting, sized as ballast"), ("TSLA", "explicitly the widest range of outcomes in the book")],
        },
        {
            "title": "Say plainly when a thesis isn't working",
            "body": "A research site is only useful if the losing calls are as visible as the winners. Nobody wins every trade, so learning from the losers is just as important as learning from the winners.",
            "examples": [("PYPL", "\"it has not gone the way I wanted\"")],
        },
    ]

    principle_cards = "".join(
        f"""<div class="principle-card">
          <h3>{p['title']}</h3>
          <p>{p['body']}</p>
          <div class="examples">{"".join(f'<a href="research/{tk.lower()}.html">{tk}</a>' for tk, _ in p['examples'])}</div>
        </div>"""
        for p in principles
    )

    body = f"""
  <div class="hero">
    <div class="hero-inner">
      <h1>About &amp; Philosophy</h1>
      <p class="tagline">Who's behind this portfolio, and the pattern behind the picks.</p>
    </div>
  </div>
  <div class="section">
    <h2 class="section-title">About</h2>
    <p class="about-bio">{bio}</p>
  </div>
  <div class="section">
    <h2 class="section-title">Investment Philosophy</h2>
    <p class="section-sub">Reading back across all fourteen positions, the same handful of judgment calls show up again and again. Here's the pattern, with the positions that actually demonstrate each one.</p>
    <div class="principle-grid">{principle_cards}</div>
  </div>
"""
    return page("About — " + DATA["accountName"], body, active="about")

def main():
    if SITE.exists():
        shutil.rmtree(SITE)
    (SITE / "research").mkdir(parents=True)
    (SITE / "assets").mkdir(parents=True)
    shutil.copy(ROOT / "assets" / "styles.css", SITE / "assets" / "styles.css")
    shutil.copy(ROOT / "assets" / "performance-chart.js", SITE / "assets" / "performance-chart.js")

    (SITE / "index.html").write_text(build_index())
    (SITE / "about.html").write_text(build_about())
    (SITE / "allocation.html").write_text(build_allocation())
    (SITE / "performance.html").write_text(build_performance())
    (SITE / "research" / "index.html").write_text(build_research_index())
    for h in DATA["holdings"]:
        (SITE / "research" / f"{h['ticker'].lower()}.html").write_text(build_research_page(h))

    n_pages = 5 + len(DATA["holdings"])
    print(f"Built {n_pages} pages into {SITE}/")

if __name__ == "__main__":
    main()
