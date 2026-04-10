"""
unwrapped_cam_animation.py
==========================
2-D animation of the MRI-compatible pneumatic motor from an **Engineering
Perspective**: the two-period wavy cam track is "unrolled" into a continuous
scrolling sine wave so that the three pistons can be observed tracking the
wave surface in real time.

Layout
------
A single panel shows:
  * The unwrapped (linear) wavy cam track as a shaded region that scrolls
    horizontally to simulate cam rotation.
  * Three vertical pistons fixed at angular positions 0°, 120° and 240° whose
    Y-positions follow the cam surface beneath them.
  * Dynamic colouring:
      Red  – piston is on the *upward* slope (cam pushing piston up → active,
             52 N pneumatic force applied).
      Gray – piston is on the *downward* slope (exhaust / return phase).
  * A live cam-angle readout and a descriptive legend.

Physics reference (from the engineering report)
------------------------------------------------
  Cam track : h(θ) = A · sin(2θ)       with A = 10 mm (amplitude)
  Two periods per revolution (2 × 2π in one shaft turn)
  Piston phase offsets: φ₁ = 0°, φ₂ = 120°, φ₃ = 240°

  Active phase detection:
    dh/dθ = 2A · cos(2(θ – φᵢ))
    If dh/dθ > 0 the cam surface is rising under the piston → piston is
    being pushed upward → it is in its active / force-generating phase.

Requirements
------------
  pip install numpy matplotlib

Usage
-----
  python unwrapped_cam_animation.py

Author: Sam Tsang (MRI Actuator Project)
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.animation as animation

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
CYCLE_TIME   = 4.5          # seconds per full revolution (slowed for clarity)
FPS          = 60
FRAMES       = int(FPS * CYCLE_TIME)   # frames for one full revolution

OMEGA        = 2.0 * np.pi / CYCLE_TIME   # shaft angular velocity (rad/s)

# Cam geometry
AMPLITUDE    = 1.0           # normalised amplitude (visual units)
PHYSICAL_AMPLITUDE_MM = 10.0 # physical cam amplitude in millimetres (from engineering report)
N_PERIODS    = 2             # number of sine-wave periods per revolution

# Piston angular positions (degrees → used for display and colour logic)
PISTON_ANGLES_DEG  = [0.0, 120.0, 240.0]
PISTON_LABELS      = ['A  (0°)', 'B  (120°)', 'C  (240°)']
PISTON_WIDTH       = 0.08    # half-width of each piston rectangle (in x-units)
PISTON_HEIGHT      = 0.50    # height of each piston rectangle (in y-units)

# Colours
COLOUR_ACTIVE  = '#E53935'   # red  – upward slope / power stroke
COLOUR_EXHAUST = '#78909C'   # steel-blue-gray – downward slope / exhaust
COLOUR_TRACK   = '#00BCD4'   # cyan for the cam track line/fill
TRACK_FILL     = '#00BCD4'
TRACK_ALPHA    = 0.20

# X-axis: 0 to 2π (one full circumference in angle units)
X_MIN = 0.0
X_MAX = 2.0 * np.pi           # full 360° unrolled

# Fine x-grid for drawing the sine wave (extra period on each side for seamless scrolling)
_N_WAVE = 600
_X_WAVE = np.linspace(-X_MAX, 2.0 * X_MAX, _N_WAVE * 3)   # 3× domain for scroll buffer

# ---------------------------------------------------------------------------
# Helper: cam surface height at angle θ for a given cam rotation φ
# ---------------------------------------------------------------------------

def cam_height(theta, cam_angle):
    """
    Return the normalised height of the unrolled cam track at angular position
    *theta* when the cam has rotated by *cam_angle* (both in radians).

    h(θ, φ) = A · sin(N · (θ − φ))

    where N = number of periods per revolution (2 for this motor).
    """
    return AMPLITUDE * np.sin(N_PERIODS * (theta - cam_angle))


def dh_dtheta(theta, cam_angle):
    """
    Derivative of cam height with respect to θ.
    dh/dθ = A · N · cos(N · (θ − φ))

    Positive → cam surface rising under the piston → active / power stroke.
    """
    return AMPLITUDE * N_PERIODS * np.cos(N_PERIODS * (theta - cam_angle))

# ---------------------------------------------------------------------------
# Figure setup
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor('#1a1a2e')
ax.set_facecolor('#16213e')
for spine in ax.spines.values():
    spine.set_edgecolor('#444')

ax.set_xlim(X_MIN, X_MAX)
ax.set_ylim(-AMPLITUDE * 2.5, AMPLITUDE * 3.2)
ax.set_aspect('auto')

ax.set_title(
    'Unwrapped Cam Track — Engineering View  |  MRI Pneumatic Motor\n'
    'Red = Active / Power Stroke (52 N)   ·   Gray = Exhaust / Return',
    color='white', fontsize=15, pad=10
)
ax.set_xlabel('Cam circumference (rad)', color='#ccc', fontsize=13)
ax.set_ylabel('Cam surface height (normalised)', color='#ccc', fontsize=13)
ax.tick_params(colors='#aaa', labelsize=12)
ax.grid(color='#333', linestyle='--', linewidth=0.5, alpha=0.7)

# Custom x-tick labels in degrees
_xticks = [0, np.pi/2, np.pi, 3*np.pi/2, 2*np.pi]
_xlabels = ['0°', '90°', '180°', '270°', '360°']
ax.set_xticks(_xticks)
ax.set_xticklabels(_xlabels, color='#aaa', fontsize=12)

# ---------------------------------------------------------------------------
# Static legend
# ---------------------------------------------------------------------------
legend_handles = [
    mpatches.Patch(color=COLOUR_TRACK,  alpha=0.6,  label='Wavy cam track'),
    mpatches.Patch(color=COLOUR_ACTIVE,             label='Piston — Active / Power (dh/dθ > 0)'),
    mpatches.Patch(color=COLOUR_EXHAUST,            label='Piston — Exhaust / Return (dh/dθ ≤ 0)'),
]
ax.legend(handles=legend_handles, loc='upper right',
          facecolor='#16213e', edgecolor='#555', labelcolor='white', fontsize=12)

# ---------------------------------------------------------------------------
# Animated artists
# ---------------------------------------------------------------------------

# ── Cam track: thick line ──────────────────────────────────────────────────
track_line, = ax.plot([], [], color=COLOUR_TRACK, lw=2.5, zorder=3)

# ── Cam track: shaded fill between ±amplitude ─────────────────────────────
_fill_poly = ax.fill_between([], [], [], color=TRACK_FILL, alpha=TRACK_ALPHA, zorder=2)

# ── Piston rectangles ─────────────────────────────────────────────────────
piston_angles_rad = [np.deg2rad(a) for a in PISTON_ANGLES_DEG]
piston_rects = []
piston_rods  = []    # vertical rod lines

for i, (phi_rad, label) in enumerate(zip(piston_angles_rad, PISTON_LABELS)):
    rect = mpatches.FancyBboxPatch(
        (phi_rad - PISTON_WIDTH, 0.0),   # bottom-left; y updated each frame
        2 * PISTON_WIDTH, PISTON_HEIGHT,
        boxstyle='round,pad=0.01',
        linewidth=1.5, edgecolor='white',
        facecolor=COLOUR_EXHAUST,
        zorder=6
    )
    ax.add_patch(rect)
    piston_rects.append(rect)

    # Thin vertical rod connecting piston bottom to Y = -2 (fixed support)
    rod, = ax.plot(
        [phi_rad, phi_rad],
        [-AMPLITUDE * 2.4, 0.0],
        color='#aaaaaa', lw=1.5, linestyle='--', zorder=4, alpha=0.6
    )
    piston_rods.append(rod)

# ── Piston labels ──────────────────────────────────────────────────────────
piston_label_texts = []
for i, (phi_rad, label) in enumerate(zip(piston_angles_rad, PISTON_LABELS)):
    txt = ax.text(phi_rad, -AMPLITUDE * 2.2, label,
                  color='#cccccc', ha='center', va='top', fontsize=11, zorder=7)
    piston_label_texts.append(txt)

# ── Live cam-angle readout ─────────────────────────────────────────────────
angle_text = ax.text(
    0.02, 0.97, '',
    transform=ax.transAxes,
    color='white', fontsize=14, ha='left', va='top',
    fontfamily='monospace',
    bbox=dict(boxstyle='round,pad=0.4', facecolor='#0d0d1a', alpha=0.80,
              edgecolor='#336688', linewidth=1.2),
    zorder=10
)


# ---------------------------------------------------------------------------
# Animation update
# ---------------------------------------------------------------------------
_x_plot = np.linspace(X_MIN, X_MAX, 400)   # x-grid for the visible window

def update(frame):
    t         = frame / FPS
    cam_angle = OMEGA * t                       # current cam rotation (rad)
    cam_deg   = np.degrees(cam_angle) % 360.0

    # ── Update cam track (scrolling sine wave) ────────────────────────────
    y_wave = cam_height(_x_plot, cam_angle)
    track_line.set_data(_x_plot, y_wave)

    # Replace fill polygon (fill_between returns a PolyCollection)
    global _fill_poly
    _fill_poly.remove()
    _fill_poly = ax.fill_between(
        _x_plot, -AMPLITUDE * 0.15, y_wave,
        color=TRACK_FILL, alpha=TRACK_ALPHA, zorder=2
    )

    # ── Update pistons ────────────────────────────────────────────────────
    for i, phi_rad in enumerate(piston_angles_rad):
        h  = cam_height(phi_rad, cam_angle)       # cam height under this piston
        dh = dh_dtheta(phi_rad, cam_angle)        # slope at this piston position

        # Piston rectangle sits ON TOP of the cam surface
        rect_y_bottom = h                         # bottom of piston block = cam surface
        piston_rects[i].set_y(rect_y_bottom)

        # Colour based on slope sign
        if dh > 0:
            piston_rects[i].set_facecolor(COLOUR_ACTIVE)
        else:
            piston_rects[i].set_facecolor(COLOUR_EXHAUST)

        # Update vertical rod
        piston_rods[i].set_ydata([-AMPLITUDE * 2.4, rect_y_bottom])

    # ── Cam angle readout ─────────────────────────────────────────────────
    angle_text.set_text(
        f'Cam angle : {cam_deg:6.1f}°\n'
        f'Amplitude : {PHYSICAL_AMPLITUDE_MM:.0f} mm  (A)\n'
        f'dh/dθ_max : {AMPLITUDE*N_PERIODS:.3f} m/rad'
    )

    return [track_line, _fill_poly, angle_text] + piston_rects + piston_rods


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
ani = animation.FuncAnimation(
    fig, update,
    frames=FRAMES,
    interval=1000.0 / FPS,
    blit=False    # blit=False allows fill_between to refresh cleanly
)

plt.tight_layout()
plt.show()
