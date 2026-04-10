"""
system_pipeline_diagram.py
==========================
Generates a **static, high-resolution 2D block diagram (flowchart)** representing
the entire system architecture of the MRI-Compatible Pneumatic Motor.

Designed to be printed on an academic A0 poster at 300 dpi.

Layout (left → right)
----------------------
  Zone 1 — Control Room (Safe Zone)
    Block 1 : Surgeon Input (Joystick)
    Block 2 : Microcontroller (Arduino)
    Block 3 : Electro-Pneumatic Interface (3× Solenoid Valves & 2 Bar Supply)

  ── MRI Shielding Wall (thick dashed vertical line) ──

  Zone 2 — MRI Room (High Magnetic Field Zone)
    Block 4 : 10 m Pneumatic Transmission Lines (Air Tubes)
    Block 5 : 3-Chamber Non-Magnetic Pneumatic Motor
    Block 6 : 2.5:1 Reduction Gearbox
    Block 7 : Catheter Drive Roller & Endovascular Tool

Connection styles
-----------------
  Electrical signal  — green  dashed line  ("Digital PWM")
  Pneumatic power    — blue   solid line   ("2 Bar Pulsed Air")
  Mechanical drive   — black  solid line   ("32 RPM", "8 mm/s")

Output
------
  Displays with plt.show() **and** saves to
  ``simulation/system_pipeline_diagram.png``  (300 dpi, tight bounding box).

Requirements
------------
  pip install matplotlib numpy

Usage
-----
  python simulation/system_pipeline_diagram.py

Author: Sam Tsang (MRI Actuator Project)
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# ---------------------------------------------------------------------------
# Canvas / figure setup
# ---------------------------------------------------------------------------
FIG_W, FIG_H = 22, 10        # inches — gives ~6600 × 3000 px at 300 dpi

fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))

# Clean white background suitable for poster printing
fig.patch.set_facecolor("white")
ax.set_facecolor("#f8f9fa")   # very light grey panel

AX_W, AX_H = 20.0, 8.0       # data-space dimensions
ax.set_xlim(0, AX_W)
ax.set_ylim(0, AX_H)
ax.set_aspect("equal")
ax.set_axis_off()

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
CTRL_FILL   = "#dbeafe"   # light blue  — control-room blocks
CTRL_EDGE   = "#1d4ed8"   # dark blue
MRI_FILL    = "#dcfce7"   # light green — MRI-room blocks
MRI_EDGE    = "#15803d"   # dark green
WALL_COL    = "#6b7280"   # grey for wall
TITLE_COL   = "#111827"   # near-black
ZONE_COL_C  = "#1e40af"   # zone label colour — control room
ZONE_COL_M  = "#166534"   # zone label colour — MRI room

ELEC_COL    = "#16a34a"   # green  — electrical signal arrows
PNEU_COL    = "#2563eb"   # blue   — pneumatic power arrows
MECH_COL    = "#111827"   # black  — mechanical transmission arrows

# ---------------------------------------------------------------------------
# Block geometry helpers
# ---------------------------------------------------------------------------
# Each block is stored as (centre_x, centre_y, half_width, half_height)
BLOCKS = {
    "joystick":   (1.55,  4.0,  1.20,  0.80),
    "arduino":    (4.30,  4.0,  1.20,  0.80),
    "solenoid":   (7.30,  4.0,  1.40,  0.80),
    # ── wall at x ≈ 9.5 ──
    "tubes":      (11.10, 4.0,  1.35,  0.80),
    "motor":      (13.70, 4.0,  1.40,  0.80),
    "gearbox":    (16.20, 4.0,  1.10,  0.80),
    "catheter":   (18.70, 4.0,  1.10,  0.80),
}

WALL_X = 9.50   # x-coordinate of the MRI shielding wall


def cx(name):  return BLOCKS[name][0]
def cy(name):  return BLOCKS[name][1]
def hw(name):  return BLOCKS[name][2]
def hh(name):  return BLOCKS[name][3]
def left(name):  return cx(name) - hw(name)
def right(name): return cx(name) + hw(name)
def top(name):   return cy(name) + hh(name)
def bot(name):   return cy(name) - hh(name)


# ---------------------------------------------------------------------------
# Draw zone backgrounds
# ---------------------------------------------------------------------------
ctrl_bg = mpatches.FancyBboxPatch(
    (0.25, 0.50), WALL_X - 0.55, AX_H - 1.10,
    boxstyle="round,pad=0.15",
    linewidth=2, edgecolor=CTRL_EDGE, facecolor="#eff6ff",
    zorder=1
)
ax.add_patch(ctrl_bg)

mri_bg = mpatches.FancyBboxPatch(
    (WALL_X + 0.30, 0.50), AX_W - WALL_X - 0.55, AX_H - 1.10,
    boxstyle="round,pad=0.15",
    linewidth=2, edgecolor=MRI_EDGE, facecolor="#f0fdf4",
    zorder=1
)
ax.add_patch(mri_bg)

# ---------------------------------------------------------------------------
# Zone labels
# ---------------------------------------------------------------------------
ax.text(
    (0.25 + WALL_X - 0.30) / 2, AX_H - 0.35,
    "ZONE 1 — CONTROL ROOM  (Safe Zone)",
    ha="center", va="center",
    color=ZONE_COL_C, fontsize=19, fontweight="bold",
    zorder=5
)
ax.text(
    (WALL_X + 0.30 + AX_W - 0.25) / 2, AX_H - 0.35,
    "ZONE 2 — MRI ROOM  (High Magnetic Field Zone)",
    ha="center", va="center",
    color=ZONE_COL_M, fontsize=19, fontweight="bold",
    zorder=5
)

# ---------------------------------------------------------------------------
# MRI Shielding Wall
# ---------------------------------------------------------------------------
# Thick dashed vertical line
ax.plot(
    [WALL_X, WALL_X], [0.60, AX_H - 0.60],
    color=WALL_COL, linewidth=5, linestyle="--",
    dash_capstyle="round", zorder=4
)
# Hatched strip
wall_strip = mpatches.Rectangle(
    (WALL_X - 0.18, 0.60), 0.36, AX_H - 1.20,
    linewidth=0, facecolor=WALL_COL, alpha=0.12, zorder=3
)
ax.add_patch(wall_strip)
# Wall label (rotated)
ax.text(
    WALL_X, AX_H * 0.50, "MRI Shielding Wall",
    ha="center", va="center",
    color=WALL_COL, fontsize=14, fontweight="bold",
    rotation=90, zorder=5,
    bbox=dict(facecolor="white", edgecolor=WALL_COL,
              linewidth=1.5, boxstyle="round,pad=0.25", alpha=0.85)
)

# ---------------------------------------------------------------------------
# Helper: draw a rounded block
# ---------------------------------------------------------------------------

def draw_block(name, fill, edge, title, subtitle="", subtitle2=""):
    x = left(name)
    y = bot(name)
    w = 2 * hw(name)
    h = 2 * hh(name)
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.12",
        linewidth=2.5,
        edgecolor=edge,
        facecolor=fill,
        zorder=3
    )
    ax.add_patch(box)

    # Title text
    ax.text(
        cx(name), cy(name) + (0.18 if subtitle else 0.0),
        title,
        ha="center", va="center",
        color=edge, fontsize=16, fontweight="bold",
        zorder=4
    )
    if subtitle:
        ax.text(
            cx(name), cy(name) - 0.22,
            subtitle,
            ha="center", va="center",
            color="#374151", fontsize=14.0,
            zorder=4
        )
    if subtitle2:
        ax.text(
            cx(name), cy(name) - 0.50,
            subtitle2,
            ha="center", va="center",
            color="#374151", fontsize=13.0, fontstyle="italic",
            zorder=4
        )


# ---------------------------------------------------------------------------
# Draw all seven blocks
# ---------------------------------------------------------------------------
draw_block(
    "joystick", CTRL_FILL, CTRL_EDGE,
    "Surgeon Input",
    "Joystick Controller",
)
draw_block(
    "arduino", CTRL_FILL, CTRL_EDGE,
    "Microcontroller",
    "Arduino (ATmega2560)",
)
draw_block(
    "solenoid", CTRL_FILL, CTRL_EDGE,
    "Electro-Pneumatic\nInterface",
    "3× Solenoid Valves",
    "2 Bar Supply",
)
draw_block(
    "tubes", MRI_FILL, MRI_EDGE,
    "Pneumatic\nTransmission Lines",
    "10 m Air Tubes",
    "Ø 6 mm Nylon",
)
draw_block(
    "motor", MRI_FILL, MRI_EDGE,
    "Pneumatic Motor",
    "3-Chamber Non-Magnetic",
    "Rolling Diaphragm",
)
draw_block(
    "gearbox", MRI_FILL, MRI_EDGE,
    "Reduction\nGearbox",
    "2.5 : 1 Ratio",
)
draw_block(
    "catheter", MRI_FILL, MRI_EDGE,
    "Catheter Drive\nRoller",
    "Endovascular Tool",
    "8 mm/s",
)

# ---------------------------------------------------------------------------
# Helper: draw a labelled arrow between two blocks
# ---------------------------------------------------------------------------

def draw_arrow(x0, y0, x1, y1, color, lw, linestyle, label, label_y_offset=0.35):
    """Draw a horizontal arrow and a label above the midpoint."""
    ax.annotate(
        "",
        xy=(x1, y1), xytext=(x0, y0),
        arrowprops=dict(
            arrowstyle="-|>",
            color=color,
            lw=lw,
            linestyle=linestyle,
            mutation_scale=22,
        ),
        zorder=5,
    )
    if label:
        mid_x = (x0 + x1) / 2
        mid_y = (y0 + y1) / 2 + label_y_offset
        ax.text(
            mid_x, mid_y, label,
            ha="center", va="bottom",
            color=color, fontsize=13, fontweight="bold",
            zorder=6,
            bbox=dict(facecolor="white", edgecolor=color,
                      linewidth=1.0, boxstyle="round,pad=0.18", alpha=0.85)
        )


# ---------------------------------------------------------------------------
# Connection 1: Joystick → Arduino  (electrical, green dashed)
# ---------------------------------------------------------------------------
draw_arrow(
    right("joystick"), cy("joystick"),
    left("arduino"),   cy("arduino"),
    color=ELEC_COL, lw=2.5, linestyle="dashed",
    label="Digital PWM"
)

# ---------------------------------------------------------------------------
# Connection 2: Arduino → Solenoid Interface  (electrical, green dashed)
# ---------------------------------------------------------------------------
draw_arrow(
    right("arduino"),  cy("arduino"),
    left("solenoid"),  cy("solenoid"),
    color=ELEC_COL, lw=2.5, linestyle="dashed",
    label="3× PWM Signals"
)

# ---------------------------------------------------------------------------
# Connection 3: Solenoid → Air Tubes  (pneumatic, blue solid, crosses wall)
# ---------------------------------------------------------------------------
draw_arrow(
    right("solenoid"), cy("solenoid"),
    left("tubes"),     cy("tubes"),
    color=PNEU_COL, lw=4.0, linestyle="solid",
    label="2 Bar Pulsed Air"
)

# ---------------------------------------------------------------------------
# Connection 4: Air Tubes → Pneumatic Motor  (pneumatic, blue solid)
# ---------------------------------------------------------------------------
draw_arrow(
    right("tubes"), cy("tubes"),
    left("motor"),  cy("motor"),
    color=PNEU_COL, lw=4.0, linestyle="solid",
    label="2 Bar @ Motor"
)

# ---------------------------------------------------------------------------
# Connection 5: Motor → Gearbox  (mechanical, black solid)
# ---------------------------------------------------------------------------
draw_arrow(
    right("motor"),   cy("motor"),
    left("gearbox"),  cy("gearbox"),
    color=MECH_COL, lw=3.0, linestyle="solid",
    label="32 RPM"
)

# ---------------------------------------------------------------------------
# Connection 6: Gearbox → Catheter Drive Roller  (mechanical, black solid)
# ---------------------------------------------------------------------------
draw_arrow(
    right("gearbox"),  cy("gearbox"),
    left("catheter"),  cy("catheter"),
    color=MECH_COL, lw=3.0, linestyle="solid",
    label="8 mm/s"
)

# ---------------------------------------------------------------------------
# Block index numbers (small badge at top-left corner of each block)
# ---------------------------------------------------------------------------
BLOCK_ORDER = [
    ("joystick",  "1"),
    ("arduino",   "2"),
    ("solenoid",  "3"),
    ("tubes",     "4"),
    ("motor",     "5"),
    ("gearbox",   "6"),
    ("catheter",  "7"),
]
for name, num in BLOCK_ORDER:
    edge = CTRL_EDGE if cx(name) < WALL_X else MRI_EDGE
    ax.text(
        left(name) + 0.14, top(name) - 0.14,
        num,
        ha="center", va="center",
        color="white", fontsize=13, fontweight="bold",
        zorder=7,
        bbox=dict(facecolor=edge, edgecolor="none",
                  boxstyle="circle,pad=0.22")
    )

# ---------------------------------------------------------------------------
# Legend
# ---------------------------------------------------------------------------
legend_handles = [
    mpatches.Patch(facecolor=CTRL_FILL, edgecolor=CTRL_EDGE,
                   linewidth=2, label="Control Room Component"),
    mpatches.Patch(facecolor=MRI_FILL,  edgecolor=MRI_EDGE,
                   linewidth=2, label="MRI Room Component (MRI-Safe)"),
    mpatches.Patch(color=WALL_COL,      label="MRI Shielding Wall"),
    mpatches.Patch(color=ELEC_COL,      label="Electrical Signal (Dashed)"),
    mpatches.Patch(color=PNEU_COL,      label="Pneumatic Power (Solid, Thick)"),
    mpatches.Patch(color=MECH_COL,      label="Mechanical Transmission (Solid)"),
]
ax.legend(
    handles=legend_handles,
    loc="lower center",
    ncol=3,
    fontsize=14,
    facecolor="white",
    edgecolor="#d1d5db",
    framealpha=0.95,
    bbox_to_anchor=(0.5, -0.01),
    title="Legend",
    title_fontsize=15,
)

# ---------------------------------------------------------------------------
# Main title
# ---------------------------------------------------------------------------
fig.suptitle(
    "MRI-Compatible Pneumatic Motor — System Architecture Pipeline",
    fontsize=26, fontweight="bold",
    color=TITLE_COL, y=0.97,
)

# ---------------------------------------------------------------------------
# Save and show
# ---------------------------------------------------------------------------
plt.tight_layout(rect=[0, 0.07, 1, 0.96])
plt.savefig(
    "simulation/system_pipeline_diagram.png",
    dpi=300,
    bbox_inches="tight",
    facecolor="white",
)
plt.show()
