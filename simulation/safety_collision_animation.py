"""
safety_collision_animation.py
==============================
2-D ``matplotlib`` FuncAnimation demonstrating the MRI-compatible robotic
catheter system's **clinical safety and force-response** behaviour.

Scenario
--------
The catheter advances smoothly at 8 mm/s (motor running at 2.0 Bar).
At T = 3.0 s it strikes a blood vessel wall (collision).  The on-board
force-sensing system detects the spike (> 0.15 N safety limit) and
instantly vents the pneumatic supply to 0.0 Bar — an emergency exhaust
that stops the motor and protects the patient.

Three stacked subplots (shared X-axis, T = 0 → 5 s)
-----------------------------------------------------
  1. **Position (mm)** — rises linearly at 8 mm/s until T = 3.0 s, then
     flatlines.
  2. **Contact Force (N)** — stays near 0 N; at T = 3.0 s it spikes rapidly
     to 0.15 N.  A dashed red safety-limit line is drawn at 0.15 N.
  3. **Motor Pressure (Bar)** — held at 2.0 Bar; drops to 0.0 Bar at T = 3.0 s
     (emergency exhaust).

A large flashing text warning **"COLLISION DETECTED — EMERGENCY STOP"** appears
in red after T = 3.0 s.

Requirements
------------
  pip install numpy matplotlib

Usage
-----
  python safety_collision_animation.py

Author: Sam Tsang (MRI Actuator Project)
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# ---------------------------------------------------------------------------
# Physical parameters
# ---------------------------------------------------------------------------
CATHETER_SPEED_MM_S = 8.0          # mm/s advance rate
COLLISION_TIME      = 3.0          # seconds at which collision occurs
TOTAL_TIME          = 5.0          # total simulation duration (s)
FORCE_LIMIT_N       = 0.15         # safety force threshold (N)
RUNNING_PRESSURE    = 2.0          # Bar — normal operating pressure

# Force spike shape parameters (Gaussian-like rise clamped at limit)
SPIKE_RISE_S        = 0.08         # seconds for the force to rise to limit

# ---------------------------------------------------------------------------
# Animation timing
# ---------------------------------------------------------------------------
FPS    = 60
FRAMES = int(FPS * TOTAL_TIME)

# ---------------------------------------------------------------------------
# Pre-compute full time axis so we can set static x-limits immediately
# ---------------------------------------------------------------------------
T_FULL = np.linspace(0.0, TOTAL_TIME, FRAMES)


def _position(t):
    """Catheter position (mm) at time t."""
    return np.where(t < COLLISION_TIME, CATHETER_SPEED_MM_S * t,
                    CATHETER_SPEED_MM_S * COLLISION_TIME)


def _force(t):
    """Contact force (N) — spikes at collision then stays at limit."""
    f = np.zeros_like(t, dtype=float)
    mask_spike = t >= COLLISION_TIME
    # Smooth exponential rise then clamp
    dt = np.clip(t - COLLISION_TIME, 0.0, None)
    spike_raw = FORCE_LIMIT_N * (1.0 - np.exp(-dt / SPIKE_RISE_S))
    f = np.where(mask_spike, spike_raw, f)
    # Add a tiny random physiological baseline (pre-collision)
    baseline = 0.004 * np.sin(2 * np.pi * 1.2 * t) + 0.002 * np.sin(2 * np.pi * 3.7 * t)
    f = np.where(t < COLLISION_TIME, baseline, f)
    return f


def _pressure(t):
    """Motor pressure (Bar) — instantly drops to 0 at collision."""
    return np.where(t < COLLISION_TIME, RUNNING_PRESSURE, 0.0)


# ---------------------------------------------------------------------------
# Figure / axes setup
# ---------------------------------------------------------------------------
fig, (ax1, ax2, ax3) = plt.subplots(
    3, 1, figsize=(11, 8), sharex=True,
    gridspec_kw={'hspace': 0.08}
)

BG      = '#0d1117'
PANEL   = '#161b22'
GRID_C  = '#30363d'
LINE1   = '#58a6ff'   # position
LINE2   = '#3fb950'   # force
LINE3   = '#f78166'   # pressure
LIMIT_C = '#ff4444'   # safety limit dashed line

fig.patch.set_facecolor(BG)
for ax in (ax1, ax2, ax3):
    ax.set_facecolor(PANEL)
    ax.tick_params(colors='#8b949e', labelsize=11)
    ax.yaxis.label.set_color('#c9d1d9')
    ax.xaxis.label.set_color('#c9d1d9')
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID_C)
    ax.grid(True, color=GRID_C, linewidth=0.5, linestyle='--', alpha=0.6)

fig.suptitle(
    'Clinical Safety & Force Response — MRI Robotic Catheter System\n'
    'Catheter advancing at 8 mm/s  |  Collision at T = 3.0 s  |  Emergency Stop',
    color='#c9d1d9', fontsize=15, fontweight='bold', y=0.99
)

# ── Subplot 1: Position ─────────────────────────────────────────────────────
ax1.set_xlim(0, TOTAL_TIME)
ax1.set_ylim(-1, CATHETER_SPEED_MM_S * COLLISION_TIME + 4)
ax1.set_ylabel('Position (mm)', fontsize=12)
ax1.yaxis.set_label_coords(-0.075, 0.5)

pos_line, = ax1.plot([], [], color=LINE1, lw=2.0, label='Catheter Position')
ax1.axvline(x=COLLISION_TIME, color='#ff4444', lw=1.2, linestyle=':', alpha=0.7)

# Annotation arrow marking collision
ax1.annotate(
    'Collision\nT = 3.0 s', xy=(COLLISION_TIME, CATHETER_SPEED_MM_S * COLLISION_TIME),
    xytext=(COLLISION_TIME + 0.4, CATHETER_SPEED_MM_S * COLLISION_TIME - 3),
    color='#ff4444', fontsize=11,
    arrowprops=dict(arrowstyle='->', color='#ff4444', lw=1.2)
)
ax1.legend(loc='upper left', facecolor=PANEL, edgecolor=GRID_C,
           labelcolor='#c9d1d9', fontsize=11, framealpha=0.9)

# ── Subplot 2: Contact Force ─────────────────────────────────────────────────
ax2.set_ylim(-0.02, FORCE_LIMIT_N * 1.35)
ax2.set_ylabel('Contact Force (N)', fontsize=12)
ax2.yaxis.set_label_coords(-0.075, 0.5)

force_line, = ax2.plot([], [], color=LINE2, lw=2.0, label='Contact Force')
# Safety-limit dashed red line
ax2.axhline(y=FORCE_LIMIT_N, color=LIMIT_C, lw=1.4, linestyle='--',
            label=f'Safety limit  {FORCE_LIMIT_N} N')
ax2.axvline(x=COLLISION_TIME, color='#ff4444', lw=1.2, linestyle=':', alpha=0.7)
ax2.text(TOTAL_TIME * 0.98, FORCE_LIMIT_N + 0.003, f'{FORCE_LIMIT_N} N limit',
         color=LIMIT_C, ha='right', va='bottom', fontsize=11)
ax2.legend(loc='upper left', facecolor=PANEL, edgecolor=GRID_C,
           labelcolor='#c9d1d9', fontsize=11, framealpha=0.9)

# ── Subplot 3: Motor Pressure ────────────────────────────────────────────────
ax3.set_ylim(-0.15, RUNNING_PRESSURE * 1.4)
ax3.set_ylabel('Motor Pressure (Bar)', fontsize=12)
ax3.set_xlabel('Time (s)', fontsize=12)
ax3.yaxis.set_label_coords(-0.075, 0.5)

pressure_line, = ax3.plot([], [], color=LINE3, lw=2.0, label='Motor Pressure')
ax3.axvline(x=COLLISION_TIME, color='#ff4444', lw=1.2, linestyle=':', alpha=0.7)
ax3.text(COLLISION_TIME + 0.05, RUNNING_PRESSURE * 0.9,
         'Emergency\nExhaust', color='#ff4444', fontsize=11, va='top')
ax3.legend(loc='upper left', facecolor=PANEL, edgecolor=GRID_C,
           labelcolor='#c9d1d9', fontsize=11, framealpha=0.9)

# ── Flashing warning text (shown after collision) ────────────────────────────
# Place it in figure-level coordinates so it spans all subplots
warning_text = fig.text(
    0.5, 0.50,
    'COLLISION DETECTED — EMERGENCY STOP',
    ha='center', va='center',
    fontsize=21, fontweight='bold',
    color='red',
    alpha=0.0,          # hidden initially; made visible after collision
    zorder=20,
    bbox=dict(boxstyle='round,pad=0.4', facecolor='#330000', alpha=0.0,
              edgecolor='red', linewidth=2.5)
)

# ---------------------------------------------------------------------------
# Animation update function
# ---------------------------------------------------------------------------
def update(frame):
    t_now = frame / FPS

    # Slice data up to current time
    mask = T_FULL <= t_now
    t_slice = T_FULL[mask]

    if len(t_slice) == 0:
        return pos_line, force_line, pressure_line, warning_text

    pos_data      = _position(t_slice)
    force_data    = _force(t_slice)
    pressure_data = _pressure(t_slice)

    pos_line.set_data(t_slice, pos_data)
    force_line.set_data(t_slice, force_data)
    pressure_line.set_data(t_slice, pressure_data)

    # Flashing warning after collision
    if t_now >= COLLISION_TIME:
        # Flash at 2 Hz
        flash_phase = (t_now - COLLISION_TIME) * 2.0
        alpha = 1.0 if int(flash_phase) % 2 == 0 else 0.35
        warning_text.set_alpha(alpha)
        warning_text.get_bbox_patch().set_alpha(alpha * 0.7)
    else:
        warning_text.set_alpha(0.0)
        warning_text.get_bbox_patch().set_alpha(0.0)

    return pos_line, force_line, pressure_line, warning_text


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
ani = animation.FuncAnimation(
    fig, update,
    frames=FRAMES,
    interval=1000.0 / FPS,
    blit=False
)

fig.subplots_adjust(top=0.91, bottom=0.08, left=0.10, right=0.97, hspace=0.08)
plt.show()
