"""
pneumatic_circuit_animation.py
===============================
2-D animation of the complete electro-pneumatic control system for the
MRI-compatible three-chamber rolling-diaphragm pneumatic motor.

System overview
---------------
  * An **Arduino** microcontroller generates three PWM/digital outputs, each
    controlling one solenoid valve via a 5 V signal line.
  * Three **Solenoid Valves** (A, B, C) connect the 2-bar compressed-air
    supply to the three pneumatic chambers.
  * Three **Pneumatic Chambers** (Cylinders A, B, C) drive the wavy cam track.
  * The valves fire in a 120°-apart H-L-H sequence (High → Low → High) so
    that the motor torque is always sustained by at least one active chamber.

Animation sequence
------------------
  A 360° virtual cycle is split into three 120° phases:
    Phase 0°  – 120°  : Valve A  ON  → Cylinder A  pressurised (Red)
    Phase 120°– 240°  : Valve B  ON  → Cylinder B  pressurised (Red)
    Phase 240°– 360°  : Valve C  ON  → Cylinder C  pressurised (Red)

  When a valve is ON:
    • Electrical signal line from Arduino → that valve  : Green / Yellow
    • Air supply line from valve → cylinder              : Red (high pressure)
    • Cylinder body fills with Red tint
  When a valve is OFF:
    • Electrical line  : Light grey
    • Air line         : Steel blue / Light grey (exhaust / venting)
    • Cylinder tint    : Light blue-grey

  Live telemetry overlay:
    "Phase Angle : X°"
    "Active Valve : A / B / C"
    "Pressure     : 2.0 bar (ON) / 0.0 bar (OFF)"

Requirements
------------
  pip install numpy matplotlib

Usage
-----
  python pneumatic_circuit_animation.py

Author: Sam Tsang (MRI Actuator Project)
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.animation as animation
from matplotlib.lines import Line2D

# ---------------------------------------------------------------------------
# Layout positions (all in "drawing units")
# ---------------------------------------------------------------------------

# Arduino controller block
ARD_X, ARD_Y = 0.50, 8.40    # centre
ARD_W, ARD_H = 1.20, 0.80

# Main air supply line (horizontal bar at the top)
SUPPLY_Y    = 6.60
SUPPLY_X0   = 0.30
SUPPLY_X1   = 4.70

# Valve positions (centre x, y) – evenly spaced horizontally
VALVE_Y     = 5.20
VALVE_CX    = [1.00, 2.50, 4.00]   # A, B, C
VALVE_W     = 0.55
VALVE_H     = 0.42

# Cylinder positions (centre x, bottom y)
CYL_TOP_Y   = 4.00
CYL_BOT_Y   = 1.80
CYL_CX      = [1.00, 2.50, 4.00]  # A, B, C
CYL_W       = 0.70
CYL_H       = CYL_TOP_Y - CYL_BOT_Y

# Piston head inside each cylinder
PISTON_H    = 0.22

# Colours
COL_BG       = "#F4F4EF"
COL_DARK     = "#1E1E2E"
COL_WALL     = "#3A3A4A"
COL_ARD      = "#2A6EBB"   # Arduino blue
COL_VALVE_ON = "#22CC44"   # bright green valve body (active)
COL_VALVE_OFF= "#888888"   # grey valve body (inactive)
COL_AIR_ON   = "#CC2222"   # red – pressurised air line / chamber
COL_AIR_OFF  = "#99AACC"   # steel blue-grey – exhaust / idle
COL_SIG_ON   = "#AAEE00"   # yellow-green – active electrical signal
COL_SIG_OFF  = "#CCCCCC"   # light grey – inactive electrical signal
COL_SUPPLY   = "#445566"   # main supply line (always live)
COL_SUPPLY_FILL = "#3399FF"  # 2-bar supply colour

VALVE_LABELS = ["A", "B", "C"]

# Animation timing
FPS       = 60
N_FRAMES  = 240     # one full electrical cycle
INTERVAL  = int(1000 / FPS)


# ---------------------------------------------------------------------------
# Figure / axes
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(7, 9.5))
fig.patch.set_facecolor(COL_BG)
ax.set_facecolor(COL_BG)
ax.set_xlim(0.0, 5.2)
ax.set_ylim(0.8, 9.8)
ax.set_aspect("equal")
ax.axis("off")

ax.set_title(
    "Electro-Pneumatic Control Circuit\n"
    "MRI-Compatible Three-Chamber Pneumatic Motor",
    fontsize=14.0, fontweight="bold", color=COL_DARK, pad=8,
)


# ---------------------------------------------------------------------------
# Helper: draw a rounded box and return the patch
# ---------------------------------------------------------------------------
def rounded_box(cx, cy, w, h, fc, ec, lw=1.5, alpha=1.0, zorder=4, radius=0.06):
    patch = mpatches.FancyBboxPatch(
        (cx - w / 2, cy - h / 2), w, h,
        boxstyle=f"round,pad={radius}",
        facecolor=fc, edgecolor=ec, linewidth=lw,
        alpha=alpha, zorder=zorder,
    )
    ax.add_patch(patch)
    return patch


# ---------------------------------------------------------------------------
# STATIC ELEMENTS
# ---------------------------------------------------------------------------

# ── Arduino controller block ──────────────────────────────────────────────
rounded_box(ARD_X + 0.50 * (SUPPLY_X1 - SUPPLY_X0),  # centre of layout
            ARD_Y, ARD_W * 2.2, ARD_H,
            fc=COL_ARD, ec="#112244", lw=2, zorder=5)
ax.text(
    ARD_X + 0.50 * (SUPPLY_X1 - SUPPLY_X0), ARD_Y,
    "Arduino Controller",
    ha="center", va="center", fontsize=12, color="white",
    fontweight="bold", zorder=6,
)

# ── Main 2-bar compressed-air supply line (horizontal) ────────────────────
supply_line = ax.add_line(
    Line2D([SUPPLY_X0, SUPPLY_X1], [SUPPLY_Y, SUPPLY_Y],
           color=COL_SUPPLY_FILL, lw=5, solid_capstyle="round", zorder=3)
)
ax.text(SUPPLY_X0 - 0.22, SUPPLY_Y,
        "2 bar\nSupply", ha="right", va="center", fontsize=11.0,
        color=COL_SUPPLY, fontweight="bold")

# Arrow from supply line to show flow direction
ax.annotate("", xy=(SUPPLY_X1 + 0.05, SUPPLY_Y),
            xytext=(SUPPLY_X1 - 0.35, SUPPLY_Y),
            arrowprops=dict(arrowstyle="-|>", color=COL_SUPPLY, lw=1.5),
            zorder=4)

# ── Supply vertical drops to each valve (always present) ──────────────────
for vx in VALVE_CX:
    ax.add_line(Line2D([vx, vx], [SUPPLY_Y, VALVE_Y + VALVE_H / 2],
                       color=COL_SUPPLY_FILL, lw=3.5, zorder=3))


# ---------------------------------------------------------------------------
# DYNAMIC ELEMENTS – create once, update in animate()
# ---------------------------------------------------------------------------

# Electrical signal lines: Arduino → each valve
# Drawn as slightly offset lines so they don't overlap the air lines
sig_lines   = []
SIG_OFFSET  = 0.16    # horizontal offset from centre
for i, vx in enumerate(VALVE_CX):
    # Signal runs from Arduino output (at the bottom edge of the Arduino box)
    # down to the valve top
    ard_cx = ARD_X + 0.50 * (SUPPLY_X1 - SUPPLY_X0)
    # Use a two-segment path: right from Arduino, then down to valve
    line = ax.add_line(
        Line2D(
            [ard_cx + (i - 1) * 0.42,  vx - SIG_OFFSET, vx - SIG_OFFSET],
            [ARD_Y - ARD_H / 2,        ARD_Y - ARD_H / 2 - 0.80, VALVE_Y + VALVE_H / 2],
            color=COL_SIG_OFF, lw=1.8, ls="--", zorder=4,
        )
    )
    sig_lines.append(line)

# Air lines: valve bottom → cylinder top
air_lines = []
for i, (vx, cx) in enumerate(zip(VALVE_CX, CYL_CX)):
    line = ax.add_line(
        Line2D([vx, cx], [VALVE_Y - VALVE_H / 2, CYL_TOP_Y],
               color=COL_AIR_OFF, lw=3.5, solid_capstyle="round", zorder=3)
    )
    air_lines.append(line)

# Valve body patches (one per valve)
valve_patches = []
valve_labels  = []
for i, vx in enumerate(VALVE_CX):
    p = rounded_box(vx, VALVE_Y, VALVE_W, VALVE_H,
                    fc=COL_VALVE_OFF, ec=COL_WALL, lw=1.5, zorder=5)
    valve_patches.append(p)
    t = ax.text(vx, VALVE_Y, f"Valve {VALVE_LABELS[i]}",
                ha="center", va="center", fontsize=11.0,
                color="white", fontweight="bold", zorder=6)
    valve_labels.append(t)

# Cylinder body patches (one per cylinder)
cyl_patches   = []   # outer rectangle (static)
fill_patches  = []   # interior fill (dynamic colour)
piston_patches= []   # piston head rectangle
cyl_texts     = []   # "Cyl A/B/C" labels

for i, cx in enumerate(CYL_CX):
    # Outer wall (always drawn)
    outer = mpatches.Rectangle(
        (cx - CYL_W / 2, CYL_BOT_Y), CYL_W, CYL_H,
        linewidth=2, edgecolor=COL_WALL, facecolor="none", zorder=5,
    )
    ax.add_patch(outer)
    cyl_patches.append(outer)

    # Interior fill
    fill = mpatches.Rectangle(
        (cx - CYL_W / 2 + 0.03, CYL_BOT_Y + 0.03),
        CYL_W - 0.06, CYL_H - PISTON_H - 0.06,
        linewidth=0, facecolor=COL_AIR_OFF, alpha=0.35, zorder=4,
    )
    ax.add_patch(fill)
    fill_patches.append(fill)

    # Piston head
    piston = mpatches.Rectangle(
        (cx - CYL_W / 2 + 0.05, CYL_TOP_Y - PISTON_H),
        CYL_W - 0.10, PISTON_H,
        linewidth=1.2, edgecolor="#334455", facecolor="#6A7E9A", zorder=6,
    )
    ax.add_patch(piston)
    piston_patches.append(piston)

    # Label below cylinder
    t = ax.text(cx, CYL_BOT_Y - 0.25, f"Cyl {VALVE_LABELS[i]}",
                ha="center", va="top", fontsize=11, color=COL_DARK,
                fontweight="bold")
    cyl_texts.append(t)


# ---------------------------------------------------------------------------
# Telemetry text
# ---------------------------------------------------------------------------
tele_box = dict(facecolor="#FFFFFFCC", edgecolor="#AAAAAA",
                boxstyle="round,pad=0.45")
txt_angle = ax.text(0.08, 1.55, "Phase Angle : 0°",
                    fontsize=12, color=COL_DARK, fontfamily="monospace",
                    bbox=tele_box, zorder=10, transform=ax.transData)
txt_valve = ax.text(0.08, 1.20, "Active Valve : A",
                    fontsize=12, color=COL_AIR_ON, fontfamily="monospace",
                    zorder=10, transform=ax.transData)
txt_press = ax.text(0.08, 0.90, "Pressure     : 2.0 bar",
                    fontsize=12, color=COL_AIR_ON, fontfamily="monospace",
                    zorder=10, transform=ax.transData)

# Small legend patches
legend_elements = [
    mpatches.Patch(facecolor=COL_AIR_ON,  label="High pressure (2.0 bar)"),
    mpatches.Patch(facecolor=COL_AIR_OFF, label="Exhaust / Idle"),
    Line2D([0], [0], color=COL_SIG_ON, lw=2, ls="--", label="Signal ON"),
    Line2D([0], [0], color=COL_SIG_OFF, lw=1.5, ls="--", label="Signal OFF"),
]
ax.legend(handles=legend_elements, loc="lower right",
          fontsize=11.0, framealpha=0.85, edgecolor="#AAAAAA",
          bbox_to_anchor=(5.1, 0.82), bbox_transform=ax.transData)


# ---------------------------------------------------------------------------
# Piston vertical motion per cylinder (sinusoidal, phased 120° apart)
# ---------------------------------------------------------------------------
PHASE_OFFSETS_DEG = [0, 120, 240]   # degrees

def piston_fill_height(angle_deg: float, phase_offset_deg: float) -> float:
    """Return normalised fill height [0, 1] for a cylinder given cycle angle."""
    theta = np.deg2rad(angle_deg - phase_offset_deg)
    raw   = 0.5 * (1.0 + np.sin(theta))    # 0 → 1 → 0
    return float(np.clip(raw, 0.05, 0.95))


# ---------------------------------------------------------------------------
# Animation update function
# ---------------------------------------------------------------------------

def animate(frame: int):
    angle_deg = (frame / N_FRAMES) * 360.0   # 0 → 360 over one cycle

    # Which valve is active? (120° window each)
    active_idx = int(angle_deg // 120) % 3   # 0=A, 1=B, 2=C

    for i in range(3):
        on = (i == active_idx)

        # ── Electrical signal line ─────────────────────────────────────────
        sig_lines[i].set_color(COL_SIG_ON if on else COL_SIG_OFF)
        sig_lines[i].set_linewidth(2.2 if on else 1.4)

        # ── Valve body colour ──────────────────────────────────────────────
        valve_patches[i].set_facecolor(COL_VALVE_ON if on else COL_VALVE_OFF)

        # ── Air supply line (valve → cylinder) ────────────────────────────
        air_lines[i].set_color(COL_AIR_ON if on else COL_AIR_OFF)
        air_lines[i].set_linewidth(4.0 if on else 2.5)

        # ── Cylinder fill (pressure builds) ───────────────────────────────
        fh = piston_fill_height(angle_deg, PHASE_OFFSETS_DEG[i])
        fill_height = fh * (CYL_H - PISTON_H - 0.06)
        fill_patches[i].set_height(fill_height)
        fill_patches[i].set_facecolor(COL_AIR_ON if on else COL_AIR_OFF)
        fill_patches[i].set_alpha(0.50 if on else 0.25)

        # ── Piston position ────────────────────────────────────────────────
        piston_y = CYL_BOT_Y + 0.03 + fill_height
        piston_patches[i].set_y(piston_y)

    # ── Telemetry ──────────────────────────────────────────────────────────
    txt_angle.set_text(f"Phase Angle : {angle_deg:.0f}°")
    txt_valve.set_text(f"Active Valve : {VALVE_LABELS[active_idx]}")
    txt_press.set_text(f"Pressure     : 2.0 bar (ON)  — Valve {VALVE_LABELS[active_idx]}")
    txt_valve.set_color(COL_AIR_ON)
    txt_press.set_color(COL_AIR_ON)

    return (*sig_lines, *air_lines, *valve_patches, *fill_patches,
            *piston_patches, txt_angle, txt_valve, txt_press)


# ---------------------------------------------------------------------------
# Run animation
# ---------------------------------------------------------------------------
ani = animation.FuncAnimation(
    fig, animate,
    frames=N_FRAMES,
    interval=INTERVAL,
    blit=True,
)

plt.tight_layout()
plt.show()
