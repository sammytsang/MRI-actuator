"""
system_architecture_animation.py
==================================
2-D ``matplotlib`` FuncAnimation that visually maps the **entire MRI-compatible
robotic catheter system** — from the surgeon to the patient — as an animated
block-diagram / pipeline suitable for an academic poster or presentation.

Layout (left → right)
----------------------
  Control Room  |  MRI Shielding Wall  |  MRI Room
  ─────────────────────────────────────────────────
  [Surgeon       [Arduino /     [10 m Air  [Pneumatic  [2.5:1    [Catheter
   Joystick]  →  Solenoid  →   Tubes]  →   Motor]   →  Gearbox] →  in Patient]
                 Valves]

Animation steps
---------------
  Step 1 — Surgeon moves joystick (small dot pulses on the joystick block).
  Step 2 — Arduino sends electrical signal (yellow flash) to solenoid valves.
  Step 3 — High-pressure air (blue/red pulses) travels along the long air tubes
            across the MRI wall into the MRI room.
  Step 4 — Pneumatic Motor block shows a spinning indicator.
  Step 5 — Catheter block advances a short red "catheter" segment into the
            "Patient" block.

Requirements
------------
  pip install numpy matplotlib

Usage
-----
  python system_architecture_animation.py

Author: Sam Tsang (MRI Actuator Project)
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.animation as animation
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# ---------------------------------------------------------------------------
# Layout constants (all in data-space units, axes range 0–10 × 0–6)
# ---------------------------------------------------------------------------
AX_W, AX_H = 10.0, 6.0

# Block positions: (centre_x, centre_y, half_width, half_height)
BLOCKS = {
    'joystick':   (0.85, 3.0, 0.70, 0.55),
    'arduino':    (2.60, 3.0, 0.70, 0.55),
    'solenoid':   (2.60, 1.6, 0.70, 0.55),
    'tubes':      (5.50, 3.0, 0.85, 0.55),
    'motor':      (7.30, 3.0, 0.70, 0.55),
    'gearbox':    (8.55, 3.0, 0.60, 0.55),
    'catheter':   (9.50, 3.0, 0.35, 0.55),
}

# Colours
BG_COL       = '#0d1117'
PANEL_COL    = '#161b22'
CTRL_COL     = '#1565C0'   # control-room blocks
MRI_COL      = '#1b5e20'   # MRI-room blocks
WALL_COL     = '#795548'   # MRI wall colour
ELEC_COL     = '#ffd600'   # electrical signal
AIR_COL_HI   = '#ef5350'   # high-pressure air
AIR_COL_LO   = '#42a5f5'   # low-pressure / exhaust air
ARROW_COL    = '#90caf9'   # static connection arrows
TEXT_COL     = '#e6edf3'
PATIENT_COL  = '#ad1457'   # patient block

# MRI wall x-position
WALL_X = 3.95

# Static arrow connection data: (from_block, to_block) — drawn once
CONNECTIONS = [
    ('joystick', 'arduino'),
    ('arduino',  'solenoid'),
    ('solenoid', 'tubes'),      # crosses the wall
    ('tubes',    'motor'),
    ('motor',    'gearbox'),
    ('gearbox',  'catheter'),
]

# ---------------------------------------------------------------------------
# Figure / axes
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(14, 7))
fig.patch.set_facecolor(BG_COL)
ax.set_facecolor(BG_COL)
ax.set_xlim(-0.2, AX_W + 0.2)
ax.set_ylim(0.0, AX_H)
ax.set_aspect('equal')
ax.set_axis_off()

fig.suptitle(
    'MRI-Compatible Robotic Catheter System — Animated Signal & Pneumatic Pipeline\n'
    'Control Room  |  MRI Shielding Wall  |  MRI Room',
    color=TEXT_COL, fontsize=12, fontweight='bold', y=0.99
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def block_rect(name):
    """Return (x_left, y_bottom, width, height) for *name*."""
    cx, cy, hw, hh = BLOCKS[name]
    return cx - hw, cy - hh, 2 * hw, 2 * hh


def block_right_edge(name):
    cx, cy, hw, hh = BLOCKS[name]
    return cx + hw, cy


def block_left_edge(name):
    cx, cy, hw, hh = BLOCKS[name]
    return cx - hw, cy


def block_centre(name):
    cx, cy, _, _ = BLOCKS[name]
    return cx, cy


def draw_fancy_box(ax, name, colour, label, sublabel='', text_col=TEXT_COL):
    x, y, w, h = block_rect(name)
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle='round,pad=0.07',
        linewidth=1.8,
        edgecolor=colour,
        facecolor=colour + '33',   # semi-transparent fill
        zorder=3
    )
    ax.add_patch(box)
    cx, cy, _, _ = BLOCKS[name]
    ax.text(cx, cy + 0.12, label, ha='center', va='center',
            color=TEXT_COL, fontsize=8.5, fontweight='bold', zorder=4)
    if sublabel:
        ax.text(cx, cy - 0.18, sublabel, ha='center', va='center',
                color=colour, fontsize=7.0, zorder=4)
    return box


# ---------------------------------------------------------------------------
# Draw MRI shielding wall
# ---------------------------------------------------------------------------
wall_patch = ax.fill_betweenx(
    [0.3, AX_H - 0.3], WALL_X - 0.08, WALL_X + 0.08,
    color=WALL_COL, alpha=0.85, zorder=2
)
# Dashed border lines
for xw in (WALL_X - 0.08, WALL_X + 0.08):
    ax.plot([xw, xw], [0.3, AX_H - 0.3],
            color='#bcaaa4', lw=1.0, linestyle='--', alpha=0.7, zorder=3)
ax.text(WALL_X, AX_H - 0.15, 'MRI Shielding Wall', ha='center', va='top',
        color='#bcaaa4', fontsize=8, style='italic', zorder=5)

# Room labels
ax.text(WALL_X * 0.45, AX_H - 0.15, 'CONTROL ROOM',
        ha='center', va='top', color='#90caf9',
        fontsize=9, fontweight='bold', zorder=5)
ax.text((WALL_X + AX_W) * 0.55, AX_H - 0.15, 'MRI ROOM',
        ha='center', va='top', color='#a5d6a7',
        fontsize=9, fontweight='bold', zorder=5)

# ---------------------------------------------------------------------------
# Draw static blocks
# ---------------------------------------------------------------------------
draw_fancy_box(ax, 'joystick', CTRL_COL, 'Surgeon\nJoystick', 'Input device')
draw_fancy_box(ax, 'arduino',  CTRL_COL, 'Arduino\nController', 'ATmega2560')
draw_fancy_box(ax, 'solenoid', CTRL_COL, 'Solenoid\nValves', '3× 24 V DC')
draw_fancy_box(ax, 'tubes',    MRI_COL,  '10 m Air\nTubes', 'Ø 6 mm nylon')
draw_fancy_box(ax, 'motor',    MRI_COL,  'Pneumatic\nMotor', '32 RPM / 2 bar')
draw_fancy_box(ax, 'gearbox',  MRI_COL,  '2.5:1\nGearbox', '12.8 RPM')

# Patient block (special colour)
cx, cy, hw, hh = BLOCKS['catheter']
patient_box = FancyBboxPatch(
    (cx - hw, cy - hh), 2 * hw, 2 * hh,
    boxstyle='round,pad=0.07',
    linewidth=1.8,
    edgecolor=PATIENT_COL,
    facecolor=PATIENT_COL + '33',
    zorder=3
)
ax.add_patch(patient_box)
ax.text(cx, cy + 0.12, 'Catheter', ha='center', va='center',
        color=TEXT_COL, fontsize=8.5, fontweight='bold', zorder=4)
ax.text(cx, cy - 0.18, 'in Patient\n8 mm/s', ha='center', va='center',
        color=PATIENT_COL, fontsize=7.0, zorder=4)

# Joystick icon — simple cross
jcx, jcy = block_centre('joystick')
ax.plot([jcx, jcx], [jcy - 0.42, jcy + 0.38], color='#90caf9', lw=2.5, zorder=5)
ax.plot([jcx - 0.20, jcx + 0.20], [jcy + 0.10, jcy + 0.10],
        color='#90caf9', lw=2.5, zorder=5)
js_dot = ax.plot(jcx, jcy + 0.38, 'o', ms=5, color='#ffd600', zorder=6)[0]

# ---------------------------------------------------------------------------
# Static connection arrows (grey)
# ---------------------------------------------------------------------------
static_arrows = {}
for src, dst in CONNECTIONS:
    x0, y0 = block_right_edge(src)
    x1, y1 = block_left_edge(dst)
    # Special routing: solenoid → tubes goes via a corner
    if src == 'solenoid' and dst == 'tubes':
        # solenoid is below arduino; route: right → up → right
        # draw two-segment path (corner at solenoid right, arduino level)
        sx0, sy0 = block_right_edge('solenoid')   # (3.30, 1.6)
        ax.annotate(
            '', xy=(WALL_X + 0.12, BLOCKS['tubes'][1]),
            xytext=(sx0, sy0),
            arrowprops=dict(
                arrowstyle='->', color=ARROW_COL + '55',
                lw=1.2,
                connectionstyle='arc3,rad=-0.35'
            ),
            zorder=2
        )
        continue
    arr = ax.annotate(
        '', xy=(x1, y1), xytext=(x0, y0),
        arrowprops=dict(arrowstyle='->', color=ARROW_COL + '55', lw=1.2),
        zorder=2
    )
    static_arrows[(src, dst)] = arr

# ---------------------------------------------------------------------------
# Animated elements
# ---------------------------------------------------------------------------

# ── Step 1: joystick pulse dot ────────────────────────────────────────────
joystick_pulse, = ax.plot([], [], 'o', ms=10, color='#ffd600', alpha=0.0, zorder=7)

# ── Step 2: electrical signal flash (joystick → arduino → solenoid) ───────
elec_line_ja, = ax.plot([], [], '-', color=ELEC_COL, lw=2.5, alpha=0.0, zorder=6)
elec_line_as, = ax.plot([], [], '-', color=ELEC_COL, lw=2.5, alpha=0.0, zorder=6)

# ── Step 3: air pulse travelling along tubes ──────────────────────────────
# Represented as a coloured dot sliding along the tube segment
tube_x_left  = block_left_edge('tubes')[0]
tube_x_right = block_right_edge('tubes')[0]
tube_y       = BLOCKS['tubes'][1]
air_pulse, = ax.plot([], [], 'o', ms=13, color=AIR_COL_HI, alpha=0.0, zorder=7)

# Air-crossing line (solenoid → tubes, animates separately)
air_cross_line, = ax.plot([], [], '-', color=AIR_COL_HI, lw=3.0, alpha=0.0, zorder=6)

# ── Step 4: motor spin indicator ─────────────────────────────────────────
mcx, mcy = block_centre('motor')
motor_arc, = ax.plot([], [], '-', color='#a5d6a7', lw=2.5, zorder=7)
motor_dot, = ax.plot([], [], 'o', ms=6, color='#a5d6a7', zorder=8)

# ── Step 5: catheter advancing ────────────────────────────────────────────
# Draw a small red "catheter" segment inside the catheter block
cat_cx, cat_cy = block_centre('catheter')
catheter_seg, = ax.plot([], [], '-', color='#ef5350', lw=4.0, solid_capstyle='butt',
                        zorder=7)

# ── General highlight overlay for each block ─────────────────────────────
block_highlight = {}
for name in BLOCKS:
    bpatch = FancyBboxPatch(
        (BLOCKS[name][0] - BLOCKS[name][2],
         BLOCKS[name][1] - BLOCKS[name][3]),
        2 * BLOCKS[name][2], 2 * BLOCKS[name][3],
        boxstyle='round,pad=0.07',
        linewidth=0.0,
        edgecolor='none',
        facecolor='white',
        alpha=0.0,
        zorder=3
    )
    ax.add_patch(bpatch)
    block_highlight[name] = bpatch

# ── Step label text ───────────────────────────────────────────────────────
step_text = ax.text(
    AX_W * 0.5, 0.55, '',
    ha='center', va='center', color='#e6edf3',
    fontsize=9, fontstyle='italic',
    bbox=dict(boxstyle='round,pad=0.3', facecolor='#21262d',
              edgecolor='#30363d', linewidth=1.2),
    zorder=10
)

# ---------------------------------------------------------------------------
# Animation cycle definition
# ---------------------------------------------------------------------------
# Each step is (duration_seconds, step_index)
STEP_DURATIONS = [1.0, 0.8, 1.2, 0.8, 1.0]   # seconds per step
TOTAL_ANIM = sum(STEP_DURATIONS)
CYCLE_TIME  = TOTAL_ANIM + 0.5                  # pause at end

FPS    = 50
FRAMES = int(FPS * CYCLE_TIME)


def _step_and_phase(t):
    """Return (step_index 0-4, phase 0-1) for time t within the cycle."""
    boundaries = np.cumsum([0.0] + STEP_DURATIONS)
    for i, (t0, t1) in enumerate(zip(boundaries[:-1], boundaries[1:])):
        if t <= t1:
            return i, (t - t0) / (t1 - t0)
    return len(STEP_DURATIONS) - 1, 1.0


STEP_LABELS = [
    'Step 1 — Surgeon activates joystick',
    'Step 2 — Arduino sends electrical signal to solenoid valves',
    'Step 3 — High-pressure air travels 10 m through air tubes into MRI room',
    'Step 4 — Pneumatic motor spins (32 RPM)',
    'Step 5 — Catheter advances into patient at 8 mm/s',
]

# Mapping step → which blocks to highlight
STEP_HIGHLIGHTS = {
    0: ['joystick'],
    1: ['arduino', 'solenoid'],
    2: ['tubes'],
    3: ['motor'],
    4: ['gearbox', 'catheter'],
}


def update(frame):
    t = (frame / FPS) % CYCLE_TIME
    step, phase = _step_and_phase(t)

    # ── Reset all animated objects ────────────────────────────────────────
    joystick_pulse.set_alpha(0.0)
    elec_line_ja.set_alpha(0.0)
    elec_line_as.set_alpha(0.0)
    air_pulse.set_alpha(0.0)
    air_cross_line.set_alpha(0.0)
    motor_arc.set_data([], [])
    motor_dot.set_data([], [])
    catheter_seg.set_data([], [])
    for bpatch in block_highlight.values():
        bpatch.set_alpha(0.0)

    # Highlight active blocks
    for name in STEP_HIGHLIGHTS.get(step, []):
        block_highlight[name].set_alpha(0.12)

    step_text.set_text(STEP_LABELS[step])

    # ── Step 1: joystick activation ───────────────────────────────────────
    if step == 0:
        pulse_alpha = 0.6 + 0.4 * np.sin(2 * np.pi * 3 * phase)
        joystick_pulse.set_data([jcx], [jcy + 0.38])
        joystick_pulse.set_alpha(pulse_alpha)

    # ── Step 2: electrical signal flashes ─────────────────────────────────
    elif step == 1:
        # Joystick → Arduino
        jax0, jay0 = block_right_edge('joystick')
        jax1, jay1 = block_left_edge('arduino')
        px2 = jax0 + (jax1 - jax0) * min(phase * 2, 1.0)
        elec_line_ja.set_data([jax0, px2], [jay0, jay1])
        elec_line_ja.set_alpha(0.9)
        # Arduino → Solenoid (after halfway)
        if phase > 0.5:
            p2 = (phase - 0.5) * 2.0
            ax0s, ay0s = block_right_edge('arduino')
            # route down to solenoid level
            ax1s, ay1s = block_right_edge('solenoid')
            # vertical drop
            dy = ay0s + (ay1s - ay0s) * p2
            elec_line_as.set_data([ax0s, ax0s], [ay0s, dy])
            elec_line_as.set_alpha(0.9)

    # ── Step 3: air pulse travels through tubes ───────────────────────────
    elif step == 2:
        # First half: solenoid right → tube left (crosses wall)
        cross_x0, cross_y0 = block_right_edge('solenoid')
        cross_x1 = tube_x_left
        cross_y1 = tube_y
        if phase < 0.45:
            p3a = phase / 0.45
            # draw a growing line from solenoid → tube
            mid_x = cross_x0 + (cross_x1 - cross_x0) * p3a
            mid_y = cross_y0 + (cross_y1 - cross_y0) * p3a
            air_cross_line.set_data([cross_x0, mid_x], [cross_y0, mid_y])
            air_cross_line.set_alpha(0.85)
            air_cross_line.set_color(AIR_COL_HI)
        else:
            # Line stays visible; pulse dot travels inside tube
            air_cross_line.set_data([cross_x0, cross_x1], [cross_y0, cross_y1])
            air_cross_line.set_alpha(0.6)
            p3b = (phase - 0.45) / 0.55
            px = tube_x_left + (tube_x_right - tube_x_left) * p3b
            air_pulse.set_data([px], [tube_y])
            # Colour oscillates between high and low pressure
            col = AIR_COL_HI if int(p3b * 6) % 2 == 0 else AIR_COL_LO
            air_pulse.set_color(col)
            air_pulse.set_alpha(0.9)

    # ── Step 4: motor spinning ────────────────────────────────────────────
    elif step == 3:
        angle = phase * 4 * np.pi   # 2 full rotations per step
        r = 0.30
        theta = np.linspace(0, angle, 60)
        motor_arc.set_data(mcx + r * np.cos(theta), mcy + r * np.sin(theta))
        motor_dot.set_data([mcx + r * np.cos(angle)], [mcy + r * np.sin(angle)])

    # ── Step 5: catheter advances ─────────────────────────────────────────
    elif step == 4:
        cat_hw = BLOCKS['catheter'][2]
        cat_hh = BLOCKS['catheter'][3]
        # Catheter advances from left edge to right edge of catheter block
        seg_start = cat_cx - cat_hw + 0.05
        seg_end   = cat_cx - cat_hw + 0.05 + (2 * cat_hw - 0.10) * phase
        catheter_seg.set_data([seg_start, seg_end], [cat_cy, cat_cy])

    return (joystick_pulse, elec_line_ja, elec_line_as,
            air_pulse, air_cross_line,
            motor_arc, motor_dot, catheter_seg, step_text,
            *block_highlight.values())


# ---------------------------------------------------------------------------
# Legend
# ---------------------------------------------------------------------------
legend_handles = [
    mpatches.Patch(color=CTRL_COL,    label='Control Room (non-MRI)'),
    mpatches.Patch(color=MRI_COL,     label='MRI Room (MRI-safe)'),
    mpatches.Patch(color=PATIENT_COL, label='Patient / Catheter'),
    mpatches.Patch(color=ELEC_COL,    label='Electrical Signal'),
    mpatches.Patch(color=AIR_COL_HI,  label='High-Pressure Air (2 Bar)'),
    mpatches.Patch(color=WALL_COL,    label='MRI RF Shielding Wall'),
]
ax.legend(
    handles=legend_handles, loc='lower center',
    ncol=3, fontsize=8,
    facecolor='#21262d', edgecolor='#30363d', labelcolor=TEXT_COL,
    framealpha=0.9, bbox_to_anchor=(0.5, 0.0)
)

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
ani = animation.FuncAnimation(
    fig, update,
    frames=FRAMES,
    interval=1000.0 / FPS,
    blit=False
)

plt.tight_layout(rect=[0, 0.09, 1, 0.97])
plt.show()
