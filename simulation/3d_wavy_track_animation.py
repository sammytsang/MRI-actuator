"""
3d_wavy_track_animation.py
==========================
Standalone 3-D animation of an MRI-compatible pneumatic axial-piston motor
with a **three-lobed / two-period wavy track** (barrel cam) instead of the
flat tilted swashplate used in ``3d_axial_animation.py``.

Mechanism
---------
Three pistons are arranged in a circle at 0°, 120° and 240° around a central
shaft, with their axes *parallel* to the shaft (axial arrangement).  A wavy
cam (two full sine-wave periods per revolution) is fixed to the shaft and
spins with it.  As the cam rotates the pistons are pushed up and down,
converting pneumatic pressure into torque via virtual work:

    T = F × dh/dθ

where h(θ) = A·sin(2(ψ − θ)) and A = 10 mm (physical amplitude).

Visual elements
---------------
* Central shaft       – black cylinder along the Z-axis
* Wavy cam surface    – translucent cyan 2-period sinusoidal disk that rotates
* Piston Head         – thick short block at the top of each piston assembly:
    Blue  (cylinder A, 0°)
    Green (cylinder B, 120°)
    Red   (cylinder C, 240°)
  Lights up in the cylinder colour when pressurised; turns gray on exhaust.
* Push-Arm (Rod)      – thin, rigid gray arm connecting the piston head down
  to the spinning cam shoe.
* Housing outline     – faint circle showing the bore positions
* Physics overlay     – live text box (top-left corner) showing cam angle,
  active chamber, theoretical thrust, and instantaneous torque.

Animation timing
----------------
  CYCLE_TIME = 4.5 s per full revolution  (slowed down for presentation clarity)
  FPS        = 60
  The animation loops continuously.

Interactivity
-------------
Click and drag the matplotlib window to rotate the 3-D view while the
animation plays (standard mpl_toolkits.mplot3d mouse interaction).

Requirements
------------
  pip install numpy matplotlib

Usage
-----
  python 3d_wavy_track_animation.py

Author: Sam Tsang (MRI Actuator Project)
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.mplot3d import Axes3D          # noqa: F401 – registers projection

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
CYCLE_TIME  = 4.5          # seconds per full revolution (slowed for presentation)
FPS         = 60           # frames per second
FRAMES      = int(FPS * CYCLE_TIME)   # frames for one full revolution (loop)

OMEGA = 2.0 * np.pi / CYCLE_TIME      # angular velocity (rad / s)

# Piston circle: pistons sit on a ring of this radius around the shaft
PISTON_RADIUS = 0.55

# Wavy-cam amplitude (visual / normalised units).
# The physical amplitude is 10 mm; here we scale it to the normalised geometry.
AMPLITUDE = 0.30 * PISTON_RADIUS   # ≈ 0.165 normalised units

# Physical amplitude used ONLY for torque calculation (metres)
PHYSICAL_AMPLITUDE = 0.010          # 10 mm → max torque = 52 N × 2 × 0.010 = 1.04 N·m
THRUST_FORCE       = 52.0           # Newtons (pneumatic force per chamber at 2 bar)

# Piston travel limits (Z-axis)
# Cam (wavy track) is at the TOP centered around CAM_CENTER_Z.
# Piston rod bases are fixed at Z = 0.0; heads follow the cam surface from below.
CAM_CENTER_Z  = 1.0    # neutral Z of the wavy cam surface (top of assembly)
PISTON_TOP    =  1.0   # alias kept for housing-outline and shaft reference
PISTON_BOTTOM =  0.0   # fixed Z of piston rod bases (bottom of assembly)

# Cylinder angles around the shaft
CYLINDER_ANGLES_DEG = [0, 120, 240]
CYLINDER_LABELS     = ['A', 'B', 'C']

COLOUR_MAP   = {'A': '#2196F3', 'B': '#4CAF50', 'C': '#F44336'}   # blue / green / red
COLOUR_GRAY  = '#aaaaaa'    # exhaust / return phase colour

# Phase window per cylinder: each cylinder is "active" for 120° of shaft rotation
PHASE_WINDOW = 2.0 * np.pi / 3.0   # 120° in radians

# ---------------------------------------------------------------------------
# Derived geometry
# ---------------------------------------------------------------------------
angles_rad = np.deg2rad(CYLINDER_ANGLES_DEG)
px = PISTON_RADIUS * np.cos(angles_rad)   # fixed X positions of piston rods
py = PISTON_RADIUS * np.sin(angles_rad)   # fixed Y positions of piston rods


def cam_z(piston_angle_rad, cam_angle_rad):
    """Return the Z height of the wavy cam surface directly under a piston
    whose angular position around the shaft is *piston_angle_rad*, when the
    cam has rotated by *cam_angle_rad*.

    The cam is centred at CAM_CENTER_Z (top of the assembly) and uses a
    2-period sine wave:
        h = CAM_CENTER_Z + A · sin(2·(ψ − θ))
    Pistons push upward from below and their heads track this surface.
    """
    return CAM_CENTER_Z + AMPLITUDE * np.sin(2.0 * (piston_angle_rad - cam_angle_rad))


def instantaneous_torque(cam_angle_rad):
    """Return the net instantaneous output torque (N·m) from all active pistons.

    Virtual-work principle:  T = F · |dh/dθ|  per active piston.
    dh/dθ = −2·A_phys · cos(2·(ψ − θ))   (derivative w.r.t. cam angle)
    We use absolute value because the cam reaction always opposes the push.
    """
    total_torque = 0.0
    for i in range(3):
        if is_active(i, cam_angle_rad):
            slope = 2.0 * PHYSICAL_AMPLITUDE * abs(
                np.cos(2.0 * (angles_rad[i] - cam_angle_rad))
            )
            total_torque += THRUST_FORCE * slope
    return total_torque


def is_active(piston_index, cam_angle_rad):
    """Return True when piston *piston_index* is in its 120° push phase."""
    phase = (cam_angle_rad - angles_rad[piston_index]) % (2.0 * np.pi)
    return phase < PHASE_WINDOW


# Swashplate mesh resolution and decoration offsets
CAM_MESH_ANGULAR_RES   = 40    # angular segments around the cam disk
CAM_MESH_RADIAL_RES    = 8     # radial rings on the cam disk
HOUSING_OUTLINE_OFFSET = 0.10  # radial gap between piston circle and housing ring
LABEL_OFFSET           = 0.20  # radial gap between piston circle and cylinder labels

# ---------------------------------------------------------------------------
# Wavy cam mesh (X/Y base computed once; Z updated each frame)
# ---------------------------------------------------------------------------
_theta = np.linspace(0, 2.0 * np.pi, CAM_MESH_ANGULAR_RES)
_r     = np.linspace(0, 0.75, CAM_MESH_RADIAL_RES)
_T, _R = np.meshgrid(_theta, _r)
_X_base = _R * np.cos(_T)
_Y_base = _R * np.sin(_T)


def swashplate_mesh(cam_angle):
    """Return (X, Y, Z) arrays for the 2-period wavy cam at *cam_angle*.

    The cam sits at the top of the assembly (CAM_CENTER_Z).  Z scales with
    radius so the centre is flat and the wave amplitude grows toward the outer
    edge (matching the physical barrel-cam geometry):
        Z = CAM_CENTER_Z + A · (r / r_max) · sin(2·(T − cam_angle))
    """
    X = _X_base
    Y = _Y_base
    Z = CAM_CENTER_Z + AMPLITUDE * (_R / 0.75) * np.sin(2.0 * (_T - cam_angle))
    return X, Y, Z


# ---------------------------------------------------------------------------
# Figure setup
# ---------------------------------------------------------------------------
fig = plt.figure(figsize=(9, 9))
fig.patch.set_facecolor('#1a1a2e')
fig.canvas.manager.set_window_title('3D Axial Piston Motor — Wavy Track | MRI Actuator')

ax = fig.add_subplot(111, projection='3d')
ax.set_facecolor('#16213e')

ax.set_xlim([-1.0, 1.0])
ax.set_ylim([-1.0, 1.0])
ax.set_zlim([-0.3, 1.4])
ax.set_axis_off()
ax.set_title(
    '3-D Axial Piston Motor — Wavy Track (2 Periods)  |  MRI Actuator\n'
    'Blue / Green / Red = pressurised (52 N)   |   Gray = exhaust',
    color='white', fontsize=11, pad=12
)

# Nice default viewing angle (isometric-ish)
ax.view_init(elev=22, azim=45)

# ---------------------------------------------------------------------------
# Static decorations
# ---------------------------------------------------------------------------

# Housing / bore outline: a faint dashed circle at Z = PISTON_BOTTOM (base of pistons)
_hx = np.cos(_theta) * (PISTON_RADIUS + HOUSING_OUTLINE_OFFSET)
_hy = np.sin(_theta) * (PISTON_RADIUS + HOUSING_OUTLINE_OFFSET)
_hz = np.full_like(_theta, PISTON_BOTTOM)
ax.plot(_hx, _hy, _hz, color='#444444', lw=1.0, linestyle='--', zorder=1)

# Labels for each cylinder at the bottom (static)
for i, label in enumerate(CYLINDER_LABELS):
    colour = COLOUR_MAP[label]
    lx = (PISTON_RADIUS + LABEL_OFFSET) * np.cos(angles_rad[i])
    ly = (PISTON_RADIUS + LABEL_OFFSET) * np.sin(angles_rad[i])
    ax.text(lx, ly, PISTON_BOTTOM - 0.15, label,
            color=colour, fontsize=13, fontweight='bold',
            ha='center', va='center', zorder=10)

# Phase / valve indicator text (bottom of the figure)
_phase_text = ax.text2D(
    0.5, 0.02, '',
    transform=ax.transAxes,
    color='white', fontsize=11, ha='center', va='bottom',
    fontweight='bold'
)

# ---------------------------------------------------------------------------
# Live physics overlay (top-left corner)
# ---------------------------------------------------------------------------
_CHAMBER_NAMES = {'A': 'A (Blue)', 'B': 'B (Green)', 'C': 'C (Red)'}

_physics_text = ax.text2D(
    0.02, 0.97, '',
    transform=ax.transAxes,
    color='white', fontsize=10, ha='left', va='top',
    fontfamily='monospace',
    bbox=dict(boxstyle='round,pad=0.4', facecolor='#0d0d1a', alpha=0.75,
              edgecolor='#336688', linewidth=1.2)
)

# ---------------------------------------------------------------------------
# Animated objects
# ---------------------------------------------------------------------------

# Central shaft: static line from piston base up through the cam
ax.plot([0, 0], [0, 0], [PISTON_BOTTOM - 0.05, CAM_CENTER_Z + AMPLITUDE + 0.05],
        color='#cccccc', lw=5, zorder=5, solid_capstyle='round')

# Wavy cam surface (re-drawn each frame via plot_surface)
swash_surf = [None]   # mutable container so the callback can replace it

# Piston assembly geometry
HEAD_HEIGHT = 0.18   # Z-height of the thick piston head block
ROD_LENGTH  = 0.60   # length of the thin push-arm rod

# Piston Heads (thick, color-coded block — lights up when pressurised)
# Initialised touching the cam from below; updated every frame.
head_lines = []
for i in range(3):
    line, = ax.plot(
        [px[i], px[i]],
        [py[i], py[i]],
        [CAM_CENTER_Z - HEAD_HEIGHT, CAM_CENTER_Z],
        lw=14,
        color=COLOUR_MAP[CYLINDER_LABELS[i]],
        solid_capstyle='round',
        zorder=6
    )
    head_lines.append(line)

# Push-Arm Rods: thin gray arm from piston base (Z = 0) up to piston head bottom
rod_lines = []
for i in range(3):
    line, = ax.plot(
        [px[i], px[i]],
        [py[i], py[i]],
        [PISTON_BOTTOM, CAM_CENTER_Z - HEAD_HEIGHT],
        lw=4,
        color='#888888',
        solid_capstyle='butt',
        zorder=6
    )
    rod_lines.append(line)


# ---------------------------------------------------------------------------
# Animation update function
# ---------------------------------------------------------------------------
def update(frame):
    t = frame / FPS                          # current time in seconds
    cam_angle = OMEGA * t                    # current cam rotation angle (rad)
    cam_deg   = np.degrees(cam_angle) % 360.0

    # ── Wavy cam surface ─────────────────────────────────────────────────
    if swash_surf[0] is not None:
        swash_surf[0].remove()
    X, Y, Z = swashplate_mesh(cam_angle)
    swash_surf[0] = ax.plot_surface(
        X, Y, Z,
        color='cyan', alpha=0.30,
        edgecolor='#336666', linewidth=0.3,
        zorder=2
    )

    # ── Pistons ───────────────────────────────────────────────────────────
    active_labels = []
    for i, label in enumerate(CYLINDER_LABELS):
        # Z of the cam surface under this piston (head top tracks cam from below)
        pz_head_top    = cam_z(angles_rad[i], cam_angle)
        pz_head_bottom = pz_head_top - HEAD_HEIGHT   # head bottom = rod top
        pz_rod_bottom  = PISTON_BOTTOM               # rod base fixed at Z = 0

        # Update push-arm rod (from fixed base up to piston head bottom)
        rod_lines[i].set_data([px[i], px[i]], [py[i], py[i]])
        rod_lines[i].set_3d_properties([pz_rod_bottom, pz_head_bottom])

        # Update piston head (thick block touching cam from below)
        head_lines[i].set_data([px[i], px[i]], [py[i], py[i]])
        head_lines[i].set_3d_properties([pz_head_bottom, pz_head_top])

        # Colouring: bright cylinder colour when active, gray on exhaust
        if is_active(i, cam_angle):
            head_colour = COLOUR_MAP[label]
            active_labels.append(label)
        else:
            head_colour = COLOUR_GRAY

        head_lines[i].set_color(head_colour)

    # ── Phase text (bottom centre) ────────────────────────────────────────
    if active_labels:
        lbl = active_labels[0]
        others = [l for l in CYLINDER_LABELS if l != lbl]
        _phase_text.set_text(
            f'Valve {lbl} ON  (pressurised)   |   '
            f'Valves {others[0]}, {others[1]} OFF  (exhaust)'
        )
        _phase_text.set_color(COLOUR_MAP[lbl])
    else:
        _phase_text.set_text('')

    # ── Live physics overlay (top-left) ───────────────────────────────────
    torque = instantaneous_torque(cam_angle)
    if active_labels:
        active_lbl = active_labels[0]
        chamber_str  = _CHAMBER_NAMES[active_lbl]
        thrust_str   = f'{THRUST_FORCE:.1f} N'
        torque_str   = f'{torque:.3f} N·m'
        overlay_colour = COLOUR_MAP[active_lbl]
    else:
        chamber_str  = '—'
        thrust_str   = '—'
        torque_str   = f'{torque:.3f} N·m'
        overlay_colour = 'white'

    _physics_text.set_text(
        f'Cam Angle         : {cam_deg:6.1f}°\n'
        f'Active Chamber    : {chamber_str}\n'
        f'Theoretical Thrust: {thrust_str}\n'
        f'Theoretical Torque: {torque_str}'
    )
    _physics_text.set_color(overlay_colour)

    return head_lines + rod_lines + [_phase_text, _physics_text]


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
ani = animation.FuncAnimation(
    fig,
    update,
    frames=FRAMES,
    interval=1000.0 / FPS,   # ms per frame
    blit=False               # blit=False keeps 3-D mouse rotation working
)

plt.tight_layout()
plt.show()
