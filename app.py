"""
Sabatier vs SMR breakeven regime map.

Plots the (natural gas price, hydrogen price) plane and shades the regions
where methanation of H2 into CH4 pays, where reforming CH4 into H2 pays,
and the wedge between them where neither does.

Run with:  streamlit run app.py
"""

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter

# ----------------------------------------------------------------------------
# Physical constants
# ----------------------------------------------------------------------------
MJ_PER_MMBTU = 1055.06
HHV_CH4 = 55.5      # MJ/kg
HHV_H2 = 141.8      # MJ/kg

KG_CH4_PER_MMBTU = MJ_PER_MMBTU / HHV_CH4          # 19.01
MMBTU_PER_KG_H2 = HHV_H2 / MJ_PER_MMBTU            # 0.1344, energy parity slope

# Sabatier: CO2 + 4 H2 -> CH4 + 2 H2O
H2_PER_CH4_MASS = (4 * 2.016) / 16.043             # 0.5026 kg H2 per kg CH4
CO2_PER_CH4_MASS = 44.010 / 16.043                 # 2.743 kg CO2 per kg CH4
SINGLE_PASS = 0.985                                # real conversion incl. recycle losses

KG_H2_PER_MMBTU = KG_CH4_PER_MMBTU * H2_PER_CH4_MASS / SINGLE_PASS   # ~9.70
T_CO2_PER_MMBTU = KG_CH4_PER_MMBTU * CO2_PER_CH4_MASS / 1000.0       # ~0.0521

# SMR: stoichiometry is 2 kg CH4/kg H2; real plants burn ~3.3 including process fuel
MMBTU_PER_KG_H2_SMR = 3.3 / KG_CH4_PER_MMBTU                          # ~0.174

# ----------------------------------------------------------------------------
# Palette
# ----------------------------------------------------------------------------
C_SMR = "#2a5d9f"
C_SAB = "#c85a29"
C_DEAD = "#8c8a83"
C_INK = "#1b1b19"
C_MUTED = "#6e6c66"
C_GRID = "#dcdad2"


def breakeven_h2_for_sabatier(p_gas, k_sab):
    """Max H2 price ($/kg) at which methanation clears, given gas price."""
    return (p_gas - k_sab) / KG_H2_PER_MMBTU


def breakeven_h2_for_smr(p_gas, k_smr):
    """Cost of SMR hydrogen ($/kg) at a given gas price."""
    return MMBTU_PER_KG_H2_SMR * p_gas + k_smr


def make_figure(k_sab_capex, co2_price, k_smr, markers, xlim, ylim, show_ideal):
    k_sab = k_sab_capex + co2_price * T_CO2_PER_MMBTU

    x = np.logspace(np.log10(xlim[0]), np.log10(xlim[1]), 400)
    y_sab = np.clip(breakeven_h2_for_sabatier(x, k_sab), ylim[0] * 0.5, ylim[1] * 2)
    y_smr = np.clip(breakeven_h2_for_smr(x, k_smr), ylim[0] * 0.5, ylim[1] * 2)

    fig, ax = plt.subplots(figsize=(9.5, 6.4))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    ax.fill_between(x, y_smr, ylim[1] * 2, color=C_SMR, alpha=0.13, lw=0)
    ax.fill_between(x, ylim[0] * 0.5, y_sab, color=C_SAB, alpha=0.15, lw=0)
    ax.fill_between(x, y_sab, y_smr, color=C_DEAD, alpha=0.10, lw=0)

    if show_ideal:
        ax.plot(x, breakeven_h2_for_sabatier(x, 0.0), color=C_SAB,
                lw=1.4, ls=(0, (5, 4)), alpha=0.6, zorder=3)
        ax.plot(x, breakeven_h2_for_smr(x, 0.0), color=C_SMR,
                lw=1.4, ls=(0, (5, 4)), alpha=0.6, zorder=3)

    ax.plot(x, MMBTU_PER_KG_H2 * x, color=C_MUTED, lw=1.2,
            ls=(0, (1, 3)), zorder=3)
    ax.plot(x, y_smr, color=C_SMR, lw=2.2, zorder=4)
    ax.plot(x, y_sab, color=C_SAB, lw=2.2, zorder=4)

    for m in markers:
        if not (xlim[0] <= m["x"] <= xlim[1] and ylim[0] <= m["y"] <= ylim[1]):
            continue
        ax.plot(m["x"], m["y"], "o", ms=7, color=C_INK,
                mec="white", mew=1.4, zorder=6)
        ax.annotate(
            m["label"],
            xy=(m["x"], m["y"]),
            xytext=(m.get("dx", 10), m.get("dy", 8)),
            textcoords="offset points",
            fontsize=9.5,
            color=C_INK,
            ha=m.get("ha", "left"),
            zorder=6,
        )

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)

    fmt = FuncFormatter(lambda v, _: f"{v:g}")

    def ticks(lo, hi):
        base = [1, 1.5, 2, 3, 5, 7]
        out = []
        for dec in range(-2, 4):
            out += [b * 10 ** dec for b in base]
        return [t for t in out if lo <= t <= hi]

    ax.set_xticks(ticks(*xlim))
    ax.set_yticks(ticks(*ylim))
    for axis in (ax.xaxis, ax.yaxis):
        axis.set_major_formatter(fmt)
        axis.set_minor_formatter(FuncFormatter(lambda v, _: ""))

    ax.set_xlabel("Natural gas price  ($/MMBtu)", fontsize=11, color=C_MUTED, labelpad=10)
    ax.set_ylabel("Hydrogen price  ($/kg)", fontsize=11, color=C_MUTED, labelpad=10)

    ax.grid(True, which="major", color=C_GRID, lw=0.8)
    ax.grid(True, which="minor", color=C_GRID, lw=0.4, alpha=0.5)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(C_GRID)
    ax.tick_params(colors=C_MUTED, labelsize=9.5)

    ax.text(0.03, 0.95, "SMR is economic", transform=ax.transAxes,
            fontsize=12, color=C_SMR, va="top")
    ax.text(0.03, 0.905, "It is profitable to convert methane to hydrogen", transform=ax.transAxes,
            fontsize=9.5, color=C_MUTED, va="top")
    ax.text(0.97, 0.09, "Sabatier is economic", transform=ax.transAxes,
            fontsize=12, color=C_SAB, ha="right", va="bottom")
    ax.text(0.97, 0.045, "It is profitable to convert hydrogen to methane", transform=ax.transAxes,
            fontsize=9.5, color=C_MUTED, ha="right", va="bottom")

    handles = [
        Line2D([], [], color=C_SMR, lw=2.2, label="SMR breakeven"),
        Line2D([], [], color=C_SAB, lw=2.2, label="Sabatier breakeven"),
        Line2D([], [], color=C_MUTED, lw=1.2, ls=(0, (1, 3)), label="Energy parity (HHV)"),
    ]
    if show_ideal:
        handles.append(
            Line2D([], [], color=C_MUTED, lw=1.4, ls=(0, (5, 4)),
                   label="Zero-capex limit")
        )
    leg = ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.03, 0.03),
                    frameon=True, facecolor="white", edgecolor="none",
                    framealpha=0.92, fontsize=9.5, labelcolor=C_MUTED)
    leg.set_zorder(7)
    for t in leg.get_texts():
        t.set_color(C_MUTED)

    fig.tight_layout()
    return fig, k_sab


