"""
3d_solid_motor_animation.py
===========================
Standalone "Solid 3D" animation of the MRI-compatible pneumatic axial-piston
motor using matplotlib.  Every component is rendered as an actual 3D geometric
volume (``plot_surface`` cylinders / disks) rather than thick lines, giving an
appearance much closer to the physical CAD model.

Mechanism
---------
Three pistons are arranged in a circle at 0°, 120° and 240° around a central
shaft, with their axes *parallel* to the shaft (axial arrangement).  A wavy
cam (two full sine-wave periods per revolution) is fixed to the shaft and
rotates with it.  As the cam rotates the pistons are pushed up and down,
converting pneumatic pressure into torque via virtual work:

    T = F × |dh/dθ|

where h(θ) = A·sin(2·(ψ − θ)) and A = 10 mm (physical amplitude).

Visual Elements
---------------
* **Central Shaft**         – solid 3D cylinder along the Z-axis.
* **Wavy Cam**              – solid disk with a flat top and a 2-period
                              sinusoidal bottom surface; rotates with the shaft.
* **Pneumatic Chambers**    – 3 translucent 3D cylinders (α = 0.2) fixed at
                              0°, 120°, and 240° to represent the housing bores.
* **Moving Pistons**        – 3 solid 3D cylinders inside the chambers; tops
                              track the bottom of the wavy cam surface.
* **Dynamic Colouring**
    - *Push phase* (piston moving UP, delivering 52 N thrust) → Bright Red
    - *Exhaust phase* (piston returning down)                  → Light Blue
* **Live Telemetry**        – text overlay: current cam angle, active chamber,
                              theoretical thrust, and instantaneous torque.

Animation Settings
------------------
  CYCLE_TIME = 4.5 s per revolution  (slow and clear for presentations)
  FPS        = 30

Requirements
------------
  pip install numpy matplotlib

Usage
-----
  python simulation/3d_solid_motor_animation.py

Author: Sam Tsang (MRI Actuator Project)
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 – registers projection

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
CYCLE_TIME = 4.5           # seconds per full revolution
FPS        = 30            # frames per second
FRAMES     = int(FPS * CYCLE_TIME)  # frames for one complete loop

OMEGA = 2.0 * np.pi / CYCLE_TIME   # angular velocity (rad/s)

# Piston circle radius (pistons sit on a ring of this radius around the shaft)
PISTON_RADIUS_CIRCLE = 0.55

# Shaft geometry
SHAFT_RADIUS = 0.07

# Chamber geometry (stationary housing bores)
CHAMBER_RADIUS = 0.13
CHAMBER_BOTTOM = 0.0
CHAMBER_TOP    = 0.85

# Piston geometry (solid cylinders inside chambers)
PISTON_BODY_RADIUS = 0.10

# Wavy cam geometry
CAM_OUTER_RADIUS = 0.75
CAM_AMPLITUDE    = 0.18          # visual amplitude (normalised units)
CAM_CENTER_Z     = 1.00          # neutral height of the cam bottom surface
CAM_TOP_Z        = CAM_CENTER_Z + CAM_AMPLITUDE + 0.06  # height of flat top

# Physical parameters (for torque calculations)
PHYSICAL_AMPLITUDE = 0.010       # 10 mm → m
THRUST_FORCE       = 52.0        # N per active chamber at 2 bar

# Cylinder angular positions and labels
CYLINDER_ANGLES_DEG = [0, 120, 240]
CYLINDER_LABELS     = ['A', 'B', 'C']

# Phase window: each cylinder is "active" (push phase) for 120° of rotation
PHASE_WINDOW = 2.0 * np.pi / 3.0

# Colours
COLOUR_PUSH    = '#FF3333'   # bright red  – push / active phase
COLOUR_EXHAUST = '#7EC8E3'   # light blue  – exhaust / return phase
COLOUR_SHAFT   = '#cccccc'   # light grey  – central shaft
COLOUR_CHAMBER = '#4488aa'   # steel blue  – housing chambers
COLOUR_CAM_BOT = '#00dddd'   # cyan        – cam bottom (wavy surface)
COLOUR_CAM_TOP = '#00aacc'   # darker cyan – cam top/edge

LABEL_COLOURS = ['#2196F3', '#4CAF50', '#F44336']  # blue / green / red for A/B/C

# Mesh resolution (keep moderate for real-time performance)
N_THETA_CYL = 24   # angular segments for shaft, chambers, pistons
N_THETA_CAM = 40   # angular segments for cam disk
N_R_CAM     =  8   # radial rings for cam disk
N_R_DISK    =  4   # radial rings for end caps

# ---------------------------------------------------------------------------
# Derived geometry
# ---------------------------------------------------------------------------
angles_rad = np.deg2rad(CYLINDER_ANGLES_DEG)
px = PISTON_RADIUS_CIRCLE * np.cos(angles_rad)   # piston X positions (fixed)
py = PISTON_RADIUS_CIRCLE * np.sin(angles_rad)   # piston Y positions (fixed)


# ---------------------------------------------------------------------------
# Physics helpers
# ---------------------------------------------------------------------------
def cam_z_at(piston_angle_rad, cam_angle_rad):
    """Z height of the wavy cam bottom surface directly under a piston.

    Uses a 2-period sine wave centred at CAM_CENTER_Z:
        Z = CAM_CENTER_Z + A · sin(2·(ψ − θ))
    """
    return CAM_CENTER_Z + CAM_AMPLITUDE * np.sin(
        2.0 * (piston_angle_rad - cam_angle_rad)
    )


def is_active(piston_index, cam_angle_rad):
    """Return True when piston *piston_index* is in its 120° push phase."""
    phase = (cam_angle_rad - angles_rad[piston_index]) % (2.0 * np.pi)
    return phase < PHASE_WINDOW


def instantaneous_torque(cam_angle_rad):
    """Net instantaneous output torque (N·m) from all active pistons.

    Virtual-work principle:  T = F · |dh/dθ| per active piston.
    dh/dθ = −2·A_phys · cos(2·(ψ − θ))
    """
    total = 0.0
    for i in range(3):
        if is_active(i, cam_angle_rad):
            slope = 2.0 * PHYSICAL_AMPLITUDE * abs(
                np.cos(2.0 * (angles_rad[i] - cam_angle_rad))
            )
            total += THRUST_FORCE * slope
    return total


# ---------------------------------------------------------------------------
# Geometry helpers: produce (X, Y, Z) arrays for plot_surface
# ---------------------------------------------------------------------------
def cylinder_surface(cx, cy, z_bot, z_top, radius, n=N_THETA_CYL):
    """Lateral surface of a closed cylinder."""
    theta = np.linspace(0, 2.0 * np.pi, n)
    z     = np.array([z_bot, z_top])
    T, Z  = np.meshgrid(theta, z)
    X = cx + radius * np.cos(T)
    Y = cy + radius * np.sin(T)
    return X, Y, Z


def disk_surface(cx, cy, z_val, radius, n=N_THETA_CYL, nr=N_R_DISK):
    """Flat circular disk (end cap)."""
    r         = np.linspace(0.0, radius, nr)
    theta     = np.linspace(0.0, 2.0 * np.pi, n)
    R, T      = np.meshgrid(r, theta)
    X = cx + R * np.cos(T)
    Y = cy + R * np.sin(T)
    Z = np.full_like(X, z_val)
    return X, Y, Z


# Pre-compute the cam disk meshgrid (X/Y base; Z updated each frame)
_cam_theta         = np.linspace(0.0, 2.0 * np.pi, N_THETA_CAM)
_cam_r             = np.linspace(0.0, CAM_OUTER_RADIUS, N_R_CAM)
_cam_T, _cam_R     = np.meshgrid(_cam_theta, _cam_r)
_cam_X             = _cam_R * np.cos(_cam_T)
_cam_Y             = _cam_R * np.sin(_cam_T)


def cam_bottom_surface(cam_angle):
    """Wavy bottom surface of the rotating cam disk.

    Z scales with radius so the centre is flat and wave amplitude grows
    toward the outer edge, matching physical barrel-cam geometry:
        Z = CAM_CENTER_Z + A · (r / r_max) · sin(2·(θ − cam_angle))
    """
    Z = CAM_CENTER_Z + CAM_AMPLITUDE * (_cam_R / CAM_OUTER_RADIUS) * np.sin(
        2.0 * (_cam_T - cam_angle)
    )
    return _cam_X, _cam_Y, Z


def cam_top_surface():
    """Flat top surface of the cam disk."""
    Z = np.full(_cam_X.shape, CAM_TOP_Z)
    return _cam_X, _cam_Y, Z


def cam_edge_surface(cam_angle):
    """Outer cylindrical rim connecting the wavy bottom edge to the flat top."""
    theta    = np.linspace(0.0, 2.0 * np.pi, N_THETA_CAM)
    z_bottom = CAM_CENTER_Z + CAM_AMPLITUDE * np.sin(2.0 * (theta - cam_angle))
    z_top    = np.full_like(theta, CAM_TOP_Z)
    E_X = CAM_OUTER_RADIUS * np.cos(theta)
    E_Y = CAM_OUTER_RADIUS * np.sin(theta)
    # Stack into (2, N) arrays: row 0 = bottom edge, row 1 = top edge
    return (np.vstack([E_X, E_X]),
            np.vstack([E_Y, E_Y]),
            np.vstack([z_bottom, z_top]))


# ---------------------------------------------------------------------------
# Figure and axes setup
# ---------------------------------------------------------------------------
fig = plt.figure(figsize=(10, 9))
fig.patch.set_facecolor('#1a1a2e')
try:
    fig.canvas.manager.set_window_title(
        'Solid 3D Axial Piston Motor — MRI Actuator'
    )
except Exception:
    pass

ax = fig.add_subplot(111, projection='3d')
ax.set_facecolor('#16213e')

ax.set_xlim([-1.0, 1.0])
ax.set_ylim([-1.0, 1.0])
ax.set_zlim([-0.2, 1.6])
ax.set_axis_off()
ax.set_title(
    'Solid 3D Axial Piston Motor — Wavy Track (2 Periods)  |  MRI Actuator\n'
    'Red = pushing (52 N thrust)   |   Light Blue = exhaust',
    color='white', fontsize=11, pad=12,
)
ax.view_init(elev=25, azim=45)

# ---------------------------------------------------------------------------
# Static 3D geometry (drawn once)
# ---------------------------------------------------------------------------

# Central shaft – solid cylinder + top end cap
_sx, _sy, _sz = cylinder_surface(0, 0, -0.12, CAM_TOP_Z + 0.08, SHAFT_RADIUS)
ax.plot_surface(_sx, _sy, _sz, color=COLOUR_SHAFT, alpha=1.0, linewidth=0)
_scx, _scy, _scz = disk_surface(0, 0, CAM_TOP_Z + 0.08, SHAFT_RADIUS)
ax.plot_surface(_scx, _scy, _scz, color=COLOUR_SHAFT, alpha=1.0, linewidth=0)

# Pneumatic chamber cylinders – translucent stationary housing bores
for i in range(3):
    cx, cy = px[i], py[i]
    # Lateral surface
    _cx, _cy, _cz = cylinder_surface(cx, cy, CHAMBER_BOTTOM, CHAMBER_TOP,
                                     CHAMBER_RADIUS)
    ax.plot_surface(_cx, _cy, _cz,
                    color=COLOUR_CHAMBER, alpha=0.18, linewidth=0)
    # Bottom end cap
    _cbx, _cby, _cbz = disk_surface(cx, cy, CHAMBER_BOTTOM, CHAMBER_RADIUS)
    ax.plot_surface(_cbx, _cby, _cbz,
                    color=COLOUR_CHAMBER, alpha=0.18, linewidth=0)
    # Cylinder label (A / B / C)
    lx = (PISTON_RADIUS_CIRCLE + 0.24) * np.cos(angles_rad[i])
    ly = (PISTON_RADIUS_CIRCLE + 0.24) * np.sin(angles_rad[i])
    ax.text(lx, ly, CHAMBER_BOTTOM - 0.13, CYLINDER_LABELS[i],
            color=LABEL_COLOURS[i], fontsize=13, fontweight='bold',
            ha='center', va='center', zorder=10)

# Faint dashed base ring (housing footprint reference)
_htheta = np.linspace(0, 2.0 * np.pi, 60)
ax.plot(
    np.cos(_htheta) * (PISTON_RADIUS_CIRCLE + 0.16),
    np.sin(_htheta) * (PISTON_RADIUS_CIRCLE + 0.16),
    np.full_like(_htheta, -0.03),
    color='#445566', lw=1.0, linestyle='--', zorder=1,
)

# ---------------------------------------------------------------------------
# Mutable containers for dynamic surfaces (replaced every frame)
# ---------------------------------------------------------------------------
# cam_surfs[0] = bottom wavy disk, [1] = top flat disk, [2] = outer rim
cam_surfs = [None, None, None]

# piston_surfs[i] = [lateral_surface, top_cap_surface]
piston_surfs = [[None, None] for _ in range(3)]

# ---------------------------------------------------------------------------
# Telemetry text overlays
# ---------------------------------------------------------------------------
_telemetry = ax.text2D(
    0.02, 0.97, '',
    transform=ax.transAxes,
    color='white', fontsize=10, ha='left', va='top',
    fontfamily='monospace',
    bbox=dict(
        boxstyle='round,pad=0.4',
        facecolor='#0d0d1a', alpha=0.80,
        edgecolor='#336688', linewidth=1.2,
    ),
)

_phase_text = ax.text2D(
    0.5, 0.02, '',
    transform=ax.transAxes,
    color='white', fontsize=11, ha='center', va='bottom',
    fontweight='bold',
)

# ---------------------------------------------------------------------------
# Animation update function
# ---------------------------------------------------------------------------
def update(frame):
    """Called by FuncAnimation for each frame."""
    t         = frame / FPS
    cam_angle = OMEGA * t
    cam_deg   = np.degrees(cam_angle) % 360.0

    # ── Wavy cam (remove old, draw new) ──────────────────────────────────
    for surf in cam_surfs:
        if surf is not None:
            surf.remove()

    # Bottom – wavy sinusoidal surface
    X, Y, Z = cam_bottom_surface(cam_angle)
    cam_surfs[0] = ax.plot_surface(
        X, Y, Z,
        color=COLOUR_CAM_BOT, alpha=0.60,
        edgecolor='#336666', linewidth=0.15,
    )

    # Top – flat solid disk
    X2, Y2, Z2 = cam_top_surface()
    cam_surfs[1] = ax.plot_surface(
        X2, Y2, Z2,
        color=COLOUR_CAM_TOP, alpha=0.80,
        linewidth=0,
    )

    # Outer rim – cylinder connecting wavy edge to flat top
    EX, EY, EZ = cam_edge_surface(cam_angle)
    cam_surfs[2] = ax.plot_surface(
        EX, EY, EZ,
        color=COLOUR_CAM_TOP, alpha=0.65,
        linewidth=0,
    )

    # ── Moving pistons ────────────────────────────────────────────────────
    active_labels = []

    for i, label in enumerate(CYLINDER_LABELS):
        pz_top = cam_z_at(angles_rad[i], cam_angle)  # top tracks cam bottom
        pz_bot = CHAMBER_BOTTOM                        # base always at Z = 0

        active = is_active(i, cam_angle)
        colour = COLOUR_PUSH if active else COLOUR_EXHAUST
        if active:
            active_labels.append(label)

        # Remove old piston surfaces
        for surf in piston_surfs[i]:
            if surf is not None:
                surf.remove()

        # Lateral surface of piston cylinder
        lx, ly, lz = cylinder_surface(px[i], py[i], pz_bot, pz_top,
                                       PISTON_BODY_RADIUS)
        piston_surfs[i][0] = ax.plot_surface(
            lx, ly, lz,
            color=colour, alpha=0.95, linewidth=0,
        )

        # Top end cap (the piston face that pushes against the cam)
        tx, ty, tz = disk_surface(px[i], py[i], pz_top, PISTON_BODY_RADIUS)
        piston_surfs[i][1] = ax.plot_surface(
            tx, ty, tz,
            color=colour, alpha=0.95, linewidth=0,
        )

    # ── Live telemetry ────────────────────────────────────────────────────
    torque = instantaneous_torque(cam_angle)

    if active_labels:
        lbl        = active_labels[0]
        idx        = CYLINDER_LABELS.index(lbl)
        colour_lbl = LABEL_COLOURS[idx]
        colour_name = ['Blue', 'Green', 'Red'][idx]
        firing_str  = f'Chamber {lbl}  ({colour_name})'
        thrust_str  = f'{THRUST_FORCE:.1f} N'
        torque_str  = f'{torque:.3f} N·m'
        others      = [l for l in CYLINDER_LABELS if l != lbl]
        _phase_text.set_text(
            f'▲  Chamber {lbl} FIRING  (52 N thrust)   |   '
            f'Chambers {others[0]}, {others[1]} exhausting'
        )
        _phase_text.set_color(COLOUR_PUSH)
        _telemetry.set_color(colour_lbl)
    else:
        firing_str = '—'
        thrust_str = '—'
        torque_str = f'{torque:.3f} N·m'
        _phase_text.set_text('')
        _telemetry.set_color('white')

    _telemetry.set_text(
        f'Cam Angle : {cam_deg:6.1f}°\n'
        f'Firing    : {firing_str}\n'
        f'Thrust    : {thrust_str}\n'
        f'Torque    : {torque_str}'
    )

    return [_telemetry, _phase_text]


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
ani = animation.FuncAnimation(
    fig,
    update,
    frames=FRAMES,
    interval=1000.0 / FPS,   # ms per frame
    blit=False,              # blit=False keeps 3-D mouse interaction working
)

plt.tight_layout()
plt.show()
