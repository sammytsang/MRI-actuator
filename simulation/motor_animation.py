"""
motor_animation.py
==================
Python simulation and animation for a 3-cylinder MRI-compatible
pneumatic / hydraulic rotary motor.

Layout
------
The script opens a single figure with THREE panels:

  Panel 1 (top)    – Piston-position sine waves (mechanical motion)
  Panel 2 (middle) – Solenoid valve square-wave timing diagram
  Panel 3 (bottom) – 2-D mechanical animation: spinning rotor + 3 pistons

A vertical "now" cursor sweeps across panels 1 & 2 in sync with the
rotor angle shown in panel 3.

Requirements
------------
  pip install numpy matplotlib

Usage
-----
  python motor_animation.py

Author: Sam Tsang (MRI Actuator Project)
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.animation as animation
from matplotlib.gridspec import GridSpec

# ---------------------------------------------------------------------------
# Motor timing parameters (match the timing graph / Arduino sketch)
# ---------------------------------------------------------------------------
CYCLE_TIME   = 1.5          # seconds per full revolution
PHASE_TIME   = CYCLE_TIME / 3.0   # 0.5 s per 120° phase
FPS          = 60           # animation frames per second
TOTAL_CYCLES = 2            # how many full cycles to show in static graphs

# Colours for the three cylinders
COLOUR = {'A': '#2196F3',   # blue
          'B': '#4CAF50',   # green
          'C': '#F44336'}   # red

# ---------------------------------------------------------------------------
# Pre-compute the static waveforms over 2 cycles for panels 1 & 2
# ---------------------------------------------------------------------------
t = np.linspace(0, CYCLE_TIME * TOTAL_CYCLES, 2000)
omega = 2 * np.pi / CYCLE_TIME   # angular frequency (rad s⁻¹)

# Mechanical piston displacement: sinusoidal, 120° apart
pos = {
    'A': np.sin(omega * t),
    'B': np.sin(omega * t - 2 * np.pi / 3),
    'C': np.sin(omega * t - 4 * np.pi / 3),
}

# Valve state: only ONE valve HIGH at a time (square-wave commutation)
# Phase 0 (0–0.5 s): A on | Phase 1 (0.5–1.0 s): B on | Phase 2 (1.0–1.5 s): C on
phase = (t % CYCLE_TIME) / PHASE_TIME          # 0–3 (repeating)
valve = {
    'A': ((phase % 3) < 1).astype(float),
    'B': (((phase % 3) >= 1) & ((phase % 3) < 2)).astype(float),
    'C': ((phase % 3) >= 2).astype(float),
}

# ---------------------------------------------------------------------------
# Figure / axes layout
# ---------------------------------------------------------------------------
fig = plt.figure(figsize=(12, 10))
fig.patch.set_facecolor('#1a1a2e')
gs  = GridSpec(3, 1, figure=fig, hspace=0.45)

ax_sine  = fig.add_subplot(gs[0])   # piston positions
ax_valve = fig.add_subplot(gs[1])   # solenoid timing
ax_mech  = fig.add_subplot(gs[2])   # 2-D mechanical view

for ax in (ax_sine, ax_valve, ax_mech):
    ax.set_facecolor('#16213e')
    for spine in ax.spines.values():
        spine.set_edgecolor('#444')

fig.suptitle('3-Cylinder MRI-Compatible Pneumatic Motor — Simulation',
             color='white', fontsize=17, fontweight='bold', y=0.98)

# ── Panel 1: Piston-position sine waves ────────────────────────────────────
for key in ('A', 'B', 'C'):
    ax_sine.plot(t, pos[key], color=COLOUR[key], lw=1.5,
                 label=f'Piston {key}  ({["0°","120°","240°"][ord(key)-65]})')

ax_sine.set_ylabel('Displacement (norm.)', color='#ccc', fontsize=12)
ax_sine.set_title('Mechanical Piston Motion', color='#ccc', fontsize=13)
ax_sine.legend(loc='upper right', fontsize=11,
               facecolor='#16213e', edgecolor='#555', labelcolor='white')
ax_sine.set_xlim(0, t[-1])
ax_sine.set_ylim(-1.4, 1.4)
ax_sine.tick_params(colors='#aaa', labelsize=11)
ax_sine.set_xticklabels([])
ax_sine.grid(color='#333', linestyle='--', linewidth=0.5)

cursor_sine,  = ax_sine.plot([], [], color='white', lw=1.5, alpha=0.8)

# ── Panel 2: Solenoid valve timing (square waves) ──────────────────────────
offsets = {'A': 2.2, 'B': 1.1, 'C': 0.0}
for key in ('A', 'B', 'C'):
    ax_valve.plot(t, valve[key] + offsets[key],
                  color=COLOUR[key], lw=1.8, label=f'Valve {key}')
    ax_valve.axhline(offsets[key],       color=COLOUR[key], lw=0.5, alpha=0.3)
    ax_valve.axhline(offsets[key] + 1.0, color=COLOUR[key], lw=0.5, alpha=0.3)
    ax_valve.text(-0.04 * t[-1], offsets[key] + 0.5, f' V{key}',
                  color=COLOUR[key], va='center', fontsize=11)

ax_valve.set_ylabel('Valve State', color='#ccc', fontsize=12)
ax_valve.set_xlabel('Time (s)', color='#ccc', fontsize=12)
ax_valve.set_title('Solenoid Commutation Logic  ("A on → B, C off")',
                   color='#ccc', fontsize=13)
ax_valve.set_xlim(0, t[-1])
ax_valve.set_ylim(-0.3, 3.5)
ax_valve.tick_params(colors='#aaa', labelsize=11)
ax_valve.set_yticks([])
ax_valve.grid(color='#333', linestyle='--', linewidth=0.5)

cursor_valve, = ax_valve.plot([], [], color='white', lw=1.5, alpha=0.8)

# ── Panel 3: 2-D mechanical view ───────────────────────────────────────────
ax_mech.set_xlim(-2.2, 2.2)
ax_mech.set_ylim(-2.2, 2.2)
ax_mech.set_aspect('equal')
ax_mech.set_title('2-D Mechanical Animation', color='#ccc', fontsize=13)
ax_mech.tick_params(left=False, bottom=False,
                    labelleft=False, labelbottom=False)

# Draw static housing circle
housing = plt.Circle((0, 0), 2.0, fill=False,
                      edgecolor='#555', linewidth=1.5, linestyle='--')
ax_mech.add_patch(housing)

# Central rotor disk
rotor_patch = plt.Circle((0, 0), 0.35, color='#888', zorder=5)
ax_mech.add_patch(rotor_patch)

# Cylinder (piston) setup – 3 cylinders at 0°, 120°, 240° from centre
# Each piston: a rectangle that moves radially in/out
CYLINDER_ANGLE_DEG = [0, 120, 240]           # fixed cylinder axes
CYLINDER_LABEL     = ['A', 'B', 'C']
PISTON_REST        = 1.25    # radius when piston fully retracted
PISTON_EXTEND      = 0.60    # radius when piston fully extended (toward rotor)
PISTON_WIDTH       = 0.22    # width of the piston rectangle

piston_patches = []   # the moving piston bodies (Polygon)
cyl_label_objs = []   # text labels


def rotated_rect_verts(cx, cy, half_w, half_h, angle_rad):
    """Return (4, 2) array of vertices for a rectangle centred at (cx, cy),
    with half-widths half_w (perpendicular) and half_h (along the radial
    direction), rotated by angle_rad."""
    corners = np.array([[-half_w, -half_h],
                        [ half_w, -half_h],
                        [ half_w,  half_h],
                        [-half_w,  half_h]], dtype=float)
    cos_a, sin_a = np.cos(angle_rad), np.sin(angle_rad)
    rot = np.array([[cos_a, -sin_a], [sin_a, cos_a]])
    rotated = corners @ rot.T
    rotated[:, 0] += cx
    rotated[:, 1] += cy
    return rotated


for i, (angle_deg, label) in enumerate(zip(CYLINDER_ANGLE_DEG, CYLINDER_LABEL)):
    angle_rad = np.deg2rad(angle_deg)

    # Static cylinder bore outline along the radial axis
    bore_len = 0.75
    bore_cx = np.cos(angle_rad) * (PISTON_REST + bore_len / 2)
    bore_cy = np.sin(angle_rad) * (PISTON_REST + bore_len / 2)
    bore_verts = rotated_rect_verts(bore_cx, bore_cy,
                                    PISTON_WIDTH / 2, bore_len / 2,
                                    angle_rad)
    bore = mpatches.Polygon(bore_verts, closed=True,
                            linewidth=1, edgecolor='#555',
                            facecolor='#1a1a2e', zorder=2)
    ax_mech.add_patch(bore)

    # Piston body (square, moves radially in/out)
    piston_r = PISTON_REST
    px = np.cos(angle_rad) * piston_r
    py = np.sin(angle_rad) * piston_r
    hw = PISTON_WIDTH / 2
    p_verts = rotated_rect_verts(px, py, hw, hw, angle_rad)
    p = mpatches.Polygon(p_verts, closed=True,
                         linewidth=1, edgecolor=COLOUR[label],
                         facecolor='#333', zorder=4)
    ax_mech.add_patch(p)
    piston_patches.append(p)

    # Cylinder label outside the housing
    lx = np.cos(angle_rad) * 2.05
    ly = np.sin(angle_rad) * 2.05
    txt = ax_mech.text(lx, ly, label,
                       color=COLOUR[label], ha='center', va='center',
                       fontsize=14, fontweight='bold', zorder=6)
    cyl_label_objs.append(txt)

# Rotor arm (a line from centre that rotates)
rotor_arm, = ax_mech.plot([], [], color='white', lw=2.5, zorder=6)

# Phase indicator text in the centre of the mechanical panel
phase_text = ax_mech.text(0, -2.1, '', color='white',
                          ha='center', va='bottom', fontsize=12)

# ---------------------------------------------------------------------------
# Animation update function
# ---------------------------------------------------------------------------
total_frames = int(FPS * CYCLE_TIME * TOTAL_CYCLES)

def update(frame):
    # Current simulation time (loops over TOTAL_CYCLES)
    sim_time = (frame / total_frames) * (CYCLE_TIME * TOTAL_CYCLES)
    sim_time = sim_time % (CYCLE_TIME * TOTAL_CYCLES)   # safety clamp

    # ── Cursors on top two panels ──────────────────────────────────────────
    cursor_sine.set_data( [sim_time, sim_time], [-1.4, 1.4])
    cursor_valve.set_data([sim_time, sim_time], [-0.3, 3.5])

    # ── Current shaft angle (radians) ─────────────────────────────────────
    shaft_angle = omega * sim_time   # continuous rotation

    # ── Rotor arm ─────────────────────────────────────────────────────────
    arm_x = [0, 0.32 * np.cos(shaft_angle)]
    arm_y = [0, 0.32 * np.sin(shaft_angle)]
    rotor_arm.set_data(arm_x, arm_y)

    # ── Which phase are we in (0=A, 1=B, 2=C)? ────────────────────────────
    current_phase = int((sim_time % CYCLE_TIME) / PHASE_TIME) % 3
    active_label  = CYLINDER_LABEL[current_phase]

    # ── Update each piston ────────────────────────────────────────────────
    for i, (angle_deg, label) in enumerate(zip(CYLINDER_ANGLE_DEG, CYLINDER_LABEL)):
        angle_rad = np.deg2rad(angle_deg)

        # Piston position: sinusoidal, phase-shifted by 120° per cylinder
        phase_offset = i * 2 * np.pi / 3
        norm_pos = np.sin(shaft_angle - phase_offset)   # −1 … +1

        # Map norm_pos to radius (−1 = fully extended, +1 = fully retracted)
        r = PISTON_REST + (PISTON_EXTEND - PISTON_REST) * (1 - norm_pos) / 2

        px = np.cos(angle_rad) * r
        py = np.sin(angle_rad) * r

        # Rebuild piston polygon vertices at the new radial position
        hw = PISTON_WIDTH / 2
        verts = rotated_rect_verts(px, py, hw, hw, angle_rad)
        piston_patches[i].set_xy(verts)

        # Colour: bright when active (pressurised), dim otherwise
        if label == active_label:
            piston_patches[i].set_facecolor(COLOUR[label])
            piston_patches[i].set_alpha(1.0)
        else:
            piston_patches[i].set_facecolor('#333')
            piston_patches[i].set_alpha(0.7)

    # ── Phase indicator ────────────────────────────────────────────────────
    phase_names = ['Valve A  ON  (B, C off)',
                   'Valve B  ON  (A, C off)',
                   'Valve C  ON  (A, B off)']
    phase_text.set_text(phase_names[current_phase])
    phase_text.set_color(COLOUR[active_label])

    return [cursor_sine, cursor_valve, rotor_arm,
            phase_text] + piston_patches

# ---------------------------------------------------------------------------
# Run the animation
# ---------------------------------------------------------------------------
ani = animation.FuncAnimation(
    fig, update,
    frames=total_frames,
    interval=1000 / FPS,   # ms per frame
    blit=True)

plt.tight_layout(rect=[0, 0, 1, 0.97])
plt.show()