# ----------------------------------------------------------------------------
# App
# ----------------------------------------------------------------------------
st.set_page_config(page_title="Sabatier vs SMR", layout="wide")

st.title("When does it make sense to convert methane to hydrogen or vice versa?")
st.caption(
    f"Sabatier consumes {KG_H2_PER_MMBTU:.1f} kg of H\u2082 per MMBtu of CH\u2084. SMR "
    f"consumes {MMBTU_PER_KG_H2_SMR:.3f} MMBtu of gas per kg of H\u2082."
)

with st.sidebar:
    st.header("Cost adders")

    k_sab_capex = st.slider(
        "Sabatier reactor capex + opex  ($/MMBtu)",
        0.0, 10.0, 2.0, 0.25,
        help="Methanation reactor, compression and gas upgrading only. The "
             "electrolyser and its power are already priced into the H\u2082 axis.",
    )
    co2_price = st.slider(
        "CO\u2082 feedstock  ($/tonne)",
        0, 400, 0, 10,
        help=f"Enters at {T_CO2_PER_MMBTU:.4f} tonnes per MMBtu of product gas. "
             "Vented biogenic CO\u2082 is near zero; DAC today is $250\u2013600.",
    )
    k_smr = st.slider(
        "SMR capex + opex  ($/kg H\u2082)",
        0.0, 3.0, 0.60, 0.05,
        help="Non-gas costs for a large-scale reformer.",
    )

    st.header("View")
    show_ideal = st.checkbox("Show zero-capex limits", value=True)
    x_hi = st.slider("Gas axis maximum  ($/MMBtu)", 20, 200, 60, 10)
    y_hi = st.slider("H\u2082 axis maximum  ($/kg)", 10, 100, 30, 5)

markers = [
    {"x": 3.50, "y": 5.00, "label": "US green H₂ typical", "dx": 10, "dy": 8},
    {"x": 3.50, "y": 1.50, "label": "US typical", "dx": 10, "dy": -16},
    {"x": 11.0, "y": 7.00, "label": "EU green H₂ typical", "dx": -10, "dy": 8, "ha": "right"},
    {"x": 11.0, "y": 3.50, "label": "EU typical", "dx": -10, "dy": -16, "ha": "right"},
]

fig, _ = make_figure(
    k_sab_capex, co2_price, k_smr, markers,
    xlim=(1.0, float(x_hi)), ylim=(0.2, float(y_hi)),
    show_ideal=show_ideal,
)
st.pyplot(fig, use_container_width=True)

with st.expander("What the lines mean"):
    st.markdown(
        f"""
The two boundaries are the same arithmetic run in opposite directions.

**Sabatier** breaks even when `P_gas = {KG_H2_PER_MMBTU:.2f} x P_H2 + K_sab`, where
`K_sab` is reactor capex plus CO\u2082 at {T_CO2_PER_MMBTU:.4f} t/MMBtu. Below that
line, hydrogen is cheap enough relative to gas that turning it into methane
makes money.

**SMR** breaks even when `P_H2 = {MMBTU_PER_KG_H2_SMR:.3f} x P_gas + K_smr`. Above
that line, hydrogen is expensive enough that reforming gas beats buying it.

The SMR line is steeper and sits above the Sabatier line everywhere in the
positive quadrant, so the two never cross. The gap between them is the
round-trip loss, and it widens as prices rise.

The dotted line is energy parity: 1 kg of H\u2082 carries
{MMBTU_PER_KG_H2:.4f} MMBtu HHV. The two boundaries straddle it at
{100 * MMBTU_PER_KG_H2 / MMBTU_PER_KG_H2_SMR:.0f} percent (SMR) and
{100 / (MMBTU_PER_KG_H2 * KG_H2_PER_MMBTU):.0f} percent (Sabatier) conversion
efficiency. With the capex sliders at zero the solid lines collapse onto the
dashed ones, so everything between dashed and solid is equipment cost rather
than physics.

The 9.7:1 slope on the Sabatier side is why gas price is the stronger lever:
halving your hydrogen cost moves you as far as a 2x move in gas, and gas
prices genuinely do 2x.
        """
    )
