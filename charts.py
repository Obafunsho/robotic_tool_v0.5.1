"""
Static charts (PNG bytes) for the Word business case: a tornado chart and a
cost-versus-cost-avoided chart. The website draws the same data with Altair.
"""
import io
import logging

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

NAVY = "#1F3864"
TEAL = "#2E8B8B"
GREY = "#8C8C8C"
LIGHT = "#BFBFBF"
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
plt.rcParams.update({"font.family": "sans-serif",
                     "font.sans-serif": ["Arial", "Liberation Sans", "Helvetica", "DejaVu Sans"],
                     "font.size": 9})


def _gbp(x):
    if x is None:
        return "n/a"
    if abs(x) >= 1e6:
        return f"£{x / 1e6:,.2f}M"
    return f"£{x:,.0f}"


def _png(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def tornado_png(t, max_bars=10):
    """t is the dict returned by sensitivity.tornado()."""
    bars = t["bars"][:max_bars][::-1]
    base = t["base"]
    fig, ax = plt.subplots(figsize=(7.2, 0.42 * max(len(bars), 3) + 1.0))
    for i, b in enumerate(bars):
        for val, lab, col in ((b["low"], b["low_label"], TEAL), (b["high"], b["high_label"], NAVY)):
            left, width = min(base, val), abs(val - base)
            ax.barh(i, width, left=left, color=col, height=0.6)
            if width > 0:
                x = val
                ha = "left" if val > base else "right"
                ax.text(x, i, f" {lab} ", va="center", ha=ha, fontsize=7, color="#404040")
    ax.axvline(base, color=GREY, lw=1)
    ax.set_yticks(range(len(bars)))
    ax.set_yticklabels([b["name"] for b in bars], fontsize=8)
    ax.set_xlabel(f"{t['metric_label']} (base case {_gbp(base)})")
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: _gbp(v)))
    lo = min([base] + [min(b["low"], b["high"]) for b in bars])
    hi = max([base] + [max(b["low"], b["high"]) for b in bars])
    pad = (hi - lo) * 0.35 or abs(base) * 0.1 or 1
    ax.set_xlim(lo - pad, hi + pad)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=TEAL, label="Low setting"), Patch(color=NAVY, label="High setting")],
              loc="lower right", fontsize=7, frameon=False)
    return _png(fig)


COST_PARTS = [("platform_fixed", "Platform"), ("instruments", "Instruments"),
              ("decontamination", "Sterile services"), ("staffing", "Surgical first assistant"),
              ("theatre_time_cost", "Extra theatre time"),
              ("implementation", "Implementation and training"),
              ("theatre_modification", "Theatre works")]
PART_COLOURS = [NAVY, TEAL, "#7FA7C9", "#A9C5A0", "#C9B37F", "#B0B0B0", "#D9D9D9"]


def cost_offset_png(yearly):
    """Stacked extra cost by year, with 30-day cost avoided as a line (not cash)."""
    years = [y["year"] for y in yearly]
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    bottom = [0.0] * len(years)
    for (key, lab), col in zip(COST_PARTS, PART_COLOURS):
        vals = [y.get(key, 0.0) / 1e3 for y in yearly]
        if not any(vals):
            continue
        ax.bar(years, vals, bottom=bottom, color=col, label=lab, width=0.6)
        bottom = [b + v for b, v in zip(bottom, vals)]
    ax.plot(years, [y["offsets"] / 1e3 for y in yearly], color="#C00000", marker="o", lw=1.5,
            label="30-day cost avoided (not cash)")
    ax.set_xticks(years)
    ax.set_xticklabels([f"Year {y}" for y in years])
    ax.set_ylabel("£ thousands")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(fontsize=7, frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.12))
    return _png(fig)
