"""
3d_axial_animation.py
=====================
Standalone 3-D animation of an MRI-compatible pneumatic axial-piston motor
(swashplate / barrel-cam design).

Mechanism
---------
Three pistons are arranged in a circle at 0°, 120° and 240° around a central
shaft, with their axes *parallel* to the shaft (axial arrangement).  A slanted
cam (swashplate) is fixed to the shaft and spins with it.  As the cam rotates
the pistons are pushed up and down, converting pneumatic pressure into torque.

Visual elements
---------------
* Central shaft     – black cylinder along the Z-axis
* Swashplate / cam  – translucent cyan tilted disk that rotates
* Piston rods       – thick lines, one per cylinder:
    Blue  (cylinder A, 0°)
    Green (cylinder B, 120°)
    Red   (cylinder C, 240°)
  When a piston is in its 120° "pushing" (pressurised) phase the line uses
  the cylinder colour.  During the exhaust / return stroke it turns gray.
* Piston caps       – small sphere at the bottom of each rod (cam-follower)
* Housing outline   – faint circle showing the bore positions

Animation timing
----------------
  CYCLE_TIME = 1.5 s per full revolution  (matches the notebook / Arduino code)
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
  python 3d_axial_animation.py

Author: Sam Tsang (MRI Actuator Project)
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.mplot3d import Axes3D          # noqa: F401 – registers projection
from mpl_toolkits.mplot3d.art3d import Line3D

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
CYCLE_TIME  = 1.5          # seconds per full revolution
FPS         = 60           # frames per second
FRAMES      = int(FPS * CYCLE_TIME)   # frames for one full revolution (loop)

OMEGA = 2.0 * np.pi / CYCLE_TIME      # angular velocity (rad / s)

# Swashplate tilt severity (fraction of piston-circle radius)
CAM_TILT = 0.30

# Piston circle: pistons sit on a ring of this radius around the shaft
PISTON_RADIUS = 0.55

# Piston travel limits (Z-axis, relative to cam neutral plane at Z = 0.5)
PISTON_TOP    =  1.0   # top of the stroke / top of housing bore
PISTON_BOTTOM = -0.05  # lowest position (at cam crest)

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
    """Return the Z height of the swashplate surface directly under a piston
    whose angular position around the shaft is *piston_angle_rad*, when the
    cam has rotated by *cam_angle_rad*."""
    return CAM_TILT * PISTON_RADIUS * np.cos(piston_angle_rad - cam_angle_rad)


def is_active(piston_index, cam_angle_rad):
    """Return True when piston *piston_index* is in its 120° push phase."""
    phase = (cam_angle_rad - angles_rad[piston_index]) % (2.0 * np.pi)
    return phase < PHASE_WINDOW


# Swashplate mesh resolution and decoration offsets
CAM_MESH_ANGULAR_RES   = 40    # angular segments around the swashplate disk
CAM_MESH_RADIAL_RES    = 8     # radial rings on the swashplate disk
HOUSING_OUTLINE_OFFSET = 0.10  # radial gap between piston circle and housing ring
LABEL_OFFSET           = 0.20  # radial gap between piston circle and cylinder labels

# ---------------------------------------------------------------------------
# Swashplate mesh (computed once at cam_angle=0; Z updated each frame)
# ---------------------------------------------------------------------------
_theta = np.linspace(0, 2.0 * np.pi, CAM_MESH_ANGULAR_RES)
_r     = np.linspace(0, 0.75, CAM_MESH_RADIAL_RES)
_T, _R = np.meshgrid(_theta, _r)
_X_base = _R * np.cos(_T)
_Y_base = _R * np.sin(_T)


def swashplate_mesh(cam_angle):
    """Return (X, Y, Z) arrays for the tilted swashplate at *cam_angle*."""
    X = _X_base
    Y = _Y_base
    Z = CAM_TILT * _R * np.cos(_T - cam_angle)
    return X, Y, Z


# ---------------------------------------------------------------------------
# Figure setup
# ---------------------------------------------------------------------------
fig = plt.figure(figsize=(9, 9))
fig.patch.set_facecolor('#1a1a2e')
fig.canvas.manager.set_window_title('3D Axial Piston Motor — MRI Actuator')

ax = fig.add_subplot(111, projection='3d')
ax.set_facecolor('#16213e')

ax.set_xlim([-1.0, 1.0])
ax.set_ylim([-1.0, 1.0])
ax.set_zlim([-0.4, 1.4])
ax.set_axis_off()
ax.set_title(
    '3-D Axial Piston Motor  —  Swashplate Concept\n'
    'Blue / Green / Red = pressurised phase   |   Gray = exhaust',
    color='white', fontsize=11, pad=12
)

# Nice default viewing angle (isometric-ish)
ax.view_init(elev=22, azim=45)

# ---------------------------------------------------------------------------
# Static decorations
# ---------------------------------------------------------------------------

# Housing / bore outline: a faint dashed circle at Z = PISTON_TOP
_hx = np.cos(_theta) * (PISTON_RADIUS + HOUSING_OUTLINE_OFFSET)
_hy = np.sin(_theta) * (PISTON_RADIUS + HOUSING_OUTLINE_OFFSET)
_hz = np.full_like(_theta, PISTON_TOP)
ax.plot(_hx, _hy, _hz, color='#444444', lw=1.0, linestyle='--', zorder=1)

# Labels for each cylinder at the top (static)
for i, label in enumerate(CYLINDER_LABELS):
    colour = COLOUR_MAP[label]
    lx = (PISTON_RADIUS + LABEL_OFFSET) * np.cos(angles_rad[i])
    ly = (PISTON_RADIUS + LABEL_OFFSET) * np.sin(angles_rad[i])
    ax.text(lx, ly, PISTON_TOP + 0.15, label,
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
# Animated objects
# ---------------------------------------------------------------------------

# Central shaft: two points – updated each frame so it extends from below
# the cam to the top housing plate
shaft_line, = ax.plot([0, 0], [0, 0], [-0.35, PISTON_TOP + 0.05],
                      color='#cccccc', lw=5, zorder=5, solid_capstyle='round')

# Swashplate surface (will be re-drawn each frame via plot_surface)
swash_surf = [None]   # mutable container so the callback can replace it

# Piston rods (one Line3D per cylinder)
piston_lines = []
for i in range(3):
    line, = ax.plot(
        [px[i], px[i]],
        [py[i], py[i]],
        [PISTON_TOP, 0.5],
        lw=10,
        color=COLOUR_MAP[CYLINDER_LABELS[i]],
        solid_capstyle='round',
        zorder=6
    )
    piston_lines.append(line)

# Cam-follower caps (small spheres at the bottom of each piston rod)
cap_plots = []
for i in range(3):
    cap, = ax.plot(
        [px[i]], [py[i]], [0.5],
        'o',
        markersize=8,
        color=COLOUR_MAP[CYLINDER_LABELS[i]],
        zorder=7
    )
    cap_plots.append(cap)


# ---------------------------------------------------------------------------
# Animation update function
# ---------------------------------------------------------------------------
def update(frame):
    t = frame / FPS                          # current time in seconds
    cam_angle = OMEGA * t                    # current cam rotation angle

    # ── Swashplate surface ────────────────────────────────────────────────
    # Remove previous surface to avoid memory build-up
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
        # Z of the cam surface under this piston
        pz = cam_z(angles_rad[i], cam_angle)

        # Update rod: from housing top down to cam surface
        piston_lines[i].set_data([px[i], px[i]], [py[i], py[i]])
        piston_lines[i].set_3d_properties([PISTON_TOP, pz])

        # Update cap position
        cap_plots[i].set_data([px[i]], [py[i]])
        cap_plots[i].set_3d_properties([pz])

        # Colouring
        if is_active(i, cam_angle):
            colour = COLOUR_MAP[label]
            active_labels.append(label)
        else:
            colour = COLOUR_GRAY

        piston_lines[i].set_color(colour)
        cap_plots[i].set_color(colour)

    # ── Phase text ────────────────────────────────────────────────────────
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

    return piston_lines + cap_plots + [_phase_text]


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
