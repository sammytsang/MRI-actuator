"""
clinical_output_animation.py
=============================
2-D animation of the MRI-compatible pneumatic motor from a **Medical /
Clinical Perspective**: the full transmission chain from the rotating motor
shaft through the 2.5:1 reduction gearbox to the roller that pushes the
catheter forward inside a blood vessel.

Visual components
-----------------
  1. **Motor Shaft / Gear**  – a small gear (radius 0.30) spinning at 32 RPM
     (the estimated main-shaft speed for a 1.0 L/min supply flow).
  2. **Reduction Gear & Roller** – a larger gear (radius 0.75, 2.5× the motor
     gear) meshing externally with the motor gear and spinning at 12.8 RPM.
     A 12 mm (radius 6 mm) roller is drawn at the centre of the large gear.
  3. **Blood Vessel & Catheter** – a horizontal channel (blood vessel) with a
     thick red line (catheter) being pushed forward by the roller at ~8 mm/s.

Live telemetry overlay
----------------------
  "Motor Speed    : 32.0 RPM (1.04 N·m peak)"
  "Gearbox Ratio  : 2.5 : 1"
  "Roller Speed   : 12.8 RPM"
  "Catheter Adv.  : 8.0 mm/s  (Target: 7–10 mm/s)"

All numbers are taken from the referenced engineering report:
  * Motor speed at 1.0 L/min supply → ~32 RPM
  * 2.5:1 gearbox → 12.8 RPM output
  * Roller radius 6 mm → v = 2π × 0.006 × 12.8/60 ≈ 8.0 mm/s

Requirements
------------
  pip install numpy matplotlib

Usage
-----
  python clinical_output_animation.py

Author: Sam Tsang (MRI Actuator Project)
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.animation as animation
from matplotlib.lines import Line2D

# ---------------------------------------------------------------------------
# Drivetrain parameters (from engineering report)
# ---------------------------------------------------------------------------
MOTOR_RPM    = 32.0           # motor / main-shaft speed
GEAR_RATIO   = 2.5            # reduction ratio
ROLLER_RPM   = MOTOR_RPM / GEAR_RATIO    # = 12.8 RPM
ROLLER_RADIUS_MM = 6.0        # 12 mm diameter roller → 6 mm radius
CATHETER_SPEED_MM_S = 2.0 * np.pi * ROLLER_RADIUS_MM * ROLLER_RPM / 60.0
# ≈ 8.04 mm/s

MOTOR_OMEGA  = MOTOR_RPM  * 2.0 * np.pi / 60.0   # rad/s (motor gear)
ROLLER_OMEGA = ROLLER_RPM * 2.0 * np.pi / 60.0   # rad/s (reduction gear)

# ---------------------------------------------------------------------------
# Animation timing
# ---------------------------------------------------------------------------
CYCLE_TIME = 60.0 / ROLLER_RPM      # one full roller revolution in seconds
FPS        = 60
FRAMES     = int(FPS * CYCLE_TIME)  # frames per full roller revolution

# ---------------------------------------------------------------------------
# Layout geometry (all in normalised "display" units)
# ---------------------------------------------------------------------------
MOTOR_CENTER  = np.array([-2.10, 0.60])   # centre of the small motor gear
MOTOR_RADIUS  =  0.30                     # display radius of motor gear

# Gear ratio 2.5:1 → large gear radius = 2.5 × motor radius
LARGE_RADIUS  = MOTOR_RADIUS * GEAR_RATIO   # = 0.75
# External meshing: the two gears touch, so the large gear centre is offset
LARGE_CENTER  = MOTOR_CENTER + np.array([MOTOR_RADIUS + LARGE_RADIUS, 0.0])

# Roller (drawn at large gear centre, r = 6 mm, scaled visually)
ROLLER_VIS_RADIUS = 0.12      # visual radius of the rubber roller at large gear hub

# Vessel channel extents (horizontal)
VESSEL_Y_TOP     =  0.30
VESSEL_Y_BOTTOM  = -0.30
VESSEL_X_LEFT    = LARGE_CENTER[0] - 0.05   # starts just under the roller
VESSEL_X_RIGHT   =  3.00

# Catheter initial left edge (at roller contact point)
CATHETER_X_INITIAL = VESSEL_X_LEFT
CATHETER_Y          = 0.0               # centre of vessel
CATHETER_THICKNESS  = 6.0              # linewidth for catheter

# Number of gear teeth to draw (for visual decoration)
MOTOR_N_TEETH = 8
LARGE_N_TEETH = 20

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------
MOTOR_COLOUR   = '#1565C0'    # dark blue
LARGE_COLOUR   = '#2E7D32'    # dark green
ROLLER_COLOUR  = '#F57F17'    # amber
VESSEL_COLOUR  = '#B71C1C'    # dark red for vessel walls
CATHETER_COLOUR = '#F44336'   # bright red for catheter
BG_COLOUR      = '#1a1a2e'
PANEL_COLOUR   = '#16213e'

# ---------------------------------------------------------------------------
# Helper: draw gear teeth as a polygon
# ---------------------------------------------------------------------------

def gear_verts(cx, cy, r_inner, r_outer, n_teeth):
    """
    Return x, y arrays forming a gear outline with *n_teeth* rectangular teeth.
    *r_inner* is the pitch circle; *r_outer* is the tooth tip.
    """
    angles = []
    tooth_half = np.pi / n_teeth * 0.35   # angular half-width of each tooth

    for k in range(n_teeth):
        theta_c = 2.0 * np.pi * k / n_teeth
        # Leading flank (inner → outer)
        angles += [theta_c - tooth_half, theta_c - tooth_half,
                   theta_c + tooth_half, theta_c + tooth_half]
    angles.append(angles[0])   # close

    radii = []
    for k in range(n_teeth):
        radii += [r_inner, r_outer, r_outer, r_inner]
    radii.append(radii[0])

    x = cx + np.array(radii) * np.cos(angles)
    y = cy + np.array(radii) * np.sin(angles)
    return x, y


def rotated_gear_verts(cx, cy, r_inner, r_outer, n_teeth, rotation):
    """Same as gear_verts but every tooth angle is offset by *rotation* rad."""
    tooth_half = np.pi / n_teeth * 0.35
    angles = []
    for k in range(n_teeth):
        theta_c = rotation + 2.0 * np.pi * k / n_teeth
        angles += [theta_c - tooth_half, theta_c - tooth_half,
                   theta_c + tooth_half, theta_c + tooth_half]
    angles.append(angles[0])

    radii = []
    for k in range(n_teeth):
        radii += [r_inner, r_outer, r_outer, r_inner]
    radii.append(radii[0])

    x = cx + np.array(radii) * np.cos(angles)
    y = cy + np.array(radii) * np.sin(angles)
    return x, y

# ---------------------------------------------------------------------------
# Figure setup
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(13, 7))
fig.patch.set_facecolor(BG_COLOUR)
ax.set_facecolor(PANEL_COLOUR)
for spine in ax.spines.values():
    spine.set_edgecolor('#444')

ax.set_xlim(-3.0, 3.5)
ax.set_ylim(-1.8, 2.0)
ax.set_aspect('equal')
ax.set_axis_off()

ax.set_title(
    'Clinical Output Animation — MRI Pneumatic Motor  |  Catheter Drive System\n'
    'Motor (32 RPM)  →  2.5:1 Gearbox  →  Roller  →  Catheter (8 mm/s)',
    color='white', fontsize=12, pad=10
)

# ---------------------------------------------------------------------------
# Static decorations
# ---------------------------------------------------------------------------

# Vessel walls (two horizontal lines)
ax.fill_between(
    [VESSEL_X_LEFT, VESSEL_X_RIGHT],
    VESSEL_Y_TOP, VESSEL_Y_TOP + 0.12,
    color='#880E0E', alpha=0.7, zorder=2
)
ax.fill_between(
    [VESSEL_X_LEFT, VESSEL_X_RIGHT],
    VESSEL_Y_BOTTOM - 0.12, VESSEL_Y_BOTTOM,
    color='#880E0E', alpha=0.7, zorder=2
)
# Vessel lumen (lighter fill)
ax.fill_between(
    [VESSEL_X_LEFT, VESSEL_X_RIGHT],
    VESSEL_Y_BOTTOM, VESSEL_Y_TOP,
    color='#3E0000', alpha=0.4, zorder=1
)

# Vessel label
ax.text(VESSEL_X_RIGHT - 0.05, 0.55, 'Blood Vessel',
        color='#EF9A9A', ha='right', va='bottom', fontsize=9, style='italic')

# Motor label
ax.text(MOTOR_CENTER[0], MOTOR_CENTER[1] + MOTOR_RADIUS + 0.18,
        'Motor\n32 RPM', color='#90CAF9', ha='center', va='bottom',
        fontsize=9, fontweight='bold')

# Gearbox label
ax.text(LARGE_CENTER[0], LARGE_CENTER[1] + LARGE_RADIUS + 0.18,
        'Reduction Gear\n2.5:1  →  12.8 RPM', color='#A5D6A7',
        ha='center', va='bottom', fontsize=9, fontweight='bold')

# Roller label
ax.text(LARGE_CENTER[0], LARGE_CENTER[1] - LARGE_RADIUS - 0.25,
        'Roller  (12 mm Ø)', color='#FFE082',
        ha='center', va='top', fontsize=9, fontweight='bold')

# ---------------------------------------------------------------------------
# Animated gear objects (filled polygons)
# ---------------------------------------------------------------------------

# Motor gear body (disk)
motor_disk = plt.Circle(MOTOR_CENTER, MOTOR_RADIUS * 0.88,
                        color=MOTOR_COLOUR, zorder=4, alpha=0.9)
ax.add_patch(motor_disk)
motor_hub = plt.Circle(MOTOR_CENTER, 0.06, color='#BBDEFB', zorder=5)
ax.add_patch(motor_hub)

# Motor gear teeth outline (animated)
_mgx, _mgy = gear_verts(*MOTOR_CENTER, MOTOR_RADIUS * 0.88, MOTOR_RADIUS * 1.08,
                         MOTOR_N_TEETH)
motor_teeth_line, = ax.plot(_mgx, _mgy, color='#90CAF9', lw=1.2, zorder=5)

# Motor gear spokes (animated via a single line set)
_motor_spoke_lines = []
for k in range(4):
    sline, = ax.plot([], [], color='#90CAF9', lw=1.0, alpha=0.7, zorder=5)
    _motor_spoke_lines.append(sline)

# Large (reduction) gear body (disk)
large_disk = plt.Circle(LARGE_CENTER, LARGE_RADIUS * 0.88,
                        color=LARGE_COLOUR, zorder=4, alpha=0.9)
ax.add_patch(large_disk)
large_hub = plt.Circle(LARGE_CENTER, 0.10, color='#C8E6C9', zorder=5)
ax.add_patch(large_hub)

# Large gear teeth outline (animated)
_lgx, _lgy = gear_verts(*LARGE_CENTER, LARGE_RADIUS * 0.88, LARGE_RADIUS * 1.05,
                         LARGE_N_TEETH)
large_teeth_line, = ax.plot(_lgx, _lgy, color='#A5D6A7', lw=1.2, zorder=5)

# Large gear spokes
_large_spoke_lines = []
for k in range(5):
    sline, = ax.plot([], [], color='#A5D6A7', lw=1.0, alpha=0.7, zorder=5)
    _large_spoke_lines.append(sline)

# Roller circle at large gear hub (animated rotation indicator)
roller_patch = plt.Circle(LARGE_CENTER, ROLLER_VIS_RADIUS,
                          color=ROLLER_COLOUR, zorder=6, alpha=0.95)
ax.add_patch(roller_patch)
# Roller rotation tick (a short line that rotates with the gear)
roller_tick, = ax.plot([], [], color='white', lw=2.0, zorder=7)

# ---------------------------------------------------------------------------
# Catheter (animated translation)
# ---------------------------------------------------------------------------
catheter_line, = ax.plot([], [], color=CATHETER_COLOUR,
                          lw=CATHETER_THICKNESS, solid_capstyle='butt',
                          zorder=3)

# Catheter tip arrow patch (updated each frame)
catheter_tip_text = ax.text(
    0.0, CATHETER_Y + 0.50, '►',
    color=CATHETER_COLOUR, ha='left', va='center', fontsize=14, zorder=8
)

# Catheter label
catheter_label = ax.text(
    VESSEL_X_LEFT + 0.5, CATHETER_Y - 0.48,
    'Catheter', color='#EF9A9A', ha='center', va='top', fontsize=9,
    style='italic'
)

# ---------------------------------------------------------------------------
# Live telemetry text box
# ---------------------------------------------------------------------------
telemetry_text = ax.text(
    -2.90, -0.90,
    '',
    color='white', ha='left', va='top', fontsize=9.5,
    fontfamily='monospace',
    bbox=dict(boxstyle='round,pad=0.5', facecolor='#0d0d1a', alpha=0.85,
              edgecolor='#336688', linewidth=1.5),
    zorder=10
)

# ---------------------------------------------------------------------------
# Arrow indicating transmission direction
# ---------------------------------------------------------------------------
ax.annotate(
    '', xy=(LARGE_CENTER[0] - LARGE_RADIUS - 0.05, LARGE_CENTER[1]),
    xytext=(MOTOR_CENTER[0] + MOTOR_RADIUS + 0.05, MOTOR_CENTER[1]),
    arrowprops=dict(arrowstyle='->', color='#FFD54F', lw=1.5)
)

# ---------------------------------------------------------------------------
# Animation update
# ---------------------------------------------------------------------------
# Catheter advance per frame (in display units, scaled from mm/s)
# The vessel display width is (VESSEL_X_RIGHT - VESSEL_X_LEFT) ≈ 2.9 units
# We map the catheter to wrap around every vessel-length worth of travel.
VESSEL_WIDTH   = VESSEL_X_RIGHT - VESSEL_X_LEFT
MM_PER_S       = CATHETER_SPEED_MM_S
DISPLAY_SCALE  = VESSEL_WIDTH / 100.0   # 100 mm ≈ full vessel width

# Fixed catheter length (display units) — represents the physical catheter body
CATHETER_DISP_LENGTH = VESSEL_WIDTH * 0.55


def update(frame):
    t = frame / FPS

    # ── Gear rotations ─────────────────────────────────────────────────────
    motor_angle  = MOTOR_OMEGA  * t          # motor rotates CCW
    roller_angle = -ROLLER_OMEGA * t         # reduction gear rotates CW (meshing)

    # Motor gear teeth
    _mgx, _mgy = rotated_gear_verts(
        *MOTOR_CENTER, MOTOR_RADIUS * 0.88, MOTOR_RADIUS * 1.08,
        MOTOR_N_TEETH, motor_angle
    )
    motor_teeth_line.set_data(_mgx, _mgy)

    # Motor spoke lines (4 spokes, 45° apart)
    for k, sline in enumerate(_motor_spoke_lines):
        ang = motor_angle + k * np.pi / 2
        x0, y0 = MOTOR_CENTER
        sline.set_data(
            [x0 + 0.06 * np.cos(ang), x0 + MOTOR_RADIUS * 0.82 * np.cos(ang)],
            [y0 + 0.06 * np.sin(ang), y0 + MOTOR_RADIUS * 0.82 * np.sin(ang)]
        )

    # Large gear teeth
    _lgx, _lgy = rotated_gear_verts(
        *LARGE_CENTER, LARGE_RADIUS * 0.88, LARGE_RADIUS * 1.05,
        LARGE_N_TEETH, roller_angle
    )
    large_teeth_line.set_data(_lgx, _lgy)

    # Large gear spoke lines (5 spokes, 72° apart)
    for k, sline in enumerate(_large_spoke_lines):
        ang = roller_angle + k * 2 * np.pi / 5
        x0, y0 = LARGE_CENTER
        sline.set_data(
            [x0 + 0.10 * np.cos(ang), x0 + LARGE_RADIUS * 0.82 * np.cos(ang)],
            [y0 + 0.10 * np.sin(ang), y0 + LARGE_RADIUS * 0.82 * np.sin(ang)]
        )

    # Roller tick (indicates roller rotation)
    rx, ry = LARGE_CENTER
    roller_tick.set_data(
        [rx, rx + ROLLER_VIS_RADIUS * 0.9 * np.cos(roller_angle * 2.5)],
        [ry, ry + ROLLER_VIS_RADIUS * 0.9 * np.sin(roller_angle * 2.5)]
    )

    # ── Catheter advancement ───────────────────────────────────────────────
    # Total distance advanced (mm), wraps around the vessel length (100 mm)
    advance_mm     = (MM_PER_S * t) % (100.0)
    catheter_x_tip = VESSEL_X_LEFT + advance_mm * DISPLAY_SCALE
    catheter_x_tail = catheter_x_tip - CATHETER_DISP_LENGTH

    # Clamp tail to vessel left edge (catheter enters from left)
    catheter_x_tail = max(catheter_x_tail, VESSEL_X_LEFT)

    # Clamp tip to vessel right edge (wrap is handled by modulo above)
    catheter_x_tip_clamped = min(catheter_x_tip, VESSEL_X_RIGHT - 0.05)

    catheter_line.set_data(
        [catheter_x_tail, catheter_x_tip_clamped],
        [CATHETER_Y, CATHETER_Y]
    )

    # Move tip arrow
    catheter_tip_text.set_x(catheter_x_tip_clamped + 0.02)

    # ── Telemetry overlay ─────────────────────────────────────────────────
    telemetry_text.set_text(
        f'Motor Speed        : {MOTOR_RPM:.1f} RPM  (1.04 N·m peak)\n'
        f'Gearbox Ratio      : {GEAR_RATIO:.1f} : 1\n'
        f'Roller Speed       : {ROLLER_RPM:.1f} RPM\n'
        f'Catheter Advance   : {MM_PER_S:.1f} mm/s  (Target: 7–10 mm/s)\n'
        f'Elapsed            : {t:5.1f} s   |   Advanced: {advance_mm:5.1f} mm'
    )

    return ([motor_teeth_line, large_teeth_line, roller_tick,
             catheter_line, catheter_tip_text, telemetry_text]
            + _motor_spoke_lines + _large_spoke_lines)


# ---------------------------------------------------------------------------
# Legend
# ---------------------------------------------------------------------------
legend_handles = [
    mpatches.Patch(color=MOTOR_COLOUR,    label=f'Motor gear  ({MOTOR_RPM:.0f} RPM)'),
    mpatches.Patch(color=LARGE_COLOUR,    label=f'Reduction gear  ({ROLLER_RPM:.1f} RPM)'),
    mpatches.Patch(color=ROLLER_COLOUR,   label='Roller  (12 mm Ø)'),
    mpatches.Patch(color=CATHETER_COLOUR, label=f'Catheter  ({MM_PER_S:.1f} mm/s)'),
]
ax.legend(handles=legend_handles, loc='lower right',
          facecolor='#16213e', edgecolor='#555', labelcolor='white',
          fontsize=8.5, framealpha=0.85)

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
ani = animation.FuncAnimation(
    fig, update,
    frames=FRAMES,
    interval=1000.0 / FPS,
    blit=False
)

plt.tight_layout()
plt.show()
