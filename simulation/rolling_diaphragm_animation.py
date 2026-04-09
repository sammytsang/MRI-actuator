"""
rolling_diaphragm_animation.py
==============================
2-D cross-section animation of a single pneumatic chamber showing the
**rolling diaphragm** mechanism used in the MRI-compatible pneumatic motor.

Unlike a conventional piston with rubber O-rings (which generate stiction due
to sliding contact), a rolling diaphragm uses a thin flexible membrane that
*unrolls* along the cylinder wall as the piston moves.  This eliminates
stick-slip friction entirely, enabling the 0.1 N fine-force resolution
required for endovascular (PCI / TAVR / TMVR) procedures.

Visual components
-----------------
  * Outer cylinder walls (fixed, dark grey).
  * Piston head (solid block) and rod, moving sinusoidally.
  * Diaphragm: flexible membrane drawn as a Bezier / spline curve that
    connects the outer edge of the piston head to the cylinder wall. As the
    piston rises the U-shaped fold migrates upward (the diaphragm "rolls"),
    preserving zero sliding contact.
  * Air-volume fill:
        Upward (pressurised) stroke  → Red   (#CC2222)
        Downward (exhaust) stroke    → Light steel-blue (#AABCCC)
  * Annotations: live stroke readout, force level, mechanism label.

Requirements
------------
  pip install numpy matplotlib

Usage
-----
  python rolling_diaphragm_animation.py

Author: Sam Tsang (MRI Actuator Project)
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.animation as animation
from matplotlib.path import Path
import matplotlib.patches as patches

# ---------------------------------------------------------------------------
# Geometry constants (all in arbitrary "drawing units")
# ---------------------------------------------------------------------------
CYL_LEFT   = -1.0          # inner left wall x
CYL_RIGHT  =  1.0          # inner right wall x
CYL_BOTTOM = -3.5          # bottom of cylinder (air inlet)
CYL_TOP    =  4.0          # top of cylinder (open to rod seal)

PISTON_W   = 1.8           # piston head width (extends slightly outside bore)
PISTON_H   = 0.45          # piston head height
ROD_W      = 0.18          # piston rod width
ROD_TOP    = CYL_TOP + 0.8 # top extent of piston rod (above cylinder)

WALL_THICK = 0.22          # cylinder wall thickness for drawing

# Piston travel limits (centre of piston head)
PISTON_MID    = 0.5        # neutral / mid position
PISTON_AMP    = 2.0        # ± amplitude of sinusoidal stroke

DIAPHRAGM_WALL_Y = 1.8     # y-level at which the diaphragm attaches to wall
                            # (upper flange, fixed clamping point)

# Animation timing
FPS        = 60
N_FRAMES   = 180           # one complete cycle
INTERVAL   = int(1000 / FPS)   # ms between frames


# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
COL_WALL        = "#2B2B2B"
COL_PISTON      = "#5A6E8C"
COL_ROD         = "#8090A8"
COL_AIR_PRESS   = "#CC2222"   # red – pressurised stroke
COL_AIR_EXHAUST = "#AABCCC"   # light steel blue – exhaust stroke
COL_DIAPHRAGM   = "#E8D0A0"   # cream / light tan for rubber membrane
COL_ANNOT       = "#1A1A2E"
COL_BG          = "#F5F5F0"


# ---------------------------------------------------------------------------
# Helper: build diaphragm Path using a cubic Bezier approximation
# ---------------------------------------------------------------------------

def diaphragm_path(piston_y: float) -> Path:
    """
    Return a matplotlib Path for the rolling diaphragm.

    The diaphragm is approximated as a smooth polygon built from sampled
    points on two mirrored cubic Bezier curves (right side and left side).
    The curve runs from the piston head outer edge, rolls into a U-fold at
    the cylinder wall level, then back up to the fixed wall clamp point.

    Parameters
    ----------
    piston_y : float
        Y-coordinate of the *top* face of the piston head.
    """
    wall_y        = DIAPHRAGM_WALL_Y
    piston_edge_y = piston_y - PISTON_H   # bottom face of piston head

    # Fold apex sits roughly halfway between wall clamp and piston bottom
    fold_y     = 0.5 * (wall_y + piston_edge_y)
    fold_depth = 0.30 + 0.20 * max(
        0.0, (piston_edge_y - wall_y) / (2 * PISTON_AMP)
    )

    # ── Build right-side cubic Bezier via de Casteljau / parametric form ──
    # Segment 1: piston outer edge → fold apex (against right wall)
    R   = CYL_RIGHT * 0.88        # x of piston head right edge
    rw  = CYL_RIGHT               # x of right inner wall

    # Bezier control points for the downward-then-outward sweep
    cp_r1 = np.array([
        [R,                         piston_edge_y          ],   # P0 (start)
        [rw * 0.95,                 piston_edge_y - 0.30   ],   # P1 (cp1)
        [rw - fold_depth * 0.5,    fold_y + 0.35          ],   # P2 (cp2)
        [rw,                        fold_y                 ],   # P3 (end)
    ])
    # Bezier control points for the inward-then-upward sweep to wall clamp
    cp_r2 = np.array([
        [rw,                        fold_y                 ],   # P0 (start)
        [rw - fold_depth * 0.5,    fold_y - 0.35          ],   # P1 (cp1)
        [rw,                        wall_y + 0.20          ],   # P2 (cp2)
        [rw,                        wall_y                 ],   # P3 (end)
    ])

    n_pts = 20   # number of samples per Bezier segment

    def bezier(cp: np.ndarray, n: int) -> np.ndarray:
        """Evaluate a cubic Bezier curve at n evenly-spaced t values."""
        t = np.linspace(0.0, 1.0, n)[:, np.newaxis]   # shape (n, 1)
        B = (
            (1 - t) ** 3 * cp[0]
            + 3 * (1 - t) ** 2 * t * cp[1]
            + 3 * (1 - t) * t ** 2 * cp[2]
            + t ** 3 * cp[3]
        )
        return B   # shape (n, 2)

    right_pts = np.vstack([bezier(cp_r1, n_pts), bezier(cp_r2, n_pts)[1:]])
    # Mirror for left side: negate x, reverse order
    left_pts  = right_pts[::-1].copy()
    left_pts[:, 0] = -left_pts[:, 0]

    # Combine: right path → left path (already ends back near start)
    all_pts = np.vstack([right_pts, left_pts])

    n_total = len(all_pts)
    codes   = [Path.MOVETO] + [Path.LINETO] * (n_total - 1) + [Path.CLOSEPOLY]
    verts   = list(map(tuple, all_pts)) + [(all_pts[0, 0], all_pts[0, 1])]

    return Path(verts, codes)


# ---------------------------------------------------------------------------
# Set up figure and axes
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(6, 9))
fig.patch.set_facecolor(COL_BG)
ax.set_facecolor(COL_BG)
ax.set_xlim(-2.6, 2.6)
ax.set_ylim(CYL_BOTTOM - 0.8, ROD_TOP + 1.2)
ax.set_aspect("equal")
ax.axis("off")

ax.set_title(
    "Rolling Diaphragm Pneumatic Chamber\n"
    "MRI-Compatible Actuator — Internal Mechanics",
    fontsize=11, fontweight="bold", color=COL_ANNOT, pad=10,
)

# ---------------------------------------------------------------------------
# Draw STATIC elements (cylinder walls, labels)
# ---------------------------------------------------------------------------

# Outer cylinder body (rectangle outline)
wall_rect = mpatches.FancyBboxPatch(
    (CYL_LEFT  - WALL_THICK, CYL_BOTTOM - 0.2),
    (CYL_RIGHT - CYL_LEFT + 2 * WALL_THICK),
    (CYL_TOP   - CYL_BOTTOM + 0.2),
    boxstyle="round,pad=0.05",
    linewidth=2, edgecolor=COL_WALL, facecolor="#C8C8C8", zorder=1,
)
ax.add_patch(wall_rect)

# Inner bore (white/bg fill to show hollow interior)
bore_rect = mpatches.Rectangle(
    (CYL_LEFT, CYL_BOTTOM - 0.1),
    CYL_RIGHT - CYL_LEFT,
    CYL_TOP - CYL_BOTTOM + 0.1,
    linewidth=0, facecolor=COL_BG, zorder=2,
)
ax.add_patch(bore_rect)

# Bottom port arrow (air inlet)
ax.annotate(
    "", xy=(0, CYL_BOTTOM - 0.1), xytext=(0, CYL_BOTTOM - 0.7),
    arrowprops=dict(arrowstyle="->", color="#444444", lw=2),
    zorder=10,
)
ax.text(0, CYL_BOTTOM - 0.9, "Air Supply\n(0 – 2 bar)", ha="center",
        fontsize=7.5, color="#444444", zorder=10)

# Wall clamp indicator (dashed line showing diaphragm attachment to wall)
ax.axhline(DIAPHRAGM_WALL_Y, xmin=0.05, xmax=0.95,
           color="#888888", lw=0.8, ls="--", zorder=3)
ax.text(CYL_RIGHT + WALL_THICK + 0.08, DIAPHRAGM_WALL_Y,
        "Wall clamp", va="center", fontsize=7, color="#666666", zorder=10)

# ---------------------------------------------------------------------------
# Draw DYNAMIC elements (created once, updated in animate())
# ---------------------------------------------------------------------------

# Air volume fill (polygon below piston head, above cylinder bottom)
air_patch = patches.PathPatch(
    Path([(CYL_LEFT, CYL_BOTTOM), (CYL_RIGHT, CYL_BOTTOM),
          (CYL_RIGHT, 0.0),       (CYL_LEFT,  0.0)],
         [Path.MOVETO, Path.LINETO, Path.LINETO, Path.CLOSEPOLY]),
    facecolor=COL_AIR_EXHAUST, edgecolor="none", alpha=0.55, zorder=3,
)
ax.add_patch(air_patch)

# Diaphragm membrane
diaphragm_patch = patches.PathPatch(
    diaphragm_path(PISTON_MID),
    facecolor=COL_DIAPHRAGM, edgecolor="#8B6914", linewidth=1.5,
    alpha=0.92, zorder=6,
)
ax.add_patch(diaphragm_patch)

# Piston head rectangle
piston_patch = mpatches.FancyBboxPatch(
    (-PISTON_W / 2, PISTON_MID - PISTON_H),
    PISTON_W, PISTON_H,
    boxstyle="round,pad=0.03",
    linewidth=1.5, edgecolor="#334455", facecolor=COL_PISTON, zorder=7,
)
ax.add_patch(piston_patch)

# Piston rod (rectangle above the piston head)
rod_patch = mpatches.Rectangle(
    (-ROD_W / 2, PISTON_MID),
    ROD_W, ROD_TOP - PISTON_MID,
    linewidth=1, edgecolor="#223344", facecolor=COL_ROD, zorder=7,
)
ax.add_patch(rod_patch)

# Horizontal centre-line on piston (decorative)
piston_line, = ax.plot(
    [-PISTON_W / 2 + 0.1, PISTON_W / 2 - 0.1],
    [PISTON_MID - PISTON_H / 2, PISTON_MID - PISTON_H / 2],
    color="#FFFFFF", lw=1.2, zorder=8,
)

# ---------------------------------------------------------------------------
# Telemetry text objects
# ---------------------------------------------------------------------------
txt_stroke = ax.text(
    -2.4, CYL_TOP + 0.3,
    "Stroke: 0.00 mm", fontsize=8.5, color=COL_ANNOT,
    fontfamily="monospace", zorder=10,
)
txt_force = ax.text(
    -2.4, CYL_TOP + 0.0,
    "Force:  52.0 N",   fontsize=8.5, color=COL_ANNOT,
    fontfamily="monospace", zorder=10,
)
txt_phase = ax.text(
    -2.4, CYL_TOP - 0.3,
    "Phase:  PRESSURISED", fontsize=8.5, color=COL_AIR_PRESS,
    fontfamily="monospace", zorder=10,
)

# Main mechanism label
ax.text(
    0, CYL_BOTTOM - 1.6,
    "Zero-Stiction Rolling Diaphragm\nfor 0.1 N fine force control",
    ha="center", fontsize=8.5, style="italic", color=COL_ANNOT,
    bbox=dict(facecolor="#FFFFFFBB", edgecolor="#AAAAAA", boxstyle="round,pad=0.4"),
    zorder=10,
)

# Diaphragm label arrow
ax.annotate(
    "Rolling\nDiaphragm",
    xy=(CYL_RIGHT - 0.05, DIAPHRAGM_WALL_Y - 0.5),
    xytext=(CYL_RIGHT + 0.55, DIAPHRAGM_WALL_Y - 1.2),
    fontsize=7.5, color="#6B4226",
    arrowprops=dict(arrowstyle="-|>", color="#6B4226", lw=1),
    zorder=10,
)


# ---------------------------------------------------------------------------
# Animation update function
# ---------------------------------------------------------------------------

def animate(frame: int):
    theta = 2 * np.pi * frame / N_FRAMES        # 0 → 2π over one cycle
    # Sinusoidal stroke: rises first half, falls second half
    raw = np.sin(theta)                          # -1 to +1
    piston_y = PISTON_MID + PISTON_AMP * raw    # piston top face y-coord

    pressurised = raw >= 0.0                     # True on upstroke

    # -- Air volume fill -----------------------------------------------
    # Fill region: from CYL_BOTTOM up to bottom of piston head
    piston_bot = piston_y - PISTON_H
    air_verts = [
        (CYL_LEFT,  CYL_BOTTOM),
        (CYL_RIGHT, CYL_BOTTOM),
        (CYL_RIGHT, piston_bot),
        (CYL_LEFT,  piston_bot),
        (CYL_LEFT,  CYL_BOTTOM),   # close
    ]
    air_codes = [Path.MOVETO, Path.LINETO, Path.LINETO, Path.LINETO, Path.CLOSEPOLY]
    air_patch.set_path(Path(air_verts, air_codes))
    air_patch.set_facecolor(COL_AIR_PRESS if pressurised else COL_AIR_EXHAUST)
    air_patch.set_alpha(0.60 if pressurised else 0.40)

    # -- Diaphragm ---------------------------------------------------------
    diaphragm_patch.set_path(diaphragm_path(piston_y))

    # -- Piston head -------------------------------------------------------
    piston_patch.set_y(piston_y - PISTON_H)
    piston_patch.set_facecolor(COL_PISTON)

    # -- Piston rod --------------------------------------------------------
    rod_patch.set_y(piston_y)
    rod_patch.set_height(ROD_TOP - piston_y)

    # -- Centre-line on piston head ----------------------------------------
    piston_line.set_ydata([piston_y - PISTON_H / 2, piston_y - PISTON_H / 2])

    # -- Telemetry text ----------------------------------------------------
    stroke_mm = raw * PISTON_AMP * 5           # scale to ±10 mm for display
    txt_stroke.set_text(f"Stroke: {stroke_mm:+.2f} mm")
    force_N   = 52.0 * max(0.0, raw)
    txt_force.set_text(f"Force:  {force_N:.1f} N")
    if pressurised:
        txt_phase.set_text("Phase:  PRESSURISED ▲")
        txt_phase.set_color(COL_AIR_PRESS)
    else:
        txt_phase.set_text("Phase:  EXHAUST     ▼")
        txt_phase.set_color("#3366AA")

    return air_patch, diaphragm_patch, piston_patch, rod_patch, piston_line, \
           txt_stroke, txt_force, txt_phase


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
